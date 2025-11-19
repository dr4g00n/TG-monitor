"""
Telegram 监控模块
使用 Pyrogram 监控频道消息
"""

from typing import Dict, List
from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from src.http_sender import HttpSender
import asyncio
import os


class TelegramMonitor:
    """Telegram 监控器"""

    def __init__(self, api_id: int, api_hash: str, session_file: str, channel_ids: List[int], http_sender: HttpSender):
        """
        初始化

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_file: 会话文件路径
            channel_ids: 要监控的频道 ID 列表
            http_sender: HTTP 发送器实例
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_file = session_file
        self.channel_ids = channel_ids
        self.http_sender = http_sender

        # 检查是否需要代理
        proxy = None
        http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')

        if http_proxy:
            logger.info(f"检测到代理设置: {http_proxy}")
            # Pyrogram 代理格式: {"hostname": str, "port": int, "scheme": str}
            # 从 http://127.0.0.1:7890 提取主机和端口
            if http_proxy.startswith('http://'):
                proxy_url = http_proxy[7:]  # 移除 http://
                if '@' in proxy_url:  # 如果有认证
                    auth_part, host_part = proxy_url.split('@')
                else:
                    host_part = proxy_url

                if ':' in host_part:
                    hostname, port = host_part.split(':')
                    proxy = {
                        "scheme": "http",
                        "hostname": hostname,
                        "port": int(port)
                    }
                    logger.info(f"配置 Pyrogram 代理: {proxy}")

        # 创建 Pyrogram 客户端
        self.client = Client(
            session_file,
            api_id=api_id,
            api_hash=api_hash,
            system_version="4.16.30-vxCUSTOM",
            proxy=proxy
        )

        logger.info(f"Telegram 监控器初始化完成")
        logger.info(f"  API ID: {api_id}")
        logger.info(f"  会话文件: {session_file}")
        logger.info(f"  监控频道: {len(channel_ids)} 个")

        # 注册消息处理器（使用同步方法）
        self.client.add_handler(
            MessageHandler(self.handle_message_sync, filters.channel & filters.incoming)
        )

    async def start_async(self):
        """异步启动监控（带详细状态反馈）"""
        logger.info("========================================")
        logger.info("正在连接 Telegram...")
        logger.info("========================================")

        try:
            # 开始连接
            logger.info("步骤 1/4: 初始化连接...")
            await self.client.start()
            logger.info("✓ 连接初始化成功")

            # 检查登录状态
            logger.info("步骤 2/4: 检查登录状态...")
            me = await self.client.get_me()
            logger.info(f"✓ 登录成功！用户名: @{me.username or 'N/A'} (ID: {me.id})")

            # 验证频道访问权限
            logger.info("步骤 3/4: 验证频道访问权限...")
            valid_channels = []
            invalid_channels = []

            for channel_id in self.channel_ids:
                try:
                    chat = await self.client.get_chat(channel_id)
                    valid_channels.append((channel_id, chat.title))
                    logger.info(f"  ✓ 频道可访问: {chat.title} ({channel_id})")
                except Exception as e:
                    invalid_channels.append((channel_id, str(e)))
                    logger.warning(f"  ✗ 频道无法访问: {channel_id} - {e}")

            logger.info(f"✓ 频道验证完成: {len(valid_channels)} 个可用, {len(invalid_channels)} 个失败")

            if not valid_channels:
                logger.error("✗ 没有可用的频道，请检查配置")
                return False

            self.channel_ids = [c[0] for c in valid_channels]  # 更新为有效的频道ID

            # 开始监听
            logger.info("步骤 4/4: 开始监听消息...")
            logger.info("========================================")
            logger.info("✓ Telegram 监控器启动成功！")
            logger.info(f"  正在监控 {len(valid_channels)} 个频道:")
            for channel_id, title in valid_channels:
                logger.info(f"    - {title} ({channel_id})")
            logger.info("========================================")
            logger.info("等待新消息... 按 Ctrl+C 停止")

            # 保持运行 - 使用更简单的等待方式
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("\n收到停止信号，正在关闭...")
            return True
        except Exception as e:
            logger.error(f"启动失败: {type(e).__name__}: {e}")
            logger.exception(e)
            return False

    def start(self):
        """启动监控（入口方法）"""
        try:
            # 使用 asyncio 运行异步方法
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            logger.info("\n用户中断，程序退出")
        except Exception as e:
            logger.error(f"运行错误: {type(e).__name__}: {e}")
            logger.exception(e)

    def stop(self):
        """停止监控（同步方法）"""
        self.client.stop()
        logger.info("Telegram 客户端已断开连接")

    async def stop_async(self):
        """异步停止监控"""
        if self.client.is_connected:
            await self.client.stop()
            logger.info("Telegram 客户端已断开连接")
        else:
            logger.info("Telegram 客户端未连接")

    def handle_message_sync(self, client: Client, message: Message):
        """
        同步处理接收到的消息（Pyrogram 要求 Handler 是同步的）

        Args:
            client: Pyrogram 客户端
            message: 接收到的消息
        """
        # 创建异步任务
        asyncio.create_task(self.handle_message_async(client, message))

    async def handle_message_async(self, client: Client, message: Message):
        """
        异步处理接收到的消息

        Args:
            client: Pyrogram 客户端
            message: 接收到的消息
        """
        try:
            # 只处理配置的频道
            if message.chat.id not in self.channel_ids:
                return

            logger.info(f"收到新消息: [{getattr(message.chat, 'title', 'Unknown')}] {message.id}")

            # 提取消息信息
            message_data = self.extract_message_data(message)

            # 发送到 Rust 服务（在后台线程中执行同步 HTTP 请求）
            await asyncio.to_thread(self.http_sender.send_message, message_data)

        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            logger.exception(e)

    def extract_message_data(self, message: Message) -> Dict:
        """
        提取消息数据

        Args:
            message: Pyrogram 消息对象

        Returns:
            dict: 提取的消息数据
        """
        data = {
            'channel_id': message.chat.id,
            'channel_name': message.chat.title or 'Unknown',
            'message_id': message.id,
            'text': '',
            'timestamp': int(message.date.timestamp()),
            'sender': None,
        }

        # 提取文本
        if message.text:
            data['text'] = message.text
        elif message.caption:
            data['text'] = message.caption
        else:
            # 媒体消息，没有文本
            media_type = self.get_media_type(message)
            data['text'] = f"[Media: {media_type}]"

        # 提取发送者信息
        if message.from_user:
            user = message.from_user
            username = user.username or user.first_name or 'Unknown'
            user_id = user.id
            data['sender'] = f"{username} ({user_id})"

        # 限制文本长度（避免发送过大的消息）
        if len(data['text']) > 4000:
            data['text'] = data['text'][:4000] + '... [截断]'

        logger.debug(f"消息数据提取完成: {data['channel_name']} - {data['message_id']}")

        return data

    def get_media_type(self, message: Message) -> str:
        """
        获取媒体类型

        Args:
            message: 消息对象

        Returns:
            str: 媒体类型描述
        """
        if message.photo:
            return "Photo"
        elif message.video:
            return "Video"
        elif message.audio:
            return "Audio"
        elif message.document:
            return f"Document: {message.document.file_name or 'Unknown'}"
        elif message.sticker:
            return "Sticker"
        elif message.animation:
            return "Animation"
        elif message.voice:
            return "Voice"
        elif message.video_note:
            return "Video Note"
        elif message.poll:
            return "Poll"
        else:
            return "Unknown Media"


# 兼容 Pyrogram 2.0+ 的 Handler 接口
from pyrogram.handlers import MessageHandler
