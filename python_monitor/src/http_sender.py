"""
HTTP 发送模块
用于将消息发送到 Rust 处理服务
"""

import json
import time
from typing import Dict, Optional
import requests
from loguru import logger


class HttpSender:
    """HTTP 发送器，将消息发送到 Rust 服务"""

    def __init__(self, config: Dict):
        """
        初始化

        Args:
            config: 配置字典
                - url: Rust 服务地址
                - max_retries: 最大重试次数
                - timeout: 超时时间（秒）
        """
        self.url = config['url']
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()

        # 配置代理：绕过 localhost 和 127.0.0.1
        self.session.trust_env = False
        self.session.proxies = {
            'http': None,
            'https': None,
        }

        logger.info(f"HTTP 发送器初始化完成: {self.url}")

    def send_message(self, message_data: Dict) -> bool:
        """
        发送消息到 Rust 服务

        Args:
            message_data: 消息数据字典

        Returns:
            bool: 是否发送成功
        """
        # ✅ 添加详细发送日志
        logger.info(f"📤 HTTP 发送消息:")
        logger.info(f"  URL: {self.url}")
        logger.info(f"  频道: {message_data.get('channel_name', 'Unknown')}")
        logger.info(f"  消息ID: {message_data.get('message_id', 'Unknown')}")
        logger.debug(f"  完整数据: {json.dumps(message_data, ensure_ascii=False, indent=2)}")

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 第 {attempt + 1}/{self.max_retries + 1} 次重试...")

                logger.debug(f"发送 HTTP 请求 (尝试 {attempt + 1}/{self.max_retries + 1})")

                response = self.session.post(
                    self.url,
                    json=message_data,
                    timeout=self.timeout,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'TelegramMonitor/1.0'
                    }
                )

                logger.info(f"  响应状态: HTTP {response.status_code}")
                logger.debug(f"  响应内容: {response.text[:200]}{'...' if len(response.text) > 200 else ''}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"✓ 消息发送成功: {message_data['channel_name']} - {message_data['message_id']}")
                        return True
                    else:
                        logger.error(f"✗ 服务返回错误: {result.get('message', '未知错误')}")
                        return False
                else:
                    logger.error(f"✗ HTTP 错误 {response.status_code}: {response.text[:100]}{'...' if len(response.text) > 100 else ''}")

                    # 如果不是最后一次尝试，等待后重试
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt  # 指数退避
                        logger.info(f"⏱️  等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)

            except requests.exceptions.Timeout:
                logger.error(f"✗ 请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                logger.error(f"✗ 连接错误: {e} (尝试 {attempt + 1}/{self.max_retries + 1})")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"✗ 发送消息异常: {type(e).__name__}: {e}")
                return False

        logger.error(f"✗ 发送失败 after {self.max_retries + 1} 次尝试")
        return False

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否正常
        """
        try:
            # 从 URL 中提取基础地址
            base_url = self.url.split('/api/')[0]
            health_url = f"{base_url}/health"

            logger.debug(f"检查 Rust 服务健康状态: {health_url}")

            response = self.session.get(
                health_url,
                timeout=10,
                headers={'User-Agent': 'TelegramMonitor/1.0'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✓ Rust 服务健康检查通过")
                    return True

            logger.warning(f"✗ Rust 服务健康检查失败: {response.text}")
            return False

        except Exception as e:
            logger.error(f"✗ 健康检查异常: {type(e).__name__}: {e}")
            return False
