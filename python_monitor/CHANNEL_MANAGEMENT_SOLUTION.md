# Python 监控器频道管理解决方案

## 📋 问题描述

Python 监控器监控的频道 ID 无法实时更新，管理不便。

## ✅ 解决方案

提供了三种灵活的管理方式（可以组合使用）：

---

## 方式一：配置文件热重载（推荐）

### 🎯 概述

创建配置监听器，自动检测配置文件变化并重新加载频道列表。

### 📁 文件位置

- `python_monitor/src/config_watcher.py` - 配置监听器实现

### 🛠️ 使用方法

#### 1. 安装依赖

```bash
cd python_monitor
source venv/bin/activate
pip install watchdog
```

#### 2. 在 monitor.py 中集成

```python
from src.config_watcher import create_watcher
from src.config_loader import load_config

def reload_config():
    """重新加载配置"""
    global config, monitor

    # 加载新配置
    new_config = load_config('config.ini')

    # 更新监控器频道列表
    new_channel_ids = new_config['telegram']['channel_ids']
    monitor.set_channel_ids(new_channel_ids)

    config = new_config
    logger.info("✓ 配置重新加载完成")

# 主程序中启动监听器
if __name__ == "__main__":
    # ... 初始化监控器 ...

    # 启动配置监听器
    watcher = create_watcher('config.ini', reload_config)

    try:
        monitor.start()
    finally:
        watcher.stop()
```

#### 3. 修改配置文件

直接编辑 `python_monitor/config.ini`：

```ini
[telegram]
channel_ids = -1002040892468,-1001419575394,-1001420359318,-1001234567890  # 添加或删除ID
```

保存文件后，监控器会自动重新加载频道列表！

---

## 方式二：频道管理工具（命令行）

### 🎯 概述

提供命令行工具，无需手动编辑配置文件。

### 📁 文件位置

- `python_monitor/manage_channels.py` - 频道管理工具

### 🛠️ 使用方法

#### 1. 查看当前频道列表

```bash
cd python_monitor
source venv/bin/activate

python3 manage_channels.py --list
# 或简写
python3 manage_channels.py -l
```

**输出示例：**
```
============================================================
当前监控频道列表
============================================================
[1] -1002040892468
[2] -1001419575394
[3] -1001420359318
[4] -1001234567890

总计: 4 个频道
============================================================
```

#### 2. 添加频道

```bash
# 添加单个频道
python3 manage_channels.py --add -100987654321 "新频道名称"

# 简写
python3 manage_channels.py -a -100987654321 "新频道名称"
```

**输出：**
```
✓ 已添加频道: -100987654321
  频道名称: 新频道名称

💾 配置文件已更新: config.ini
```

#### 3. 删除频道

```bash
# 删除频道
python3 manage_channels.py --remove -1001234567890

# 简写
python3 manage_channels.py -r -1001234567890
```

**输出：**
```
✓ 已删除频道: -1001234567890

💾 配置文件已更新: config.ini
```

#### 4. 批量更新频道列表

```bash
# 替换整个频道列表（逗号分隔）
python3 manage_channels.py --update -1002040892468,-1001419575394,-100987654321

# 简写
python3 manage_channels.py -u -1002040892468,-1001419575394,-100987654321
```

**输出：**
```
✓ 频道列表已更新
  5 -> 3 个频道

💾 配置文件已更新: config.ini
```

#### 5. 指定配置文件

```bash
python3 manage_channels.py --config config.prod.ini --list
python3 manage_channels.py -c config.prod.ini -a -1001234567890 "频道"
```

---

## 方式三：Web 管理界面（可选）

### 🎯 概述

提供一个简单的 Web 界面来管理频道。

### 🛠️ 快速实现（基于现有 Rust HTTP 服务）

#### 1. 添加频道管理 API（可选）

因为 Rust 服务已经提供了 HTTP API，可以添加频道管理接口：

```bash
# 获取当前频道列表（需要 Rust 服务事先知道频道列表）
curl http://localhost:8080/api/v1/channels

# 添加频道
curl -X POST http://localhost:8080/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{"channel_id": -1001234567890, "channel_name": "新频道"}'

# 删除频道
curl -X DELETE http://localhost:8080/api/v1/channels/-1001234567890

# 更新整个列表
curl -X PUT http://localhost:8080/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{"channel_ids": [-1002040892468, -1001419575394, -100987654321]}'
```

#### 2. 创建简单的 Web 页面

