"""
配置监听器 - 自动重新加载配置和频道列表
"""

import os
import threading
import time
from loguru import logger


class ConfigReloader:
    """配置文件热重载器"""

    def __init__(self, config_file, reload_callback):
        """
        初始化配置重载器

        Args:
            config_file: 配置文件路径
            reload_callback: 配置更改后的回调函数
        """
        self.config_file = config_file
        self.reload_callback = reload_callback
        self.last_modified = 0
        self.running = False
        self.thread = None

    def start(self, check_interval=5):
        """
        启动监控线程

        Args:
            check_interval: 检查间隔（秒）
        """
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._watch_loop, args=(check_interval,), daemon=True
        )
        self.thread.start()
        logger.info(f"启动配置文件监控: {self.config_file} (每 {check_interval} 秒检查一次)")

    def stop(self):
        """停止监控线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("配置文件监控已停止")

    def _watch_loop(self, interval):
        """监控循环"""
        while self.running:
            try:
                self._check_file()
            except Exception as e:
                logger.error(f"检查配置文件时出错: {e}")

            time.sleep(interval)

    def _check_file(self):
        """检查文件是否已修改"""
        if not os.path.exists(self.config_file):
            return

        try:
            current_modified = os.path.getmtime(self.config_file)

            # 第一次运行时记录时间
            if self.last_modified == 0:
                self.last_modified = current_modified
                return

            # 检查文件是否已修改
            if current_modified > self.last_modified:
                logger.info("检测到配置文件更改")
                self.last_modified = current_modified

                # 等待文件写入完成（避免读取到不完整的内容）
                time.sleep(0.5)

                # 调用回调函数
                try:
                    self.reload_callback()
                    logger.info("✓ 配置重新加载成功")
                except Exception as e:
                    logger.error(f"配置重新加载失败: {e}")

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")


def create_watcher(config_file, reload_callback):
    """创建并启动配置监听器

    Args:
        config_file: 配置文件路径
        reload_callback: 配置更改后的回调函数

    Returns:
        ConfigReloader 实例
    """
    reloader = ConfigReloader(config_file, reload_callback)
    reloader.start()
    return reloader
