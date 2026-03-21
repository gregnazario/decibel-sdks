use std::collections::HashMap;
use parking_lot::RwLock;
use crate::models::{
    AccountOverview, MarketDepth, MarketPrice, UserOpenOrder, UserPosition,
};

pub struct PositionStateManager {
    inner: RwLock<PositionStateInner>,
}

struct PositionStateInner {
    positions: HashMap<String, HashMap<String, UserPosition>>,
    open_orders: HashMap<String, Vec<UserOpenOrder>>,
    overviews: HashMap<String, AccountOverview>,
    prices: HashMap<String, MarketPrice>,
    depths: HashMap<String, MarketDepth>,
    last_update_ms: i64,
    is_connected: bool,
    gap_detected: bool,
}

fn now_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

impl Default for PositionStateManager {
    fn default() -> Self {
        Self::new()
    }
}

impl PositionStateManager {
    pub fn new() -> Self {
        Self {
            inner: RwLock::new(PositionStateInner {
                positions: HashMap::new(),
                open_orders: HashMap::new(),
                overviews: HashMap::new(),
                prices: HashMap::new(),
                depths: HashMap::new(),
                last_update_ms: 0,
                is_connected: false,
                gap_detected: false,
            }),
        }
    }

    // -- Position methods ---------------------------------------------------

    pub fn merge_position(&self, subaccount: &str, market: &str, position: UserPosition) {
        let mut inner = self.inner.write();
        let sub_positions = inner
            .positions
            .entry(subaccount.to_string())
            .or_default();
        if position.size.abs() < f64::EPSILON {
            sub_positions.remove(market);
        } else {
            sub_positions.insert(market.to_string(), position);
        }
        inner.last_update_ms = now_ms();
    }

    pub fn positions(&self, subaccount: &str) -> HashMap<String, UserPosition> {
        let inner = self.inner.read();
        inner
            .positions
            .get(subaccount)
            .cloned()
            .unwrap_or_default()
    }

    pub fn position(&self, subaccount: &str, market: &str) -> Option<UserPosition> {
        let inner = self.inner.read();
        inner
            .positions
            .get(subaccount)
            .and_then(|m| m.get(market))
            .cloned()
    }

    pub fn has_position(&self, subaccount: &str, market: &str) -> bool {
        let inner = self.inner.read();
        inner
            .positions
            .get(subaccount)
            .map(|m| m.contains_key(market))
            .unwrap_or(false)
    }

    pub fn net_exposure_usd(&self, subaccount: &str) -> f64 {
        let inner = self.inner.read();
        let positions = match inner.positions.get(subaccount) {
            Some(p) => p,
            None => return 0.0,
        };
        positions
            .iter()
            .map(|(market, pos)| {
                let mark = inner
                    .prices
                    .get(market)
                    .map(|p| p.mark_px)
                    .unwrap_or(pos.entry_price);
                pos.size * mark
            })
            .sum()
    }

    pub fn gross_exposure_usd(&self, subaccount: &str) -> f64 {
        let inner = self.inner.read();
        let positions = match inner.positions.get(subaccount) {
            Some(p) => p,
            None => return 0.0,
        };
        positions
            .iter()
            .map(|(market, pos)| {
                let mark = inner
                    .prices
                    .get(market)
                    .map(|p| p.mark_px)
                    .unwrap_or(pos.entry_price);
                (pos.size * mark).abs()
            })
            .sum()
    }

    // -- Open order methods -------------------------------------------------

    pub fn merge_open_orders(&self, orders: Vec<UserOpenOrder>, subaccount: &str) {
        let filtered: Vec<UserOpenOrder> = orders
            .into_iter()
            .filter(|o| {
                let s = o.status.to_ascii_lowercase();
                s != "cancelled" && s != "canceled"
            })
            .collect();
        let mut inner = self.inner.write();
        inner
            .open_orders
            .insert(subaccount.to_string(), filtered);
        inner.last_update_ms = now_ms();
    }

