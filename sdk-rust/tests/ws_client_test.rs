use std::sync::Arc;
use decibel_sdk::client::ws::{WebSocketManager, WsReadyState};
use decibel_sdk::config::*;

fn test_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Custom,
        fullnode_url: "http://localhost:8080/v1".into(),
        trading_http_url: "http://localhost:3000".into(),
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
async fn test_ws_manager_creation() {
    let config = test_config();
    let _manager = WebSocketManager::new(config, None, None);
}

#[tokio::test]
async fn test_ws_manager_initial_state_closed() {
    let config = test_config();
    let manager = WebSocketManager::new(config, None, None);
    assert_eq!(manager.ready_state().await, WsReadyState::Closed);
}

#[tokio::test]
async fn test_ws_manager_with_api_key() {
    let config = test_config();
    let _manager = WebSocketManager::new(config, Some("test-key".into()), None);
}

#[tokio::test]
async fn test_ws_manager_with_error_handler() {
    let config = test_config();
    let handler: Arc<dyn Fn(String) + Send + Sync> = Arc::new(|err| {
        eprintln!("WS error: {}", err);
    });
    let _manager = WebSocketManager::new(config, None, Some(handler));
}

#[tokio::test]
async fn test_ws_manager_close_when_not_connected() {
    let config = test_config();
    let manager = WebSocketManager::new(config, None, None);
    manager.close().await;
    assert_eq!(manager.ready_state().await, WsReadyState::Closed);
}

#[tokio::test]
async fn test_ws_manager_connect_to_invalid_url_fails() {
    let config = test_config(); // Port 9999 is not listening
    let manager = WebSocketManager::new(config, None, None);
    let result = manager.connect().await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_ws_manager_subscribe_without_server_fails() {
    let config = test_config();
    let manager = WebSocketManager::new(config, None, None);
    let result = manager.subscribe("test-topic", |_value| {}).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_ws_ready_state_values() {
    assert_eq!(WsReadyState::Connecting, WsReadyState::Connecting);
    assert_eq!(WsReadyState::Open, WsReadyState::Open);
    assert_eq!(WsReadyState::Closing, WsReadyState::Closing);
    assert_eq!(WsReadyState::Closed, WsReadyState::Closed);
    assert_ne!(WsReadyState::Open, WsReadyState::Closed);
}
