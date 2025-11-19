use crate::config::TelegramConfig;
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use tracing::{error, info};

/// Telegram Bot API 客户端
pub struct TelegramBot {
    token: String,
    target_user: i64,
    client: reqwest::Client,
}

#[derive(Serialize)]
struct SendMessageRequest<'a> {
    chat_id: i64,
    text: &'a str,
    parse_mode: &'a str,
}

#[derive(Deserialize, Debug)]
struct TelegramResponse {
    ok: bool,
    #[serde(default)]
    description: Option<String>,
}

impl TelegramBot {
    /// 创建 Bot 客户端
    pub fn new(config: TelegramConfig) -> Self {
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("创建 HTTP 客户端失败");

        Self {
            token: config.bot_token,
            target_user: config.target_user,
            client,
        }
    }

    /// 发送消息给用户
    pub async fn send_message(&self, text: &str) -> Result<()> {
        let url = format!("https://api.telegram.org/bot{}/sendMessage", self.token);

        let request = SendMessageRequest {
            chat_id: self.target_user,
            text,
            parse_mode: "Markdown",
        };

        info!("发送消息到用户 {} (长度: {} 字符)", self.target_user, text.len());

        let response = self
            .client
            .post(&url)
            .json(&request)
            .send()
            .await
            .context("发送 Telegram 消息失败")?;

        let status = response.status();
        let body = response
            .text()
            .await
            .context("读取响应失败")?;

        if status.is_success() {
            // 解析响应
            let result: TelegramResponse = serde_json::from_str(&body)
                .context("解析 Telegram 响应失败")?;

            if result.ok {
                info!("✓ 消息发送成功");
                Ok(())
            } else {
                error!("✗ Telegram API 错误: {:?}", result.description);
                anyhow::bail!("Telegram API 错误: {:?}", result.description);
            }
        } else {
            error!("✗ HTTP 请求失败: {} - {}", status, body);
            anyhow::bail!("HTTP 请求失败: {} - {}", status, body);
        }
    }

    /// 健康检查（验证 Bot Token 是否有效）
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("https://api.telegram.org/bot{}/getMe", self.token);

        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    info!("✓ Telegram Bot Token 验证通过");
                    Ok(true)
                } else {
                    error!("✗ Telegram Bot Token 验证失败: {}", response.status());
                    Ok(false)
                }
            }
            Err(e) => {
                error!("✗ Telegram Bot Token 验证失败: {}", e);
                Ok(false)
            }
        }
    }
}