    pub fn open_orders(&self, subaccount: &str) -> Vec<UserOpenOrder> {
        let inner = self.inner.read();
        inner
            .open_orders
            .get(subaccount)
            .cloned()
            .unwrap_or_default()
    }

    pub fn order_by_id(&self, order_id: &str, subaccount: &str) -> Option<UserOpenOrder> {
        let inner = self.inner.read();
        inner
            .open_orders
            .get(subaccount)
            .and_then(|orders| orders.iter().find(|o| o.order_id == order_id))
            .cloned()
    }

    // -- Overview methods ---------------------------------------------------

    pub fn merge_overview(&self, overview: AccountOverview, subaccount: &str) {
        let mut inner = self.inner.write();
        inner
            .overviews
            .insert(subaccount.to_string(), overview);
        inner.last_update_ms = now_ms();
    }

    pub fn overview(&self, subaccount: &str) -> Option<AccountOverview> {
        self.inner.read().overviews.get(subaccount).cloned()
    }

    pub fn equity(&self, subaccount: &str) -> f64 {
        self.inner
            .read()
            .overviews
            .get(subaccount)
            .map(|o| o.perp_equity_balance)
            .unwrap_or(0.0)
    }

    pub fn margin_usage_pct(&self, subaccount: &str) -> f64 {
        self.inner
            .read()
            .overviews
            .get(subaccount)
            .map(|o| o.margin_usage_pct())
            .unwrap_or(0.0)
    }

    // -- Price methods ------------------------------------------------------

    pub fn merge_price(&self, market: &str, price: MarketPrice) {
        let mut inner = self.inner.write();
        inner.prices.insert(market.to_string(), price);
        inner.last_update_ms = now_ms();
    }

    pub fn price(&self, market: &str) -> Option<MarketPrice> {
        self.inner.read().prices.get(market).cloned()
    }

    pub fn mark_price(&self, market: &str) -> Option<f64> {
        self.inner.read().prices.get(market).map(|p| p.mark_px)
    }

    // -- Depth methods ------------------------------------------------------

    pub fn merge_depth(&self, market: &str, depth: MarketDepth) {
        let mut inner = self.inner.write();
        inner.depths.insert(market.to_string(), depth);
        inner.last_update_ms = now_ms();
    }

    pub fn depth(&self, market: &str) -> Option<MarketDepth> {
        self.inner.read().depths.get(market).cloned()
    }

    // -- Connection state ---------------------------------------------------

    pub fn is_connected(&self) -> bool {
        self.inner.read().is_connected
    }

    pub fn set_connected(&self) {
        self.inner.write().is_connected = true;
    }

    pub fn set_disconnected(&self) {
        self.inner.write().is_connected = false;
    }

    // -- Gap detection ------------------------------------------------------

    pub fn gap_detected(&self) -> bool {
        self.inner.read().gap_detected
    }

    pub fn set_gap_detected(&self) {
        self.inner.write().gap_detected = true;
    }

    pub fn clear_gap_detected(&self) {
        self.inner.write().gap_detected = false;
    }

    // -- Timestamp ----------------------------------------------------------

