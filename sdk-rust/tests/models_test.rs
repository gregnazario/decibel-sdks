use decibel_sdk::models::*;

// BDD: Model Serialization/Deserialization Tests

#[test]
fn given_market_config_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "market_addr": "0xabc123",
        "market_name": "BTC-USD",
        "sz_decimals": 8,
        "px_decimals": 2,
        "max_leverage": 50.0,
        "min_size": 0.001,
        "lot_size": 0.001,
        "tick_size": 0.1,
        "max_open_interest": 1000000.0,
        "margin_call_fee_pct": 0.5,
        "taker_in_next_block": false
    }"#;

    let config: PerpMarketConfig = serde_json::from_str(json).unwrap();
    assert_eq!(config.market_name, "BTC-USD");
    assert_eq!(config.market_addr, "0xabc123");
    assert_eq!(config.sz_decimals, 8);
    assert_eq!(config.px_decimals, 2);
    assert_eq!(config.max_leverage, 50.0);
    assert!(!config.taker_in_next_block);
}

#[test]
fn given_market_depth_json_when_deserialized_then_bids_and_asks_present() {
    let json = r#"{
        "market": "BTC-USD",
        "bids": [{"price": 45100.0, "size": 2.5}, {"price": 45050.0, "size": 1.0}],
        "asks": [{"price": 45150.0, "size": 3.0}, {"price": 45200.0, "size": 0.5}],
        "unix_ms": 1708000000000
    }"#;

    let depth: MarketDepth = serde_json::from_str(json).unwrap();
    assert_eq!(depth.market, "BTC-USD");
    assert_eq!(depth.bids.len(), 2);
    assert_eq!(depth.asks.len(), 2);
    assert_eq!(depth.bids[0].price, 45100.0);
    assert_eq!(depth.asks[0].size, 3.0);
    assert_eq!(depth.unix_ms, 1708000000000);
}

#[test]
fn given_market_price_json_when_deserialized_then_all_prices_present() {
    let json = r#"{
        "market": "ETH-USD",
        "mark_px": 3000.5,
        "mid_px": 3000.0,
        "oracle_px": 3001.0,
        "funding_rate_bps": 0.0123,
        "is_funding_positive": true,
        "open_interest": 500000.0,
        "transaction_unix_ms": 1708000000000
    }"#;

    let price: MarketPrice = serde_json::from_str(json).unwrap();
    assert_eq!(price.market, "ETH-USD");
    assert_eq!(price.mark_px, 3000.5);
    assert!(price.is_funding_positive);
}

#[test]
fn given_candlestick_json_when_deserialized_then_ohlcv_present() {
    let json = r#"{
        "T": 1708000060000,
        "c": 45200.0,
        "h": 45300.0,
        "i": "1m",
        "l": 45100.0,
        "o": 45150.0,
        "t": 1708000000000,
        "v": 125.5
    }"#;

    let candle: Candlestick = serde_json::from_str(json).unwrap();
    assert_eq!(candle.o, 45150.0);
    assert_eq!(candle.h, 45300.0);
    assert_eq!(candle.l, 45100.0);
    assert_eq!(candle.c, 45200.0);
    assert_eq!(candle.v, 125.5);
    assert_eq!(candle.i, "1m");
}

#[test]
fn given_account_overview_json_when_deserialized_then_balances_present() {
    let json = r#"{
        "perp_equity_balance": 10000.0,
        "unrealized_pnl": 500.0,
        "unrealized_funding_cost": -10.5,
        "cross_margin_ratio": 0.15,
        "maintenance_margin": 1000.0,
        "cross_account_leverage_ratio": 5.0,
        "volume": 250000.0,
        "net_deposits": 8000.0,
        "all_time_return": 0.25,
        "pnl_90d": 2000.0,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.1,
        "weekly_win_rate_12w": 0.6,
        "average_cash_position": 5000.0,
        "average_leverage": 3.0,
        "cross_account_position": 7000.0,
        "total_margin": 2000.0,
        "usdc_cross_withdrawable_balance": 3000.0,
        "usdc_isolated_withdrawable_balance": 1000.0,
        "realized_pnl": 1500.0,
        "liquidation_fees_paid": 50.0,
        "liquidation_losses": 200.0
    }"#;

    let overview: AccountOverview = serde_json::from_str(json).unwrap();
    assert_eq!(overview.perp_equity_balance, 10000.0);
    assert_eq!(overview.unrealized_pnl, 500.0);
    assert_eq!(overview.cross_account_leverage_ratio, Some(5.0));
    assert_eq!(overview.volume, Some(250000.0));
}

