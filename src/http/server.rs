use crate::http::handler;
use crate::processor::MessageProcessor;
use axum::{
    routing::{get, post},
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
            .route("/health", get(handler::health_check))
            .route("/api/v1/message", post(handler::receive_message))
            .layer(cors)
            .with_state(self.processor.clone());

        let addr = SocketAddr::from(([0, 0, 0, 0], self.port));

        info!("========================================");
        info!("HTTP 消息处理服务启动中...");
        info!("监听地址: http://{}", addr);
        info!("API 端点:");
        info!("  - GET  /health          - 健康检查");
        info!("  - POST /api/v1/message  - 接收消息");
        info!("========================================\n");

        // 启动服务器
        let listener = tokio::net::TcpListener::bind(addr).await?;
        axum::serve(listener, app).await?;

        Ok(())
    }
}
