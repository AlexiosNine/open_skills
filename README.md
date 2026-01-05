# OpenSkill Skill Host - Local Demo

本地 Skill Host 实现，使用 FastAPI 提供统一的 HTTP 协议来调用和执行 skills。

## 快速开始

### 前置要求

- Python 3.10+（建议 3.11）
- macOS / Linux

**macOS 用户**：推荐使用 Homebrew 安装 Python
```bash
brew install python@3.11
```

### 安装依赖

**macOS 用户（推荐）**

```bash
# 安装系统依赖（可选，首次使用）
./scripts/install-macos-deps.sh

# 设置项目环境
./scripts/setup-macos.sh
```

**Linux/macOS 通用方式**

```bash
# 方式 1: 使用脚本
./setup.sh

# 方式 2: 手动安装

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 环境变量配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENSKILL_HTTP_BASE_URL | 否 | http://127.0.0.1:8000 | Skill Host 基地址（客户端使用） |
| OPENSKILL_ALLOWED_ROOT | 否 | ./data | 文件/日志类 skill 允许访问的根目录 |
| OPENSKILL_CLI_DIR | 否 | ./skill_cli | CLI skills 脚本所在目录 |
| OPENSKILL_TIMEOUT_MS | 否 | 15000 | 单次调用超时（毫秒） |
| OPENSKILL_DEBUG | 否 | 0 | 1 开启 debug 日志 |

### 大模型 API 配置（可选）

如果需要使用大模型 API，可以配置以下环境变量：

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENAI_API_KEY | 否 | - | OpenAI API 密钥 |
| OPENAI_API_BASE | 否 | https://api.openai.com/v1 | OpenAI API 基地址 |
| OPENAI_MODEL | 否 | gpt-3.5-turbo | OpenAI 模型名称 |
| ANTHROPIC_API_KEY | 否 | - | Anthropic Claude API 密钥 |
| ANTHROPIC_API_BASE | 否 | https://api.anthropic.com | Anthropic API 基地址 |
| ANTHROPIC_MODEL | 否 | claude-3-sonnet-20240229 | Anthropic 模型名称 |
| DASHSCOPE_API_KEY | 否 | - | 阿里百炼 DashScope API 密钥 |
| DASHSCOPE_API_BASE | 否 | https://dashscope.aliyuncs.com/api/v1 | DashScope API 基地址 |
| DASHSCOPE_MODEL | 否 | qwen-turbo | DashScope 模型名称（如 qwen-turbo, qwen-plus, qwen-max） |
| LLM_API_KEY | 否 | - | 通用 LLM API 密钥 |
| LLM_API_BASE | 否 | - | 通用 LLM API 基地址 |
| LLM_MODEL | 否 | - | 通用 LLM 模型名称 |
| LLM_PROVIDER | 否 | - | LLM 提供商（openai/anthropic/custom） |

### 启动服务

**macOS 用户（推荐）**

```bash
# 使用 macOS 优化脚本（自动打开浏览器）
./scripts/start-macos.sh
```

**Linux/macOS 通用方式**

```bash
# 方式 1: 使用启动脚本
./scripts/start.sh

# 方式 2: 手动启动

```bash
source .venv/bin/activate  # 如果虚拟环境未激活
uvicorn src.app:app --host 127.0.0.1 --port 8000
```

**方式 3: 使用 Python 模块方式**

```bash
source .venv/bin/activate
python -m src.app
```

### 调用示例

#### 测试 echo skill

**macOS 用户（推荐）**

```bash
# 使用 macOS 优化测试脚本（彩色输出）
./scripts/test-macos.sh [trace_id] [text]
# 示例:
./scripts/test-macos.sh test-123 hello
```

**Linux/macOS 通用方式**

```bash
# 方式 1: 使用测试脚本
./scripts/test_echo.sh [trace_id] [text]
# 示例:
./scripts/test_echo.sh test-123 hello

# 方式 2: 使用 curl

```bash
curl -X POST "http://127.0.0.1:8000/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: test-123" \
  -d '{"input": {"text": "hello"}}'
