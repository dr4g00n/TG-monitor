#!/bin/bash

# Telegram Monitor Python 安装脚本

set -e

echo "=========================================="
echo "Telegram Monitor Python 安装脚本"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $python_version"

# 提取主版本号
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 8 ]); then
    echo "错误: 需要 Python 3.8+"
    exit 1
fi
echo "✓ Python 版本检查通过"
echo ""

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ 虚拟环境已创建"
    echo ""
    echo "提示: 以后运行前需要执行: source venv/bin/activate"
    echo ""
fi

# 安装依赖
echo "安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依赖安装完成"
echo ""

# 检查配置文件
if [ ! -f "config.ini" ]; then
    echo "创建配置文件示例..."
    cp config_sample.ini config.ini
    echo "✓ 已创建 config.ini"
    echo ""
    echo "⚠️  重要: 请编辑 config.ini 文件，设置以下参数:"
    echo "   - telegram.api_id"
    echo "   - telegram.api_hash"
    echo "   - telegram.channel_ids"
    echo ""
else
    echo "✓ 配置文件已存在"
fi

echo ""
echo "=========================================="
echo "安装完成!"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 编辑 config.ini，配置你的 Telegram API 和频道 ID"
echo "2. 确保 Rust 服务已启动 (cargo run --release)"
echo "3. 运行监控器: python3 monitor.py"
echo ""
echo "首次运行需要登录 Telegram 账号:"
echo "  - 输入手机号 (格式: +86138xxxxxxxx)"
echo "  - 输入验证码"
echo "  - 如有两步验证，输入密码"
echo ""
