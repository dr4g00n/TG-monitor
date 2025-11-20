// 集成测试：测试完整的端到端消息处理流程

use serde_json::json;
use std::sync::Arc;
use tokio::time::{sleep, Duration};
use tower::ServiceExt; // For .oneshot()

// 注意：集成测试需要访问 src 中的私有模块
// 我们会在 Cargo.toml 中配置 [lib] 来暴露这些模块

#[cfg(test)]
mod integration_tests {
    use super::*;
    use tg_meme_token_monitor::{
        ai::AIServiceFactory,
        config::{AIConfig, Config, ProcessingConfig, TelegramConfig, HttpConfig, KimiConfig},
        http::handler::{ApiResponse, ReceiveMessageRequest},
        processor::MessageProcessor,
    };
    use axum::{body::Body, http::{Request, StatusCode}, Router};

    fn create_test_request() -> ReceiveMessageRequest {
        ReceiveMessageRequest {
            channel_id: -1001234567890,
            channel_name: "TestChannel".to_string(),
            message_id: 12345,
            text: "新币发布 TESTTOKEN 合约地址 0x1234567890abcdef 即将起飞".to_string(),
            timestamp: chrono::Utc::now().timestamp(),
            sender: Some("TestUser".to_string()),
        }
    }

    // 测试配置加载
    #[tokio::test]
    async fn test_config_loading() {
        let config = Config::load("config.toml").expect("Should load config");
        assert_eq!(config.http.port, 8080);
        assert_eq!(config.ai.provider, "kimi");
        assert!(config.processing.batch_size > 0);
    }

    // 测试健康检查端点
    #[tokio::test]
    async fn test_health_check_endpoint() {
        let app = create_test_app().await;

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/health")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = axum::body::to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap();
        let api_response: ApiResponse = serde_json::from_slice(&body).unwrap();
        assert!(api_response.success);
        assert_eq!(api_response.message, "服务运行正常");
    }

    // 测试接收消息端点
    #[tokio::test]
    async fn test_receive_message_endpoint() {
        let app = create_test_app().await;
        let request = create_test_request();

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/message")
                    .header("content-type", "application/json")
                    .body(Body::from(serde_json::to_string(&request).unwrap()))
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = axum::body::to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap();
        let api_response: ApiResponse = serde_json::from_slice(&body).unwrap();
        assert!(api_response.success);
        assert!(api_response.message.contains("消息已接收"));
    }

    // 测试 AI 服务健康检查
    #[tokio::test]
    async fn test_ai_service_health_check() {
        let config = Config::load("config.toml").unwrap();
        let ai_service = AIServiceFactory::create(&config.ai).expect("Should create AI service");

        let is_healthy = ai_service.health_check().await;
        println!("AI 服务健康状态: {}", is_healthy);
        // 注意：如果网络/配置问题，可能会返回 false
        // 这里我们不断言，只是检查不 panic
    }

    // 测试批量消息处理
    #[tokio::test]
    async fn test_batch_processing() {
        let app = create_test_app().await;
        let num_messages = 5;

        for i in 0..num_messages {
            let request = ReceiveMessageRequest {
                message_id: 1000 + i,
                text: format!("测试消息 {}", i),
                ..create_test_request()
            };

            let response = app
                .clone()
                .oneshot(
                    Request::builder()
                        .method("POST")
                        .uri("/api/v1/message")
                        .header("content-type", "application/json")
                        .body(Body::from(serde_json::to_string(&request).unwrap()))
                        .unwrap(),
                )
                .await
                .unwrap();

            assert_eq!(response.status(), StatusCode::OK);
        }

        // 等待批处理完成
        sleep(Duration::from_secs(2)).await;
        println!("批量消息处理测试完成");
    }

    // 测试无效 JSON 请求
    #[tokio::test]
    async fn test_invalid_json_request() {
        let app = create_test_app().await;

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/message")
                    .header("content-type", "application/json")
                    .body(Body::from("{"))  // 无效的 JSON
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    }

    // 测试缺少必填字段的请求
    #[tokio::test]
    async fn test_missing_field_request() {
        let app = create_test_app().await;

        let invalid_request = json!({
            "channel_id": -1001234567i64,
            "missing_fields": true
        });

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/message")
                    .header("content-type", "application/json")
                    .body(Body::from(serde_json::to_string(&invalid_request).unwrap()))
                    .unwrap(),
            )
            .await
            .unwrap();

        // Axum 返回 422 (Unprocessable Entity) 反序列化失败
        assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
    }

    // 测试消息通道和处理流程
    #[tokio::test]
    async fn test_message_processing_pipeline() {
        use tg_meme_token_monitor::telegram::bot::TelegramBot;

        // 加载配置
        let config = Config::load("config.toml").unwrap();

        // 创建 AI 服务
        let ai_service = AIServiceFactory::create(&config.ai).unwrap();

        // 创建 Telegram Bot
        let _bot = TelegramBot::new(config.telegram.clone());

        // 创建消息处理器
        let processor = Arc::new(MessageProcessor::new(config.clone(), ai_service.into()));
        processor.start().await.expect("Failed to start processor");

        // 创建测试消息
        let message = tg_meme_token_monitor::ai::models::Message {
            id: 99999,
            channel_id: -1001234567890,
            channel_name: "PipelineTest".to_string(),
            text: "测试完整的处理管道".to_string(),
            timestamp: chrono::Utc::now().timestamp(),
            sender: Some("TestUser".to_string()),
            media_type: None,
        };

        // 发送消息
        let result = processor.process_message(message).await;
        assert!(result.is_ok(), "应该成功发送消息到处理器");

        // 等待处理
        sleep(Duration::from_secs(3)).await;

        println!("端到端消息处理管道测试完成");
    }

    // 助手函数：创建测试用的应用实例
    async fn create_test_app() -> Router {
        use axum::routing::{get, post};
        use tg_meme_token_monitor::http::handler::{health_check, receive_message};

        // 加载测试配置
        let config = Config {
            telegram: TelegramConfig {
                target_user: 8030185949,
                bot_token: "TEST_BOT_TOKEN".to_string(),
            },
            http: HttpConfig {
                port: 8080,
            },
            processing: ProcessingConfig {
                batch_size: 10,
                batch_timeout_seconds: 5,
                min_confidence: 0.7,
                keywords: vec![
                    "token".to_string(),
                    "合约地址".to_string(),
                ],
            },
            ai: AIConfig {
                provider: "kimi".to_string(),
                timeout_seconds: 30,
                max_retries: 1,
                prompt_template: "".to_string(),
                kimi: Some(KimiConfig {
                    api_key: "TEST_API_KEY".to_string(),
                    model: "moonshot-v1-8k".to_string(),
                    base_url: "https://api.moonshot.cn/v1".to_string(),
                }),
                ollama: None,
                openai: None,
            },
        };

        // 创建 AI 服务
        let ai_service = AIServiceFactory::create(&config.ai).expect("Should create AI service");

        // 创建消息处理器
        let message_processor = Arc::new(MessageProcessor::new(
            config,
            ai_service.into(),
        ));

        // 添加测试频道到监控列表
        message_processor.add_channel(-1001234567890, Some("TestChannel".to_string())).await.expect("Failed to add test channel");

        message_processor.start().await.expect("Failed to start processor");

        // 创建路由
        Router::new()
            .route("/health", get(health_check))
            .route("/api/v1/message", post(receive_message))
            .with_state(message_processor)
    }

    // 配置测试客户端
    fn create_test_client() -> reqwest::Client {
        reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .build()
            .unwrap()
    }
}