#[test]
fn given_account_overview_with_nulls_when_deserialized_then_optional_fields_none() {
    let json = r#"{
        "perp_equity_balance": 10000.0,
        "unrealized_pnl": 0.0,
        "unrealized_funding_cost": 0.0,
        "cross_margin_ratio": 0.0,
        "maintenance_margin": 0.0,
        "cross_account_leverage_ratio": null,
        "volume": null,
        "net_deposits": null,
        "all_time_return": null,
        "pnl_90d": null,
        "sharpe_ratio": null,
        "max_drawdown": null,
        "weekly_win_rate_12w": null,
        "average_cash_position": null,
        "average_leverage": null,
        "cross_account_position": 0.0,
        "total_margin": 0.0,
        "usdc_cross_withdrawable_balance": 0.0,
        "usdc_isolated_withdrawable_balance": 0.0,
        "realized_pnl": null,
        "liquidation_fees_paid": null,
        "liquidation_losses": null
    }"#;

    let overview: AccountOverview = serde_json::from_str(json).unwrap();
    assert_eq!(overview.cross_account_leverage_ratio, None);
    assert_eq!(overview.volume, None);
    assert_eq!(overview.sharpe_ratio, None);
}

#[test]
fn given_user_position_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "market": "0xmarket",
        "user": "0xuser",
        "size": 1.5,
        "user_leverage": 10.0,
        "entry_price": 45000.0,
        "is_isolated": false,
        "unrealized_funding": -5.0,
        "estimated_liquidation_price": 40000.0,
        "tp_order_id": "123",
        "tp_trigger_price": 50000.0,
        "tp_limit_price": 49500.0,
        "sl_order_id": "456",
        "sl_trigger_price": 42000.0,
        "sl_limit_price": 42500.0,
        "has_fixed_sized_tpsls": true
    }"#;

    let pos: UserPosition = serde_json::from_str(json).unwrap();
    assert_eq!(pos.size, 1.5);
    assert!(!pos.is_isolated);
    assert_eq!(pos.tp_order_id, Some("123".into()));
    assert_eq!(pos.sl_trigger_price, Some(42000.0));
    assert!(pos.has_fixed_sized_tpsls);
}

#[test]
fn given_user_position_without_tpsl_when_deserialized_then_optional_fields_none() {
    let json = r#"{
        "market": "0xmarket",
        "user": "0xuser",
        "size": -2.0,
        "user_leverage": 5.0,
        "entry_price": 3000.0,
        "is_isolated": true,
        "unrealized_funding": 0.0,
        "estimated_liquidation_price": 3500.0,
        "tp_order_id": null,
        "tp_trigger_price": null,
        "tp_limit_price": null,
        "sl_order_id": null,
        "sl_trigger_price": null,
        "sl_limit_price": null,
        "has_fixed_sized_tpsls": false
    }"#;

    let pos: UserPosition = serde_json::from_str(json).unwrap();
    assert_eq!(pos.size, -2.0);
    assert!(pos.is_isolated);
    assert_eq!(pos.tp_order_id, None);
    assert_eq!(pos.sl_order_id, None);
}

#[test]
fn given_open_order_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "market": "0xmarket",
        "order_id": "12345",
        "client_order_id": "my-order-1",
        "price": 45000.0,
        "orig_size": 1.0,
        "remaining_size": 0.5,
        "is_buy": true,
        "time_in_force": "GoodTillCanceled",
        "is_reduce_only": false,
        "status": "Acknowledged",
        "transaction_unix_ms": 1708000000000,
        "transaction_version": 100
    }"#;

    let order: UserOpenOrder = serde_json::from_str(json).unwrap();
    assert_eq!(order.order_id, "12345");
    assert_eq!(order.client_order_id, Some("my-order-1".into()));
    assert!(order.is_buy);
    assert_eq!(order.remaining_size, 0.5);
}

