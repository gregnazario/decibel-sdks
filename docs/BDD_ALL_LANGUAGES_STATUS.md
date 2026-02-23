# BDD Implementation Status - All Languages

## Executive Summary

The Decibel SDK project has **13 Gherkin feature files** with approximately **234 scenarios** that need to be tested across **4 language SDKs** (Rust, Go, Kotlin, Swift).

### Current Implementation Status

| Language | Client Status | BDD Framework | Step Definitions | Functional |
|----------|--------------|---------------|------------------|------------|
| **Rust** | ✅ Complete | Cucumber 0.21 | 106+ | ✅ Yes |
| **Go** | 🔄 Partial | Godog | 0 (started) | ❌ No |
| **Kotlin** | ❌ None | Cucumber-JVM | 0 | ❌ No |
| **Swift** | ❌ None | Quick/Nimble | 0 | ❌ No |

---

## Detailed Status by Language

### 1. Rust SDK ✅ COMPLETE

**Package**: `sdk-rust`

**Client Implementation**: ✅ FULLY IMPLEMENTED
- `DecibelReadClient` with 20+ API methods
- `DecibelWriteClient` with transaction support
- Full error handling
- WebSocket client

**BDD Framework**: ✅ cucumber crate (v0.21)

**Step Definitions**: ✅ 106+ FUNCTIONAL STEPS

| Feature File | Steps | Status |
|-------------|-------|--------|
| `sdk-configuration.feature` | 14 | ✅ Complete |
| `market-data.feature` | 35+ | ✅ Complete |
| `account-management.feature` | 18 | ✅ Complete |
| `order-management.feature` | 20 | ✅ Complete |
| `positions-and-tpsl.feature` | 19 | ✅ Complete |
| **Total** | **106+** | **✅ Complete** |

**Example Implementation**:
```rust
#[when("I request all markets")]
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

#[then("each market should have a market name")]
async fn check_market_name(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(!market.market_name.is_empty(), "Market name should not be empty");
    }
}
```

**Files**:
- `sdk-rust/tests/bdd/steps/config_steps.rs`
- `sdk-rust/tests/bdd/steps/market_data_steps.rs`
- `sdk-rust/tests/bdd/steps/account_steps.rs`
- `sdk-rust/tests/bdd/steps/order_steps.rs`
- `sdk-rust/tests/bdd/steps/position_steps.rs`

---

### 2. Go SDK 🔄 IN PROGRESS

**Package**: `sdk-go`

**Client Implementation**: 🔄 PARTIAL
- Config: ✅ Complete (`config.go`)
- Models: ✅ Complete (market, account, order, position, vault)
- **Client**: 🔄 Partial (`client.go` created but needs completion)

**Current Issue**:
The `client.go` file references types without proper imports to the `models` package. Needs:
1. Proper imports: `import "decibel/models"`
2. Type aliases or full type names
3. Completion of all API methods

**Models Available**:
```go
// In models/market.go
type PerpMarketConfig struct { ... }
type MarketDepth struct { ... }
type MarketPrice struct { ... }
// ... etc

// In models/account.go
type AccountOverview struct { ... }
type UserSubaccount struct { ... }
// ... etc

// In models/order.go
type UserOpenOrder struct { ... }
type UserOrderHistoryItem struct { ... }
// ... etc
```

**BDD Framework**: ✅ Godog (ready to implement)

**Step Definitions**: 🔄 STARTED
- `tests/bdd/config_steps.go` created (14 steps)
- Needs: market_data_steps.go, account_steps.go, order_steps.go, position_steps.go

**To Complete Go SDK**:
1. Fix `client.go` imports to use models package
2. Complete any missing API methods
3. Implement remaining step definition files
4. Create `test_world.go` for state management
5. Create `bdd_test.go` as test runner

---

### 3. Kotlin SDK ⏳ PENDING

**Package**: `sdk-kotlin`

**Client Implementation**: ❌ NOT STARTED
- Config: ✅ Complete (`DecibelConfig.kt`)
- Models: ✅ Complete (Market, Account, Order, Position, Vault)
- **Client**: ❌ Needs implementation

**BDD Framework**: ⏳ Cucumber-JVM (not set up)

**Required Implementation**:

