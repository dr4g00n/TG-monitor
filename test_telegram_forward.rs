use tg_meme_token_monitor::telegram::bot::TelegramBot;
use tg_meme_token_monitor::config::Config;
use std::sync::Arc;
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    println!("========================================");
    println!("Telegram Bot 转发功能测试程序");
    println!("========================================");

    // 加载配置
    println!("加载配置文件...");
    let config = Config::load("config.toml")?;

    println!("目标用户 ID: {}", config.telegram.target_user);
    println!("Bot Token: {}...", &config.telegram.bot_token[..20]);

    // 创建 Telegram Bot
    println!("\n初始化 Telegram Bot...");
    let telegram_bot = Arc::new(TelegramBot::new(config.telegram.clone()));

    // 验证 Bot Token
    println!("进行 Telegram Bot 健康检查...");
    match telegram_bot.health_check().await {
        Ok(true) => println!("✅ Telegram Bot Token 验证通过"),
        Ok(false) => {
            println!("❌ Telegram Bot Token 验证失败");
            return Ok(());
        },
        Err(e) => {
            println!("❌ Telegram Bot 连接失败: {}", e);
            return Ok(());
        }
    }

    // 测试消息内容
    let test_messages = vec![
        "🔥 **测试消息 #1**\n\
         📊 Token: TEST\n\
         💰 价格: $0.001\n\
         🎯 建议: 买入\n\
         ⏰ 时间: ".to_string() + &chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),

        "📈 **测试消息 #2 - 详细报告**\n\
         Token名称: HAPPY\n\
         合约地址: `0x742d35cc663897c5f2f2c7e3b5f8c9d4e2f1a0b9`\n\
         当前价格: 0.0001 USD\n\
         目标价格: 0.001 USD\n\
         推荐理由: 新token即将发射，流动性已锁定，社区活跃\n\
         置信度: 85%\n\
         紧急度: 7/10\n\
         发送时间: ".to_string() + &chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string(),

        "⚠️ **系统测试**\n\
         这是来自TG监控系统的测试消息\n\
         如果收到此消息，说明转发功能正常工作！\n\
         🎉 ".to_string() + &chrono::Local::now().format("%H:%M:%S").to_string(),
    ];

    // 发送测试消息
    println!("\n========================================");
    println!("开始发送测试消息到用户 {}...", config.telegram.target_user);
    println!("========================================");

    for (i, message) in test_messages.iter().enumerate() {
        println!("\n📤 发送测试消息 #{}...", i + 1);
        println!("内容长度: {} 字符", message.len());

        match telegram_bot.send_message(message).await {
            Ok(_) => {
                println!("✅ 测试消息 #{} 发送成功！", i + 1);
            },
            Err(e) => {
                println!("❌ 测试消息 #{} 发送失败: {}", i + 1, e);
            }
        }

        // 等待2秒再发送下一条
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
    }

    println!("\n========================================");
    println!("测试完成！请检查用户 {} 是否收到消息", config.telegram.target_user);
    println!("========================================");

    Ok(())
}