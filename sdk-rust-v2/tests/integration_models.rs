//! Integration tests for the v2 SDK models.
//!
//! These tests exercise the public API surface from the perspective of an
//! external consumer (a trading bot crate) — verifying that re-exports,
//! serialization, and computed methods all work end-to-end through the
//! crate's public interface.

use decibel_sdk_v2::*;

// ---------------------------------------------------------------------------
// Config integration
// ---------------------------------------------------------------------------

#[test]
fn mainnet_and_testnet_are_different_networks() {
    let mn = mainnet_config();
    let tn = testnet_config();
    assert_ne!(mn.network, tn.network);
    assert_ne!(mn.fullnode_url, tn.fullnode_url);
}

#[test]
fn config_survives_json_roundtrip() {
    let cfg = mainnet_config();
    let json = serde_json::to_string_pretty(&cfg).unwrap();
    let restored: DecibelConfig = serde_json::from_str(&json).unwrap();
    assert_eq!(restored.network, Network::Mainnet);
    assert_eq!(restored.compat_version, "v0.4");
}

// ---------------------------------------------------------------------------
// Enum integration — wire format correctness
// ---------------------------------------------------------------------------

#[test]
fn time_in_force_integers_on_wire() {
    assert_eq!(serde_json::to_value(TimeInForce::GoodTillCanceled).unwrap(), 0);
    assert_eq!(serde_json::to_value(TimeInForce::PostOnly).unwrap(), 1);
    assert_eq!(serde_json::to_value(TimeInForce::ImmediateOrCancel).unwrap(), 2);
}

#[test]
fn candlestick_interval_strings_on_wire() {
    assert_eq!(
        serde_json::to_value(CandlestickInterval::OneMinute).unwrap(),
        "1m"
    );
    assert_eq!(
        serde_json::to_value(CandlestickInterval::OneMonth).unwrap(),
        "1mo"
    );
}

#[test]
fn depth_aggregation_integers_on_wire() {
    assert_eq!(serde_json::to_value(DepthAggregationLevel::L1).unwrap(), 1);
    assert_eq!(serde_json::to_value(DepthAggregationLevel::L1000).unwrap(), 1000);
}

#[test]
fn sort_direction_uppercase_strings() {
    assert_eq!(serde_json::to_value(SortDirection::Ascending).unwrap(), "ASC");
    assert_eq!(serde_json::to_value(SortDirection::Descending).unwrap(), "DESC");
}

// ---------------------------------------------------------------------------
// Market data integration — realistic BTC scenario
// ---------------------------------------------------------------------------

#[test]
fn btc_market_depth_full_pipeline() {
    let depth_json = r#"{
        "market": "BTC-USD",
        "bids": [
            {"price": 67450.0, "size": 2.5},
            {"price": 67440.0, "size": 5.0},
            {"price": 67420.0, "size": 10.0}
        ],
        "asks": [
            {"price": 67460.0, "size": 1.8},
            {"price": 67470.0, "size": 3.2},
            {"price": 67500.0, "size": 8.0}
        ],
        "unix_ms": 1710000000000
    }"#;

    let depth: MarketDepth = serde_json::from_str(depth_json).unwrap();

    assert!((depth.best_bid().unwrap() - 67_450.0).abs() < 1e-6);
    assert!((depth.best_ask().unwrap() - 67_460.0).abs() < 1e-6);
    assert!((depth.spread().unwrap() - 10.0).abs() < 1e-6);
    assert!((depth.mid_price().unwrap() - 67_455.0).abs() < 1e-6);

    let imb = depth.imbalance().unwrap();
    assert!(imb > 0.0, "more bid volume → positive imbalance");

    let bid_depth = depth.bid_depth_at(0.05);
    assert!(bid_depth >= 2.5);
}

#[test]
fn candlestick_wire_alias_roundtrip() {
    let wire_json = r#"{"t":1710000000000,"T":1710000060000,"o":67400,"h":67500,"l":67350,"c":67480,"v":456.7,"i":"1m"}"#;
    let candle: Candlestick = serde_json::from_str(wire_json).unwrap();
    assert!(candle.is_bullish());
    assert!(candle.body_pct() > 0.0);
    assert!(candle.range_pct() > 0.0);

    let re_serialized = serde_json::to_string(&candle).unwrap();
    let restored: Candlestick = serde_json::from_str(&re_serialized).unwrap();
    assert!((restored.open - candle.open).abs() < 1e-10);
}

// ---------------------------------------------------------------------------
// Account integration — realistic account state
// ---------------------------------------------------------------------------

