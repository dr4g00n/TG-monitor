#!/usr/bin/env python3
"""
调试版本：简化 monitor.py 来找出消息捕获问题
"""

import asyncio
import configparser
import sys
from pathlib import Path
from loguru import logger
from pyrogram import Client
import os

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="DEBUG"
)

# 加载配置
config = configparser.ConfigParser()
config.read("config.ini")

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
session_file = config['telegram']['session_file']
channel_ids = [int(id.strip()) for id in config['telegram']['channel_ids'].split(',')]

logger.info(f"API ID: {api_id}")
logger.info(f"会话文件: {session_file}")
logger.info(f"监控频道: {channel_ids}")

async def debug_monitor():
    """调试监控器"""
    logger.info("=" * 60)
    logger.info("调试监控器启动")
    logger.info("=" * 60)

    # 检查代理
    proxy = None
    http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    if http_proxy:
        logger.info(f"检测到代理: {http_proxy}")
        if http_proxy.startswith('http://'):
            proxy_url = http_proxy[7:]
            if ':' in proxy_url:
                hostname, port = proxy_url.split(':')
                proxy = {
                    "scheme": "http",
                    "hostname": hostname,
                    "port": int(port)
                }

    # 创建客户端（与 test_monitor.py 完全相同的方式）
    app = Client(session_file, api_id=api_id, api_hash=api_hash, proxy=proxy)

    # 注册处理器（与 test_monitor.py 完全相同的方式）
    @app.on_message()
    async def message_handler(client, message):
        """处理所有收到的消息"""
        logger.info("✅✅✅ DEBUG Handler触发！收到消息！✅✅✅")
        logger.info(f"  聊天ID: {message.chat.id}")
        logger.info(f"  消息ID: {message.id}")
        logger.info(f"  聊天类型: {message.chat.type}")
        logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")

        # 检查是否在监控列表中
        if message.chat.id in channel_ids:
            logger.info(f"🎯 消息来自监控频道: {message.chat.id}")
        else:
            logger.info(f"📍 消息来自非监控频道: {message.chat.id}")

    # 启动客户端
    await app.start()
    logger.info("✓ 客户端启动成功")

    # 保持运行
    try:
        await asyncio.sleep(300)  # 运行5分钟
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        await app.stop()
        logger.info("调试完成")

if __name__ == "__main__":
    import sys
    print("【调试监控器】")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    print()

    asyncio.run(debug_monitor())