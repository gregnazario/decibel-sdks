use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerpMarketConfig {
    pub market_addr: String,
    pub market_name: String,
    pub sz_decimals: i32,
    pub px_decimals: i32,
    pub max_leverage: f64,
    pub min_size: f64,
    pub lot_size: f64,
    pub tick_size: f64,
    pub max_open_interest: f64,
    pub margin_call_fee_pct: f64,
    pub taker_in_next_block: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDepth {
    pub market: String,
    pub bids: Vec<MarketOrder>,
    pub asks: Vec<MarketOrder>,
    pub unix_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketOrder {
    pub price: f64,
    pub size: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketPrice {
    pub market: String,
    pub mark_px: f64,
    pub mid_px: f64,
    pub oracle_px: f64,
    pub funding_rate_bps: f64,
    pub is_funding_positive: bool,
    pub open_interest: f64,
    pub transaction_unix_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketContext {
    pub market: String,
    pub volume_24h: f64,
    pub open_interest: f64,
    pub previous_day_price: f64,
    pub price_change_pct_24h: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Candlestick {
    #[serde(rename = "T")]
    pub close_timestamp: i64,
    pub c: f64,
    pub h: f64,
    pub i: String,
    pub l: f64,
    pub o: f64,
    pub t: i64,
    pub v: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketTrade {
    pub market: String,
    pub price: f64,
    pub size: f64,
    pub is_buy: bool,
    pub unix_ms: i64,
}
