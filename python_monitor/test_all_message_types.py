#!/usr/bin/env python3
"""
测试所有消息类型捕获
专门测试频道、Bot、群组、私聊等不同类型消息的捕获
"""

import asyncio
from pyrogram import Client
from loguru import logger
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.config_loader import load_config

# 配置详细日志
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

# 加载配置
config = load_config('config.ini')
API_ID = config['telegram']['api_id']
API_HASH = config['telegram']['api_hash']
SESSION_FILE = config['telegram']['session_file']

# 测试用的消息类型统计
message_stats = {
    'channel': 0,
    'bot': 0,
    'private': 0,
    'group': 0,
    'unknown': 0,
    'total': 0
}

async def test_all_message_types():
    """测试所有消息类型捕获"""
    logger.info("=" * 60)
    logger.info("测试所有消息类型捕获")
    logger.info("=" * 60)
    logger.info("目标：验证频道、Bot、群组、私聊消息的捕获")

    logger.info("正在启动 Pyrogram 客户端...")

    # 创建客户端 - 不设置任何过滤器，捕获所有消息
    app = Client(
        SESSION_FILE,
        api_id=API_ID,
        api_hash=API_HASH
    )

    # 检查代理设置
    http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    if http_proxy:
        logger.info(f"检测到代理: {http_proxy}")
        if http_proxy.startswith('http://'):
            proxy_url = http_proxy[7:]
            if ':' in proxy_url:
                hostname, port = proxy_url.split(':')
                app.proxy = {
                    "scheme": "http",
                    "hostname": hostname,
                    "port": int(port)
                }
                logger.info(f"配置代理: {app.proxy}")

    # 添加详细的消息处理器
    @app.on_message()
    async def detailed_message_handler(client, message):
        """详细的消息处理器 - 捕获和分析所有消息"""
        message_stats['total'] += 1

        logger.info("=" * 60)
        logger.info("✅✅✅ 捕获到消息！✅✅✅")
        logger.info(f"📊 消息总数: {message_stats['total']}")

        # 基本信息
        logger.info(f"📍 聊天ID: {message.chat.id}")
        logger.info(f"📍 消息ID: {message.id}")
        logger.info(f"📍 聊天类型: {message.chat.type}")
        logger.info(f"📍 聊天标题: {getattr(message.chat, 'title', 'N/A')}")

        # 消息类型分析
        logger.info("🔬【原始类型分析】开始分析消息类型...")

        # 基于 chat.type 的详细分析
        # 注意：Pyrogram返回的是枚举值，需要转换为字符串进行比较
        chat_type = str(message.chat.type)

        if chat_type == "ChatType.CHANNEL":
            logger.info("  📢【频道消息】这是频道消息")
            message_stats['channel'] += 1
        elif chat_type == "ChatType.BOT":
            logger.info("  🤖【Bot消息】这是Bot消息")
            message_stats['bot'] += 1
        elif chat_type == "ChatType.PRIVATE":
            logger.info("  💬【私聊消息】这是私人聊天消息")
            message_stats['private'] += 1
        elif chat_type in ["ChatType.GROUP", "ChatType.SUPERGROUP"]:
            logger.info("  👥【群组消息】这是群组消息")
            message_stats['group'] += 1
        else:
            logger.info(f"  ❓【未知类型】未识别的聊天类型: {chat_type}")
            message_stats['unknown'] += 1

        # 发送者信息详细分析
        logger.info("👤【发送者分析】分析发送者信息...")
        if message.from_user:
            sender = message.from_user
            sender_name = sender.username or sender.first_name or 'Unknown'
            logger.info(f"  👤 发送者用户: {sender_name} (ID: {sender.id})")
            logger.info(f"  📱 用户类型: {sender.type if hasattr(sender, 'type') else 'Unknown'}")

        if message.sender_chat:
            sender = message.sender_chat
            sender_name = getattr(sender, 'title', 'Unknown')
            logger.info(f"  📢 发送者频道: {sender_name} (ID: {sender.id})")
            logger.info(f"  📋 发送者类型: {sender.type}")

        # 消息内容
        logger.info("📝【内容分析】分析消息内容...")
        if message.text:
            preview = message.text[:200].replace('\n', '\\n')
            logger.info(f"  📝 文本内容: {preview}{'...' if len(message.text) > 200 else ''}")

            # 关键词检查
            if message.text:
                if "PUMP" in message.text.upper():
                    logger.info("  🎯 关键词: 检测到 PUMP")
                if "ALERT" in message.text.upper():
                    logger.info("  🎯 关键词: 检测到 ALERT")
                if "-1002115686230" in message.text:
                    logger.info("  🎯 特殊ID: 检测到 Pump Alert 频道ID")
                if "Pump Alert" in message.text:
                    logger.info("  🎯 特殊名称: 检测到 Pump Alert 名称")

        # 统计信息
        logger.info("📊【统计信息】当前统计:")
        logger.info(f"  📊 频道消息: {message_stats['channel']}")
        logger.info(f"  📊 Bot消息: {message_stats['bot']}")
        logger.info(f"  📊 私聊消息: {message_stats['private']}")
        logger.info(f"  📊 群组消息: {message_stats['group']}")
        logger.info(f"  📊 未知类型: {message_stats['unknown']}")
        logger.info(f"  📊 总计: {message_stats['total']}")

        logger.info("=" * 60)

    # 开始监控
    await app.start()
    logger.info("✓ Pyrogram 客户端启动成功！")
    logger.info("")
    logger.info("正在等待消息...")
    logger.info("提示：")
    logger.info("1. 在监控的频道中发送消息")
    logger.info("2. 向Bot发送私聊消息")
    logger.info("3. 在群组中发送消息")
    logger.info("4. 等待Bot自动发送的消息")
    logger.info("")
    logger.info("=" * 60)

    try:
        # 运行30分钟进行测试
        logger.info("开始30分钟测试期...")
        for i in range(30):
            if i % 5 == 0:  # 每5分钟报告一次
                logger.info(f"⏰ 测试进行中... 已运行 {i} 分钟")
                logger.info(f"📊 当前统计 - 频道:{message_stats['channel']} Bot:{message_stats['bot']} 私聊:{message_stats['private']} 群组:{message_stats['group']} 总计:{message_stats['total']}")
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("\n用户中断，正在停止...")

    await app.stop()

    # 最终统计报告
    logger.info("=" * 60)
    logger.info("🎯 测试完成！最终统计报告")
    logger.info("=" * 60)
    logger.info(f"📊 频道消息: {message_stats['channel']}")
    logger.info(f"📊 Bot消息: {message_stats['bot']}")
    logger.info(f"📊 私聊消息: {message_stats['private']}")
    logger.info(f"📊 群组消息: {message_stats['group']}")
    logger.info(f"📊 未知类型: {message_stats['unknown']}")
    logger.info(f"📊 总计消息: {message_stats['total']}")

    # 结果分析
    logger.info("\n📈 结果分析:")
    if message_stats['bot'] == 0:
        logger.warning("⚠️  未捕获到Bot消息 - 需要检查Bot消息来源")
    if message_stats['private'] == 0:
        logger.warning("⚠️  未捕获到私聊消息 - 需要主动发送私聊消息测试")
    if message_stats['group'] == 0:
        logger.warning("⚠️  未捕获到群组消息 - 需要加入群组或创建测试群组")

    if message_stats['bot'] > 0 and message_stats['private'] > 0 and message_stats['group'] > 0:
        logger.success("🎉 成功！所有消息类型都已捕获到！")
    else:
        logger.info("💡 建议：根据警告信息，在相应的聊天类型中发送测试消息")

if __name__ == "__main__":
    print("【测试所有消息类型捕获】")
    print("目标：验证频道、Bot、群组、私聊消息的完整捕获")
    print("方法：")
    print("1. 在监控频道中发送消息")
    print("2. 向Bot发送私聊消息")
    print("3. 在群组中发送消息")
    print("4. 等待Bot自动发送的消息")
    print()
    print("按 Ctrl+C 停止测试")
    print("=" * 60)
    print()

    try:
        asyncio.run(test_all_message_types())
    except KeyboardInterrupt:
        print("\n✅ 测试已正常停止")
        sys.exit(0)

print("测试脚本已创建完成！")