    pub fn last_update_ms(&self) -> i64 {
        self.inner.read().last_update_ms
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{MarketOrder, MarketPrice};

    fn make_position(market: &str, size: f64, entry_price: f64) -> UserPosition {
        UserPosition {
            market: market.into(),
            user: "0xuser".into(),
            size,
            user_leverage: 10.0,
            entry_price,
            is_isolated: false,
            unrealized_funding: 0.0,
            estimated_liquidation_price: 0.0,
            tp_order_id: None,
            tp_trigger_price: None,
            tp_limit_price: None,
            sl_order_id: None,
            sl_trigger_price: None,
            sl_limit_price: None,
            has_fixed_sized_tpsls: false,
        }
    }

    fn make_price(market: &str, mark_px: f64) -> MarketPrice {
        MarketPrice {
            market: market.into(),
            mark_px,
            mid_px: mark_px,
            oracle_px: mark_px,
            funding_rate_bps: 0.0,
            is_funding_positive: true,
            open_interest: 0.0,
            transaction_unix_ms: 0,
        }
    }

    fn make_order(order_id: &str, status: &str) -> UserOpenOrder {
        UserOpenOrder {
            market: "BTC-USD".into(),
            order_id: order_id.into(),
            client_order_id: None,
            price: 50000.0,
            orig_size: 1.0,
            remaining_size: 1.0,
            is_buy: true,
            time_in_force: "GoodTillCanceled".into(),
            is_reduce_only: false,
            status: status.into(),
            transaction_unix_ms: 0,
            transaction_version: 0,
        }
    }

    fn make_overview(equity: f64, total_margin: f64) -> AccountOverview {
        AccountOverview {
            perp_equity_balance: equity,
            unrealized_pnl: 0.0,
            unrealized_funding_cost: 0.0,
            cross_margin_ratio: 0.0,
            maintenance_margin: 0.0,
            cross_account_leverage_ratio: None,
            cross_account_position: 0.0,
            total_margin,
            usdc_cross_withdrawable_balance: 0.0,
            usdc_isolated_withdrawable_balance: 0.0,
            volume: None,
            net_deposits: None,
            realized_pnl: None,
            liquidation_fees_paid: None,
            liquidation_losses: None,
            all_time_return: None,
            pnl_90d: None,
            sharpe_ratio: None,
            max_drawdown: None,
            weekly_win_rate_12w: None,
            average_cash_position: None,
            average_leverage: None,
        }
    }

    #[test]
    fn empty_state() {
        let mgr = PositionStateManager::new();
        assert!(mgr.positions("sub1").is_empty());
        assert!(mgr.position("sub1", "BTC-USD").is_none());
        assert!(!mgr.has_position("sub1", "BTC-USD"));
        assert_eq!(mgr.net_exposure_usd("sub1"), 0.0);
        assert_eq!(mgr.gross_exposure_usd("sub1"), 0.0);
        assert!(mgr.open_orders("sub1").is_empty());
        assert!(mgr.overview("sub1").is_none());
        assert_eq!(mgr.equity("sub1"), 0.0);
        assert_eq!(mgr.margin_usage_pct("sub1"), 0.0);
        assert!(mgr.price("BTC-USD").is_none());
        assert!(mgr.mark_price("BTC-USD").is_none());
        assert!(mgr.depth("BTC-USD").is_none());
        assert!(!mgr.is_connected());
        assert!(!mgr.gap_detected());
        assert_eq!(mgr.last_update_ms(), 0);
    }

    #[test]
    fn merge_and_query_positions() {
        let mgr = PositionStateManager::new();
        let pos = make_position("BTC-USD", 1.5, 50000.0);
        mgr.merge_position("sub1", "BTC-USD", pos);
        assert!(mgr.has_position("sub1", "BTC-USD"));

        let fetched = mgr.position("sub1", "BTC-USD").unwrap();
        assert!((fetched.size - 1.5).abs() < f64::EPSILON);
        assert_eq!(mgr.positions("sub1").len(), 1);

        let zero = make_position("BTC-USD", 0.0, 50000.0);
        mgr.merge_position("sub1", "BTC-USD", zero);
        assert!(!mgr.has_position("sub1", "BTC-USD"));
        assert!(mgr.positions("sub1").is_empty());
    }

    #[test]
    fn exposure_calculations() {
        let mgr = PositionStateManager::new();
        mgr.merge_position("sub1", "BTC-USD", make_position("BTC-USD", 2.0, 50000.0));
        mgr.merge_position("sub1", "ETH-USD", make_position("ETH-USD", -10.0, 3000.0));
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));
        mgr.merge_price("ETH-USD", make_price("ETH-USD", 3000.0));

