use decibel_sdk::config::*;

// BDD: Configuration and Initialization Tests

#[test]
fn given_mainnet_preset_when_creating_config_then_all_fields_populated() {
    let config = mainnet_config();
    assert_eq!(config.network, Network::Mainnet);
    assert!(!config.fullnode_url.is_empty());
    assert!(!config.trading_http_url.is_empty());
    assert!(!config.trading_ws_url.is_empty());
    assert!(!config.deployment.package.is_empty());
    assert_eq!(config.compat_version, CompatVersion::V0_4);
    assert_eq!(config.chain_id, Some(1));
}

#[test]
fn given_testnet_preset_when_creating_config_then_network_is_testnet() {
    let config = testnet_config();
    assert_eq!(config.network, Network::Testnet);
    assert_eq!(config.chain_id, Some(2));
}

#[test]
fn given_local_preset_when_creating_config_then_uses_localhost() {
    let config = local_config();
    assert_eq!(config.network, Network::Local);
    assert!(config.fullnode_url.contains("localhost"));
    assert!(config.trading_http_url.contains("localhost"));
    assert!(config.trading_ws_url.contains("localhost"));
}

#[test]
fn given_valid_config_when_validating_then_succeeds() {
    let config = mainnet_config();
    assert!(config.validate().is_ok());
}

#[test]
fn given_empty_fullnode_url_when_validating_then_returns_error() {
    let mut config = mainnet_config();
    config.fullnode_url = String::new();
    let result = config.validate();
    assert!(result.is_err());
    let err_msg = result.unwrap_err().to_string();
    assert!(err_msg.contains("fullnode_url"));
}

#[test]
fn given_empty_trading_http_url_when_validating_then_returns_error() {
    let mut config = mainnet_config();
    config.trading_http_url = String::new();
    assert!(config.validate().is_err());
}

#[test]
fn given_empty_trading_ws_url_when_validating_then_returns_error() {
    let mut config = mainnet_config();
    config.trading_ws_url = String::new();
    assert!(config.validate().is_err());
}

#[test]
fn given_empty_deployment_package_when_validating_then_returns_error() {
    let mut config = mainnet_config();
    config.deployment.package = String::new();
    assert!(config.validate().is_err());
}

#[test]
fn given_named_config_mainnet_when_looking_up_then_returns_mainnet() {
    let config = named_config("mainnet");
    assert!(config.is_some());
    assert_eq!(config.unwrap().network, Network::Mainnet);
}

#[test]
fn given_named_config_unknown_when_looking_up_then_returns_none() {
    let config = named_config("nonexistent");
    assert!(config.is_none());
}

#[test]
fn given_config_when_serialized_and_deserialized_then_roundtrips() {
    let config = mainnet_config();
    let json = serde_json::to_string(&config).unwrap();
    let deserialized: DecibelConfig = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.network, config.network);
    assert_eq!(deserialized.fullnode_url, config.fullnode_url);
}

#[test]
fn given_compat_version_default_when_created_then_is_v0_4() {
    let version = CompatVersion::default();
    assert_eq!(version, CompatVersion::V0_4);
}
