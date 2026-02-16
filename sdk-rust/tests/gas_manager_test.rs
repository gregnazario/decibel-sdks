use decibel_sdk::config::*;
use decibel_sdk::gas::GasPriceManager;
use wiremock::{Mock, MockServer, ResponseTemplate};
use wiremock::matchers::{method, path};

fn test_config(fullnode_url: &str) -> DecibelConfig {
    DecibelConfig {
        network: Network::Custom,
        fullnode_url: fullnode_url.into(),
        trading_http_url: "http://localhost:3000".into(),
        trading_ws_url: "ws://localhost:3000/ws".into(),
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
async fn test_gas_price_manager_creation() {
    let config = test_config("http://localhost:8080/v1");
    let manager = GasPriceManager::new(&config, 1.5, 5000);
    let price = manager.get_gas_price().await;
    assert!(price.is_none()); // Not initialized yet
}

#[tokio::test]
async fn test_gas_price_manager_initialize_and_fetch() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/estimate_gas_price"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "gas_estimate": 100,
            "deprioritized_gas_estimate": 50,
            "prioritized_gas_estimate": 200
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let manager = GasPriceManager::new(&config, 1.5, 60000);
    manager.initialize().await;

    let price = manager.get_gas_price().await;
    assert!(price.is_some());
    assert_eq!(price.unwrap(), 150); // 100 * 1.5

    manager.destroy().await;
}

#[tokio::test]
async fn test_gas_price_manager_multiplier() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/estimate_gas_price"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "gas_estimate": 200
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let manager = GasPriceManager::new(&config, 2.0, 60000);
    manager.initialize().await;

    let price = manager.get_gas_price().await;
    assert_eq!(price.unwrap(), 400); // 200 * 2.0

    manager.destroy().await;
}

#[tokio::test]
async fn test_gas_price_manager_destroy() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/estimate_gas_price"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "gas_estimate": 100
        })))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let manager = GasPriceManager::new(&config, 1.0, 60000);
    manager.initialize().await;
    manager.destroy().await;
    // Should not panic after destroy
}

#[tokio::test]
async fn test_gas_price_manager_server_error() {
    let mock_server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/estimate_gas_price"))
        .respond_with(ResponseTemplate::new(500).set_body_string("error"))
        .mount(&mock_server)
        .await;

    let config = test_config(&mock_server.uri());
    let manager = GasPriceManager::new(&config, 1.0, 60000);
    manager.initialize().await;

    // Gas price should still be None or have a default if fetch failed gracefully
    // The implementation falls back to None on error
    manager.destroy().await;
}
