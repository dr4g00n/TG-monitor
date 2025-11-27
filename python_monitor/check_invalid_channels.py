#!/usr/bin/env python3
"""
检查无效频道/群组 ID
专门用于验证 config.ini 中的频道 ID 是否有效
"""

import asyncio
from pyrogram import Client
from loguru import logger
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.config_loader import load_config

# 配置日志
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

# 加载配置
config = load_config('config.ini')
API_ID = config['telegram']['api_id']
API_HASH = config['telegram']['api_hash']
SESSION_FILE = config['telegram']['session_file']
CHANNEL_IDS = config['telegram']['channel_ids']

# 检查结果
results = {
    'valid': [],
    'invalid': [],
    'errors': {}
}

async def check_channels():
    """验证所有频道 ID"""
    logger.info("=" * 70)
    logger.info("检查频道/群组 ID 有效性")
    logger.info("=" * 70)
    logger.info("共 {} 个频道/群组需要验证".format(len(CHANNEL_IDS)))
    logger.info("")

    # 检查代理设置
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
                logger.info(f"配置代理: {proxy}")
                logger.info("")

    # 创建客户端
    app = Client(
        SESSION_FILE,
        api_id=API_ID,
        api_hash=API_HASH,
        proxy=proxy
    )

    try:
        await app.start()
        logger.info("✓ Telegram 客户端启动成功")
        logger.info("")

        # 逐个验证频道
        for i, channel_id in enumerate(CHANNEL_IDS, 1):
            logger.info(f"[{i}/{len(CHANNEL_IDS)}] 检查 ID: {channel_id}")

            try:
                chat = await app.get_chat(channel_id)
                logger.success(f"  ✓ 有效 - 名称: {chat.title} - 类型: {chat.type}")
                results['valid'].append({
                    'id': channel_id,
                    'title': chat.title,
                    'type': chat.type
                })
            except Exception as e:
                logger.error(f"  ✗ 无效 - 错误: {e}")
                results['invalid'].append(channel_id)
                results['errors'][channel_id] = str(e)

            logger.info("")

        await app.stop()

    except Exception as e:
        logger.error(f"客户端启动失败: {e}")
        return

    # 打印总结
    logger.info("=" * 70)
    logger.info("验证完成！")
    logger.info("=" * 70)
    logger.info(f"有效频道/群组: {len(results['valid'])} 个")
    logger.info(f"无效频道/群组: {len(results['invalid'])} 个")
    logger.info("")

    if results['valid']:
        logger.info("✓ 有效的频道/群组:")
        for item in results['valid']:
            logger.info(f"  - {item['title']} ({item['id']}) - {item['type']}")
        logger.info("")

    if results['invalid']:
        logger.warning("✗ 无效的频道/群组:")
        for channel_id in results['invalid']:
            error = results['errors'][channel_id]
            logger.warning(f"  - {channel_id}: {error}")
        logger.info("")

    # 给出建议
    if results['invalid']:
        logger.info("💡 建议:")
        logger.info("1. 确认您已在 Telegram 中加入这些群组/频道")
        logger.info("2. 使用 @userinfobot 重新获取准确的 ID")
        logger.info("3. 从配置中移除无效的 ID")
        logger.info("")

if __name__ == "__main__":
    print("【检查频道/群组 ID 有效性】")
    print("这个脚本会验证 config.ini 中的所有频道/群组 ID")
    print("")
    print("提示:")
    print("- 对于无效的 ID，请检查是否已加入该群组/频道")
    print("- 使用 @userinfobot 获取准确的 ID")
    print("")
    print("按 Ctrl+C 停止测试")
    print("=" * 70)
    print("")

    try:
        asyncio.run(check_channels())
    except KeyboardInterrupt:
        print("\n✅ 检查已停止")
        sys.exit(0)
