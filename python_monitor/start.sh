#!/bin/bash

# 快速启动脚本

echo "=========================================="
echo "Telegram Monitor Python - 快速启动"
echo "=========================================="
echo ""

# 检查配置文件
if [ ! -f "config.ini" ]; then
    echo "错误: 未找到 config.ini 配置文件"
    echo ""
    echo "请执行以下步骤："
    echo "1. 复制示例配置: cp config_sample.ini config.ini"
    echo "2. 编辑 config.ini，设置你的 Telegram API 和频道 ID"
    echo "3. 确保 Rust 服务已启动"
    echo ""
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "检测到虚拟环境，激活中..."
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
    echo ""
fi

# 启动监控器
echo "启动 Telegram 监控器..."
echo "=========================================="
echo ""

python3 monitor.py config.ini
