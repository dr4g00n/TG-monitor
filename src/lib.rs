// Library crate for tg-meme-token-monitor
// This allows integration tests to access internal modules

pub mod ai;
pub mod config;
pub mod http;
pub mod processor;
pub mod telegram;

// Re-export commonly used types for convenience
pub use ai::{AIService, AIServiceFactory};
pub use config::Config;
pub use http::server::HttpServer;
pub use processor::MessageProcessor;
pub use telegram::bot::TelegramBot;
