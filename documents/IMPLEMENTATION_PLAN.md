# Agent 实现计划

## 实现顺序

### Step 1: 基础结构搭建
1. 创建 `src/agent/` 目录结构
2. 定义基础数据模型（Message, ToolCall, AgentResponse 等）
3. 配置依赖（openai, dashscope）

### Step 2: Pydantic Schema 定义
1. 为每个 skill 定义输入/输出 Pydantic 模型
   - `schemas/echo.py`
   - `schemas/file_search.py`
   - `schemas/calculator.py`
   - `schemas/log_transform.py`
2. 实现统一的校验接口

### Step 3: Tool Manager
1. 从 Registry 获取所有 skills
2. Skill Manifest → Function Calling Schema 转换
3. 生成简单的工具描述
4. 工具调用接口封装

### Step 4: LLM Client
1. OpenAI Client 实现
2. DashScope/Qwen Client 实现
3. 统一接口抽象
4. Function Calling 支持
5. Token 限制管理

### Step 5: Agent Loop
1. 对话历史管理
2. 工具调用检测
3. Pydantic 校验集成
4. 错误反馈机制
5. 工具执行和结果反馈
6. 循环控制（Token、次数、超时）

### Step 6: API 端点
1. POST /agent/chat 实现
2. 对话会话管理
3. 错误处理
4. 集成到 FastAPI

### Step 7: 测试
1. 单元测试（各组件）
2. 集成测试（完整流程）
3. 格式校验测试
4. 多工具组合测试

---

## 关键实现细节

### Pydantic 校验错误反馈格式

**错误信息格式：**
```
工具调用参数格式错误：
工具名称: file_search
错误详情:
  - query: 字段是必需的（缺失）
  - limit: 必须是整数（当前值: "20"，类型: str）

请根据以上错误修正参数格式，确保：
1. 所有必需字段都已提供
2. 字段类型正确（query 应为字符串，limit 应为整数）
3. 参数值符合约束条件

修正后的参数应为：
{
  "query": "your_search_query",
  "limit": 20
}
```

### Token 限制策略

**默认限制：**
- 单次对话最大 token: 2000
- 最大工具调用次数: 5
- 单次工具调用超时: 15秒

**可配置：**
- 通过 API 请求参数覆盖
- 通过环境变量设置全局默认值

### 对话历史管理

**存储方式：**
- 内存存储（简单实现）
- 使用 `conversation_id` 关联
- 支持上下文窗口限制（保留最近 N 轮）

**消息结构：**
```python
class Message:
    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # 用于 tool role
```

---

## 测试用例设计

### Echo Skill 测试
1. ✅ "echo hello" → 验证调用 echo，参数正确
2. ✅ "echo 123" → 验证数字也能正确处理

### File Search Skill 测试
1. ✅ "搜索包含 'calculator' 的文件"
2. ✅ "在 data 目录下搜索 'openSkill'，最多返回 5 条"
3. ✅ 格式错误测试：缺少 query 参数 → 验证校验和修正

### Calculator Skill 测试
1. ✅ "计算 [1,2,3,4,5] 的平均值"
2. ✅ "计算 [10,20,30] 的平均值、最大值和最小值"
3. ✅ 格式错误测试：numbers 不是数组 → 验证校验和修正

### 多工具组合测试
1. ✅ "搜索包含 'calculator' 的文件，然后计算 [1,2,3] 的平均值"
2. ✅ "先搜索文件，再计算平均值，最后 echo 结果"

### 格式校验和修正测试
1. ✅ 故意传入错误类型（字符串代替数字）
2. ✅ 缺少必需字段
3. ✅ 参数值超出范围
4. ✅ 验证 LLM 能够根据错误信息修正

### 边界情况测试
1. ✅ Token 限制触发
2. ✅ 工具调用次数限制触发
3. ✅ 工具执行失败处理
4. ✅ 超时处理

---

## 依赖添加

### requirements.txt 新增
```
openai>=1.0.0
dashscope>=1.10.0
```

### 可选依赖
```
anthropic>=0.18.0  # Phase 2
```

---

## API 设计细节

### POST /agent/chat

**请求体：**
```json
{
  "message": "用户消息",
  "conversation_id": "可选，用于多轮对话",
  "provider": "openai" | "qwen",
  "model": "gpt-3.5-turbo" | "qwen-turbo",
  "max_tool_calls": 5,
  "max_tokens": 2000,
  "temperature": 0.7
}
```

**响应体：**
```json
{
  "success": true,
  "response": "LLM 的最终回答",
  "conversation_id": "conv-123",
  "trace_id": "trace-456",
  "tool_calls": [
    {
      "tool": "file_search",
      "arguments": {"query": "calculator"},
      "validated": true,
      "result": {
        "success": true,
        "data": {...}
      }
    }
  ],
  "meta": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "total_tokens": 1500,
    "tool_calls_count": 1,
    "validation_retries": 0,
    "latency_ms": 2500
  }
}
```

---

## 实现检查清单

### Phase 1: MVP
- [ ] 目录结构创建
- [ ] Pydantic Schema 定义（4 个 skills）
- [ ] Tool Manager 实现
- [ ] OpenAI Client 实现
- [ ] DashScope/Qwen Client 实现
- [ ] Pydantic 校验器实现
- [ ] Agent Loop 核心逻辑
- [ ] 错误反馈机制
- [ ] API 端点实现
- [ ] 基础测试用例

### Phase 2: 增强
- [ ] 多轮工具调用优化
- [ ] 对话历史持久化
- [ ] 性能优化
- [ ] 更完善的错误处理
- [ ] Anthropic Claude 支持

