use decibel_sdk::models::*;

// Extended model tests covering serialization edge cases

#[test]
fn test_candlestick_interval_serde_roundtrip() {
    let intervals = vec![
        CandlestickInterval::OneMinute,
        CandlestickInterval::FiveMinutes,
        CandlestickInterval::FifteenMinutes,
        CandlestickInterval::ThirtyMinutes,
        CandlestickInterval::OneHour,
        CandlestickInterval::TwoHours,
        CandlestickInterval::FourHours,
        CandlestickInterval::EightHours,
        CandlestickInterval::TwelveHours,
        CandlestickInterval::OneDay,
        CandlestickInterval::ThreeDays,
        CandlestickInterval::OneWeek,
        CandlestickInterval::OneMonth,
    ];
    for interval in intervals {
        let json = serde_json::to_string(&interval).unwrap();
        let deserialized: CandlestickInterval = serde_json::from_str(&json).unwrap();
        assert_eq!(interval, deserialized);
    }
}

#[test]
fn test_time_in_force_serde_roundtrip() {
    let values = vec![
        TimeInForce::GoodTillCanceled,
        TimeInForce::PostOnly,
        TimeInForce::ImmediateOrCancel,
    ];
    for val in values {
        let json = serde_json::to_string(&val).unwrap();
        let deserialized: TimeInForce = serde_json::from_str(&json).unwrap();
        assert_eq!(val, deserialized);
    }
}

#[test]
fn test_volume_window_serde_roundtrip() {
    let windows = vec![
        VolumeWindow::SevenDays,
        VolumeWindow::FourteenDays,
        VolumeWindow::ThirtyDays,
        VolumeWindow::NinetyDays,
    ];
    for w in windows {
        let json = serde_json::to_string(&w).unwrap();
        let deserialized: VolumeWindow = serde_json::from_str(&json).unwrap();
        assert_eq!(w, deserialized);
    }
}

#[test]
fn test_sort_direction_serde() {
    let asc: SortDirection = serde_json::from_str("\"ASC\"").unwrap();
    assert_eq!(asc, SortDirection::Ascending);
    let desc: SortDirection = serde_json::from_str("\"DESC\"").unwrap();
    assert_eq!(desc, SortDirection::Descending);
}

#[test]
fn test_twap_status_serde() {
    let activated: TwapStatus = serde_json::from_str("\"Activated\"").unwrap();
    assert_eq!(activated, TwapStatus::Activated);
    let finished: TwapStatus = serde_json::from_str("\"Finished\"").unwrap();
    assert_eq!(finished, TwapStatus::Finished);
    let cancelled: TwapStatus = serde_json::from_str("\"Cancelled\"").unwrap();
    assert_eq!(cancelled, TwapStatus::Cancelled);
}

#[test]
fn test_trade_action_serde() {
    let actions = vec![
        TradeAction::OpenLong,
        TradeAction::CloseLong,
        TradeAction::OpenShort,
        TradeAction::CloseShort,
        TradeAction::Net,
    ];
    for action in actions {
        let json = serde_json::to_string(&action).unwrap();
        let deserialized: TradeAction = serde_json::from_str(&json).unwrap();
        assert_eq!(action, deserialized);
    }
}

#[test]
fn test_vault_type_serde() {
    let user: VaultType = serde_json::from_str("\"user\"").unwrap();
    assert_eq!(user, VaultType::User);
    let protocol: VaultType = serde_json::from_str("\"protocol\"").unwrap();
    assert_eq!(protocol, VaultType::Protocol);
}

#[test]
fn test_order_status_type_all_variants() {
    assert_eq!(OrderStatusType::from_str("Acknowledged"), OrderStatusType::Acknowledged);
    assert_eq!(OrderStatusType::from_str("Filled"), OrderStatusType::Filled);
    assert_eq!(OrderStatusType::from_str("Cancelled"), OrderStatusType::Cancelled);
    assert_eq!(OrderStatusType::from_str("Canceled"), OrderStatusType::Cancelled);
    assert_eq!(OrderStatusType::from_str("Rejected"), OrderStatusType::Rejected);
    assert_eq!(OrderStatusType::from_str("SomethingElse"), OrderStatusType::Unknown);
    assert_eq!(OrderStatusType::from_str(""), OrderStatusType::Unknown);
}