**1. Client Class** (`src/main/kotlin/trade/decibel/sdk/client/DecibelReadClient.kt`):
```kotlin
package trade.decibel.sdk.client

import trade.decibel.sdk.config.DecibelConfig
import trade.decibel.sdk.models.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*

class DecibelReadClient(
    private val config: DecibelConfig,
    private val apiKey: String? = null
) {
    private val client = HttpClient {
        expectSuccess = false
    }

    suspend fun getAllMarkets(): List<PerpMarketConfig> {
        return client.get("${config.tradingHttpUrl}/markets") {
            apiKey?.let { header("x-api-key", it) }
        }.body()
    }

    suspend fun getMarketByName(name: String): PerpMarketConfig {
        return client.get("${config.tradingHttpUrl}/markets/$name") {
            apiKey?.let { header("x-api-key", it) }
        }.body()
    }

    // ... 18+ more API methods needed
}
```

**2. Build Configuration** (`build.gradle.kts`):
```kotlin
dependencies {
    // Add HTTP client
    implementation("io.ktor:ktor-client-core:2.3.4")
    implementation("io.ktor:ktor-client-cio:2.3.4")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.4")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.4")

    // BDD testing
    testImplementation("io.cucumber:cucumber-java8:7.14.0")
    testImplementation("io.cucumber:cucumber-junit:7.14.0")
    testImplementation("org.junit.vintage:junit-vintage-engine:5.10.0")
}
```

**3. Test Structure** (`src/test/kotlin/trade/decibel/sdk/bdd/`):
- `TestWorld.kt` - State management
- `ConfigSteps.kt` - Configuration step definitions
- `MarketDataSteps.kt` - Market data step definitions
- `AccountSteps.kt` - Account step definitions
- `OrderSteps.kt` - Order step definitions
- `PositionSteps.kt` - Position step definitions
- `BddTest.kt` - Cucumber test runner

**4. Step Definition Example**:
```kotlin
package trade.decibel.sdk.bdd

import io.cucumber.java8.En
import kotlinx.coroutines.runBlocking

class ConfigSteps(private val world: TestWorld) : En {
    init {
        Given("I have an initialized Decibel read client") {
            world.readClient = DecibelReadClient(world.config!!, null)
        }

        When("I request all markets") {
            runBlocking {
                try {
                    world.markets = world.readClient!!.getAllMarkets()
                } catch (e: Exception) {
                    world.lastError = e
                }
            }
        }

        Then("I should receive a list of market configurations") {
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.markets)
            assertTrue(world.markets!!.isNotEmpty())
        }

        And("each market should have a market name") {
            for (market in world.markets!!) {
                assertTrue(market.marketName.isNotEmpty())
            }
        }
    }
}
```

---

### 4. Swift SDK ⏳ PENDING

**Package**: `sdk-swift`

**Client Implementation**: ❌ NOT STARTED
- Config: ✅ Complete (`DecibelConfig.swift`)
- Models: ✅ Complete (Market, Account, Order, Position, Vault)
- **Client**: ❌ Needs implementation

**BDD Framework**: ⏳ Quick/Nimble (not set up)

**Important Note**: Swift does not have a native Gherkin/Cucumber implementation. We will use **Quick/Nimble** which provides BDD-style testing with `describe`/`context`/`it` syntax.

**Required Implementation**:

**1. Client Class** (`Sources/DecibelSDK/Client/DecibelReadClient.swift`):
```swift
import Foundation

public class DecibelReadClient {
    private let config: DecibelConfig
    private let apiKey: String?
    private let session: URLSession

    public init(config: DecibelConfig, apiKey: String? = nil) {
        self.config = config
        self.apiKey = apiKey
        self.session = URLSession.shared
    }

    public func getAllMarkets() async throws -> [PerpMarketConfig] {
        var request = URLRequest(url: URL(string: "\(config.tradingHttpUrl)/markets")!)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let apiKey = apiKey {
            request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        }

        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode([PerpMarketConfig].self, from: data)
    }

    // ... 18+ more API methods needed
}
```

**2. Package Dependencies** (`Package.swift`):
```swift
dependencies: [
    .package(url: "https://github.com/Quick/Quick.git", from: "7.0.0"),
    .package(url: "https://github.com/Quick/Nimble.git", from: "12.0.0")
],
targets: [
    .testTarget(
        name: "DecibelSDKTests",
        dependencies: ["DecibelSDK", "Quick", "Nimble"]
    )
]
```

**3. Test Structure** (`Tests/DecibelSDKTests/BDD/`):
- `TestWorld.swift` - State management
- `ConfigSpec.swift` - Configuration specs
- `MarketDataSpec.swift` - Market data specs
- `AccountSpec.swift` - Account specs
- `OrderSpec.swift` - Order specs
- `PositionSpec.swift` - Position specs

