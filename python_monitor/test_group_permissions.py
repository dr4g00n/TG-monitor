#!/usr/bin/env python3
"""
测试群组权限和消息捕获
专门测试群组消息捕获的权限问题
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

async def test_group_permissions():
    """测试群组权限和消息捕获"""
    logger.info("=" * 60)
    logger.info("测试群组权限和消息捕获")
    logger.info("=" * 60)
    logger.info("目标：验证群组消息捕获的权限限制")

    logger.info("正在启动 Pyrogram 客户端...")

    # 创建客户端
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

    # 添加权限检查和消息捕获
    @app.on_message()
    async def analyze_group_messages(client, message):
        """分析群组消息捕获情况"""
        logger.info("=" * 60)
        logger.info("✅ 捕获到消息！开始权限分析")

        # 基本信息
        logger.info(f"📍 聊天ID: {message.chat.id}")
        logger.info(f"📍 消息ID: {message.id}")
        logger.info(f"📍 聊天类型: {message.chat.type}")
        logger.info(f"📍 聊天标题: {getattr(message.chat, 'title', 'N/A')}")

        # 发送者信息
        if message.from_user:
            logger.info(f"👤 发送者用户: {message.from_user.username or message.from_user.first_name or 'Unknown'} ({message.from_user.id})")
        if message.sender_chat:
            logger.info(f"📢 发送者频道: {getattr(message.sender_chat, 'title', 'Unknown')} ({message.sender_chat.id})")

        # 消息内容
        if message.text:
            logger.info(f"📝 消息内容: {message.text[:100]}")

        # 权限分析
        try:
            # 获取当前用户在群组中的权限
            me = await client.get_me()
            chat_member = await client.get_chat_member(message.chat.id, me.id)

            logger.info("🔍【权限分析】当前用户在群组中的权限:")
            logger.info(f"  📊 权限状态: {chat_member.status}")
            logger.info(f"  📊 权限级别: {chat_member.privileges if hasattr(chat_member, 'privileges') else '无特殊权限'}")

            # 分析是否能获取其他成员消息
            if chat_member.status in ["administrator", "creator"]:
                logger.info("  ✅ 有管理员权限，应该能看到所有消息")
            elif chat_member.status == "member":
                logger.info("  ⚠️ 普通成员权限，可能只能看到自己发送的消息")
            else:
                logger.info(f"  ❓ 特殊状态: {chat_member.status}")

        except Exception as e:
            logger.error(f"  ❌ 权限检查失败: {e}")

        # 群组类型分析
        if message.chat.type in ["group", "supergroup"]:
            logger.info("📋【群组分析】群组详细信息:")
            try:
                chat = await client.get_chat(message.chat.id)
                logger.info(f"  🏷️ 群组标题: {chat.title}")
                logger.info(f"  🏷️ 群组类型: {chat.type}")
                logger.info(f"  🏷️ 成员数量: {chat.members_count if hasattr(chat, 'members_count') else '未知'}")
                logger.info(f"  🔒 是否私有: {'是' if chat.type == 'private' else '否'}")
            except Exception as e:
                logger.error(f"  ❌ 群组信息获取失败: {e}")

        # 结果分析
        if message.chat.type in ["group", "supergroup"]:
            if message.from_user and message.from_user.id == me.id:
                logger.info("  ✅ 这是我自己发送的消息")
            else:
                logger.info("  🔍 这是其他成员发送的消息")
                logger.info("  💡 如果看不到此类消息，说明权限不足")

        logger.info("=" * 60)

    # 开始监控
    await app.start()
    logger.info("✓ Pyrogram 客户端启动成功！")
    logger.info("")
    logger.info("正在等待消息...")
    logger.info("提示：")
    logger.info("1. 在群组中发送消息进行测试")
    logger.info("2. 观察是否能捕获其他成员的消息")
    logger.info("3. 检查权限状态和限制")
    logger.info("")
    logger.info("=" * 60)

    try:
        # 运行20分钟进行测试
        for i in range(20):
            if i % 5 == 0:
                logger.info(f"⏰ 测试进行中... 已运行 {i} 分钟")
                logger.info("💡 提示：请在群组中发送消息进行测试")
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("\n用户中断，正在停止...")

    await app.stop()
    logger.info("测试完成")

if __name__ == "__main__":
    print("【测试群组权限和消息捕获】")
    print("目标：验证群组消息捕获的权限限制")
    print("方法：")
    print("1. 在群组中发送消息")
    print("2. 观察是否能捕获其他成员的消息")
    print("3. 检查当前用户的权限状态")
    print()
    print("按 Ctrl+C 停止测试")
    print("=" * 60)
    print()

    try:
        asyncio.run(test_group_permissions())
    except KeyboardInterrupt:
        print("\n✅ 测试已正常停止")
        sys.exit(0)

print("群组权限测试脚本已创建完成！")