# Telegram 登录指南

## 步骤 1: 进入项目目录
```bash
cd /Users/dr4/WorkSpace/git/Rust-testCode/TG-monitor/python_monitor
```

## 步骤 2: 激活虚拟环境
```bash
source venv/bin/activate
```

## 步骤 3: 运行监控器（交互式）
```bash
python3 monitor.py config.ini
```

## 步骤 4: 输入 Telegram 认证信息

程序会提示：
```
Enter phone number or bot token:
```

输入您的手机号（必须使用国际格式）：
```
+86138xxxxxxxx
```

然后您会收到 Telegram 发送的验证码，程序会提示：
```
Enter verification code:
```

输入验证码（6位数字）。

如果您启用了两步验证，还会提示：
```
Enter password:
```

输入您的两步验证密码。

## 步骤 5: 验证登录成功

如果登录成功，您会看到：
```
✓ 登录成功！
开始监控频道消息...
按 Ctrl+C 停止
```

同时会话文件会被创建/更新：
- `my_monitor.session.session`（自动保存登录状态）

## 步骤 6: 测试系统

1. 在监控的频道发送一条测试消息
2. 查看日志确认接收：
```bash
tail -f monitor.log
```

应该看到类似输出：
```
收到新消息: [频道名称] 12345
✓ 消息发送成功: 频道名称 - 12345
```

3. 检查 Rust 服务日志，确认 AI 分析和转发

## 故障排除

### 问题 1: 仍然连接超时
- 检查代理是否运行正常：`curl -x http://127.0.0.1:7890 https://api.telegram.org`
- 检查代理配置是否正确：Pyrogram 已配置使用代理 `127.0.0.1:7890`

### 问题 2: API ID/Hash 错误
- 确认 `config.ini` 中的 api_id 和 api_hash 正确
- 访问 https://my.telegram.org 重新获取

### 问题 3: 验证码收不到
- 确认手机号格式正确（+86开头）
- 检查 Telegram 账号是否能正常接收消息
- 尝试重新运行程序

### 问题 4: 两步验证密码错误
- 确认输入的密码正确
- 如果忘记密码，需要在 Telegram 设置中重置

## 后台运行（登录后）

登录成功后，可以使用以下命令后台运行：

```bash
nohup python3 monitor.py config.ini > monitor_output.log 2>&1 &
```

查看运行状态：
```bash
tail -f monitor.log
tail -f monitor_output.log
```

停止运行：
```bash
pkill -f "python3 monitor.py"
```

## 系统验证清单

登录成功后，确认以下都正常：

- [ ] Rust 服务运行中（端口 8080）
- [ ] Python 监控器运行中
- [ ] Telegram 登录成功
- [ ] 测试消息能正常接收
- [ ] Rust 服务能接收 HTTP 请求
- [ ] AI 分析正常工作
- [ ] 最终结果能转发到目标用户

## 需要帮助？

检查日志文件：
```bash
tail -n 50 monitor.log
```

查看 Rust 服务状态：
```bash
curl http://localhost:8080/health
```

查看进程：
```bash
ps aux | grep -E "tg-meme-token-monitor|monitor\.py"
```
