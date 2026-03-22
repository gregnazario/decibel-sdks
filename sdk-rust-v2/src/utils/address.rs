use sha3::{Digest, Sha3_256};

const OBJECT_ADDRESS_SCHEME: u8 = 0xFE;

fn create_object_address(source: &[u8], seed: &[u8]) -> [u8; 32] {
    let mut hasher = Sha3_256::new();
    hasher.update(source);
    hasher.update(seed);
    hasher.update([OBJECT_ADDRESS_SCHEME]);
    let result = hasher.finalize();
    let mut addr = [0u8; 32];
    addr.copy_from_slice(&result);
    addr
}

/// Derive the on-chain market address for a named perpetual market.
///
/// The address is `SHA3-256(perp_engine_global_bytes || market_name_bytes || 0xFE)`.
pub fn get_market_addr(market_name: &str, perp_engine_global: &str) -> String {
    let source = decode_hex_address(perp_engine_global);
    let seed = market_name.as_bytes();
    let addr = create_object_address(&source, seed);
    format!("0x{}", hex::encode(addr))
}

/// Derive the primary subaccount address for an account.
///
/// The seed is `"subaccount" || compat_version`.
pub fn get_primary_subaccount_addr(
    account_addr: &str,
    compat_version: &str,
    package_addr: &str,
) -> String {
    let source = decode_hex_address(account_addr);
    let seed_string = format!("subaccount{}{}", compat_version, package_addr);
    let seed = seed_string.as_bytes();
    let addr = create_object_address(&source, seed);
    format!("0x{}", hex::encode(addr))
}

/// Derive the vault share address from a vault address.
///
/// The seed is the literal bytes `"vault_share"`.
pub fn get_vault_share_address(vault_address: &str) -> String {
    let source = decode_hex_address(vault_address);
    let seed = b"vault_share";
    let addr = create_object_address(&source, seed);
    format!("0x{}", hex::encode(addr))
}

fn decode_hex_address(hex_str: &str) -> Vec<u8> {
    let stripped = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    let padded = if stripped.len() < 64 {
        format!("{:0>64}", stripped)
    } else {
        stripped.to_string()
    };
    hex::decode(&padded).expect("invalid hex address")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_object_address_deterministic() {
        let source = [0u8; 32];
        let seed = b"test_seed";
        let addr1 = create_object_address(&source, seed);
        let addr2 = create_object_address(&source, seed);
        assert_eq!(addr1, addr2);
    }

    #[test]
    fn create_object_address_different_sources_differ() {
        let source_a = [0u8; 32];
        let mut source_b = [0u8; 32];
        source_b[0] = 1;
        let seed = b"same_seed";
        let addr_a = create_object_address(&source_a, seed);
        let addr_b = create_object_address(&source_b, seed);
        assert_ne!(addr_a, addr_b);
    }

    #[test]
    fn create_object_address_different_seeds_differ() {
        let source = [0u8; 32];
        let addr_a = create_object_address(&source, b"seed_a");
        let addr_b = create_object_address(&source, b"seed_b");
        assert_ne!(addr_a, addr_b);
    }

    #[test]
    fn get_market_addr_returns_hex_prefixed() {
        let addr = get_market_addr(
            "BTC-USD",
            "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06",
        );
        assert!(addr.starts_with("0x"));
        assert_eq!(addr.len(), 66); // "0x" + 64 hex chars
    }

    #[test]
    fn get_market_addr_deterministic() {
        let global = "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06";
        let a1 = get_market_addr("BTC-USD", global);
        let a2 = get_market_addr("BTC-USD", global);
        assert_eq!(a1, a2);
    }

    #[test]
    fn get_market_addr_different_markets_differ() {
        let global = "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06";
        let btc = get_market_addr("BTC-USD", global);
        let eth = get_market_addr("ETH-USD", global);
        assert_ne!(btc, eth);
    }

    #[test]
    fn get_primary_subaccount_addr_returns_hex() {
        let addr = get_primary_subaccount_addr(
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "v0.4",
            "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06",
        );
        assert!(addr.starts_with("0x"));
        assert_eq!(addr.len(), 66);
    }

    #[test]
    fn get_primary_subaccount_addr_deterministic() {
        let account = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
        let compat = "v0.4";
        let package = "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06";
        let a1 = get_primary_subaccount_addr(account, compat, package);
        let a2 = get_primary_subaccount_addr(account, compat, package);
        assert_eq!(a1, a2);
    }

    #[test]
    fn get_primary_subaccount_different_accounts_differ() {
        let compat = "v0.4";
        let package = "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06";
        let a1 = get_primary_subaccount_addr(
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            compat,
            package,
        );
        let a2 = get_primary_subaccount_addr(
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            compat,
            package,
        );
        assert_ne!(a1, a2);
    }

    #[test]
    fn get_vault_share_address_returns_hex() {
        let addr = get_vault_share_address(
            "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        );
        assert!(addr.starts_with("0x"));
        assert_eq!(addr.len(), 66);
    }

    #[test]
    fn get_vault_share_address_deterministic() {
        let vault = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef";
        let a1 = get_vault_share_address(vault);
        let a2 = get_vault_share_address(vault);
        assert_eq!(a1, a2);
    }

    #[test]
    fn get_vault_share_address_different_vaults_differ() {
        let a1 = get_vault_share_address(
            "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        );
        let a2 = get_vault_share_address(
            "0x1111111111111111111111111111111111111111111111111111111111111111",
        );
        assert_ne!(a1, a2);
    }

    #[test]
    fn known_vector_create_object_address() {
        let source = [0u8; 32];
        let seed = b"";
        let addr = create_object_address(&source, seed);
        // SHA3-256 of 32 zero bytes + empty seed + 0xFE
        let mut hasher = sha3::Sha3_256::new();
        hasher.update([0u8; 32]);
        hasher.update(b"");
        hasher.update([0xFE]);
        let expected = hasher.finalize();
        assert_eq!(&addr[..], &expected[..]);
    }

    #[test]
    fn decode_hex_address_strips_prefix() {
        let with_prefix = decode_hex_address("0x0000000000000000000000000000000000000000000000000000000000000001");
        let without_prefix = decode_hex_address("0000000000000000000000000000000000000000000000000000000000000001");
        assert_eq!(with_prefix, without_prefix);
    }

    #[test]
    fn decode_hex_address_pads_short_addresses() {
        let short = decode_hex_address("0x1");
        assert_eq!(short.len(), 32);
        assert_eq!(short[31], 1);
        assert_eq!(short[0], 0);
    }
}
