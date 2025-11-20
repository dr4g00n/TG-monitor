#!/usr/bin/env python3
"""
频道管理工具

使用方法:
    # 查看当前频道列表
    python3 manage_channels.py --list
    python3 manage_channels.py -l

    # 添加频道
    python3 manage_channels.py --add -1001234567890 "频道名称"
    python3 manage_channels.py -a -1001234567890 "频道名称"

    # 删除频道
    python3 manage_channels.py --remove -1001234567890
    python3 manage_channels.py -r -1001234567890

    # 更新频道列表（替换所有）
    python3 manage_channels.py --update -100111,-100222,-100333
    python3 manage_channels.py -u -100111,-100222,-100333
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config_loader import load_config


def display_channels(config):
    """显示当前频道列表"""
    print("\n" + "=" * 60)
    print("当前监控频道列表")
    print("=" * 60)

    channel_ids = config['telegram']['channel_ids']

    if not channel_ids:
        print("当前没有监控任何频道")
        return

    for i, channel_id in enumerate(channel_ids, 1):
        print(f"[{i}] {channel_id}")

    print(f"\n总计: {len(channel_ids)} 个频道")
    print("=" * 60 + "\n")


def add_channel_to_config(config_file, channel_id, channel_name=None):
    """添加频道到配置文件"""
    config = load_config(config_file)

    channel_ids = config['telegram']['channel_ids']

    if channel_id in channel_ids:
        print(f"⚠️  频道 {channel_id} 已在监控列表中")
        return False

    channel_ids.append(channel_id)
    channel_ids.sort()

    # 更新配置文件
    update_config_file(config_file, config)

    print(f"✓ 已添加频道: {channel_id}")
    if channel_name:
        print(f"  频道名称: {channel_name}")

    return True


def remove_channel_from_config(config_file, channel_id):
    """从配置文件中删除频道"""
    config = load_config(config_file)

    channel_ids = config['telegram']['channel_ids']

    if channel_id not in channel_ids:
        print(f"⚠️  频道 {channel_id} 不在监控列表中")
        return False

    channel_ids.remove(channel_id)

    # 更新配置文件
    update_config_file(config_file, config)

    print(f"✓ 已删除频道: {channel_id}")

    return True


def update_channels_in_config(config_file, new_channel_ids):
    """更新频道列表（替换所有）"""
    config = load_config(config_file)

    old_count = len(config['telegram']['channel_ids'])
    config['telegram']['channel_ids'] = new_channel_ids

    # 更新配置文件
    update_config_file(config_file, config)

    print(f"✓ 频道列表已更新")
    print(f"  {old_count} -> {len(new_channel_ids)} 个频道")

    return True


def update_config_file(config_file, config):
    """更新配置文件"""
    import configparser

    parser = configparser.ConfigParser()
    parser.read(config_file)

    # 更新 channel_ids
    channel_ids = config['telegram']['channel_ids']
    parser.set('telegram', 'channel_ids', ','.join(str(cid) for cid in channel_ids))

    # 写回文件
    with open(config_file, 'w') as f:
        parser.write(f)

    print(f"\n💾 配置文件已更新: {config_file}")


def main():
    parser = argparse.ArgumentParser(description='频道管理工具', add_help=False)

    parser.add_argument('--help', '-h', action='help', help='显示帮助信息')

    parser.add_argument(
        '--config', '-c',
        default='config.ini',
        help='配置文件路径 (默认: config.ini)'
    )

    # 创建互斥的参数组
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--list', '-l',
        action='store_true',
        help='显示当前频道列表'
    )

    group.add_argument(
        '--add', '-a',
        nargs=2,
        metavar=('CHANNEL_ID', 'CHANNEL_NAME'),
        help='添加频道到监控列表'
    )

    group.add_argument(
        '--remove', '-r',
        metavar='CHANNEL_ID',
        help='从监控列表删除频道'
    )

    group.add_argument(
        '--update', '-u',
        metavar='CHANNEL_IDS',
        help='更新频道列表（逗号分隔，如: -100111,-100222,-100333）'
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    config_file = args.config

    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)

    try:
        if args.list:
            # 显示频道列表
            config = load_config(config_file)
            display_channels(config)

        elif args.add:
            # 添加频道
            channel_id_str, channel_name = args.add
            try:
                channel_id = int(channel_id_str)
                add_channel_to_config(config_file, channel_id, channel_name)
            except ValueError:
                print(f"❌ 无效的频道ID: {channel_id_str}")
                sys.exit(1)

        elif args.remove:
            # 删除频道
            try:
                channel_id = int(args.remove)
                remove_channel_from_config(config_file, channel_id)
            except ValueError:
                print(f"❌ 无效的频道ID: {args.remove}")
                sys.exit(1)

        elif args.update:
            # 更新频道列表
            try:
                channel_ids_str = args.update
                channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(',')]
                update_channels_in_config(config_file, channel_ids)
            except ValueError:
                print(f"❌ 无效的频道ID格式")
                sys.exit(1)

    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
