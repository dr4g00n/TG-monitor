use crate::processor::MessageProcessor;
use axum::{
    extract::{State, Path, Json},
    http::{StatusCode, header},
    response::{IntoResponse, Response},
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{debug, info, warn};

/// 频道信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChannelInfo {
    pub channel_id: i64,
    pub channel_name: Option<String>,
    pub added_at: i64,
}

/// 频道管理请求
#[derive(Deserialize)]
pub struct AddChannelRequest {
    pub channel_id: i64,
    pub channel_name: Option<String>,
}

/// 更新频道列表请求
#[derive(Deserialize)]
pub struct UpdateChannelsRequest {
    pub channel_ids: Vec<i64>,
}

/// 频道管理响应
#[derive(Serialize)]
pub struct ChannelApiResponse<T> {
    pub success: bool,
    pub message: String,
    pub data: Option<T>,
}

impl<T> ChannelApiResponse<T> {
    pub fn success(data: T, message: impl Into<String>) -> Self {
        Self {
            success: true,
            message: message.into(),
            data: Some(data),
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

impl<T> IntoResponse for ChannelApiResponse<T>
where
    T: Serialize,
{
    fn into_response(self) -> Response {
        let status = if self.success {
            StatusCode::OK
        } else {
            StatusCode::BAD_REQUEST
        };

        // 设置包含 charset=utf-8 的 Content-Type 头
        let mut response = (status, Json(self)).into_response();
        response.headers_mut().insert(
            header::CONTENT_TYPE,
            header::HeaderValue::from_static("application/json; charset=utf-8")
        );
        response
    }
}

/// 获取所有监控频道
pub async fn get_channels(
    State(processor): State<Arc<MessageProcessor>>,
) -> impl IntoResponse {
    debug!("获取频道列表");

    match processor.get_channels().await {
        Ok(channels) => {
            info!("返回 {} 个频道", channels.len());
            ChannelApiResponse::success(channels, "获取频道列表成功")
        }
        Err(e) => {
            warn!("获取频道列表失败: {}", e);
            ChannelApiResponse::error(format!("获取频道列表失败: {}", e))
        }
    }
}

/// 添加单个频道
pub async fn add_channel(
    State(processor): State<Arc<MessageProcessor>>,
    Json(request): Json<AddChannelRequest>,
) -> impl IntoResponse {
    info!("添加频道: {}", request.channel_id);

    match processor.add_channel(request.channel_id, request.channel_name).await {
        Ok(_) => {
            info!("✓ 频道添加成功: {}", request.channel_id);
            ChannelApiResponse::success(
                request.channel_id,
                format!("频道添加成功: {}", request.channel_id),
            )
        }
        Err(e) => {
            warn!("✗ 频道添加失败 {}: {}", request.channel_id, e);
            ChannelApiResponse::error(format!("频道添加失败: {}", e))
        }
    }
}

/// 删除单个频道
pub async fn remove_channel(
    State(processor): State<Arc<MessageProcessor>>,
    Path(channel_id): Path<i64>,
) -> impl IntoResponse {
    info!("删除频道: {}", channel_id);

    match processor.remove_channel(channel_id).await {
        Ok(_) => {
            info!("✓ 频道删除成功: {}", channel_id);
            ChannelApiResponse::success(
                channel_id,
                format!("频道删除成功: {}", channel_id),
            )
        }
        Err(e) => {
            warn!("✗ 频道删除失败 {}: {}", channel_id, e);
            ChannelApiResponse::error(format!("频道删除失败: {}", e))
        }
    }
}

/// 更新频道列表（替换整个列表）
pub async fn update_channels(
    State(processor): State<Arc<MessageProcessor>>,
    Json(request): Json<UpdateChannelsRequest>,
) -> impl IntoResponse {
    info!("更新频道列表，共 {} 个频道", request.channel_ids.len());

    match processor.update_channels(request.channel_ids.clone()).await {
        Ok(_) => {
            info!("✓ 频道列表更新成功");
            ChannelApiResponse::success(
                request.channel_ids,
                "频道列表更新成功",
            )
        }
        Err(e) => {
            warn!("✗ 频道列表更新失败: {}", e);
            ChannelApiResponse::error(format!("频道列表更新失败: {}", e))
        }
    }
}

/// 检查频道是否在监控列表中
pub async fn check_channel(
    State(processor): State<Arc<MessageProcessor>>,
    Path(channel_id): Path<i64>,
) -> impl IntoResponse {
    debug!("检查频道是否在监控列表中: {}", channel_id);

    match processor.has_channel(channel_id).await {
        Ok(has_channel) => {
            if has_channel {
                ChannelApiResponse::success(
                    true,
                    format!("频道 {} 在监控列表中", channel_id),
                )
            } else {
                ChannelApiResponse::success(
                    false,
                    format!("频道 {} 不在监控列表中", channel_id),
                )
            }
        }
        Err(e) => {
            warn!("检查频道失败 {}: {}", channel_id, e);
            ChannelApiResponse::error(format!("检查频道失败: {}", e))
        }
    }
}
