# 访问日志记录功能说明

## ✅ 功能概述

已成功添加访问日志记录功能，用于记录所有客户端请求信息。

---

## 📄 日志记录内容

每条访问记录包含以下信息：

### 请求开始
```
request{method=GET uri=/health version=HTTP/1.1}: tower_http::trace::on_request: started processing request
```

### 响应完成
```
request{method=GET uri=/health version=HTTP/1.1}: tower_http::trace::on_response: finished processing request latency=0 ms status=200
```

### 日志字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `method` | HTTP方法 | GET, POST, PUT, DELETE |
| `uri` | 请求路径 | /health, /api/v1/message |
| `version` | HTTP版本 | HTTP/1.1 |
| `latency` | 处理延迟 | 0 ms, 123 ms |
| `status` | 响应状态码 | 200, 400, 404, 500 |

---

## 🔍 实时查看访问日志

### 方法1: tail -f 实时监控

```bash
# 查看实时访问日志
tail -f service_with_trace.log

# 只显示访问日志（过滤tower_http）
tail -f service_with_trace.log | grep tower_http

# 显示请求和响应摘要
tail -f service_with_trace.log | grep -E "(on_request|on_response)"
```

### 方法2: 使用 grep 过滤特定请求

```bash
# 查看所有对健康检查端点的访问
tail -f service_with_trace.log | grep "uri=/health"

# 查看所有消息接收请求
tail -f service_with_trace.log | grep "uri=/api/v1/message"

# 查看所有404错误
tail -f service_with_trace.log | grep "status=404"

# 查看所有503错误
tail -f service_with_trace.log | grep "status=503"

# 查看响应时间超过100ms的请求
tail -f service_with_trace.log | grep "latency=[1-9]"
```

### 方法3: awk 格式化输出

```bash
# 格式化显示访问日志
tail -f service_with_trace.log | grep tower_http | awk '
/on_request/ {
    split($0, a, "method=")
    split(a[2], b, " ");
    method = b[1]

    split($0, a, "uri=")
    split(a[2], b, " ");
    uri = b[1]

    printf "[→] %-6s %s\n", method, uri
}
/on_response/ {
    split($0, a, "status=")
    split(a[2], b, " ");
    status = b[1]

    split($0, a, "latency=")
    split(a[2], b, " ");
    latency = b[1]

    printf "[←] %s %s\n\n", status, latency
}
'
```

---

## 📊 访问日志分析示例

### 示例1: 健康检查访问

```
[2025-12-16T06:34:54.482343Z] DEBUG request{method=GET uri=/health version=HTTP/1.1} tower_http::trace::on_request: started processing request
[2025-12-16T06:34:54.482392Z] DEBUG request{method=GET uri=/health version=HTTP/1.1} tower_http::trace::on_response: finished processing request latency=0 ms status=200
```

**分析**: 健康检查端点，响应时间0ms，状态码200

### 示例2: 消息接收（成功）

```
[2025-12-16T06:34:54.482865Z] DEBUG request{method=POST uri=/api/v1/message version=HTTP/1.1} tower_http::trace::on_request: started processing request
[2025-12-16T06:34:54.482998Z] DEBUG request{method=POST uri=/api/v1/message version=HTTP/1.1} tower_http::trace::on_response: finished processing request latency=0 ms status=200
```

**分析**: 消息接收请求，响应时间0ms，状态码200

### 示例3: 404 错误

```
[2025-12-16T06:34:54.482865Z] DEBUG request{method=POST uri=/api/v1/messages version=HTTP/1.1} tower_http::trace::on_request: started processing request
[2025-12-16T06:34:54.482998Z] DEBUG request{method=POST uri=/api/v1/messages version=HTTP/1.1} tower_http::trace::on_response: finished processing request latency=0 ms status=404
```

**分析**: 客户端使用了错误的端点（复数形式），导致404错误

### 示例4: 批量消息接收

```
[2025-12-16T06:34:54.482865Z] DEBUG request{method=POST uri=/api/v1/message version=HTTP/1.1} tower_http::trace::on_request: started processing request
# ... 批量处理日志 ...
[2025-12-16T06:34:56.123456Z] DEBUG request{method=POST uri=/api/v1/message version=HTTP/1.1} tower_http::trace::on_response: finished processing request latency=2345 ms status=200
```

**分析**: 批量消息处理耗时2345ms，处理多条评论

---

## 🔧 自定义访问日志

如果需要更详细的访问日志（如客户端IP、User-Agent），可以自定义TraceLayer配置：

在 `src/http/server.rs` 中：

```rust
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::Level;

.layer(
    TraceLayer::new_for_http()
        .make_span_with(|request: &http::Request<_>| {
            tracing::info_span!(
                "http_request",
                method = %request.method(),
                uri = %request.uri().path(),
                version = ?request.version(),
                // 可以添加更多字段
            )
        })
        .on_request(|request: &http::Request<_>, _span: &tracing::Span| {
            tracing::info!(
                "📥 收到请求: {} {} from {:?}",
                request.method(),
                request.uri().path(),
                request.headers().get("user-agent").and_then(|h| h.to_str().ok())
            );
        })
        .on_response(|response: &http::Response<_>, latency, _span: &tracing::Span| {
            tracing::info!(
                "📤 响应完成: status={} latency={:?}",
                response.status(),
                latency
            );
        })
)
```