```python
# manage.html
<!DOCTYPE html>
<html>
<head>
    <title>频道管理</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .channel-item { padding: 10px; margin: 5px 0; background: #f0f0f0; }
        button { padding: 8px 16px; margin: 5px; }
    </style>
</head>
<body>
    <h1>频道管理</h1>
    <button onclick="loadChannels()">刷新列表</button>
    <div id="channels"></div>

    <script>
        async function loadChannels() {
            const response = await fetch('/api/v1/channels');
            const data = await response.json();
            const container = document.getElementById('channels');
            container.innerHTML = data.data.map(ch =>
                `<div class="channel-item">
                    ${ch.channel_id} - <button onclick="removeChannel(${ch.channel_id})">删除</button>
                 </div>`
            ).join('');
        }

        async function removeChannel(id) {
            await fetch(`/api/v1/channels/${id}`, {method: 'DELETE'});
            loadChannels();
        }
    </script>
</body>
</html>
```

---

## 📊 三种方式对比

| 特性 | 方式一：热重载 | 方式二：管理工具 | 方式三：Web界面 |
|------|---------------|----------------|---------------|
| 实时生效 | ✅ 自动 | ✅ 立即 | ✅ 立即 |
| 操作难度 | ⭐⭐ 简单 | ⭐ 非常简单 | ⭐⭐⭐ 中等 |
| 需要额外依赖 | watchdog | 无 | Web框架 |
| 适合场景 | 自动化环境 | 命令行操作 | 图形化界面 |
| 远程管理 | ❌ 需要SSH | ❌ 需要SSH | ✅ 可通过浏览器 |

---

## 🎯 推荐方案

### 开发环境
**组合使用方式一和方式二：**
- 方式一：自动热重载，无需重启
- 方式二：快速增删频道

### 生产环境
**方式一 + 方式三：**
- 方式一：自动热重载
- 方式三：提供Web界面给运维人员

---

## 🔧 集成配置监听器的示例

### 修改 monitor.py

```python
#!/usr/bin/env python3
"""
Telegram 频道监控器 - 支持配置文件热重载
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.telegram_client import TelegramMonitor
from src.http_sender import HttpSender
from src.config_loader import load_config
from src.config_watcher import create_watcher
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")
logger.add("monitor.log", rotation="500 MB", retention="10 days", level="DEBUG")

# 全局变量
config = None
monitor = None
config_watcher = None


def reload_config():
    """配置文件重新加载回调"""
    global config, monitor

    logger.info("=" * 60)
    logger.info("配置文件变更检测")
    logger.info("=" * 60)

    try:
        # 加载新配置
        new_config = load_config('config.ini')

        # 获取新旧频道列表
        old_channels = set(monitor.channel_ids)
        new_channels = set(new_config['telegram']['channel_ids'])

        # 计算差异
        added = new_channels - old_channels
        removed = old_channels - new_channels

        if added:
            logger.info(f"新增频道: {len(added)} 个")
            for cid in added:
                logger.info(f"  + {cid}")

        if removed:
            logger.info(f"删除频道: {len(removed)} 个")
            for cid in removed:
                logger.info(f"  - {cid}")

        # 更新监控器频道列表
        monitor.set_channel_ids(list(new_channels))

        config = new_config
        logger.info("✓ 配置重新加载成功")
        logger.info("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        logger.info("当前配置保持不变\n")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Telegram 频道监控器启动中...")
    logger.info("=" * 60)

    # 加载配置
    config_file = "config.ini"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    logger.info(f"加载配置文件: {config_file}")

    try:
        config = load_config(config_file)
        logger.info("✓ 配置加载成功")
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)

    # 创建 HTTP 发送器
    http_sender = HttpSender(config['rust_service'])

    # 创建 Telegram 监控器
    global monitor
    monitor = TelegramMonitor(
        api_id=int(config['telegram']['api_id']),
        api_hash=config['telegram']['api_hash'],
        session_file=config['telegram']['session_file'],
        channel_ids=config['telegram']['channel_ids'],
        http_sender=http_sender
    )

    # 启动配置文件监听器
    global config_watcher
    config_watcher = create_watcher(config_file, reload_config)

    # 启动监控
    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("\n收到停止信号，正在退出...")
    finally:
        # 停止监听器
        if config_watcher:
            config_watcher.stop()

        logger.info("监控器已停止")


if __name__ == "__main__":
    main()
```

---

## 📝 完整工作流程示例

### 场景：添加新频道到监控列表

**方法 A - 使用管理工具（推荐）：**

