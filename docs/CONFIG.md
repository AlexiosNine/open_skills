# 配置读取机制说明

## 概述

配置系统采用**环境变量优先**的方式，支持从多个来源读取配置，优先级从高到低如下：

1. **系统环境变量**（最高优先级）
2. **`.env` 文件**（如果 python-dotenv 可用）
3. **默认值**（代码中定义）

## 配置读取流程

### 1. 初始化阶段

当 `src/config.py` 模块被导入时，会执行以下步骤：

```python
# 步骤 1: 尝试加载 .env 文件（如果 python-dotenv 可用）
try:
    from dotenv import load_dotenv
    load_dotenv()  # 从当前目录或父目录查找 .env 文件
except ImportError:
    pass  # python-dotenv 是可选的

# 步骤 2: 创建全局配置实例
config = Config()  # 在模块导入时立即创建
```

### 2. Config 类初始化

`Config.__init__()` 方法会：

1. **读取环境变量**：使用 `os.getenv()` 读取环境变量
2. **应用默认值**：如果环境变量不存在，使用默认值
3. **类型转换**：将字符串转换为适当类型（int, bool, Path）
4. **路径解析**：使用 `Path.resolve()` 解析相对路径为绝对路径
5. **验证配置**：调用 `_validate()` 验证必需路径是否存在

### 3. 配置读取示例

```python
# 读取环境变量，如果不存在则使用默认值
self.http_base_url: str = os.getenv(
    "OPENSKILL_HTTP_BASE_URL",  # 环境变量名
    "http://127.0.0.1:8000"      # 默认值
)

# 读取路径并解析为绝对路径
self.cli_dir: Path = Path(
    os.getenv("OPENSKILL_CLI_DIR", "./skill_cli")
).resolve()  # 转换为绝对路径

# 类型转换
self.timeout_ms: int = int(os.getenv("OPENSKILL_TIMEOUT_MS", "15000"))
self.debug: bool = os.getenv("OPENSKILL_DEBUG", "0") == "1"
```

## 配置来源

### 方式 1: 系统环境变量（推荐用于生产环境）

```bash
# Linux/macOS
export OPENSKILL_HTTP_BASE_URL=http://0.0.0.0:8000
export OPENSKILL_DEBUG=1
export OPENAI_API_KEY=sk-...

# Windows
set OPENSKILL_HTTP_BASE_URL=http://0.0.0.0:8000
set OPENSKILL_DEBUG=1
```

### 方式 2: .env 文件（推荐用于开发环境）

创建 `.env` 文件（项目根目录）：

```bash
# 复制示例文件
cp env.example .env

# 编辑 .env 文件
OPENSKILL_HTTP_BASE_URL=http://127.0.0.1:8000
OPENSKILL_DEBUG=1
OPENAI_API_KEY=sk-...
```

**注意**：需要安装 `python-dotenv` 包才能使用 `.env` 文件：
```bash
pip install python-dotenv
```

### 方式 3: 默认值

如果环境变量和 `.env` 文件都不存在，使用代码中定义的默认值。

## 配置验证

配置初始化时会自动验证：

1. **路径存在性检查**：
   - `OPENSKILL_CLI_DIR` 必须存在且是目录
   - 如果不存在会抛出 `ValueError`

2. **自动创建目录**：
   - `OPENSKILL_ALLOWED_ROOT` 如果不存在会自动创建

## 全局单例模式

配置使用**全局单例模式**：

```python
# src/config.py
config = Config()  # 模块级别的全局实例

# 在其他模块中使用
from src.config import config

print(config.debug)  # 访问配置
```

**优点**：
- 整个应用共享同一配置实例
- 配置在应用启动时加载一次，性能好
- 避免重复读取环境变量

**注意**：配置在模块导入时加载，修改环境变量后需要重启应用才能生效。

## 配置访问

### 在代码中访问配置

```python
from src.config import config

# 访问基本配置
print(config.http_base_url)
print(config.debug)
print(config.timeout_ms)

# 访问路径配置
script_path = config.get_skill_script_path("echo")

# 检查 LLM 配置
if config.has_llm_config():
    providers = config.get_llm_providers()
    print(f"Configured providers: {providers}")

# 访问 LLM API 配置
if config.openai_api_key:
    print("OpenAI API is configured")
```

### 在 Skill 脚本中访问配置

```python
# skill_cli/my_skill.py
import sys
import json

# 注意：skill 脚本是独立进程，需要通过环境变量访问
import os
api_key = os.getenv("OPENAI_API_KEY")

# 或者通过 stdin 接收配置（如果 Skill Host 传递）
```

## 配置优先级示例

假设有以下配置来源：

1. **系统环境变量**：`OPENSKILL_DEBUG=1`
2. **.env 文件**：`OPENSKILL_DEBUG=0`
3. **默认值**：`OPENSKILL_DEBUG=0`（代码中）

**最终结果**：`config.debug = True`（系统环境变量优先级最高）

## 常见问题

### Q: 修改 .env 文件后配置没有生效？

A: 配置在模块导入时加载，需要重启应用才能生效。

### Q: 如何在不同环境使用不同配置？

A: 
1. **开发环境**：使用 `.env` 文件
2. **生产环境**：使用系统环境变量
3. **Docker**：通过 `docker-compose.yml` 或 `-e` 参数传递环境变量

### Q: 如何查看当前配置？

A: 可以通过健康检查端点查看：
```bash
curl http://127.0.0.1:8000/health
```

### Q: 配置验证失败怎么办？

A: 检查错误信息，确保：
- `OPENSKILL_CLI_DIR` 目录存在
- 路径有正确的权限
- 环境变量格式正确

## 配置项列表

### Skill Host 配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| OPENSKILL_HTTP_BASE_URL | str | http://127.0.0.1:8000 | Skill Host 基地址 |
| OPENSKILL_ALLOWED_ROOT | Path | ./data | 允许访问的根目录 |
| OPENSKILL_CLI_DIR | Path | ./skill_cli | CLI skills 目录 |
| OPENSKILL_TIMEOUT_MS | int | 15000 | 超时时间（毫秒） |
| OPENSKILL_DEBUG | bool | False | 调试模式 |

### LLM API 配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| OPENAI_API_KEY | str | None | OpenAI API 密钥 |
| OPENAI_API_BASE | str | https://api.openai.com/v1 | OpenAI API 基地址 |
| OPENAI_MODEL | str | gpt-3.5-turbo | OpenAI 模型名称 |
| ANTHROPIC_API_KEY | str | None | Anthropic API 密钥 |
| ANTHROPIC_API_BASE | str | https://api.anthropic.com | Anthropic API 基地址 |
| ANTHROPIC_MODEL | str | claude-3-sonnet-20240229 | Anthropic 模型名称 |
| DASHSCOPE_API_KEY | str | None | 阿里百炼 API 密钥 |
| DASHSCOPE_API_BASE | str | https://dashscope.aliyuncs.com/api/v1 | DashScope API 基地址 |
| DASHSCOPE_MODEL | str | qwen-turbo | DashScope 模型名称 |