#[test]
fn test_paginated_response_serde() {
    let json = r#"{"items":[{"rank":1,"account":"0x1","account_value":100.0,"realized_pnl":50.0,"roi":0.5,"volume":1000.0}],"total_count":42}"#;
    let resp: PaginatedResponse<LeaderboardItem> = serde_json::from_str(json).unwrap();
    assert_eq!(resp.total_count, 42);
    assert_eq!(resp.items.len(), 1);
}

#[test]
fn test_twap_order_result_serde() {
    let result = TwapOrderResult {
        success: true,
        order_id: Some("twap-123".into()),
        transaction_hash: "0xhash".into(),
    };
    let json = serde_json::to_string(&result).unwrap();
    let deserialized: TwapOrderResult = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.success, true);
    assert_eq!(deserialized.order_id, Some("twap-123".into()));
}

#[test]
fn test_place_order_result_serde_roundtrip() {
    let result = PlaceOrderResult::success(Some("ord-1".into()), "0xtx".into());
    let json = serde_json::to_string(&result).unwrap();
    let deserialized: PlaceOrderResult = serde_json::from_str(&json).unwrap();
    assert!(deserialized.success);
    assert_eq!(deserialized.order_id, Some("ord-1".into()));
}

#[test]
fn test_order_event_deserialization() {
    let json = r#"{
        "client_order_id": {"vec": []},
        "details": "filled",
        "is_bid": true,
        "is_taker": true,
        "market": "0xmarket",
        "metadata_bytes": "",
        "order_id": "12345",
        "orig_size": "1000000",
        "parent": "0xparent",
        "price": "45000000",
        "remaining_size": "0",
        "size_delta": "1000000",
        "status": {"__variant__": "Filled"},
        "time_in_force": {"__variant__": "GTC"},
        "trigger_condition": {"vec": []},
        "user": "0xuser"
    }"#;
    let event: OrderEvent = serde_json::from_str(json).unwrap();
    assert_eq!(event.order_id, "12345");
    assert!(event.is_bid);
    assert_eq!(event.user, "0xuser");
}

#[test]
fn test_perp_position_deserialization() {
    let json = r#"{
        "size": 1.5,
        "sz_decimals": 8,
        "entry_px": 45000.0,
        "max_leverage": 50.0,
        "is_long": true,
        "token_type": "BTC"
    }"#;
    let pos: PerpPosition = serde_json::from_str(json).unwrap();
    assert_eq!(pos.size, 1.5);
    assert!(pos.is_long);
}

#[test]
fn test_crossed_position_deserialization() {
    let json = r#"{"positions": []}"#;
    let pos: CrossedPosition = serde_json::from_str(json).unwrap();
    assert_eq!(pos.positions.len(), 0);
}

#[test]
fn test_vault_full_deserialization() {
    let json = r#"{
        "address": "0xvault",
        "name": "Test",
        "description": null,
        "manager": "0xmgr",
        "status": "Active",
        "created_at": 1700000000000,
        "tvl": null,
        "volume": null,
        "volume_30d": null,
        "all_time_pnl": null,
        "net_deposits": null,
        "all_time_return": null,
        "past_month_return": null,
        "sharpe_ratio": null,
        "max_drawdown": null,
        "weekly_win_rate_12w": null,
        "profit_share": null,
        "pnl_90d": null,
        "manager_cash_pct": null,
        "average_leverage": null,
        "depositors": null,
        "perp_equity": null,
        "vault_type": null,
        "social_links": null
    }"#;
    let vault: Vault = serde_json::from_str(json).unwrap();
    assert_eq!(vault.name, "Test");
    assert!(vault.tvl.is_none());
    assert!(vault.vault_type.is_none());
}

#[test]
fn test_vaults_response_deserialization() {
    let json = r#"{
        "items": [],
        "total_count": 0,
        "total_value_locked": 1000000.0,
        "total_volume": 5000000.0
    }"#;
    let resp: VaultsResponse = serde_json::from_str(json).unwrap();
    assert_eq!(resp.total_value_locked, 1000000.0);
}

