use crate::http::{handler, channel_handler};
use crate::processor::MessageProcessor;
use axum::{
    routing::{get, post, put, delete},
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tracing::info;

/// HTTP 服务器
pub struct HttpServer {
    processor: Arc<MessageProcessor>,
    port: u16,
}

impl HttpServer {
    /// 创建 HTTP 服务器
    pub fn new(processor: Arc<MessageProcessor>, port: u16) -> Self {
        Self { processor, port }
    }

    /// 启动服务器
    pub async fn start(&self) -> anyhow::Result<()> {
        // 配置 CORS
        let cors = CorsLayer::new()
            .allow_origin(Any)
            .allow_methods(Any)
            .allow_headers(Any);

        // 配置路由
        let app = Router::new()
            // 健康检查
            .route("/health", get(handler::health_check))
            // 消息接收
            .route("/api/v1/message", post(handler::receive_message))
            // 频道管理
            .route("/api/v1/channels", get(channel_handler::get_channels))
            .route("/api/v1/channels", post(channel_handler::add_channel))
            .route("/api/v1/channels", put(channel_handler::update_channels))
            .route("/api/v1/channels/:channel_id", delete(channel_handler::remove_channel))
            .route("/api/v1/channels/:channel_id/check", get(channel_handler::check_channel))
            .layer(cors)
            .with_state(self.processor.clone());

        let addr = SocketAddr::from(([0, 0, 0, 0], self.port));

        info!("========================================");
        info!("HTTP 消息处理服务启动中...");
        info!("监听地址: http://{}", addr);
        info!("API 端点:");
        info!("  - GET  /health                          - 健康检查");
        info!("  - POST /api/v1/message                  - 接收消息");
        info!("  - GET  /api/v1/channels                 - 获取频道列表");
        info!("  - POST /api/v1/channels                 - 添加频道");
        info!("  - PUT  /api/v1/channels                 - 更新频道列表");
        info!("  - DELETE /api/v1/channels/:channel_id   - 删除频道");
        info!("  - GET  /api/v1/channels/:channel_id/check - 检查频道");
        info!("========================================\n");

        // 启动服务器
        let listener = tokio::net::TcpListener::bind(addr).await?;
        axum::serve(listener, app).await?;

        Ok(())
    }
}
