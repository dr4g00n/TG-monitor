# Message API 接口文档

## 📋 接口概述

**端点**: `POST /api/v1/message`

**功能**: 接收批量评论数据并进行AI分析（情感分析、主题分析、关键词提取）

**Content-Type**: `application/json`

---

## 📝 请求格式

### 完整请求示例

```json
{
  "batch_id": "batch_{note_id}_{timestamp}",
  "timestamp": "2025-12-16T10:00:00",
  "source": "xhs_crawler_v1.0",
  "note_info": {
    "note_id": "6937fcb5000000001e0339ff",
    "note_title": "笔记标题",
    "total_comments": 50
  },
  "messages": [
    {
      "message_id": "comment_001",
      "role": "user",
      "content": "这个口红颜色太好看了，非常喜欢！",
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

---

## 🏗️ 数据模型

### BatchRequest (批量请求)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_id` | string | 是 | 批次ID，格式: `batch_{note_id}_{timestamp}` |
| `timestamp` | string | 是 | ISO 8601格式时间戳 |
| `source` | string | 是 | 数据来源标识 |
| `note_info` | object | 是 | 笔记信息 |
| `messages` | array | 是 | 评论消息数组 |

### NoteInfo (笔记信息)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记ID |
| `note_title` | string | 是 | 笔记标题 |
| `total_comments` | integer | 是 | 评论总数 |

### Message (单条消息)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message_id` | string | 是 | 评论ID |
| `role` | string | 是 | 角色（固定为"user"） |
| `content` | string | 是 | 评论内容 |
| `metadata` | object | 是 | 元数据 |

### MessageMetadata (消息元数据)

**注意**: `user_info` 字段是**必填**的，位于 `metadata` 对象内

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_info` | object | 是 | **用户信息（客户端报错缺少此字段）** |
| `interaction` | object | 是 | 互动数据 |
| `temporal` | object | 是 | 时间信息 |
| `location` | object | 是 | 位置信息 |

### UserInfo (用户信息)

**注意**: 这是导致客户端报错的字段，必须包含在 `metadata.user_info` 中

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 用户ID |
| `user_name` | string | 是 | 用户昵称 |

### Interaction (互动数据)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `like_count` | integer | 是 | 点赞数 |
| `reply_count` | integer | 是 | 回复数 |

### Temporal (时间信息)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `absolute` | float | 是 | Unix时间戳 |
| `relative` | string | 是 | 相对时间描述 |

### Location (位置信息)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `country` | string/null | 否 | 国家 |
| `city` | string/null | 否 | 城市 |

---

## ✅ 成功响应

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

### 状态说明

- `status`: `success` | `partial` | `failed`
- `processed_count`: 成功处理的评论数
- `total_count`: 总评论数

---

## ❌ 错误响应

### 格式验证错误

当请求格式不正确时返回：

```json
{
  "status": "failed",
  "batch_id": "batch_xxx_timestamp",
  "note_info": {
    "note_id": "unknown",
    "processed_count": 0,
    "total_count": 0
  },
  "analysis_result": {
    "sentiment_analysis": {},
    "topic_analysis": {},
    "keyword_analysis": {}
  },
  "processing_stats": {
    "total_time_ms": 0,
    "average_time_per_comment_ms": 0.0
  },
  "error_message": "解析失败: missing field `user_info`"
}
```

**常见错误**:

1. **缺少 `user_info` 字段**（客户端当前遇到的问题）
   ```
   error_message: "解析失败: missing field `user_info`"
   ```
   **原因**: `messages[].metadata.user_info` 字段缺失
   **解决**: 确保每条消息的 metadata 都包含 user_info 对象

2. **JSON格式错误**
   ```
   error_message: "解析失败: expected value at line X column Y"
   ```
   **原因**: JSON格式不正确
   **解决**: 使用JSON验证工具检查格式

3. **数据类型不匹配**
   ```
   error_message: "解析失败: invalid type"
   ```
   **原因**: 字段类型不匹配
   **解决**: 检查字段类型是否符合文档要求

---

## 🐍 Python 客户端示例

### 完整示例（包含 user_info）

```python
import requests
import json
import time
from datetime import datetime

class CommentAnalyzerClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.trust_env = False  # 禁用代理

    def analyze_comments(self, note_id, note_title, comments):
        """分析笔记评论"""

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
            "messages": [
                self.format_comment(comment) for comment in comments
            ]
        }

        # 发送请求
        response = self.session.post(
            f"{self.base_url}/api/v1/message",
            json=batch_request,
            timeout=30
        )

        return response.json()

    def format_comment(self, comment_data):
        """格式化单条评论"""
        return {
            "message_id": f"comment_{comment_data['id']}",
            "role": "user",
            "content": comment_data['content'].strip(),
            "metadata": {
                "user_info": {  # ✅ 注意：必须包含此字段
                    "user_id": comment_data.get('user_id', ''),
                    "user_name": comment_data.get('user_name', '匿名')
                },
                "interaction": {
                    "like_count": comment_data.get('like_count', 0),
                    "reply_count": comment_data.get('reply_count', 0)
                },
                "temporal": {
                    "absolute": comment_data.get('timestamp', 0.0),
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
            "content": "这个口红颜色太好看了！",
            "user_id": "user_001",
            "user_name": "美妆达人",
            "like_count": 10,
            "timestamp": 1640000000.0,
            "country": "中国",
            "city": "上海"
        },
        {
            "id": "002",
            "content": "价格有点贵，但是质量很好",
            "user_id": "user_002",
            "user_name": "理性买家",
            "like_count": 5,
            "timestamp": 1640000100.0,
            "country": "中国",
            "city": "北京"
        }
    ]

    # 发送分析请求
    result = client.analyze_comments(
        note_id="6937fcb5000000001e0339ff",
        note_title="我的美妆分享",
        comments=comments
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 🐛 错误排查

### 错误：missing field `user_info`

**问题代码**:
```python
# ❌ 错误：缺少 user_info
{
    "message_id": "comment_001",
    "role": "user",
    "content": "评论内容",
    "metadata": {
        # 没有 user_info 字段！
        "interaction": {...},
        "temporal": {...},
        "location": {...}
    }
}
```

**正确代码**:
```python
# ✅ 正确：包含 user_info
{
    "message_id": "comment_001",
    "role": "user",
    "content": "评论内容",
    "metadata": {
        "user_info": {  # ✅ 必须包含
            "user_id": "user_001",
            "user_name": "用户名"
        },
        "interaction": {...},
        "temporal": {...},
        "location": {...}
    }
}
```

### 验证JSON格式

使用Python验证JSON格式是否正确：

```python
import json

# 示例请求
data = {
    "batch_id": "batch_test_001",
    "timestamp": "2025-12-16T10:00:00",
    "source": "xhs_crawler_v1.0",
    "note_info": {
        "note_id": "test_note_001",
        "note_title": "测试笔记",
        "total_comments": 1
    },
    "messages": [
        {
            "message_id": "comment_001",
            "role": "user",
            "content": "这个产品很好",
            "metadata": {
                "user_info": {
                    "user_id": "user_001",
                    "user_name": "测试用户"
                },
                "interaction": {
                    "like_count": 10,
                    "reply_count": 2
                },
                "temporal": {
                    "absolute": 1640000000.0,
                    "relative": "2小时前"
                },
                "location": {
                    "country": "中国",
                    "city": "北京"
                }
            }
        }
    ]
}

# 验证JSON序列化
try:
    json_str = json.dumps(data)
    print("✅ JSON格式正确")

    # 检查是否有所有必需字段
    for msg in data['messages']:
        if 'user_info' not in msg.get('metadata', {}):
            print("❌ 缺少 user_info 字段")
        else:
            print("✅ user_info 字段存在")
except Exception as e:
    print(f"❌ JSON格式错误: {e}")
```

---

## 📊 快速测试

### 使用 curl 测试

```bash
cat > test_request.json << 'EOF'
{
  "batch_id": "batch_test_001",
  "timestamp": "2025-12-16T10:00:00",
  "source": "test_crawler",
  "note_info": {
    "note_id": "test_note_001",
    "note_title": "测试笔记",
    "total_comments": 1
  },
  "messages": [
    {
      "message_id": "comment_001",
      "role": "user",
      "content": "测试评论内容",
      "metadata": {
        "user_info": {
          "user_id": "user_001",
          "user_name": "测试用户"
        },
        "interaction": {
          "like_count": 10,
          "reply_count": 2
        },
        "temporal": {
          "absolute": 1640000000.0,
          "relative": "2小时前"
        },
        "location": {
          "country": "中国",
          "city": "北京"
        }
      }
    }
  ]
}
EOF

# 发送请求（禁用代理）
unset http_proxy https_proxy
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

**预期响应**: `{"status":"success",...}` ✅

---

## 🎯 关键要点

### 1. user_info 的位置

```
batch_request
└─ messages[]
   └─ metadata
      └─ user_info  ← 必须包含
         ├─ user_id
         └─ user_name
```

### 2. 必填字段检查清单

每个评论消息必须包含：
- [ ] `message_id`
- [ ] `role`（固定为"user"）
- [ ] `content`
- [ ] `metadata`（必须包含）
  - [ ] `user_info`（必须包含） ← **客户端报错点**
    - [ ] `user_id`
    - [ ] `user_name`
  - [ ] `interaction`
    - [ ] `like_count`
    - [ ] `reply_count`
  - [ ] `temporal`
    - [ ] `absolute`
    - [ ] `relative`
  - [ ] `location`
    - [ ] `country`（可以为null）
    - [ ] `city`（可以为null）

### 3. 错误解决流程

1. 检查客户端发送的JSON
2. 确认 `messages[].metadata.user_info` 存在
3. 确认 `user_info` 包含 `user_id` 和 `user_name`
4. 使用JSON验证工具检查格式
5. 参考本文档的Python示例代码

---

## 📞 技术支持

如果遇到其他问题：

1. **查看服务日志**: `tail -f service_with_trace.log | grep tower_http`
2. **验证JSON格式**: 使用在线JSON验证工具
3. **参考完整示例**: 见 `API_MESSAGE_INTERFACE.md`
4. **查看实现代码**: `src/models/batch_request.rs`
