# Agent/模型自主调用工具的设计思路

## 当前状态分析

### ✅ 已实现
1. **Skill Host 基础设施**
   - FastAPI Skill Host（HTTP 接口）
   - Skill Registry（技能注册表）
   - Runner 框架（可扩展执行层）
   - Normalized Skill Result（统一返回格式）
   - Trace ID 追踪

2. **配置支持**
   - LLM API 配置（OpenAI, Anthropic, DashScope）
   - 环境变量管理

3. **基础 Skill**
   - Echo skill（已实现）

### ❌ 待实现
1. **Agent/Client 层**
   - 模型调用封装
   - 工具发现机制
   - 工具调用决策
   - 多轮对话/工具调用循环

2. **工具描述系统**
   - Skill 的 Function Calling 描述
   - 工具 Schema 生成
   - 工具文档自动生成

3. **集成层**
   - 模型 API 调用封装
   - 工具调用与模型响应的桥接
   - 错误处理和重试机制

---

## 架构设计思路

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent/Client Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  LLM Client  │  │ Tool Manager │  │   Router     │ │
│  │  (OpenAI/    │  │  (发现/描述)  │  │ (决策/路由)   │ │
│  │  Claude/     │  │              │  │              │ │
│  │  Qwen)       │  │              │  │              │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                    ┌───────▼────────┐                   │
│                    │  Agent Loop    │                   │
│                    │  (多轮对话)     │                   │
│                    └───────┬────────┘                   │
└────────────────────────────┼────────────────────────────┘
                             │
                             │ HTTP
                             │
┌────────────────────────────▼────────────────────────────┐
│              FastAPI Skill Host (已有)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Registry   │  │   Factory   │  │   Runners   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 1. Tool Manager（工具管理器）

**职责：**
- 从 Skill Registry 获取所有可用 skills
- 将 Skill Manifest 转换为 Function Calling Schema
- 提供工具描述给 LLM
- 管理工具调用的生命周期

**关键方法：**
```python
class ToolManager:
    def get_available_tools() -> List[ToolSchema]
    def skill_to_function_schema(manifest: SkillManifest) -> FunctionSchema
    def invoke_tool(tool_name: str, arguments: dict) -> NormalizedSkillResult
```

**Function Calling Schema 示例：**
```json
{
  "name": "file_search",
  "description": "在允许目录下检索文件内容并返回命中片段",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "搜索关键词"
      },
      "root_dir": {
        "type": "string",
        "description": "根目录（可选，默认 ./data）"
      },
      "limit": {
        "type": "integer",
        "description": "最大返回条数（默认 20）"
      }
    },
    "required": ["query"]
  }
}
```

### 2. LLM Client（模型客户端）

**职责：**
- 封装不同 LLM 提供商的 API 调用
- 支持 Function Calling
- 处理模型响应和工具调用请求
- Token 限制管理

**优先支持的提供商：**
- ✅ **DashScope/Qwen** (qwen-turbo, qwen-plus) - Function Calling
- ✅ **OpenAI** (gpt-3.5-turbo, gpt-4) - 原生 Function Calling
- ⏳ Anthropic Claude - Tools API (Phase 2)

**关键方法：**
```python
class LLMClient:
    def chat(
        messages: List[Message], 
        tools: List[ToolSchema],
        max_tokens: Optional[int] = None
    ) -> LLMResponse
    
    def supports_function_calling(self) -> bool
```

**Token 限制：**
- 输入 token 限制（根据模型能力）
- 输出 token 限制（防止过长响应）
- 总 token 限制（单次对话）

### 3. Agent Loop（代理循环）

**职责：**
- 管理多轮对话
- 处理模型返回的工具调用请求
- **Pydantic 校验工具调用参数**
- **错误反馈和自动修正**
- 执行工具并反馈结果
- 控制循环终止条件（Token 限制、工具调用次数限制）

**流程：**
```
1. 用户输入 → Agent
2. Agent → LLM (携带工具列表)
3. LLM 响应：
   - 如果返回工具调用：
     a. Pydantic 校验参数格式
     b. 如果格式错误 → 反馈错误给 LLM → 回到步骤 2
     c. 如果格式正确 → 执行工具 → 将结果反馈给 LLM → 回到步骤 2
   - 如果返回最终答案 → 返回给用户
4. 重复直到：
   - LLM 返回最终答案
   - 达到最大工具调用次数
   - 达到 Token 限制
   - 超时
```

**关键方法：**
```python
class Agent:
    def chat(
        user_input: str,
        conversation_id: Optional[str] = None,
        max_tool_calls: int = 5,
        max_tokens: int = 2000
    ) -> AgentResponse
    
    def _validate_tool_call(tool_call: ToolCall) -> ValidationResult
    def _execute_tool_call(tool_call: ToolCall) -> ToolResult
    def _should_continue(response: LLMResponse) -> bool
    def _format_validation_error(error: ValidationError) -> str
```

