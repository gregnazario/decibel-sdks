use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionPayload {
    pub function: String,
    pub type_arguments: Vec<String>,
    pub arguments: Vec<serde_json::Value>,
}

#[derive(Debug, Clone)]
pub struct TransactionBuildOptions {
    pub max_gas_amount: Option<u64>,
    pub gas_unit_price: Option<u64>,
    pub expiration_timestamp_secs: Option<u64>,
    pub with_fee_payer: bool,
    pub replay_protection_nonce: Option<u64>,
}

impl Default for TransactionBuildOptions {
    fn default() -> Self {
        Self {
            max_gas_amount: None,
            gas_unit_price: None,
            expiration_timestamp_secs: None,
            with_fee_payer: true,
            replay_protection_nonce: None,
        }
    }
}

/// Generate an expiration timestamp for a transaction.
/// Default: 60 seconds from now, with optional time delta correction.
pub fn generate_expire_timestamp(time_delta_ms: i64) -> u64 {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;
    let adjusted = now + time_delta_ms;
    ((adjusted / 1000) + 60) as u64
}

/// Build a transaction payload for a Move entry function call
pub fn build_entry_function_payload(
    function: &str,
    type_arguments: Vec<String>,
    arguments: Vec<serde_json::Value>,
) -> TransactionPayload {
    TransactionPayload {
        function: function.to_string(),
        type_arguments,
        arguments,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_expire_timestamp() {
        let ts = generate_expire_timestamp(0);
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        assert!(ts >= now + 59);
        assert!(ts <= now + 61);
    }

    #[test]
    fn test_generate_expire_timestamp_with_delta() {
        let ts_positive = generate_expire_timestamp(5000);
        let ts_negative = generate_expire_timestamp(-5000);
        assert!(ts_positive > ts_negative);
    }

    #[test]
    fn test_build_entry_function_payload() {
        let payload = build_entry_function_payload(
            "0x1::dex_accounts::place_order",
            vec![],
            vec![serde_json::json!("0xabc"), serde_json::json!(100)],
        );
        assert_eq!(payload.function, "0x1::dex_accounts::place_order");
        assert!(payload.type_arguments.is_empty());
        assert_eq!(payload.arguments.len(), 2);
    }
}
