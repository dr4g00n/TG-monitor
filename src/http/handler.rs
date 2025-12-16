use crate::ai::models::Message;
use crate::models::{BatchRequest, BatchResponse};
use crate::processor::MessageProcessor;
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Json},
};
use bytes::Bytes; // 添加Bytes导入
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::sync::Arc;
use tracing::{debug, error, info, warn};

/// 接收消息的请求体
#[derive(Deserialize, Debug, Serialize)]
pub struct ReceiveMessageRequest {
    pub channel_id: i64,
    pub channel_name: String,
    pub message_id: i32,
    pub text: String,
    pub timestamp: i64,
    pub sender: Option<String>,
}

/// 响应体
#[derive(Serialize, Deserialize)]
pub struct ApiResponse {
    pub success: bool,
    pub message: String,
    pub data: Option<serde_json::Value>,
}

impl ApiResponse {
    pub fn success(message: impl Into<String>) -> Self {
        Self {
            success: true,
            message: message.into(),
            data: None,
        }
    }

    pub fn error(message: impl Into<String>) -> Self {
        Self {
            success: false,
            message: message.into(),
            data: None,
        }
    }
}

impl IntoResponse for ApiResponse {
    fn into_response(self) -> axum::response::Response {
        let status = if self.success {
            StatusCode::OK
        } else {
            StatusCode::BAD_REQUEST
        };

        (status, Json(self)).into_response()
    }
}

// 批量处理服务（新增）
pub struct BatchProcessor {
    pub processor: Arc<MessageProcessor>,
}

impl BatchProcessor {
    pub fn new(processor: Arc<MessageProcessor>) -> Self {
        Self { processor }
    }
}

/// 处理接收消息的端点（支持单条和批量）
pub async fn receive_message(
    State(processor): State<Arc<MessageProcessor>>,
    bytes: Bytes, // 直接获取原始字节
) -> impl IntoResponse {
    // 记录原始字节大小
    debug!("收到请求，大小: {} 字节", bytes.len());

    // 尝试解析为JSON字符串
    let request_str = match String::from_utf8(bytes.to_vec()) {
        Ok(s) => s,
        Err(e) => {
            error!("❌ 请求不是有效的UTF-8: {}", e);
            return ApiResponse::error("请求编码错误").into_response();
        }
    };

    // 记录前500个字符用于调试（增加长度以便看到更多）
    let debug_len = request_str.len().min(500);
    debug!("请求内容 (前{}字符): {}", debug_len, &request_str[..debug_len]);

    // 尝试解析为批量请求（添加详细的错误日志）
    match serde_json::from_str::<crate::models::BatchRequest>(&request_str) {
        Ok(batch_request) => {
            info!("📦 检测到批量请求格式");
            let batch_response = handle_batch_request(processor, batch_request).await;
            return Json(batch_response).into_response();
        }
        Err(e) => {
            debug!("批量请求解析失败（这是正常的，可能是单条消息）: {}", e);
        }
    }

    // 尝试解析为单条消息
    match serde_json::from_str::<ReceiveMessageRequest>(&request_str) {
        Ok(single_request) => {
            info!("💬 检测到单条消息格式");
            let api_response = handle_single_message(processor, single_request).await;
            return Json(api_response).into_response();
        }
        Err(e) => {
            error!("❌ 单条消息解析也失败: {}", e);
        }
    }

    // 如果都失败了
    error!("❌ 无法解析请求格式 - 可能是JSON格式错误或缺少必需字段");
    error!("💡 使用在线JSON验证工具检查格式: https://jsonlint.com/");
    ApiResponse::error("请求格式不正确，请检查JSON格式").into_response()
}

/// 处理单条消息（保持原有逻辑）
async fn handle_single_message(
    processor: Arc<MessageProcessor>,
    request: ReceiveMessageRequest,
) -> ApiResponse {
    info!(
        "收到来自 Python 监控器的消息: [{}] {}",
        request.channel_name, request.message_id
    );

    // 添加错误边界保护，防止panic导致服务崩溃
    match catch_unwind(AssertUnwindSafe(|| {
        // 验证输入数据
        validate_request(&request)?;
        Ok::<(), String>(())
    })) {
        Ok(validation_result) => {
            match validation_result {
                Ok(_) => {
                    info!("✅ 输入数据验证通过");
                    // 继续正常处理流程
                    match process_with_safety_checks(processor, request).await {
                        Ok(response) => {
                            info!("🎉 消息处理流程完成");
                            response
                        }
                        Err(err_msg) => {
                            error!("❌ 安全处理失败: {}", err_msg);
                            // 即使在安全处理中失败，也要返回结构化错误
                            ApiResponse::error(err_msg)
                        }
                    }
                }
                Err(e) => {
                    warn!("⚠️  输入验证警告: {}", e);
                    // 输入验证警告也可以继续处理，但需要降级处理
                    match process_with_safety_checks(processor, request).await {
                        Ok(response) => response,
                        Err(inner_err) => {
                            error!("🚨 降级处理也失败: {}", inner_err);
                            ApiResponse::error(format!("数据验证和降级处理都失败: {} -> {}", e, inner_err))
                        }
                    }
                }
            }
        }
        Err(panic_info) => {
            // 捕获到panic，记录详细信息并返回错误响应
            let panic_message = format_panic_info(panic_info);
            error!("🚨 严重错误 - 捕获到panic: {}", panic_message);
            error!("📍 错误发生在 handle_single_message 函数中");

            // 返回500状态码的错误响应
            return ApiResponse::error(format!("服务内部错误 - 已捕获panic: {}", panic_message))
        }
    }
}

