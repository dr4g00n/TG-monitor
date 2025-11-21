#!/bin/bash

echo "========================================"
echo "Telegram Bot 转发功能测试"
echo "========================================"

BOT_TOKEN="8251881402:AAEzi7YFZJOr6FA5h9bF_dJUy0SkU_SbWU0"
TARGET_USER="8030185949"

echo "Bot Token: ${BOT_TOKEN:0:20}..."
echo "目标用户: $TARGET_USER"

# 测试消息
TEST_MESSAGE="🔥 *TG监控系统测试*\n📊 系统状态: 正常运行\n✅ Bot Token: 验证通过\n🎯 目标用户: 8030185949\n⏰ 测试时间: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "📤 发送测试消息..."
echo "消息内容: $TEST_MESSAGE"

# URL编码
ENCODED_MESSAGE=$(echo "$TEST_MESSAGE" | sed 's/ /%20/g' | sed 's/!/%21/g' | sed 's/"/%22/g' | sed 's/#/%23/g' | sed 's/\$/%24/g' | sed 's/&/%26/g' | sed "s/'/%27/g" | sed 's/(/%28/g' | sed 's/)/%29/g' | sed 's/\*/%2A/g' | sed 's/\+/%2B/g' | sed 's/\,/%2C/g' | sed 's/\//%2F/g' | sed 's/:/%3A/g' | sed 's/;/%3B/g' | sed 's/\=/%3D/g' | sed 's/\?/%3F/g' | sed 's/@/%40/g' | sed 's/\[/%5B/g' | sed 's/\]/%5D/g')

# 构建API URL
API_URL="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${TARGET_USER}&text=${ENCODED_MESSAGE}&parse_mode=Markdown"

echo "API URL: ${API_URL:0:100}..."

# 发送请求
echo ""
echo "执行发送请求..."
RESPONSE=$(curl -s -X POST "$API_URL")

echo "响应: $RESPONSE"

# 检查响应
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "🎉 消息成功发送到目标用户！"
    MESSAGE_ID=$(echo "$RESPONSE" | grep -o '"message_id":[0-9]*' | grep -o '[0-9]*')
    echo "消息ID: $MESSAGE_ID"
else
    echo "⚠️  消息发送可能失败"
    if echo "$RESPONSE" | grep -q '"description"'; then
        ERROR_DESC=$(echo "$RESPONSE" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
        echo "错误描述: $ERROR_DESC"
    fi
fi

echo ""
echo "========================================"
echo "测试完成！请检查用户 8030185949 的 Telegram"
echo "========================================"