#[test]
fn account_risk_metrics_pipeline() {
    let json = r#"{
        "perp_equity_balance": 250000.0,
        "unrealized_pnl": 5000.0,
        "unrealized_funding_cost": -120.0,
        "cross_margin_ratio": 0.08,
        "maintenance_margin": 12000.0,
        "cross_account_leverage_ratio": 4.2,
        "cross_account_position": 1050000.0,
        "total_margin": 50000.0,
        "usdc_cross_withdrawable_balance": 190000.0,
        "usdc_isolated_withdrawable_balance": 10000.0,
        "volume": 5000000.0,
        "net_deposits": 200000.0,
        "realized_pnl": 45000.0,
        "liquidation_fees_paid": 0.0,
        "liquidation_losses": 0.0,
        "all_time_return": 25.0,
        "pnl_90d": 15000.0,
        "sharpe_ratio": 2.1,
        "max_drawdown": -5.5,
        "weekly_win_rate_12w": 0.83,
        "average_cash_position": 100000.0,
        "average_leverage": 3.5
    }"#;

    let acc: AccountOverview = serde_json::from_str(json).unwrap();

    let usage = acc.margin_usage_pct();
    assert!((usage - 20.0).abs() < 1e-6);

    let buf_usd = acc.liquidation_buffer_usd();
    assert!((buf_usd - 238_000.0).abs() < 1e-6);

    assert!(!acc.is_liquidation_warning(50.0));

    let total = acc.total_withdrawable();
    assert!((total - 200_000.0).abs() < 1e-6);
}

#[test]
fn position_pnl_with_realistic_btc_data() {
    let json = r#"{
        "market": "0xbtc",
        "user": "0xuser",
        "size": 0.5,
        "user_leverage": 10.0,
        "entry_price": 65000.0,
        "is_isolated": false,
        "unrealized_funding": -12.5,
        "estimated_liquidation_price": 58500.0,
        "tp_order_id": "tp1",
        "tp_trigger_price": 72000.0,
        "tp_limit_price": 71900.0,
        "sl_order_id": "sl1",
        "sl_trigger_price": 62000.0,
        "sl_limit_price": 61900.0,
        "has_fixed_sized_tpsls": false
    }"#;

    let pos: UserPosition = serde_json::from_str(json).unwrap();
    assert!(pos.is_long());
    assert!(pos.has_protection());

    let mark = 67_000.0;
    let pnl = pos.unrealized_pnl(mark);
    assert!((pnl - 1000.0).abs() < 1e-6);

    let notional = pos.notional(mark);
    assert!((notional - 33_500.0).abs() < 1e-6);

    let liq_dist = pos.liquidation_distance_pct(mark);
    assert!(liq_dist > 10.0);
}

// ---------------------------------------------------------------------------
// Common models integration
// ---------------------------------------------------------------------------

#[test]
fn paginated_response_with_market_prices() {
    let resp = PaginatedResponse {
        items: vec![
            MarketPrice {
                market: "BTC-USD".into(),
                mark_px: 67000.0,
                mid_px: 66999.0,
                oracle_px: 67001.0,
                funding_rate_bps: 0.3,
                is_funding_positive: true,
                open_interest: 500_000_000.0,
                transaction_unix_ms: 1_710_000_000_000,
            },
            MarketPrice {
                market: "ETH-USD".into(),
                mark_px: 3500.0,
                mid_px: 3499.5,
                oracle_px: 3500.5,
                funding_rate_bps: -0.1,
                is_funding_positive: false,
                open_interest: 200_000_000.0,
                transaction_unix_ms: 1_710_000_000_000,
            },
        ],
        total_count: 2,
    };

    let json = serde_json::to_string(&resp).unwrap();
    let restored: PaginatedResponse<MarketPrice> = serde_json::from_str(&json).unwrap();
    assert_eq!(restored.items.len(), 2);
    assert_eq!(restored.total_count, 2);
    assert_eq!(restored.items[0].funding_direction(), "longs_pay");
    assert_eq!(restored.items[1].funding_direction(), "shorts_pay");
}

#[test]
fn order_status_parse_from_various_wire_formats() {
    assert!(OrderStatusType::parse("Filled").is_success());
    assert!(OrderStatusType::parse("FILLED").is_final());
    assert!(OrderStatusType::parse("partially_filled").is_success());
    assert!(!OrderStatusType::parse("acknowledged").is_final());
    assert!(OrderStatusType::parse("garbage").is_final() == false);
}
