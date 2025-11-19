import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.http_sender import HttpSender

# Create sender
sender = HttpSender({
    'url': 'http://localhost:8080/api/v1/message',
    'max_retries': 1,
    'timeout': 5
})

# Test message
test_message = {
    "channel_id": -1001234567890,
    "channel_name": "测试频道",
    "message_id": 12345,
    "text": "新币发射：TestToken 合约地址 0x1234567890abcdef 可以考虑买入",
    "timestamp": 1700000000,
    "sender": "test_user (12345)"
}

print(f"Sending test message to Rust service...")
result = sender.send_message(test_message)
print(f"Result: {result}")
