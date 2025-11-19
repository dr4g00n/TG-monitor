# Telegram 频道监控器（Python）

使用 Pyrogram 监控 Telegram 频道，并将消息发送到 Rust 处理服务。

## 功能特性

✅ 使用 Pyrogram 监控 Telegram 频道（支持用户账号）
✅ 自动检测新消息并提取关键信息
✅ 支持文本、图片、视频、文件等各种消息类型
✅ HTTP 发送到 Rust 服务，带自动重试机制
✅ 连接断开后自动重试
✅ 详细的日志记录

## 安装

### 1. 安装依赖

```bash
cd python_monitor
pip install -r requirements.txt
```

### 2. 配置 Telegram API

访问 [https://my.telegram.org/auth](https://my.telegram.org/auth) 创建应用，获取：
- `api_id`
- `api_hash`

### 3. 配置监控频道

向 @userinfobot 发送消息，获取频道 ID（格式: `-1001234567890`）

### 4. 配置 Rust 服务

确保 Rust 服务已启动并监听（默认: http://localhost:8080）

## 配置

复制配置文件：

```bash
cp config_sample.ini config.ini
```

编辑 `config.ini`：

```ini
[telegram]
# Telegram API 配置
api_id = 1234567
api_hash = your_api_hash_here
session_file = my_monitor.session

# 要监控的频道 IDs（用逗号分隔）
channel_ids = -1001234567890,-1009876543210

[rust_service]
# Rust 处理服务地址
url = http://localhost:8080/api/v1/message
max_retries = 3
timeout = 30

[logging]
# 日志级别: DEBUG, INFO, WARNING, ERROR
level = INFO
```

## 使用

### 首次运行（需要登录）

```bash
python monitor.py
```

首次运行时会提示输入手机号，然后会发送验证码到 Telegram，输入验证码即可完成登录。

登录成功后，会话会保存在 `session_file` 指定的文件中，下次运行无需再次登录。

### 指定配置文件

```bash
python monitor.py custom_config.ini
```

## 工作原理

1. **连接 Telegram**: 使用用户账号登录（需要 api_id/api_hash）
2. **监控频道**: 监听配置的频道列表中的新消息
3. **提取信息**: 从消息中提取文本、发送者、时间等信息
4. **发送 HTTP**: 将消息转换为 JSON 格式，POST 到 Rust 服务
5. **错误处理**: 失败时自动重试（指数退避策略）

## 消息格式

发送到 Rust 服务的消息格式：

```json
{
  "channel_id": -1001234567890,
  "channel_name": "频道名称",
  "message_id": 12345,
  "text": "消息内容",
  "timestamp": 1700000000,
  "sender": "用户名 (用户ID)"
}
```

## 架构图

```
┌─────────────────────────────────────┐
│  Telegram Channels                  │
└──────────────┬──────────────────────┘
               │
               │  New Message
               ▼
┌─────────────────────────────────────┐
│  Python Monitor (Pyrogram)          │
│  - Monitor channels                 │
│  - Extract message info             │
└──────────────┬──────────────────────┘
               │
               │  HTTP POST
               │  /api/v1/message
               ▼
┌─────────────────────────────────────┐
│  Rust HTTP Server (Axum)            │
│  - Receive messages                 │
│  - Batch processing                 │
└──────────────┬──────────────────────┘
               │
               │  AI Analysis
               ▼
┌─────────────────────────────────────┐
│  AI Service (Kimi/Ollama/OpenAI)    │
│  - Semantic analysis                │
│  - Extract token info               │
└──────────────┬──────────────────────┘
               │
               │  Forward Result
               ▼
┌─────────────────────────────────────┐
│  Telegram Bot API                   │
│  Send formatted message to target   │
└─────────────────────────────────────┘
```

## 日志

日志输出到控制台和 `monitor.log` 文件（自动轮转，最大 500MB，保留 10 天）。

日志级别可在配置文件中设置：
- `DEBUG`: 详细调试信息
- `INFO`: 一般运行信息（推荐）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

## 常见问题

### 1. 无法连接到 Rust 服务

确保 Rust 服务已启动：
```bash
cargo run --release -- config.toml
```

检查端口是否开放：
```bash
curl http://localhost:8080/health
```

### 2. Session 文件问题

如果登录失败，可以删除 session 文件重新登录：
```bash
rm my_monitor.session
python monitor.py
```

### 3. 频道 ID 格式

频道 ID 必须是数字，格式为 `-1001234567890`（负数）。

### 4. API ID/Hash 错误

确保从 [https://my.telegram.org](https://my.telegram.org) 获取的 API ID 和 Hash 正确。

## 代码结构

```
python_monitor/
├── monitor.py              # 主程序
├── requirements.txt        # 依赖
├── config_sample.ini      # 配置示例
├── src/
│   ├── config_loader.py   # 配置加载
│   ├── telegram_client.py # Telegram 监控
│   └── http_sender.py     # HTTP 发送
└── README.md              # 本文档
```

## 注意事项

1. **用户账号**: Python 监控器需要 Telegram 用户账号（不是 Bot）
2. **隐私**: 频道监控使用用户账号，遵守 Telegram 服务条款
3. **错误处理**: 监控器有自动重试机制，但建议设置监控告警
4. **性能**: 本监控器适用于中等规模的频道监控

## 扩展功能

可以根据需要扩展的功能：

- [ ] 添加数据库记录
- [ ] 支持消息过滤（关键词、正则表达式）
- [ ] 添加 Web 管理界面
- [ ] 支持多账号监控
- [ ] 消息去重
- [ ] 速率限制

## License

MIT
