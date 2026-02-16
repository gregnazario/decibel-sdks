use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPosition {
    pub market: String,
    pub user: String,
    pub size: f64,
    pub user_leverage: f64,
    pub entry_price: f64,
    pub is_isolated: bool,
    pub unrealized_funding: f64,
    pub estimated_liquidation_price: f64,
    pub tp_order_id: Option<String>,
    pub tp_trigger_price: Option<f64>,
    pub tp_limit_price: Option<f64>,
    pub sl_order_id: Option<String>,
    pub sl_trigger_price: Option<f64>,
    pub sl_limit_price: Option<f64>,
    pub has_fixed_sized_tpsls: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerpPosition {
    pub size: f64,
    pub sz_decimals: i32,
    pub entry_px: f64,
    pub max_leverage: f64,
    pub is_long: bool,
    pub token_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrossedPosition {
    pub positions: Vec<PerpPosition>,
}
