# API接口使用指南（2025-12-16 更新）

## 📋 变更摘要

本次更新**完全保持了向后兼容性**，原有单条消息格式无需任何修改即可继续使用。同时新增了批量爬虫格式支持。

---

## 🔧 接口特性

### 1. 自动检测请求类型

服务端自动识别请求格式，无需额外配置：
- 识别到 `batch_id` 字段 → 按批量爬虫格式处理
- 无 `batch_id` 字段 → 按原有单条消息格式处理

### 2. 完全向后兼容

所有现有的Python监控器代码**无需任何修改**，继续正常工作。

---

## 📡 接口端点

### POST /api/v1/messages

**主接口端点**，支持两种请求格式。

---

## 💬 单条消息格式（原有格式，完全兼容）

### 请求格式

```json
{
  "channel_id": -1002115686230,
  "channel_name": "Pump Alert - GMGN",
  "message_id": 12345,
  "text": "消息文本内容",
  "timestamp": 1700000000,
  "sender": "Bot_PumpAlert (52504489)"
}
```

### 响应格式

```json
{
  "success": true,
  "message": "消息已接收并加入处理队列",
  "data": null
}
```

### Python 示例代码

```python
import requests
import time

# 原有代码无需任何修改
response = requests.post(
    "http://localhost:8080/api/v1/message",
    json={
        "channel_id": -1002115686230,
        "channel_name": "Pump Alert - GMGN",
        "message_id": 12345,
        "text": "🚀 NEW TOKEN ALERT!",
        "timestamp": int(time.time()),
        "sender": "Bot_PumpAlert (52504489)"
    }
)

data = response.json()
if data["success"]:
    print("消息发送成功")
else:
    print(f"发送失败: {data['message']}")
```

---

## 📦 批量爬虫格式（新增支持）

### 请求格式

```json
{
  "batch_id": "batch_{note_id}_{timestamp}",
  "timestamp": "2025-12-16T09:20:30",
  "source": "xhs_crawler_v1.0",
  "note_info": {
    "note_id": "6937fcb5000000001e0339ff",
    "note_title": "笔记标题",
    "total_comments": 50
  },
  "messages": [
    {
      "message_id": "comment_{comment_id}",
      "role": "user",
      "content": "清洗后的评论文本",
      "metadata": {
        "user_info": {
          "user_id": "user_123",
          "user_name": "用户昵称"
        },
        "interaction": {
          "like_count": 10,
          "reply_count": 3
        },
        "temporal": {
          "absolute": 1640000000.0,
          "relative": "昨天 20:38"
        },
        "location": {
          "country": "中国",
          "city": null
        }
      }
    }
  ]
}
```

### 响应格式

```json
{
  "status": "success",
  "batch_id": "batch_6937fcb5000000001e0339ff_202512160920",
  "note_info": {
    "note_id": "6937fcb5000000001e0339ff",
    "processed_count": 50,
    "total_count": 50
  },
  "analysis_result": {
    "sentiment_analysis": {
      "comment_001": {
        "sentiment": "positive",
        "confidence": 0.85,
        "emotion_scores": {
          "positive": 0.85,
          "negative": 0.10,
          "neutral": 0.05
        }
      }
    },
    "topic_analysis": {
      "comment_001": {
        "topics": ["产品质量", "性价比"],
        "confidence_scores": [0.9, 0.7]
      }
    },
    "keyword_analysis": {
      "comment_001": {
        "keywords": ["质量很好", "推荐购买"],
        "importance_scores": [0.8, 0.7]
      }
    }
  },
  "processing_stats": {
    "total_time_ms": 1500,
    "average_time_per_comment_ms": 30.0
  }
}
```

### Python 爬虫集成示例

```python
import requests
import time
from datetime import datetime

class CommentAnalyzerClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url

    def analyze_note_comments(self, note_id, note_title, comments):
        """分析笔记的所有评论"""

        # 构建批量请求
        batch_request = {
            "batch_id": f"batch_{note_id}_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "source": "xhs_crawler_v1.0",
            "note_info": {
                "note_id": note_id,
                "note_title": note_title,
                "total_comments": len(comments)
            },
            "messages": [self.format_comment(c) for c in comments]
        }

        # 发送请求
        response = requests.post(
            f"{self.base_url}/api/v1/message",
            json=batch_request,
            headers={"Content-Type": "application/json"}
        )

        return response.json()

    @staticmethod
    def format_comment(comment_data):
        """格式化单条评论"""
        return {
            "message_id": f"comment_{comment_data['id']}",
            "role": "user",
            "content": comment_data['content'].strip(),
            "metadata": {
                "user_info": {
                    "user_id": comment_data.get('user_id', ''),
                    "user_name": comment_data.get('user', '匿名')
                },
                "interaction": {
                    "like_count": comment_data.get('like_count', 0),
                    "reply_count": comment_data.get('reply_count', 0)
                },
                "temporal": {
                    "absolute": comment_data.get('timestamp', 0),
                    "relative": comment_data.get('relative_time', '')
                },
                "location": {
                    "country": comment_data.get('country'),
                    "city": comment_data.get('city')
                }
            }
        }


# 使用示例
if __name__ == "__main__":
    client = CommentAnalyzerClient()

    # 准备评论数据
    comments = [
        {
            "id": "001",
            "content": "这个口红颜色太好看了，非常喜欢！",
            "user_id": "user_001",
            "user": "美妆达人",
            "like_count": 10,
            "timestamp": 1640000000.0
        },
        {
            "id": "002",
            "content": "价格有点贵，但是质量很好",
            "user_id": "user_002",
            "user": "理性买家",
            "like_count": 5,
            "timestamp": 1640000100.0
        }
    ]

    # 发送分析请求
    result = client.analyze_note_comments(
        note_id="6937fcb5000000001e0339ff",
        note_title="我的美妆分享",
        comments=comments
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 🧪 测试验证

### 运行自动化测试

```bash
# 确保服务已经启动
python test_api_compatibility.py
```

预期输出：
```
============================================================
API接口兼容性测试
测试地址: http://localhost:8080
============================================================