**4. Test Spec Example**:
```swift
import Quick
import Nimble
@testable import DecibelSDK

final class ConfigSpec: QuickSpec {
    override class func spec() {
        describe("SDK Configuration") {
            var world: TestWorld!

            beforeEach {
                world = TestWorld()
            }

            afterEach {
                world.clear()
            }

            context("when requesting all markets") {
                it("receives a list of market configurations") async throws {
                    world.config = DecibelConfig.TESTNET
                    world.readClient = try DecibelReadClient(config: world.config, apiKey: nil)
                    world.markets = try await world.readClient.getAllMarkets()

                    expect(world.markets).toNot(beEmpty())
                }

                it("validates market properties") async throws {
                    world.config = DecibelConfig.TESTNET
                    world.readClient = try DecibelReadClient(config: world.config, apiKey: nil)
                    world.markets = try await world.readClient.getAllMarkets()

                    for market in world.markets {
                        expect(market.marketName).toNot(beEmpty())
                        expect(market.marketAddr).toNot(beEmpty())
                        expect(market.szDecimals).to(beGreaterThanOrEqualTo(0))
                        expect(market.maxLeverage).to(beGreaterThan(0))
                    }
                }
            }
        }
    }
}
```

---

## Implementation Priority & Effort Estimate

### Phase 1: Complete Go SDK (2-3 days)
- [ ] Fix `client.go` imports and complete API methods
- [ ] Create `test_world.go` for state management
- [ ] Implement `market_data_steps.go` (35+ steps)
- [ ] Implement `account_steps.go` (18 steps)
- [ ] Implement `order_steps.go` (20 steps)
- [ ] Implement `position_steps.go` (19 steps)
- [ ] Create `bdd_test.go` runner

### Phase 2: Implement Kotlin SDK (3-4 days)
- [ ] Create `DecibelReadClient.kt` with 20+ API methods
- [ ] Set up Cucumber-JVM dependencies
- [ ] Create `TestWorld.kt` for state management
- [ ] Implement all step definition files (106+ steps)
- [ ] Create Cucumber test runner

### Phase 3: Implement Swift SDK (3-4 days)
- [ ] Create `DecibelReadClient.swift` with 20+ API methods
- [ ] Set up Quick/Nimble dependencies
- [ ] Create `TestWorld.swift` for state management
- [ ] Implement all test specs (106+ step equivalents)
- [ ] Configure test targets

---

## Summary Table

| Component | Rust | Go | Kotlin | Swift |
|-----------|------|----|--------|------|
| **Config Models** | ✅ | ✅ | ✅ | ✅ |
| **Data Models** | ✅ | ✅ | ✅ | ✅ |
| **Read Client** | ✅ | 🔄 | ❌ | ❌ |
| **Write Client** | ✅ | ❌ | ❌ | ❌ |
| **BDD Framework** | ✅ | ✅ | ⏳ | ⏳ |
| **Config Steps** | ✅ (14) | 🔄 (14) | ❌ | ❌ |
| **Market Steps** | ✅ (35+) | ❌ | ❌ | ❌ |
| **Account Steps** | ✅ (18) | ❌ | ❌ | ❌ |
| **Order Steps** | ✅ (20) | ❌ | ❌ | ❌ |
| **Position Steps** | ✅ (19) | ❌ | ❌ | ❌ |
| **Total Steps** | **106+** | **14/106+** | **0/106+** | **0/106+** |
| **Functional** | ✅ | ❌ | ❌ | ❌ |

---

## Recommendation

Given the current state:

1. **Rust SDK is production-ready** for BDD testing with 106+ functional step definitions
2. **Go SDK needs client completion** before BDD tests can be functional
3. **Kotlin and Swift SDKs need full client implementation** before any BDD testing can be done

**Suggested approach**:
- Focus on completing the Go SDK first (closest to being ready)
- Use the Rust implementation as a reference for both API client design and BDD test structure
- Implement Kotlin and Swift clients following the same patterns

**Files created to assist**:
- `docs/BDD_MULTI_LANGUAGE_IMPLEMENTATION.md` - Detailed implementation guide
- `sdk-go/client.go` - Go client (partial, needs completion)
- `sdk-go/tests/bdd/config_steps.go` - Go config steps (partial)

---

**Last Updated**: 2026-02-23
