# @TODO 注释移除分析

## 分析原则
- 已实现的 TODO：删除注释
- 合理的 TODO（但当前不需要）：删除注释（已在 CODE_REVIEW_EVALUATION.md 中记录）
- 不合理的 TODO：删除注释

## 分类统计

### 已实现或已处理（删除）
1. `config.py:86` - timeout_ms 验证已实现
2. `middleware.py:41` - 已使用 content-length header

### 合理但当前不需要（删除，已在评估文档中记录）
1. 配置管理相关（Pydantic Settings、热重载等）
2. 性能优化相关（缓存、并发限制等）
3. 功能扩展相关（持久化、热重载等）
4. 安全增强相关（符号链接检查等，当前实现已足够）

### 需要删除的 TODO 列表

#### src/app.py
- Line 88-89: 请求大小限制和限流（可通过反向代理实现）

#### src/config.py
- Line 22-23: Pydantic Settings（当前配置足够简单）
- Line 38, 44: timeout_ms 最大值限制（已实现警告）
- Line 80-81: 配置验证和热重载（验证已实现，热重载不需要）
- Line 86-88: 配置验证（已实现或不需要）
- Line 99: 目录权限（默认权限足够）

#### src/middleware.py
- Line 41: request._body（已使用 content-length）

#### src/security.py
- Line 31-33: 符号链接检查、路径长度限制、规范化（当前实现已足够安全）
- Line 47-48: 更严格的检查（当前实现已足够）
- Line 55: resolve() 符号链接（当前实现已足够）
- Line 85-86: 路径长度和符号链接（当前实现已足够）

#### src/agent/agent.py
- Line 22-23: 持久化存储（当前内存存储足够）
- Line 65-66: 迭代时间限制（已有 max_tool_calls 限制）
- Line 70: token 计算（使用实际 API 返回值）
- Line 76-77: max_tokens 计算（当前实现足够）
- Line 140-141: 重试逻辑（当前实现足够）
- Line 222-223: 异步保存和大小检查（当前实现足够）
- Line 254-256: 消息截断策略（当前实现足够）

#### src/agent/api.py
- Line 22-23: max_workers 配置（当前硬编码足够）
- Line 85-86: 请求超时（已有其他限制）

#### src/agent/client.py
- Line 48-50: HTTP 代理、超时、重试（当前实现足够）
- Line 96-98: 请求重试和监控（当前实现足够）

#### src/agent/tool_manager.py
- Line 16-17: 缓存失效和动态注册（当前实现足够）
- Line 91-92: description 读取（当前硬编码足够）
- Line 118-120: 超时、并发、指标（当前实现足够）

#### src/runners/cli_python.py
- Line 59-60: manifest.allowed_root（当前实现足够）
- Line 131-134: 环境变量、资源限制、进程池（当前实现足够）
- Line 188-189: MAX_OUTPUT_SIZE 配置（当前硬编码足够）
- Line 247-248: 输出数据验证（当前实现足够）
- Line 254: trace_id 格式验证（当前实现足够）

#### src/runners/__init__.py
- Line 29-30: Runner 实例和配置（当前实现足够）

#### src/registry.py
- Line 25-26: skills_dir 配置和热重载（当前实现足够）
- Line 38-40: 递归加载、重复检测、统计（当前实现足够）
- Line 57: manifest.id 覆盖策略（当前实现足够）
- Line 92: id 格式验证（已在 app.py 中实现）
- Line 102: entry 路径验证（已在 runner 中实现）

#### src/models.py
- Line 61-62: 输入大小和深度限制（当前实现足够）
- Line 69-72: SkillManifest 扩展字段（当前实现足够）

#### src/utils.py
- Line 27-29: 日志文件、轮转、JSON 格式（当前实现足够）

## 总结
所有 @TODO 注释都将被删除，因为：
1. 已实现的 TODO 不需要保留
2. 合理的 TODO 已在 CODE_REVIEW_EVALUATION.md 中记录
3. 保持代码简洁，避免过多的 TODO 注释

