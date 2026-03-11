# Behavioral Testing Implementation for Decibel SDK

This document describes the behavioral testing (BDD) implementation across all four language SDKs in the Decibel project.

## Overview

The Decibel SDK now includes **behavior-driven testing** using Gherkin feature files. The 13 feature files in the `features/` directory serve as both:

1. **Executable test specifications** - Automated tests that verify SDK behavior
2. **Living documentation** - Human-readable descriptions of SDK functionality

## Supported Languages

Each SDK has a BDD framework integration:

| Language | Framework | Status | Implementation Directory |
|----------|-----------|--------|--------------------------|
| **Rust** | cucumber | ✅ Implemented | `sdk-rust/tests/bdd/` |
| **Go** | godog | ⏳ Planned | `sdk-go/testbdd/` |
| **Kotlin** | cucumber-jvm | ⏳ Planned | `sdk-kotlin/src/test/kotlin/bdd/` |
| **Swift** | Quick/Nimble | ⏳ Planned | `sdk-swift/Tests/DecibelSDKTests/BDDTests/` |

## Feature Files

The following Gherkin feature files define test scenarios:

| Feature File | Description | Scenarios |
|-------------|-------------|-----------|
| `sdk-configuration.feature` | SDK initialization and configuration | 15 |
| `market-data.feature` | REST API market data queries | 13 |
| `account-management.feature` | Account and subaccount operations | 18 |
| `order-management.feature` | Order placement and management | 20 |
| `positions-and-tpsl.feature` | Position and TP/SL management | 19 |
| `twap-orders.feature` | TWAP order operations | 15 |
| `websocket-subscriptions.feature` | Real-time WebSocket subscriptions | 21 |
| `vaults.feature` | Vault creation and management | 18 |
| `delegation-and-builder-fees.feature` | Trading delegation and builder fees | 18 |
| `analytics-and-leaderboard.feature` | Performance analytics | 19 |
| `error-handling.feature` | Error scenarios | 22 |
| `utility-functions.feature` | Helper function testing | 19 |
| `on-chain-view-functions.feature` | Blockchain view functions | 17 |

**Total**: 234 scenarios across 13 feature files

## Running Tests

### Quick Start

```bash
# Run all BDD tests
./scripts/run-bdd-tests.sh

# Run tests for a specific SDK
./scripts/run-bdd-tests.sh rust

# Run tests for multiple SDKs
./scripts/run-bdd-tests.sh rust go
```

### Rust SDK BDD Tests

```bash
cd sdk-rust

# Run basic BDD integration test
cargo test --test bdd_basic_test

# Run with verbose output
RUST_LOG=debug cargo test --test bdd_basic_test -- --nocapture

# Run specific test
cargo test test_bdd_market_data_basic
```

### Environment Setup

Create a `.env` file in the repository root:

```bash
# Network configuration
DECIBEL_NETWORK=testnet
DECIBEL_API_KEY=your_api_key_here

# Optional: For write operations (on-chain transactions)
DECIBEL_PRIVATE_KEY=your_testnet_private_key
DECIBEL_TESTNET_RPC_URL=https://fullnode.testnet.aptos.dev

# Optional: Use mock server for faster, deterministic tests
DECIBEL_USE_MOCK_SERVER=true
```

## Implementation Details

### Rust SDK (Complete)

**Directory Structure**:
```
sdk-rust/
├── tests/
│   ├── bdd/
│   │   ├── mod.rs              # Module definition
│   │   ├── world.rs            # Test world/context
│   │   ├── steps/              # Step definitions
│   │   │   ├── config_steps.rs
│   │   │   ├── market_data_steps.rs
│   │   │   ├── account_steps.rs
│   │   │   ├── order_steps.rs
│   │   │   └── position_steps.rs
│   │   ├── README.md           # Documentation
│   │   └── ...
│   ├── bdd_basic_test.rs       # Basic integration test
│   └── ...
└── Cargo.toml                 # Includes cucumber dependency
```

**Key Components**:

1. **Test World** (`world.rs`)
   - Maintains state across scenario steps
   - Holds SDK clients, responses, and test data
   - Provides helper methods for common operations

