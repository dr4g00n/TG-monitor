# Telegram 客户端库选型指南

## Rust 生态的 Telegram 客户端库

### 1. **grammers** (推荐 ⭐⭐⭐⭐⭐)

**项目地址**: https://github.com/Lonami/grammers

**特点**:
- ✅ 纯 Rust 实现，无外部依赖
- ✅ 完整的 MTProto 协议支持
- ✅ 活跃的开发和维护
- ✅ 详细的文档和示例
- ✅ 支持所有 Telegram 功能（频道、群组、私密聊天）

**安装**:
```toml
[dependencies]
grammers-client = "0.5"
grammers-session = "0.5"
grammers-tl-types = "0.5"
```

**示例代码**:
```rust
use grammers_client::{Client, Config, SignInError};
use grammers_session::Session;

async fn main() {
    let client = Client::connect(Config {
        session: Session::load_file_or_create("session.session").unwrap(),
        api_id: 12345,
        api_hash: "your-api-hash",
        params: Default::default(),
    }).await.unwrap();

    // 登录
    if !client.is_authorized().await.unwrap() {
        let phone = "+86138xxxxxxxx".to_string();
        let token = client.request_login_code(&phone).await.unwrap();
        // ... 输入验证码
    }

    // 监听消息
    while let Some(update) = client.next_update().await.unwrap() {
        // 处理消息
    }
}
```

**优点**:
- 类型安全，编译时检查
- 异步/await 支持
- 内存占用低
- 支持会话持久化

**缺点**:
- 学习曲线稍陡
- 某些高级功能需要理解 MTProto 协议

---

### 2. **teloxide** (推荐 ⭐⭐⭐⭐)

**项目地址**: https://github.com/teloxide/teloxide

**特点**:
- ✅ 专用于 Telegram Bot
- ✅ 基于 grammers 构建但更高层次
- ✅ 优雅的命令处理框架
- ✅ 支持中间件
- ✅ 大量内置功能（如对话管理）

**安装**:
```toml
[dependencies]
teloxide = { version = "0.12", features = ["macros"] }
```

**示例代码**:
```rust
use teloxide::prelude::*;

async fn run_bot() {
    let bot = Bot::new("your-bot-token");

    teloxide::repl(bot, |message: Message, bot: Bot| async move {
        bot.send_message(message.chat.id, "Hello!").await?;
        Ok(())
    })
    .await;
}
```

**优点**:
- 简洁的 API 设计
- 理想用于 Bot 开发
- 强大的 dispatch 系统
- 支持状态机（对话）

**缺点**:
- 仅支持 Bot API，不支持用户账号
- 无法监控频道（Bot 无法加入频道）
- 功能受限于 Bot API

---

### 3. **telethon-rs** (不推荐 ⭐⭐)

**项目地址**: https://github.com/telegram-rs/telethon

**特点**:
- 早期的 Rust Telegram 客户端
- 基于旧的 MTProto 实现

**状态**:
⚠️ 项目已归档，不再维护
⚠️ 推荐使用 grammers 代替

---

### 4. **tg** (简单 API 封装 ⭐⭐⭐)

**项目地址**: https://github.com/rossnomann/tg

**特点**:
- 简单的 Telegram 客户端 API 封装
- 轻量级
- 仅支持基本功能

**安装**:
```toml
[dependencies]
tg = "0.2"
```

**适用场景**:
- 简单的消息收发
- 不需要复杂功能的场景

---

## 其他语言的 Telegram 库（供参考）

### Python

#### 1. **pyrogram** (推荐 ⭐⭐⭐⭐⭐)
```python
from pyrogram import Client, filters

app = Client("my_account", api_id=12345, api_hash="xxx")

@app.on_message(filters.channel)
def handle_channel_message(client, message):
    print(f"New message: {message.text}")

app.run()
```

**优点**:
- ✅ 完整的 MTProto 支持
- ✅ 优雅的装饰器 API
- ✅ 支持所有 Telegram 功能
- ✅ 活跃的社区

#### 2. **Telethon**
```python
from telethon import TelegramClient

client = TelegramClient('session', api_id, api_hash)

@client.on(events.NewMessage(chats=['channel_id']))
async def handler(event):
    print(event.message.text)

client.start()
client.run_until_disconnected()
```

**优点**:
- ✅ 成熟的库
- ✅ 大量文档和示例
- ✅ 支持高级功能

---

### Node.js

#### 1. **gramjs** (推荐 ⭐⭐⭐⭐)
```javascript
const { TelegramClient } = require('telegram');

const client = new TelegramClient(session, apiId, apiHash, {});
await client.connect();

client.addEventHandler((update) => {
    console.log(update);
});
```

---

### Go

#### 1. **gotd/td** (推荐 ⭐⭐⭐⭐)
```go
import "github.com/gotd/td/telegram"

client := telegram.NewClient(appID, appHash, telegram.Options{})
client.Run(ctx, func(ctx context.Context) error {
    // 使用 client
    return nil
})
```

---

## 选型建议

### 对于本项目的推荐方案

**首选: grammers-client** (Rust)