### 4. API 服务层

**职责：**
- 提供 HTTP API 接口
- 管理对话会话
- 处理请求和响应
- 集成到 FastAPI Skill Host

**端点设计：**
- `POST /agent/chat` - 主要对话接口
- `GET /agent/conversations/{id}` - 获取对话历史（可选）
- `DELETE /agent/conversations/{id}` - 删除对话（可选）

**集成方式：**
- 作为 FastAPI 的路由模块添加到 `src/app.py`
- 或独立的 FastAPI 应用（推荐：集成到现有应用）

---

## 实现方案对比

### 方案 A：完全依赖 LLM Function Calling（推荐）

**优点：**
- 利用 LLM 的智能决策能力
- 无需手动编写路由规则
- 支持复杂场景和上下文理解

**实现：**
1. 将所有 skills 转换为 Function Calling Schema
2. 在每次 LLM 调用时传入工具列表
3. LLM 自主决定调用哪个工具
4. Agent 执行工具调用并反馈结果

**适用场景：**
- 复杂任务
- 需要多工具协作
- 需要上下文理解

### 方案 B：规则路由 + LLM 增强

**优点：**
- 简单场景快速响应
- 可预测性强
- 成本较低

**实现：**
1. 简单场景使用规则路由
2. 复杂场景回退到 LLM Function Calling

**适用场景：**
- 简单明确的指令
- 成本敏感场景

---

## 数据流设计

### 单次工具调用流程

```
User Input
    ↓
Agent.chat()
    ↓
LLMClient.chat(messages, tools)
    ↓
LLM Response (tool_call: file_search)
    ↓
Agent._execute_tool_call()
    ↓
ToolManager.invoke_tool()
    ↓
HTTP POST → Skill Host
    ↓
NormalizedSkillResult
    ↓
Agent 将结果加入对话历史
    ↓
LLMClient.chat(messages + tool_result)
    ↓
LLM Response (final_answer)
    ↓
返回给用户
```

### 多轮工具调用流程

```
Round 1:
  User: "搜索包含 'openSkill' 的文件"
  → LLM: tool_call(file_search, {query: "openSkill"})
  → Tool Result: [file1.md, file2.md]
  
Round 2:
  → LLM: tool_call(file_search, {query: "openSkill", root_dir: "./data/docs"})
  → Tool Result: [file1.md]
  
Round 3:
  → LLM: "找到了 file1.md，内容包含..."
  → Final Answer
```

---

## 关键设计决策

### 1. Skill Manifest → Function Schema 转换

**需要的信息：**
- Skill ID
- Skill 描述（从 manifest 或文档）
- 输入参数 Schema
- 输出格式说明

**实现位置：**
- `src/agent/tool_manager.py` 或 `src/agent/schema_generator.py`

### 2. 工具描述来源

**选项：**
- A. 从 `documents/agents.md` 的 Skills Catalog 读取
- B. 从 Skill Manifest 的 `description` 字段读取
- C. 从 Skill 脚本的 docstring 读取
- D. 组合使用（优先级：manifest > docstring > 文档）

**推荐：** 选项 D（组合使用，有优先级）

### 3. Agent 实现位置

**选项：**
- A. 独立模块 `src/agent/`
- B. 作为 Skill Host 的一部分（新增路由）
- C. 独立的 Agent 服务

**推荐：** 选项 A（独立模块，可单独运行）

### 4. 对话历史管理

**需要存储：**
- 用户消息
- LLM 响应
- 工具调用记录
- 工具执行结果

**实现：**
- 使用 `List[Message]` 结构
- 支持上下文窗口限制
- 支持 trace_id 关联

---

## 证明模型自主调用工具的方式

### 测试场景设计

#### 场景 1：简单工具调用
```
用户: "echo hello"
预期: LLM 调用 echo skill，返回 "hello"
```

#### 场景 2：需要多步工具调用
```
用户: "搜索包含 'calculator' 的文件，然后计算 [1,2,3,4,5] 的平均值"
预期: 
  1. LLM 调用 file_search
  2. 根据结果，LLM 调用 calculator
  3. 返回最终答案
```

#### 场景 3：工具选择决策
```
用户: "帮我分析一下 data/logs/app.log"
预期: LLM 自主选择 log_transform skill
```

#### 场景 4：错误处理和重试
```
用户: "搜索不存在的文件"
预期: LLM 收到错误后，理解错误并给出合理回复
```

### 验证指标

1. **工具调用准确率**
   - LLM 是否选择了正确的工具
   - 参数是否正确传递

