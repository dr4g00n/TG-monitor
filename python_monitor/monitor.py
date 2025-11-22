#!/usr/bin/env python3
"""
Telegram 频道监控器

功能：
1. 使用 Pyrogram 监控指定频道
2. 当有新消息时，发送到 Rust 处理服务
3. 自动重试和错误处理
"""

import configparser
import sys
from pathlib import Path
from loguru import logger

# 添加项目路径到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.telegram_client import TelegramMonitor
from src.http_sender import HttpSender
from src.config_loader import load_config

# 配置日志 - 优化显示，隐藏Pyrogram网络调试，显示应用层重要信息
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"  # 改为INFO级别，减少调试信息
)
logger.add("monitor.log", rotation="500 MB", retention="10 days", level="DEBUG")

# ✅ 配置Pyrogram日志 - 详细调试模式，捕获所有消息事件
import logging
# 设置Pyrogram为DEBUG级别，捕获所有消息和事件
pyrogram_logger = logging.getLogger("pyrogram")
pyrogram_logger.setLevel(logging.DEBUG)

# 创建控制台处理器，显示重要Pyrogram信息
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | PYROGRAM | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
pyrogram_logger.addHandler(console_handler)

# ✅ 配置HTTP日志 - 显示发送相关日志
http_logger = logging.getLogger("urllib3")
http_logger.setLevel(logging.INFO)  # 显示HTTP发送相关信息

logger.info("✅ 日志配置完成 - 显示消息捕获和HTTP发送，隐藏网络心跳包")


def main():
    """主函数"""
    logger.info("========================================")
    logger.info("Telegram 频道监控器启动中...")
    logger.info("========================================")

    # 加载配置
    config_file = "config.ini"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    logger.info(f"加载配置文件: {config_file}")

    try:
        config = load_config(config_file)
        logger.info("配置加载成功")
        logger.info(f"  监控频道数量: {len(config['telegram']['channel_ids'])}")
        logger.info(f"  Rust 服务地址: {config['rust_service']['url']}")
        logger.info(f"  日志级别: {config['logging']['level']}")
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)

    # 创建 HTTP 发送器
    http_sender = HttpSender(config['rust_service'])

    # 测试连接
    logger.info("测试 Rust 服务连接...")
    if http_sender.health_check():
        logger.info("✓ Rust 服务连接正常")
    else:
        logger.warning("✗ Rust 服务连接失败，将继续运行但可能无法发送消息")

    # 创建 Telegram 监控器
    monitor = TelegramMonitor(
        api_id=int(config['telegram']['api_id']),
        api_hash=config['telegram']['api_hash'],
        session_file=config['telegram']['session_file'],
        channel_ids=config['telegram']['channel_ids'],
        http_sender=http_sender
    )

    # 启动监控
    logger.info("========================================")
    logger.info("开始监控频道消息...")
    logger.info("按 Ctrl+C 停止")
    logger.info("========================================")

    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("\n收到停止信号，正在退出...")
    except Exception as e:
        logger.error(f"运行错误: {e}")
        sys.exit(1)

    logger.info("监控器已停止")


if __name__ == "__main__":
    main()