        // net = 2*50000 + (-10)*3000 = 100000 - 30000 = 70000
        assert!((mgr.net_exposure_usd("sub1") - 70000.0).abs() < 0.01);
        // gross = |100000| + |-30000| = 130000
        assert!((mgr.gross_exposure_usd("sub1") - 130000.0).abs() < 0.01);
    }

    #[test]
    fn exposure_uses_entry_price_when_no_market_price() {
        let mgr = PositionStateManager::new();
        mgr.merge_position("sub1", "BTC-USD", make_position("BTC-USD", 1.0, 45000.0));
        assert!((mgr.net_exposure_usd("sub1") - 45000.0).abs() < 0.01);
    }

    #[test]
    fn order_tracking() {
        let mgr = PositionStateManager::new();
        let orders = vec![
            make_order("ord1", "Acknowledged"),
            make_order("ord2", "Cancelled"),
            make_order("ord3", "Acknowledged"),
        ];
        mgr.merge_open_orders(orders, "sub1");

        let result = mgr.open_orders("sub1");
        assert_eq!(result.len(), 2);
        assert!(mgr.order_by_id("ord1", "sub1").is_some());
        assert!(mgr.order_by_id("ord2", "sub1").is_none());
        assert!(mgr.order_by_id("ord3", "sub1").is_some());
    }

    #[test]
    fn multi_subaccount() {
        let mgr = PositionStateManager::new();
        mgr.merge_position("sub1", "BTC-USD", make_position("BTC-USD", 1.0, 50000.0));
        mgr.merge_position("sub2", "ETH-USD", make_position("ETH-USD", 5.0, 3000.0));

        assert_eq!(mgr.positions("sub1").len(), 1);
        assert_eq!(mgr.positions("sub2").len(), 1);
        assert!(!mgr.has_position("sub1", "ETH-USD"));
        assert!(!mgr.has_position("sub2", "BTC-USD"));
    }

    #[test]
    fn connection_state() {
        let mgr = PositionStateManager::new();
        assert!(!mgr.is_connected());
        mgr.set_connected();
        assert!(mgr.is_connected());
        mgr.set_disconnected();
        assert!(!mgr.is_connected());
    }

    #[test]
    fn gap_detection() {
        let mgr = PositionStateManager::new();
        assert!(!mgr.gap_detected());
        mgr.set_gap_detected();
        assert!(mgr.gap_detected());
        mgr.clear_gap_detected();
        assert!(!mgr.gap_detected());
    }

    #[test]
    fn overview_and_equity() {
        let mgr = PositionStateManager::new();
        let overview = make_overview(100_000.0, 30_000.0);
        mgr.merge_overview(overview, "sub1");
        assert!((mgr.equity("sub1") - 100_000.0).abs() < 0.01);
        assert!((mgr.margin_usage_pct("sub1") - 30.0).abs() < 0.01);
    }

    #[test]
    fn price_merge_and_query() {
        let mgr = PositionStateManager::new();
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 45000.0));
        assert!((mgr.mark_price("BTC-USD").unwrap() - 45000.0).abs() < 0.01);
        let p = mgr.price("BTC-USD").unwrap();
        assert!((p.mark_px - 45000.0).abs() < 0.01);
    }

    #[test]
    fn depth_merge_and_query() {
        let mgr = PositionStateManager::new();
        let depth = MarketDepth {
            market: "BTC-USD".into(),
            bids: vec![MarketOrder {
                price: 44990.0,
                size: 1.0,
            }],
            asks: vec![MarketOrder {
                price: 45010.0,
                size: 1.0,
            }],
            unix_ms: 0,
        };
        mgr.merge_depth("BTC-USD", depth);
        let d = mgr.depth("BTC-USD").unwrap();
        assert_eq!(d.bids.len(), 1);
        assert_eq!(d.asks.len(), 1);
    }

    #[test]
    fn last_update_ms_advances() {
        let mgr = PositionStateManager::new();
        assert_eq!(mgr.last_update_ms(), 0);
        mgr.merge_position("sub1", "BTC-USD", make_position("BTC-USD", 1.0, 50000.0));
        assert!(mgr.last_update_ms() > 0);
    }

    #[test]
    fn send_sync_assertion() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<PositionStateManager>();
    }
}