2. **多轮调用能力**
   - 能否根据工具结果继续调用
   - 能否组合多个工具

3. **错误处理**
   - 工具失败后的处理
   - 能否理解错误并调整策略

4. **最终答案质量**
   - 是否有效利用工具结果
   - 答案是否准确完整

---

## 实现优先级

### Phase 1: 基础 Agent（MVP）
1. ✅ Tool Manager - 工具发现和 Schema 生成
2. ✅ LLM Client - 单一提供商（如 OpenAI）
3. ✅ Agent Loop - 单轮工具调用
4. ✅ 简单测试场景

### Phase 2: 增强功能
1. 多轮工具调用
2. 多 LLM 提供商支持
3. 错误处理和重试
4. 对话历史管理

### Phase 3: 高级特性
1. 工具调用优化（并行调用）
2. 成本控制（token 限制）
3. 缓存机制
4. 性能监控

---

## 技术选型

### LLM SDK
- **OpenAI**: `openai` 官方库
- **Anthropic**: `anthropic` 官方库
- **DashScope**: `dashscope` 官方库

### 依赖管理
- 添加到 `requirements.txt`
- 可选依赖（根据配置的提供商安装）

### 代码组织
```
src/
├── agent/                    # Agent 相关代码
│   ├── __init__.py
│   ├── client.py             # LLM Client (OpenAI, Qwen)
│   ├── tool_manager.py      # Tool Manager
│   ├── agent.py              # Agent Loop
│   ├── validator.py          # Pydantic 校验器
│   ├── schemas/              # Pydantic 模型定义
│   │   ├── __init__.py
│   │   ├── echo.py
│   │   ├── file_search.py
│   │   ├── calculator.py
│   │   └── log_transform.py
│   └── api.py                # FastAPI 路由
├── ... (现有代码)
```

---

## 已确认的设计决策

### 1. Agent 运行模式
✅ **API 服务**
- 作为 FastAPI 的扩展路由添加到 Skill Host
- 提供统一的 HTTP API 接口
- 支持异步处理

### 2. 工具描述详细程度
✅ **简单描述**
- 从 Skill Manifest 和文档中提取简洁描述
- 包含必要的参数说明
- 不包含详细示例（减少 token 消耗）

### 3. 成本控制
✅ **Token 限制**
- 设置最大 token 数（输入+输出）
- 工具调用次数限制
- 超时控制

### 4. 实现方案
✅ **完全依赖 LLM Function Calling**
- 使用方案 A
- LLM 自主决策工具调用
- 支持多轮工具调用

### 5. 工具调用格式校验
✅ **Pydantic 校验 + 自动修正**
- 使用 Pydantic 模型校验工具调用参数
- 如果格式不符合，将错误信息反馈给 LLM
- LLM 根据错误信息修正并重试

### 6. LLM 提供商优先级
✅ **优先支持 Qwen 和 OpenAI**
- Phase 1: OpenAI (gpt-3.5-turbo, gpt-4)
- Phase 1: DashScope/Qwen (qwen-turbo, qwen-plus)
- Phase 2: Anthropic Claude

### 7. 测试用例
✅ **根据工具决定**
- 为每个已实现的 skill 设计测试场景
- 包含单工具和多工具组合场景

---

## 工具调用格式校验流程

### 校验机制设计

```
LLM Response (tool_call)
    ↓
Pydantic 模型校验
    ↓
┌─────────────────┐
│ 格式正确？      │
└────┬───────┬────┘
     │       │
   是│       │否
     │       │
     │       ↓
     │   提取错误信息
     │       │
     │       ↓
     │   反馈给 LLM
     │       │
     │       ↓
     │   LLM 修正
     │       │
     └───────┘
         │
         ↓
    执行工具调用
```

### Pydantic 校验实现

**示例：**
```python
from pydantic import BaseModel, ValidationError

class FileSearchInput(BaseModel):
    query: str
    root_dir: Optional[str] = None
    limit: Optional[int] = 20

def validate_tool_call(tool_name: str, arguments: dict) -> tuple[bool, Optional[str]]:
    """校验工具调用参数格式"""
    try:
        if tool_name == "file_search":
            FileSearchInput(**arguments)
            return True, None
        # ... 其他工具
    except ValidationError as e:
        error_msg = format_validation_error(e)
        return False, error_msg
```

### 错误反馈格式

**反馈给 LLM 的消息：**
```
工具调用参数格式错误：
- query: 字段是必需的（缺失）
- limit: 必须是整数（当前值: "20"）

请修正参数后重试。
```

---

## API 服务设计

### Agent API 端点

