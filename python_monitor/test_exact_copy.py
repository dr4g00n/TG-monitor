#!/usr/bin/env python3
"""
精确复制测试 - 逐行复制 debug_monitor.py 的逻辑到类结构中
验证是否是运行时机或环境差异
"""

import asyncio
import configparser
import sys
from pathlib import Path
from loguru import logger
from pyrogram import Client
import os

# 配置日志（完全相同的配置）
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="DEBUG"
)

class ExactCopyMonitor:
    """完全复制 debug_monitor.py 的逻辑，但用类封装"""

    def __init__(self):
        """构造函数 - 完全复制 debug_monitor.py 的初始化逻辑"""
        # 加载配置（完全相同的代码）
        config = configparser.ConfigParser()
        config.read("config.ini")

        api_id = int(config['telegram']['api_id'])
        api_hash = config['telegram']['api_hash']
        session_file = config['telegram']['session_file']
        channel_ids = [int(id.strip()) for id in config['telegram']['channel_ids'].split(',')]

        logger.info(f"API ID: {api_id}")
        logger.info(f"会话文件: {session_file}")
        logger.info(f"监控频道: {channel_ids}")

        # 保存到实例属性
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_file = session_file
        self.channel_ids = channel_ids

        # 检查代理（完全相同的逻辑）
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
            logger.info("✅✅✅ EXACT COPY Handler触发！收到消息！✅✅✅")
            logger.info(f"  聊天ID: {message.chat.id}")
            logger.info(f"  消息ID: {message.id}")
            logger.info(f"  聊天类型: {message.chat.type}")
            logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")

            # 检查是否在监控列表中
            if message.chat.id in self.channel_ids:
                logger.info(f"🎯 消息来自监控频道: {message.chat.id}")
            else:
                logger.info(f"📍 消息来自非监控频道: {message.chat.id}")

    async def start_async(self):
        """完全复制 debug_monitor.py 的主函数逻辑"""
        logger.info("=" * 60)
        logger.info("精确复制监控器启动")
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
            logger.info("精确复制测试完成")

    def start(self):
        """入口函数 - 完全复制 monitor.py 的启动方式"""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            logger.info("\n用户中断，程序退出")
        except Exception as e:
            logger.error(f"运行错误: {type(e).__name__}: {e}")
            logger.exception(e)

if __name__ == "__main__":
    print("【精确复制监控器 - 完全复制 debug_monitor.py 逻辑】")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    print()

    monitor = ExactCopyMonitor()
    monitor.start()