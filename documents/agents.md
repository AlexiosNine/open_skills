# agents.md (Developer Guide)

## Overview
本仓库是 openSkill 的本地 demo：使用 **FastAPI** 作为本地 Skill Host，对外提供统一的 Skill 调用协议（HTTP），并在内部通过可插拔的 Runner（运行器）执行不同形态的 skill（当前为 Python CLI 脚本 `{skill_id}.py`，后续可扩展为可执行文件、远端 HTTP、容器、进程内函数等）。

**目标**
- 本地一键跑通：Agent/Client → FastAPI Skill Host → Skill Runner → Skill
- 统一 I/O：所有 skill 均返回 **Normalized Skill Result**
- 可扩展：新增 skill / 新增运行方式（Runner）尽量不改主流程
- 安全可控：文件与日志相关能力仅允许访问项目 `./data` 目录
- 可观测：使用 `trace_id` 串起一次调用链路

**预期 skills**
- `echo`：连通性验证
- `file_search`：本地文件检索（限定 `当前目录下的./data`）
- `calculator`：统计/比较（均值、中位数、min/max、比较大小等）
- `log_transform`：日志解析/转换为结构化输出（限定 `./data`）

---

## Quickstart

### Prerequisites
- Python 3.10+（建议 3.11）
- OS：macOS / Linux 

### Environment Variables
| Name | Required | Default | Notes |
|------|----------|---------|------|
| OPENSKILL_HTTP_BASE_URL | yes | http://127.0.0.1:8000 | FastAPI Skill Host 基地址 |
| OPENSKILL_ALLOWED_ROOT | yes | ./data | 文件/日志类 skill 允许访问的根目录 |
| OPENSKILL_CLI_DIR | yes | ./skills_cli | CLI skills 脚本所在目录（*.py） |
| OPENSKILL_TIMEOUT_MS | no | 15000 | 单次调用超时（HTTP/CLI 共用） |
| OPENSKILL_DEBUG | no | 0 | 1 开启 debug |

> 说明：`OPENSKILL_HTTP_BASE_URL` 主要用于 client/agent 侧调用 Skill Host；Skill Host 自身监听地址/端口以实际启动参数为准。

