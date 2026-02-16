use sha3::{Digest, Sha3_256};

/// Derives a market object address from the market name and perp engine global address.
///
/// This follows the Aptos `create_object_address` pattern:
/// 1. BCS-serialize the market name as a Move String (length-prefixed bytes)
/// 2. Compute SHA3-256(perp_engine_global_addr || bcs_name || 0xFE)
pub fn get_market_addr(name: &str, perp_engine_global_addr: &str) -> String {
    let addr_bytes = hex_to_bytes(perp_engine_global_addr);
    let seed = bcs_serialize_string(name);
    let object_addr = create_object_address(&addr_bytes, &seed);
    format!("0x{}", hex::encode(object_addr))
}

/// Derives the primary subaccount address for an account.
pub fn get_primary_subaccount_addr(
    account_addr: &str,
    _compat_version: &str,
    package_addr: &str,
) -> String {
    let addr_bytes = hex_to_bytes(account_addr);
    let seed = format!("{}::dex_accounts::primary_account", strip_hex_prefix(package_addr));
    let seed_bytes = seed.as_bytes();
    let object_addr = create_object_address(&addr_bytes, seed_bytes);
    format!("0x{}", hex::encode(object_addr))
}

/// Derives a vault share token address from the vault address.
pub fn get_vault_share_address(vault_address: &str) -> String {
    let addr_bytes = hex_to_bytes(vault_address);
    let seed = b"vault_share";
    let object_addr = create_object_address(&addr_bytes, seed);
    format!("0x{}", hex::encode(object_addr))
}

/// Aptos `create_object_address`: SHA3-256(source || seed || 0xFE)
fn create_object_address(source: &[u8], seed: &[u8]) -> [u8; 32] {
    let mut hasher = Sha3_256::new();
    // Source address is 32 bytes, pad if needed
    let mut padded_source = [0u8; 32];
    let src_len = source.len().min(32);
    padded_source[32 - src_len..].copy_from_slice(&source[..src_len]);
    hasher.update(&padded_source);
    hasher.update(seed);
    hasher.update(&[0xFE]); // Object address scheme byte
    let result = hasher.finalize();
    let mut addr = [0u8; 32];
    addr.copy_from_slice(&result);
    addr
}

/// BCS-serialize a string (ULEB128 length prefix + UTF-8 bytes)
fn bcs_serialize_string(s: &str) -> Vec<u8> {
    let bytes = s.as_bytes();
    let mut result = Vec::new();
    // ULEB128 encode the length
    let mut len = bytes.len();
    loop {
        let mut byte = (len & 0x7f) as u8;
        len >>= 7;
        if len > 0 {
            byte |= 0x80;
        }
        result.push(byte);
        if len == 0 {
            break;
        }
    }
    result.extend_from_slice(bytes);
    result
}

/// Converts a hex string (with optional 0x prefix) to bytes
fn hex_to_bytes(hex_str: &str) -> Vec<u8> {
    let stripped = strip_hex_prefix(hex_str);
    // Pad to even length
    let padded = if stripped.len() % 2 != 0 {
        format!("0{}", stripped)
    } else {
        stripped.to_string()
    };
    hex::decode(&padded).unwrap_or_default()
}

fn strip_hex_prefix(s: &str) -> &str {
    s.strip_prefix("0x").unwrap_or(s)
}

/// Rounds a price to the nearest valid tick size.
pub fn round_to_tick_size(price: f64, tick_size: f64, _px_decimals: i32, round_up: bool) -> f64 {
    if tick_size <= 0.0 {
        return price;
    }
    let ticks = price / tick_size;
    let rounded_ticks = if round_up {
        ticks.ceil()
    } else {
        ticks.floor()
    };
    rounded_ticks * tick_size
}

/// Generates a random nonce for replay protection.
pub fn generate_random_replay_protection_nonce() -> u64 {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    rng.gen::<u64>()
}

/// Extracts an order ID from transaction events.
pub fn extract_order_id_from_events(
    events: &[serde_json::Value],
    subaccount_addr: &str,
) -> Option<String> {
    for event in events {
        if let Some(event_type) = event.get("type").and_then(|t| t.as_str()) {
            if event_type.contains("::market_types::OrderEvent") {
                if let Some(data) = event.get("data") {
                    if let Some(user) = data.get("user").and_then(|u| u.as_str()) {
                        if user == subaccount_addr {
                            return data
                                .get("order_id")
                                .and_then(|id| id.as_str())
                                .map(|s| s.to_string());
                        }
                    }
                }
            }
        }
    }
    None
}

/// Construct URL query parameters from pagination, sort, and search params.
pub fn construct_query_params(
    page: &super::models::PageParams,
    sort: &super::models::SortParams,
    search: &super::models::SearchTermParams,
) -> Vec<(String, String)> {
    let mut params = Vec::new();

    if let Some(limit) = page.limit {
        params.push(("limit".to_string(), limit.to_string()));
    }
    if let Some(offset) = page.offset {
        params.push(("offset".to_string(), offset.to_string()));
    }
    if let Some(ref key) = sort.sort_key {
        params.push(("sort_key".to_string(), key.clone()));
    }
    if let Some(ref dir) = sort.sort_dir {
        let dir_str = match dir {
            super::models::SortDirection::Ascending => "ASC",
            super::models::SortDirection::Descending => "DESC",
        };
        params.push(("sort_dir".to_string(), dir_str.to_string()));
    }
    if let Some(ref term) = search.search_term {
        params.push(("search_term".to_string(), term.clone()));
    }

    params
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bcs_serialize_string() {
        let result = bcs_serialize_string("BTC-USD");
        assert_eq!(result[0], 7); // length
        assert_eq!(&result[1..], b"BTC-USD");
    }

    #[test]
    fn test_round_to_tick_size() {
        assert_eq!(round_to_tick_size(45123.45, 0.5, 2, false), 45123.0);
        assert_eq!(round_to_tick_size(45123.45, 0.5, 2, true), 45123.5);
        assert_eq!(round_to_tick_size(100.0, 10.0, 0, false), 100.0);
        assert_eq!(round_to_tick_size(105.0, 10.0, 0, false), 100.0);
        assert_eq!(round_to_tick_size(105.0, 10.0, 0, true), 110.0);
    }

    #[test]
    fn test_hex_to_bytes() {
        let bytes = hex_to_bytes("0xabcd");
        assert_eq!(bytes, vec![0xab, 0xcd]);

        let bytes = hex_to_bytes("abcd");
        assert_eq!(bytes, vec![0xab, 0xcd]);
    }

    #[test]
    fn test_generate_nonce() {
        let n1 = generate_random_replay_protection_nonce();
        let n2 = generate_random_replay_protection_nonce();
        assert_ne!(n1, n2); // Extremely unlikely to collide
    }
}
