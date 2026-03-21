use serde::{Deserialize, Serialize};

use super::enums::TradeAction;

// ---------------------------------------------------------------------------
// AccountOverview
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct AccountOverview {
    pub perp_equity_balance: f64,
    pub unrealized_pnl: f64,
    pub unrealized_funding_cost: f64,
    pub cross_margin_ratio: f64,
    pub maintenance_margin: f64,
    pub cross_account_leverage_ratio: Option<f64>,
    pub cross_account_position: f64,
    pub total_margin: f64,
    pub usdc_cross_withdrawable_balance: f64,
    pub usdc_isolated_withdrawable_balance: f64,
    pub volume: Option<f64>,
    pub net_deposits: Option<f64>,
    pub realized_pnl: Option<f64>,
    pub liquidation_fees_paid: Option<f64>,
    pub liquidation_losses: Option<f64>,
    pub all_time_return: Option<f64>,
    pub pnl_90d: Option<f64>,
    pub sharpe_ratio: Option<f64>,
    pub max_drawdown: Option<f64>,
    pub weekly_win_rate_12w: Option<f64>,
    pub average_cash_position: Option<f64>,
    pub average_leverage: Option<f64>,
}

impl AccountOverview {
    /// Percentage of equity used as margin. 100% = fully utilized.
    pub fn margin_usage_pct(&self) -> f64 {
        if self.perp_equity_balance == 0.0 {
            return 0.0;
        }
        (self.total_margin / self.perp_equity_balance) * 100.0
    }

    /// USD buffer between current equity and maintenance margin.
    pub fn liquidation_buffer_usd(&self) -> f64 {
        self.perp_equity_balance - self.maintenance_margin
    }

    /// Percentage buffer above maintenance margin.
    pub fn liquidation_buffer_pct(&self) -> f64 {
        if self.maintenance_margin == 0.0 {
            return f64::INFINITY;
        }
        (self.perp_equity_balance / self.maintenance_margin - 1.0) * 100.0
    }

    /// True if within `threshold_pct` of liquidation.
    pub fn is_liquidation_warning(&self, threshold_pct: f64) -> bool {
        self.liquidation_buffer_pct() < threshold_pct
    }

    /// Total withdrawable USDC across cross and isolated accounts.
    pub fn total_withdrawable(&self) -> f64 {
        self.usdc_cross_withdrawable_balance + self.usdc_isolated_withdrawable_balance
    }
}

impl std::fmt::Display for AccountOverview {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Account(equity={:.2}, margin_usage={:.1}%, liq_buf={:.1}%)",
            self.perp_equity_balance,
            self.margin_usage_pct(),
            self.liquidation_buffer_pct()
        )
    }
}

// ---------------------------------------------------------------------------
// UserPosition
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
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

impl UserPosition {
    pub fn is_long(&self) -> bool {
        self.size > 0.0
    }

    pub fn is_short(&self) -> bool {
        self.size < 0.0
    }

    pub fn is_flat(&self) -> bool {
        self.size == 0.0
    }

    pub fn direction(&self) -> &str {
        if self.size > 0.0 {
            "long"
        } else if self.size < 0.0 {
            "short"
        } else {
            "flat"
        }
    }

    /// Position notional value at current mark price.
    pub fn notional(&self, mark_price: f64) -> f64 {
        self.size.abs() * mark_price
    }

    /// Unrealized P&L excluding funding.
    pub fn unrealized_pnl(&self, mark_price: f64) -> f64 {
        (mark_price - self.entry_price) * self.size
    }

    /// Percentage distance from current price to estimated liquidation.
    pub fn liquidation_distance_pct(&self, mark_price: f64) -> f64 {
        if self.estimated_liquidation_price == 0.0 || mark_price == 0.0 {
            return f64::INFINITY;
        }
        ((mark_price - self.estimated_liquidation_price).abs() / mark_price) * 100.0
    }

    pub fn has_tp(&self) -> bool {
        self.tp_order_id.is_some()
    }

    pub fn has_sl(&self) -> bool {
        self.sl_order_id.is_some()
    }