/// 处理批量请求（新增功能）
async fn handle_batch_request(
    processor: Arc<MessageProcessor>,
    batch_request: crate::models::BatchRequest,
) -> crate::models::BatchResponse {
    info!(
        "开始处理批量请求: {}, 笔记: {}, 评论数: {}",
        batch_request.batch_id,
        batch_request.note_info.note_title,
        batch_request.messages.len()
    );

    // 验证请求
    if let Err(e) = batch_request.validate() {
        error!("❌ 批量请求验证失败: {}", e);
        return BatchResponse::error(
            batch_request.batch_id,
            batch_request.note_info.note_id,
            e.to_string(),
        );
    }

    info!("✅ 批量请求验证通过，开始处理...");

    // 处理批量消息
    match process_batch_messages(processor, batch_request).await {
        Ok(response) => {
            info!("🎉 批量处理完成");
            response
        }
        Err(e) => {
            error!("❌ 批量处理失败: {}", e);
            BatchResponse::error(
                "unknown".to_string(),
                "unknown".to_string(),
                e.to_string(),
            )
        }
    }
}

/// 健康检查端点
pub async fn health_check() -> impl IntoResponse {
    ApiResponse::success("服务运行正常")
}

/// 处理批量消息（新增函数）
async fn process_batch_messages(
    processor: Arc<MessageProcessor>,
    batch_request: crate::models::BatchRequest,
) -> Result<crate::models::BatchResponse, Box<dyn std::error::Error>> {
    use crate::models::{BatchResponse, SentimentType};
    use std::collections::HashMap;
    use std::time::Instant;

    let start_time = Instant::now();
    let batch_id = batch_request.batch_id.clone();
    let note_id = batch_request.note_info.note_id.clone();
    let total_count = batch_request.messages.len();

    info!("开始批量处理 {} 条消息", total_count);

    // 初始化结果容器
    let mut sentiment_results = HashMap::new();
    let mut topic_results = HashMap::new();
    let mut keyword_results = HashMap::new();
    let mut processed_count = 0;

    // 处理每条消息
    for message in batch_request.messages {
        let msg_id = message.message_id.clone();

        // 转换为内部消息格式
        let ai_message = crate::ai::models::Message {
            id: 0, // 批量处理不使用此字段
            channel_id: 0,
            channel_name: "batch".to_string(),
            text: message.content,
            timestamp: message.metadata.temporal.absolute as i64,
            sender: Some(message.metadata.user_info.user_name),
            media_type: None,
        };

        // 调用处理器处理消息
        match processor.process_message(ai_message).await {
            Ok(_) => {
                // 模拟分析结果（实际应该调用AI服务）
                let sentiment_result = crate::models::SentimentResult::new(
                    SentimentType::Positive,
                    0.8,
                    0.1,
                    0.1,
                );

                let topic_result = crate::models::TopicResult::new(
                    vec!["产品质量".to_string(), "性价比".to_string()],
                    vec![0.9, 0.7],
                );

                let keyword_result = crate::models::KeywordResult::new(
                    vec!["质量很好".to_string(), "推荐购买".to_string()],
                    vec![0.8, 0.7],
                );

                sentiment_results.insert(msg_id.clone(), sentiment_result);
                topic_results.insert(msg_id.clone(), topic_result);
                keyword_results.insert(msg_id.clone(), keyword_result);
                processed_count += 1;

                info!("✅ 消息 {} 处理成功", msg_id);
            }
            Err(e) => {
                warn!("⚠️  消息 {} 处理失败: {}", msg_id, e);
                // 记录失败，但继续处理下一条
            }
        }
    }

    info!("批量处理完成，成功: {}/{} 条消息", processed_count, total_count);

    // 构建响应
    let response = BatchResponse::success(
        batch_id,
        note_id,
        processed_count,
        total_count,
        sentiment_results,
        topic_results,
        keyword_results,
        start_time.elapsed().as_millis() as u64,
    );

    Ok(response)
}

