use crate::ai::AIService;
use crate::config::Config;
use crate::ai::models::{Message, AnalysisResult, TokenInfo, SummaryReport};
use crate::http::channel_handler::ChannelInfo;
use crate::telegram::bot::TelegramBot;
use crate::unicode_safe::{create_safe_summary, safe_log_message, normalize_for_logging};
use anyhow::Result;
use std::collections::{HashMap, VecDeque};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{interval, Duration};
use tracing::{debug, error, info};

/// 消息处理器
pub struct MessageProcessor {
    config: Config,
    ai_service: Arc<dyn AIService>,
    telegram_bot: Arc<TelegramBot>,
    message_queue: Arc<Mutex<VecDeque<Message>>>,
    analysis_results: Arc<Mutex<Vec<AnalysisResult>>>,
    is_running: Arc<Mutex<bool>>,
    /// 监控频道列表
    monitored_channels: Arc<Mutex<Vec<ChannelInfo>>>,
}

impl MessageProcessor {
    /// 创建新的消息处理器
    pub fn new(config: Config, ai_service: Arc<dyn AIService>, telegram_bot: Arc<TelegramBot>) -> Self {
        Self {
            config,
            ai_service,
            telegram_bot,
            message_queue: Arc::new(Mutex::new(VecDeque::new())),
            analysis_results: Arc::new(Mutex::new(Vec::new())),
            is_running: Arc::new(Mutex::new(false)),
            monitored_channels: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// 启动处理器（后台任务）
    pub async fn start(&self) -> Result<()> {
        *self.is_running.lock().await = true;

        info!("启动消息处理器...");

        // 启动两个后台任务：
        // 1. 消息处理任务 - 持续处理队列中的消息
        // 2. 定时报告任务 - 定期发送汇总报告

        let processor = self.clone();
        tokio::spawn(async move {
            if let Err(e) = processor.processing_loop().await {
                error!("消息处理循环出错: {}", e);
            }
        });

        let reporter = self.clone();
        tokio::spawn(async move {
            if let Err(e) = reporter.reporting_loop().await {
                error!("报告发送循环出错: {}", e);
            }
        });

        info!("✓ 消息处理器已启动");
        Ok(())
    }

    /// 停止处理器
    pub async fn stop(&self) {
        *self.is_running.lock().await = false;
        info!("消息处理器已停止");
    }

    /// 是否正在运行
    pub async fn is_running(&self) -> bool {
        *self.is_running.lock().await
    }

    /// 处理消息（从 Telegram 接收）
    pub async fn process_message(&self, message: Message) -> Result<()> {
        // 使用Unicode安全的日志记录
        let safe_summary = create_safe_summary(&message.text);
        info!("🎯 MESSAGE PROCESSOR: process_message() 被调用！消息: [{}] {} - {}",
            message.channel_name, message.id, safe_summary);

        // 预处理：检查关键词
        info!("🔍 检查消息是否需要过滤...");
        if self.should_filter(&message).await {
            info!("⚠️  消息被过滤（不包含关键词）: {}", message.id);
            return Ok(());
        }

        info!("✅ 消息通过关键词过滤");

        // 将消息加入队列
        info!("📥 将消息加入处理队列...");
        self.message_queue.lock().await.push_back(message);
        info!("✓ 消息已加入处理队列");

        // 如果队列达到批量大
        let queue_size = self.message_queue.lock().await.len();
        info!("📊 当前队列大小: {}", queue_size);
        if queue_size >= self.config.processing.batch_size {
            info!("🚀 队列达到批量大小 ({}), 触发处理", queue_size);
            self.process_queue().await?;
        } else {
            info!("⏳ 队列未达到批量大小，等待更多消息");
        }

        Ok(())
    }

    /// 消息处理循环
    async fn processing_loop(&self) -> Result<()> {
        info!("启动消息处理循环");

        let mut check_interval = interval(Duration::from_secs(5));

        loop {
            tokio::select! {
                _ = check_interval.tick() => {
                    if !*self.is_running.lock().await {
                        break;
                    }

                    let queue_size = self.message_queue.lock().await.len();
                    if queue_size > 0 {
                        debug!("处理队列中的 {} 条消息", queue_size);
                        if let Err(e) = self.process_queue().await {
                            error!("处理队列失败: {}", e);
                        }
                    }
                }
            }
        }

        info!("消息处理循环已退出");
        Ok(())
    }

    /// 定时报告循环
    async fn reporting_loop(&self) -> Result<()> {
        info!("启动定时报告循环");

        let report_interval = Duration::from_secs(self.config.processing.batch_timeout_seconds);
        let mut interval_timer = interval(report_interval);

        loop {
            tokio::select! {
                _ = interval_timer.tick() => {
                    if !*self.is_running.lock().await {
                        break;
                    }

                    debug!("定时触发报告发送");
                    if let Err(e) = self.send_summary_report().await {
                        error!("发送报告失败: {}", e);
                    }
                }
            }
        }

        info!("报告循环已退出");
        Ok(())
    }

    /// 处理队列中的所有消息
    pub async fn process_queue(&self) -> Result<()> {
        let messages: Vec<Message> = {
            let mut queue = self.message_queue.lock().await;
            queue.drain(..).collect()
        };

        if messages.is_empty() {
            return Ok(());
        }

        info!("开始批量处理 {} 条消息", messages.len());

        let mut results = Vec::new();
        for message in messages {
            match self.analyze_message(&message).await {
                Ok(analysis_result) => {
                    if analysis_result.is_relevant {
                        info!("发现相关消息:");
                        // 使用Unicode安全的日志记录，避免tracing内部UTF-8问题
                        let safe_summary = crate::unicode_safe::safe_log_message(&analysis_result.format_summary(), "analysis_summary");
                        info!("{}", safe_summary);
                        results.push(analysis_result);
                    } else {
                        debug!("消息不是相关内容");
                    }
                }
                Err(e) => {
                    error!("分析消息失败: {}", e);
                }
            }
        }

        // 将结果保存
        if !results.is_empty() {
            self.analysis_results.lock().await.extend(results);
        }

        Ok(())
    }

    /// 分析单条消息
    async fn analyze_message(&self, message: &Message) -> Result<AnalysisResult> {
        debug!("开始 AI 分析消息 {}...", message.id);

        let start_time = std::time::Instant::now();
        let result = self.ai_service.analyze(&message.text).await
            .map_err(|e| anyhow::anyhow!("AI 分析失败: {}", e))?;

        let elapsed = start_time.elapsed();
        debug!("AI 分析完成，耗时: {:?}", elapsed);

        Ok(result)
    }

    /// 发送汇总报告
    async fn send_summary_report(&self) -> Result<()> {
        let results: Vec<AnalysisResult> = {
            let mut stored_results = self.analysis_results.lock().await;
            if stored_results.is_empty() {
                return Ok(());
            }
            stored_results.drain(..).collect()
        };

        if results.is_empty() {
            return Ok(());
        }

        info!("生成汇总报告，包含 {} 条分析结果", results.len());

        // 按 Token 名称分组
        let mut token_groups: HashMap<String, Vec<AnalysisResult>> = HashMap::new();
        for result in results {
            if let Some(token_name) = &result.token_name {
                token_groups.entry(token_name.clone())
                    .or_insert_with(Vec::new)
                    .push(result);
            }
        }

        // 构建 Token 信息列表
        let mut tokens = Vec::new();
        for (_, group) in token_groups {
            if let Some(token_info) = TokenInfo::from_analysis(&group) {
                tokens.push(token_info);
            }
        }

        // 按提及次数排序
        tokens.sort_by(|a, b| b.mentions.cmp(&a.mentions));

        // 创建报告
        let report = SummaryReport {
            tokens,
            generated_at: chrono::Utc::now().timestamp(),
            total_messages: 0,  // TODO: 需要正确统计
            relevant_messages: 0,  // TODO: 需要正确统计
        };

        // 格式化并发送报告
        if !report.is_empty() {
            self.send_report(&report).await?;
        }

        Ok(())
    }

    /// 发送报告（输出详细日志并转发到Telegram）
    async fn send_report(&self, report: &SummaryReport) -> Result<()> {
        info!("========== AI 评估报告 ==========");

        // 获取详细报告内容
        let report_content = report.format_full_report();

        // 按行输出，确保日志中能完整显示
        for line in report_content.lines() {
            if !line.trim().is_empty() {
                info!("{}", line);
            }
        }

        info!("===============================");
        info!("✓ AI 评估报告已生成，共包含 {} 个 token 分析", report.tokens.len());

        // 如果有具体的 token 分析，额外输出详细信息
        if !report.tokens.is_empty() {
            info!("📊 详细分析:");
            for (i, token) in report.tokens.iter().enumerate() {
                info!("  {}. Token: {} | 提及次数: {} | 推荐: {}",
                    i + 1,
                    token.name,
                    token.mentions,
                    token.recommendation
                );
                if let Some(contract) = &token.contract_address {
                    info!("     合约地址: {}", contract);
                }
                info!("     平均置信度: {:.1}%", token.avg_confidence * 100.0);
                info!("     来源频道: {}", token.sources.join(", "));
            }
        }

        // 转发报告到 Telegram 目标用户
        if !report_content.is_empty() {
            info!("正在转发报告到 Telegram 用户 {}...", self.config.telegram.target_user);
            match self.telegram_bot.send_message(&report_content).await {
                Ok(_) => info!("✓ 报告已成功转发到 Telegram 用户 {}", self.config.telegram.target_user),
                Err(e) => error!("✗ 转发报告到 Telegram 失败: {}", e),
            }
        }

        Ok(())
    }

    /// 判断消息是否应该被过滤
    async fn should_filter(&self, message: &Message) -> bool {
        // 如果没有配置关键词，不过滤
        if self.config.processing.keywords.is_empty() {
            return false;
        }

        // 检查消息是否包含关键词 - 如果包含关键词则不过滤（返回false）
        let lower_text = message.text.to_lowercase();
        let has_keyword = self.config.processing.keywords.iter().any(|keyword| {
            lower_text.contains(&keyword.to_lowercase())
        });

        // 如果包含任何关键词，则不过滤（返回false）
        // 如果不包含关键词，则过滤（返回true）
        !has_keyword
    }

    /// 检查消息是否来自监控的频道 - 现在接受所有频道
    pub async fn should_process_message(&self, _channel_id: i64) -> bool {
        true  // 接受所有频道的消息，不再进行验证
    }

    /// 获取所有监控的频道
    pub async fn get_channels(&self) -> Result<Vec<ChannelInfo>> {
        let channels = self.monitored_channels.lock().await;
        Ok(channels.clone())
    }

    /// 添加频道到监控列表
    pub async fn add_channel(&self, channel_id: i64, channel_name: Option<String>) -> Result<()> {
        let mut channels = self.monitored_channels.lock().await;

        // 检查是否已存在
        if channels.iter().any(|c| c.channel_id == channel_id) {
            return Ok(()); // 已存在，无需添加
        }

        let channel = ChannelInfo {
            channel_id,
            channel_name,
            added_at: chrono::Utc::now().timestamp(),
        };

        channels.push(channel);
        info!("添加监控频道: {}", channel_id);

        Ok(())
    }

    /// 从监控列表中删除频道
    pub async fn remove_channel(&self, channel_id: i64) -> Result<()> {
        let mut channels = self.monitored_channels.lock().await;
        let initial_len = channels.len();

        channels.retain(|c| c.channel_id != channel_id);

        if channels.len() < initial_len {
            info!("删除监控频道: {}", channel_id);
        }

        Ok(())
    }

    /// 更新整个频道列表
    pub async fn update_channels(&self, channel_ids: Vec<i64>) -> Result<()> {
        let mut channels = self.monitored_channels.lock().await;

        // 保留现有的频道名称信息
        let existing: std::collections::HashMap<i64, Option<String>> = channels.iter()
            .map(|c| (c.channel_id, c.channel_name.clone()))
            .collect();

        // 替换为新的频道列表
        *channels = channel_ids.into_iter()
            .map(|id| ChannelInfo {
                channel_id: id,
                channel_name: existing.get(&id).cloned().unwrap_or(None),
                added_at: existing.get(&id).map_or(chrono::Utc::now().timestamp(), |_| {
                    // 如果频道已存在，保留原添加时间
                    chrono::Utc::now().timestamp()
                }),
            })
            .collect();

        info!("更新频道列表，共 {} 个频道", channels.len());
        Ok(())
    }

    /// 检查频道是否在监控列表中
    pub async fn has_channel(&self, channel_id: i64) -> Result<bool> {
        let channels = self.monitored_channels.lock().await;
        Ok(channels.iter().any(|c| c.channel_id == channel_id))
    }
}

// 为 MessageProcessor 实现 Clone
impl Clone for MessageProcessor {
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            ai_service: Arc::clone(&self.ai_service),
            telegram_bot: Arc::clone(&self.telegram_bot),
            message_queue: Arc::clone(&self.message_queue),
            analysis_results: Arc::clone(&self.analysis_results),
            is_running: Arc::clone(&self.is_running),
            monitored_channels: Arc::clone(&self.monitored_channels),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{AIConfig, KimiConfig};

    // TODO: 添加测试用的 Mock AI Service
    // 目前暂时跳过，因为需要 Mock trait object

    #[tokio::test]
    async fn test_message_summary() {
        let msg = Message {
            id: 1,
            channel_id: -100123,
            channel_name: "TestChannel".to_string(),
            text: "This is a very long message that should be truncated in the summary".to_string(),
            timestamp: 1234567890,
            sender: None,
            media_type: None,
        };

        let summary = msg.summary();
        assert!(summary.contains("TestChannel"));
        assert!(summary.contains("1"));
        assert!(summary.contains("..."));  // 应该被截断
    }
}
