# Python 监控器运行时错误诊断报告

## 发现的问题

### 1. ⚠️ 严重问题：异步/同步调用不匹配

**位置**: `src/telegram_client.py:80`

```python
# 当前代码
self.http_sender.send_message(message_data)  # 同步调用

# 问题: handle_message 是 async 方法，但 send_message 是同步方法
# 可能导致阻塞事件循环
```

**修复建议**:

将 `send_message` 改为异步方法，或使用 `asyncio.to_thread`:

```python
# 方案A: 使用 to_thread
import asyncio
await asyncio.to_thread(self.http_sender.send_message, message_data)

# 方案B: 将 send_message 改为 async（需要修改 http_sender.py）
await self.http_sender.send_message(message_data)
```

### 2. ⚠️ MessageHandler 注册问题

**位置**: `src/telegram_client.py:48`

```python
self.client.add_handler(
    MessageHandler(self.handle_message, filters.channel & filters.incoming)
)
```

**潜在问题**: `handle_message` 是一个 async 函数，但 Pyrogram 的 MessageHandler 可能期望同步函数。

**修复建议**:

```python
# 移除 async，保持为同步方法
def handle_message(self, client: Client, message: Message):
    # 在需要的地方使用 asyncio.run_coroutine_threadsafe
    import asyncio
    asyncio.create_task(self.process_message_async(client, message))

async def process_message_async(self, client: Client, message: Message):
    # 异步处理逻辑
    message_data = self.extract_message_data(message)
    await asyncio.to_thread(self.http_sender.send_message, message_data)
```

### 3. ⚠️ 配置解析问题

**位置**: `src/config_loader.py`

**潜在问题**:
- `channel_ids` 解析为列表时，可能包含空字符串
- 没有处理配置缺失的默认值

**修复建议**:

```python
# 在 load_config 函数中添加验证
channel_ids_str = config['telegram']['channel_ids'].strip()

if not channel_ids_str:
    raise ValueError("[telegram] channel_ids 不能为空")

channel_ids = []
for channel_id in channel_ids_str.split(','):
    channel_id = channel_id.strip()
    if not channel_id:
        continue
    try:
        if channel_id.startswith('-100'):
            channel_ids.append(int(channel_id))
        else:
            raise ValueError(f"频道 ID 必须以 -100 开头: {channel_id}")
    except ValueError as e:
        raise ValueError(f"无效的频道 ID '{channel_id}': {e}")
```

### 4. ⚠️ HTTP 错误处理不完整

**位置**: `src/http_sender.py:20`

**潜在问题**:
- 没有验证 URL 格式
- 没有设置合理的连接池

**修复建议**:

```python
# 在 __init__ 中添加 URL 验证
from urllib.parse import urlparse

url_info = urlparse(self.url)
if not all([url_info.scheme, url_info.netloc]):
    raise ValueError(f"无效的 URL: {self.url}")

if url_info.scheme not in ['http', 'https']:
    raise ValueError(f"URL 协议必须是 http 或 https: {self.url}")

# 设置连接池
self.session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=0  # 我们自己处理重试
)
self.session.mount('http://', adapter)
self.session.mount('https://', adapter)
```

### 5. ⚠️ 消息数据验证缺失

**位置**: `src/telegram_client.py:114-143`

**潜在问题**:
- 没有验证 message.chat 是否为 None
- 没有处理 message.from_user 缺失的情况
- text 长度限制可能导致编码错误

**修复建议**:

