pub mod local;
pub mod kimi;
pub mod openai;
pub mod models;

use async_trait::async_trait;
use crate::config::AIConfig;
use thiserror::Error;
use models::{AnalysisResult, AIProvider};

#[derive(Error, Debug)]
pub enum AIError {
    #[error("配置错误: {0}")]
    ConfigError(String),

    #[error("API 调用失败: {0}")]
    ApiError(String),

    #[error("响应解析失败: {0}")]
    ParseError(String),

    #[error("网络错误: {0}")]
    NetworkError(String),

    #[error("超时错误")]
    TimeoutError,

    #[error("不支持的提供商: {0}")]
    UnsupportedProvider(String),
}

/// AI 服务抽象接口
#[async_trait]
pub trait AIService: Send + Sync {
    /// 分析消息内容，返回结构化结果
    async fn analyze(&self, message: &str) -> Result<AnalysisResult, AIError>;

    /// 获取服务状态（健康检查）
    async fn health_check(&self) -> bool;

    /// 获取服务名称
    fn name(&self) -> String;

    /// 获取提供商类型
    fn provider(&self) -> AIProvider;
}

/// AI 服务工厂，根据配置创建对应的服务实例
pub struct AIServiceFactory;

impl AIServiceFactory {
    /// 根据配置创建 AI 服务
    pub fn create(config: &AIConfig) -> Result<Box<dyn AIService>, AIError> {
        let provider = config.provider.to_lowercase();

        match provider.as_str() {
            "ollama" | "local" => {
                info!("初始化 Ollama 本地服务...");
                let service = local::OllamaService::new(config)?;
                Ok(Box::new(service))
            }
            "kimi" => {
                info!("初始化 Kimi API 服务...");
                let service = kimi::KimiService::new(config)?;
                Ok(Box::new(service))
            }
            "openai" => {
                info!("初始化 OpenAI API 服务...");
                let service = openai::OpenAIService::new(config)?;
                Ok(Box::new(service))
            }
            _ => {
                error!("不支持的 AI 提供商: {}", provider);
                Err(AIError::UnsupportedProvider(provider))
            }
        }
    }
}

use tracing::{info, error, debug};
use serde_json::Value;

/// 通用响应解析函数
pub fn parse_analysis_response(content: &str, original_message: &str, source: &str) -> Result<AnalysisResult, AIError> {
    // 首先尝试解析 JSON 格式的响应
    if let Ok(json_data) = serde_json::from_str::<Value>(content) {
        debug!("成功解析 JSON 响应，来源: {}", source);

        // 如果 JSON 包含完整的分析结果
        if let Some(is_relevant) = json_data["is_relevant"].as_bool() {
            return Ok(AnalysisResult {
                is_relevant,
                token_name: json_data["token_name"].as_str().map(String::from),
                contract_address: json_data["contract_address"].as_str().map(String::from),
                recommendation: json_data["recommendation"].as_str().map(String::from),
                reason: json_data["reason"].as_str().map(String::from),
                confidence: json_data["confidence"].as_f64().unwrap_or(0.0) as f32,
                urgency: json_data["urgency"].as_i64().unwrap_or(0) as i32,
                source: source.to_string(),
                timestamp: chrono::Utc::now().timestamp(),
                raw_response: Some(content.to_string()),
            });
        }

        // 如果 JSON 不包含标准格式，尝试提取关键信息
        if is_token_related_message(original_message) {
            info!("消息内容与 Token 相关，但响应格式不标准，手动解析");

            return Ok(AnalysisResult {
                is_relevant: true,
                token_name: extract_token_name(original_message),
                contract_address: extract_contract_address(original_message),
                recommendation: extract_recommendation(&json_data, content),
                reason: json_data["reason"].as_str().or(Some(content)).map(String::from),
                confidence: 0.6,
                urgency: 5,
                source: source.to_string(),
                timestamp: chrono::Utc::now().timestamp(),
                raw_response: Some(content.to_string()),
            });
        }
    }

    // 如果不是 JSON，使用启发式方法判断
    info!("响应不是标准 JSON，使用启发式分析");

    let is_relevant = is_token_related_message(original_message);

    Ok(AnalysisResult {
        is_relevant,
        token_name: extract_token_name(original_message),
        contract_address: extract_contract_address(original_message),
        recommendation: if is_relevant { extract_recommendation_from_text(content) } else { None },
        reason: if is_relevant { Some(content.to_string()) } else { None },
        confidence: if is_relevant { 0.5 } else { 0.0 },
        urgency: if is_relevant { 5 } else { 0 },
        source: source.to_string(),
        timestamp: chrono::Utc::now().timestamp(),
        raw_response: Some(content.to_string()),
    })
}

/// 启发式判断消息是否与 Token 相关
fn is_token_related_message(message: &str) -> bool {
    let lower_msg = message.to_lowercase();
    let keywords = [
        "token", "代币", "合约", "address", "地址", "买入", "卖出",
        "hold", "持有", "buy", "sell", "合约地址", "token address",
        "发射", "launch", "池子", "pool", "liquidity", "流动性",
        "chart", "k线", "阳线", "阴线", "突破", "break",
    ];

    keywords.iter().any(|&kw| lower_msg.contains(kw))
}

/// 提取 Token 名称
fn extract_token_name(message: &str) -> Option<String> {
    // 简单的启发式：查找大写的单词（可能是 Token 名称）
    let words: Vec<&str> = message.split_whitespace().collect();
    for word in words {
        if word.len() >= 2 && word.len() <= 10 && word.chars().all(|c| c.is_uppercase() || c.is_ascii_digit()) {
            return Some(word.to_string());
        }
    }
    None
}

/// 提取合约地址（简单的 ETH/BSC 地址格式匹配）
fn extract_contract_address(message: &str) -> Option<String> {
    use regex::Regex;

    // 0x 开头的 42 位地址
    let re = Regex::new(r"0x[a-fA-F0-9]{40}").ok()?;
    re.find(message).map(|m| m.as_str().to_string())
}

/// 从 JSON 数据中提取交易建议
fn extract_recommendation(json_data: &Value, _raw_content: &str) -> Option<String> {
    // 首先从标准字段提取
    if let Some(rec) = json_data["recommendation"].as_str() {
        return Some(rec.to_string());
    }

    // 从内容中通过关键词提取
    let content = json_data["content"]
        .as_str()
        .or_else(|| json_data["response"].as_str())?;

    extract_recommendation_from_text(content)
}

/// 从文本中提取交易建议
fn extract_recommendation_from_text(content: &str) -> Option<String> {
    let lower = content.to_lowercase();

    if lower.contains("buy") || lower.contains("买入") {
        Some("买入".to_string())
    } else if lower.contains("sell") || lower.contains("卖出") {
        Some("卖出".to_string())
    } else if lower.contains("hold") || lower.contains("持有") {
        Some("持有".to_string())
    } else {
        None
    }
}
