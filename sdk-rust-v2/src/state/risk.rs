use super::position_manager::PositionStateManager;

#[derive(Debug, Clone)]
pub struct LiquidationEstimate {
    pub liquidation_price: f64,
    pub current_price: f64,
    pub distance_pct: f64,
    pub distance_usd: f64,
}

#[derive(Debug, Clone)]
pub struct MarginWarning {
    pub level: String,
    pub margin_usage_pct: f64,
    pub available_margin: f64,
    pub equity: f64,
}

#[derive(Debug, Clone)]
pub struct FundingAccrual {
    pub hourly_usd: f64,
    pub annualized_pct: f64,
    pub funding_rate_bps: f64,
    pub position_notional: f64,
}

pub struct RiskMonitor<'a> {
    state: &'a PositionStateManager,
}

impl<'a> RiskMonitor<'a> {
    pub fn new(state: &'a PositionStateManager) -> Self {
        Self { state }
    }

    pub fn liquidation_distance(
        &self,
        subaccount: &str,
        market: &str,
    ) -> Option<LiquidationEstimate> {
        let pos = self.state.position(subaccount, market)?;
        if pos.estimated_liquidation_price == 0.0 {
            return None;
        }
        let current_price = self
            .state
            .mark_price(market)
            .unwrap_or(pos.entry_price);
        if current_price <= 0.0 {
            return None;
        }
        let distance_usd = (current_price - pos.estimated_liquidation_price).abs();
        let distance_pct = (distance_usd / current_price) * 100.0;
        Some(LiquidationEstimate {
            liquidation_price: pos.estimated_liquidation_price,
            current_price,
            distance_pct,
            distance_usd,
        })
    }

    pub fn min_liquidation_distance(
        &self,
        subaccount: &str,
    ) -> Option<LiquidationEstimate> {
        let positions = self.state.positions(subaccount);
        positions
            .keys()
            .filter_map(|market| self.liquidation_distance(subaccount, market))
            .min_by(|a, b| {
                a.distance_pct
                    .partial_cmp(&b.distance_pct)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    }

    pub fn margin_warning(&self, subaccount: &str) -> Option<MarginWarning> {
        let overview = self.state.overview(subaccount)?;
        let usage = overview.margin_usage_pct();
        if usage < 50.0 {
            return None;
        }
        let level = if usage >= 75.0 {
            "critical"
        } else {
            "warning"
        };
        Some(MarginWarning {
            level: level.to_string(),
            margin_usage_pct: usage,
            available_margin: overview.perp_equity_balance - overview.total_margin,
            equity: overview.perp_equity_balance,
        })
    }

    pub fn positions_without_tp_sl(&self, subaccount: &str) -> Vec<String> {
        let positions = self.state.positions(subaccount);
        let mut result: Vec<String> = positions
            .iter()
            .filter(|(_, pos)| !pos.has_tp() && !pos.has_sl())
            .map(|(market, _)| market.clone())
            .collect();
        result.sort();
        result
    }

    pub fn unprotected_exposure_usd(&self, subaccount: &str) -> f64 {
        let positions = self.state.positions(subaccount);
        positions
            .iter()
            .filter(|(_, pos)| !pos.has_tp() && !pos.has_sl())
            .map(|(market, pos)| {
                let mark = self
                    .state
                    .mark_price(market)
                    .unwrap_or(pos.entry_price);
                (pos.size * mark).abs()
            })
            .sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{AccountOverview, MarketPrice, UserPosition};

    fn make_position(
        market: &str,
        size: f64,
        entry_price: f64,
        liq_price: f64,
    ) -> UserPosition {
        UserPosition {
            market: market.into(),
            user: "0xuser".into(),
            size,
            user_leverage: 10.0,
            entry_price,
            is_isolated: false,
            unrealized_funding: 0.0,
            estimated_liquidation_price: liq_price,
            tp_order_id: None,
            tp_trigger_price: None,
            tp_limit_price: None,
            sl_order_id: None,
            sl_trigger_price: None,
            sl_limit_price: None,
            has_fixed_sized_tpsls: false,
        }
    }

    fn make_protected_position(
        market: &str,
        size: f64,
        entry_price: f64,
        liq_price: f64,
    ) -> UserPosition {
        let mut pos = make_position(market, size, entry_price, liq_price);
        pos.tp_order_id = Some("tp_001".into());
        pos.tp_trigger_price = Some(entry_price * 1.1);
        pos.sl_order_id = Some("sl_001".into());
        pos.sl_trigger_price = Some(entry_price * 0.9);
        pos
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
    fn long_liquidation_distance() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_position("BTC-USD", 1.0, 50000.0, 40000.0),
        );
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));

        let risk = RiskMonitor::new(&mgr);
        let est = risk.liquidation_distance("sub1", "BTC-USD").unwrap();
        assert!((est.current_price - 50000.0).abs() < 0.01);
        assert!((est.liquidation_price - 40000.0).abs() < 0.01);
        assert!((est.distance_usd - 10000.0).abs() < 0.01);
        assert!((est.distance_pct - 20.0).abs() < 0.01);
    }

