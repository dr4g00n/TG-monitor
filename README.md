# Telegram Meme Token Monitor

一个基于 Rust 的 Telegram 频道监控系统，使用 AI 语义分析提取 meme token 交易信息，并智能汇总转发。

[![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://rust-lang.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 功能特性

### ✅ 已实现

- **多 AI 服务支持**
  - Ollama 本地模型（Llama 3, Mistral 等）
  - Kimi API (Moonshot)
  - OpenAI 兼容 API（OpenAI, DeepSeek 等）

- **统一 AI 服务接口**
  - 抽象 Trait 设计，易于扩展
  - 配置驱动，一键切换 AI 后端

- **消息处理**
  - 批量处理（可配置批次大小）
  - 智能过滤（关键词、置信度）
  - 定时汇总报告

- **配置管理**
  - TOML 配置文件
  - 完善的配置验证
  - 多环境配置示例

### 🚧 待实现

- **Telegram 客户端集成**
  - [ ] 集成 `grammers-client` 或类似库
  - [ ] 频道消息实时监控
  - [ ] 私聊/群组消息推送

- **数据持久化**
  - [ ] 历史记录存储（SQLite/sled）
  - [ ] Token 追踪记录
  - [ ] 分析结果持久化

- **高级功能**
  - [ ] Web 管理界面
  - [ ] 多币种合约地址解析
  - [ ] 市场情绪分析
  - [ ] 价格数据集成

## 技术架构

```
┌─────────────────────────────────────────────┐
│         Telegram 频道(s)                    │
│              ↓                              │
│    ┌──────────────────────┐                 │
│    │  Telegram Client     │                 │
│    │  (TODO: integration) │                 │
│    └──────────┬───────────┘                 │
│               ↓                             │
│    ┌──────────────────────┐                 │
│    │  Message Queue       │                 │
│    │  (batch processing)  │                 │
│    └──────────┬───────────┘                 │
│               ↓                             │
│    ┌──────────────────────┐                 │
│    │  AI Analysis Engine  │◄─────────────┐ │
│    │  (configurable)      │              │ │
│    └──────────┬───────────┘              │ │
│               ↓                            │ │
│    ┌──────────────────────┐              │ │
│    │  Results Aggregator  │              │ │
│    └──────────┬───────────┘              │ │
│               ↓                            │ │
│    ┌──────────────────────┐              │ │
│    │  Summary Reporter    │              │ │
│    └──────────┬───────────┘              │ │
│               ↓                            │ │
│    ┌──────────────────────┐              │ │
│    │ Telegram User/Bot    │              │ │
│    └──────────────────────┘              │ │
│                                          │ │
│  ┌──────────────┐  ┌──────────────┐     │ │
│  │  Ollama      │  │   Kimi API   │     │ │
│  │  Local Model │  │   (Moonshot) │     │ │
│  └──────────────┘  └──────────────┘     │ │
│  ┌──────────────┐                        │ │
│  │  OpenAI API  │                        │ │
│  │  (Compatible)│                        │ │
│  └──────────────┘                        │ │
└──────────────────────────────────────────┘─┘
```

## 快速开始

### 前置要求

- **Rust 1.70+**
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

### 方式 1: 使用 Kimi API（推荐快速开始）

**步骤：**

1. **获取 Kimi API Key**
   - 访问 https://platform.moonshot.cn/
   - 注册账号并创建 API Key

2. **配置**
   ```bash
   cp config.example.toml config.toml
   ```
   编辑 `config.toml`：
   ```toml
   [ai]
   provider = "kimi"

   [ai.kimi]
   api_key = "sk-your-api-key-here"
   model = "moonshot-v1-8k"
   ```

3. **运行**
   ```bash
   cargo run
   ```

### 方式 2: 使用 Ollama 本地模型

**步骤：**

1. **安装 Ollama**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **下载模型**（推荐 llama3:8b）
   ```bash
   ollama pull llama3:8b
   ```

3. **启动服务**
   ```bash
   ollama serve
   ```

4. **配置**
   ```toml
   [ai]
   provider = "ollama"

   [ai.ollama]
   api_endpoint = "http://localhost:11434"
   model = "llama3:8b"
   ```

5. **运行**
   ```bash
   cargo run
   ```

### 方式 3: 使用 OpenAI API

1. **配置**
   ```toml
   [ai]
   provider = "openai"

   [ai.openai]
   api_key = "sk-your-api-key"
   model = "gpt-3.5-turbo"
   base_url = "https://api.openai.com/v1"  # 可替换为 DeepSeek 等兼容 API
   ```

## 详细配置

完整配置示例见 `config.example.toml`

### 核心配置说明

#### `[telegram]` 部分

```toml
[telegram]
api_id = 123456                                    # 必须
api_hash = "your_api_hash"                         # 必须
session_file = "session.session"                   # 可选
source_channels = [-1001234567890, -1009876543210] # 必须
target_user = 123456789                            # 必须
```

#### `[ai]` 部分

```toml
[ai]
provider = "kimi"  # 可选值: ollama | kimi | openai

timeout_seconds = 60  # API 超时时间
max_retries = 3       # 失败重试次数

# Prompt 模板（高级用户可自定义）
prompt_template = '''
你是加密货币分析师... 消息: {}
'''
```

#### `[processing]` 部分

```toml
[processing]
batch_size = 10              # 批处理大小
batch_timeout_seconds = 300  # 超时时间
min_confidence = 0.7         # 最小置信度（0.0-1.0）
keywords = ["token", "合约"]   # 关键词过滤（可选）
```

## 项目结构

```
├── Cargo.toml              # 项目依赖
├── config.example.toml     # 配置示例
├── README.md              # 本文档
├── src/
│   ├── main.rs            # 程序入口
│   ├── config.rs          # 配置管理
│   ├── processor.rs       # 消息处理器
│   ├── ai/                # AI 服务模块
│   │   ├── mod.rs         # 抽象接口和工厂
│   │   ├── models.rs      # 数据模型
│   │   ├── local.rs       # Ollama 本地服务
│   │   ├── kimi.rs        # Kimi API 服务
│   │   └── openai.rs      # OpenAI 兼容服务
│   └── telegram/          # Telegram 模块
│       ├── mod.rs
│       └── client.rs      # 客户端封装
└── .gitignore
```

## AI 服务对比

| 特性 | Kimi API | Ollama 本地 | OpenAI API |
|------|---------|------------|-----------|
| **隐私性** | 数据发送到外部 | ✅ 完全本地 | 数据发送到外部 |
| **启动速度** | ✅ 立即使用 | 需要下载模型 | ✅ 立即使用 |
| **成本** | 按量计费 (~¥0.01/次) | ✅ 免费 | 按量计费 |
| **硬件要求** | 无 | 8GB+ RAM 推荐 | 无 |
| **响应速度** | ✅ 快速 (2-5s) | 较慢 (10-30s) | ✅ 快速 |
| **离线使用** | ❌ 需要网络 | ✅ 完全离线 | ❌ 需要网络 |
| **数据安全** | 发送到第三方 | ✅ 本地处理 | 发送到第三方 |

**推荐场景：**
- **新手/快速验证**：Kimi API
- **隐私/长期使用**：Ollama 本地模型
- **企业/已有 OpenAI 账号**：OpenAI API

## 开发指南

### 运行测试

```bash
cargo test
```

### 调试模式

```bash
RUST_LOG=debug cargo run
```

### 构建发布版本

```bash
cargo build --release
```

二进制文件路径：`target/release/tg-meme-token-monitor`

## 下一步开发计划

### 高优先级
1. [ ] 集成 Telegram 客户端库（grammers-client）
2. [ ] 实现消息实时接收
3. [ ] 实现报告推送功能

### 中优先级
4. [ ] 添加数据持久化（SQLite）
5. [ ] Web 管理界面
6. [ ] 合约地址自动验证
7. [ ] 多链支持（ETH, BSC, SOL）

### 低优先级
8. [ ] WebSocket 实时推送
9. [ ] 消息去重优化
10. [ ] 性能监控面板

## 常见问题

### Q1: 如何选择 AI 服务？

**A:** 参考上面对比表格。快速开始用 Kimi，长期使用选 Ollama。

### Q2: Ollama 需要什么硬件配置？

**A:** 最低要求：
- CPU: 4 核心
- RAM: 8GB（Llama 3 8B）
- 存储: 10GB（模型文件）

推荐配置：
- CPU: 8 核心
- RAM: 16GB
- SSD: 加快模型加载

### Q3: Kimi API 费用如何？

**A:** 参考价格：
- moonshot-v1-8k: ¥0.012 / 1K tokens
- 每次分析约 500-800 tokens
- 100 条消息/天 ≈ ¥5-8

### Q4: 如何获取 Telegram API ID 和 Hash？

**A:** 访问 https://my.telegram.org/auth，登录后创建应用即可获取。

### Q5: 如何获取 Telegram 频道 ID？

**A:** 向 @userinfobot 发送转发自该频道的消息，Bot 会返回频道 ID。

### Q6: 程序运行时报 API 错误？

**A:** 请检查：
1. API Key 是否正确
2. 网络连接是否正常
3. API 额度是否用尽
4. 配置文件中 provider 是否与实际配置匹配

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建

```bash
git clone https://github.com/yourusername/tg-meme-token-monitor.git
cd tg-meme-token-monitor
cargo build
```

### 提交规范

- 使用清晰的提交信息
- 添加适当的测试
- 更新 README.md（如有必要）
- 遵循 Rust 代码规范（cargo fmt, cargo clippy）

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 免责声明

本项目仅供学习和研究使用。使用本项目产生的任何损失，作者不承担责任。加密货币投资有风险，请谨慎决策。

## 致谢

- [Rust](https://rust-lang.org) - 优秀的编程语言
- [Ollama](https://ollama.ai) - 本地 LLM 运行环境
- [Kimi Moonshot](https://moonshot.cn) - 强大的中文 AI 模型
- [Grammers](https://github.com/Lonami/grammers) - Telegram 客户端库（计划集成）

## 联系方式

- 提交 Issue: [GitHub Issues](https://github.com/yourusername/tg-meme-token-monitor/issues)
- 邮箱: your.email@example.com

---

**🌟 Star 本项目以表示支持！**
