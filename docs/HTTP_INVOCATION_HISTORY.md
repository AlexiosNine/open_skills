# Agent 通过 HTTP 调用 Skill Host 的历史实现

## 之前的实现方式

在修复死锁问题之前，`ToolManager.invoke_tool()` 方法是通过 HTTP 调用 Skill Host 的：

### 实现代码（已废弃）

```python
def invoke_tool(
    self, tool_name: str, arguments: Dict[str, Any], trace_id: str
) -> Dict[str, Any]:
    """
    Invoke a tool via Skill Host (HTTP).
    """
    import requests  # 或 httpx
    from ..config import config

    # 构建 Skill Host 的 HTTP 端点 URL
    url = f"{config.http_base_url}/skills/{tool_name}:invoke"
    headers = {
        "Content-Type": "application/json",
        "X-Trace-Id": trace_id,
    }
    payload = {"input": arguments}

    try:
        # 方式 1: 使用 requests（同步）
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
        
        # 方式 2: 使用 httpx（同步客户端）
        # import httpx
        # with httpx.Client(timeout=60.0) as client:
        #     response = client.post(url, json=payload, headers=headers)
        #     response.raise_for_status()
        #     return response.json()
    except Exception as e:
        logger.error(f"Failed to invoke tool {tool_name}: {e}", exc_info=True)
        return {
            "success": False,
            "skill_id": tool_name,
            "trace_id": trace_id,
            "data": None,
            "error": {
                "code": "TOOL_INVOCATION_ERROR",
                "message": f"Failed to invoke tool: {str(e)}",
            },
            "meta": {"latency_ms": 0, "version": "0.1.0"},
        }
```

## 调用流程

```
Agent API (/agent/chat)
    ↓
Agent.chat() [同步方法]
    ↓
ToolManager.invoke_tool()
    ↓
HTTP POST → http://127.0.0.1:8000/skills/echo:invoke
    ↓
Skill Host API (/skills/{skill_id}:invoke) [异步路由]
    ↓
Runner.invoke()
    ↓
返回 NormalizedSkillResult
```

## 问题：死锁/阻塞

### 问题场景

1. **用户请求** → `POST /agent/chat`（异步路由）
2. **Agent 处理** → `agent.chat()`（同步方法，在异步路由中执行）
3. **工具调用** → `ToolManager.invoke_tool()` 通过 HTTP 调用 Skill Host
4. **Skill Host** → 正在处理同一个 Agent 请求（`/agent/chat`）
5. **死锁** → Agent 等待 Skill Host 响应，但 Skill Host 正在处理 Agent 的请求

### 为什么会死锁？

- **FastAPI 异步路由**：`/agent/chat` 是 `async def`，运行在事件循环中
- **同步阻塞调用**：`agent.chat()` 是同步方法，内部使用 `requests.post()` 或 `httpx.Client()`（同步）
- **同一进程**：Agent 和 Skill Host 在同一个 FastAPI 应用中
- **事件循环阻塞**：同步 HTTP 调用阻塞了事件循环，导致 Skill Host 无法处理新的请求

### 超时表现

- Agent 等待 Skill Host 响应：60 秒超时
- Skill Host 无法响应：因为事件循环被阻塞
- 最终：请求超时失败

## 解决方案

### 当前实现：直接调用 Runner

```python
def invoke_tool(
    self, tool_name: str, arguments: Dict[str, Any], trace_id: str
) -> Dict[str, Any]:
    """
    Invoke a tool directly via Runner (avoid HTTP deadlock).
    """
    from ..runners import get_factory
    
    # 获取 skill manifest
    manifest = self.registry.get_skill(tool_name)
    if not manifest:
        return error_response(...)
    
    try:
        # 直接调用 Runner，避免 HTTP 死锁
        factory = get_factory()
        runner = factory.get_runner(manifest)
        
        result = runner.invoke(
            skill_id=tool_name,
            input_data=arguments,
            trace_id=trace_id,
            manifest=manifest,
        )
        
        # 转换为 dict 格式返回
        return convert_to_dict(result)
    except Exception as e:
        return error_response(...)
```

### 优势

1. **避免死锁**：不通过 HTTP，直接调用 Runner
2. **性能更好**：减少了 HTTP 序列化/反序列化开销
3. **更简单**：不需要处理 HTTP 错误、超时等

### 适用场景

- ✅ **同一进程内调用**：Agent 和 Skill Host 在同一应用中
- ✅ **性能优先**：减少网络开销
- ❌ **分布式部署**：如果 Agent 和 Skill Host 分离，仍需 HTTP

## 如果 Agent 和 Skill Host 分离部署

如果将来需要将 Agent 和 Skill Host 分离到不同服务，可以：

1. **使用异步 HTTP 客户端**：
   ```python
   async def invoke_tool(...):
       async with httpx.AsyncClient(timeout=60.0) as client:
           response = await client.post(url, json=payload, headers=headers)
           return response.json()
   ```

2. **使用线程池**：
   ```python
   # 在异步路由中
   loop = asyncio.get_event_loop()
   with ThreadPoolExecutor() as executor:
       response = await loop.run_in_executor(
           executor,
           lambda: requests.post(url, json=payload, headers=headers)
       )
   ```

3. **使用消息队列**：Agent → Queue → Skill Host（解耦）

## 总结

- **之前**：通过 HTTP 调用 Skill Host（`http://127.0.0.1:8000/skills/{id}:invoke`）
- **问题**：在同一进程中导致死锁/阻塞
- **现在**：直接调用 Runner，避免 HTTP 调用
- **未来**：如果分离部署，可以使用异步 HTTP 或消息队列

