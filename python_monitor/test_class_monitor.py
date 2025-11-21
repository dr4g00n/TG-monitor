#!/usr/bin/env python3
"""
测试类版本 - 完全复制 debug_monitor.py 的逻辑但用类封装
验证是否是面向对象 vs 函数式编程的问题
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

class TestMonitor:
    """测试版本的监控器 - 完全复制 debug_monitor.py 的逻辑"""

    def __init__(self):
        # 加载配置
        config = configparser.ConfigParser()
        config.read("config.ini")

        self.api_id = int(config['telegram']['api_id'])
        self.api_hash = config['telegram']['api_hash']
        self.session_file = config['telegram']['session_file']
        self.channel_ids = [int(id.strip()) for id in config['telegram']['channel_ids'].split(',')]

        logger.info(f"API ID: {self.api_id}")
        logger.info(f"会话文件: {self.session_file}")
        logger.info(f"监控频道: {self.channel_ids}")

        # 创建客户端（与 debug_monitor.py 完全相同的方式）
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

        # 关键：完全相同的客户端创建方式
        self.client = Client(self.session_file, api_id=self.api_id, api_hash=self.api_hash, proxy=proxy)

        # 关键：完全相同的处理器注册方式
        @self.client.on_message()
        async def message_handler(client, message):
            """处理所有收到的消息 - 完全复制 debug_monitor.py"""
            logger.info("✅✅✅ CLASS Handler触发！收到消息！✅✅✅")
            logger.info(f"  聊天ID: {message.chat.id}")
            logger.info(f"  消息ID: {message.id}")
            logger.info(f"  聊天类型: {message.chat.type}")
            logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")

            # 检查是否在监控列表中
            if message.chat.id in self.channel_ids:
                logger.info(f"🎯 消息来自监控频道: {message.chat.id}")
            else:
                logger.info(f"📍 消息来自非监控频道: {message.chat.id}")

    async def start(self):
        """启动监控 - 完全复制 debug_monitor.py 的流程"""
        logger.info("=" * 60)
        logger.info("类测试监控器启动")
        logger.info("=" * 60)

        # 启动客户端（完全相同的调用）
        await self.client.start()
        logger.info("✓ 客户端启动成功")

        # 保持运行（完全相同的逻辑）
        try:
            await asyncio.sleep(300)  # 运行5分钟
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            await self.client.stop()
            logger.info("类测试完成")

if __name__ == "__main__":
    print("【类测试监控器 - 复制 debug_monitor.py 逻辑】")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    print()

    monitor = TestMonitor()
    asyncio.run(monitor.start())