    /// True if position has both TP and SL.
    pub fn has_protection(&self) -> bool {
        self.has_tp() && self.has_sl()
    }
}

impl std::fmt::Display for UserPosition {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Position({} {} {} @ {} {}x, liq={})",
            self.market,
            self.direction(),
            self.size.abs(),
            self.entry_price,
            self.user_leverage,
            self.estimated_liquidation_price
        )
    }
}

// ---------------------------------------------------------------------------
// UserOpenOrder
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
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

impl UserOpenOrder {
    pub fn filled_size(&self) -> f64 {
        self.orig_size - self.remaining_size
    }

    /// Fill percentage: 0–100.
    pub fn fill_pct(&self) -> f64 {
        if self.orig_size == 0.0 {
            return 0.0;
        }
        (self.filled_size() / self.orig_size) * 100.0
    }

    pub fn side(&self) -> &str {
        if self.is_buy {
            "buy"
        } else {
            "sell"
        }
    }

    /// Remaining order notional = remaining_size * price.
    pub fn notional(&self) -> f64 {
        self.remaining_size * self.price
    }
}

impl std::fmt::Display for UserOpenOrder {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Order({} {} {} @ {} [{:.0}% filled])",
            self.market,
            self.side(),
            self.remaining_size,
            self.price,
            self.fill_pct()
        )
    }
}

// ---------------------------------------------------------------------------
// UserTradeHistoryItem
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct UserTradeHistoryItem {
    pub account: String,
    pub market: String,
    pub action: TradeAction,
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

impl UserTradeHistoryItem {
    /// Net P&L after fees and funding.
    pub fn net_pnl(&self) -> f64 {
        let pnl = self.realized_pnl_amount;
        let fee = if self.is_rebate {
            self.fee_amount
        } else {
            -self.fee_amount
        };
        let funding = if self.is_funding_positive {
            -self.realized_funding_amount
        } else {
            self.realized_funding_amount
        };
        pnl + fee + funding
    }

    pub fn notional(&self) -> f64 {
        self.size * self.price
    }
}

impl std::fmt::Display for UserTradeHistoryItem {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Trade({} {:?} {} @ {}, pnl={:.2})",
            self.market,
            self.action,
            self.size,
            self.price,
            self.net_pnl()
        )
    }
}

// ---------------------------------------------------------------------------
// UserSubaccount
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct UserSubaccount {
    pub subaccount_address: String,
    pub primary_account_address: String,
    pub is_primary: bool,
    pub custom_label: Option<String>,
    pub is_active: Option<bool>,
}

