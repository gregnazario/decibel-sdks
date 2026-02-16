use decibel_sdk::client::DecibelWriteClient;
use decibel_sdk::config::*;
use decibel_sdk::models::*;

fn test_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Custom,
        fullnode_url: "http://localhost:8080/v1".into(),
        trading_http_url: "http://localhost:3000".into(),
        trading_ws_url: "ws://localhost:3000/ws".into(),
        gas_station_url: None,
        gas_station_api_key: None,
        deployment: Deployment {
            package: "0xabc123".into(),
            usdc: "0xdef456".into(),
            testc: "".into(),
            perp_engine_global: "0x789012345678901234567890123456789012345678901234567890123456".into(),
        },
        chain_id: Some(4),
        compat_version: CompatVersion::V0_4,
    }
}

fn test_private_key() -> &'static str {
    "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}

fn test_address() -> &'static str {
    "0xaabbccdd00112233aabbccdd00112233aabbccdd00112233aabbccdd00112233"
}

#[test]
fn test_write_client_creation() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    );
    assert!(client.is_ok());
}

#[test]
fn test_write_client_invalid_config() {
    let mut config = test_config();
    config.fullnode_url = "".into();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    );
    assert!(client.is_err());
}

#[test]
fn test_write_client_invalid_private_key() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, "not-hex", test_address(),
        false, false, None, None, None,
    );
    assert!(client.is_err());
}

#[test]
fn test_write_client_account_address() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    assert_eq!(client.account_address(), test_address());
}

#[test]
fn test_write_client_primary_subaccount() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let sub = client.get_primary_subaccount_addr();
    assert!(sub.starts_with("0x"));
    assert_eq!(sub.len(), 66);
}

#[test]
fn test_write_client_primary_subaccount_deterministic() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let sub1 = client.get_primary_subaccount_addr();
    let sub2 = client.get_primary_subaccount_addr();
    assert_eq!(sub1, sub2);
}

#[tokio::test]
async fn test_place_order_returns_failure_without_chain() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.place_order(decibel_sdk::client::write::PlaceOrderArgs {
        market_name: "BTC-USD".into(),
        price: 45000.0,
        size: 1.0,
        is_buy: true,
        time_in_force: TimeInForce::GoodTillCanceled,
        is_reduce_only: false,
        client_order_id: Some("test-123".into()),
        stop_price: None,
        tp_trigger_price: Some(50000.0),
        tp_limit_price: Some(49500.0),
        sl_trigger_price: Some(42000.0),
        sl_limit_price: Some(42500.0),
        builder_addr: Some("0xbuilder".into()),
        builder_fee: Some(100),
        subaccount_addr: Some("0xsub".into()),
        tick_size: Some(0.5),
    }).await.unwrap();

    assert!(!result.success);
    assert!(result.error.is_some());
}

#[tokio::test]
async fn test_place_order_with_tick_size_rounding() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.place_order(decibel_sdk::client::write::PlaceOrderArgs {
        market_name: "BTC-USD".into(),
        price: 45123.45,
        size: 1.0,
        is_buy: true,
        time_in_force: TimeInForce::PostOnly,
        is_reduce_only: false,
        client_order_id: None,
        stop_price: None,
        tp_trigger_price: None,
        tp_limit_price: None,
        sl_trigger_price: None,
        sl_limit_price: None,
        builder_addr: None,
        builder_fee: None,
        subaccount_addr: None,
        tick_size: Some(0.5),
    }).await.unwrap();

    // Should return failure since no chain, but exercises the tick rounding code path
    assert!(!result.success);
}

#[tokio::test]
async fn test_cancel_order_requires_market() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.cancel_order(decibel_sdk::client::write::CancelOrderArgs {
        order_id: "12345".into(),
        market_name: None,
        market_addr: None,
        subaccount_addr: None,
    }).await;

    assert!(result.is_err());
    match result.unwrap_err() {
        decibel_sdk::DecibelError::Validation(msg) => {
            assert!(msg.contains("market_name"));
        }
        other => panic!("Expected Validation error, got {:?}", other),
    }
}

