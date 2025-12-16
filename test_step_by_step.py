import requests
import json
from datetime import datetime

url = "http://localhost:8080/api/v1/message"
session = requests.Session()
session.trust_env = False

# 基础请求结构
base_request = {
    "batch_id": "batch_step_test",
    "timestamp": "2025-12-16T15:00:00Z",
    "source": "test",
    "note_info": {
        "note_id": "test",
        "note_title": "test",
        "total_comments": 1
    },
}

# 测试1: 空messages
print("测试1: 空messages数组...")
test1 = {**base_request, "messages": []}
resp = session.post(url, json=test1)
print(f"  状态: {resp.status_code}, 错误: {resp.json()['error_message']}\n")

# 测试2: 添加一个message，使用最少字段
print("测试2: 添加最少字段的message...")
test2 = {**base_request}
test2["messages"] = [
    {
        "message_id": "test1",
        "role": "user",
        "content": "test",
        "metadata": {
            "user_info": {"user_id": "u1", "user_name": "test"},
            "interaction": {"like_count": 0, "reply_count": 0},
            "temporal": {"absolute": 1.0, "relative": "now"},
            "location": {"country": "test", "city": "test"}
        }
    }
]
resp = session.post(url, json=test2)
result = resp.json()
print(f"  状态: {resp.status_code}")
print(f"  批ID: {result.get('batch_id')}")
print(f"  状态: {result.get('status')}")
if 'error_message' in result:
    print(f"  错误: {result['error_message']}")
else:
    print(f"  成功处理 {result.get('note_info', {}).get('processed_count', 0)} 条评论")
print()
