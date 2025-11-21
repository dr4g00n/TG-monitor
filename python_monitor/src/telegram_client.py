"""
Telegram 监控模块 - 使用 debug_monitor.py 验证成功的架构
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

# 全局变量防止客户端被垃圾回收
_global_pyrogram_client = None
_global_http_sender = None

class TelegramMonitor:
    """Telegram 监控器 - 使用验证成功的架构"""

    def __init__(self, api_id: int, api_hash: str, session_file: str, channel_ids: List[int], http_sender: HttpSender):
        """
        初始化 - 使用与 debug_monitor.py 相同的简单架构

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

        # 保存到全局变量防止垃圾回收
        global _global_http_sender
        _global_http_sender = http_sender

        # ✅ 初始化统计（简化版）
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'last_message_time': None,
            'channels_active': set()
        }

        logger.info(f"Telegram 监控器初始化完成")
        logger.info(f"  API ID: {api_id}")
        logger.info(f"  会话文件: {session_file}")
        logger.info(f"  监控频道: {len(channel_ids)} 个")

    async def start_async(self):
        """异步启动监控 - 使用 debug_monitor.py 的成功模式"""
        logger.info("========================================")
        logger.info("Telegram 监控器启动中...")
        logger.info("========================================")

        try:
            # 步骤 1: 连接 Telegram（简化流程）
            logger.info("步骤 1/3: 连接 Telegram...")

            # 检查代理设置
            proxy = None
            http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
            if http_proxy:
                logger.info(f"检测到代理设置: {http_proxy}")
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

            # 关键：使用全局变量存储客户端引用
            global _global_pyrogram_client

            # 创建 Pyrogram 客户端（与 debug_monitor.py 相同的方式）
            _global_pyrogram_client = Client(
                self.session_file,
                api_id=self.api_id,
                api_hash=self.api_hash,
                proxy=proxy
            )

            # 同时保存到实例属性
            self.client = _global_pyrogram_client

            # 步骤 2: 注册消息处理器
            logger.info("步骤 2/3: 注册消息处理器...")

            @self.client.on_message()
            async def message_handler(client, message):
                """处理所有收到的消息 - 使用 debug_monitor.py 的成功模式"""
                logger.info("🎯 Handler触发 - 收到消息事件！")
                logger.info(f"  聊天ID: {message.chat.id}")
                logger.info(f"  消息ID: {message.id}")
                logger.info(f"  聊天类型: {message.chat.type}")
                logger.info(f"  聊天标题: {getattr(message.chat, 'title', 'N/A')}")

                # 检查频道是否在监控列表中
                if message.chat.id not in self.channel_ids:
                    logger.debug(f"跳过未监控的频道: {message.chat.id}")
                    return

                # ✅ 更新统计
                self.stats['messages_received'] += 1
                self.stats['last_message_time'] = message.date
                self.stats['channels_active'].add(message.chat.id)

                try:
                    # 提取消息信息
                    channel_name = getattr(message.chat, 'title', 'Unknown')
                    logger.info(f"📨 收到新消息:")
                    logger.info(f"  频道: {channel_name} ({message.chat.id})")
                    logger.info(f"  消息ID: {message.id}")
                    logger.info(f"  时间: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 显示发送者信息
                    if message.from_user:
                        sender = message.from_user
                        sender_name = sender.username or sender.first_name or 'Unknown'
                        logger.info(f"  发送者: {sender_name} ({sender.id})")
                    elif message.sender_chat:
                        sender_chat = message.sender_chat
                        sender_name = getattr(sender_chat, 'title', 'Unknown')
                        logger.info(f"  发送者: {sender_name} (频道)")

                    # 显示消息内容预览
                    if message.text:
                        preview = message.text[:100].replace('\n', '\\n')
                        logger.info(f"  内容: {preview}{'...' if len(message.text) > 100 else ''}")
                    elif message.caption:
                        preview = message.caption[:100].replace('\n', '\\n')
                        logger.info(f"  媒体描述: {preview}{'...' if len(message.caption) > 100 else ''}")
                    else:
                        media_type = self.get_media_type(message)
                        logger.info(f"  媒体类型: {media_type}")

                    # 提取消息数据
                    message_data = self.extract_message_data(message)

                    # 发送到 Rust 服务
                    logger.info(f"⬆️  转发到 Rust 服务...")
                    success = await asyncio.to_thread(self.http_sender.send_message, message_data)

                    # 更新统计
                    if success:
                        self.stats['messages_sent'] += 1
                        logger.info(f"✓ 消息处理完成: {message_data['message_id']}")
                    else:
                        self.stats['messages_failed'] += 1
                        logger.warning(f"⚠️  消息发送失败: {message_data['message_id']}")

                    # 显示统计
                    logger.info(f"📊 实时统计:")
                    logger.info(f"  累计接收: {self.stats['messages_received']}")
                    logger.info(f"  成功发送: {self.stats['messages_sent']}")
                    logger.info(f"  发送失败: {self.stats['messages_failed']}")
                    logger.info(f"  活跃频道: {len(self.stats['channels_active'])}")

                except Exception as e:
                    self.stats['messages_failed'] += 1
                    logger.error(f"处理消息时出错: {e}")
                    logger.exception(e)

            logger.info("✓ 消息处理器注册成功")

            # 步骤 3: 启动客户端并监听
            logger.info("步骤 3/3: 启动客户端并监听消息...")
            logger.info("========================================")

            await self.client.start()
            logger.info("✓ Telegram 监控器启动成功！")
            logger.info("等待新消息... 按 Ctrl+C 停止")
            logger.info("========================================")

            # 保持运行 - 使用与 debug_monitor.py 相同的简单等待方式
            self._running = True
            while self._running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("\n收到停止信号，正在关闭...")
            return True
        except Exception as e:
            logger.error(f"启动失败: {type(e).__name__}: {e}")
            logger.exception(e)
            return False
        finally:
            self._running = False

    def start(self):
        """启动监控（入口方法）"""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            logger.info("\n用户中断，程序退出")
        except Exception as e:
            logger.error(f"运行错误: {type(e).__name__}: {e}")
            logger.exception(e)

    def stop(self):
        """停止监控"""
        self._running = False
        if self.client and self.client.is_connected:
            asyncio.create_task(self.client.stop())
            logger.info("Telegram 客户端已断开连接")

    def get_channel_ids(self):
        """获取当前频道ID列表"""
        return self.channel_ids

    def set_channel_ids(self, channel_ids):
        """设置新的频道ID列表"""
        old_count = len(self.channel_ids)
        self.channel_ids = channel_ids.copy()
        new_count = len(self.channel_ids)
        logger.info(f"频道列表已更新: {old_count} -> {new_count} 个频道")

    def add_channel(self, channel_id):
        """添加单个频道"""
        if channel_id not in self.channel_ids:
            self.channel_ids.append(channel_id)
            logger.info(f"添加监控频道: {channel_id}")
            return True
        return False

    def remove_channel(self, channel_id):
        """删除频道"""
        if channel_id in self.channel_ids:
            self.channel_ids.remove(channel_id)
            logger.info(f"删除监控频道: {channel_id}")
            return True
        return False

    def is_channel_monitored(self, channel_id):
        """检查频道是否在监控列表中"""
        return channel_id in self.channel_ids

    def extract_message_data(self, message: Message) -> Dict:
        """提取消息数据 - 保持原有功能"""
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

        # 限制文本长度
        if len(data['text']) > 4000:
            data['text'] = data['text'][:4000] + '... [截断]'

        logger.debug(f"消息数据提取完成: {data['channel_name']} - {data['message_id']}")
        return data

    def get_media_type(self, message: Message) -> str:
        """获取媒体类型 - 保持原有功能"""
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

    async def stop_async(self):
        """异步停止监控"""
        if self.client and self.client.is_connected:
            await self.client.stop()
            logger.info("Telegram 客户端已断开连接")