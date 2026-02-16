use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountOverview {
    pub perp_equity_balance: f64,
    pub unrealized_pnl: f64,
    pub unrealized_funding_cost: f64,
    pub cross_margin_ratio: f64,
    pub maintenance_margin: f64,
    pub cross_account_leverage_ratio: Option<f64>,
    pub volume: Option<f64>,
    pub net_deposits: Option<f64>,
    pub all_time_return: Option<f64>,
    pub pnl_90d: Option<f64>,
    pub sharpe_ratio: Option<f64>,
    pub max_drawdown: Option<f64>,
    pub weekly_win_rate_12w: Option<f64>,
    pub average_cash_position: Option<f64>,
    pub average_leverage: Option<f64>,
    pub cross_account_position: f64,
    pub total_margin: f64,
    pub usdc_cross_withdrawable_balance: f64,
    pub usdc_isolated_withdrawable_balance: f64,
    pub realized_pnl: Option<f64>,
    pub liquidation_fees_paid: Option<f64>,
    pub liquidation_losses: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserSubaccount {
    pub subaccount_address: String,
    pub primary_account_address: String,
    pub is_primary: bool,
    pub custom_label: Option<String>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Delegation {
    pub delegated_account: String,
    pub permission_type: String,
    pub expiration_time_s: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFundHistoryItem {
    pub amount: f64,
    pub is_deposit: bool,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFundingHistoryItem {
    pub market: String,
    pub funding_rate_bps: f64,
    pub is_funding_positive: bool,
    pub funding_amount: f64,
    pub position_size: f64,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LeaderboardItem {
    pub rank: i64,
    pub account: String,
    pub account_value: f64,
    pub realized_pnl: f64,
    pub roi: f64,
    pub volume: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Leaderboard {
    pub items: Vec<LeaderboardItem>,
    pub total_count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioChartData {
    pub timestamp: i64,
    pub value: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserNotification {
    pub id: String,
    #[serde(rename = "type")]
    pub notification_type: String,
    pub message: String,
    pub timestamp: i64,
    pub read: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserTradeHistoryItem {
    pub account: String,
    pub market: String,
    pub action: String,
    pub size: f64,
    pub price: f64,
    pub is_profit: bool,
    pub realized_pnl_amount: f64,
    pub is_funding_positive: bool,
    pub realized_funding_amount: f64,
    pub is_rebate: bool,
    pub fee_amount: f64,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}