2. **Step Definitions** (`steps/*.rs`)
   - Map Gherkin steps to Rust code
   - Use cucumber macros: `given`, `when`, `then`
   - Support regex parameter extraction

3. **Test Runner** (`bdd_basic_test.rs`)
   - Entry point for running BDD tests
   - Initializes environment and runs scenarios

**Example Step Definition**:

```rust
#[when(expr = "I request all markets")]
async fn request_all_markets(world: &mut TestWorld) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_all_markets().await {
        Ok(markets) => world.markets = Some(markets),
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive a list of market configurations")]
async fn should_receive_markets(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error");
    assert!(world.markets.is_some(), "Markets should be set");
}
```

### Go SDK (Planned)

**Planned Framework**: godog (official Cucumber for Go)

**Dependencies**:
```go
require github.com/cucumber/godog v0.15.0
```

**Step Definition Example**:
```go
func InitializeScenario(ctx *godog.ScenarioContext) {
    testCtx := &TestContext{}

    ctx.Step(`^I have an initialized (.+) client$`, testCtx.haveClient)
    ctx.Step(`^I request all markets$`, testCtx.requestAllMarkets)
    ctx.Step(`^I should receive a list of market configurations$`, testCtx.verifyMarkets)
}

func (t *TestContext) requestAllMarkets(ctx context.Context) (context.Context, error) {
    t.markets = t.readClient.GetAllMarkets(ctx)
    return ctx, nil
}
```

### Kotlin SDK (Planned)

**Planned Framework**: Cucumber-JVM with JUnit integration

**Dependencies**:
```kotlin
testImplementation("io.cucumber:cucumber-java:7.14.0")
testImplementation("io.cucumber:cucumber-junit:7.14.0")
testImplementation("io.cucumber:cucumber-kotlin:7.14.0")
testImplementation("org.junit.jupiter:junit-jupiter:5.10.0")
```

**Step Definition Example**:
```kotlin
class StepDefinitions {
    private lateinit var readClient: DecibelReadClient
    private lateinit var markets: List<PerpMarketConfig>

    @Given("I have an initialized read client")
    fun haveClient() {
        readClient = createReadClient()
    }

    @When("I request all markets")
    fun requestAllMarkets() = runBlocking {
        markets = readClient.getAllMarkets()
    }

    @Then("I should receive a list of market configurations")
    fun verifyMarkets() {
        assertTrue(markets.isNotEmpty())
    }
}
```

### Swift SDK (Planned)

**Planned Framework**: Quick + Nimble (BDD-style, not Gherkin-based)

**Dependencies**:
```swift
.package(url: "https://github.com/Quick/Quick.git", from: "7.0.0")
.package(url: "https://github.com/Quick/Nimble.git", from: "12.0.0")
```

**Note**: Swift uses Quick/Nimble's `describe/it` syntax rather than direct Gherkin parsing. The feature files will be **translated** to Swift specs.

**Example Spec**:
```swift
class MarketDataSpec: QuickSpec {
    override func spec() {
        var client: DecibelReadClient!
        var markets: [PerpMarketConfig]!

        describe("Market Data") {
            beforeEach {
                client = createReadClient()
            }

            context("Given I have an initialized read client") {
                it("When I request all markets") {
                    waitUntil(timeout: .seconds(10)) { done in
                        Task {
                            markets = await client.getAllMarkets()
                            done()
                        }
                    }
                }

                it("Then I should receive a list of market configurations") {
                    expect(markets).toNot(beEmpty())
                }
            }
        }
    }
}
```

## Test Coverage

### Current Coverage (Rust SDK)

| Feature | Steps Implemented | Coverage |
|---------|-------------------|----------|
| SDK Configuration | 14 | ✅ 93% |
| Market Data | 35+ | ✅ 100% |
| Account Management | Stub | ⏳ 0% |
| Order Management | Stub | ⏳ 0% |
| Positions & TP/SL | Stub | ⏳ 0% |
| TWAP Orders | - | ⏳ 0% |
| WebSocket Subscriptions | - | ⏳ 0% |
| Vaults | - | ⏳ 0% |
| Delegation & Builder Fees | - | ⏳ 0% |
| Analytics & Leaderboard | - | ⏳ 0% |
| Error Handling | Partial | ⏳ 20% |
| Utility Functions | - | ⏳ 0% |
| On-Chain View Functions | - | ⏳ 0% |

