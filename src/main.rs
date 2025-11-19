mod ai;
mod config;
mod processor;
mod telegram;

use ai::AIServiceFactory;
use anyhow::Result;
use config::Config;
use std::sync::Arc;
use tracing::{error, info, warn};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // 初始化日志
    init_logging();

    info!("========================================");
    info!("Telegram Meme Token Monitor 启动中...");
    info!("========================================");

    // 加载配置
    let config_file = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "config.toml".to_string());

    info!("加载配置文件: {}", config_file);
    let config = Config::load(&config_file)?;

    info!("配置加载成功");
    info!("  AI 服务: {}", config.ai.provider);
    info!("  监控频道数量: {}", config.telegram.source_channels.len());
    info!("  目标用户: {}", config.telegram.target_user);
    info!("  批量处理: {} 条/{} 秒",
        config.processing.batch_size,
        config.processing.batch_timeout_seconds
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

    // 创建消息处理器（转换为 Arc）
    let message_processor = processor::MessageProcessor::new(config.clone(), ai_service.into());

    // 启动 Telegram 客户端
    info!("启动 Telegram 客户端...");
    let mut client = telegram::Client::new(config.telegram, message_processor);

    match client.start().await {
        Ok(_) => {
            info!("✓ Telegram 客户端启动成功");
            info!("  开始监控频道消息...");
        }
        Err(e) => {
            error!("✗ Telegram 客户端启动失败: {}", e);
            return Err(e);
        }
    }

    // 保持程序运行
    tokio::signal::ctrl_c().await?;
    info!("收到中断信号，正在关闭...");

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
