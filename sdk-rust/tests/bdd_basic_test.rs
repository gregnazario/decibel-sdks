//! Basic BDD test demonstration

#[path = "bdd/mod.rs"]
mod bdd;

use bdd::TestWorld;

#[tokio::test]
async fn test_bdd_world_creation() {
    let world = TestWorld::default();
    assert!(world.read_client.is_none());
    assert!(!world.has_error());
}

#[tokio::test]
async fn test_bdd_config_parsing() {
    use decibel_sdk::config::testnet_config;

    let config = testnet_config();
    assert!(!config.trading_http_url.is_empty());
}

#[tokio::test]
async fn test_bdd_environment_setup() {
    let network = std::env::var("DECIBEL_NETWORK").unwrap_or_else(|_| "testnet".to_string());
    assert!(network == "testnet" || network == "mainnet");
}
