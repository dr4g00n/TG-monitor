use crate::ai::models::Message;
use crate::processor::MessageProcessor;
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Json},
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{error, info, warn};

/// 接收消息的请求体
#[derive(Deserialize, Debug, Serialize)]
pub struct ReceiveMessageRequest {
    pub channel_id: i64,
    pub channel_name: String,
    pub message_id: i32,
    pub text: String,
    pub timestamp: i64,
    pub sender: Option<String>,
}

/// 响应体
#[derive(Serialize, Deserialize)]
pub struct ApiResponse {
    pub success: bool,
    pub message: String,
    pub data: Option<serde_json::Value>,
}

impl ApiResponse {
    pub fn success(message: impl Into<String>) -> Self {
        Self {
            success: true,
            message: message.into(),
            data: None,
        }
    }

    pub fn error(message: impl Into<String>) -> Self {
        Self {
            success: false,
            message: message.into(),
            data: None,
        }
    }
}

impl IntoResponse for ApiResponse {
    fn into_response(self) -> axum::response::Response {
        let status = if self.success {
            StatusCode::OK
        } else {
            StatusCode::BAD_REQUEST
        };

        (status, Json(self)).into_response()
    }
}

/// 处理接收消息的端点
pub async fn receive_message(
    State(processor): State<Arc<MessageProcessor>>,
    Json(request): Json<ReceiveMessageRequest>,
) -> impl IntoResponse {
    info!(
        "收到来自 Python 监控器的消息: [{}] {}",
        request.channel_name, request.message_id
    );

    // 检查频道是否在监控列表中
    if processor.should_process_message(request.channel_id).await {
        // 转换为内部消息格式
        let message = Message {
            id: request.message_id as i64,
            channel_id: request.channel_id,
            channel_name: request.channel_name,
            text: request.text,
            timestamp: request.timestamp,
            sender: request.sender,
            media_type: None,
        };

        // 发送到消息处理器
        match processor.process_message(message).await {
            Ok(_) => {
                info!("消息已加入处理队列");
                ApiResponse::success("消息已接收并加入处理队列")
            }
            Err(e) => {
                error!("处理消息失败: {}", e);
                ApiResponse::error(format!("处理消息失败: {}", e))
            }
        }
    } else {
        warn!(
            "频道 {} 不在监控列表中，消息被忽略",
            request.channel_id
        );
        ApiResponse::error(format!(
            "频道 {} 不在监控列表中",
            request.channel_id
        ))
    }
}

/// 健康检查端点
pub async fn health_check() -> impl IntoResponse {
    ApiResponse::success("服务运行正常")
}
