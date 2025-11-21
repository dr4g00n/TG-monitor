use tg_meme_token_monitor::{
    ai::AIServiceFactory,
    config::Config,
    http::HttpServer,
    processor::MessageProcessor,
    telegram::bot::TelegramBot,
};
use anyhow::Result;
use std::sync::Arc;
use tracing::{info, warn};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // 初始化日志
    init_logging();

    info!("========================================");
    info!("Telegram Meme Token 处理服务启动中...");
    info!("========================================");

    // 加载配置
    let config_file = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "config.toml".to_string());

    info!("加载配置文件: {}", config_file);
    let config = Config::load(&config_file)?;

    info!("配置加载成功");
    info!("  AI 服务: {}", config.ai.provider);
    info!("  HTTP 端口: {}", config.http.port);
    info!("  目标用户: {}", config.telegram.target_user);
    info!(
        "  批量处理: {} 条/{} 秒",
        config.processing.batch_size, config.processing.batch_timeout_seconds
    );

    // 创建 AI 服务
    info!("初始化 AI 服务...");
    let ai_service = AIServiceFactory::create(&config.ai)?;
    info!("✓ AI 服务创建成功: {}", ai_service.name());

    // 健康检查
    info!("进行 AI 服务健康检查...");
    let is_healthy = ai_service.health_check().await;
    if is_healthy {
        info!("✓ AI 服务健康检查通过");
    } else {
        warn!("⚠️  AI 服务健康检查失败，将尝试继续运行");
        warn!("    请检查配置和网络连接");
    }

    // 创建 Telegram Bot（用于转发消息）
    info!("初始化 Telegram Bot...");
    let telegram_bot = Arc::new(TelegramBot::new(config.telegram.clone()));

    // 验证 Telegram Bot
    info!("进行 Telegram Bot 健康检查...");
    match telegram_bot.health_check().await {
        Ok(true) => info!("✓ Telegram Bot 健康检查通过"),
        Ok(false) => {
            warn!("⚠️  Telegram Bot 健康检查失败，请检查 bot_token");
            warn!("    消息转发功能可能无法正常工作");
        },
        Err(e) => {
            warn!("⚠️  Telegram Bot 连接失败: {}", e);
            warn!("    消息转发功能可能无法正常工作");
        }
    }

    // 创建消息处理器
    let message_processor = Arc::new(MessageProcessor::new(
        config.clone(),
        ai_service.into(),
        telegram_bot,
    ));

    // 启动消息处理器的后台任务
    info!("启动消息处理器...");
    message_processor.start().await?;
    info!("✓ 消息处理器已启动");

    // 创建并启动 HTTP 服务器
    info!("启动 HTTP 服务器...");
    let http_server = HttpServer::new(message_processor, config.http.port);

    info!("✓ HTTP 服务器创建成功");
    info!("等待接收来自 Python 监控器的消息...");
    info!("========================================\n");

    // 启动 HTTP 服务器（这会阻塞直到出错或用户中断）
    http_server.start().await?;

    Ok(())
}

/// 初始化日志系统
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,tg_meme_token_monitor=debug".into()),
        )
        .with(
            tracing_subscriber::fmt::layer()
                .with_target(true)
                .with_thread_ids(false)
                .with_file(false)
                .with_line_number(false),
        )
        .init();
}