📊 测试健康检查接口...
✅ 健康检查成功

📨 测试单条消息格式（向后兼容）...
HTTP状态码: 200
✅ 单条消息格式测试通过，响应格式保持兼容

📦 测试批量爬虫格式...
HTTP状态码: 200
✅ 批量格式测试通过，响应包含所有必要字段

🚨 测试格式错误的请求...
✅ 正确识别了格式错误的请求

============================================================
📊 测试结果总结
============================================================
✅ 通过 - 单条消息格式（向后兼容）
✅ 通过 - 批量爬虫格式
✅ 通过 - 格式错误处理

通过率: 3/3 (100.0%)

🎉 所有测试通过！API接口兼容性良好
```

---

## 📊 状态码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功处理 |
| 400 | 请求格式错误 |
| 408 | 请求超时 |
| 500 | 服务器内部错误 |

---

## 🎯 数据流向对比

### 单条消息（原有流程）

```
Python监控器
    ↓
POST /api/v1/messages
    ↓
ReceiveMessageRequest
    ↓
MessageProcessor
    ↓
ApiResponse
```

### 批量爬虫（新流程）

```
爬虫客户端
    ↓
POST /api/v1/messages
    ↓
BatchRequest
    ↓
批量验证
    ↓
逐条处理（MessageProcessor）
    ↓
BatchResponse
```

---

## 🚀 部署升级指南

### 1. 停止旧服务

```bash
# 停止旧的Rust服务
killall tg-meme-token-monitor
```

### 2. 编译新版本

```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor
cargo build --release
```

### 3. 启动新服务

```bash
# 启动新服务（使用相同配置）
./target/release/tg-meme-token-monitor
```

### 4. 运行兼容性测试

```bash
python test_api_compatibility.py
```

### 5. 验证Python监控器正常工作

检查现有的Python监控器日志，确认消息正常处理。

---

## ⚠️ 注意事项

### 1. 配置兼容性

新服务完全兼容原有的配置文件格式，无需修改 `config.toml`。

### 2. 日志格式

批量请求的日志格式：
```
📦 检测到批量请求格式
开始处理批量请求: batch_xxx, 笔记: xxx, 评论数: 50
✅ 批量请求验证通过，开始处理...
开始批量处理 50 条消息
✅ 消息 comment_001 处理成功
✅ 消息 comment_002 处理成功
...
🎉 批量处理完成
```

单条消息的日志格式：
```
💬 检测到单条消息格式
收到来自 Python 监控器的消息: [频道名] 消息ID
✅ 输入数据验证通过
🚀 调用processor.process_message()...
✅ process_message() 调用成功
🎉 消息已安全处理并加入队列
```

### 3. 性能影响

- 单条消息处理：**无性能影响**，与原有实现完全相同
- 批量请求处理：第一个版本为串行处理，后续可优化为并行

### 4. 错误恢复

- **业务错误**（如验证失败）：继续处理后续消息，返回partial状态
- **系统错误**（如网络中断）：记录错误日志，返回failed状态
- **单条消息panic**：被捕获并记录，不影响其他消息

---

## 📞 技术支持

如果遇到任何问题：

1. **检查日志**：查看服务日志中的错误信息
2. **运行测试**：执行 `python test_api_compatibility.py`
3. **查看文档**：参考方案文档 `/Users/dr4/.claude/plans/api-design-crawler-compat.md`
4. **提交问题**：在GitHub提交Issue

---

## 📝 版本记录

| 版本 | 日期 | 变更内容 | 兼容性 |
|------|------|----------|--------|
| v1.0 | 2025-11-28 | 初始版本 | - |
| v1.1 | 2025-12-16 | 新增批量爬虫格式支持 | 100%向后兼容 |

---

**重要提醒**：本次升级是完全向后兼容的，您可以**安全地部署**新版本而不会中断现有服务！🚀
