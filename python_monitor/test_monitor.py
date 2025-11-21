#!/usr/bin/env python3
"""
测试日志：验证消息接收

这个脚本用于测试 Telegram 消息接收功能，确认 Pyrogram 是否能捕获频道消息。
"""

import asyncio
from pyrogram import Client, filters
from loguru import logger
from pathlib import Path

# 配置 - 从config.ini加载
CONFIG_FILE = "config.ini"

# 加载API配置
def load_api_config():
    """从配置文件加载API配置"""
    if not Path(CONFIG_FILE).exists():
        logger.error(f"配置文件 {CONFIG_FILE} 不存在")
        return None, None

    import configparser
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    api_id = int(config['telegram']['api_id'])
    api_hash = config['telegram']['api_hash']

    return api_id, api_hash

# 加载配置
API_ID, API_HASH = load_api_config()
if not API_ID or not API_HASH:
    logger.error("无法加载API配置")
    sys.exit(1)

SESSION_FILE = "my_monitor.session"

# 添加当前目录到路径
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 日志配置
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

# 测试时可以修改为只监控特定频道，或者设为 None 监听所有消息
# 从 config.ini 读取频道ID
CONFIG_FILE = "config.ini"

def load_channel_ids():
    """从配置文件加载频道ID"""
    if not Path(CONFIG_FILE).exists():
        logger.warning(f"配置文件 {CONFIG_FILE} 不存在，将监听所有聊天")
        return None

    import configparser
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if 'telegram' in config and 'channel_ids' in config['telegram']:
        channel_ids_str = config['telegram']['channel_ids']
        channel_ids = [int(id.strip()) for id in channel_ids_str.split(',')]
        logger.info(f"从配置文件加载频道ID: {channel_ids}")
        return channel_ids
    else:
        logger.warning("配置文件中未找到 channel_ids，将监听所有聊天")
        return None


async def test_monitor():
    """测试消息接收"""
    logger.info("=" * 60)
    logger.info("Telegram 消息接收测试")
    logger.info("=" * 60)

    # 加载频道ID
    channel_ids = load_channel_ids()

    logger.info("正在启动 Pyrogram 客户端...")

    try:
        # 创建客户端
        app = Client(SESSION_FILE, api_id=API_ID, api_hash=API_HASH)

        # 检查是否需要代理
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

        # 添加handler - 监听所有消息（不搞任何过滤）
        @app.on_message()
        async def test_handler(client, message):
            """测试消息处理器 - 监听所有消息"""
            logger.info("✅✅✅ Handler触发！收到消息！✅✅✅")
            logger.info(f"  聊天类型: {message.chat.type}")
            logger.info(f"  聊天ID: {message.chat.id}")
            logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")
            logger.info(f"  消息ID: {message.id}")
            logger.info(f"  时间: {message.date}")

            # 发送者信息
            if message.from_user:
                sender = message.from_user
                sender_name = sender.username or sender.first_name or 'Unknown'
                logger.info(f"  发送者: {sender_name} ({sender.id})")
            elif message.sender_chat:
                sender = message.sender_chat
                sender_name = getattr(sender, 'title', 'Unknown')
                logger.info(f"  发送者: {sender_name} (频道)")

            # 消息内容
            if message.text:
                logger.info(f"  文本内容: {message.text[:200]}")
            elif message.caption:
                logger.info(f"  媒体描述: {message.caption[:200]}")
            else:
                media_type = "Unknown"
                if message.photo:
                    media_type = "Photo"
                elif message.video:
                    media_type = "Video"
                elif message.document:
                    media_type = f"Document: {message.document.file_name}"
                elif message.audio:
                    media_type = "Audio"
                logger.info(f"  媒体类型: {media_type}")

            logger.info("=" * 60)

        # 开始监控
        await app.start()
        logger.info("✓ Pyrogram 客户端启动成功！")
        logger.info("" )
        logger.info("正在等待消息...")
        logger.info("提示：在监控的频道发送测试消息，或等待新消息")
        logger.info("" )

        # 显示监控的频道
        if channel_ids:
            logger.info(f"监控的频道ID: {channel_ids}")
        else:
            logger.info("监控所有聊天（未配置特定频道）")

        logger.info("=" * 60)

        # 保持运行
        try:
            await asyncio.sleep(3600)  # 测试1小时
        except KeyboardInterrupt:
            logger.info("\n用户中断，正在停止...")

        await app.stop()
        logger.info("测试完成")

    except Exception as e:
        logger.error(f"启动失败: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    print("【重要提示】")
    print("1. 确保配置文件 config.ini 存在且包含正确的 channel_ids")
    print("2. 确保网络连接正常")
    print("3. 在监控的频道中手动发送测试消息")
    print("4. 观察日志是否显示 'Handler触发！'")
    print()
    print("按 Ctrl+C 停止测试")
    print("=" * 60)
    print()

    asyncio.run(test_monitor())
