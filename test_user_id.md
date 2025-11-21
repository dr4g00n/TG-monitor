# Telegram Bot 转发测试报告

## ❌ 发现的问题

**错误信息**: `Bad Request: chat not found`

**原因分析**:
1. 用户ID `8030185949` 可能不正确
2. 机器人需要先与用户建立对话（用户需要先给机器人发送消息）
3. 用户ID格式可能错误（应该是聊天ID，而不一定是用户ID）

## ✅ 解决方案

### 方法1：获取正确的用户ID

1. **让用户先给你的机器人发送任意消息**
   - 在Telegram中搜索你的机器人（用户名）
   - 发送任意消息，比如 "/start"

2. **使用API获取更新**：
   ```bash
   curl -s "https://api.telegram.org/bot8251881402:AAEzi7YFZJOr6FA5h9bF_dJUy0SkU_SbWU0/getUpdates"
   ```

3. **从响应中提取正确的chat_id**。

### 方法2：使用 @userinfobot

1. 在Telegram中搜索 `@userinfobot`
2. 发送任意消息
3. 机器人会返回你的正确用户ID

### 方法3：测试向自己发送消息

先用你自己的Telegram账户测试：

1. 给你的机器人发送消息
2. 运行测试获取你的正确ID
3. 确认能收到消息后，再设置为目标用户

## 🔧 修改建议

1. **先停止当前服务**：
   ```bash
   pkill -f tg-meme-token-monitor
   ```

2. **获取正确的用户ID后，更新config.toml**：
   ```toml
   target_user = 正确的用户ID
   ```

3. **重新启动服务**

## 📋 测试流程

建议按照以下步骤测试：

1. ✅ Bot Token 验证通过
2. ❌ 用户ID验证失败
3. 🔄 需要获取正确的用户ID
4. 📱 用户给机器人发送消息
5. 🔍 提取正确的chat_id
6. ✅ 重新测试转发功能

需要我帮你获取正确的用户ID吗？