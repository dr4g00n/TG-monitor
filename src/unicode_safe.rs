//! Unicode安全工具模块
//! 解决tracing库在处理复杂Unicode字符时的UTF-8边界错误

use unicode_normalization::UnicodeNormalization;

/// 确保字符串在日志记录时是UTF-8安全的
/// 通过规范化Unicode字符来避免字节边界问题
pub fn normalize_for_logging(text: &str, max_chars: usize) -> String {
    // 首先进行Unicode规范化，避免组合字符问题
    let normalized: String = text.nfc().collect();

    // 限制字符数而不是字节数
    let char_count = normalized.chars().count();
    if char_count > max_chars {
        let truncated: String = normalized.chars().take(max_chars - 3).collect();
        format!("{}...", truncated)
    } else {
        normalized
    }
}

/// 安全的字符串截断，确保不破坏UTF-8字符边界
pub fn safe_truncate_for_async(text: &str, max_chars: usize) -> String {
    if text.chars().count() <= max_chars {
        return text.to_string();
    }

    // 使用字符迭代器而不是字节切片
    text.chars().take(max_chars).collect()
}

/// 检测并清理可能导致UTF-8边界问题的字符组合
pub fn sanitize_unicode_combinations(text: &str) -> String {
    // 移除或替换可能导致问题的字符
    let cleaned = text
        .replace('：', ":")  // 全角冒号 -> 半角冒号
        .replace('，', ",")  // 全角逗号 -> 半角逗号
        .replace('。', ".")  // 全角句号 -> 半角句号
        .replace('（', "(")  // 全角左括号 -> 半角左括号
        .replace('）', ")")  // 全角右括号 -> 半角右括号
        .replace('【', "[")  // 全角左方括号 -> 半角左方括号
        .replace('】', "]")  // 全角右方括号 -> 半角右方括号
        .replace('“', "\"") // 全角左引号 -> 半角引号
        .replace('”', "\"") // 全角右引号 -> 半角引号
        .replace('‘', "'")  // 全角左单引号 -> 半角单引号
        .replace('’', "'"); // 全角右单引号 -> 半角单引号

    cleaned
}

/// 为异步任务创建安全的日志消息
pub fn safe_log_message(original: &str, context: &str) -> String {
    // 首先清理Unicode组合
    let cleaned = sanitize_unicode_combinations(original);

    // 然后进行规范化
    let normalized = normalize_for_logging(&cleaned, 200);

    // 如果文本被显著修改，添加提示
    if cleaned != original {
        format!("{} [Unicode已清理]", normalized)
    } else {
        normalized
    }
}

/// 为tracing日志创建安全的格式化器
pub fn create_safe_summary(text: &str) -> String {
    if text.is_empty() {
        return "(空文本)".to_string();
    }

    // 先进行基本清理
    let cleaned = sanitize_unicode_combinations(text);

    // 限制长度并规范化
    let normalized = normalize_for_logging(&cleaned, 100);

    // 如果文本很短，直接返回
    if text.chars().count() <= 50 {
        normalized
    } else {
        // 对于长文本，确保安全的字符边界
        let safe_truncated = safe_truncate_for_async(&normalized, 50);
        if safe_truncated.len() < normalized.len() {
            format!("{}...", safe_truncated)
        } else {
            safe_truncated
        }
    }
}

/// 检测文本是否包含可能导致UTF-8边界问题的字符
pub fn has_problematic_unicode(text: &str) -> bool {
    text.contains('：') ||
    text.contains('，') ||
    text.contains('。') ||
    text.contains('（') ||
    text.contains('）') ||
    text.contains('【') ||
    text.contains('】') ||
    text.contains('“') ||
    text.contains('”') ||
    text.contains('‘') ||
    text.contains('’')
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize_for_logging() {
        let text = "🚀 新token $HAPPY 即将发射！合约地址：0x123";
        let result = normalize_for_logging(text, 50);
        assert!(result.contains("🚀"));
        assert!(result.len() <= 53); // 50 chars + "..."
    }

    #[test]
    fn test_sanitize_unicode_combinations() {
        let text = "买入建议：现在价格0.0001";
        let result = sanitize_unicode_combinations(text);
        assert!(!result.contains('：'));
        assert!(result.contains(':'));
    }

    #[test]
    fn test_create_safe_summary() {
        let text = "🚀 新token $HAPPY 即将发射！合约地址：0x742d35cc663897c5f2f2c7e3b5f8c9d4e2f1a0b9\n\n买入建议：现在价格0.0001，目标0.001";
        let result = create_safe_summary(text);
        assert!(result.len() <= 100);
        assert!(!result.contains('：'));
    }

    #[test]
    fn test_has_problematic_unicode() {
        assert!(has_problematic_unicode("买入建议：现在价格"));
        assert!(!has_problematic_unicode("buy suggestion: current price"));
    }
}