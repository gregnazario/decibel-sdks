use decibel_sdk::client::DecibelReadClient;
use decibel_sdk::config::*;
use decibel_sdk::models::*;
use wiremock::matchers::{method, path, query_param};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn test_config(base_url: &str) -> DecibelConfig {
    DecibelConfig {
        network: Network::Custom,
        fullnode_url: "http://localhost:8080/v1".into(),
        trading_http_url: base_url.into(),
        trading_ws_url: "ws://localhost:9999/ws".into(),
        gas_station_url: None,
        gas_station_api_key: None,
        deployment: Deployment {
            package: "0xabc".into(),
            usdc: "0xdef".into(),
            testc: "".into(),
            perp_engine_global: "0x123".into(),
        },
        chain_id: Some(4),
        compat_version: CompatVersion::V0_4,
    }
}

#[tokio::test]
async fn test_get_all_markets() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market_addr": "0xmarket1",
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
            },
            {
                "market_addr": "0xmarket2",
                "market_name": "ETH-USD",
                "sz_decimals": 6,
                "px_decimals": 2,
                "max_leverage": 25.0,
                "min_size": 0.01,
                "lot_size": 0.01,
                "tick_size": 0.05,
                "max_open_interest": 500000.0,
                "margin_call_fee_pct": 0.5,
                "taker_in_next_block": true
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let markets = client.get_all_markets().await.unwrap();
    assert_eq!(markets.len(), 2);
    assert_eq!(markets[0].market_name, "BTC-USD");
    assert_eq!(markets[1].market_name, "ETH-USD");
    assert_eq!(markets[0].max_leverage, 50.0);
    assert!(markets[1].taker_in_next_block);
}

#[tokio::test]
async fn test_get_market_by_name() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets/BTC-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "market_addr": "0xmarket1",
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
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let market = client.get_market_by_name("BTC-USD").await.unwrap();
    assert_eq!(market.market_name, "BTC-USD");
    assert_eq!(market.sz_decimals, 8);
}

#[tokio::test]
async fn test_get_all_market_contexts() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/asset-contexts"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market": "BTC-USD",
                "volume_24h": 5000000.0,
                "open_interest": 200000.0,
                "previous_day_price": 45000.0,
                "price_change_pct_24h": 2.5
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let contexts = client.get_all_market_contexts().await.unwrap();
    assert_eq!(contexts.len(), 1);
    assert_eq!(contexts[0].market, "BTC-USD");
    assert_eq!(contexts[0].volume_24h, 5000000.0);
}

#[tokio::test]
async fn test_get_market_depth() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/depth/BTC-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "market": "BTC-USD",
            "bids": [{"price": 45100.0, "size": 2.5}, {"price": 45050.0, "size": 1.0}],
            "asks": [{"price": 45150.0, "size": 3.0}],
            "unix_ms": 1708000000000i64
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let depth = client.get_market_depth("BTC-USD", Some(10)).await.unwrap();
    assert_eq!(depth.market, "BTC-USD");
    assert_eq!(depth.bids.len(), 2);
    assert_eq!(depth.asks.len(), 1);
    assert_eq!(depth.bids[0].price, 45100.0);
}

#[tokio::test]
async fn test_get_market_depth_no_limit() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/depth/ETH-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "market": "ETH-USD",
            "bids": [],
            "asks": [],
            "unix_ms": 0
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let depth = client.get_market_depth("ETH-USD", None).await.unwrap();
    assert_eq!(depth.bids.len(), 0);
}

#[tokio::test]
async fn test_get_all_market_prices() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/prices"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market": "BTC-USD",
                "mark_px": 45123.5,
                "mid_px": 45120.0,
                "oracle_px": 45125.0,
                "funding_rate_bps": 0.01,
                "is_funding_positive": true,
                "open_interest": 1500000.0,
                "transaction_unix_ms": 1708000000000i64
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let prices = client.get_all_market_prices().await.unwrap();
    assert_eq!(prices.len(), 1);
    assert_eq!(prices[0].mark_px, 45123.5);
    assert!(prices[0].is_funding_positive);
}

#[tokio::test]
async fn test_get_market_price_by_name() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/prices/BTC-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market": "BTC-USD",
                "mark_px": 45123.5,
                "mid_px": 45120.0,
                "oracle_px": 45125.0,
                "funding_rate_bps": 0.01,
                "is_funding_positive": true,
                "open_interest": 1500000.0,
                "transaction_unix_ms": 1708000000000i64
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let prices = client.get_market_price_by_name("BTC-USD").await.unwrap();
    assert_eq!(prices[0].market, "BTC-USD");
}