#[test]
fn given_vault_json_when_deserialized_then_nullable_fields_handled() {
    let json = r#"{
        "address": "0xvault",
        "name": "Alpha Vault",
        "description": "A great vault",
        "manager": "0xmanager",
        "status": "Active",
        "created_at": 1700000000000,
        "tvl": 500000.0,
        "volume": 1000000.0,
        "volume_30d": null,
        "all_time_pnl": 50000.0,
        "net_deposits": 400000.0,
        "all_time_return": 0.125,
        "past_month_return": 0.03,
        "sharpe_ratio": 2.1,
        "max_drawdown": -0.05,
        "weekly_win_rate_12w": 0.75,
        "profit_share": 0.2,
        "pnl_90d": 30000.0,
        "manager_cash_pct": 0.1,
        "average_leverage": 2.0,
        "depositors": 42,
        "perp_equity": 450000.0,
        "vault_type": "user",
        "social_links": ["https://twitter.com/vault"]
    }"#;

    let vault: Vault = serde_json::from_str(json).unwrap();
    assert_eq!(vault.name, "Alpha Vault");
    assert_eq!(vault.vault_type, Some(VaultType::User));
    assert_eq!(vault.depositors, Some(42));
    assert_eq!(vault.volume_30d, None);
}

#[test]
fn given_user_subaccount_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "subaccount_address": "0xsub",
        "primary_account_address": "0xowner",
        "is_primary": true,
        "custom_label": "Main Trading",
        "is_active": true
    }"#;

    let sub: UserSubaccount = serde_json::from_str(json).unwrap();
    assert_eq!(sub.subaccount_address, "0xsub");
    assert!(sub.is_primary);
    assert_eq!(sub.custom_label, Some("Main Trading".into()));
}

#[test]
fn given_paginated_response_json_when_deserialized_then_items_and_count_present() {
    let json = r#"{
        "items": [
            {"rank": 1, "account": "0x1", "account_value": 100000.0, "realized_pnl": 5000.0, "roi": 0.05, "volume": 500000.0},
            {"rank": 2, "account": "0x2", "account_value": 90000.0, "realized_pnl": 4000.0, "roi": 0.044, "volume": 400000.0}
        ],
        "total_count": 100
    }"#;

    let resp: PaginatedResponse<LeaderboardItem> = serde_json::from_str(json).unwrap();
    assert_eq!(resp.items.len(), 2);
    assert_eq!(resp.total_count, 100);
    assert_eq!(resp.items[0].rank, 1);
}

// --- Enum Tests ---

#[test]
fn given_time_in_force_when_converting_to_u8_then_correct_values() {
    assert_eq!(TimeInForce::GoodTillCanceled.as_u8(), 0);
    assert_eq!(TimeInForce::PostOnly.as_u8(), 1);
    assert_eq!(TimeInForce::ImmediateOrCancel.as_u8(), 2);
}

#[test]
fn given_u8_when_converting_to_time_in_force_then_correct_variant() {
    assert_eq!(TimeInForce::from_u8(0), Some(TimeInForce::GoodTillCanceled));
    assert_eq!(TimeInForce::from_u8(1), Some(TimeInForce::PostOnly));
    assert_eq!(TimeInForce::from_u8(2), Some(TimeInForce::ImmediateOrCancel));
    assert_eq!(TimeInForce::from_u8(3), None);
}

#[test]
fn given_candlestick_interval_when_converting_to_str_then_correct_values() {
    assert_eq!(CandlestickInterval::OneMinute.as_str(), "1m");
    assert_eq!(CandlestickInterval::FiveMinutes.as_str(), "5m");
    assert_eq!(CandlestickInterval::FifteenMinutes.as_str(), "15m");
    assert_eq!(CandlestickInterval::ThirtyMinutes.as_str(), "30m");
    assert_eq!(CandlestickInterval::OneHour.as_str(), "1h");
    assert_eq!(CandlestickInterval::TwoHours.as_str(), "2h");
    assert_eq!(CandlestickInterval::FourHours.as_str(), "4h");
    assert_eq!(CandlestickInterval::EightHours.as_str(), "8h");
    assert_eq!(CandlestickInterval::TwelveHours.as_str(), "12h");
    assert_eq!(CandlestickInterval::OneDay.as_str(), "1d");
    assert_eq!(CandlestickInterval::ThreeDays.as_str(), "3d");
    assert_eq!(CandlestickInterval::OneWeek.as_str(), "1w");
    assert_eq!(CandlestickInterval::OneMonth.as_str(), "1mo");
}

#[test]
fn given_volume_window_when_converting_to_str_then_correct_values() {
    assert_eq!(VolumeWindow::SevenDays.as_str(), "7d");
    assert_eq!(VolumeWindow::FourteenDays.as_str(), "14d");
    assert_eq!(VolumeWindow::ThirtyDays.as_str(), "30d");
    assert_eq!(VolumeWindow::NinetyDays.as_str(), "90d");
}

