# BDD Tests for Decibel SDK (Rust)

This directory contains Behavior Driven Development (BDD) tests using Cucumber/Gherkin for the Decibel Rust SDK.

## Overview

The BDD tests:
- Use the **cucumber** crate for Gherkin feature parsing
- Execute the 13 feature files from the repository root
- Provide cross-language behavioral testing consistency
- Serve as living documentation for SDK behavior

## Directory Structure

```
tests/
├── bdd/
│   ├── mod.rs              # BDD module definition
│   ├── world.rs            # Test world/context
│   └── steps/              # Step definitions
│       ├── mod.rs
│       ├── config_steps.rs
│       ├── market_data_steps.rs
│       ├── account_steps.rs
│       ├── order_steps.rs
│       └── position_steps.rs
└── bdd_runner_simple.rs    # Test entry point
```

## Running the Tests

### Prerequisites

Set up environment variables for tests:

```bash
# Create a .env file in the repository root
cat > .env << EOF
DECIBEL_NETWORK=testnet
DECIBEL_API_KEY=your_api_key_here
# Optional: For write operations
DECIBEL_PRIVATE_KEY=your_testnet_private_key
EOF
```

### Run All BDD Tests

```bash
# From the repository root
cd sdk-rust
cargo test --test bdd_runner_simple
```

### Run Specific Feature

```bash
# Run only market-data.feature scenarios
cargo test --test bdd_runner_simple -- market-data
```

### Run with Verbose Output

```bash
RUST_LOG=debug cargo test --test bdd_runner_simple -- --nocapture
```

## Feature Files

The 13 Gherkin feature files are located in the repository root:

- `sdk-configuration.feature` - SDK initialization and configuration
- `market-data.feature` - REST API market data queries
- `account-management.feature` - Account and subaccount operations
- `order-management.feature` - Order placement and management
- `positions-and-tpsl.feature` - Position and TP/SL management
- `twap-orders.feature` - TWAP order operations
- `websocket-subscriptions.feature` - Real-time WebSocket subscriptions
- `vaults.feature` - Vault creation and management
- `delegation-and-builder-fees.feature` - Trading delegation and builder fees
- `analytics-and-leaderboard.feature` - Performance analytics
- `error-handling.feature` - Error scenarios
- `utility-functions.feature` - Helper function testing
- `on-chain-view-functions.feature` - Blockchain view functions

## Step Implementation Status

| Feature | Step Definitions | Status |
|---------|------------------|--------|
| sdk-configuration.feature | config_steps.rs | ✅ Complete |
| market-data.feature | market_data_steps.rs | ✅ Complete |
| account-management.feature | account_steps.rs | 🚧 Stub |
| order-management.feature | order_steps.rs | 🚧 Stub |
| positions-and-tpsl.feature | position_steps.rs | 🚧 Stub |
| websocket-subscriptions.feature | - | ⏳ Pending |
| vaults.feature | - | ⏳ Pending |
| delegation-and-builder-fees.feature | - | ⏳ Pending |
| analytics-and-leaderboard.feature | - | ⏳ Pending |
| error-handling.feature | - | ⏳ Pending |
| utility-functions.feature | - | ⏳ Pending |
| on-chain-view-functions.feature | - | ⏳ Pending |

## Adding New Step Definitions

1. Create a new file in `tests/bdd/steps/` (e.g., `my_feature_steps.rs`)
2. Use the cucumber macros to define steps:

```rust
use cucumber::{given, when, then};
use crate::TestWorld;

#[given(expr = "I have an initialized {word} client")]
async fn given_client(world: &mut TestWorld, client_type: String) {
    // Implementation
}

#[when(expr = "I {word} the {word}")]
async fn do_action(world: &mut TestWorld, _verb: String, _resource: String) {
    // Implementation
}

#[then(expr = "I should receive {word}")]
async fn check_result(world: &mut TestWorld, _expected: String) {
    // Implementation
}
```

3. Export the steps in `tests/bdd/steps/mod.rs`:

```rust
pub mod my_feature_steps;
pub use my_feature_steps::*;
```

4. The steps will be automatically discovered by the cucumber framework

## Test Modes

### Mock Mode (Fast, Deterministic)
Uses wiremock to mock HTTP responses. No real API calls.

```bash
DECIBEL_USE_MOCK_SERVER=true cargo test --test bdd_runner_simple
```

### Live Mode (Real API Calls)
Makes real API calls to the Decibel testnet.

```bash
# Ensure DECIBEL_API_KEY is set
cargo test --test bdd_runner_simple
```

## Troubleshooting

### Feature Files Not Found

If tests can't find feature files, ensure you're running from the correct directory:

```bash
cd sdk-rust
cargo test --test bdd_runner_simple
```

Or create a symlink to the features directory:

```bash
cd sdk-rust
ln -s ../features features
```

### Private Key Errors

Write operations require `DECIBEL_PRIVATE_KEY` in `.env`. This should be a testnet private key, not a mainnet key.

### Timeouts

Increase timeout for slow tests:

```bash
cargo test --test bdd_runner_simple -- --test-threads=1
```

## CI Integration

BDD tests run automatically in CI via GitHub Actions. See `.github/workflows/bdd-tests.yml`.

## References

- [Cucumber for Rust Documentation](https://github.com/cucumber-rs/cucumber)
- [Gherkin Syntax Reference](https://cucumber.io/docs/gherkin/reference/)
- [Decibel SDK Specification](../../docs/specification.md)
- [Feature Audit Report](../../FEATURE_AUDIT_REPORT.md)
