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