#[tokio::test]
async fn test_get_market_trades() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/trades/BTC-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {"market": "BTC-USD", "price": 45123.0, "size": 0.5, "is_buy": true, "unix_ms": 1708000000000i64}
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let trades = client.get_market_trades("BTC-USD", Some(50)).await.unwrap();
    assert_eq!(trades.len(), 1);
    assert!(trades[0].is_buy);
}

#[tokio::test]
async fn test_get_candlesticks() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/candlesticks/BTC-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {"T": 1708000060000i64, "c": 45200.0, "h": 45300.0, "i": "1m", "l": 45100.0, "o": 45150.0, "t": 1708000000000i64, "v": 125.5}
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let candles = client.get_candlesticks("BTC-USD", CandlestickInterval::OneMinute, 1708000000000, 1708000060000).await.unwrap();
    assert_eq!(candles.len(), 1);
    assert_eq!(candles[0].o, 45150.0);
}

#[tokio::test]
async fn test_get_account_overview() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/account/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": 500.0,
            "unrealized_funding_cost": -10.5,
            "cross_margin_ratio": 0.15,
            "maintenance_margin": 1000.0,
            "cross_account_leverage_ratio": 5.0,
            "volume": 250000.0,
            "net_deposits": null,
            "all_time_return": null,
            "pnl_90d": null,
            "sharpe_ratio": null,
            "max_drawdown": null,
            "weekly_win_rate_12w": null,
            "average_cash_position": null,
            "average_leverage": null,
            "cross_account_position": 7000.0,
            "total_margin": 2000.0,
            "usdc_cross_withdrawable_balance": 3000.0,
            "usdc_isolated_withdrawable_balance": 1000.0,
            "realized_pnl": null,
            "liquidation_fees_paid": null,
            "liquidation_losses": null
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let overview = client.get_account_overview("0xsub", Some(VolumeWindow::ThirtyDays), Some(true)).await.unwrap();
    assert_eq!(overview.perp_equity_balance, 10000.0);
    assert_eq!(overview.cross_account_leverage_ratio, Some(5.0));
}

#[tokio::test]
async fn test_get_account_overview_no_optional_params() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/account/0xsub2"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "perp_equity_balance": 0.0, "unrealized_pnl": 0.0,
            "unrealized_funding_cost": 0.0, "cross_margin_ratio": 0.0,
            "maintenance_margin": 0.0, "cross_account_leverage_ratio": null,
            "volume": null, "net_deposits": null, "all_time_return": null,
            "pnl_90d": null, "sharpe_ratio": null, "max_drawdown": null,
            "weekly_win_rate_12w": null, "average_cash_position": null,
            "average_leverage": null, "cross_account_position": 0.0,
            "total_margin": 0.0, "usdc_cross_withdrawable_balance": 0.0,
            "usdc_isolated_withdrawable_balance": 0.0,
            "realized_pnl": null, "liquidation_fees_paid": null,
            "liquidation_losses": null
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let overview = client.get_account_overview("0xsub2", None, None).await.unwrap();
    assert_eq!(overview.perp_equity_balance, 0.0);
}

#[tokio::test]
async fn test_get_user_positions() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/positions/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market": "0xmarket", "user": "0xsub", "size": 1.5, "user_leverage": 10.0,
                "entry_price": 45000.0, "is_isolated": false, "unrealized_funding": 0.0,
                "estimated_liquidation_price": 40000.0,
                "tp_order_id": null, "tp_trigger_price": null, "tp_limit_price": null,
                "sl_order_id": null, "sl_trigger_price": null, "sl_limit_price": null,
                "has_fixed_sized_tpsls": false
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let positions = client.get_user_positions("0xsub", None, None, None).await.unwrap();
    assert_eq!(positions.len(), 1);
    assert_eq!(positions[0].size, 1.5);
}

#[tokio::test]
async fn test_get_user_positions_with_filters() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/positions/0xsub"))
        .and(query_param("market_addr", "0xmarket"))
        .and(query_param("include_deleted", "true"))
        .and(query_param("limit", "5"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let positions = client.get_user_positions("0xsub", Some("0xmarket"), Some(true), Some(5)).await.unwrap();
    assert_eq!(positions.len(), 0);
}

#[tokio::test]
async fn test_get_user_open_orders() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/open-orders/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {
                "market": "0xmarket", "order_id": "12345", "client_order_id": "my-1",
                "price": 45000.0, "orig_size": 1.0, "remaining_size": 0.5,
                "is_buy": true, "time_in_force": "GoodTillCanceled",
                "is_reduce_only": false, "status": "Acknowledged",
                "transaction_unix_ms": 1708000000000i64, "transaction_version": 100
            }
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let orders = client.get_user_open_orders("0xsub").await.unwrap();
    assert_eq!(orders.len(), 1);
    assert_eq!(orders[0].order_id, "12345");
}

