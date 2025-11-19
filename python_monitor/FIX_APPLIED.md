# Python 监控器运行时错误修复报告

## ✅ 已应用的修复

### 1. 修复异步/同步调用不匹配（CRITICAL）

**问题**: `handle_message` 是 async 方法，但 Pyrogram 的 MessageHandler 要求同步方法

**修复**:
- 创建了两层处理方法：
  - `handle_message_sync()` - 同步方法，由 Pyrogram 直接调用
  - `handle_message_async()` - 异步方法，实际处理逻辑
- 使用 `asyncio.create_task()` 在同步方法中启动异步任务
- 使用 `asyncio.to_thread()` 在异步方法中执行同步 HTTP 请求

**文件**: `src/telegram_client.py`

### 2. 添加了 import asyncio

**文件**: `src/telegram_client.py:12`

### 3. 改进了错误日志

**问题**: 错误信息不够详细

**修复**:
```python
logger.error(f"处理消息时出错: {e}")
logger.exception(e)  # 添加这一行，打印完整堆栈跟踪
```

**文件**: `src/telegram_client.py:95-97`

## 🔧 其他潜在问题（需要用户注意）

### 1. 配置验证

请在 `config_sample.ini` 中正确配置：

```ini
[telegram]
api_id = YOUR_API_ID              # 从 https://my.telegram.org 获取
api_hash = YOUR_API_HASH          # 从 https://my.telegram.org 获取
session_file = my_monitor.session  # 会话文件，自动生成
channel_ids = -1001234567890      # 从 @userinfobot 获取，必须是 -100 开头

[rust_service]
url = http://localhost:8080/api/v1/message  # Rust 服务地址
max_retries = 3
timeout = 30
```

### 2. 创建配置文件

```bash
cd python_monitor
cp config_sample.ini config.ini
vim config.ini  # 编辑配置
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 测试步骤

### 步骤 1: 启动 Rust 服务

```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor
cargo run --release -- config_new.toml
```

观察日志，确保没有错误。

### 步骤 2: 测试配置加载

```bash
cd python_monitor
python3 -c "
from src.config_loader import load_config
cfg = load_config('config_sample.ini')
print('✓ 配置加载成功')
print(f"  频道 IDs: {cfg['telegram']['channel_ids']}")
print(f"  Rust URL: {cfg['rust_service']['url']}")
"
```

### 步骤 3: 测试 HTTP 发送器

```bash
python3 -c "
from src.http_sender import HttpSender
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 1, 'timeout': 5})
print('✓ HTTP 发送器创建成功')
result = sender.health_check()
print(f"  健康检查: {'PASS' if result else 'FAIL'}")
"
```

如果健康检查失败，请确保 Rust 服务已启动。

### 步骤 4: 测试 Telegram 监控器导入

```bash
python3 -c "
from src.telegram_client import TelegramMonitor
from src.http_sender import HttpSender

# 创建模拟的 HTTP 发送器
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 1, 'timeout': 5})

# 创建监控器（不会连接）
monitor = TelegramMonitor(
    api_id=12345,
    api_hash='test_hash',
    session_file='test_session',
    channel_ids=[-1001234567890],
    http_sender=sender
)
print('✓ Telegram 监控器创建成功')
print(f"  监控频道数: {len(monitor.channel_ids)}")
"
```

### 步骤 5: 运行完整程序（首次登录）

```bash
python3 monitor.py config.ini
```

第一次运行会提示：
1. 输入手机号（格式: +86138xxxxxxxx）
2. 输入验证码（发送到 Telegram）
3. 如果有两步验证，输入密码

登录成功后，会看到：
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

### 步骤 6: 发送测试消息

在监控的频道发送一条测试消息，观察日志：

```
收到新消息: [测试频道] 12345
✓ 消息发送成功: 测试频道 - 12345
```

## 📊 预期日志输出

### 正常情况

```
22:30:15 | INFO     | Telegram 频道监控器启动中...
22:30:15 | INFO     | 加载配置文件: config.ini
22:30:15 | INFO     | 配置加载成功
22:30:15 | INFO     | Telegram 监控器初始化完成
22:30:15 | INFO     |   API ID: 12345
22:30:15 | INFO     |   会话文件: my_monitor.session
22:30:15 | INFO     |   监控频道: 2 个
22:30:15 | INFO     | 测试 Rust 服务连接...
22:30:16 | INFO     | ✓ Rust 服务连接正常
22:30:16 | INFO     | 开始监控频道消息...
22:30:16 | INFO     | 按 Ctrl+C 停止
22:30:20 | INFO     | 收到新消息: [测试频道] 12345
22:30:21 | INFO     | ✓ 消息发送成功: 测试频道 - 12345
```

### 异常情况

**连接失败**:
```
22:30:15 | WARNING  | ✗ Rust 服务连接失败，将继续运行但可能无法发送消息
```

**消息发送失败**:
```
22:30:20 | ERROR    | ✗ 发送失败 after 3 次尝试
22:30:20 | ERROR    | 处理消息时出错: HTTP Error 500
```

## 🐛 常见问题

### Q1: `ImportError: cannot import name 'TelegramMonitor'`

**原因**: Python 路径问题

**解决**:
```bash
# 在项目根目录运行
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor/python_monitor
python3 monitor.py
```

### Q2: `ValueError: 无效的频道 ID: 123456`

**原因**: 频道 ID 格式不正确

**解决**: 频道 ID 必须以 `-100` 开头，例如 `-1001234567890`

### Q3: `RuntimeError: no running event loop`

**原因**: asyncio 事件循环问题

**解决**: 确保 Pyrogram 版本正确
```bash
pip install pyrogram==2.0.106
pip install tgcrypto==1.25
```

### Q4: `ModuleNotFoundError: No module named 'src'`

**原因**: Python 路径问题

**解决**: 在 `python_monitor` 目录下运行

### Q5: `ConnectionError: Failed to connect`

**原因**: 无法连接到 Telegram

**解决**:
- 检查网络连接
- 检查 api_id 和 api_hash 是否正确
- 尝试删除 session 文件重新登录

## ✅ 验证清单

- [ ] Rust 服务已启动并运行
- [ ] 配置文件 `config.ini` 已创建并正确配置
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] Telegram API ID 和 Hash 已正确配置
- [ ] 频道 ID 格式正确（以 `-100` 开头）
- [ ] Rust 服务地址可访问 (`curl http://localhost:8080/health`)
- [ ] 首次运行能成功登录 Telegram
- [ ] 发送测试消息能成功转发

## 📝 日志文件

日志文件: `python_monitor/monitor.log`

查看实时日志：
```bash
tail -f monitor.log
```

日志轮转：
- 自动轮转（每 500MB）
- 保留 10 天的日志
- DEBUG 级别及以上都记录

## 🎉 成功标志

当看到以下日志时，说明系统运行正常：

```
✓ Rust 服务连接正常
✓ 监控器已启动
收到新消息: [频道名称] 12345
✓ 消息发送成功: 频道名称 - 12345
```

目标用户应该能收到 Telegram Bot 发送的 AI 分析结果。
