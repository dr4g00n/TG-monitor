# Rust Monitor HTTP API 接口文档

## 📋 接口总览

**服务地址**: `http://localhost:8080`

**认证方式**: 当前版本无需认证（建议在生产环境添加API Key认证）

**Content-Type**: `application/json; charset=utf-8`

**接口版本**: v1.0

## 基础接口

### 1. 健康检查

**GET** `/health`

**功能**: 检查服务运行状态和健康情况

**请求示例**:
```bash
curl -X GET http://localhost:8080/health
```

**响应示例**:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": null
}
```

**状态码**:
- `200`: 服务正常运行
- `500`: 服务异常

---

## 消息处理接口

### 2. 接收消息

**POST** `/api/v1/message`

**功能**: 接收来自Python监控器的Telegram消息，进行AI分析和处理

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 频道/群组ID（负数表示频道/群组，正数表示私聊） |
| channel_name | string | 是 | 频道/群组名称 |
| message_id | integer | 是 | 消息ID |
| text | string | 是 | 消息文本内容（最大4000字符） |
| timestamp | integer | 是 | 消息时间戳（Unix时间戳） |
| sender | string | 否 | 发送者信息（格式: "用户名 (用户ID)"） |

**请求示例**:
```bash
curl -X POST http://localhost:8080/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": -1002115686230,
    "channel_name": "Pump Alert - GMGN",
    "message_id": 12345,
    "text": "🚀 NEW TOKEN ALERT! Contract: 0x1234567890abcdef1234567890abcdef12345678",
    "timestamp": 1700000000,
    "sender": "Bot_PumpAlert (52504489)"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "消息已成功接收并加入处理队列",
  "data": null
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "消息格式验证失败: 缺少必要字段 channel_id",
  "data": null
}
```

**状态码**:
- `200`: 消息接收成功
- `400`: 请求格式错误或缺少必要字段
- `408`: 请求超时
- `500`: 服务端处理错误

**重要说明**:
- 消息会先进入处理队列，不会立即返回分析结果
- 处理时间取决于AI服务响应速度和当前队列长度（通常30-300秒）
- 处理结果会通过Telegram Bot自动转发到配置的目标用户
- 大批量发送时建议控制请求频率（推荐每秒不超过10个请求）

---

## 频道管理接口

### 3. 获取频道列表

**GET** `/api/v1/channels`

**功能**: 获取当前监控的所有频道/群组列表

**请求示例**:
```bash
curl -X GET http://localhost:8080/api/v1/channels
```

**响应示例**:
```json
{
  "success": true,
  "message": "获取频道列表成功",
  "data": [
    {
      "channel_id": -1002115686230,
      "channel_name": "Pump Alert - GMGN",
      "added_at": 1700000000
    },
    {
      "channel_id": -1002096576678,
      "channel_name": "Happy Nuts",
      "added_at": 1700000100
    }
  ]
}
```

**状态码**:
- `200`: 获取成功
- `500`: 服务端错误

---

### 4. 添加频道

**POST** `/api/v1/channels`

**功能**: 添加新的频道/群组到监控列表

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 频道/群组ID |
| channel_name | string | 否 | 频道/群组名称 |

**请求示例**:
```bash
curl -X POST http://localhost:8080/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": -1001234567890,
    "channel_name": "Test Channel"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "频道添加成功: -1001234567890",
  "data": -1001234567890
}
```

**状态码**:
- `200`: 添加成功
- `400`: 频道ID已存在或格式错误

**注意**: channel_id为负数表示群组/频道，正数表示私聊

---

### 5. 删除频道

**DELETE** `/api/v1/channels/{channel_id}`

**功能**: 从监控列表中删除指定频道

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 要删除的频道ID |

**请求示例**:
```bash
curl -X DELETE http://localhost:8080/api/v1/channels/-1001234567890
```

**响应示例**:
```json
{
  "success": true,
  "message": "频道删除成功: -1001234567890",
  "data": -1001234567890
}
```

**状态码**:
- `200`: 删除成功
- `400`: 频道不存在或删除失败

---

### 6. 检查频道有效性

**GET** `/api/v1/channels/{channel_id}/check`

**功能**: 验证特定频道的可访问性和有效性

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 要检查的频道ID |

**请求示例**:
```bash
curl -X GET http://localhost:8080/api/v1/channels/-1002115686230/check
```

**响应示例**:
```json
{
  "success": true,
  "message": "频道可访问: Pump Alert - GMGN",
  "data": {
    "channel_id": -1002115686230,
    "title": "Pump Alert - GMGN",
    "type": "channel",
    "accessible": true
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| channel_id | integer | 频道ID |
| title | string | 频道/群组标题 |
| type | string | 类型（channel、supergroup、private） |
| accessible | boolean | 是否可访问 |

**状态码**:
- `200`: 频道有效且可访问
- `400`: 频道无法访问或ID无效

**使用场景**:
- 验证频道ID是否正确
- 检查频道是否已加入/可访问
- 批量验证频道配置

---

### 7. 批量更新频道列表

**PUT** `/api/v1/channels`

**功能**: 替换整个监控频道列表（覆盖更新）

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_ids | array | 是 | 频道ID列表 |

**请求示例**:
```bash
curl -X PUT http://localhost:8080/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_ids": [
      -1002115686230,
      -1002096576678,
      -1002040892468
    ]
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "频道列表更新成功，共3个频道",
  "data": 3
}
```

**警告**: 此操作会完全替换现有频道列表，请谨慎使用！

**状态码**:
- `200`: 更新成功
- `400`: 参数错误

---

## 📊 响应格式说明

### 标准响应结构

所有接口返回统一格式的JSON响应：

```json
{
  "success": boolean,    // 请求是否成功
  "message": string,     // 人类可读的提示信息
  "data": any            // 响应数据（null或具体数据结构）
}
```

### 状态码映射

| HTTP状态码 | success值 | 说明 |
|------------|-----------|------|
| 200 | true | 请求成功 |
| 400 | false | 请求失败，客户端错误 |
| 408 | false | 请求超时 |
| 500 | false | 服务端错误 |
| 502 | false | 网关错误 |
| 503 | false | 服务不可用 |
| 504 | false | 上游服务超时 |

---

## 🐍 Python爬虫集成示例

### 快速开始

```python
import requests
import json
import time

class RustMonitorClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RustMonitorCrawler/1.0'
        })

    def is_healthy(self):
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.json().get('success', False)
        except:
            return False

    def get_channels(self):
        """获取监控频道列表"""
        response = self.session.get(f"{self.base_url}/api/v1/channels")
        return response.json()

    def send_message(self, message_data):
        """发送消息到处理服务"""
        response = self.session.post(
            f"{self.base_url}/api/v1/message",
            json=message_data,
            timeout=30
        )
        return response.json()

    def check_channel(self, channel_id):
        """检查频道有效性"""
        response = self.session.get(
            f"{self.base_url}/api/v1/channels/{channel_id}/check"
        )
        return response.json()

# 使用示例
if __name__ == "__main__":
    client = RustMonitorClient()

    # 1. 检查服务健康
    if client.is_healthy():
        print("✅ 服务运行正常")
    else:
        print("❌ 服务异常")

    # 2. 获取频道列表
    channels = client.get_channels()
    print(f"监控频道数: {len(channels.get('data', []))}")

    # 3. 发送测试消息
    test_message = {
        "channel_id": -1002115686230,
        "channel_name": "Test Channel",
        "message_id": 99999,
        "text": "🚀 TEST ALERT: New token 0x1234567890abcdef",
        "timestamp": int(time.time()),
        "sender": "TestBot"
    }

    result = client.send_message(test_message)
    print(f"发送结果: {result}")
```

### 高级用法示例

```python
import requests
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential

class AdvancedRustMonitorClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AdvancedRustMonitorCrawler/1.0'
        })
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_with_retry(self, method, endpoint, data=None):
        """发送请求并支持自动重试"""
        url = f"{self.base_url}{endpoint}"

        if method.upper() == "GET":
            response = self.session.get(url, timeout=10)
        elif method.upper() == "POST":
            response = self.session.post(url, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = self.session.delete(url, timeout=10)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        response.raise_for_status()
        return response.json()

    def batch_send_messages(self, messages, delay=0.1):
        """批量发送消息，带延迟控制"""
        results = []
        for i, message in enumerate(messages):
            try:
                result = self.send_with_retry("POST", "/api/v1/message", message)
                results.append(result)
                print(f"✅ 消息 {i+1}/{len(messages)} 发送成功")
            except Exception as e:
                print(f"❌ 消息 {i+1}/{len(messages)} 发送失败: {e}")
                results.append({"success": False, "error": str(e)})

            # 控制发送频率
            time.sleep(delay)

        return results

    def validate_and_send(self, raw_message):
        """验证消息格式并发送"""
        # 验证必要字段
        required_fields = ["channel_id", "channel_name", "message_id", "text", "timestamp"]
        for field in required_fields:
            if field not in raw_message:
                return {"success": False, "error": f"缺少必要字段: {field}"}

        # 验证字段类型
        if not isinstance(raw_message["channel_id"], int):
            return {"success": False, "error": "channel_id必须是整数"}

        if not isinstance(raw_message["timestamp"], int):
            return {"success": False, "error": "timestamp必须是整数"}

        # 发送消息
        return self.send_with_retry("POST", "/api/v1/message", raw_message)

# 批量发送示例
if __name__ == "__main__":
    client = AdvancedRustMonitorClient()

    # 批量发送测试消息
    test_messages = []
    for i in range(10):
        test_messages.append({
            "channel_id": random.choice([-1002115686230, -1002096576678, -1002040892468]),
            "channel_name": f"TestChannel_{i}",
            "message_id": 100000 + i,
            "text": f"🚀 TEST ALERT {i}: 0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "timestamp": int(time.time()),
            "sender": f"TestBot_{i}"
        })

    print("开始批量发送消息...")
    results = client.batch_send_messages(test_messages, delay=0.2)

    # 统计结果
    success_count = sum(1 for r in results if r.get('success', False))
    print(f"\n批量发送完成:")
    print(f"  成功: {success_count}/{len(results)}")
    print(f"  失败: {len(results) - success_count}/{len(results)}")
```

---

## 📋 最佳实践

### 1. 请求频率控制

```python
# 推荐请求频率：每秒不超过10个请求
REQUEST_DELAY = 0.1  # 100ms延迟

# 或使用漏桶算法控制
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=10, per_second=1):
        self.max_requests = max_requests
        self.per_second = per_second
        self.requests = deque()

    def allow_request(self):
        now = time.time()
        # 清理超过时间窗口的请求记录
        while self.requests and now - self.requests[0] > self.per_second:
            self.requests.popleft()

        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True
```

### 2. 错误处理和重试

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
)
def robust_request(url, data, timeout=30):
    """健壮请求，自动重试3次"""
    response = requests.post(url, json=data, timeout=timeout)
    response.raise_for_status()
    return response.json()
```

### 3. 数据完整性保证

```python
def validate_message_format(raw_message):
    """验证消息格式完整性"""
    required_fields = ["channel_id", "channel_name", "message_id", "text", "timestamp"]

    # 检查必需字段
    for field in required_fields:
        if field not in raw_message:
            return False, f"缺少必要字段: {field}"

    # 验证字段类型
    if not isinstance(raw_message["channel_id"], int):
        return False, "channel_id必须是整数"

    if not isinstance(raw_message["timestamp"], (int, float)):
        return False, "timestamp必须是数字"

    # 验证内容长度
    if len(raw_message["text"]) > 4000:
        return False, "消息内容超过4000字符限制"

    return True, "格式验证通过"
```

### 4. 性能优化技巧

```python
# 使用连接池
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=50,
    max_retries=3
)
session.mount("http://", adapter)