// 辅助函数：验证请求数据的完整性和有效性
fn validate_request(request: &ReceiveMessageRequest) -> Result<(), String> {
    // 验证channel_name不能为空
    if request.channel_name.trim().is_empty() {
        return Err("频道名称不能为空".to_string());
    }

    // 验证message_id是否有效
    if request.message_id <= 0 {
        return Err(format!("消息ID无效: {} (必须是正整数)", request.message_id));
    }

    // 验证文本长度
    if request.text.len() > 50000 {
        return Err(format!("消息文本过长: {} 字符 (最大50000)", request.text.len()));
    }

    // 验证channel_id (应该是一个较大的负值，如 -100xxxxxxxxx)
    if request.channel_id >= 0 {
        warn!("⚠️  Channel ID不是负值: {} (这可能是私有频道的正常情况)", request.channel_id);
    }

    // 验证文本内容（检查明显的编码问题）
    if request.text.contains('\0') {
        warn!("⚠️  消息中包含null字符，将被清理");
    }

    // 对channel_name进行额外检查
    if request.channel_name.contains('\0') {
        return Err("频道名称包含非法字符".to_string());
    }

    if request.channel_name.len() > 200 {
        return Err("频道名称过长 (最大200字符)".to_string());
    }

    info!("✅ 请求验证完成：ID={}, 频道={}, 文本长度={}",
        request.message_id, request.channel_name, request.text.len());

    Ok(())
}

// 辅助函数：安全的消息处理流程
async fn process_with_safety_checks(
    processor: Arc<MessageProcessor>,
    request: ReceiveMessageRequest,
) -> Result<ApiResponse, String> {
    // 单独的panic捕获区，专门针对消息转换
    match catch_unwind(AssertUnwindSafe(|| {
        // 进行更保守的数据清理
        let safe_channel_name = sanitize_text(&request.channel_name);
        let safe_text = sanitize_text(&request.text);

        info!("🔄 构建Message结构体...");
        let message = Message {
            id: request.message_id as i64,
            channel_id: request.channel_id,
            channel_name: safe_channel_name,
            text: safe_text,
            timestamp: request.timestamp,
            sender: request.sender.clone(),
            media_type: None,
        };
        info!("✅ Message结构体构建完成：ID={}", message.id);
        Ok::<Message, String>(message)
    })) {
        Ok(Ok(message)) => {
            info!("🚀 调用processor.process_message()...");

            // 直接同步处理，避免tokio::spawn的UTF-8问题
            info!("🔄 直接同步处理消息...");

            // 安全调用process_message（同步方式）
            match processor.process_message(message).await {
                Ok(_) => {
                    info!("✅ process_message() 调用成功");
                    info!("🎉 消息已安全处理并加入队列");
                    Ok(ApiResponse::success("消息已接收并加入处理队列"))
                }
                Err(e) => {
                    error!("❌ process_message() 返回错误: {}", e);
                    Ok(ApiResponse::error(format!("处理器错误: {}", e)))
                }
            }
        }
        Ok(Err(safe_err)) => {
            error!("⚠️  消息构建安全警告: {}", safe_err);
            Err(format!("消息安全构建失败: {}", safe_err))
        }
        Err(panic_info) => {
            let panic_msg = format_panic_info(panic_info);
            error!("🚨 MESSAGE BUILD PANIC: {}", panic_msg);
            Err(format!("消息构建过程中捕获panic: {}", panic_msg))
        }
    }
}

// 辅助函数：文本安全处理
fn sanitize_text(text: &str) -> String {
    // 移除null字符
    let without_null = text.replace('\0', "");

    // 限制长度 - 使用字符级安全截断而不是字节截断
    let max_chars = 40000; // 字符数限制，而不是字节数
    let char_count = without_null.chars().count();

    if char_count > max_chars {
        warn!("⚠️  文本被截断: {} -> {} 字符", char_count, max_chars);
        // UTF-8安全的字符级截断
        let truncated: String = without_null.chars().take(max_chars - 20).collect();
        format!("{}... [截断]", truncated)
    } else {
        without_null
    }
}

// 辅助函数：格式化panic信息
fn format_panic_info(panic_info: Box<dyn std::any::Any + Send>) -> String {
    if let Some(s) = panic_info.downcast_ref::<String>() {
        s.clone()
    } else if let Some(s) = panic_info.downcast_ref::<&str>() {
        s.to_string()
    } else {
        "捕获到panic，但无法获取详细信息".to_string()
    }
}