**注意**: 当前使用的是默认的TraceLayer配置，已经能够记录请求的基本信息。

---

## 📈 性能监控

### 统计平均响应时间

```bash
# 统计所有请求的平均延迟
grep "latency=" service_with_trace.log | \
  grep -oP 'latency=\K\d+' | \
  awk '{sum+=$1; count++} END {print "平均延迟: " sum/count " ms"}'
```

### 统计状态码分布

```bash
# 统计各种状态码的数量
grep "status=" service_with_trace.log | \
  grep -oP 'status=\K\d+' | \
  sort | uniq -c | \
  sort -nr
```

### 监控错误率

```bash
# 实时监控错误率
while true; do
    total=$(grep -c "on_response" service_with_trace.log)
    errors=$(grep -c "status=[45][0-9][0-9]" service_with_trace.log)
    error_rate=$((errors * 100 / total))
    echo "$(date) - 总请求: $total, 错误数: $errors, 错误率: ${error_rate}%"
    sleep 10
done
```

---

## 🚨 故障排查

### 情景1: 客户端收到503错误

**查看日志**:
```bash
tail -n 100 service_with_trace.log | grep "status=503"
```

**可能原因**:
1. 代理配置问题
2. 服务未启动
3. 端口被占用

### 情景2: 客户端收到404错误

**查看日志**:
```bash
tail -n 100 service_with_trace.log | grep "status=404"
```

**可能原因**:
1. 客户端使用了错误的端点（如 `/api/v1/messages` 而不是 `/api/v1/message`）
2. 请求路径拼写错误

### 情景3: 响应时间异常

**查看日志**:
```bash
# 查看响应时间超过1秒的请求
tail -n 100 service_with_trace.log | grep "latency=[1-9][0-9][0-9][0-9]\|latency=[0-9]\{2,3\}\."
```

**可能原因**:
1. AI服务响应慢
2. 批量消息处理量大
3. 网络延迟

---

## 💾 日志文件位置

### 当前日志文件
- **服务日志**: `service_with_trace.log`
- **包含访问日志**: 是
- **日志级别**: info + tower_http debug

### 配置说明

在 `src/main.rs` 中配置了日志级别：
```rust
tracing_subscriber::EnvFilter::try_from_default_env()
    .unwrap_or_else(|_| "info,tower_http=debug,tg_meme_token_monitor=debug".into())
```

**环境变量控制**:
```bash
# 运行时设置日志级别
RUST_LOG="info,tower_http=debug" ./target/release/tg-meme-token-monitor
```

---

## 🎯 快速开始

### 1. 启动服务

```bash
./target/release/tg-meme-token-monitor > service_with_trace.log 2>&1 &
```

### 2. 监控访问日志

```bash
# 实时监控
tail -f service_with_trace.log | grep tower_http

# 监控特定端点
tail -f service_with_trace.log | grep "uri=/api/v1/message"
```

### 3. 测试访问

```python
import requests

# 禁用代理
session = requests.Session()
session.trust_env = False

# 发送测试请求
response = session.get("http://localhost:8080/health")
response = session.post("http://localhost:8080/api/v1/message", json={...})
```

---

## 📊 日志示例解析

### 完整的访问日志示例

```
[2025-12-16T06:34:54.482343Z] DEBUG request{method=GET uri=/health version=HTTP/1.1}: tower_http::trace::on_request: started processing request
[2025-12-16T06:34:54.482343Z]  INFO request{method=GET uri=/health version=HTTP/1.1}: tg_meme_token_monitor::http::handler: ✅ 输入数据验证通过
[2025-12-16T06:34:54.482343Z]  INFO request{method=GET uri=/health version=HTTP/1.1}: tg_meme_token_monitor::http::handler: ✅ 消息已安全处理并加入队列
[2025-12-16T06:34:54.482392Z] DEBUG request{method=GET uri=/health version=HTTP/1.1}: tower_http::trace::on_response: finished processing request latency=0 ms status=200
```

**时间线**:
1. 0ms - 收到请求（tower_http）
2. 0ms - 验证通过（应用逻辑）
3. 0ms - 处理完成（应用逻辑）
4. 0ms - 响应发送（tower_http）

---

## ✅ 功能总结

| 功能 | 状态 | 说明 |
|------|------|------|
| 请求日志记录 | ✅ 已启用 | tower_http::trace |
| 响应日志记录 | ✅ 已启用 | 包含状态码和延迟 |
| 实时查看 | ✅ 支持 | tail -f + grep |
| 日志持久化 | ✅ 支持 | 写入文件 |
| 错误跟踪 | ✅ 支持 | 可过滤状态码 |
| 性能监控 | ✅ 支持 | 延迟统计 |

---

## 📝 总结

访问日志已经集成到服务中，可以通过以下方式查看：

1. **实时监控**: `tail -f service_with_trace.log | grep tower_http`
2. **查看历史**: `grep tower_http service_with_trace.log`
3. **过滤端点**: `grep "uri=/api/v1/message" service_with_trace.log`
4. **查看错误**: `grep "status=404" service_with_trace.log`

所有客户端访问都会被记录，包括请求方法、URI、HTTP版本、响应状态码和处理延迟。