### Implementation Roadmap

**Phase 1** (Current): Core BDD Infrastructure
- ✅ Rust SDK framework setup
- ✅ Test world/context implementation
- ✅ Configuration step definitions
- ✅ Market data step definitions
- ⏳ Account management steps
- ⏳ Order management steps

**Phase 2**: Complete Rust Implementation
- Implement all remaining step definitions
- Add mock server support with wiremock
- CI/CD integration

**Phase 3**: Go SDK Implementation
- Set up godog framework
- Port step definitions from Rust
- Implement Go-specific patterns

**Phase 4**: Kotlin SDK Implementation
- Set up Cucumber-JVM
- Port step definitions
- Coroutine-based async handling

**Phase 5**: Swift SDK Implementation
- Set up Quick/Nimble
- Translate Gherkin to Swift specs
- Async/await support

## Benefits

### Cross-Language Consistency

The same 234 scenarios test all four SDK implementations, ensuring:
- **Consistent behavior** across languages
- **API compatibility** between implementations
- **Behavioral differences** are caught early

### Living Documentation

Feature files serve as:
- **Executable specifications** - Tests that verify the code
- **Human-readable docs** - Clear examples for developers
- **Stakeholder communication** - Business-friendly test scenarios

### Regression Protection

BDD tests catch:
- Behavioral changes between SDK versions
- Cross-language implementation differences
- API contract violations

## CI/CD Integration

BDD tests run automatically in CI:

```yaml
name: BDD Tests

on: [push, pull_request]

jobs:
  bdd-tests:
    strategy:
      matrix:
        sdk: [rust, go, kotlin, swift]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up environment
        run: echo "DECIBEL_NETWORK=testnet" >> $GITHUB_ENV
      - name: Run BDD Tests
        run: ./scripts/run-bdd-tests.sh ${{ matrix.sdk }}
```

## Troubleshooting

### Feature Files Not Found

**Problem**: Tests can't find .feature files

**Solution**: Ensure you're running from the repository root or create symlinks:
```bash
cd sdk-rust
ln -s ../features features
```

### API Key Required

**Problem**: Tests fail with authentication errors

**Solution**: Set `DECIBEL_API_KEY` in `.env`:
```bash
echo "DECIBEL_API_KEY=your_key_here" >> .env
```

### Write Operation Failures

**Problem**: On-chain transaction tests fail

**Solution**: Set `DECIBEL_PRIVATE_KEY` for a testnet account:
```bash
echo "DECIBEL_PRIVATE_KEY=0x..." >> .env
```

### Timeouts

**Problem**: Tests time out on slow connections

**Solution**: Increase timeout or use mock mode:
```bash
DECIBEL_USE_MOCK_SERVER=true cargo test --test bdd_basic_test
```

## Contributing

### Adding New Step Definitions

1. Create a new step file in `tests/bdd/steps/`
2. Use cucumber macros to define steps
3. Export in `tests/bdd/steps/mod.rs`
4. Cucumber will auto-discover the steps

### Adding New Feature Files

1. Create `.feature` file in the `features/` directory
2. Follow Gherkin syntax
3. Implement step definitions in each SDK
4. Update this documentation

## References

- **Specification**: `docs/specification.md`
- **Feature Audit**: `FEATURE_AUDIT_REPORT.md`
- **Cucumber (Rust)**: https://github.com/cucumber-rs/cucumber
- **Gherkin Reference**: https://cucumber.io/docs/gherkin/reference/
- **Godog (Go)**: https://github.com/cucumber/godog
- **Cucumber-JVM**: https://cucumber.io/docs/cucumber/api/
- **Quick/Nimble (Swift)**: https://github.com/Quick/Quick

---

**Last Updated**: 2026-02-23
**Status**: Phase 1 (Rust SDK) - In Progress