    #[test]
    fn short_liquidation_distance() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "ETH-USD",
            make_position("ETH-USD", -5.0, 3000.0, 3600.0),
        );
        mgr.merge_price("ETH-USD", make_price("ETH-USD", 3000.0));

        let risk = RiskMonitor::new(&mgr);
        let est = risk.liquidation_distance("sub1", "ETH-USD").unwrap();
        assert!((est.distance_usd - 600.0).abs() < 0.01);
        assert!((est.distance_pct - 20.0).abs() < 0.01);
    }

    #[test]
    fn no_liquidation_distance_when_liq_price_zero() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_position("BTC-USD", 1.0, 50000.0, 0.0),
        );
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));

        let risk = RiskMonitor::new(&mgr);
        assert!(risk.liquidation_distance("sub1", "BTC-USD").is_none());
    }

    #[test]
    fn min_liquidation_distance_picks_closest() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_position("BTC-USD", 1.0, 50000.0, 40000.0),
        );
        mgr.merge_position(
            "sub1",
            "ETH-USD",
            make_position("ETH-USD", -5.0, 3000.0, 3300.0),
        );
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));
        mgr.merge_price("ETH-USD", make_price("ETH-USD", 3000.0));

        let risk = RiskMonitor::new(&mgr);
        let min = risk.min_liquidation_distance("sub1").unwrap();
        // ETH: 300/3000 = 10%, BTC: 10000/50000 = 20% → ETH is closer
        assert!((min.distance_pct - 10.0).abs() < 0.01);
    }

    #[test]
    fn margin_ok_no_warning() {
        let mgr = PositionStateManager::new();
        mgr.merge_overview(make_overview(100_000.0, 30_000.0), "sub1");

        let risk = RiskMonitor::new(&mgr);
        assert!(risk.margin_warning("sub1").is_none());
    }

    #[test]
    fn margin_warning_level() {
        let mgr = PositionStateManager::new();
        mgr.merge_overview(make_overview(100_000.0, 60_000.0), "sub1");

        let risk = RiskMonitor::new(&mgr);
        let warning = risk.margin_warning("sub1").unwrap();
        assert_eq!(warning.level, "warning");
        assert!((warning.margin_usage_pct - 60.0).abs() < 0.01);
        assert!((warning.available_margin - 40_000.0).abs() < 0.01);
        assert!((warning.equity - 100_000.0).abs() < 0.01);
    }

    #[test]
    fn margin_critical_level() {
        let mgr = PositionStateManager::new();
        mgr.merge_overview(make_overview(100_000.0, 80_000.0), "sub1");

        let risk = RiskMonitor::new(&mgr);
        let warning = risk.margin_warning("sub1").unwrap();
        assert_eq!(warning.level, "critical");
        assert!((warning.margin_usage_pct - 80.0).abs() < 0.01);
    }

    #[test]
    fn margin_warning_none_for_unknown_subaccount() {
        let mgr = PositionStateManager::new();
        let risk = RiskMonitor::new(&mgr);
        assert!(risk.margin_warning("unknown").is_none());
    }

    #[test]
    fn positions_without_tp_sl() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_protected_position("BTC-USD", 1.0, 50000.0, 40000.0),
        );
        mgr.merge_position(
            "sub1",
            "ETH-USD",
            make_position("ETH-USD", 10.0, 3000.0, 2400.0),
        );
        mgr.merge_position(
            "sub1",
            "SOL-USD",
            make_position("SOL-USD", -50.0, 100.0, 120.0),
        );

        let risk = RiskMonitor::new(&mgr);
        let unprotected = risk.positions_without_tp_sl("sub1");
        assert_eq!(unprotected, vec!["ETH-USD", "SOL-USD"]);
    }

    #[test]
    fn unprotected_exposure_usd() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_protected_position("BTC-USD", 1.0, 50000.0, 40000.0),
        );
        mgr.merge_position(
            "sub1",
            "ETH-USD",
            make_position("ETH-USD", 10.0, 3000.0, 2400.0),
        );
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));
        mgr.merge_price("ETH-USD", make_price("ETH-USD", 3000.0));

        let risk = RiskMonitor::new(&mgr);
        // Only ETH is unprotected: |10 * 3000| = 30000
        assert!((risk.unprotected_exposure_usd("sub1") - 30000.0).abs() < 0.01);
    }

    #[test]
    fn unprotected_exposure_zero_when_all_protected() {
        let mgr = PositionStateManager::new();
        mgr.merge_position(
            "sub1",
            "BTC-USD",
            make_protected_position("BTC-USD", 1.0, 50000.0, 40000.0),
        );
        mgr.merge_price("BTC-USD", make_price("BTC-USD", 50000.0));

        let risk = RiskMonitor::new(&mgr);
        assert!((risk.unprotected_exposure_usd("sub1")).abs() < 0.01);
    }
}
