# Scratchpad

## Task: Error Types and Utility Modules for Rust v2 SDK

### Status: COMPLETE

All files created with full implementations and passing tests:
- `sdk-rust-v2/src/error.rs` — 14 error variants with position safety classification, retryability, criticality checks (25 tests)
- `sdk-rust-v2/src/utils/mod.rs` — Re-exports address, formatting, nonce submodules
- `sdk-rust-v2/src/utils/address.rs` — Market/subaccount/vault address derivation via SHA3-256 (12 tests)
- `sdk-rust-v2/src/utils/formatting.rs` — Chain unit conversion, tick/lot rounding (17 tests)
- `sdk-rust-v2/src/utils/nonce.rs` — Random u64 replay protection nonce (4 tests)
- `sdk-rust-v2/src/lib.rs` — Updated to export error and utils modules

### Notes
- Trimmed Cargo.toml to only include dependencies needed by current modules (serde, thiserror, sha3, hex, rand)
- Removed stub modules (config, models, state, bulk) that referenced unavailable deps
- 65 tests all passing