```

预期响应：

```json
{
  "success": true,
  "skill_id": "echo",
  "trace_id": "test-123",
  "data": {
    "echoed": "hello"
  },
  "error": null,
  "meta": {
    "latency_ms": 3,
    "version": "0.1.0"
  }
}
```

#### 查看可用 skills

```bash
curl http://127.0.0.1:8000/
```

#### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

## 项目结构

```
skill_demo/
├── src/                    # 核心代码
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── security.py        # 路径安全验证
│   ├── registry.py        # Skill Registry
│   ├── utils.py           # 工具函数
│   ├── middleware.py      # FastAPI 中间件
│   ├── runners/           # Runner 实现
│   │   ├── __init__.py    # Runner Factory
│   │   ├── base.py        # Runner 基类
│   │   └── cli_python.py  # CLI Python Runner
│   └── app.py             # FastAPI 应用
├── skill_cli/             # Skill 脚本目录
│   └── echo.py           # echo skill（已实现）
├── skills/                # Skill manifests
│   ├── echo.yaml
│   ├── calculator.yaml
│   ├── file_search.yaml
│   └── log_transform.yaml
├── scripts/               # 脚本文件
│   ├── start.sh          # 启动脚本（Linux/macOS）
│   ├── start.bat          # 启动脚本（Windows）
│   └── test_echo.sh       # 测试脚本
├── data/                  # 允许访问的数据目录
├── requirements.txt       # Python 依赖
├── env.example           # 环境变量示例
├── setup.sh              # 安装脚本（Linux/macOS）
├── setup.bat             # 安装脚本（Windows）
├── README.md             # 本文档
└── CHANGELOG.md          # 更新日志
```

## 架构说明

### 调用流程

1. Client/Agent → Skill Host: `POST /skills/{id}:invoke`
2. Skill Host 读取 `X-Trace-Id` header（缺失则生成）
3. Skill Host 从 Registry 查找 skill manifest
4. RunnerFactory 根据 manifest 选择 Runner
5. Runner 执行 skill（当前为 CLI Python）
6. Runner 适配结果为 Normalized Skill Result
7. Skill Host 返回结果并记录日志

### 统一返回格式

所有 skill 返回 **Normalized Skill Result**：

```json
{
  "success": boolean,
  "skill_id": string,
  "trace_id": string,
  "data": object | null,
  "error": {
    "code": string,
    "message": string,
    "details": object (optional)
  } | null,
  "meta": {
    "latency_ms": number,
    "version": string,
    "truncated": boolean (optional)
  }
}
```

### 安全策略

- 所有文件访问限制在 `OPENSKILL_ALLOWED_ROOT` 目录下（默认 `./data`）
- 拒绝绝对路径和包含 `..` 的路径
- 路径规范化后验证是否在允许目录内

## 开发指南

### 添加新的 Skill

1. 创建 Python 脚本：`skill_cli/{skill_id}.py`
2. 脚本从 stdin 读取 JSON：`{ "input": { ... } }`
3. 脚本向 stdout 输出 JSON：Normalized Skill Result
4. 创建 manifest：`skills/{skill_id}.yaml`
5. 重启服务以加载新 skill

### Skill 脚本约定

- **stdin**: 固定输入 JSON `{ "input": { ... } }`
- **stdout**: 严格只输出 JSON（Normalized Skill Result）
- **stderr**: 推荐也只输出 JSON（用于错误）
- **exit code**: `0` 表示成功，非 `0` 表示失败

## Docker 部署

### 构建镜像

**方式 1: 使用脚本（推荐）**

```bash
./scripts/build-docker.sh
```

**方式 2: 手动构建**

```bash
docker build -t openskill-host:latest .
```

**方式 3: 指定标签**

```bash
docker build -t openskill-host:v0.1.0 .
```

### 运行容器

**方式 1: 使用 docker-compose（推荐）**

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**方式 2: 直接运行**

```bash
docker run -d \
  --name openskill-host \
  -p 8000:8000 \
  -e OPENSKILL_DEBUG=1 \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/data:/app/data \
  openskill-host:latest