**理由**:
1. ✅ 完整的 MTProto 协议支持
2. ✅ 可以监控频道（用户账号）
3. ✅ Rust 实现，与当前项目语言一致
4. ✅ 异步支持，性能优秀
5. ✅ 活跃的维护
6. ✅ 类型安全，减少运行时错误

**次选: Pyrogram** (Python)

**理由**:
1. ✅ 如果你熟悉 Python，可以快速原型开发
2. ✅ 文档丰富，社区活跃
3. ✅ 完整的频道监控支持

**不推荐**:
- teloxide: 仅支持 Bot，无法监控频道
- Telethon (Python): 虽然功能完整，但 Python 性能不如 Rust

---

## grammers-client 集成步骤

### 步骤 1: 添加依赖

```toml
[dependencies]
grammers-client = "0.5"
grammers-session = "0.5"
tokio = { version = "1", features = ["full"] }
```

### 步骤 2: 创建 Telegram 客户端模块

```rust
// src/telegram/client.rs

use grammers_client::{Client, Config, SignInError, Update};
use grammers_session::Session;
use crate::processor::MessageProcessor;

pub struct TelegramClient {
    client: Client,
    processor: MessageProcessor,
}

impl TelegramClient {
    pub async fn new(config: &TelegramConfig, processor: MessageProcessor) -> Result<Self> {
        let session = Session::load_file_or_create(&config.session_file)?;

        let client = Client::connect(Config {
            session,
            api_id: config.api_id,
            api_hash: config.api_hash.clone(),
            params: Default::default(),
        }).await?;

        // 检查是否需要登录
        if !client.is_authorized().await? {
            self.login(&client).await?;
        }

        Ok(Self { client, processor })
    }

    async fn login(&self, client: &Client) -> Result<()> {
        println!("需要登录 Telegram");
        println!("请输入手机号 (例如 +86138xxxxxxxx):");

        let mut phone = String::new();
        std::io::stdin().read_line(&mut phone)?;

        let token = client.request_login_code(&phone.trim()).await?;
        println!("验证码已发送到 {}", phone.trim());
        println!("请输入验证码:");

        let mut code = String::new();
        std::io::stdin().read_line(&mut code)?;

        match client.sign_in(&token, &code.trim()).await {
            Ok(_) => println!("登录成功！"),
            Err(SignInError::PasswordRequired(password_token)) => {
                println!("需要输入两步验证密码:");
                let mut password = String::new();
                std::io::stdin().read_line(&mut password)?;
                client.check_password(password_token, password.trim()).await?;
                println!("登录成功！");
            }
            Err(e) => return Err(e.into()),
        }

        Ok(())
    }

    pub async fn start(&self) -> Result<()> {
        println!("开始监听消息...");

        while let Some(update) = self.client.next_update().await? {
            match update {
                Update::NewMessage(message) if !message.outgoing() => {
                    self.handle_message(message).await?;
                }
                _ => {}
            }
        }

        Ok(())
    }

    async fn handle_message(&self, message: grammers_client::types::Message) -> Result<()> {
        // 提取消息内容
        let chat = message.chat();

        // 检查是否来自监控的频道
        if let Some(chat_id) = chat.id() {
            if self.is_monitored_channel(chat_id) {
                let msg = Message {
                    id: message.id(),
                    channel_id: chat_id as i64,
                    channel_name: chat.name().unwrap_or("Unknown").to_string(),
                    text: message.text().to_string(),
                    timestamp: message.date().timestamp(),
                    sender: None,
                    media_type: None,
                };

                self.processor.process_message(msg).await?;
            }
        }

        Ok(())
    }

    fn is_monitored_channel(&self, chat_id: i64) -> bool {
        // 检查频道是否在监控列表中
        // TODO: 实现频道过滤逻辑
        true
    }
}
```

### 步骤 3: 在主程序中使用

```rust
// src/main.rs

use telegram::TelegramClient;

#[tokio::main]
async fn main() -> Result<()> {
    let config = Config::load("config.toml")?;
    let ai_service = AIServiceFactory::create(&config.ai)?;

    // 创建消息处理器
    let processor = MessageProcessor::new(config.clone(), ai_service);

    // 创建并启动 Telegram 客户端
    let client = TelegramClient::new(&config.telegram, processor).await?;
    client.start().await?;

    Ok(())
}
```

---

## 各库对比总结

| 库 | 语言 | 协议 | 用户账号 | Bot | 活跃度 | 推荐度 |
|---|---|---|---|---|---|---|
| **grammers** | Rust | MTProto | ✅ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **teloxide** | Rust | Bot API | ❌ | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **pyrogram** | Python | MTProto | ✅ | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Telethon** | Python | MTProto | ✅ | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **gramjs** | Node.js | MTProto | ✅ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **tg** | Rust | MTProto | ✅ | ❌ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 最终建议

**对于本项目，强烈推荐使用 grammers-client**，原因：

1. ✅ 支持监控频道（用户账号）
2. ✅ Rust 实现，性能优异
3. ✅ 异步支持，资源占用低
4. ✅ 完整的类型安全
5. ✅ 活跃的维护，Bug 修复及时
6. ✅ 支持所有 Telegram 功能

**如果考虑其他语言**：pyrogram (Python) 是一个优秀的替代方案

**如果不监控频道，只是做 Bot**：teloxide (Rust) 是最佳选择