### Run (示例占位，按仓库实际入口补充)
1. 安装依赖（示例）：
   - `python -m venv .venv`
   - `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
   - `pip install -r requirements.txt`

2. 启动 FastAPI Skill Host（示例）：
   - `python -m skill_host`
   - 或 `uvicorn skill_host.app:app --host 127.0.0.1 --port 8000`

3. 调用一个 skill（curl 示例）：
   - `curl -sS -X POST "http://127.0.0.1:8000/skills/echo:invoke" -H "Content-Type: application/json" -H "X-Trace-Id: demo-123" -d '{ "input": { "text": "hello" } }'`

---

## Architecture

### Components
- **Client/Agent**
  - 发起 skill 调用请求
  - 决定调用哪个 `skill_id`（可用规则路由/更智能的意图识别）
- **FastAPI Skill Host**
  - 对外提供统一 HTTP 协议：`POST /skills/{id}:invoke`
  - 读取 `X-Trace-Id`
  - 查找 skill manifest
  - 选择 Runner 并执行
  - 返回 Normalized Skill Result
- **Skill Registry / Manifest Loader**
  - 负责从配置加载 skill 定义（manifest）
- **Runners（运行器，兼容层）**
  - Strategy：根据 manifest 的 `type/runtime` 选择不同执行方式
  - 统一适配输出为 Normalized Skill Result
- **Skills**
  - 当前为 Python 脚本：`{OPENSKILL_CLI_DIR}/{skill_id}.py`

### Call Flow
1. Client/Agent → Skill Host：`POST /skills/{id}:invoke`
2. Skill Host 读取 `X-Trace-Id`（没有则生成）
3. Skill Host 查 manifest → RunnerFactory 选择 Runner
4. Runner 执行 skill（CLI/HTTP/…）
5. Runner 适配结果为 Normalized Skill Result
6. Skill Host 返回结果并记录日志（trace_id、latency 等）

---

## Invocation Protocol (HTTP)

### Endpoint
- `POST /skills/{skill_id}:invoke`

### Headers
- `Content-Type: application/json`
- `X-Trace-Id: <trace_id>`
  - trace_id 统一放在 header
  - client 可传入；如缺失可由 host 生成并在响应中返回

### Request Body
固定结构：
- `{ "input": { ... } }`

### Response Body
固定结构：**Normalized Skill Result**（详见下一节）。

---

## Normalized Skill Result (统一返回结构)

所有 skill（无论是 HTTP/CLI/其它）必须最终返回以下 JSON 结构：

- `success`: boolean
- `skill_id`: string
- `trace_id`: string
- `data`: object | null
- `error`: object | null
  - `code`: number
  - `message`: string
  - `details`: object (optional)
- `meta`: object (optional)
  - `latency_ms`: number
  - `version`: string
  - `truncated`: boolean (optional)

**约束**
- `success=true` → `error=null`
- `success=false` → `data=null`（推荐，保持一致性）
- 调试信息不要直接打印到 stdout；应放到 `meta` 或 `error.details`

---

## Runner Compatibility Design (可扩展设计)

### Why
当前 demo 仅支持 Python CLI 脚本 `{skill_id}.py`，但未来可能支持：
- 无扩展名可执行文件
- 远端 HTTP skills
- Docker 容器
- 进程内函数（SDK）

为避免主流程（路由/host）不断改动，引入 Runner 抽象层。

### Patterns
- **Strategy**：不同 Runner 是不同执行策略（cli:python / cli:exec / http / docker / inproc）
- **Factory**：RunnerFactory 根据 manifest 选择 runner
- **Adapter**：Runner 将原始输出/异常统一适配成 Normalized Skill Result
- **Registry**：集中加载并管理 skill manifest

---

## Skill Manifest (Recommended)
建议为每个 skill 提供 manifest（YAML/JSON 均可），用于驱动 Runner 选择与安全策略。

示例（YAML）：
- `id`: `calculator`
- `type`: `cli`
- `runtime`: `python`
- `entry`: `./skills_cli/calculator.py`
- `timeout_ms`: 15000
- `allowed_root`: `./data`

> 说明：manifest 是推荐项。demo 初期也可用硬编码 registry，但建议尽早用 manifest 以验证“可扩展”设计。

---

## CLI Skill Contract (Python Scripts)

### Naming
- 当前仅支持：`{OPENSKILL_CLI_DIR}/{skill_id}.py`

### stdin
- 固定输入 JSON：`{ "input": { ... } }`

### stdout / stderr
- **stdout 严格只输出 JSON**
- **stderr 也严格只输出 JSON（推荐）**
  - 避免上层解析失败
  - 如需 debug，写入 `meta` 或 `error.details`

### Exit Code
- `success=true` → exit 0
- `success=false` → exit non-zero（推荐 1）

---

## Security & Filesystem Policy (Local Demo)
- 允许访问当前目录下的 data ：项目 `./data`
- 所有输入路径（如 `root_dir`、`input_path`）必须满足：
  - 规范化后仍位于 `./data` 之下（防止路径穿越）
  - 拒绝绝对路径（推荐）
  - 拒绝包含 `..`
- 建议的资源限制（实现中体现，文档中声明）：
  - 单文件最大读取大小（例如 5MB）
  - 最大返回条数 limit（默认 20）
  - 超时：`OPENSKILL_TIMEOUT_MS`

---

## Skills Catalog

### Skill: echo
**Skill ID**
- `echo`

**Purpose**
- 验证调用链路与 trace_id header 透传。

**Inputs**
| Field | Type | Required | Example |
|------|------|----------|---------|
| text | string | yes | "hello" |

**Outputs (data)**
| Field | Type | Notes |
|------|------|------|
| echoed | string | 回显输入 |

**HTTP Example**
Request:
- `POST {BASE_URL}/skills/echo:invoke`
- Headers:
  - `X-Trace-Id: demo-123`
- Body:
  - `{ "input": { "text": "hello" } }`

Response (example):
- `{ "success": true, "skill_id": "echo", "trace_id": "demo-123", "data": { "echoed": "hello" }, "error": null, "meta": { "latency_ms": 3, "version": "0.1.0" } }`

---

### Skill: file_search
**Skill ID**
- `file_search`

**Purpose**
- 在允许目录（默认 `./data`）下检索文件内容并返回命中片段。

**Inputs**
| Field | Type | Required | Example |
|------|------|----------|---------|
| query | string | yes | "openSkill" |
| root_dir | string | no | "./data/docs" |
| glob | string | no | "**/*.md" |
| limit | int | no | 20 |

**Outputs (data)**
| Field | Type | Notes |
|------|------|------|
| matches | array | 元素包含 path, line_no, snippet |

**Errors**
- `INVALID_ARGUMENT`：query 为空、limit 非法等
- `FORBIDDEN_PATH`：root_dir 不在 `./data` 下
- `INTERNAL`：读取失败、编码错误等

**CLI Example**
- command: `{OPENSKILL_CLI_DIR}/file_search.py`
- stdin: `{ "input": { "query": "openSkill", "glob": "**/*.md", "limit": 5 } }`

---

### Skill: calculator
**Skill ID**
- `calculator`

**Purpose**
- 数据处理/统计计算（均值、中位数、最小/最大、比较大小等），用于原材料价格 demo。

**Inputs**
| Field | Type | Required | Example |
|------|------|----------|---------|
| numbers | array[number] | yes | [10.5, 9.9, 11.2] |
| ops | array[string] | yes | ["mean", "median", "min", "max"] |
| compare | object | no | {"a": 10, "b": 12} |

**Outputs (data)**
| Field | Type | Notes |
|------|------|------|
| results | object | 例如：mean/median/min/max |
| comparison | object | 可选：比较结论 |

**Errors**
- `INVALID_ARGUMENT`：numbers 为空、包含非数值、ops 不支持等

**CLI Example**
- command: `{OPENSKILL_CLI_DIR}/calculator.py`
- stdin: `{ "input": { "numbers": [10.5, 9.9, 11.2], "ops": ["mean","median"] } }`

---

### Skill: log_transform
**Skill ID**
- `log_transform`

**Purpose**
- 将 `./data` 下的日志文件转换为结构化记录（JSON/JSONL/CSV 等，按实现支持），便于后续检索与分析。

**Inputs**
| Field | Type | Required | Example |
|------|------|----------|---------|
| input_path | string | yes | "./data/logs/app.log" |
| format | string | no | "text" / "jsonl" |
| output | string | no | "stdout" / "file" |
| rules | object | no | {"timestamp_regex": "...", "level_map": {"WARN":"WARNING"}} |
| limit | int | no | 200 |

**Outputs (data)**
| Field | Type | Notes |
|------|------|------|
| records | array | output=stdout 时建议仅返回前 N 条 |
| output_path | string | output=file 时返回生成文件路径 |
| stats | object | 可选：处理行数、丢弃行数、截断等 |

**Errors**
- `FORBIDDEN_PATH`：input_path 不在 `./data`
- `INVALID_ARGUMENT`：format/output/rules 不合法
- `INTERNAL`：解析失败、写入失败等

**CLI Example**
- command: `{OPENSKILL_CLI_DIR}/log_transform.py`
- stdin: `{ "input": { "input_path": "./data/logs/app.log", "format": "text", "output": "stdout", "limit": 50 } }`

---

## Routing / Invocation (Demo Strategy)

本 demo 可采用最小规则路由（在 client/agent 侧实现）：
- 以 `echo:` 开头 → `echo`
- 包含 `搜索|find|grep|检索` → `file_search`
- 包含 `平均|均值|mean|中位数|median|min|max|比较` → `calculator`
- 包含 `日志|log|转换|parse|jsonl` → `log_transform`
- 否则默认 `echo` 并提示可用指令

建议记录路由日志字段：
- `trace_id`
- `selected_skill_id`
- `routing_reason`

---

## Observability & Debugging

### Required Log Fields
- `trace_id`
- `skill_id`
- `runner_type`（例如 `cli:python` / `http`）
- `latency_ms`
- `success`
- `error.code`
- `error.message`

### Common Issues
1) HTTP Skill Host 不通
- 检查 `OPENSKILL_HTTP_BASE_URL`
- 确认路由为 `POST /skills/{id}:invoke`
- 确认 `X-Trace-Id` header 已传

2) CLI 输出解析失败
- 确保 stdout/stderr **只输出 JSON**
- 如需调试，将信息放到 `meta` 或 `error.details`

3) 路径被拒绝（FORBIDDEN_PATH）
- 确保所有路径位于项目 `./data` 下
- 检查路径规范化（realpath）后是否仍在允许目录内

4) 超时
- 调整 `OPENSKILL_TIMEOUT_MS`
- 检查 CLI 是否存在长耗时计算/死循环

---

## Adding a New Skill

### Add a new CLI Python skill (current supported)
1. 新建脚本：`{OPENSKILL_CLI_DIR}/{skill_id}.py`
2. 读取 stdin JSON：`{ "input": { ... } }`
3. 输出 stdout JSON：Normalized Skill Result（success/data/error/meta）
4. 如需文件访问：严格限制在 `./data`
5. 为 skill 添加 manifest（推荐）与本文档的 Catalog 条目
6. 添加至少 1 个测试：
- stdin → stdout JSON schema 校验

### Add a new Runner (future extension)
1. 实现 `SkillRunner` 接口（invoke）
2. 在 RunnerFactory/Registry 中注册（如键为 `type:runtime`）
3. 在 manifest 中为目标 skill 指定新的 `type/runtime/entry`
4. 确保最终返回 Normalized Skill Result（Adapter 逻辑在 runner 内完成）

---

## Versioning
- 建议在 `meta.version` 中填充 skill 或 host 的版本号（例如 `0.1.0`）
- manifest 变更需同步更新本文档对应的 Inputs/Outputs/Examples

---

## Best Practices & Patterns (最佳实践与范式)

### 1. Agent 实现范式：LLM Function Calling

#### 架构设计
- **Agent Loop**：管理多轮对话和工具调用循环
- **Tool Manager**：将 Skill Manifest 转换为 Function Calling Schema
- **Validator**：使用 Pydantic 进行参数验证
- **LLM Client**：支持多提供商（OpenAI、DashScope/Qwen）

#### 核心流程
```
用户消息 → Agent Loop
    ↓
