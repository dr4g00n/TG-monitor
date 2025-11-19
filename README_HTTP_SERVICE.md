# Telegram Meme Token Monitor - HTTP 服务版

## 架构变更

本项目已从直接监控 Telegram 频道改为接收 HTTP 请求的处理服务架构：

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python 监控器（Pyrogram）                    │
│                   监控频道 → 发送 HTTP 请求                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │ POST /api/v1/message
                               │ JSON: {channel_id, text, ...}
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Rust HTTP 处理服务（本程序）                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  HTTP Server │ →  │  AI 分析     │ →  │  Telegram Bot API│  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│  接收消息               语义分析          转发给目标用户        │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
src/
├── main.rs           # 入口点，启动 HTTP 服务器
├── config.rs         # 配置管理
├── http/
│   ├── mod.rs        # HTTP 模块入口
│   ├── server.rs     # HTTP 服务器实现
│   └── handler.rs    # API 请求处理器
├── telegram/
│   ├── mod.rs        # Telegram 模块入口
│   └── bot.rs        # Telegram Bot API 客户端（发送消息）
├── ai/               # AI 服务模块（复用原有代码）
└── processor.rs      # 消息处理和批处理逻辑
```

## API 端点

### 健康检查
```bash
GET http://localhost:8080/health
Response: { "success": true, "message": "服务运行正常", "data": null }
```

### 接收消息
```bash
POST http://localhost:8080/api/v1/message
Content-Type: application/json

{
  "channel_id": -1001234567890,
  "channel_name": "频道名称",
  "message_id": 12345,
  "text": "买入 XTOKEN 0x1234567890abcdef...",
  "timestamp": 1700000000,
  "sender": "用户123 (id123)"
}

Response:
{
  "success": true,
  "message": "消息已接收并加入处理队列",
  "data": null
}
```

## 配置说明

编辑 `config_new.toml` 文件：

```toml
[telegram]
target_user = 123456789  # 接收消息的用户 ID
bot_token = "YOUR_BOT_TOKEN"  # Telegram Bot Token

[http]
port = 8080  # HTTP 监听端口

[ai]
provider = "kimi"  # AI 服务提供商: ollama, kimi, openai
# ... 其他 AI 配置 ...
```

## 运行服务

```bash
# 编译并运行
cargo run --release -- config_new.toml

# 或使用默认配置
cargo run --release
```

服务启动后会监听 `http://0.0.0.0:8080`，等待接收消息。

## Python 监控器示例

Python 监控器需要：
1. 使用 Pyrogram 监控 Telegram 频道
2. 检测到消息后，发送 HTTP POST 到 Rust 服务
3. 消息格式必须符合 API 要求

### Python 发送消息示例

```python
import requests
import json

def send_to_processor(message_data):
    """发送消息到 Rust 处理服务"""
    url = "http://localhost:8080/api/v1/message"

    payload = {
        "channel_id": message_data["chat"]["id"],
        "channel_name": message_data["chat"]["title"],
        "message_id": message_data["id"],
        "text": message_data["text"] or "[Media]",
        "timestamp": int(message_data["date"].timestamp()),
        "sender": f"{message_data['from_user']['username']} ({message_data['from_user']['id']})" if message_data.get('from_user') else None
    }

    response = requests.post(url, json=payload)
    return response.json()
```

## 工作流程

1. **Python 监控器**：
   - 连接到 Telegram（使用用户账号）
   - 监控配置的频道
   - 当有新消息时，提取相关信息
   - 发送 HTTP POST 请求到 Rust 服务

2. **Rust 服务**：
   - HTTP 服务器接收消息
   - 验证消息格式
   - 加入处理队列（批处理）
   - AI 服务进行语义分析
   - 判断是否包含 meme token 交易信息
   - 提取关键信息（token 名称、合约地址、操作建议等）
   - 格式化分析结果

3. **转发消息**：
   - 使用 Telegram Bot API
   - 发送格式化的分析结果给目标用户
   - 包含置信度、紧急程度等元信息

## 优势

✅ **解耦架构**：监控和处理分离，独立扩展
✅ **发挥优势**：Python 监控成熟稳定，Rust 处理高性能
✅ **易于维护**：每个组件职责清晰
✅ **灵活部署**：可以分别部署在不同服务器
✅ **技术选型**：各自使用最适合的工具

## 下一步

1. 创建 Python 监控器（使用 Pyrogram）
2. 配置 Telegram Bot（@BotFather）
3. 获取 Bot Token 并配置到 config.toml
4. 测试完整流程

## 注意事项

- Rust 服务只需要 Bot Token（不需要用户账号）
- Python 监控器需要用户账号（用于监控频道）
- 确保防火墙允许 HTTP 端口（默认 8080）
- 生产环境建议使用 Nginx 反向代理，并启用 HTTPS
