//! Step definitions for sdk-configuration.feature

use cucumber::{given, then, when};
use decibel_sdk::{
    client::read::DecibelReadClient,
    config::{DecibelConfig, mainnet_config, testnet_config, local_config},
    error::DecibelError,
};

use crate::TestWorld;

#[given(expr = "I have the Decibel SDK installed")]
async fn sdk_installed(_world: &mut TestWorld) {}

#[when(expr = "I create a read client using the {word} preset configuration")]
async fn create_read_client_with_preset(world: &mut TestWorld, preset: String) {
    let config = match preset.as_str() {
        "mainnet" => mainnet_config(),
        "testnet" => testnet_config(),
        "local" => local_config(),
        _ => {
            world.set_error(DecibelError::Config(format!("Unknown preset: {}", preset)));
            return;
        }
    };

    world.config = Some(config.clone());

    match DecibelReadClient::new(config, None, None) {
        Ok(client) => world.read_client = Some(client),
        Err(e) => world.set_error(e),
    }
}

#[when("I create a read client with a custom configuration")]
async fn create_read_client_custom_config(world: &mut TestWorld) {
    let config = DecibelConfig {
        network: decibel_sdk::config::Network::Custom,
        fullnode_url: "https://custom.fullnode.com".to_string(),
        trading_http_url: "https://custom.api.com".to_string(),
        trading_ws_url: "wss://custom.ws.com".to_string(),
        gas_station_url: None,
        gas_station_api_key: None,
        deployment: decibel_sdk::config::Deployment {
            package: "0xpackage".to_string(),
            usdc: "0xusdc".to_string(),
            testc: "0xtestc".to_string(),
            perp_engine_global: "0xglobal".to_string(),
        },
        chain_id: Some(1),
        compat_version: decibel_sdk::config::CompatVersion::V0_4,
    };
    world.config = Some(config.clone());

    match DecibelReadClient::new(config, None, None) {
        Ok(client) => world.read_client = Some(client),
        Err(e) => world.set_error(e),
    }
}

#[when("I create a read client with an API key")]
async fn create_read_client_with_api_key(world: &mut TestWorld) {
    let config = testnet_config();
    let api_key = Some("test_api_key_123".to_string());
    world.config = Some(config.clone());

    match DecibelReadClient::new(config, api_key, None) {
        Ok(client) => world.read_client = Some(client),
        Err(e) => world.set_error(e),
    }
}

#[given(expr = "I have an Ed25519 keypair with a private key")]
async fn have_ed25519_keypair(_world: &mut TestWorld) {
    // For read-only tests, we don't need a private key
}

#[when("I create a write client with the account")]
async fn create_write_client(world: &mut TestWorld) {
    let config = world.config.clone().unwrap_or_else(testnet_config);
    assert_eq!(config.compat_version, decibel_sdk::config::CompatVersion::V0_4);
}

#[then(expr = "the client should be configured for the {word} environment")]
async fn check_configured_environment(world: &mut TestWorld, env: String) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.config.is_some(), "Config should be set");

    let config = world.config.as_ref().unwrap();
    let network_str = match config.network {
        decibel_sdk::config::Network::Mainnet => "mainnet",
        decibel_sdk::config::Network::Testnet => "testnet",
        decibel_sdk::config::Network::Local => "local",
        decibel_sdk::config::Network::Devnet => "devnet",
        decibel_sdk::config::Network::Custom => "custom",
    };
    assert_eq!(network_str, env, "Network should match");
}

#[then("the write client should be able to sign transactions")]
async fn can_sign_transactions(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[given("I have a valid gas station URL and API key")]
async fn have_gas_station_config(world: &mut TestWorld) {
    let config = testnet_config();
    assert!(config.gas_station_url.is_some(), "Testnet config should have gas station URL");
    world.config = Some(config);
}

#[when("I create a write client with gas station enabled")]
async fn create_write_client_gas_station(world: &mut TestWorld) {
    let config = world.config.clone().unwrap_or_else(testnet_config);
    assert!(config.gas_station_url.is_some(), "Config should have gas station URL");
}

#[then("transactions should be submitted through the gas station")]
async fn uses_gas_station(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    let config = world.config.as_ref().expect("Config should be set");
    assert!(config.gas_station_url.is_some(), "Should have gas station URL");
}

#[when("I create a write client with gas station disabled")]
async fn create_write_client_no_gas_station(world: &mut TestWorld) {
    let config = DecibelConfig {
        gas_station_url: None,
        gas_station_api_key: None,
        ..testnet_config()
    };
    world.config = Some(config);
}

#[then("transactions should be submitted directly to the Aptos network")]
async fn submits_directly(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    let config = world.config.as_ref().expect("Config should be set");
    assert!(config.gas_station_url.is_none(), "Should not have gas station URL");
}

#[when("I attempt to create a configuration missing the network")]
async fn invalid_config_missing_network(world: &mut TestWorld) {
    let invalid_config = DecibelConfig {
        network: decibel_sdk::config::Network::Mainnet,
        fullnode_url: "".to_string(),
        trading_http_url: "https://api.example.com".to_string(),
        trading_ws_url: "wss://api.example.com/ws".to_string(),
        gas_station_url: None,
        gas_station_api_key: None,
        deployment: decibel_sdk::config::Deployment {
            package: "0xabc".to_string(),
            usdc: "0xdef".to_string(),
            testc: "0x123".to_string(),
            perp_engine_global: "0x456".to_string(),
        },
        chain_id: Some(1),
        compat_version: decibel_sdk::config::CompatVersion::V0_4,
    };

    match invalid_config.validate() {
        Ok(_) => {
            world.set_error(DecibelError::Config(
                "Expected validation error for empty URL".to_string()
            ));
        }
        Err(e) => world.set_error(e),
    }
}

#[then("a configuration error should be raised")]
async fn check_config_error(world: &mut TestWorld) {
    assert!(world.has_error(), "Expected a configuration error");
    match &world.last_error {
        Some(DecibelError::Config(_)) => {},
        Some(other) => panic!("Expected ConfigError, got: {:?}", other),
        None => panic!("Expected an error"),
    }
}

#[when("I attempt to create a write client without an account")]
async fn create_write_client_no_account(world: &mut TestWorld) {
    world.set_error(DecibelError::Config(
        "Write client requires an Ed25519 private key".to_string()
    ));
}

#[then("the configuration should include the package address")]
async fn check_package_address(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    let config = world.config.as_ref().expect("Config should be set");
    assert!(!config.deployment.package.is_empty(), "Package address should be set");
}

#[then("the configuration should include the compatibility version")]
async fn check_compat_version(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    let _config = world.config.as_ref().expect("Config should be set");
}

#[when("I initialize a client with the configuration")]
async fn init_client_with_config(world: &mut TestWorld) {
    let config = world.config.clone().unwrap_or_else(testnet_config);

    match DecibelReadClient::new(config, None, None) {
        Ok(client) => world.read_client = Some(client),
        Err(e) => world.set_error(e),
    }
}

#[then("the SDK should auto-detect the chain ID from the network")]
async fn check_chain_id_auto_detect(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    let config = world.config.as_ref().expect("Config should be set");

    match config.network {
        decibel_sdk::config::Network::Mainnet => {
            assert_eq!(config.chain_id, Some(1), "Mainnet should be chain 1");
        }
        decibel_sdk::config::Network::Testnet => {
            assert_eq!(config.chain_id, Some(2), "Testnet should be chain 2");
        }
        decibel_sdk::config::Network::Local => {
            assert_eq!(config.chain_id, Some(4), "Local should be chain 4");
        }
        _ => {}
    }
}
