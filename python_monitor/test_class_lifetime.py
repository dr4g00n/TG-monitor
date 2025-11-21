#!/usr/bin/env python3
"""
测试变量生命周期问题 - 确保客户端引用不会被垃圾回收
"""

import asyncio
import configparser
import sys
import gc
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

# 全局变量防止垃圾回收
_global_client = None

def create_monitor():
    """创建监控器，确保客户端引用安全"""
    global _global_client

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

    # 关键：存储到全局变量防止垃圾回收
    _global_client = Client(session_file, api_id=api_id, api_hash=api_hash, proxy=proxy)

    # 注册处理器
    @_global_client.on_message()
    async def message_handler(client, message):
        """处理所有收到的消息"""
        logger.info("✅✅✅ LIFETIME Handler触发！收到消息！✅✅✅")
        logger.info(f"  聊天ID: {message.chat.id}")
        logger.info(f"  消息ID: {message.id}")
        logger.info(f"  聊天类型: {message.chat.type}")
        logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")

        if message.chat.id in channel_ids:
            logger.info(f"🎯 消息来自监控频道: {message.chat.id}")
        else:
            logger.info(f"📍 消息来自非监控频道: {message.chat.id}")

    return _global_client, channel_ids

async def test_lifetime_monitor():
    """测试生命周期监控"""
    logger.info("=" * 60)
    logger.info("生命周期测试监控器启动")
    logger.info("=" * 60)

    # 创建监控器
    client, channel_ids = create_monitor()

    # 强制垃圾回收，测试是否会影响客户端
    gc.collect()
    logger.info("强制垃圾回收完成")

    # 启动客户端
    await client.start()
    logger.info("✓ 客户端启动成功")

    # 保持运行
    try:
        await asyncio.sleep(300)  # 运行5分钟
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        await client.stop()
        logger.info("生命周期测试完成")

if __name__ == "__main__":
    print("【生命周期测试监控器】")
    print("测试变量生命周期和垃圾回收问题")
    print("=" * 60)
    print()

    asyncio.run(test_lifetime_monitor())