# Telegram Meme Token Monitor - 完整架构

## 系统架构

本项目采用混合架构，结合 Python 的成熟生态和 Rust 的高性能优势。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    第一层：Python 监控层（Pyrogram）                     │
│                    职责：频道监控、消息采集                              │
└──────────────────────────────┬──────────────────────────────────────────┘
                              │ HTTP POST
                              │ JSON Message
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    第二层：Rust 处理层（Axum）                          │
│                    职责：HTTP 接收、消息处理、AI 分析                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   HTTP Server    │───▶│ Message Queue    │───▶│    AI Service    │  │
│  │  (接收和验证)    │    │   (批处理)       │    │  (Kimi/Ollama)   │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                              │
                              │ Analysis Result
                              │ (Formatted Markdown)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    第三层：Telegram Bot API                              │
│                    职责：消息转发、通知发送                            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 技术栈

### Python 层（监控器）
- **框架**: Pyrogram
- **功能**: 监控 Telegram 频道、接收消息
- **HTTP**: Requests
- **日志**: Loguru
- **配置**: ConfigParser

### Rust 层（处理器）
- **HTTP 服务器**: Axum + Tokio
- **AI 服务**: 多提供商支持（Kimi, Ollama, OpenAI）
- **消息处理**: 批处理、队列管理
- **Telegram 输出**: Bot API

## 组件说明

### 1. Python Monitor

**位置**: `python_monitor/`

**核心功能**:
- 使用用户账号登录 Telegram
- 监控配置的频道列表
- 接收所有新消息（文本、媒体、文件等）
- 提取消息元数据（频道、发送者、时间等）
- HTTP POST 到 Rust 服务

**文件结构**:
```
python_monitor/
├── monitor.py              # 主程序
├── config.ini             # 配置文件
├── requirements.txt       # Python 依赖
├── setup.sh              # 安装脚本
└── src/
    ├── telegram_client.py  # Pyrogram 包装器
    ├── http_sender.py      # HTTP 客户端
    └── config_loader.py    # 配置加载
```

**配置示例**:
```ini
[telegram]
api_id = 123456
api_hash = your_hash
session_file = monitor.session
channel_ids = -1001234567890,-1009876543210

[rust_service]
url = http://localhost:8080/api/v1/message
```

**启动方式**:
```bash
python monitor.py
```

### 2. Rust HTTP Server

**位置**: 项目根目录

**核心功能**:
- HTTP API 接收消息
- 消息批处理（batch_size, batch_timeout）
- AI 语义分析
- 结果格式化
- Telegram Bot API 转发

**API 端点**:

#### 健康检查
```
GET /health
Response: { "success": true, "message": "服务运行正常" }
```

#### 接收消息
```
POST /api/v1/message
Content-Type: application/json

请求体:
{
  "channel_id": -1001234567890,
  "channel_name": "频道名称",
  "message_id": 12345,
  "text": "消息内容",
  "timestamp": 1700000000,
  "sender": "用户名 (用户ID)"
}

响应:
{
  "success": true,
  "message": "消息已接收并加入处理队列",
  "data": null
}
```

**配置示例**:
```toml
[telegram]
target_user = 123456789          # 接收通知的用户 ID
bot_token = "YOUR_BOT_TOKEN"     # Bot API Token

[http]
port = 8080                      # HTTP 端口

[processing]
batch_size = 10                  # 批处理大小
batch_timeout_seconds = 300      # 超时时间
min_confidence = 0.7             # 最小置信度
keywords = ["token", "买入", "卖出"]

[ai]
provider = "kimi"                # AI 提供商
# ... AI 配置 ...
```

**启动方式**:
```bash
cargo run --release -- config.toml
```

### 3. AI 服务

**支持提供商**:
- **Kimi**: Moonshot AI，快速、准确
- **Ollama**: 本地模型，隐私保护
- **OpenAI**: GPT 系列，或兼容 API（如 DeepSeek）

**功能**:
- 分析消息是否关于 meme token
- 提取关键信息（token 名称、合约地址、操作建议）
- 评估置信度和紧急程度
- 返回结构化 JSON

**AI Prompt 示例**:
```
你是一名专业的加密货币交易信息分析师。
你的任务是分析 Telegram 消息，判断是否在讨论 meme token 交易信息。

如果是相关消息，请提取以下信息并以 JSON 格式返回：
{
  "is_relevant": true,
  "token_name": "Token名称",
  "contract_address": "0x...",
  "recommendation": "买入/卖出/持有",
  "reason": "详细的推荐理由",
  "confidence": 0.85,
  "urgency": 7
}

如果不是相关消息，返回：
{"is_relevant": false}

消息内容: {}
```

## 工作流程

### 消息流转

```
1. Telegram Channel
   ↓ New Message
2. Python Monitor (Pyrogram)
   ↓ Extract Info
3. HTTP POST to Rust
   ↓ Validate & Queue
4. Batch Processing
   ↓ AI Analysis
5. AI Service (Kimi/Ollama)
   ↓ Structured Data
6. Format Message
   ↓ Telegram Bot API
7. Target User Receives Notification
```

### 批处理机制

Rust 服务实现了智能批处理：

