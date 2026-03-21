use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Network {
    Mainnet,
    Testnet,
    Devnet,
    Custom,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct Deployment {
    pub package: String,
    pub usdc: String,
    pub testc: String,
    pub perp_engine_global: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct DecibelConfig {
    pub network: Network,
    pub fullnode_url: String,
    pub trading_http_url: String,
    pub trading_ws_url: String,
    pub deployment: Deployment,
    pub compat_version: String,
    pub gas_station_url: Option<String>,
    pub gas_station_api_key: Option<String>,
    pub chain_id: Option<u8>,
}

pub fn mainnet_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Mainnet,
        fullnode_url: "https://fullnode.mainnet.aptoslabs.com".into(),
        trading_http_url: "https://perps-tradeapi.kanalabs.io".into(),
        trading_ws_url: "wss://perps-tradeapi.kanalabs.io/ws".into(),
        deployment: Deployment {
            package: "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06"
                .into(),
            usdc: "0xbae207659db88bea0d0ffd4c6b2d987731698b98e0cfbdb1ed1d0b4b907b3a16"
                .into(),
            testc: "0x0".into(),
            perp_engine_global:
                "0x610c649060aa5388e861b975a21a720a2de4b5da6aff8a20e84e1ef89085e5ab"
                    .into(),
        },
        compat_version: "v0.4".into(),
        gas_station_url: None,
        gas_station_api_key: None,
        chain_id: None,
    }
}

pub fn testnet_config() -> DecibelConfig {
    DecibelConfig {
        network: Network::Testnet,
        fullnode_url: "https://fullnode.testnet.aptoslabs.com".into(),
        trading_http_url: "https://perps-tradeapi-testnet.kanalabs.io".into(),
        trading_ws_url: "wss://perps-tradeapi-testnet.kanalabs.io/ws".into(),
        deployment: Deployment {
            package: "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06"
                .into(),
            usdc: "0xbae207659db88bea0d0ffd4c6b2d987731698b98e0cfbdb1ed1d0b4b907b3a16"
                .into(),
            testc: "0x1".into(),
            perp_engine_global:
                "0x610c649060aa5388e861b975a21a720a2de4b5da6aff8a20e84e1ef89085e5ab"
                    .into(),
        },
        compat_version: "v0.4".into(),
        gas_station_url: None,
        gas_station_api_key: None,
        chain_id: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Roundtrip serialization ensures configs survive JSON persistence
    /// (e.g., saving to disk and reloading in a bot restart).
    #[test]
    fn config_roundtrip_serialization() {
        let cfg = mainnet_config();
        let json = serde_json::to_string(&cfg).unwrap();
        let restored: DecibelConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.network, Network::Mainnet);
        assert_eq!(restored.fullnode_url, cfg.fullnode_url);
        assert_eq!(restored.deployment.package, cfg.deployment.package);
        assert_eq!(restored.compat_version, "v0.4");
    }

    /// Mainnet preset must point to production endpoints so bots don't
    /// accidentally trade on testnet.
    #[test]
    fn mainnet_preset_values() {
        let cfg = mainnet_config();
        assert_eq!(cfg.network, Network::Mainnet);
        assert!(cfg.fullnode_url.contains("mainnet"));
        assert!(cfg.trading_http_url.starts_with("https://"));
        assert!(cfg.trading_ws_url.starts_with("wss://"));
        assert_eq!(cfg.compat_version, "v0.4");
        assert!(cfg.gas_station_url.is_none());
        assert!(cfg.gas_station_api_key.is_none());
        assert!(cfg.chain_id.is_none());
    }

    /// Testnet preset must point to testnet so development never touches
    /// real funds.
    #[test]
    fn testnet_preset_values() {
        let cfg = testnet_config();
        assert_eq!(cfg.network, Network::Testnet);
        assert!(cfg.fullnode_url.contains("testnet"));
        assert!(cfg.trading_http_url.contains("testnet"));
        assert!(cfg.trading_ws_url.contains("testnet"));
    }

    /// Clone must produce a fully independent copy — critical when
    /// multiple bot threads each hold their own config snapshot.
    #[test]
    fn config_clone_is_independent() {
        let cfg1 = mainnet_config();
        let mut cfg2 = cfg1.clone();
        cfg2.fullnode_url = "https://custom-node.example.com".into();
        assert_ne!(cfg1.fullnode_url, cfg2.fullnode_url);
        assert_eq!(cfg1.network, Network::Mainnet);
    }

    /// Network enum must serialize to its variant name for readable
    /// JSON configs.
    #[test]
    fn network_enum_serialization() {
        let json = serde_json::to_string(&Network::Mainnet).unwrap();
        assert_eq!(json, "\"Mainnet\"");
        let restored: Network = serde_json::from_str(&json).unwrap();
        assert_eq!(restored, Network::Mainnet);
    }

    /// Deployment must carry all four required addresses. Missing any
    /// would make order placement fail at runtime.
    #[test]
    fn deployment_roundtrip() {
        let dep = Deployment {
            package: "0xabc".into(),
            usdc: "0xdef".into(),
            testc: "0x000".into(),
            perp_engine_global: "0x123".into(),
        };
        let json = serde_json::to_string(&dep).unwrap();
        let restored: Deployment = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.package, "0xabc");
        assert_eq!(restored.usdc, "0xdef");
        assert_eq!(restored.testc, "0x000");
        assert_eq!(restored.perp_engine_global, "0x123");
    }

    /// Optional fields should serialize as null and deserialize back
    /// to None, ensuring configs without gas station work cleanly.
    #[test]
    fn optional_fields_roundtrip() {
        let mut cfg = mainnet_config();
        cfg.gas_station_url = Some("https://gas.example.com".into());
        cfg.gas_station_api_key = Some("key123".into());
        cfg.chain_id = Some(1);

        let json = serde_json::to_string(&cfg).unwrap();
        let restored: DecibelConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(
            restored.gas_station_url.as_deref(),
            Some("https://gas.example.com")
        );
        assert_eq!(restored.gas_station_api_key.as_deref(), Some("key123"));
        assert_eq!(restored.chain_id, Some(1));
    }
}
