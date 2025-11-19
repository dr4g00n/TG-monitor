use super::{AIService, AIError};
use super::models::AnalysisResult;
use async_trait::async_trait;
use config::{AIConfig, KimiConfig};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::time::Duration;
use tracing::{debug, error, info};

/// Kimi API 服务实现
pub struct KimiService {
    client: Client,
    config: KimiConfig,
    timeout: Duration,
    prompt_template: String,
    max_retries: u32,
}

impl KimiService {
    /// 创建 Kimi 服务实例
    pub fn new(ai_config: &AIConfig) -> Result<Self, AIError> {
        let kimi_config = ai_config.kimi.as_ref()
            .ok_or_else(|| AIError::ConfigError("Kimi 配置未找到".to_string()))?;

        let client = Client::builder()
            .timeout(Duration::from_secs(ai_config.timeout_seconds))
            .build()
            .map_err(|e| AIError::NetworkError(e.to_string()))?;

        Ok(Self {
            client,
            config: kimi_config.clone(),
            timeout: Duration::from_secs(ai_config.timeout_seconds),
            prompt_template: ai_config.prompt_template.clone(),
            max_retries: ai_config.max_retries,
        })
    }

    /// 构建系统提示词
    fn build_system_prompt(&self) -> String {
        r#"你是一名专业的加密货币交易信息分析师。

你的任务是分析 Telegram 消息，判断是否在讨论 meme token 交易信息。

如果是相关消息，请提取以下信息并以 JSON 格式返回：
{
  "is_relevant": true,
  "token_name": "Token名称（如果有）",
  "contract_address": "合约地址（ETH/BSC格式：0x...）",
  "recommendation": "买入/卖出/持有",
  "reason": "详细的推荐理由",
  "confidence": 0.85,
  "urgency": 7
}

如果不是相关消息，返回：
{"is_relevant": false}

注意：
- confidence 是 0.0 到 1.0 之间的浮点数
- urgency 是 1 到 10 之间的整数（1=不紧急，10=非常紧急）
- 只返回 JSON，不要包含其他文本
"#.to_string()
    }

    /// 构建完整的提示词
    fn build_prompt(&self, message: &str) -> String {
        self.prompt_template.replace("{}", message)
    }

    /// 解析 JSON 响应
    fn parse_response(&self, content: &str, original_message: &str) -> Result<AnalysisResult, AIError> {
        use super::parse_analysis_response;
        parse_analysis_response(content, original_message, "kimi")
            .map_err(|e| AIError::ParseError(e.to_string()))
    }
}

#[async_trait]
impl AIService for KimiService {
    async fn analyze(&self, message: &str) -> Result<AnalysisResult, AIError> {
        debug!("使用 Kimi 分析消息: {}", message[..message.len().min(50)].to_string());

        // 构建请求体
        let request_body = serde_json::json!({
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.build_system_prompt()
                },
                {
                    "role": "user",
                    "content": self.build_prompt(message)
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": false
        });

        debug!("发送请求到 Kimi API...");

        // 发送请求并处理重试
        let mut last_error = None;
        for attempt in 0..=self.max_retries {
            if attempt > 0 {
                info!("第 {} 次重试...", attempt);
                tokio::time::sleep(Duration::from_secs(2_u64.pow(attempt - 1))).await;
            }

            match self.client
                .post(format!("{}/chat/completions", self.config.base_url))
                .header("Authorization", format!("Bearer {}", self.config.api_key))
                .header("Content-Type", "application/json")
                .json(&request_body)
                .timeout(self.timeout)
                .send()
                .await
            {
                Ok(response) => {
                    let status = response.status();

                    if status.is_success() {
                        match response.json::<Value>().await {
                            Ok(result) => {
                                debug!("成功收到 Kimi API 响应");

                                // 提取 content
                                let content = result["choices"][0]["message"]["content"]
                                    .as_str()
                                    .ok_or_else(|| AIError::ParseError("响应中没有 content 字段".to_string()))?;

                                return self.parse_response(content, message);
                            }
                            Err(e) => {
                                error!("解析 Kimi API 响应失败: {}", e);
                                last_error = Some(AIError::ParseError(e.to_string()));
                            }
                        }
                    } else {
                        let error_text = response.text().await
                            .unwrap_or_else(|_| "无法读取错误信息".to_string());
                        error!("Kimi API 返回错误状态 {}: {}", status, error_text);
                        last_error = Some(AIError::ApiError(format!("HTTP {}: {}", status, error_text)));
                    }
                }
                Err(e) => {
                    error!("请求 Kimi API 失败: {}", e);
                    last_error = Some(AIError::NetworkError(e.to_string()));
                }
            }
        }

        Err(last_error.unwrap_or_else(|| AIError::ApiError("所有重试均失败".to_string())))
    }

    async fn health_check(&self) -> bool {
        debug!("检查 Kimi API 健康状态...");

        let request_body = serde_json::json!({
            "model": self.config.model,
            "messages": [{
                "role": "user",
                "content": "Hi"
            }],
            "max_tokens": 1,
            "stream": false
        });

        match self.client
            .post(format!("{}/chat/completions", self.config.base_url))
            .header("Authorization", format!("Bearer {}", self.config.api_key))
            .json(&request_body)
            .timeout(Duration::from_secs(10))
            .send()
            .await
        {
            Ok(response) => {
                let is_success = response.status().is_success();
                if is_success {
                    info!("✓ Kimi API 健康检查通过");
                } else {
                    error!("✗ Kimi API 健康检查失败: HTTP {}", response.status());
                }
                is_success
            }
            Err(e) => {
                error!("✗ Kimi API 健康检查失败: {}", e);
                false
            }
        }
    }

    fn name(&self) -> &str {
        &format!("Kimi API Service ({})", self.config.model)
    }

    fn provider(&self) -> AIProvider {
        AIProvider::Kimi
    }
}

// Kimi API 响应结构
#[derive(Deserialize)]
struct KimiResponse {
    choices: Vec<KimiChoice>,
    usage: Option<KimiUsage>,
}

#[derive(Deserialize)]
struct KimiChoice {
    message: KimiMessage,
    finish_reason: String,
}

#[derive(Deserialize)]
struct KimiMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct KimiUsage {
    prompt_tokens: u32,
    completion_tokens: u32,
    total_tokens: u32,
}

// Kimi API 错误响应
#[derive(Deserialize)]
struct KimiErrorResponse {
    error: KimiErrorDetail,
}

#[derive(Deserialize)]
struct KimiErrorDetail {
    message: String,
    code: String,
}