#[tokio::test]
async fn test_cancel_order_by_market_name() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.cancel_order(decibel_sdk::client::write::CancelOrderArgs {
        order_id: "12345".into(),
        market_name: Some("BTC-USD".into()),
        market_addr: None,
        subaccount_addr: Some("0xsub".into()),
    }).await;

    // Will fail because no chain, but exercises the code path
    assert!(result.is_err());
}

#[tokio::test]
async fn test_cancel_order_by_market_addr() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.cancel_order(decibel_sdk::client::write::CancelOrderArgs {
        order_id: "12345".into(),
        market_name: None,
        market_addr: Some("0xmarket".into()),
        subaccount_addr: None,
    }).await;

    assert!(result.is_err());
}

#[tokio::test]
async fn test_cancel_client_order() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();

    let result = client.cancel_client_order("my-order-1", "BTC-USD", None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_create_subaccount() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.create_subaccount().await;
    assert!(result.is_err()); // No chain connection
}

#[tokio::test]
async fn test_deposit() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.deposit(1000000, Some("0xsub")).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_deposit_default_subaccount() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.deposit(1000000, None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_withdraw() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.withdraw(500000, Some("0xsub")).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_configure_market_settings() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.configure_user_settings_for_market(
        decibel_sdk::client::write::ConfigureMarketSettingsArgs {
            market_addr: "0xmarket".into(),
            subaccount_addr: "0xsub".into(),
            is_cross: true,
            user_leverage: 1000,
        }
    ).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_place_twap_order() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.place_twap_order(decibel_sdk::client::write::PlaceTwapOrderArgs {
        market_name: "BTC-USD".into(),
        size: 10.0,
        is_buy: true,
        is_reduce_only: false,
        client_order_id: Some("twap-1".into()),
        twap_frequency_seconds: 60,
        twap_duration_seconds: 3600,
        builder_address: None,
        builder_fees: None,
        subaccount_addr: None,
    }).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_cancel_twap_order() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.cancel_twap_order("twap-1", "0xmarket", None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_place_tp_sl() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.place_tp_sl_order_for_position(
        decibel_sdk::client::write::PlaceTpSlArgs {
            market_addr: "0xmarket".into(),
            tp_trigger_price: Some(50000.0),
            tp_limit_price: Some(49500.0),
            tp_size: Some(0.5),
            sl_trigger_price: Some(42000.0),
            sl_limit_price: Some(42500.0),
            sl_size: Some(1.0),
            subaccount_addr: None,
            tick_size: None,
        }
    ).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_delegate_trading() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.delegate_trading_to(
        decibel_sdk::client::write::DelegateTradingArgs {
            subaccount_addr: "0xsub".into(),
            account_to_delegate_to: "0xdelegate".into(),
            expiration_timestamp_secs: Some(1700000000),
        }
    ).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_revoke_delegation() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.revoke_delegation(Some("0xsub"), "0xdelegate").await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_approve_max_builder_fee() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.approve_max_builder_fee("0xbuilder", 100, Some("0xsub")).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_revoke_max_builder_fee() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.revoke_max_builder_fee("0xbuilder", None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_create_vault() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.create_vault(CreateVaultArgs {
        vault_name: "Test Vault".into(),
        vault_description: "A test vault".into(),
        vault_social_links: vec!["https://x.com".into()],
        vault_share_symbol: "TST".into(),
        vault_share_icon_uri: None,
        vault_share_project_uri: None,
        fee_bps: 200,
        fee_interval_s: 86400,
        contribution_lockup_duration_s: 604800,
        initial_funding: 1000000,
        accepts_contributions: true,
        delegate_to_creator: true,
        contribution_asset_type: None,
        subaccount_addr: None,
    }).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_activate_vault() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.activate_vault("0xvault").await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_deposit_to_vault() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.deposit_to_vault("0xvault", 1000000).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_withdraw_from_vault() {
    let config = test_config();
    let client = DecibelWriteClient::new(
        config, test_private_key(), test_address(),
        false, false, None, None, None,
    ).unwrap();
    let result = client.withdraw_from_vault("0xvault", 500).await;
    assert!(result.is_err());
}