#### POST /agent/chat
**请求：**
```json
{
  "message": "搜索包含 calculator 的文件",
  "conversation_id": "optional-conversation-id",
  "max_tool_calls": 5,
  "max_tokens": 2000
}
```

**响应：**
```json
{
  "success": true,
  "response": "找到了以下文件...",
  "conversation_id": "conv-123",
  "trace_id": "trace-456",
  "tool_calls": [
    {
      "tool": "file_search",
      "arguments": {"query": "calculator"},
      "result": {...}
    }
  ],
  "meta": {
    "total_tokens": 1500,
    "tool_calls_count": 1,
    "latency_ms": 2500
  }
}
```

### 对话管理

**存储结构：**
- 使用 `conversation_id` 关联多轮对话
- 在内存或 Redis 中存储对话历史
- 支持上下文窗口限制

---

## 实现计划

### Phase 1: 核心功能（MVP）

#### 1.1 Tool Manager
- [ ] Skill Manifest → Function Schema 转换
- [ ] 从 Registry 获取可用工具
- [ ] 生成简单的工具描述

#### 1.2 LLM Client (OpenAI + Qwen)
- [ ] OpenAI Client 封装
- [ ] DashScope/Qwen Client 封装
- [ ] Function Calling 支持
- [ ] 统一接口抽象

#### 1.3 Pydantic 校验层
- [ ] 为每个 skill 定义 Pydantic 模型
- [ ] 参数校验函数
- [ ] 错误格式化函数

#### 1.4 Agent Loop
- [ ] 单轮工具调用
- [ ] 工具调用格式校验
- [ ] 错误反馈和重试机制
- [ ] Token 限制

#### 1.5 API 端点
- [ ] POST /agent/chat
- [ ] 对话历史管理
- [ ] 错误处理

### Phase 2: 增强功能

- [ ] 多轮工具调用
- [ ] 工具调用次数限制
- [ ] 对话历史持久化
- [ ] 性能优化

---

## 测试场景设计

### Echo Skill
- ✅ 简单调用："echo hello"
- ✅ 验证：LLM 正确调用 echo，参数格式正确

### File Search Skill
- ✅ 单次调用："搜索包含 'calculator' 的文件"
- ✅ 带参数："在 ./data/docs 目录下搜索 'openSkill'，最多返回 5 条"
- ✅ 验证：LLM 正确构建参数，Pydantic 校验通过

### Calculator Skill
- ✅ 单次调用："计算 [1,2,3,4,5] 的平均值"
- ✅ 多操作："计算 [10,20,30] 的平均值、最大值和最小值"
- ✅ 验证：参数格式正确，计算结果准确

### 多工具组合
- ✅ "搜索包含 'calculator' 的文件，然后计算文件中数字的平均值"
- ✅ 验证：LLM 依次调用多个工具，正确传递参数

### 格式校验测试
- ✅ 故意传入错误格式，验证 Pydantic 校验
- ✅ 验证 LLM 能够根据错误信息修正
- ✅ 验证重试机制

---

## 技术实现细节

### Pydantic 模型定义位置

```
src/agent/
├── schemas/
│   ├── __init__.py
│   ├── echo.py          # EchoInput, EchoOutput
│   ├── file_search.py   # FileSearchInput, FileSearchOutput
│   ├── calculator.py    # CalculatorInput, CalculatorOutput
│   └── log_transform.py # LogTransformInput, LogTransformOutput
```

### LLM Client 接口设计

```python
class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        tools: List[ToolSchema],
        max_tokens: Optional[int] = None
    ) -> LLMResponse
    
    @abstractmethod
    def supports_function_calling(self) -> bool
```

### Agent Loop 核心逻辑

```python
class Agent:
    def chat(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        max_tool_calls: int = 5,
        max_tokens: int = 2000
    ) -> AgentResponse:
        # 1. 获取对话历史
        # 2. 获取可用工具
        # 3. 调用 LLM
        # 4. 检查工具调用
        # 5. Pydantic 校验
        # 6. 执行工具或反馈错误
        # 7. 重复直到完成
```

---

## 下一步行动

1. **创建 Agent 模块结构**
   - `src/agent/` 目录
   - 基础文件结构

2. **实现 Tool Manager**
   - Skill → Function Schema 转换
   - 工具描述生成

3. **实现 LLM Client**
   - OpenAI Client
   - DashScope/Qwen Client

4. **实现 Pydantic 校验**
   - 为每个 skill 定义模型
   - 校验和错误格式化

5. **实现 Agent Loop**
   - 核心对话循环
   - 工具调用执行
   - 错误处理和重试

6. **添加 API 端点**
   - POST /agent/chat
   - 集成到 FastAPI

7. **编写测试**
   - 为每个工具设计测试场景
   - 格式校验测试