#[test]
fn given_order_status_type_when_checking_success_then_correct() {
    assert!(OrderStatusType::Acknowledged.is_success());
    assert!(OrderStatusType::Filled.is_success());
    assert!(!OrderStatusType::Cancelled.is_success());
    assert!(!OrderStatusType::Rejected.is_success());
}

#[test]
fn given_order_status_type_when_checking_failure_then_correct() {
    assert!(OrderStatusType::Cancelled.is_failure());
    assert!(OrderStatusType::Rejected.is_failure());
    assert!(!OrderStatusType::Acknowledged.is_failure());
}

#[test]
fn given_order_status_type_when_checking_final_then_correct() {
    assert!(OrderStatusType::Filled.is_final());
    assert!(OrderStatusType::Cancelled.is_final());
    assert!(!OrderStatusType::Unknown.is_final());
}

#[test]
fn given_status_string_when_parsing_then_correct_variant() {
    assert_eq!(OrderStatusType::from_str("Acknowledged"), OrderStatusType::Acknowledged);
    assert_eq!(OrderStatusType::from_str("Filled"), OrderStatusType::Filled);
    assert_eq!(OrderStatusType::from_str("Cancelled"), OrderStatusType::Cancelled);
    assert_eq!(OrderStatusType::from_str("Canceled"), OrderStatusType::Cancelled);
    assert_eq!(OrderStatusType::from_str("Rejected"), OrderStatusType::Rejected);
    assert_eq!(OrderStatusType::from_str("garbage"), OrderStatusType::Unknown);
}

#[test]
fn given_place_order_result_success_when_created_then_fields_correct() {
    let result = PlaceOrderResult::success(Some("123".into()), "0xhash".into());
    assert!(result.success);
    assert_eq!(result.order_id, Some("123".into()));
    assert_eq!(result.transaction_hash, Some("0xhash".into()));
    assert_eq!(result.error, None);
}

#[test]
fn given_place_order_result_failure_when_created_then_fields_correct() {
    let result = PlaceOrderResult::failure("Insufficient balance".into());
    assert!(!result.success);
    assert_eq!(result.order_id, None);
    assert_eq!(result.transaction_hash, None);
    assert_eq!(result.error, Some("Insufficient balance".into()));
}

#[test]
fn given_market_depth_aggregation_sizes_when_listed_then_all_present() {
    let sizes = MarketDepthAggregationSize::all();
    assert_eq!(sizes.len(), 6);
}

#[test]
fn given_delegation_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "delegated_account": "0xdelegate",
        "permission_type": "trading",
        "expiration_time_s": 1700000000
    }"#;

    let delegation: Delegation = serde_json::from_str(json).unwrap();
    assert_eq!(delegation.delegated_account, "0xdelegate");
    assert_eq!(delegation.expiration_time_s, Some(1700000000));
}

#[test]
fn given_trade_history_item_json_when_deserialized_then_all_fields_present() {
    let json = r#"{
        "account": "0xaccount",
        "market": "0xmarket",
        "action": "OpenLong",
        "size": 1.5,
        "price": 45000.0,
        "is_profit": true,
        "realized_pnl_amount": 500.0,
        "is_funding_positive": true,
        "realized_funding_amount": 10.0,
        "is_rebate": false,
        "fee_amount": 5.0,
        "transaction_unix_ms": 1708000000000,
        "transaction_version": 100
    }"#;

    let trade: UserTradeHistoryItem = serde_json::from_str(json).unwrap();
    assert_eq!(trade.action, "OpenLong");
    assert!(trade.is_profit);
    assert_eq!(trade.realized_pnl_amount, 500.0);
}

#[test]
fn given_ws_subscribe_request_when_serialized_then_correct_format() {
    let req = WsSubscribeRequest::subscribe("marketPrice:BTC-USD");
    let json = serde_json::to_string(&req).unwrap();
    assert!(json.contains("\"method\":\"subscribe\""));
    assert!(json.contains("\"subscription\":\"marketPrice:BTC-USD\""));
}

#[test]
fn given_ws_unsubscribe_request_when_serialized_then_correct_format() {
    let req = WsSubscribeRequest::unsubscribe("marketPrice:BTC-USD");
    let json = serde_json::to_string(&req).unwrap();
    assert!(json.contains("\"method\":\"unsubscribe\""));
}
