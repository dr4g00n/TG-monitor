use serde::{Deserialize, Serialize};
use std::fmt;

/// 分析结果结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    /// 是否与 Token 交易相关
    pub is_relevant: bool,

    /// Token 名称
    pub token_name: Option<String>,

    /// 合约地址
    pub contract_address: Option<String>,

    /// 交易建议: 买入/卖出/持有
    pub recommendation: Option<String>,

    /// 推荐理由
    pub reason: Option<String>,

    /// 置信度 (0.0 - 1.0)
    pub confidence: f32,

    /// 紧急程度 (1-10)
    pub urgency: i32,

    /// AI 来源: "local" or "kimi" or "openai"
    pub source: String,

    /// 时间戳（Unix 秒）
    pub timestamp: i64,

    /// 原始响应（用于调试）
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw_response: Option<String>,
}

impl AnalysisResult {
    /// 创建空的分析结果
    pub fn empty() -> Self {
        Self {
            is_relevant: false,
            token_name: None,
            contract_address: None,
            recommendation: None,
            reason: None,
            confidence: 0.0,
            urgency: 0,
            source: String::new(),
            timestamp: chrono::Utc::now().timestamp(),
            raw_response: None,
        }
    }

    /// 判断此结果是否有效（置信度达标）
    pub fn is_valid(&self, min_confidence: f32) -> bool {
        self.is_relevant && self.confidence >= min_confidence
    }

    /// 获取处理建议
    pub fn get_action_suggestion(&self) -> String {
        match self.recommendation.as_deref() {
            Some("买入") | Some("buy") => "🟢 买入".to_string(),
            Some("卖出") | Some("sell") => "🔴 卖出".to_string(),
            Some("持有") | Some("hold") => "🟡 持有".to_string(),
            _ => "⚪ 观望".to_string(),
        }
    }

    /// 格式化输出
    pub fn format_summary(&self) -> String {
        if !self.is_relevant {
            return "不相关的消息".to_string();
        }

        let mut summary = String::new();

        // Token 名称
        if let Some(token_name) = &self.token_name {
            summary.push_str(&format!("> **Token**: {}\n", token_name));
        }

        // 合约地址
        if let Some(contract) = &self.contract_address {
            summary.push_str(&format!("> **合约**: `{}`\n", contract));
        }

        // 交易建议
        summary.push_str(&format!("> **建议**: {}\n", self.get_action_suggestion()));

        // 推荐理由（可选）
        if let Some(reason) = &self.reason {
            if !reason.is_empty() {
                summary.push_str(&format!("> **理由**: {}\n", reason.trim()));
            }
        }

        // 置信度和紧急程度
        summary.push_str(&format!("> **置信度**: {:.1}% | **紧急度**: {}/10\n",
            self.confidence * 100.0,
            self.urgency
        ));

        // AI 来源
        summary.push_str(&format!("> **来源**: {}\n", self.source));

        summary
    }
}

/// AI 服务提供商枚举
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AIProvider {
    Ollama,
    Kimi,
    OpenAI,
}

impl fmt::Display for AIProvider {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AIProvider::Ollama => write!(f, "ollama"),
            AIProvider::Kimi => write!(f, "kimi"),
            AIProvider::OpenAI => write!(f, "openai"),
        }
    }
}

impl From<&str> for AIProvider {
    fn from(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "ollama" | "local" => AIProvider::Ollama,
            "kimi" => AIProvider::Kimi,
            "openai" => AIProvider::OpenAI,
            _ => AIProvider::Kimi, // 默认
        }
    }
}

/// 消息结构
#[derive(Debug, Clone)]
pub struct Message {
    /// 消息 ID
    pub id: i64,

    /// 频道 ID
    pub channel_id: i64,

    /// 频道名称
    pub channel_name: String,

    /// 消息文本内容
    pub text: String,

    /// 时间戳（Unix 秒）
    pub timestamp: i64,

    /// 发送者（如果有）
    pub sender: Option<String>,

    /// 媒体类型（如果有）
    pub media_type: Option<String>,
}

impl Message {
    /// 创建消息
    pub fn new(id: i64, channel_id: i64, channel_name: String, text: String, timestamp: i64) -> Self {
        Self {
            id,
            channel_id,
            channel_name,
            text,
            timestamp,
            sender: None,
            media_type: None,
        }
    }

    /// 是否为媒体消息
    pub fn has_media(&self) -> bool {
        self.media_type.is_some()
    }

    /// 消息摘要（用于日志）
    pub fn summary(&self) -> String {
        let preview = if self.text.len() > 50 {
            format!("{}...", &self.text[..50])
        } else {
            self.text.clone()
        };

        format!("[{}] {}: {}", self.channel_name, self.id, preview)
    }
}

