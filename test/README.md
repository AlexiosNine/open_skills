# 测试指南

本目录包含各种测试脚本，用于验证 OpenSkill Skill Host 的功能。

## 快速开始

### 1. 启动服务

在运行测试之前，确保服务正在运行：

```bash
# macOS
./scripts/start-macos.sh

# Linux
./scripts/start.sh
```

### 2. 运行测试

#### 基础 API 测试

```bash
# macOS (彩色输出)
./scripts/test-macos.sh

# Linux/macOS 通用
./scripts/test_echo.sh
```

#### 完整测试套件

```bash
# 运行所有测试
./test/test_api.sh

# 运行集成测试
./test/test_integration.sh

# 运行 echo skill 专项测试
./test/test_echo_skill.sh
```

## 测试脚本说明

### `test_api.sh` - 完整 API 测试

测试所有 API 端点：
- Health check
- Root endpoint
- Echo skill (成功和失败场景)
- 错误处理

**使用方法：**
```bash
./test/test_api.sh
```

### `test_integration.sh` - 集成测试

测试完整的调用流程：
- 服务健康检查
- 获取可用 skills
- 调用 skill 并验证响应
- Trace ID 传递验证

**使用方法：**
```bash
./test/test_integration.sh
```

### `test_echo_skill.sh` - Echo Skill 专项测试

专门测试 echo skill 的各种场景：
- 正常调用
- 空文本（应该失败）
- 缺少字段（应该失败）

**使用方法：**
```bash
./test/test_echo_skill.sh
```

## 手动测试

### 1. 健康检查

```bash
curl http://127.0.0.1:8000/health
```

预期响应：
```json
{
  "status": "ok",
  "skills_count": 4,
  "llm_configured": false
}
```

### 2. 获取可用 Skills

```bash
curl http://127.0.0.1:8000/
```

预期响应：
```json
{
  "service": "OpenSkill Skill Host",
  "version": "0.1.0",
  "skills": ["echo", "calculator", "file_search", "log_transform"],
  "llm_providers": []
}
```

### 3. 测试 Echo Skill

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

### 4. 测试错误场景

**空文本：**
```bash
curl -X POST "http://127.0.0.1:8000/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: test-456" \
  -d '{"input": {"text": ""}}'
```

**不存在的 Skill：**
```bash
curl -X POST "http://127.0.0.1:8000/skills/nonexistent:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: test-789" \
  -d '{"input": {}}'
```

## 使用 Python 测试

### 安装测试依赖（可选）

```bash
pip install pytest requests
```

### 运行 Python 测试

```bash
# 如果有 pytest 测试文件
pytest test/

# 或使用 Python 脚本
python test/test_manual.py
```

## 测试环境变量

可以通过环境变量配置测试：

```bash
# 设置不同的 base URL
export OPENSKILL_HTTP_BASE_URL=http://localhost:8000

# 运行测试
./test/test_api.sh
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: ./setup.sh
      - run: ./scripts/start.sh &
      - run: sleep 5
      - run: ./test/test_api.sh
```

## 故障排查

### 测试失败

1. **确保服务正在运行**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **检查端口是否被占用**
   ```bash
   lsof -i :8000
   ```

3. **查看服务日志**
   ```bash
   # 如果使用脚本启动，日志会在终端显示
   # 检查是否有错误信息
   ```

4. **验证环境变量**
   ```bash
   echo $OPENSKILL_HTTP_BASE_URL
   ```

### 常见问题

- **连接被拒绝**: 服务未启动或端口错误
- **404 错误**: 端点路径错误
- **500 错误**: 查看服务日志了解详细错误

## 添加新测试

创建新的测试脚本：

```bash
#!/bin/bash
# test_new_feature.sh

set -e

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}

echo "Testing new feature..."

# Your test code here

echo "✅ Test passed!"
```

然后添加执行权限：

```bash
chmod +x test/test_new_feature.sh
```