获取可用工具（Function Calling Schemas）
    ↓
调用 LLM（传入 messages + tools）
    ↓
LLM 返回 tool_calls（或最终答案）
    ↓
验证参数（Pydantic Schema）
    ↓
执行工具（直接调用 Runner）
    ↓
将结果反馈给 LLM
    ↓
LLM 生成最终回答
```

#### 关键实现点
1. **工具发现**：从 `SkillRegistry` 获取所有 skills，转换为 Function Calling Schema
2. **参数验证**：使用 Pydantic Schema 验证 LLM 返回的参数
3. **错误反馈**：验证失败时，格式化错误信息反馈给 LLM，支持自动修正（最多 `max_validation_retries` 次）
4. **会话管理**：支持多轮对话，通过 `conversation_id` 管理历史

#### 代码示例
```python
# Agent Loop 核心逻辑
for iteration in range(max_iterations):
    llm_response = self.llm_client.chat(messages=messages, tools=tools)
    
    if llm_response.tool_calls:
        for tool_call in llm_response.tool_calls:
            # 验证参数
            validation_result = self.validator.validate(tool_call)
            if not validation_result.valid:
                # 反馈错误给 LLM，让其修正
                messages.append(Message(role="user", content=validation_result.error_message))
                continue
            
            # 执行工具
            tool_result = self.tool_manager.invoke_tool(...)
            # 将结果添加到会话
            messages.append(Message(role="tool", content=json.dumps(tool_result)))
