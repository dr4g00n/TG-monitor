#!/usr/bin/env python3
"""
测试错误处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.http_sender import HttpSender

# Create sender
sender = HttpSender({
    'url': 'http://localhost:8080/api/v1/message',
    'max_retries': 2,
    'timeout': 5
})

# Test 1: 正确的消息
print("\n=== 测试1: 正确的消息格式 ===")
test_message1 = {
    "channel_id": -1001234567890,
    "channel_name": "测试频道",
    "message_id": 12345,
    "text": "新币发射：TestToken 合约地址 0x1234567890abcdef 可以考虑买入",
    "timestamp": 1700000000,
    "sender": "test_user (12345)"
}
result = sender.send_message(test_message1)
print(f"Result: {result}\n")

# Test 2: 缺少必填字段
print("=== 测试2: 缺少必填字段 ===")
test_message2 = {
    "channel_id": -100123,
    "text": "只有部分字段的消息"
}
result = sender.send_message(test_message2)
print(f"Result: {result}\n")

# Test 3: 服务不可达
print("=== 测试3: 服务不可达 ===")
sender_bad = HttpSender({
    'url': 'http://localhost:9999/api/v1/message',  # 错误的端口
    'max_retries': 2,
    'timeout': 3
})

result = sender_bad.send_message(test_message1)
print(f"Result: {result}\n")

# Test 4: 健康检查
print("=== 测试4: 健康检查 ===")
result = sender.health_check()
print(f"Health check: {result}\n")
