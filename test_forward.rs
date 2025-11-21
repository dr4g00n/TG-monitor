use std::process::Command;

fn main() {
    println!("========================================");
    println!("Telegram Bot 转发功能测试");
    println!("========================================");

    // 使用 curl 直接测试 Telegram Bot API
    let bot_token = "8251881402:AAEzi7YFZJOr6FA5h9bF_dJUy0SkU_SbWU0";
    let target_user = "8030185949";

    println!("Bot Token: {}...", &bot_token[..20]);
    println!("目标用户: {}", target_user);

    // 测试消息
    let test_message = "🔥 **TG监控系统测试**\n\
                       📊 系统状态: 正常运行\n\
                       ✅ Bot Token: 验证通过\n\
                       🎯 目标用户: 8030185949\n\
                       ⏰ 测试时间: ".to_string() + &chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    println!("\n📤 发送测试消息...");
    println!("消息内容: {}", test_message);

    // 构建 Telegram API URL
    let api_url = format!(
        "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=Markdown",
        bot_token, target_user, urlencoding::encode(&test_message)
    );

    println!("API URL: {}...", &api_url[..100]);

    // 使用 curl 发送请求
    let output = Command::new("curl")
        .arg("-s")
        .arg("-X")
        .arg("POST")
        .arg(&api_url)
        .output()
        .expect("执行 curl 命令失败");

    if output.status.success() {
        let response = String::from_utf8_lossy(&output.stdout);
        println!("✅ 请求发送成功！");
        println!("响应: {}", response);

        // 检查响应是否包含 "ok": true
        if response.contains("\"ok\":true") || response.contains("\"ok\": true") {
            println!("🎉 消息成功发送到目标用户！");
        } else {
            println!("⚠️  消息可能发送失败，请检查响应内容");
        }
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        println!("❌ 请求发送失败: {}", error);
    }

    println!("\n========================================");
    println!("测试完成！请检查用户 8030185949 的 Telegram");
    println!("========================================");
}