```

---

### 2. 死锁问题解决：避免同步 HTTP 调用

#### 问题场景
在 FastAPI 异步路由中，如果 Agent 使用同步 HTTP 调用 Skill Host（同一进程），会导致事件循环阻塞，形成死锁。

#### 解决方案
**直接调用 Runner，避免 HTTP 层**

```python
# ❌ 错误做法（会导致死锁）
class ToolManager:
    def invoke_tool(self, ...):
        response = requests.post(f"{BASE_URL}/skills/{tool_name}:invoke", ...)
        return response.json()

# ✅ 正确做法（直接调用）
class ToolManager:
    def invoke_tool(self, ...):
        factory = get_factory()
        runner = factory.get_runner(manifest)
        result = runner.invoke(...)  # 直接调用，不经过 HTTP
        return result
```

#### 关键原则
- **同一进程内**：Agent 和 Skill Host 在同一 FastAPI 应用中时，直接调用 Runner
- **异步路由**：如果 Agent 的 `chat()` 是同步方法，使用 `ThreadPoolExecutor` 在线程池中执行
- **分离部署**：如果 Agent 和 Skill Host 分离部署，使用异步 HTTP 客户端（如 `httpx`）

#### 代码示例
```python
# FastAPI 路由中使用线程池
@router.post("/agent/chat")
async def chat(request: AgentRequest):
    agent = get_agent()
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        response = await loop.run_in_executor(
            executor, 
            lambda: agent.chat(request, trace_id=trace_id)
        )
    return response
