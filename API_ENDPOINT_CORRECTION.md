# API端点问题说明与修复指南

## 🔍 问题确认

### 测试结果

| 端点 | 状态码 | 结果 | 说明 |
|------|--------|------|------|
| `/health` | 200 | ✅ 正常 | 服务运行正常 |
| `/api/v1/message` | 200 | ✅ 正常 | 正确端点（单数） |
| `/api/v1/messages` | 404 | ❌ 错误 | **错误端点**（复数） |
| `/info` | 404 | ❌ 错误 | 未定义的端点 |

---

## 📋 正确端点列表

### 已实现并可用的端点

```
GET    /health                          - 健康检查
POST   /api/v1/message                  - 接收消息（支持单条和批量）
GET    /api/v1/channels                 - 获取频道列表
POST   /api/v1/channels                 - 添加频道
PUT    /api/v1/channels                 - 更新频道列表
DELETE /api/v1/channels/:channel_id     - 删除频道
GET    /api/v1/channels/:channel_id/check - 检查频道
```

---

## ❌ 错误端点说明

### 1. `/api/v1/messages` (复数)

**错误原因**: 服务器配置的路由是 `/api/v1/message`（单数），客户端使用了错误的复数形式。

**解决方案**:
```python
# ❌ 错误
response = requests.post("http://localhost:8080/api/v1/messages", json=data)

# ✅ 正确
response = requests.post("http://localhost:8080/api/v1/message", json=data)
```

### 2. `/info`

**错误原因**: 这个端点在服务器中未定义。

**说明**: 如果需要服务信息，请使用 `/health` 端点。

---

## 🔧 客户端修复

### 单条消息格式

```python
import requests
import time

# ❌ 错误示例
response = requests.post(
    "http://localhost:8080/api/v1/messages",  # 错误的复数形式
    json={
        "channel_id": -1002115686230,
        "channel_name": "Pump Alert - GMGN",
        "message_id": 12345,
        "text": "测试消息",
        "timestamp": int(time.time())
    }
)
# 结果: 404 Not Found ❌

# ✅ 正确示例
response = requests.post(
    "http://localhost:8080/api/v1/message",  # 正确的单数形式
    json={
        "channel_id": -1002115686230,
        "channel_name": "Pump Alert - GMGN",
        "message_id": 12345,
        "text": "测试消息",
        "timestamp": int(time.time())
    }
)
# 结果: 200 OK ✅
```

### 批量消息格式

```python
# ❌ 错误示例
response = requests.post(
    "http://localhost:8080/api/v1/messages",  # 错误的复数形式
    json={
        "batch_id": "batch_test_001",
        "timestamp": "2025-12-16T10:00:00",
        "source": "xhs_crawler_v1.0",
        "note_info": {
            "note_id": "6937fcb5000000001e0339ff",
            "note_title": "测试笔记",
            "total_comments": 2
        },
        "messages": [
            {
                "message_id": "comment_001",
                "role": "user",
                "content": "评论内容",
                "metadata": {...}
            }
        ]
    }
)
# 结果: 404 Not Found ❌

# ✅ 正确示例
response = requests.post(
    "http://localhost:8080/api/v1/message",  # 正确的单数形式
    json={
        "batch_id": "batch_test_001",
        "timestamp": "2025-12-16T10:00:00",
        "source": "xhs_crawler_v1.0",
        "note_info": {
            "note_id": "6937fcb5000000001e0339ff",
            "note_title": "测试笔记",
            "total_comments": 2
        },
        "messages": [...]
    }
)
# 结果: 200 OK ✅
```

---

## 📚 文档对比

### Python监控器文档
文件：`python_monitor/HTTP_API_DOCS.md`

正确文档示例：
```bash
# ✅ 正确（单数）
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Rust服务端文档
文件：`api_documentation.md`

正确文档示例：
```bash
# ✅ 正确（单数）
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 💡 快速验证

在客户端环境中运行此测试，确认端点是否正确：

```bash
# 测试正确的端点（单数）
unset http_proxy https_proxy
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{"channel_id":-1002115686230,"channel_name":"Test","message_id":99999,"text":"test","timestamp":1700000000}'

# 预期结果: 200 OK
# {"success":true,"message":"消息已接收并加入处理队列","data":null}
```

---

## 📊 总结

| 问题 | 原因 | 影响 | 修复方法 |
|------|------|------|----------|
| `/api/v1/messages` | 错误的复数形式 | 404 Not Found | 改为 `/api/v1/message` |
| `/info` | 未定义的端点 | 404 Not Found | 使用 `/health` 替代 |
| `/health` | 正常端点 | 200 OK | 保持使用 |

---

## ⚡ 立即行动

1. **检查客户端代码**: 搜索所有使用 `/api/v1/messages` 的地方
2. **修改为单数**: 改为 `/api/v1/message`
3. **移除 `/info`调用**: 改为使用 `/health`
4. **重新测试**: 确认所有接口返回 200 OK

---

## 🔧 兼容性考虑

如果需要同时支持单数和复数形式，可以添加备用路由：

```rust
// 在 server.rs 中添加备用路由
.route("/api/v1/message", post(handler::receive_message))
.route("/api/v1/messages", post(handler::receive_message))  // 兼容复数形式
```

**但建议**: 统一使用 `/api/v1/message`（单数），保持RESTful API的一致性。

---

## ✅ 完整客户端示例

```python
import requests
import time

# 不使用代理（避免503错误）
session = requests.Session()
session.trust_env = False

def send_single_message():
    """发送单条消息"""
    response = session.post(
        "http://localhost:8080/api/v1/message",  # ✅ 注意：这里是单数
        json={
            "channel_id": -1002115686230,
            "channel_name": "Test Channel",
            "message_id": 12345,
            "text": "测试消息",
            "timestamp": int(time.time())
        }
    )
    return response.json()

def send_batch_messages():
    """发送批量消息"""
    response = session.post(
        "http://localhost:8080/api/v1/message",  # ✅ 注意：这里也是单数
        json={
            "batch_id": f"batch_{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "xhs_crawler_v1.0",
            "note_info": {
                "note_id": "6937fcb5000000001e0339ff",
                "note_title": "测试笔记",
                "total_comments": 2
            },
            "messages": [
                {
                    "message_id": "comment_001",
                    "role": "user",
                    "content": "测试评论1",
                    "metadata": {...}
                },
                {
                    "message_id": "comment_002",
                    "role": "user",
                    "content": "测试评论2",
                    "metadata": {...}
                }
            ]
        }
    )
    return response.json()

def health_check():
    """健康检查"""
    response = session.get("http://localhost:8080/health")
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 1. 健康检查
    health = health_check()
    print(f"健康检查: {health}")

    # 2. 发送单条消息
    result1 = send_single_message()
    print(f"单条消息: {result1}")

    # 3. 发送批量消息
    result2 = send_batch_messages()
    print(f"批量消息: {result2}")
```

---

**重要提醒**: 所有API端点中的 "message" 都是单数形式，不是复数形式。请务必检查您的客户端代码，将 `/api/v1/messages` 改为 `/api/v1/message`。