```

### 环境变量配置

在 `docker-compose.yml` 中配置环境变量，或使用 `-e` 参数：

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e DASHSCOPE_API_KEY=sk-... \
  openskill-host:latest
```

### 数据持久化

使用 volume 挂载数据目录：

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  openskill-host:latest
```

## Agent API（模型自主调用工具）

### 快速开始

Agent API 允许 LLM 自主调用可用的 tools（skills）。

**前提条件：**
- 配置 LLM API 密钥（OpenAI 或 DashScope/Qwen）
- Skill Host 服务正在运行

**调用示例：**

```bash
curl -X POST "http://127.0.0.1:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: agent-test-123" \
  -d '{
    "message": "echo hello",
    "provider": "openai",
    "max_tool_calls": 5,
    "max_tokens": 2000
  }'
```

**使用测试脚本：**

```bash
# 使用 OpenAI
./test/test_agent.sh openai "echo hello"

# 使用 Qwen
./test/test_agent.sh qwen "echo hello"
```

### API 端点

#### POST /agent/chat

**请求体：**
```json
{
  "message": "用户消息",
  "conversation_id": "可选，用于多轮对话",
  "provider": "openai" | "qwen",
  "model": "可选，模型名称",
  "max_tool_calls": 5,
  "max_tokens": 2000,
  "temperature": 0.7,
  "max_validation_retries": 3
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
      "tool": "echo",
      "arguments": {"text": "hello"},
      "validated": true,
      "result": {...}
    }
  ],
  "meta": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "total_tokens": 150,
    "tool_calls_count": 1,
    "validation_retries": 0,
    "latency_ms": 1200
  }
}
```

### 特性

1. **自动工具发现**：Agent 自动发现所有可用的 skills
2. **格式校验**：使用 Pydantic 校验工具调用参数
3. **自动修正**：参数格式错误时，LLM 会根据错误信息自动修正
4. **多轮工具调用**：支持 LLM 连续调用多个工具
5. **Token 限制**：可配置 token 和工具调用次数限制

## 测试

### 快速测试

**运行所有测试：**

```bash
# 确保服务正在运行
./scripts/start-macos.sh  # macOS
# 或
./scripts/start.sh        # Linux

# 在另一个终端运行测试
./test/run_all_tests.sh
```

**单独运行测试：**

```bash
# API 完整测试
./test/test_api.sh

# 集成测试
./test/test_integration.sh

# Echo skill 专项测试
./test/test_echo_skill.sh

# macOS 优化测试脚本
./scripts/test-macos.sh
```

### 手动测试

**健康检查：**
```bash
curl http://127.0.0.1:8000/health
```

**测试 echo skill：**
```bash
curl -X POST "http://127.0.0.1:8000/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: test-123" \
  -d '{"input": {"text": "hello"}}'
```

更多测试说明请参考 [`test/README.md`](test/README.md)

## 故障排查

### Skill Host 无法启动

- 检查 Python 版本（需要 3.10+）
- 检查依赖是否安装：`pip install -r requirements.txt`
- 检查 `OPENSKILL_CLI_DIR` 目录是否存在

### Skill 调用失败

- 检查 skill manifest 是否正确加载：`curl http://127.0.0.1:8000/`
- 检查 skill 脚本是否存在且可执行
- 查看服务日志（设置 `OPENSKILL_DEBUG=1` 获取详细日志）

### 路径被拒绝（FORBIDDEN_PATH）

- 确保所有路径位于 `./data` 目录下
- 检查路径是否包含 `..` 或为绝对路径

### Docker 相关问题

- **镜像构建失败**：检查 Dockerfile 和依赖
- **容器无法启动**：查看日志 `docker logs openskill-host`
- **端口被占用**：修改 `docker-compose.yml` 中的端口映射

## 许可证

（待补充）