```

---

### 3. 参数验证与错误反馈范式

#### Pydantic Schema 定义
为每个 skill 定义对应的 Pydantic Schema：

```python
# src/agent/schemas/calculator.py
class CalculatorInput(BaseModel):
    numbers: List[float] = Field(..., description="List of numbers")
    ops: List[str] = Field(..., description="Operations: mean, median, min, max")
    compare: Optional[Dict[str, float]] = Field(None, description="Comparison values")
```

#### 验证与错误格式化
```python
class ToolCallValidator:
    def validate(self, tool_call: ToolCall) -> ValidationResult:
        schema_class = SKILL_INPUT_SCHEMAS.get(tool_call.name)
        try:
            validated_data = schema_class(**tool_call.arguments)
            return ValidationResult(valid=True, corrected_arguments=validated_data.model_dump())
        except ValidationError as e:
            # 格式化错误信息，反馈给 LLM
            error_message = self._format_validation_error(e, tool_call.name)
            return ValidationResult(valid=False, error_message=error_message)
```

#### 错误反馈格式
错误信息应该：
- 明确指出哪些字段有问题
- 说明期望的类型和格式
- 提供修正建议
- 使用 LLM 易于理解的语言

---

### 4. 日志与可观测性范式

#### Trace ID 上下文传递
使用 `ContextVar` 在异步上下文中传递 `trace_id`：

```python
# 定义上下文变量
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")

# 在请求开始时设置
trace_id = x_trace_id or str(uuid.uuid4())
trace_id_ctx.set(trace_id)

# 在日志中使用
logger.info("message", extra={"trace_id": trace_id_ctx.get()})
```

#### 日志格式化
确保所有日志都包含 `trace_id`，即使在某些子进程中缺失：

```python
class TraceIDFormatter(logging.Formatter):
    def format(self, record):
        # 确保 trace_id 始终存在
        if not hasattr(record, 'trace_id'):
            record.trace_id = "-"
        return super().format(record)
