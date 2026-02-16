use thiserror::Error;

#[derive(Error, Debug)]
pub enum DecibelError {
    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),

    #[error("API error (status {status}): {message}")]
    Api {
        status: u16,
        status_text: String,
        message: String,
    },

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Transaction error: {message}")]
    Transaction {
        transaction_hash: Option<String>,
        vm_status: Option<String>,
        message: String,
    },

    #[error("Simulation error: {0}")]
    Simulation(String),

    #[error("Signing error: {0}")]
    Signing(String),

    #[error("Gas estimation error: {0}")]
    GasEstimation(String),

    #[error("WebSocket error: {0}")]
    WebSocket(String),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Timeout error: {0}")]
    Timeout(String),

    #[error("URL parse error: {0}")]
    UrlParse(#[from] url::ParseError),
}

pub type Result<T> = std::result::Result<T, DecibelError>;

#[derive(Debug, Clone)]
pub struct ApiResponse<T> {
    pub data: T,
    pub status: u16,
    pub status_text: String,
}