```bash
# 1. 查看当前频道
python3 manage_channels.py -l

# 2. 添加新频道
python3 manage_channels.py -a -100987654321 "新监控频道"

# 3. 验证已添加
python3 manage_channels.py -l

# 监控器自动检测到配置变更并重新加载
# 无需重启程序！
```

**方法 B - 手动编辑配置：**

```bash
# 1. 编辑配置文件
vim config.ini
# 修改 channel_ids = ..., -100987654321

# 2. 保存文件
# 监控器自动检测到变更并重新加载
```

**方法 C - 通过 Web 界面：**

```bash
# 1. 打开浏览器
# 2. 访问 http://your-server:8080/manage.html
# 3. 点击"添加频道"按钮
# 4. 输入频道ID和名称
```

---

## 🔍 故障排查

### Q1: 修改配置文件后没有自动重载？

**A:**
1. 检查 monitor.py 是否集成了 ConfigWatcher
2. 查看日志是否有 "配置文件已更改" 的提示
3. 确保配置文件路径正确

### Q2: 使用管理工具提示 "配置文件不存在"？

**A:**
1. 确保在 python_monitor 目录下运行命令
2. 使用 `--config` 参数指定正确的配置文件路径
3. 检查配置文件权限

### Q3: 添加了频道但没有生效？

**A:**
1. 检查频道ID是否正确（必须以 -100 开头）
2. 确保 Bot 有访问该频道的权限
3. 查看日志是否有访问权限验证错误
4. 使用 `manage_channels.py -l` 确认已添加

### Q4: 如何获取频道 ID？

**A:**
```bash
# 1. 向 @userinfobot 发送频道消息
# 2. Bot 会返回频道信息，包含 channel_id
```

---

## 📈 监控器日志示例

### 正常启动日志

```
2025-11-20 10:30:15.123 | INFO | 加载配置文件: config.ini
2025-11-20 10:30:15.245 | INFO | ✓ 配置加载成功
2025-11-20 10:30:15.246 | INFO | 监控频道: 3 个
2025-11-20 10:30:15.247 | INFO | 启动配置文件监控: config.ini (每 5 秒检查一次)
2025-11-20 10:30:15.248 | INFO | ========================================
2025-11-20 10:30:20.123 | INFO | 步骤 1/4: 初始化连接...
2025-11-20 10:30:22.456 | INFO | ✓ 连接初始化成功
```

### 配置文件变更日志

```
2025-11-20 10:35:10.456 | INFO | ========================================
2025-11-20 10:35:10.457 | INFO | 配置文件变更检测
2025-11-20 10:35:10.458 | INFO | ========================================
2025-11-20 10:35:10.459 | INFO | 新增频道: 1 个
2025-11-20 10:35:10.460 | INFO |   + -100987654321
2025-11-20 10:35:10.461 | INFO | ✓ 配置重新加载成功
2025-11-20 10:35:10.462 | INFO | ========================================
```

---

## 🚀 下一步建议

1. **添加频道名称缓存**
   - 第一次验证频道时保存名称
   - 显示更友好的频道列表

2. **添加频道验证**
   - 添加频道时验证是否可以访问
   - 提供错误提示

3. **支持从链接添加**
   - 支持 `https://t.me/channelname` 格式
   - 自动解析为 channel_id

4. **添加频道分组/标签**
   - 按类型分组（DeFi, NFT, Meme等）
   - 支持按组启用/禁用

5. **频道推荐系统**
   - 基于现有频道推荐类似频道
   - 热门频道排行榜

---

## 📚 相关文件

### Python 监控器
- `python_monitor/config.ini` - 配置文件
- `python_monitor/monitor.py` - 主监控程序
- `python_monitor/src/telegram_client.py` - Telegram 客户端
- `python_monitor/src/config_watcher.py` - 配置监听器
- `python_monitor/manage_channels.py` - 频道管理工具

### Rust 服务端
- `src/http/channel_handler.rs` - 频道管理 API（已提供，可选）
- `config.toml` - Rust 服务配置

---

## ✨ 总结

我们提供了三种灵活的方式来管理监控频道：

1. **配置文件热重载** - 自动化，无需重启
2. **命令行管理工具** - 简单直接，适合运维
3. **Web 管理界面** - 图形化，适合远程管理

**推荐组合使用方式一和方式二**，既保证了实时性，又提供了便捷的管理手段！

---

**文档版本**: 1.0
**创建日期**: 2025-11-20
