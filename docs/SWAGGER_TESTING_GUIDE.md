# 使用 Swagger UI 测试 Agent API

## 访问 Swagger UI

1. **确保服务正在运行**
   ```bash
   ./scripts/start-macos.sh
   ```

2. **打开 Swagger UI**
   - 浏览器访问：http://127.0.0.1:8000/docs
   - 或者访问：http://127.0.0.1:8000/redoc（ReDoc 格式）

## 测试 Agent API

### 1. 找到 Agent API 端点

在 Swagger UI 中，找到 **`POST /agent/chat`** 端点（在 `agent` 标签下）

### 2. 点击 "Try it out"

点击端点旁边的 **"Try it out"** 按钮

### 3. 填写请求参数

#### 基本请求示例（计算平均数）

```json
{
  "message": "计算这些数字的平均数: 1,2,5,6.7,3.3,9",
  "provider": "qwen",
  "max_tool_calls": 5,
  "max_tokens": 2000,
  "temperature": 0.7
}
```

#### 完整参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | ✅ | - | 用户消息 |
| `provider` | string | ❌ | "openai" | LLM 提供商：`openai` 或 `qwen` |
| `model` | string | ❌ | null | 模型名称（可选，使用默认值） |
| `conversation_id` | string | ❌ | null | 对话 ID（用于多轮对话） |
| `max_tool_calls` | integer | ❌ | 5 | 最大工具调用次数（1-10） |
| `max_tokens` | integer | ❌ | 2000 | 最大 token 数（100-8000） |
| `temperature` | number | ❌ | 0.7 | 温度参数（0.0-2.0） |
| `max_validation_retries` | integer | ❌ | 3 | 最大验证重试次数（0-5） |

### 4. 设置 Header（可选）

如果需要设置 `X-Trace-Id`：
- 在 Swagger UI 中找到 **"Headers"** 部分
- 添加：`X-Trace-Id: my-test-123`

### 5. 执行请求

点击 **"Execute"** 按钮

### 6. 查看响应

响应示例：

```json
{
  "success": true,
  "response": "这些数字的平均数是 4.5。",
  "conversation_id": "conv-xxx",
  "trace_id": "xxx",
  "tool_calls": [
    {
      "tool": "calculator",
      "arguments": {
        "numbers": [1.0, 2.0, 5.0, 6.7, 3.3, 9.0],
        "ops": ["mean"]
      },
      "validated": true,
      "result": {
        "success": true,
        "skill_id": "calculator",
        "data": {
          "results": {
            "mean": 4.5
          }
        }
      }
    }
  ],
  "meta": {
    "provider": "qwen",
    "model": "qwen-turbo",
    "total_tokens": 1847,
    "tool_calls_count": 1,
    "validation_retries": 0,
    "latency_ms": 1756
  }
}
```

## 测试用例示例

### 1. 测试 Echo 工具

```json
{
  "message": "echo hello world",
  "provider": "qwen"
}
```

### 2. 测试 Calculator - 计算平均数

```json
{
  "message": "计算这些数字的平均数: 1,2,5,6.7,3.3,9",
  "provider": "qwen"
}
```

### 3. 测试 Calculator - 多个操作

```json
{
  "message": "计算 [10, 20, 30, 40, 50] 的平均数、中位数、最大值和最小值",
  "provider": "qwen"
}
```

### 4. 测试 Calculator - 比较大小

```json
{
  "message": "比较 10 和 20 的大小",
  "provider": "qwen"
}
```

### 5. 多轮对话

**第一轮：**
```json
{
  "message": "计算 [1, 2, 3] 的平均数",
  "provider": "qwen",
  "conversation_id": "my-conv-123"
}
```

**第二轮（使用相同的 conversation_id）：**
```json
{
  "message": "那最大值是多少？",
  "provider": "qwen",
  "conversation_id": "my-conv-123"
}
```

## 常见问题

### Q: 如何查看可用的工具？

访问：http://127.0.0.1:8000/
查看 `skills` 字段，会列出所有可用的工具。

### Q: 如何查看 API 文档？

- Swagger UI：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

### Q: 如何测试其他工具？

直接修改 `message` 字段，让 LLM 理解你的意图：
- Echo: `"echo hello"`
- Calculator: `"计算 [1,2,3] 的平均数"`
- File Search: `"搜索包含 'test' 的文件"`（如果已实现）
- Log Transform: `"转换日志文件"`（如果已实现）

### Q: 如何查看请求/响应详情？

在 Swagger UI 中：
1. 执行请求后，查看 **"Responses"** 部分
2. 查看 **"Server response"** 获取完整响应
3. 查看 **"curl"** 获取等效的 curl 命令

### Q: 如何调试错误？

1. 查看响应中的 `success` 字段
2. 如果 `success: false`，查看 `error` 字段
3. 查看 `meta` 字段中的 `error` 信息
4. 检查服务日志（终端输出）

## 提示

1. **使用自然语言**：Agent 会理解你的意图并自动选择合适的工具
2. **查看 tool_calls**：响应中的 `tool_calls` 字段显示了 Agent 调用了哪些工具
3. **多轮对话**：使用 `conversation_id` 可以保持对话上下文
4. **调整参数**：可以调整 `temperature`、`max_tokens` 等参数来影响 LLM 行为

