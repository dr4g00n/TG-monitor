# Rust Monitor HTTP API 接口文档

## 📋 接口概览

**服务地址**: `http://localhost:8080`

**认证方式**: 当前版本无需认证（建议在生产环境添加API Key认证）

**Content-Type**: `application/json; charset=utf-8`

**CORS策略**: 允许所有域名访问（建议在生产环境限制特定域名）

## 接口列表

### 1. 健康检查接口

#### **GET /health**

**接口描述**: 检查服务运行状态和健康情况

**请求示例**:
```bash
curl -X GET http://localhost:8080/health
```

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": null
}
```

**使用场景**:
- 服务监控和告警
- 负载均衡健康检查
- 部署前服务验证

---

### 2. 消息接收接口

#### **POST /api/v1/message**

**接口描述**: 接收来自Python监控器的Telegram消息，进行AI分析和处理

**请求头**:
```
Content-Type: application/json
```

**请求参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | Telegram频道/群组ID（例如: -1002115686230） |
| channel_name | string | 是 | 频道/群组名称 |
| message_id | integer | 是 | 消息ID |
| text | string | 是 | 消息文本内容 |
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

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "消息已成功接收并加入处理队列",
  "data": null
}
```

**失败响应 (400 Bad Request)**:
```json
{
  "success": false,
  "message": "消息格式验证失败: 缺少必要字段 channel_id",
  "data": null
}
```

**数据验证规则**:
- `channel_id`必须是有效的整数，负数表示群组/频道，正数表示私聊
- `text`字段长度限制为4000字符，超长会自动截断
- `timestamp`必须是有效的Unix时间戳（10位或13位整数）
- `sender`如果提供，格式应为"用户名 (用户ID)"

**错误码说明**:

| HTTP状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 200 | Success | 请求成功 |
| 400 | Bad Request | 请求格式错误或缺少必要字段 |
| 408 | Request Timeout | 请求超时 |
| 500 | Internal Server Error | 服务端处理错误 |

**使用场景**:
- Python监控器推送新消息到Rust服务
- 批量导入历史消息进行分析
- 测试AI分析功能

**注意事项**:
1. 消息会先进入处理队列，不会立即返回分析结果
2. 处理时间取决于AI服务响应速度和当前队列长度（通常30-300秒）
3. 处理结果会通过Telegram Bot自动转发到配置的目标用户
4. 大批量发送时建议控制请求频率（推荐每秒不超过10个请求）

---

### 3. 频道管理接口

#### **3.1 获取频道列表**

**GET /api/v1/channels**

**接口描述**: 获取当前监控的所有频道/群组列表

**请求示例**:
```bash
curl -X GET http://localhost:8080/api/v1/channels
```

**成功响应 (200 OK)**:
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

**字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| channel_id | integer | 频道/群组ID |
| channel_name | string/null | 频道/群组名称（可能为null）|
| added_at | integer | 添加时间（Unix时间戳）|

**使用场景**:
- 管理界面展示监控频道列表
- 验证频道配置是否生效
- 审计当前监控范围

---

#### **3.2 添加频道**

**POST /api/v1/channels**

**接口描述**: 添加新的频道/群组到监控列表

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

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "频道添加成功: -1001234567890",
  "data": -1001234567890
}
```

**失败响应 (400 Bad Request)**:
```json
{
  "success": false,
  "message": "频道添加失败: 频道ID已存在于监控列表",
  "data": null
}
```

**使用场景**:
- 动态添加新的监控频道
- 批量导入频道配置

---

#### **3.3 更新频道列表**

**PUT /api/v1/channels**

**接口描述**: 替换整个监控频道列表（覆盖更新）

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

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "频道列表更新成功，共3个频道",
  "data": 3
}
```

**警告**: 此操作会完全替换现有频道列表，请谨慎使用！

**使用场景**:
- 批量更新监控频道配置
- 从备份恢复频道列表

---

#### **3.4 删除频道**

**DELETE /api/v1/channels/{channel_id}**

**接口描述**: 从监控列表中删除指定频道

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 要删除的频道ID |

**请求示例**:
```bash
curl -X DELETE http://localhost:8080/api/v1/channels/-1001234567890
```

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "频道删除成功: -1001234567890",
  "data": -1001234567890
}
```

**使用场景**:
- 停止监控某个频道
- 清理无效频道配置

---

#### **3.5 检查频道**

**GET /api/v1/channels/{channel_id}/check**

**接口描述**: 验证特定频道的可访问性和有效性

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_id | integer | 是 | 要检查的频道ID |

**请求示例**:
```bash
curl -X GET http://localhost:8080/api/v1/channels/-1002115686230/check
```

**成功响应 (200 OK)**:
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

**失败响应 (400 Bad Request)**:
```json
{
  "success": false,
  "message": "频道无法访问: Peer id invalid: -1009999999999",
  "data": null
}
```

**使用场景**:
- 验证频道ID是否正确
- 检查频道是否已加入/可访问
- 批量验证频道配置

---

## 📊 响应格式说明

### 标准响应结构

所有接口（除健康检查外）返回统一格式的JSON响应：

```json
{
  "success": boolean,    // 请求是否成功
  "message": string,     // 人类可读的提示信息
  "data": any            // 响应数据，结构取决于具体接口
}
```

### 状态码映射

| HTTP状态码 | success值 | 说明 |
|------------|-----------|------|
| 200 | true | 请求成功，操作完成 |
| 400 | false | 请求失败，客户端错误 |
| 408 | false | 请求超时 |
| 500 | false | 服务端错误 |
| 502 | false | 网关错误（AI服务不可用） |
| 503 | false | 服务不可用 |
| 504 | false | 上游服务超时 |

---

## 🚀 爬虫开发最佳实践

### 1. 请求频率控制

```python
import time
import requests