```

#### 关键日志字段
- `trace_id`：追踪整个调用链路
- `skill_id`：标识调用的 skill
- `latency_ms`：执行耗时
- `success`：是否成功
- `error.code`、`error.message`：错误信息

---

### 5. 配置管理范式

#### 多 LLM 提供商支持
支持多个 LLM 提供商，通过配置切换：

```python
# 环境变量配置
OPENAI_API_KEY=...
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

DASHSCOPE_API_KEY=...
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

#### 配置加载优先级
1. 环境变量
2. `.env` 文件
3. 默认值

#### 配置验证
在应用启动时验证必需的配置：

```python
def has_llm_config() -> bool:
    """检查是否配置了至少一个 LLM 提供商"""
    return bool(
        config.openai_api_key or
        config.dashscope_api_key or
        config.anthropic_api_key
    )
```

---

### 6. Skill 调用流程（完整链路）

#### 通过 Agent API 调用
```
用户请求 POST /agent/chat
    ↓
FastAPI 路由（异步）
    ↓
在线程池中执行 agent.chat()（同步方法）
    ↓
Agent Loop：
    ├─ 获取工具列表（Function Calling Schemas）
    ├─ 调用 LLM
    ├─ 验证工具参数（Pydantic）
    ├─ 执行工具（直接调用 Runner）
    └─ 将结果反馈给 LLM
    ↓
Runner Factory 选择 Runner
    ↓
CLIPythonRunner 执行 Python 脚本
    ├─ subprocess.run()
    ├─ 通过 stdin 传入 JSON
    └─ 从 stdout 读取 JSON 结果
    ↓
返回 NormalizedSkillResult
    ↓
Agent 生成最终回答
    ↓
返回 AgentResponse
```

#### 直接调用 Skill API
```
用户请求 POST /skills/{skill_id}:invoke
    ↓
FastAPI 路由（异步）
    ↓
Skill Registry 查找 manifest
    ↓
Runner Factory 选择 Runner
    ↓
Runner 执行 skill
    ↓
返回 NormalizedSkillResult
```

---

### 7. 测试与调试范式

#### Swagger UI 测试
- 访问 `http://127.0.0.1:8000/docs`
- 使用 "Try it out" 功能测试 API
- 查看请求/响应格式和错误信息

#### 测试脚本
为每个 skill 创建测试脚本：
- `test/test_api.sh`：基础 API 测试
- `test/test_agent.sh`：Agent API 测试
- `test/test_calculator.sh`：Calculator skill 测试

#### 调试技巧
1. **查看日志**：所有日志都包含 `trace_id`，可以追踪完整调用链
2. **检查参数**：使用 Pydantic 验证确保参数格式正确
3. **验证工具输出**：确保 skill 脚本只输出 JSON 格式
4. **检查超时**：如果超时，检查 skill 脚本是否有死循环或长耗时操作

---

### 8. 错误处理范式

#### 分层错误处理
1. **Skill 层**：返回 `NormalizedSkillResult`，包含错误信息
2. **Runner 层**：捕获异常，转换为 `NormalizedSkillResult`
3. **Agent 层**：处理工具调用错误，反馈给 LLM
4. **API 层**：捕获未处理异常，返回标准错误响应

#### 错误代码规范
- `INVALID_ARGUMENT`：参数错误
- `NOT_FOUND`：资源未找到
- `TIMEOUT`：超时
- `FORBIDDEN_PATH`：路径不允许
- `INTERNAL`：内部错误
- `TOOL_INVOCATION_ERROR`：工具调用错误

#### 错误信息格式
```json
{
  "success": false,
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "参数错误：numbers 字段是必需的",
    "details": {
      "field": "numbers",
      "reason": "missing"
    }
  }
}
```

---

### 9. 性能优化范式