#[test]
fn test_user_owned_vault_deserialization() {
    let json = r#"{
        "vault_address": "0xv",
        "vault_name": "V",
        "vault_share_symbol": "VLT",
        "status": "Active",
        "age_days": 30,
        "num_managers": 2,
        "tvl": 100000.0,
        "apr": 0.15,
        "manager_equity": null,
        "manager_stake": null
    }"#;
    let vault: UserOwnedVault = serde_json::from_str(json).unwrap();
    assert_eq!(vault.age_days, 30);
}

#[test]
fn test_market_trade_deserialization() {
    let json = r#"{"market":"BTC-USD","price":45000.0,"size":0.1,"is_buy":false,"unix_ms":1708000000000}"#;
    let trade: MarketTrade = serde_json::from_str(json).unwrap();
    assert!(!trade.is_buy);
}

#[test]
fn test_user_fund_history_item_deserialization() {
    let json = r#"{"amount":1000.0,"is_deposit":true,"transaction_unix_ms":1708000000000,"transaction_version":1}"#;
    let item: UserFundHistoryItem = serde_json::from_str(json).unwrap();
    assert!(item.is_deposit);
}

#[test]
fn test_user_active_twap_deserialization() {
    let json = r#"{
        "market":"0xm","is_buy":true,"order_id":"1","client_order_id":"c1",
        "is_reduce_only":false,"start_unix_ms":1000,"frequency_s":60,"duration_s":3600,
        "orig_size":10.0,"remaining_size":5.0,"status":"Activated",
        "transaction_unix_ms":1000,"transaction_version":1
    }"#;
    let twap: UserActiveTwap = serde_json::from_str(json).unwrap();
    assert_eq!(twap.frequency_s, 60);
}

#[test]
fn test_ws_account_overview_message() {
    let json = r#"{"account_overview":{"perp_equity_balance":1000.0,"unrealized_pnl":0.0,"unrealized_funding_cost":0.0,"cross_margin_ratio":0.0,"maintenance_margin":0.0,"cross_account_leverage_ratio":null,"volume":null,"net_deposits":null,"all_time_return":null,"pnl_90d":null,"sharpe_ratio":null,"max_drawdown":null,"weekly_win_rate_12w":null,"average_cash_position":null,"average_leverage":null,"cross_account_position":0.0,"total_margin":0.0,"usdc_cross_withdrawable_balance":0.0,"usdc_isolated_withdrawable_balance":0.0,"realized_pnl":null,"liquidation_fees_paid":null,"liquidation_losses":null}}"#;
    let msg: AccountOverviewWsMessage = serde_json::from_str(json).unwrap();
    assert_eq!(msg.account_overview.perp_equity_balance, 1000.0);
}

#[test]
fn test_ws_candlestick_message() {
    let json = r#"{"candle":{"T":100,"c":1.0,"h":2.0,"i":"1m","l":0.5,"o":0.8,"t":0,"v":10.0}}"#;
    let msg: CandlestickWsMessage = serde_json::from_str(json).unwrap();
    assert_eq!(msg.candle.c, 1.0);
}

#[test]
fn test_create_vault_args() {
    let args = CreateVaultArgs {
        vault_name: "Test".into(),
        vault_description: "Desc".into(),
        vault_social_links: vec![],
        vault_share_symbol: "TST".into(),
        vault_share_icon_uri: Some("https://icon.com".into()),
        vault_share_project_uri: None,
        fee_bps: 100,
        fee_interval_s: 86400,
        contribution_lockup_duration_s: 604800,
        initial_funding: 1000,
        accepts_contributions: true,
        delegate_to_creator: false,
        contribution_asset_type: Some("0xusdc".into()),
        subaccount_addr: Some("0xsub".into()),
    };
    assert_eq!(args.vault_name, "Test");
    assert_eq!(args.fee_bps, 100);
}

#[test]
fn test_activate_vault_args() {
    let args = ActivateVaultArgs {
        vault_address: "0xv".into(),
        additional_funding: Some(1000),
    };
    assert_eq!(args.vault_address, "0xv");
}

#[test]
fn test_deposit_to_vault_args() {
    let args = DepositToVaultArgs {
        vault_address: "0xv".into(),
        amount: 5000,
    };
    assert_eq!(args.amount, 5000);
}

#[test]
fn test_withdraw_from_vault_args() {
    let args = WithdrawFromVaultArgs {
        vault_address: "0xv".into(),
        shares: 100,
    };
    assert_eq!(args.shares, 100);
}