# 批量操作
async def batch_operation(channels):
    """批量处理频道操作"""
    results = []
    for channel in channels:
        try:
            result = check_channel(channel)
            results.append(result)
        except Exception as e:
            print(f"处理失败 {channel}: {e}")
            results.append({"channel": channel, "error": str(e)})

    return results
```

---

## 📊 状态码与错误处理

### 常见错误类型

| 错误场景 | HTTP状态码 | 错误信息示例 | 处理建议 |
|----------|------------|--------------|----------|
| 参数缺失 | 400 | "缺少必要字段: channel_id" | 检查请求参数完整性 |
| 无效频道ID | 400 | "Peer id invalid: -1009999999999" | 使用 /check 接口验证 |
| 频道已存在 | 400 | "频道ID已存在于监控列表" | 先删除再添加 |
| 频道不存在 | 400 | "频道不存在: -1009999999999" | 检查频道ID是否正确 |
| 请求超时 | 408 | "请求超时" | 增加超时时间或重试 |
| 服务不可用 | 503 | "AI服务不可用" | 等待服务恢复 |

### 重试策略建议

```python
# 不同类型错误的重试策略
RETRY_POLICIES = {
    'network_error': {
        'max_attempts': 5,
        'backoff': 'exponential',
        'retry_on': [408, 500, 502, 503, 504]
    },
    'client_error': {
        'max_attempts': 1,  # 不重试
        'backoff': 'none',
        'retry_on': [400, 401, 403, 404]
    },
    'success_200': {
        'max_attempts': 1,  # 不重试
        'backoff': 'none',
        'retry_on': []
    }
}
```

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-11-28 | 初始文档创建 | Claude |

---

## 🔗 相关文档

- [项目架构文档](../ARCHITECTURE.md)
- [实现指南](../IMPLEMENTATION_GUIDE.md)
- [配置文件说明](./config_sample.ini)

---

## 📞 技术支持

如有接口相关问题，请联系项目维护者或提交GitHub Issue。

**文档生成时间**: 2025年11月28日
**服务版本**: tg-meme-token-monitor v1.0
**接口版本**: v1.0
**最后更新**: 2025-11-28 22:45