```python
def extract_message_data(self, message: Message) -> Dict:
    # 验证 chat 存在
    if not message.chat:
        raise ValueError("消息没有 chat 信息")

    # 安全地获取数据
    data = {
        'channel_id': message.chat.id,
        'channel_name': getattr(message.chat, 'title', None) or 'Unknown',
        'message_id': message.id,
        'text': '',
        'timestamp': int(message.date.timestamp()),
        'sender': None,
    }

    # 提取文本
    text = message.text or message.caption or ''
    if not text and message.media:
        text = f"[Media: {self.get_media_type(message)}]"

    # 安全地截断文本
    max_length = 4000
    if len(text) > max_length:
        text = text[:max_length]
        # 确保不截断在 Unicode 字符中间
        while text and not text[-1].isprintable():
            text = text[:-1]
        text += '... [截断]'

    data['text'] = text

    # 提取发送者（安全模式）
    if message.from_user:
        try:
            user = message.from_user
            username = (
                user.username or
                user.first_name or
                f"User{user.id}"
            )
            data['sender'] = f"{username} ({user.id})"
        except Exception as e:
            logger.warning(f"提取发送者信息失败: {e}")

    return data
```

### 6. ⚠️ 日志配置问题

**位置**: `monitor.py:15-23`

**潜在问题**:
- 日志级别是硬编码的
- 生产环境可能需要不同的日志格式

**修复建议**:

```python
# 从配置读取日志级别
log_level = config['logging']['level']
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level=log_level
)
```

### 7. ⚠️ 导入路径问题

**位置**: `src/telegram_client.py:140`

```python
# 在文件末尾的导入
from pyrogram.handlers import MessageHandler
```

**问题**: 这个导入在类定义之后，可能导致循环依赖或导入错误。

**修复建议**:

```python
# 将导入移到文件顶部
from typing import Dict, List
from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from src.http_sender import HttpSender
```

## 修复脚本

我已经创建了一个修复补丁：`fix_python_monitor.patch`

## 推荐修复步骤

1. **生成修复后的文件**:
```bash
cd python_monitor
```

2. **测试修复**:
```bash
# 测试配置加载
python3 -c "from src.config_loader import load_config; cfg = load_config('config_sample.ini'); print('配置加载成功:', cfg['telegram']['channel_ids'])"

# 测试 HTTP 发送器
python3 -c "from src.http_sender import HttpSender; sender = HttpSender({'url': 'http://httpbin.org/post', 'max_retries': 1, 'timeout': 5}); print('HTTP 发送器创建成功')"

# 测试 Telegram 客户端导入
python3 -c "from src.telegram_client import TelegramMonitor; print('Telegram 客户端导入成功')"
```

3. **首次运行**:
```bash
# 先测试健康检查
python3 -c "
from src.http_sender import HttpSender
sender = HttpSender({'url': 'http://localhost:8080/api/v1/message', 'max_retries': 1, 'timeout': 10})
print('Health check:', 'PASS' if sender.health_check() else 'FAIL')
"

# 如果健康检查通过，再运行完整程序
python3 monitor.py config_sample.ini
```

4. **观察日志**:
- 检查是否有 `ERROR` 级别的日志
- 检查 `monitor.log` 文件中的异常信息
- 确保消息能正常发送到 Rust 服务

## 需要修复的关键问题

### 优先级 1（立即修复）:
1. MessageHandler 的 async/await 问题
2. HTTP 发送器的同步调用问题

### 优先级 2（建议修复）:
3. 配置验证和错误处理
4. 消息数据提取的边界情况
5. 导入顺序问题

### 优先级 3（可选优化）:
6. HTTP 连接池优化
7. 日志级别可配置
8. 更好的错误提示

## 测试建议

在修复后，按以下顺序测试：

1. **单元测试**:
   - 配置加载测试
   - HTTP 发送器测试
   - 消息数据提取测试

2. **集成测试**:
   - 运行 Rust 服务
   - 运行 Python 监控器
   - 观察日志输出

3. **端到端测试**:
   - 在监控的频道发送测试消息
   - 验证 Rust 服务接收消息
   - 验证 AI 分析
   - 验证最终转发

## 总结

Python 监控器的主要问题是 **异步/同步调用不匹配**，这是 Pyrogram 2.0+ 版本中常见的问题。修复后应该可以正常工作。