# 推荐请求频率：每秒不超过10个请求
REQUEST_DELAY = 0.1  # 100ms延迟

def send_with_rate_limit(url, data):
    response = requests.post(url, json=data)
    time.sleep(REQUEST_DELAY)  # 控制请求频率
    return response
```

### 2. 错误处理和重试

```python
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def send_with_retry(url, data):
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        raise
```

### 3. 批量数据处理

```python
def batch_process_messages(messages, batch_size=10):
    """批量处理消息，每批10条"""
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        # 发送批量更新请求
        response = requests.put(
            "http://localhost:8080/api/v1/channels",
            json={"channel_ids": batch}
        )
        print(f"处理批次 {i//batch_size + 1}: {response.json()}")
```

### 4. 数据解析示例

```python
def parse_telegram_message(raw_data):
    """Parse Telegram message for analysis"""
    return {
        'channel_id': raw_data['chat']['id'],
        'channel_name': raw_data['chat'].get('title', 'Unknown'),
        'message_id': raw_data['message_id'],
        'text': raw_data.get('text', ''),
        'timestamp': raw_data['date'],
        'sender': raw_data.get('from', {}).get('username', 'Unknown')
    }
```

### 5. 完整爬虫示例

```python
import requests
import time
import json
from datetime import datetime

class TelegramMonitorCrawler:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramMonitorCrawler/1.0'
        })

    def health_check(self):
        """检查服务健康状态"""
        response = self.session.get(f"{self.api_url}/health")
        return response.json()

    def get_channels(self):
        """获取监控频道列表"""
        response = self.session.get(f"{self.api_url}/api/v1/channels")
        return response.json()

    def check_channel(self, channel_id):
        """检查频道有效性"""
        response = self.session.get(
            f"{self.api_url}/api/v1/channels/{channel_id}/check"
        )
        return response.json()

    def add_channel(self, channel_id, channel_name=None):
        """添加监控频道"""
        data = {
            "channel_id": channel_id,
            "channel_name": channel_name
        }
        response = self.session.post(
            f"{self.api_url}/api/v1/channels",
            json=data
        )
        return response.json()

    def remove_channel(self, channel_id):
        """删除监控频道"""
        response = self.session.delete(
            f"{self.api_url}/api/v1/channels/{channel_id}"
        )
        return response.json()

    def send_message(self, message_data):
        """发送消息到处理服务"""
        response = self.session.post(
            f"{self.api_url}/api/v1/message",
            json=message_data
        )
        return response.json()

# 使用示例
if __name__ == "__main__":
    crawler = TelegramMonitorCrawler()

    # 1. 检查服务健康
    health = crawler.health_check()
    print(f"服务状态: {health}")

    # 2. 获取当前频道列表
    channels = crawler.get_channels()
    print(f"监控频道: {channels}")

    # 3. 添加新频道
    result = crawler.add_channel(-1001234567890, "New Channel")
    print(f"添加结果: {result}")

    # 4. 检查频道有效性
    check_result = crawler.check_channel(-1001234567890)
    print(f"频道检查: {check_result}")

    # 5. 发送测试消息
    test_message = {
        "channel_id": -1001234567890,
        "channel_name": "Test Channel",
        "message_id": 99999,
        "text": "🚀 TEST ALERT: New token detected!",
        "timestamp": int(time.time()),
        "sender": "TestBot"
    }
    result = crawler.send_message(test_message)
    print(f"消息发送: {result}")
```

---

## ⚠️ 注意事项

### 1. 频率限制
- **建议**: 单个IP每秒不超过10个请求
- **硬性限制**: 系统层面暂无硬性限制（建议后续添加）

### 2. 数据安全
- 消息内容可能包含敏感信息（API密钥、私钥等）
- 建议对重要数据进行加密存储
- 限制日志中的敏感信息输出

### 3. 错误处理
- 必须实现完善的错误处理和重试机制
- 记录错误日志便于问题排查
- 对不同类型的错误采用不同的重试策略

### 4. 数据完整性
- 消息处理是异步的，不会立即返回结果
- 建议实现消息ID去重机制
- 重要操作记录操作日志

---

## 🔧 接口变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-11-28 | 初始文档创建 | Claude |

---

## 📞 技术支持

如有接口相关问题，请联系项目维护者或提交GitHub Issue。

**文档生成时间**: 2025年11月28日
**接口版本**: v1.0
**服务版本**: tg-meme-token-monitor v1.0