// ---------------------------------------------------------------------------
// UserFundingHistoryItem
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct UserFundingHistoryItem {
    pub market: String,
    pub funding_rate_bps: f64,
    pub is_funding_positive: bool,
    pub funding_amount: f64,
    pub position_size: f64,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

// ---------------------------------------------------------------------------
// UserFundHistoryItem
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct UserFundHistoryItem {
    pub amount: f64,
    pub is_deposit: bool,
    pub transaction_unix_ms: i64,
    pub transaction_version: i64,
}

// ---------------------------------------------------------------------------
// Delegation
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct Delegation {
    pub delegated_account: String,
    pub permission_type: String,
    pub expiration_time_s: Option<i64>,
}

// ===========================================================================
// Tests
// ===========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -- AccountOverview ----------------------------------------------------

    fn sample_account() -> AccountOverview {
        AccountOverview {
            perp_equity_balance: 100_000.0,
            unrealized_pnl: 2_500.0,
            unrealized_funding_cost: -50.0,
            cross_margin_ratio: 0.15,
            maintenance_margin: 5_000.0,
            cross_account_leverage_ratio: Some(3.0),
            cross_account_position: 300_000.0,
            total_margin: 30_000.0,
            usdc_cross_withdrawable_balance: 65_000.0,
            usdc_isolated_withdrawable_balance: 5_000.0,
            volume: Some(1_000_000.0),
            net_deposits: Some(90_000.0),
            realized_pnl: Some(8_000.0),
            liquidation_fees_paid: Some(0.0),
            liquidation_losses: Some(0.0),
            all_time_return: Some(11.1),
            pnl_90d: Some(5_000.0),
            sharpe_ratio: Some(1.5),
            max_drawdown: Some(-8.0),
            weekly_win_rate_12w: Some(0.75),
            average_cash_position: Some(50_000.0),
            average_leverage: Some(2.5),
        }
    }

    /// Margin usage tells the bot how much room is left for new positions.
    /// At 30% usage a bot can safely add more positions.
    #[test]
    fn account_margin_usage_pct() {
        let acc = sample_account();
        let usage = acc.margin_usage_pct();
        assert!((usage - 30.0).abs() < 1e-10);
    }

    /// Liquidation buffer in USD tells how much equity can evaporate
    /// before the account is liquidated.
    #[test]
    fn account_liquidation_buffer_usd() {
        let acc = sample_account();
        let buf = acc.liquidation_buffer_usd();
        assert!((buf - 95_000.0).abs() < 1e-10);
    }

    /// Liquidation buffer percentage — the bot triggers warnings
    /// when this drops below a threshold.
    #[test]
    fn account_liquidation_buffer_pct() {
        let acc = sample_account();
        let pct = acc.liquidation_buffer_pct();
        let expected = (100_000.0 / 5_000.0 - 1.0) * 100.0;
        assert!((pct - expected).abs() < 1e-10);
    }

    /// Warning fires when buffer drops below threshold.
    #[test]
    fn account_liquidation_warning() {
        let acc = sample_account();
        assert!(!acc.is_liquidation_warning(50.0));

        let mut close_to_liq = acc.clone();
        close_to_liq.perp_equity_balance = 6_000.0;
        close_to_liq.maintenance_margin = 5_000.0;
        assert!(close_to_liq.is_liquidation_warning(50.0));
    }

    /// Total withdrawable combines cross + isolated withdrawable.
    #[test]
    fn account_total_withdrawable() {
        let acc = sample_account();
        assert!((acc.total_withdrawable() - 70_000.0).abs() < 1e-10);
    }

    /// Zero equity edge case — should not panic.
    #[test]
    fn account_zero_equity() {
        let mut acc = sample_account();
        acc.perp_equity_balance = 0.0;
        assert_eq!(acc.margin_usage_pct(), 0.0);
    }

    /// Zero maintenance margin — buffer pct should be infinite.
    #[test]
    fn account_zero_maintenance() {
        let mut acc = sample_account();
        acc.maintenance_margin = 0.0;
        assert!(acc.liquidation_buffer_pct().is_infinite());
    }

    /// JSON roundtrip for AccountOverview.
    #[test]
    fn account_overview_roundtrip() {
        let acc = sample_account();
        let json = serde_json::to_string(&acc).unwrap();
        let restored: AccountOverview = serde_json::from_str(&json).unwrap();
        assert!((restored.perp_equity_balance - 100_000.0).abs() < 1e-10);
        assert_eq!(restored.cross_account_leverage_ratio, Some(3.0));
        assert_eq!(restored.volume, Some(1_000_000.0));
    }

    /// Nullable fields should deserialize from null.
    #[test]
    fn account_overview_nullable_fields() {
        let json = r#"{
            "perp_equity_balance": 50000,
            "unrealized_pnl": 0,
            "unrealized_funding_cost": 0,
            "cross_margin_ratio": 0.1,
            "maintenance_margin": 1000,
            "cross_account_leverage_ratio": null,
            "cross_account_position": 0,
            "total_margin": 5000,
            "usdc_cross_withdrawable_balance": 45000,
            "usdc_isolated_withdrawable_balance": 0,
            "volume": null,
            "net_deposits": null,
            "realized_pnl": null,
            "liquidation_fees_paid": null,
            "liquidation_losses": null,
            "all_time_return": null,
            "pnl_90d": null,
            "sharpe_ratio": null,
            "max_drawdown": null,
            "weekly_win_rate_12w": null,
            "average_cash_position": null,
            "average_leverage": null
        }"#;
        let acc: AccountOverview = serde_json::from_str(json).unwrap();
        assert!(acc.cross_account_leverage_ratio.is_none());
        assert!(acc.volume.is_none());
        assert!(acc.sharpe_ratio.is_none());
    }

    // -- UserPosition -------------------------------------------------------

    fn btc_long_position() -> UserPosition {
        UserPosition {
            market: "0xmarket_btc".into(),
            user: "0xuser1".into(),
            size: 1.5,
            user_leverage: 10.0,
            entry_price: 44_000.0,
            is_isolated: false,
            unrealized_funding: -25.0,
            estimated_liquidation_price: 40_000.0,
            tp_order_id: Some("tp_001".into()),
            tp_trigger_price: Some(48_000.0),
            tp_limit_price: Some(47_900.0),
            sl_order_id: Some("sl_001".into()),
            sl_trigger_price: Some(42_000.0),
            sl_limit_price: Some(41_900.0),
            has_fixed_sized_tpsls: false,
        }
    }

    fn eth_short_position() -> UserPosition {
        UserPosition {
            market: "0xmarket_eth".into(),
            user: "0xuser1".into(),
            size: -10.0,
            user_leverage: 5.0,
            entry_price: 3_500.0,
            is_isolated: true,
            unrealized_funding: 15.0,
            estimated_liquidation_price: 4_200.0,
            tp_order_id: None,
            tp_trigger_price: None,
            tp_limit_price: None,
            sl_order_id: None,
            sl_trigger_price: None,
            sl_limit_price: None,
            has_fixed_sized_tpsls: false,
        }
    }

    /// Direction detection determines order routing logic.
    #[test]
    fn position_direction() {
        let long = btc_long_position();
        assert!(long.is_long());
        assert!(!long.is_short());
        assert!(!long.is_flat());
        assert_eq!(long.direction(), "long");

        let short = eth_short_position();
        assert!(!short.is_long());
        assert!(short.is_short());
        assert_eq!(short.direction(), "short");
    }

    /// Flat position (size = 0) must be detected to skip risk calculations.
    #[test]
    fn position_flat() {
        let mut pos = btc_long_position();
        pos.size = 0.0;
        assert!(pos.is_flat());
        assert_eq!(pos.direction(), "flat");
    }

    /// Notional value at mark price tells the bot the position's USD exposure.
    #[test]
    fn position_notional() {
        let pos = btc_long_position();
        let n = pos.notional(45_000.0);
        assert!((n - 67_500.0).abs() < 1e-10);
    }

    /// Unrealized P&L for a long position where price increased.
    /// BTC long 1.5 @ $44k, mark = $45k → PnL = (45k-44k)*1.5 = $1500.
    #[test]
    fn position_unrealized_pnl_long() {
        let pos = btc_long_position();
        let pnl = pos.unrealized_pnl(45_000.0);
        assert!((pnl - 1_500.0).abs() < 1e-10);
    }

    /// Unrealized P&L for a short position where price increased.
    /// ETH short -10 @ $3500, mark = $3600 → PnL = (3600-3500)*(-10) = -$1000.
    #[test]
    fn position_unrealized_pnl_short() {
        let pos = eth_short_position();
        let pnl = pos.unrealized_pnl(3_600.0);
        assert!((pnl - (-1_000.0)).abs() < 1e-10);
    }

    /// Liquidation distance tells the bot how safe the position is.
    /// BTC long, liq=$40k, mark=$45k → distance = |45k-40k|/45k * 100 ≈ 11.1%.
    #[test]
    fn position_liquidation_distance() {
        let pos = btc_long_position();
        let dist = pos.liquidation_distance_pct(45_000.0);
        let expected = (5_000.0 / 45_000.0) * 100.0;
        assert!((dist - expected).abs() < 1e-6);
    }

    /// TP/SL detection is critical — unprotected positions need alerts.
    #[test]
    fn position_tp_sl() {
        let btc = btc_long_position();
        assert!(btc.has_tp());
        assert!(btc.has_sl());
        assert!(btc.has_protection());

        let eth = eth_short_position();
        assert!(!eth.has_tp());
        assert!(!eth.has_sl());
        assert!(!eth.has_protection());
    }

    /// JSON roundtrip for UserPosition.
    #[test]
    fn position_roundtrip() {
        let pos = btc_long_position();
        let json = serde_json::to_string(&pos).unwrap();
        let restored: UserPosition = serde_json::from_str(&json).unwrap();
        assert!((restored.size - 1.5).abs() < 1e-10);
        assert_eq!(restored.tp_order_id.as_deref(), Some("tp_001"));
    }

    #[test]
    fn position_display() {
        let pos = btc_long_position();
        let s = pos.to_string();
        assert!(s.contains("long"));
        assert!(s.contains("10"));
    }

    // -- UserOpenOrder ------------------------------------------------------

    fn sample_open_order() -> UserOpenOrder {
        UserOpenOrder {
            market: "0xmarket_btc".into(),
            order_id: "order_123".into(),
            client_order_id: Some("client_456".into()),
            price: 44_500.0,
            orig_size: 2.0,
            remaining_size: 1.5,
            is_buy: true,
            time_in_force: "GoodTillCanceled".into(),
            is_reduce_only: false,
            status: "Acknowledged".into(),
            transaction_unix_ms: 1_710_000_000_000,
            transaction_version: 12345,
        }
    }

    /// Filled size tracks how much has executed — essential for inventory.
    #[test]
    fn open_order_filled_size() {
        let o = sample_open_order();
        assert!((o.filled_size() - 0.5).abs() < 1e-10);
    }

    /// Fill percentage for partial fills.
    #[test]
    fn open_order_fill_pct() {
        let o = sample_open_order();
        let pct = o.fill_pct();
        assert!((pct - 25.0).abs() < 1e-10);
    }

    /// Side as human-readable string for logging.
    #[test]
    fn open_order_side() {
        let o = sample_open_order();
        assert_eq!(o.side(), "buy");

        let mut sell = o.clone();
        sell.is_buy = false;
        assert_eq!(sell.side(), "sell");
    }

    /// Notional = remaining_size * price, used for margin calculations.
    #[test]
    fn open_order_notional() {
        let o = sample_open_order();
        let n = o.notional();
        assert!((n - 66_750.0).abs() < 1e-10);
    }

    /// Zero orig_size should not panic.
    #[test]
    fn open_order_zero_size() {
        let mut o = sample_open_order();
        o.orig_size = 0.0;
        o.remaining_size = 0.0;
        assert_eq!(o.fill_pct(), 0.0);
    }

    /// JSON roundtrip for UserOpenOrder.
    #[test]
    fn open_order_roundtrip() {
        let o = sample_open_order();
        let json = serde_json::to_string(&o).unwrap();
        let restored: UserOpenOrder = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.order_id, "order_123");
        assert!((restored.price - 44_500.0).abs() < 1e-10);
    }

    // -- UserTradeHistoryItem -----------------------------------------------

    fn sample_trade_history() -> UserTradeHistoryItem {
        UserTradeHistoryItem {
            account: "0xuser1".into(),
            market: "0xmarket_btc".into(),
            action: TradeAction::CloseLong,
            size: 1.0,
            price: 45_500.0,
            is_profit: true,
            realized_pnl_amount: 500.0,
            is_funding_positive: true,
            realized_funding_amount: 10.0,
            is_rebate: false,
            fee_amount: 5.0,
            transaction_unix_ms: 1_710_000_000_000,
            transaction_version: 12346,
        }
    }

    /// Net P&L must account for fees and funding direction.
    /// PnL=500, fee=-5 (not rebate), funding=-10 (is_funding_positive → longs pay)
    /// Net = 500 + (-5) + (-10) = 485.
    #[test]
    fn trade_history_net_pnl() {
        let t = sample_trade_history();
        let net = t.net_pnl();
        assert!((net - 485.0).abs() < 1e-10);
    }

    /// When the fee is a rebate, it adds to P&L instead of subtracting.
    #[test]
    fn trade_history_net_pnl_with_rebate() {
        let mut t = sample_trade_history();
        t.is_rebate = true;
        let net = t.net_pnl();
        // PnL=500, fee=+5 (rebate), funding=-10
        assert!((net - 495.0).abs() < 1e-10);
    }

    /// Notional = size * price.
    #[test]
    fn trade_history_notional() {
        let t = sample_trade_history();
        assert!((t.notional() - 45_500.0).abs() < 1e-10);
    }

    /// JSON roundtrip for UserTradeHistoryItem.
    #[test]
    fn trade_history_roundtrip() {
        let t = sample_trade_history();
        let json = serde_json::to_string(&t).unwrap();
        let restored: UserTradeHistoryItem = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.action, TradeAction::CloseLong);
        assert!((restored.size - 1.0).abs() < 1e-10);
    }

    // -- UserSubaccount -----------------------------------------------------

    /// JSON roundtrip for UserSubaccount.
    #[test]
    fn subaccount_roundtrip() {
        let sub = UserSubaccount {
            subaccount_address: "0xsub1".into(),
            primary_account_address: "0xprimary".into(),
            is_primary: true,
            custom_label: Some("Main".into()),
            is_active: Some(true),
        };
        let json = serde_json::to_string(&sub).unwrap();
        let restored: UserSubaccount = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.subaccount_address, "0xsub1");
        assert!(restored.is_primary);
        assert_eq!(restored.custom_label.as_deref(), Some("Main"));
    }

    /// Subaccount with null optional fields.
    #[test]
    fn subaccount_nullable_fields() {
        let json = r#"{
            "subaccount_address": "0xsub2",
            "primary_account_address": "0xprimary",
            "is_primary": false,
            "custom_label": null,
            "is_active": null
        }"#;
        let sub: UserSubaccount = serde_json::from_str(json).unwrap();
        assert!(sub.custom_label.is_none());
        assert!(sub.is_active.is_none());
    }

    // -- UserFundingHistoryItem ---------------------------------------------

    /// JSON roundtrip for UserFundingHistoryItem.
    #[test]
    fn funding_history_roundtrip() {
        let fh = UserFundingHistoryItem {
            market: "0xmarket_btc".into(),
            funding_rate_bps: 0.5,
            is_funding_positive: true,
            funding_amount: 12.5,
            position_size: 2.0,
            transaction_unix_ms: 1_710_000_000_000,
            transaction_version: 12347,
        };
        let json = serde_json::to_string(&fh).unwrap();
        let restored: UserFundingHistoryItem = serde_json::from_str(&json).unwrap();
        assert!((restored.funding_rate_bps - 0.5).abs() < 1e-10);
        assert!((restored.position_size - 2.0).abs() < 1e-10);
    }

    // -- UserFundHistoryItem ------------------------------------------------

    /// JSON roundtrip for deposit/withdrawal history.
    #[test]
    fn fund_history_roundtrip() {
        let fh = UserFundHistoryItem {
            amount: 10_000.0,
            is_deposit: true,
            transaction_unix_ms: 1_710_000_000_000,
            transaction_version: 12348,
        };
        let json = serde_json::to_string(&fh).unwrap();
        let restored: UserFundHistoryItem = serde_json::from_str(&json).unwrap();
        assert!((restored.amount - 10_000.0).abs() < 1e-10);
        assert!(restored.is_deposit);
    }

    // -- Delegation ---------------------------------------------------------

    /// JSON roundtrip for Delegation.
    #[test]
    fn delegation_roundtrip() {
        let d = Delegation {
            delegated_account: "0xdelegate".into(),
            permission_type: "trade".into(),
            expiration_time_s: Some(1_710_100_000),
        };
        let json = serde_json::to_string(&d).unwrap();
        let restored: Delegation = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.delegated_account, "0xdelegate");
        assert_eq!(restored.expiration_time_s, Some(1_710_100_000));
    }

    /// Delegation without expiration (permanent delegation).
    #[test]
    fn delegation_no_expiry() {
        let json = r#"{
            "delegated_account": "0xbot",
            "permission_type": "trade",
            "expiration_time_s": null
        }"#;
        let d: Delegation = serde_json::from_str(json).unwrap();
        assert!(d.expiration_time_s.is_none());
    }
}
