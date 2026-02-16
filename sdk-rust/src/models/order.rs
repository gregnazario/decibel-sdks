use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserOpenOrder {
    pub market: String,
    pub order_id: String,
    pub client_order_id: Option<String>,
    pub price: f64,
    pub orig_size: f64,
    pub remaining_size: f64,
    pub is_buy: bool,
    pub time_in_force: String,
    pub is_reduce_only: bool,
    pub status: String,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserOrderHistoryItem {
    pub market: String,
    pub order_id: String,
    pub client_order_id: Option<String>,
    pub price: f64,
    pub orig_size: f64,
    pub remaining_size: f64,
    pub is_buy: bool,
    pub time_in_force: String,
    pub is_reduce_only: bool,
    pub status: String,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderStatus {
    pub parent: String,
    pub market: String,
    pub order_id: String,
    pub status: String,
    pub orig_size: f64,
    pub remaining_size: f64,
    pub size_delta: f64,
    pub price: f64,
    pub is_buy: bool,
    pub details: String,
    pub transaction_version: i64,
    pub unix_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserActiveTwap {
    pub market: String,
    pub is_buy: bool,
    pub order_id: String,
    pub client_order_id: String,
    pub is_reduce_only: bool,
    pub start_unix_ms: i64,
    pub frequency_s: i64,
    pub duration_s: i64,
    pub orig_size: f64,
    pub remaining_size: f64,
    pub status: String,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderEvent {
    pub client_order_id: serde_json::Value,
    pub details: String,
    pub is_bid: bool,
    pub is_taker: bool,
    pub market: String,
    pub metadata_bytes: String,
    pub order_id: String,
    pub orig_size: String,
    pub parent: String,
    pub price: String,
    pub remaining_size: String,
    pub size_delta: String,
    pub status: serde_json::Value,
    pub time_in_force: serde_json::Value,
    pub trigger_condition: serde_json::Value,
    pub user: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TwapEvent {
    pub account: String,
    pub duration_s: String,
    pub frequency_s: String,
    pub is_buy: bool,
    pub is_reduce_only: bool,
    pub market: String,
    pub order_id: serde_json::Value,
    pub orig_size: String,
    pub remain_size: String,
    pub start_time_s: String,
    pub status: serde_json::Value,
    pub client_order_id: serde_json::Value,
}