#[tokio::test]
async fn test_get_user_order_history() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/order-history/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [
                {
                    "market": "0xmarket", "order_id": "123", "client_order_id": null,
                    "price": 45000.0, "orig_size": 1.0, "remaining_size": 0.0,
                    "is_buy": true, "time_in_force": "GTC", "is_reduce_only": false,
                    "status": "Filled", "transaction_unix_ms": 1708000000000i64, "transaction_version": 100
                }
            ],
            "total_count": 1
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let history = client.get_user_order_history("0xsub", Some("0xmarket"), Some(10), Some(0)).await.unwrap();
    assert_eq!(history.items.len(), 1);
    assert_eq!(history.total_count, 1);
}

#[tokio::test]
async fn test_get_user_trade_history() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/trade-history/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [
                {
                    "account": "0xsub", "market": "0xmarket", "action": "OpenLong",
                    "size": 1.0, "price": 45000.0, "is_profit": false,
                    "realized_pnl_amount": 0.0, "is_funding_positive": true,
                    "realized_funding_amount": 0.0, "is_rebate": false, "fee_amount": 5.0,
                    "transaction_unix_ms": 1708000000000i64, "transaction_version": 100
                }
            ],
            "total_count": 1
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let trades = client.get_user_trade_history("0xsub", Some(10), Some(0)).await.unwrap();
    assert_eq!(trades.items.len(), 1);
    assert_eq!(trades.items[0].action, "OpenLong");
}

#[tokio::test]
async fn test_get_user_funding_history() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/funding-history/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [
                {
                    "market": "0xmarket", "funding_rate_bps": 0.01, "is_funding_positive": true,
                    "funding_amount": 5.0, "position_size": 1.0,
                    "transaction_unix_ms": 1708000000000i64, "transaction_version": 100
                }
            ],
            "total_count": 1
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let funding = client.get_user_funding_history("0xsub", Some("0xmarket"), Some(10), Some(0)).await.unwrap();
    assert_eq!(funding.items.len(), 1);
}

#[tokio::test]
async fn test_get_user_fund_history() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/fund-history/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [
                {"amount": 1000.0, "is_deposit": true, "transaction_unix_ms": 1708000000000i64, "transaction_version": 100}
            ],
            "total_count": 1
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let history = client.get_user_fund_history("0xsub", Some(10), None).await.unwrap();
    assert_eq!(history.items.len(), 1);
    assert!(history.items[0].is_deposit);
}

#[tokio::test]
async fn test_get_user_subaccounts() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/subaccounts/0xowner"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {"subaccount_address": "0xsub1", "primary_account_address": "0xowner", "is_primary": true, "custom_label": null, "is_active": true}
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let subs = client.get_user_subaccounts("0xowner").await.unwrap();
    assert_eq!(subs.len(), 1);
    assert!(subs[0].is_primary);
}

#[tokio::test]
async fn test_get_delegations() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/delegations/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
            {"delegated_account": "0xdelegate", "permission_type": "trading", "expiration_time_s": 1700000000}
        ])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let delegations = client.get_delegations("0xsub").await.unwrap();
    assert_eq!(delegations.len(), 1);
    assert_eq!(delegations[0].delegated_account, "0xdelegate");
}

#[tokio::test]
async fn test_get_active_twaps() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/active-twaps/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let twaps = client.get_active_twaps("0xsub").await.unwrap();
    assert_eq!(twaps.len(), 0);
}

#[tokio::test]
async fn test_get_twap_history() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/twap-history/0xsub"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [], "total_count": 0
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let history = client.get_twap_history("0xsub", Some(10), Some(0)).await.unwrap();
    assert_eq!(history.total_count, 0);
}

#[tokio::test]
async fn test_get_vaults() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/vaults"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [], "total_count": 0, "total_value_locked": 0.0, "total_volume": 0.0
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let vaults = client.get_vaults(&PageParams::default(), &SortParams::default(), &SearchTermParams::default()).await.unwrap();
    assert_eq!(vaults.total_count, 0);
}

#[tokio::test]
async fn test_get_user_owned_vaults() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/vaults/owned/0xaccount"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [], "total_count": 0
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let vaults = client.get_user_owned_vaults("0xaccount", None, None).await.unwrap();
    assert_eq!(vaults.total_count, 0);
}