#### 成本控制
- **Token 限制**：`max_tokens` 限制每次请求的最大 token 数
- **工具调用限制**：`max_tool_calls` 限制每次请求的最大工具调用次数
- **超时控制**：`timeout_ms` 限制单个 skill 的执行时间

#### 资源管理
- **Runner 缓存**：RunnerFactory 缓存 Runner 实例，避免重复创建
- **工具 Schema 缓存**：ToolManager 缓存工具 Schema，避免重复构建
- **会话限制**：限制会话历史长度（如最多 20 条消息）

---

### 10. 扩展性设计范式

#### 新增 Skill
1. 创建 Python 脚本：`skill_cli/{skill_id}.py`
2. 创建 Manifest：`skills/{skill_id}.yaml`
3. 定义 Pydantic Schema：`src/agent/schemas/{skill_id}.py`
4. 注册 Schema：在 `src/agent/schemas/__init__.py` 中注册
5. 添加测试：创建 `test/test_{skill_id}.sh`

#### 新增 Runner
1. 实现 `SkillRunner` 接口
2. 在 `RunnerFactory` 中注册（键为 `type:runtime`）
3. 确保返回 `NormalizedSkillResult`

#### 新增 LLM 提供商
1. 实现 `LLMClient` 接口
2. 在 `create_client()` 中注册
3. 添加配置项（API key、base URL、model）

---

## 案例研究

### 案例 1：Calculator Skill 实现

**需求**：实现一个计算器 skill，支持统计计算（均值、中位数、最小值、最大值、求和）

**实现步骤**：
1. 创建 `skill_cli/calculator.py`，实现计算逻辑
2. 创建 `skills/calculator.yaml` manifest
3. 定义 `src/agent/schemas/calculator.py` Pydantic Schema
4. 注册到 `SKILL_INPUT_SCHEMAS`
5. 创建测试脚本 `test/test_calculator.sh`

**关键点**：
- 输入验证：确保 `numbers` 是数字列表，`ops` 是支持的操作
- 错误处理：处理空列表、无效操作等边界情况
- 输出格式：返回标准化的 `NormalizedSkillResult`

### 案例 2：死锁问题解决

**问题**：Agent 调用 Skill Host 时出现超时，最终发现是死锁问题

**原因**：
- Agent 和 Skill Host 在同一 FastAPI 应用中
- Agent 使用同步 HTTP 调用 Skill Host
- 阻塞了事件循环，导致 Skill Host 无法响应

**解决方案**：
- 修改 `ToolManager.invoke_tool()`，直接调用 Runner 而不是 HTTP
- 在 FastAPI 路由中使用 `ThreadPoolExecutor` 执行同步的 `agent.chat()`

**效果**：
- 消除了死锁问题
- 提高了性能（减少了 HTTP 开销）
- 保持了代码的简洁性

### 案例 3：参数验证与 LLM 自我修正

**场景**：LLM 返回的工具参数格式不正确（如缺少必需字段、类型错误）

**实现**：
1. 使用 Pydantic Schema 验证参数
2. 格式化错误信息，反馈给 LLM
3. LLM 根据错误信息修正参数
4. 最多重试 `max_validation_retries` 次

**效果**：
- 提高了工具调用的成功率
- 减少了人工干预
- 提升了用户体验

---

## 总结

本 demo 实现了一个完整的 Agent 系统，核心特点：

1. **LLM Function Calling**：完全依赖 LLM 的 Function Calling 能力，无需规则路由
2. **参数验证**：使用 Pydantic 进行严格验证，支持 LLM 自我修正
3. **直接调用**：Agent 直接调用 Runner，避免 HTTP 死锁
4. **可观测性**：完整的 trace_id 追踪和日志记录
5. **可扩展性**：支持新增 skill、runner、LLM 提供商
6. **标准化**：统一的输入输出格式（NormalizedSkillResult）

这些范式可以应用到其他类似的 Agent 系统中。
