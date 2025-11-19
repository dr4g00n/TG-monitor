"""
配置加载模块
"""

import configparser
from pathlib import Path


def load_config(config_file):
    """
    加载配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        dict: 配置字典
    """
    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')

    # 解析 channel_ids 为列表
    channel_ids_str = config['telegram']['channel_ids']
    channel_ids = []

    if channel_ids_str:
        for channel_id in channel_ids_str.split(','):
            try:
                channel_ids.append(int(channel_id.strip()))
            except ValueError:
                raise ValueError(f"无效的频道 ID: {channel_id}")

    # 构建配置字典
    return {
        'telegram': {
            'api_id': int(config['telegram']['api_id']),
            'api_hash': config['telegram']['api_hash'],
            'session_file': config['telegram']['session_file'],
            'channel_ids': channel_ids,
        },
        'rust_service': {
            'url': config['rust_service']['url'],
            'max_retries': int(config['rust_service'].get('max_retries', '3')),
            'timeout': int(config['rust_service'].get('timeout', '30')),
        },
        'logging': {
            'level': config['logging']['level'],
            'log_file': config['logging'].get('log_file', ''),
        }
    }


def create_sample_config():
    """创建配置文件示例"""
    sample = '''[telegram]
# Telegram API 配置
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = my_monitor.session

# 要监控的频道 ID 列表
channel_ids = -1001234567890,-1009876543210

[rust_service]
url = http://localhost:8080/api/v1/message
max_retries = 3
timeout = 30

[logging]
level = INFO
'''

    with open('config_sample.ini', 'w', encoding='utf-8') as f:
        f.write(sample)

    print("已创建配置文件示例: config_sample.ini")
    print("请将 YOUR_API_ID, YOUR_API_HASH 和 channel_ids 替换为实际值")