#[tokio::test]
async fn test_get_user_performances_on_vaults() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/vaults/performance/0xaccount"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let perfs = client.get_user_performances_on_vaults("0xaccount").await.unwrap();
    assert_eq!(perfs.len(), 0);
}

#[tokio::test]
async fn test_get_leaderboard() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/leaderboard"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "items": [
                {"rank": 1, "account": "0x1", "account_value": 100000.0, "realized_pnl": 5000.0, "roi": 0.05, "volume": 500000.0}
            ],
            "total_count": 1
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let lb = client.get_leaderboard(&PageParams::default(), &SortParams::default(), &SearchTermParams::default()).await.unwrap();
    assert_eq!(lb.items.len(), 1);
    assert_eq!(lb.items[0].rank, 1);
}

#[tokio::test]
async fn test_get_order_status_found() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/orders/12345"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "parent": "0xparent", "market": "0xmarket", "order_id": "12345",
            "status": "Filled", "orig_size": 1.0, "remaining_size": 0.0,
            "size_delta": 1.0, "price": 45000.0, "is_buy": true,
            "details": "fully filled", "transaction_version": 200, "unix_ms": 1708000000000i64
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let status = client.get_order_status("12345", "0xmarket", "0xuser").await.unwrap();
    assert!(status.is_some());
    assert_eq!(status.unwrap().status, "Filled");
}

#[tokio::test]
async fn test_get_order_status_not_found() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/orders/99999"))
        .respond_with(ResponseTemplate::new(404).set_body_string("Not found"))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let status = client.get_order_status("99999", "0xmarket", "0xuser").await.unwrap();
    assert!(status.is_none());
}

#[tokio::test]
async fn test_api_error_500() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets"))
        .respond_with(ResponseTemplate::new(500).set_body_string("Internal server error"))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let result = client.get_all_markets().await;
    assert!(result.is_err());
    match result.unwrap_err() {
        decibel_sdk::DecibelError::Api { status, message, .. } => {
            assert_eq!(status, 500);
            assert_eq!(message, "Internal server error");
        }
        other => panic!("Expected Api error, got {:?}", other),
    }
}

#[tokio::test]
async fn test_read_client_with_api_key() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets"))
        .and(wiremock::matchers::header("x-api-key", "test-key"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, Some("test-key".to_string()), None).unwrap();
    let markets = client.get_all_markets().await.unwrap();
    assert_eq!(markets.len(), 0);
}

#[tokio::test]
async fn test_get_market_trades_no_limit() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/trades/SOL-USD"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let trades = client.get_market_trades("SOL-USD", None).await.unwrap();
    assert_eq!(trades.len(), 0);
}

#[tokio::test]
async fn test_get_user_funding_history_no_filters() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/funding-history/0xsub2"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({"items":[],"total_count":0})))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let result = client.get_user_funding_history("0xsub2", None, None, None).await.unwrap();
    assert_eq!(result.total_count, 0);
}

#[tokio::test]
async fn test_get_user_order_history_no_filters() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/order-history/0xsub2"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({"items":[],"total_count":0})))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let result = client.get_user_order_history("0xsub2", None, None, None).await.unwrap();
    assert_eq!(result.total_count, 0);
}

#[tokio::test]
async fn test_ws_accessor() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([])))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let ws = client.ws();
    let state = ws.ready_state().await;
    assert_eq!(state, decibel_sdk::client::ws::WsReadyState::Closed);
}

#[tokio::test]
async fn test_api_error_403() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/markets"))
        .respond_with(ResponseTemplate::new(403).set_body_string("Forbidden"))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let client = DecibelReadClient::new(config, None, None).unwrap();
    let result = client.get_all_markets().await;
    assert!(result.is_err());
    match result.unwrap_err() {
        decibel_sdk::DecibelError::Api { status, .. } => assert_eq!(status, 403),
        other => panic!("Expected Api error, got {:?}", other),
    }
}

#[tokio::test]
async fn test_invalid_config_fails() {
    let config = DecibelConfig {
        network: Network::Custom,
        fullnode_url: "".into(),
        trading_http_url: "".into(),
        trading_ws_url: "".into(),
        gas_station_url: None,
        gas_station_api_key: None,
        deployment: Deployment {
            package: "".into(),
            usdc: "".into(),
            testc: "".into(),
            perp_engine_global: "".into(),
        },
        chain_id: None,
        compat_version: CompatVersion::V0_4,
    };
    let result = DecibelReadClient::new(config, None, None);
    assert!(result.is_err());
}
