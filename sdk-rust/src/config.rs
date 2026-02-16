use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Network {
    Mainnet,
    Testnet,
    Devnet,
    Local,
    Custom,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CompatVersion {
    #[serde(rename = "v0.4")]
    V0_4,
}

impl Default for CompatVersion {
    fn default() -> Self {
        CompatVersion::V0_4
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Deployment {
    pub package: String,
    pub usdc: String,
    pub testc: String,
    pub perp_engine_global: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecibelConfig {
    pub network: Network,
    pub fullnode_url: String,
    pub trading_http_url: String,
    pub trading_ws_url: String,
    pub gas_station_url: Option<String>,
    pub gas_station_api_key: Option<String>,
    pub deployment: Deployment,
    pub chain_id: Option<u8>,
    pub compat_version: CompatVersion,
}

impl DecibelConfig {
    pub fn validate(&self) -> crate::Result<()> {
        if self.fullnode_url.is_empty() {
            return Err(crate::DecibelError::Config(
                "fullnode_url must not be empty".into(),
            ));
        }
        if self.trading_http_url.is_empty() {
            return Err(crate::DecibelError::Config(
                "trading_http_url must not be empty".into(),
            ));
        }
        if self.trading_ws_url.is_empty() {
            return Err(crate::DecibelError::Config(
                "trading_ws_url must not be empty".into(),
            ));
        }
        if self.deployment.package.is_empty() {
            return Err(crate::DecibelError::Config(
                "deployment.package must not be empty".into(),
            ));
        }
        Ok(())
    }
}

pub fn mainnet_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Mainnet,
        fullnode_url: "https://fullnode.mainnet.aptoslabs.com/v1".into(),
        trading_http_url: "https://api.decibel.trade".into(),
        trading_ws_url: "wss://api.decibel.trade/ws".into(),
        gas_station_url: Some("https://api.netna.aptoslabs.com/gs/v1".into()),
        gas_station_api_key: None,
        deployment: Deployment {
            package: "0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d".into(),
            usdc: "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b".into(),
            testc: "".into(),
            perp_engine_global: "".into(),
        },
        chain_id: Some(1),
        compat_version: CompatVersion::V0_4,
    }
}

pub fn testnet_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Testnet,
        fullnode_url: "https://fullnode.testnet.aptoslabs.com/v1".into(),
        trading_http_url: "https://api.testnet.decibel.trade".into(),
        trading_ws_url: "wss://api.testnet.decibel.trade/ws".into(),
        gas_station_url: Some("https://api.testnet.aptoslabs.com/gs/v1".into()),
        gas_station_api_key: None,
        deployment: Deployment {
            package: "".into(),
            usdc: "".into(),
            testc: "".into(),
            perp_engine_global: "".into(),
        },
        chain_id: Some(2),
        compat_version: CompatVersion::V0_4,
    }
}

pub fn local_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Local,
        fullnode_url: "http://localhost:8080/v1".into(),
        trading_http_url: "http://localhost:3000".into(),
        trading_ws_url: "ws://localhost:3000/ws".into(),
        gas_station_url: Some("http://localhost:8081".into()),
        gas_station_api_key: None,
        deployment: Deployment {
            package: "".into(),
            usdc: "".into(),
            testc: "".into(),
            perp_engine_global: "".into(),
        },
        chain_id: Some(4),
        compat_version: CompatVersion::V0_4,
    }
}

/// Named configs for lookup by string key
pub fn named_config(name: &str) -> Option<DecibelConfig> {
    match name.to_lowercase().as_str() {
        "mainnet" => Some(mainnet_config()),
        "testnet" => Some(testnet_config()),
        "local" => Some(local_config()),
        _ => None,
    }
}
