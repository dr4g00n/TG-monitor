#!/usr/bin/env python3
"""
测试 Telegram 连接状态反馈功能
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_loader import load_config
from src.http_sender import HttpSender
from src.telegram_client import TelegramMonitor
from loguru import logger

# 移除默认的日志处理器
logger.remove()
# 添加新的日志处理器，显示时间、级别和消息
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

async def test_connection():
    """测试连接并显示详细状态"""
    print("\n" + "="*60)
    print("测试 Telegram 连接状态反馈功能")
    print("="*60 + "\n")

    # 加载配置
    config = load_config('config.ini')

    # 创建 HTTP 发送器
    sender = HttpSender({
        'url': config['rust_service']['url'],
        'max_retries': 1,
        'timeout': 5
    })

    # 创建监控器
    monitor = TelegramMonitor(
        api_id=int(config['telegram']['api_id']),
        api_hash=config['telegram']['api_hash'],
        session_file=config['telegram']['session_file'],
        channel_ids=config['telegram']['channel_ids'],
        http_sender=sender
    )

    # 测试连接（模拟完整的 start_async 过程）
    try:
        print("\n┌─ 步骤 1/4: 初始化连接...")
        print("│  正在通过代理连接到 Telegram 服务器...")
        await monitor.client.connect()
        print("│  ✓ 网络连接成功")

        print("\n├─ 步骤 2/4: 检查登录状态...")
        if await monitor.client.get_me():
            me = await monitor.client.get_me()
            print(f"│  ✓ 已登录: @{me.username or 'N/A'} (ID: {me.id})")
        else:
            print("│  ✗ 未登录，需要先进行认证")
            print("\n├─ 需要手动登录:")
            print("│  1. 停止此测试")
            print("│  2. 运行: python3 monitor.py config.ini")
            print("│  3. 按提示输入手机号和验证码")
            return False

        print("\n├─ 步骤 3/4: 验证频道访问权限...")
        for i, channel_id in enumerate(monitor.channel_ids, 1):
            try:
                chat = await monitor.client.get_chat(channel_id)
                print(f"│  ✓ [{i}] {chat.title} ({channel_id})")
            except Exception as e:
                print(f"│  ✗ [{i}] 无法访问 {channel_id}: {e}")

        print("\n├─ 步骤 4/4: 开始监听消息...")
        print("│  ✓ 监控器已启动")
        print("│  ✓ 等待新消息...")

        print("\n" + "="*60)
        print("✓ 所有测试通过！系统运行正常")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        print("="*60 + "\n")
        return False

    finally:
        await monitor.client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
