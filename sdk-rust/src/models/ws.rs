use serde::{Deserialize, Serialize};

use super::{
    AccountOverview, Candlestick, MarketDepth, MarketPrice, MarketTrade,
    UserActiveTwap, UserFundingHistoryItem, UserOpenOrder, UserOrderHistoryItem,
    UserPosition, UserTradeHistoryItem,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WsMessage<T> {
    pub channel: String,
    pub data: T,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountOverviewWsMessage {
    pub account_overview: AccountOverview,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPositionsWsMessage {
    pub positions: Vec<UserPosition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserOpenOrdersWsMessage {
    pub orders: Vec<UserOpenOrder>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserOrderHistoryWsMessage {
    pub orders: Vec<UserOrderHistoryItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserTradeHistoryWsMessage {
    pub trades: Vec<UserTradeHistoryItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFundingHistoryWsMessage {
    pub funding: Vec<UserFundingHistoryItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketPriceWsMessage {
    #[serde(flatten)]
    pub price: MarketPrice,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AllMarketPricesWsMessage {
    pub prices: Vec<MarketPrice>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketTradesWsMessage {
    pub trades: Vec<MarketTrade>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CandlestickWsMessage {
    pub candle: Candlestick,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDepthWsMessage {
    #[serde(flatten)]
    pub depth: MarketDepth,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserActiveTwapsWsMessage {
    pub twaps: Vec<UserActiveTwap>,
}

// --- WebSocket Subscribe/Unsubscribe Messages ---

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WsSubscribeRequest {
    pub method: String,
    pub subscription: String,
}

impl WsSubscribeRequest {
    pub fn subscribe(topic: &str) -> Self {
        Self {
            method: "subscribe".to_string(),
            subscription: topic.to_string(),
        }
    }

    pub fn unsubscribe(topic: &str) -> Self {
        Self {
            method: "unsubscribe".to_string(),
            subscription: topic.to_string(),
        }
    }
}
