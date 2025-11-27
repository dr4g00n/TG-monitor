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

            # 步骤 2: 注册消息处理器（将在客户端启动后验证频道）
            logger.info("步骤 2/3: 注册消息处理器...")

            @self.client.on_message()
            async def message_handler(client, message):
                """
                全局消息捕获和分析处理器
                - 捕获所有消息
                - 分析消息类型和来源
                - 只处理我们关心的消息（频道和 Bot）
                """
                # ==================== 全局消息捕获 ====================
                logger.info("🎯【全局捕获】收到新消息！")
                logger.info(f"  📍 聊天ID: {message.chat.id}")
                logger.info(f"  📍 消息ID: {message.id}")
                logger.info(f"  📍 聊天类型: {message.chat.type}")
                logger.info(f"  📍 聊天标题: {getattr(message.chat, 'title', 'N/A')}")

                # 显示发送者信息
                if message.from_user:
                    sender = message.from_user
                    sender_name = sender.username or sender.first_name or 'Unknown'
                    logger.info(f"  👤 发送者用户: {sender_name} ({sender.id})")
                elif message.sender_chat:
                    sender = message.sender_chat
                    sender_name = getattr(sender, 'title', 'Unknown')
                    logger.info(f"  📢 发送者频道: {sender_name} ({sender.id})")

                # 显示消息内容预览
                if message.text:
                    preview = message.text[:200].replace('\n', '\\n')
                    logger.info(f"  📝 内容预览: {preview}{'...' if len(message.text) > 200 else ''}")
                elif message.caption:
                    preview = message.caption[:200].replace('\n', '\\n')
                    logger.info(f"  🖼️  媒体描述: {preview}{'...' if len(message.caption) > 200 else ''}")

                # ==================== 消息类型分析 ====================
                logger.info("🔬【消息分析】开始分析消息类型...")

                # 分析1: 是否在监控的频道列表中
                if message.chat.id in self.channel_ids:
                    logger.info(f"  ✅【频道消息】这是监控的频道消息！")
                    message_type = "channel"
                # 分析2: 是否为 Bot 消息
                elif str(message.chat.type) == "ChatType.BOT":
                    logger.info(f"  🤖【Bot消息】这是 Bot 消息，检查是否包含 Pump Alert...")
                    message_type = "bot"
                # 分析3: 是否为私聊
                elif str(message.chat.type) == "ChatType.PRIVATE":
                    logger.info(f"  💬【私聊消息】这是私人聊天消息")
                    message_type = "private"
                # 分析4: 是否为群组/超级群组
                elif str(message.chat.type) in ["ChatType.GROUP", "ChatType.SUPERGROUP"]:
                    logger.info(f"  👥【群组消息】这是群组消息")
                    message_type = "group"
                else:
                    logger.info(f"  ❓【未知类型】未识别的聊天类型: {message.chat.type}")
                    message_type = "unknown"

                # ==================== 智能过滤和处理 ====================
                logger.info("🤖【智能处理】根据消息类型决定是否处理...")

                # 处理我们关心的消息类型：频道消息、Bot 消息、群组消息和私聊消息
                if message_type in ["channel", "bot", "group", "private"]:
                    logger.info(f"  ✅【处理决定】处理此消息 (类型: {message_type})")

                    # 特殊处理：群组和私聊消息，检查是否包含 Pump Alert 信息
                    if message_type in ["group", "private"] and message.text:
                        logger.info("🔍【非频道消息检查】检查是否包含 Pump/Alert 关键词...")
                        if "PUMP" in message.text.upper() or "ALERT" in message.text.upper():
                            logger.info("🎯【特殊消息】群组/私聊消息包含 Pump/Alert 关键词！")
                            # 继续处理，可能包含重要信息

                    # 特殊调试：针对 Pump Alert 频道和 Bot 消息的详细日志
                    if message.chat.id == -1002115686230:
                        logger.info("🚨【特殊频道】收到 PUMP ALERT 频道消息！")

                    # Bot 消息特殊处理：检查是否包含 Pump Alert 信息
                    if message_type == "bot" and message.text and "PUMP" in message.text.upper():
                        logger.info("🎯【Bot关键词】Bot消息包含 PUMP 关键词！")

                        # 检查是否包含 Pump Alert 频道信息
                        if "-1002115686230" in message.text or "Pump Alert" in message.text:
                            logger.info("🎯【确认PumpAlert】这是 Pump Alert 的 Bot 转发消息！")
                            # 将 Bot 消息视为 Pump Alert 频道消息进行处理
                            pump_alert_data = {
                                'channel_id': -1002115686230,
                                'channel_name': 'Pump Alert - GMGN',
                                'message_id': message.id,
                                'text': message.text,
                                'timestamp': int(message.date.timestamp()),
                                'sender': f"Bot_{message.chat.id}",
                                'is_bot_forward': True
                            }
                            # 使用 Pump Alert 频道ID进行后续处理
                            effective_channel_id = -1002115686230
                        else:
                            # 其他 Bot 消息，使用 Bot ID
                            effective_channel_id = message.chat.id
                    else:
                        # 正常频道消息
                        effective_channel_id = message.chat.id

                    # ✅ 更新统计
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = message.date
                    self.stats['channels_active'].add(effective_channel_id)

                    try:
                        # 提取消息信息
                        channel_name = getattr(message.chat, 'title', 'Unknown')
                        logger.info(f"📨【消息详情】正在处理:")
                        logger.info(f"  📍 频道: {channel_name} ({effective_channel_id})")
                        logger.info(f"  📝 消息ID: {message.id}")
                        logger.info(f"  ⏰ 时间: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")

                        # 提取并发送消息数据
                        if message_type == "bot" and "-1002115686230" in message.text:
                            # 使用 Pump Alert 数据
                            message_data = pump_alert_data
                        else:
                            # 正常提取消息数据
                            message_data = self.extract_message_data(message)

                        # 发送到 Rust 服务
                        logger.info(f"⬆️【转发到Rust】发送到处理服务...")
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

                else:
                    logger.info(f"  ⏭️【跳过处理】不处理此消息 (类型: {message_type})")
                    # 只记录接收统计，不处理消息
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = message.date
                    self.stats['channels_active'].add(message.chat.id)
                    return  # 直接返回，不继续处理

                # ==================== 消息处理 ====================

                # 只有在处理的消息才执行这部分
                try:
                    # 确定有效频道/聊天ID和名称
                    if message_type == "bot" and message.text and ("-1002115686230" in message.text or "Pump Alert" in message.text):
                        # Bot转发的Pump Alert消息映射到实际频道
                        effective_channel_id = -1002115686230
                        effective_channel_name = "Pump Alert - GMGN"
                    elif message_type == "group":
                        # 群组消息 - 接受权限限制，专注于内容分析
                        effective_channel_id = message.chat.id
                        effective_channel_name = getattr(message.chat, 'title', f'Group_{message.chat.id}')
                        # 注意：作为普通成员，无法获取其他成员的详细信息，这是Telegram的安全限制
                        logger.info("  📌【权限说明】作为普通成员，无法获取其他成员的详细信息，专注于消息内容分析")
                    elif message_type == "private":
                        # 私聊消息
                        effective_channel_id = message.chat.id
                        sender_name = getattr(message.from_user, 'username', 'Unknown') if message.from_user else 'Unknown'
                        effective_channel_name = f"Private_{sender_name}"
                    else:
                        # 正常频道消息
                        effective_channel_id = message.chat.id
                        effective_channel_name = getattr(message.chat, 'title', 'Unknown')

                    # 记录活跃频道/聊天
                    self.stats['channels_active'].add(effective_channel_id)

                    # 提取消息信息
                    logger.info(f"📨 收到新消息:")
                    logger.info(f"  来源: {effective_channel_name} ({effective_channel_id})")
                    logger.info(f"  消息ID: {message.id}")
                    logger.info(f"  时间: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 显示发送者信息（根据聊天类型调整显示级别）
                    if message.from_user:
                        sender = message.from_user
                        sender_name = sender.username or sender.first_name or 'Unknown'
                        # 群组消息：简化发送者信息，专注于内容
                        if message_type == "group":
                            logger.info(f"  发送者: Group_Member")
                        else:
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

                    # 提取消息数据（根据聊天类型特殊处理）
                    if message_type == "bot" and message.text and ("-1002115686230" in message.text or "Pump Alert" in message.text):
                        # 使用 Pump Alert 数据
                        message_data = {
                            'channel_id': -1002115686230,
                            'channel_name': 'Pump Alert - GMGN',
                            'message_id': message.id,
                            'text': message.text,
                            'timestamp': int(message.date.timestamp()),
                            'sender': f"Bot_{message.chat.id}",
                            'is_bot_forward': True
                        }
                    elif message_type == "group":
                        # 群组消息 - 专注于内容分析，简化发送者信息
                        message_data = {
                            'channel_id': message.chat.id,
                            'channel_name': getattr(message.chat, 'title', f'Group_{message.chat.id}'),
                            'message_id': message.id,
                            'text': message.text or '',
                            'timestamp': int(message.date.timestamp()),
                            'sender': 'Group_Member',  # 简化发送者信息，专注于内容
                            'is_group': True,
                            'content_analysis': self.analyze_message_content(message)
                        }
                    else:
                        # 正常提取消息数据
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

            # 步骤 3: 启动客户端、验证频道并开始监听
            logger.info("步骤 3/3: 启动客户端、验证频道并开始监听...")
            logger.info("========================================")

            await self.client.start()
            logger.info("✓ Telegram 监控器启动成功！")

            # 验证频道访问权限（需要在客户端启动后进行）
            logger.info("验证频道访问权限...")
            verified_channels, failed_channels = await self.verify_channels()

            # 如果所有频道都验证失败，给出警告但继续运行
            if not verified_channels:
                logger.warning("⚠️  所有频道验证失败！将继续运行但无法监控任何频道。")
                logger.warning("请检查：1) 频道ID是否正确 2) 是否已加入这些频道 3) 账号权限")

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

    async def verify_channels(self):
        """验证所有频道的访问权限"""
        logger.info("验证频道访问权限...")
        verified_channels = []
        failed_channels = []

        for i, channel_id in enumerate(self.channel_ids, 1):
            try:
                chat = await self.client.get_chat(channel_id)
                logger.info(f"  ✓ [{i}] 频道可访问: {chat.title} ({channel_id})")
                verified_channels.append(channel_id)
            except Exception as e:
                logger.error(f"  ✗ [{i}] 无法访问频道 {channel_id}: {e}")
                failed_channels.append(channel_id)

        # 更新监控列表为仅包含验证通过的频道
        logger.info(f"✓ 频道验证完成: {len(verified_channels)} 个可用, {len(failed_channels)} 个失败")

        if failed_channels:
            logger.warning(f"以下频道验证失败，将被跳过: {failed_channels}")

        return verified_channels, failed_channels

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

    def analyze_message_content(self, message: Message) -> dict:
        """
        分析消息内容，提供智能内容分析
        专注于消息内容而非发送者身份
        """
        analysis = {
            'message_length': 0,
            'has_links': False,
            'has_mentions': False,
            'has_hashtags': False,
            'has_emojis': False,
            'keyword_matches': [],
            'sentiment': 'neutral',
            'language': 'unknown'
        }

        if not message.text:
            return analysis

        text = message.text

        # 基础统计
        analysis['message_length'] = len(text)

        # 内容特征检测
        analysis['has_links'] = 'http' in text.lower() or 'www.' in text.lower()
        analysis['has_mentions'] = '@' in text
        analysis['has_hashtags'] = '#' in text
        analysis['has_emojis'] = any(ord(char) > 127 for char in text)

        # 关键词匹配（专注于加密货币相关词汇）
        crypto_keywords = [
            'pump', 'dump', 'moon', 'diamond', 'hands', 'hodl',
            'buy', 'sell', 'hold', 'trade', 'swap', 'liquidity',
            'contract', 'address', 'ca', 'token', 'coin'
        ]

        text_lower = text.lower()
        analysis['keyword_matches'] = [keyword for keyword in crypto_keywords if keyword in text_lower]

        # 简单的情感分析
        positive_words = ['moon', 'pump', 'buy', 'bull', 'up', 'gain', 'profit']
        negative_words = ['dump', 'sell', 'bear', 'down', 'loss', 'rug']

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            analysis['sentiment'] = 'positive'
        elif negative_count > positive_count:
            analysis['sentiment'] = 'negative'
        else:
            analysis['sentiment'] = 'neutral'

        # 语言检测（简单实现）
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            analysis['language'] = 'chinese'
        elif any('a' <= char <= 'z' for char in text.lower()):
            analysis['language'] = 'english'
        else:
            analysis['language'] = 'mixed'

        return analysis

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