use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

/// 主配置结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub telegram: TelegramConfig,
    pub ai: AIConfig,
    pub processing: ProcessingConfig,
}

impl Config {
    /// 从文件加载配置
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref();

        if !path.exists() {
            anyhow::bail!("配置文件不存在: {}", path.display());
        }

        let content = fs::read_to_string(path)
            .with_context(|| format!("无法读取配置文件: {}", path.display()))?;

        let config: Config = toml::from_str(&content)
            .with_context(|| format!("配置文件格式错误: {}", path.display()))?;

        // 验证配置
        config.validate()?;

        Ok(config)
    }

    /// 验证配置的有效性
    fn validate(&self) -> Result<()> {
        // 验证 Telegram 配置
        if self.telegram.api_id == 0 {
            anyhow::bail!("telegram.api_id 不能为空或 0");
        }

        if self.telegram.api_hash.is_empty() {
            anyhow::bail!("telegram.api_hash 不能为空");
        }

        if self.telegram.source_channels.is_empty() {
            anyhow::bail!("至少需要配置一个 source_channel");
        }

        if self.telegram.target_user == 0 {
            anyhow::bail!("telegram.target_user 不能为空或 0");
        }

        // 验证 AI 配置
        if self.ai.provider.is_empty() {
            anyhow::bail!("ai.provider 不能为空");
        }

        match self.ai.provider.as_str() {
            "ollama" | "local" => {
                if self.ai.ollama.is_none() {
                    anyhow::bail!("使用 ollama 时，必须配置 [ai.ollama]");
                }
            }
            "kimi" => {
                if self.ai.kimi.is_none() {
                    anyhow::bail!("使用 kimi 时，必须配置 [ai.kimi]");
                }
                let kimi = self.ai.kimi.as_ref().unwrap();
                if kimi.api_key.starts_with("sk-") && kimi.api_key.len() < 10 {
                    anyhow::bail!("ai.kimi.api_key 格式不正确");
                }
            }
            "openai" => {
                if self.ai.openai.is_none() {
                    anyhow::bail!("使用 openai 时，必须配置 [ai.openai]");
                }
            }
            _ => {
                anyhow::bail!(
                    "不支持的 ai.provider: {}，支持: ollama, kimi, openai",
                    self.ai.provider
                );
            }
        }

        // 验证处理配置
        if self.processing.batch_size == 0 {
            anyhow::bail!("processing.batch_size 必须大于 0");
        }

        if self.processing.batch_timeout_seconds == 0 {
            anyhow::bail!("processing.batch_timeout_seconds 必须大于 0");
        }

        if self.processing.min_confidence < 0.0 || self.processing.min_confidence > 1.0 {
            anyhow::bail!("processing.min_confidence 必须在 0.0 到 1.0 之间");
        }

        Ok(())
    }
}

/// Telegram 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelegramConfig {
    pub api_id: i32,
    pub api_hash: String,
    pub session_file: String,
    pub source_channels: Vec<i64>,
    pub target_user: i64,
}

/// AI 服务配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIConfig {
    /// 服务提供商: "ollama", "kimi", "openai"
    pub provider: String,

    /// 超时时间（秒）
    pub timeout_seconds: u64,

    /// 最大重试次数
    pub max_retries: u32,

    /// Prompt 模板，支持 {} 占位符
    pub prompt_template: String,

    /// Ollama 本地配置（当 provider = "ollama" 时生效）
    pub ollama: Option<OllamaConfig>,

    /// Kimi API 配置（当 provider = "kimi" 时生效）
    pub kimi: Option<KimiConfig>,

    /// OpenAI API 配置（当 provider = "openai" 时生效）
    pub openai: Option<OpenAIConfig>,
}

/// Ollama 本地配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaConfig {
    /// API 地址，例如: "http://localhost:11434"
    pub api_endpoint: String,

    /// 模型名称，例如: "llama3:8b"
    pub model: String,
}

/// Kimi API 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KimiConfig {
    /// API Key，例如: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    pub api_key: String,

    /// 模型名称，例如: "moonshot-v1-8k"
    pub model: String,

    /// 基础 URL，默认: "https://api.moonshot.cn/v1"
    pub base_url: String,
}

impl KimiConfig {
    pub fn default_base_url() -> String {
        "https://api.moonshot.cn/v1".to_string()
    }
}

/// OpenAI API 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenAIConfig {
    /// API Key
    pub api_key: String,

    /// 模型名称，例如: "gpt-3.5-turbo"
    pub model: String,

    /// 基础 URL，默认: "https://api.openai.com/v1"
    /// 可以替换为其他兼容接口（如 DeepSeek）
    pub base_url: String,
}

impl OpenAIConfig {
    pub fn default_base_url() -> String {
        "https://api.openai.com/v1".to_string()
    }
}

/// 消息处理配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingConfig {
    /// 每批处理的消息数量
    pub batch_size: usize,

    /// 批处理超时时间（秒），达到此时间即使没有满也会发送
    pub batch_timeout_seconds: u64,

    /// 最小置信度（0.0-1.0），低于此值的消息将被过滤
    pub min_confidence: f32,

    /// 关键词过滤（可选），包含这些词的消息优先处理
    pub keywords: Vec<String>,
}
