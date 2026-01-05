# Changelog

## [0.1.1] - 优化版本

### 新增功能

1. **工具函数模块** (`src/utils.py`)
   - 添加日志格式化工具
   - 添加 JSON 安全解析函数
   - 添加延迟计算工具
   - 添加字符串截断工具
   - 添加版本获取函数

2. **中间件支持** (`src/middleware.py`)
   - 请求/响应日志记录中间件
   - 自动添加处理时间 header (`X-Process-Time-Ms`)

3. **配置管理增强** (`src/config.py`)
   - 支持从 `.env` 文件加载配置（使用 python-dotenv）
   - 添加 `has_llm_config()` 方法检查 LLM 配置
   - 添加 `get_llm_providers()` 方法获取已配置的 LLM 提供商列表

4. **日志系统优化** (`src/app.py`, `src/utils.py`)
   - 改进日志格式，包含 trace_id
   - 添加结构化日志支持
   - 使用 ContextVar 管理 trace_id

5. **API 文档改进**
   - 添加 API 标签分组（skills, system）
   - 改进端点描述
   - 健康检查端点返回更多信息

### 改进

1. **错误处理**
   - 统一使用 `format_latency_ms()` 计算延迟
   - 统一使用 `get_version()` 获取版本号

2. **代码质量**
   - 改进类型提示
   - 添加更详细的文档字符串
   - 优化导入顺序

3. **依赖管理**
   - 添加 `python-dotenv` 作为可选依赖

### 修复

- 修复日志重复配置问题
- 修复版本号硬编码问题

## [0.1.0] - 初始版本

- 初始框架实现
- FastAPI Skill Host
- CLI Python Runner
- Skill Registry
- 基础配置管理