/// Token 信息汇总
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenInfo {
    /// Token 名称
    pub name: String,

    /// 合约地址
    pub contract_address: Option<String>,

    /// 被提及次数
    pub mentions: i32,

    /// 来源频道列表
    pub sources: Vec<String>,

    /// 主要建议（买入/卖出/持有）
    pub recommendation: String,

    /// 平均置信度
    pub avg_confidence: f32,

    /// 最早出现时间
    pub first_seen: i64,

    /// 最新出现时间
    pub last_seen: i64,
}

impl TokenInfo {
    /// 创建 Token 信息
    pub fn from_analysis(results: &[AnalysisResult]) -> Option<Self> {
        if results.is_empty() {
            return None;
        }

        let first = &results[0];
        let token_name = first.token_name.as_ref()?.clone();
        let contract_address = first.contract_address.clone();

        // 统计信息
        let mentions = results.len() as i32;
        let mut sources = Vec::new();
        let mut recommendations = Vec::new();
        let mut total_confidence = 0.0;
        let mut first_seen = first.timestamp;
        let mut last_seen = first.timestamp;

        for result in results {
            if !sources.contains(&result.source) {
                sources.push(result.source.clone());
            }

            if let Some(rec) = &result.recommendation {
                recommendations.push(rec.clone());
            }

            total_confidence += result.confidence;
        }

        let avg_confidence = if recommendations.is_empty() {
            0.0
        } else {
            total_confidence / mentions as f32
        };

        // 统计最常见的建议
        let recommendation = if recommendations.is_empty() {
            "观望".to_string()
        } else {
            find_most_common(recommendations)
        };

        Some(Self {
            name: token_name,
            contract_address,
            mentions,
            sources,
            recommendation,
            avg_confidence,
            first_seen,
            last_seen,
        })
    }

    /// 格式化输出
    pub fn format_detail(&self) -> String {
        format!(
            "📊 **Token 分析报告: {}**\n\
             > **合约**: {}\n\
             > **提及次数**: {}\n\
             > **来源频道**: {}\n\
             > **主要建议**: {}\n\
             > **平均置信度**: {:.1}%\n\
             > **首次出现**: {}\n\
             > **最新出现**: {}",
            self.name,
            self.contract_address.as_deref().unwrap_or("未提供"),
            self.mentions,
            self.sources.join(", "),
            self.recommendation,
            self.avg_confidence * 100.0,
            format_timestamp(self.first_seen),
            format_timestamp(self.last_seen),
        )
    }
}

/// 汇总报告
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SummaryReport {
    /// Token 列表
    pub tokens: Vec<TokenInfo>,

    /// 报告生成时间（Unix 秒）
    pub generated_at: i64,

    /// 包含的消息总数
    pub total_messages: usize,

    /// 相关消息数
    pub relevant_messages: usize,
}

impl SummaryReport {
    /// 创建汇总报告
    pub fn new(tokens: Vec<TokenInfo>, total_messages: usize, relevant_messages: usize) -> Self {
        Self {
            tokens,
            generated_at: chrono::Utc::now().timestamp(),
            total_messages,
            relevant_messages,
        }
    }

    /// 是否为空
    pub fn is_empty(&self) -> bool {
        self.tokens.is_empty()
    }

    /// 格式化输出完整报告
    pub fn format_full_report(&self) -> String {
        if self.is_empty() {
            return "📈 **Meme Token 监控报告**\n\n没有找到相关的 Token 交易信息。".to_string();
        }

        let mut report = String::new();
        report.push_str("📈 **Meme Token 监控报告**\n\n");
        report.push_str(&format!(
            "📊 **统计**: {} 条消息中，{} 条相关\n\n",
            self.total_messages, self.relevant_messages
        ));

        for (i, token) in self.tokens.iter().enumerate() {
            report.push_str(&format!("{}. {}\n", i + 1, token.format_detail()));
            report.push('\n');
        }

        report.push_str(&format!("⏰ **生成时间**: {}", format_timestamp(self.generated_at)));

        report
    }
}

/// 辅助函数：查找列表中最常见的元素
fn find_most_common(items: Vec<String>) -> String {
    use std::collections::HashMap;

    let mut counts = HashMap::new();
    for item in &items {
        *counts.entry(item).or_insert(0) += 1;
    }

    counts
        .into_iter()
        .max_by_key(|(_, count)| *count)
        .map(|(item, _)| item.clone())
        .unwrap_or_else(|| items[0].clone())
}

/// 格式化时间戳
fn format_timestamp(timestamp: i64) -> String {
    use chrono::{DateTime, Utc};

    let dt: DateTime<Utc> = DateTime::from_timestamp(timestamp, 0)
        .unwrap_or_else(|| DateTime::from_timestamp(0, 0).unwrap());
    dt.format("%Y-%m-%d %H:%M:%S UTC").to_string()
}

use tracing::debug;