- **批量大小**: 达到 N 条消息后处理
- **超时机制**: 达到 T 秒后处理（即使没有满批）
- **优先级**: 关键词匹配的消息优先处理

配置：
```toml
[processing]
batch_size = 10                  # 达到 10 条立即处理
batch_timeout_seconds = 300      # 或 5 分钟超时
min_confidence = 0.7             # 过滤低置信度
keywords = ["token", "买入"]      # 优先处理关键词
```

### 错误处理

1. **Python 监控器**
   - 连接丢失：自动重连
   - HTTP 失败：指数退避重试
   - 日志记录：详细错误信息

2. **Rust 处理器**
   - 消息验证：JSON 解析和字段检查
   - AI 失败：记录错误，继续处理
   - Telegram API 失败：记录错误

## 部署

### 本地开发

**终端 1 - Rust 服务**:
```bash
cd telegram_monitor
cargo run --release -- config.toml
```

**终端 2 - Python 监控**:
```bash
cd telegram_monitor/python_monitor
python monitor.py
```

### 生产环境

**使用 systemd**: (可选)

1. Rust 服务:
```bash
# /etc/systemd/system/telegram-processor.service
[Unit]
Description=Telegram Meme Token Processor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/telegram_monitor
ExecStart=/opt/telegram_monitor/target/release/telegram-monitor config.toml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Python 监控:
```bash
# /etc/systemd/system/telegram-monitor.service
[Unit]
Description=Telegram Channel Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/telegram_monitor/python_monitor
ExecStart=/opt/telegram_monitor/python_monitor/venv/bin/python monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Docker** (推荐):

```dockerfile
# Dockerfile.rust
FROM rust:1.75 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/telegram-monitor /usr/local/bin/
COPY config.toml /app/
CMD ["telegram-monitor", "/app/config.toml"]
```

```dockerfile
# Dockerfile.python
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "monitor.py"]
```

## 监控和运维

### 日志

**Python 监控器**:
```bash
tail -f python_monitor/monitor.log
```

**Rust 处理器**:
```bash
tail -f rust_service.log
# 或使用 systemd
journalctl -u telegram-processor -f
journalctl -u telegram-monitor -f
```

### 健康检查

```bash
# 检查 Rust 服务
curl http://localhost:8080/health

# 检查 Python 到 Rust 的连通性
cd python_monitor
python3 -c "
from src.http_sender import HttpSender
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 3, 'timeout': 30})
print('Health check:', sender.health_check())
"
```

### 指标

建议添加 Prometheus 监控：

- 接收消息数量
- 处理成功/失败率
- AI 响应时间
- Telegram API 响应时间

## 安全考虑

### 1. API 密钥

- 不要在代码中硬编码 API 密钥
- 使用环境变量或配置文件
- 配置文件权限: `chmod 600 config.ini`

### 2. Telegram 账号

- 建议使用专用账号
- 启用两步验证
- 定期更换 session

### 3. 网络安全

- 生产环境启用 HTTPS (Nginx + SSL)
- 使用防火墙限制访问
- 内网部署，不暴露公网

### 4. 数据隐私

- 消息内容可能包含敏感信息
- AI 服务的选择考虑隐私政策
- 本地部署（Ollama）可保护隐私

## 性能优化

### Python 监控器

- 使用 Pyrogram 的 smart plugins
- 减少不必要的日志
- 优化 HTTP 连接池

### Rust 处理器

- 调整批处理大小
- 优化 AI 并发数
- 使用连接池

### AI 服务

- 选择合适模型（balance cost & quality）
- 实现缓存（避免重复分析）
- 限流保护

## 扩展功能

### 高优先级

- [ ] Prometheus 监控指标
- [ ] Web 管理面板
- [ ] 关键词管理 API
- [ ] 数据分析报表

### 中优先级

- [ ] 多语言支持
- [ ] 多 AI 提供商并发
- [ ] 消息去重
- [ ] 自定义转发格式

### 低优先级

- [ ] 支持 Telegram Topic
- [ ] 支持多目标用户
- [ ] 消息编辑/删除跟踪
- [ ] 自动回复

## 故障排除

### Python 监控器无法连接

检查：
1. API ID/Hash 正确
2. 手机验证码输入正确
3. 网络连接正常

```bash
# 测试连通性
python3 -c "from pyrogram import Client; print('Pyrogram OK')"
```

### Rust 服务无法接受消息

检查：
1. 服务已启动
2. 端口没有被占用
3. 防火墙配置

```bash
# 检查端口
netstat -tlnp | grep 8080

# 测试端点
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{"channel_id": 1, "channel_name": "test", "message_id": 1, "text": "test", "timestamp": 123}'
```

### AI 分析失败

检查：
1. API 密钥有效
2. 网络可访问 AI 服务
3. Prompt 格式正确

```bash
# 测试 AI 服务
cd ../  # 回到 Rust 项目目录
cargo run --release -- config.toml  # 观察 AI 错误日志
```

### Telegram Bot 无法发送

检查：
1. Bot Token 正确
2. Bot 可访问目标用户
3. 目标用户没有屏蔽 Bot

```bash
# 测试 Bot
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

## 贡献

欢迎提交 PR 或 Issue！

## License

MIT
