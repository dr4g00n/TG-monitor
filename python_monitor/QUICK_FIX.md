# Python 监控器运行时错误修复总结

## 已修复的关键问题

### ✅ 问题 1: 异步/同步调用不匹配（已修复）

**问题**: `handle_message` 作为 async 函数传递给 Pyrogram 的 MessageHandler，但 Pyrogram 2.0+ 要求 Handler 必须是同步函数。

**修复**: `src/telegram_client.py`
- 创建了 `handle_message_sync()` - 同步包装函数
- 创建了 `handle_message_async()` - 异步实际处理函数
- 使用 `asyncio.create_task()` 启动异步任务
- 使用 `asyncio.to_thread()` 在异步函数中调用同步 HTTP 请求

### ✅ 问题 2: 缺少 asyncio import（已修复）

**修复**: 在文件顶部添加 `import asyncio`

### ✅ 问题 3: 错误日志不够详细（已修复）

**修复**: 在异常处理中添加 `logger.exception(e)` 打印完整堆栈跟踪

## 其他需要检查的问题

### ⚠️ 配置问题

确保配置文件 `config.ini` 已正确创建：

```bash
cd python_monitor
cp config_sample.ini config.ini
# 然后编辑 config.ini，填入你的 Telegram API ID/Hash 和频道 ID
```

### ⚠️ 依赖安装

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### ⚠️ Python 路径

在正确目录下运行：

```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor/python_monitor
python3 monitor.py
```

### ⚠️ Rust 服务必须先启动

```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor
cargo run --release -- config_new.toml
```

## 快速测试

### 测试配置加载

```bash
cd python_monitor
python3 -c "from src.config_loader import load_config; cfg = load_config('config_sample.ini'); print('✓ 配置加载成功')"
```

预期输出：`✓ 配置加载成功`

### 测试 HTTP 发送器

首先确保 Rust 服务已运行：

```bash
cd python_monitor
python3 -c "
from src.http_sender import HttpSender
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 1, 'timeout': 5})
print('✓ HTTP 发送器创建成功')
result = sender.health_check()
print(f'✓ 健康检查: {\"PASS\" if result else \"FAIL\"}')
"
```

预期输出：`✓ HTTP 发送器创建成功` 和 `✓ 健康检查: PASS`

### 测试 Telegram 监控器

```bash
cd python_monitor
python3 -c "
from src.telegram_client import TelegramMonitor
from src.http_sender import HttpSender
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 1, 'timeout': 5})
monitor = TelegramMonitor(12345, 'test_hash', 'test_session', [-1001234567890], sender)
print('✓ Telegram 监控器创建成功')
"
```

预期输出：`✓ Telegram 监控器创建成功`

## 运行完整程序

如果以上测试都通过，可以运行完整程序：

```bash
cd python_monitor
python3 monitor.py config.ini
```

首次运行会提示登录：
1. 输入手机号（格式: +86138xxxxxxxx）
2. 输入验证码（发送到 Telegram）
3. 如有两步验证，输入密码

登录成功后，应该看到：
```
========================================
Telegram 频道监控器启动中...
========================================
加载配置文件: config.ini
配置加载成功
  监控频道数量: 2
  Rust 服务地址: http://localhost:8080/api/v1/message
  日志级别: INFO
测试 Rust 服务连接...
✓ Rust 服务连接正常
========================================
开始监控频道消息...
按 Ctrl+C 停止
========================================
```

## 排错指南

### 错误 1: `ImportError: cannot import name 'TelegramMonitor'`

**原因**: 不在正确的目录

**解决**:
```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor/python_monitor
```

### 错误 2: `ModuleNotFoundError: No module named 'src'`

**原因**: Python 路径问题

**解决**: 确保在 `python_monitor` 目录下运行

### 错误 3: `ValueError: 无效的频道 ID: 123456`

**原因**: 频道 ID 格式错误

**解决**: 频道 ID 必须是 `-100` 开头的数字，例如 `-1001234567890`

### 错误 4: `ConnectionError: Failed to connect to Telegram`

**原因**: API ID/Hash 错误或网络问题

**解决**:
1. 检查 https://my.telegram.org 的 API ID/Hash
2. 检查网络连接
3. 删除 session 文件重试

### 错误 5: `HTTP Error 500` 或连接超时

**原因**: Rust 服务未运行或端口错误

**解决**:
```bash
# 检查 Rust 服务
curl http://localhost:8080/health
```

## 验证成功

当在监控的频道发送消息时，应该看到：
```
收到新消息: [频道名称] 12345
✓ 消息发送成功: 频道名称 - 12345
```

说明 Python 监控器已成功将消息发送到 Rust 服务！
