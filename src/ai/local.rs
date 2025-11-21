use super::{AIService, AIError};
use super::models::{AnalysisResult, AIProvider};
use async_trait::async_trait;
use crate::config::{AIConfig, OllamaConfig};
use reqwest::Client;
use serde::Deserialize;
use serde_json::Value;
use std::time::Duration;
use tracing::{debug, error, info};

/// Ollama 本地服务实现
pub struct OllamaService {
    client: Client,
    config: OllamaConfig,
    timeout: Duration,
    prompt_template: String,
    max_retries: u32,
}

impl OllamaService {
    /// 创建 Ollama 服务实例
    pub fn new(ai_config: &AIConfig) -> Result<Self, AIError> {
        let ollama_config = ai_config.ollama.as_ref()
            .ok_or_else(|| AIError::ConfigError("Ollama 配置未找到".to_string()))?;

        let client = Client::builder()
            .timeout(Duration::from_secs(ai_config.timeout_seconds))
            .build()
            .map_err(|e| AIError::NetworkError(e.to_string()))?;

        Ok(Self {
            client,
            config: ollama_config.clone(),
            timeout: Duration::from_secs(ai_config.timeout_seconds),
            prompt_template: ai_config.prompt_template.clone(),
            max_retries: ai_config.max_retries,
        })
    }

    /// 构建完整的提示词
    fn build_prompt(&self, message: &str) -> String {
        // 在 Ollama 中使用模板直接包含系统提示
        self.prompt_template.replace("{}", message)
    }
}

#[async_trait]
impl AIService for OllamaService {
    async fn analyze(&self, message: &str) -> Result<AnalysisResult, AIError> {
        // UTF-8安全的字符截断
        let preview: String = message.chars().take(50).collect();
        debug!("使用 Ollama 本地模型分析消息: {}", preview);

        // 构建请求体
        let request_body = serde_json::json!({
            "model": self.config.model,
            "prompt": self.build_prompt(message),
            "stream": false,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        });

        debug!("发送请求到 Ollama: {}", self.config.api_endpoint);

        // 发送请求并处理重试
        let mut last_error = None;
        for attempt in 0..=self.max_retries {
            if attempt > 0 {
                info!("第 {} 次重试...", attempt);
                tokio::time::sleep(Duration::from_secs(2_u64.pow(attempt - 1))).await;
            }

            match self.client
                .post(format!("{}/api/generate", self.config.api_endpoint))
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
                                debug!("成功收到 Ollama 本地模型响应");

                                // Ollama 的响应在 "response" 字段
                                let content = result["response"]
                                    .as_str()
                                    .ok_or_else(|| {
                                        AIError::ParseError("响应中没有 response 字段".to_string())
                                    })?;

                                return self.parse_response(content, message);
                            }
                            Err(e) => {
                                error!("解析 Ollama 响应失败: {}", e);
                                last_error = Some(AIError::ParseError(e.to_string()));
                            }
                        }
                    } else {
                        let error_text = response.text().await
                            .unwrap_or_else(|_| "无法读取错误信息".to_string());
                        error!("Ollama 返回错误 {}: {}", status, error_text);
                        last_error = Some(AIError::ApiError(format!(
                            "HTTP {}: {}", status, error_text)));
                    }
                }
                Err(e) => {
                    error!("连接 Ollama 失败: {}", e);
                    last_error = Some(AIError::NetworkError(e.to_string()));
                }
            }
        }

        Err(last_error.unwrap_or_else(|| AIError::ApiError("所有重试均失败".to_string())))
    }

    async fn health_check(&self) -> bool {
        debug!("检查 Ollama 服务健康状态...");

        let request_body = serde_json::json!({
            "model": self.config.model,
            "prompt": "Hi",
            "stream": false,
            "options": {
                "max_tokens": 1,
            }
        });

        match self.client
            .post(format!("{}/api/generate", self.config.api_endpoint))
            .json(&request_body)
            .timeout(Duration::from_secs(10))
            .send()
            .await
        {
            Ok(response) => {
                let is_success = response.status().is_success();
                if is_success {
                    info!("✓ Ollama 本地服务健康检查通过");
                } else {
                    error!("✗ Ollama 健康检查失败: HTTP {}", response.status());
                }
                is_success
            }
            Err(e) => {
                error!("✗ 无法连接 Ollama 服务: {}", e);
                error!("  请确保: 1) Ollama 已安装 2) 服务正在运行 3) 模型已下载");
                false
            }
        }
    }

    fn name(&self) -> String {
        format!("Ollama Local Service ({})", self.config.model)
    }

    fn provider(&self) -> AIProvider {
        AIProvider::Ollama
    }
}

impl OllamaService {
    /// 解析响应内容
    fn parse_response(&self, content: &str, original_message: &str) -> Result<AnalysisResult, AIError> {
        use super::parse_analysis_response;
        parse_analysis_response(content, original_message, "local")
            .map_err(|e| AIError::ParseError(e.to_string()))
    }
}

/// Ollama API 响应（字段由反序列化使用）
#[derive(Deserialize)]
#[allow(dead_code)]
struct OllamaResponse {
    response: String,
    done: bool,
    context: Option<Vec<u32>>,
}

/// Ollama 模型信息（字段由反序列化使用）
#[derive(Deserialize)]
#[allow(dead_code)]
struct OllamaModelInfo {
    name: String,
    model: String,
    size: u64,
    digest: String,
}
