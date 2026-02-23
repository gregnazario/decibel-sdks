# Multi-Language BDD Implementation Plan

## Overview

This document outlines the plan to implement functional BDD tests for all four language SDKs in the Decibel SDK project.

## Current Status

### Rust SDK ✅ COMPLETE
- **Client Implementation**: Full `DecibelReadClient` and `DecibelWriteClient` classes
- **BDD Framework**: Cucumber-based with 106+ functional step definitions
- **Test Files**:
  - `sdk-rust/tests/bdd/steps/config_steps.rs` (14 steps)
  - `sdk-rust/tests/bdd/steps/market_data_steps.rs` (35+ steps)
  - `sdk-rust/tests/bdd/steps/account_steps.rs` (18 steps)
  - `sdk-rust/tests/bdd/steps/order_steps.rs` (20 steps)
  - `sdk-rust/tests/bdd/steps/position_steps.rs` (19 steps)

### Go SDK 🔄 IN PROGRESS
- **Client Implementation**: Needs completion (partial implementation in `client.go`)
- **BDD Framework**: Godog-based (started)
- **Status**:
  - ✅ Config models available
  - ✅ Market models available
  - ✅ Account models available
  - ✅ Order models available
  - ✅ Position models available
  - ✅ Vault models available
  - 🔄 Client implementation needs completion
  - 🔄 BDD test structure started

### Kotlin SDK ⏳ PENDING
- **Client Implementation**: Not started
- **BDD Framework**: Cucumber-JVM (planned)
- **Status**:
  - ✅ Config models available
  - ✅ Basic models available
  - ⏳ Client implementation needed
  - ⏳ BDD test structure needed

### Swift SDK ⏳ PENDING
- **Client Implementation**: Not started
- **BDD Framework**: Quick/Nimble (planned, not Gherkin-based)
- **Status**:
  - ✅ Config models available
  - ✅ Basic models available
  - ⏳ Client implementation needed
  - ⏳ BDD test structure needed

## Implementation Strategy

### Phase 1: Complete Go SDK (Current)

#### Step 1: Complete Go Client Implementation
The Go client needs to be completed with proper type references to the models package. The current `client.go` has:
- HTTP client setup
- API request methods
- Error handling

But needs:
- Proper imports for the models package
- Type aliases or model references
- Completion of any missing API methods

#### Step 2: Create Go BDD Test Structure

**Directory Structure**:
```
sdk-go/tests/bdd/
├── config_steps.go          (created)
├── market_data_steps.go     (pending)
├── account_steps.go         (pending)
├── order_steps.go           (pending)
├── position_steps.go        (pending)
├── test_world.go            (pending)
└── bdd_test.go              (pending)
```

**TestWorld Structure**:
```go
type TestWorld struct {
    Config       *decibel.DecibelConfig
    ReadClient   *decibel.DecibelReadClient
    WriteClient  *decibel.DecibelWriteClient
    LastError    error
    Markets      []models.PerpMarketConfig
    MarketDepth  *models.MarketDepth
    MarketPrices []models.MarketPrice
    Positions    []models.UserPosition
    OpenOrders   []models.UserOpenOrder
    // ... other state fields
}
```

#### Step 3: Implement Go Step Definitions

**Config Steps** (14 steps):
- ✅ Started in `config_steps.go`
- Need to complete with proper imports

**Market Data Steps** (35+ steps):
- `Given("I have an initialized Decibel read client")`
- `When("I request all markets")`
- `Then("I should receive a list of market configurations")`
- `And("each market should have a market address")`
- `And("each market should have a market name")`
- `And("each market should have size decimals")`
- `And("each market should have price decimals")`
- `And("each market should have maximum leverage")`
- `And("each market should have minimum order size")`
- `And("each market should have lot size")`
- `And("each market should have tick size")`
- `When("I request the market with name {word}")`
- `Then("I should receive the {word} market configuration")`
- ... and more

**Account Steps** (18 steps):
- `Given("I have an initialized Decibel read client")`
- `Given("I have a subaccount address {string}")`
- `When("I request the account overview for a subaccount")`
- `Then("I should receive the account overview data")`
- `And("the overview should include the total margin")`
- ... and more

**Order Steps** (20 steps):
- `Given("I have an initialized Decibel write client")`
- `Given("I have configured my subaccount for the {word} market")`
- `When("I place a limit buy order")`
- `Then("the order should be accepted")`
- ... and more

**Position Steps** (19 steps):
- `Given("I have an open position in the {word} market")`
- `When("I request my positions")`
- `Then("I should receive my open positions")`
- ... and more

### Phase 2: Implement Kotlin SDK

#### Step 1: Create Kotlin Client
```kotlin
// File: src/main/kotlin/trade/decibel/sdk/client/DecibelReadClient.kt
class DecibelReadClient(
    private val config: DecibelConfig,
    private val apiKey: String?
) {
    suspend fun getAllMarkets(): List<PerpMarketConfig>
    suspend fun getMarketByName(name: String): PerpMarketConfig
    suspend fun getMarketDepth(marketName: String, limit: Int?): MarketDepth
    // ... all other API methods
}
```

#### Step 2: Set up Cucumber-JVM
**build.gradle.kts dependencies**:
```kotlin
testImplementation("io.cucumber:cucumber-java8:7.14.0")
testImplementation("io.cucumber:cucumber-junit:7.14.0")
testImplementation("org.junit.vintage:junit-vintage-engine:5.10.0")
```

#### Step 3: Create Kotlin BDD Structure
```
sdk-kotlin/src/test/kotlin/trade/decibel/sdk/bdd/
├── ConfigSteps.kt
├── MarketDataSteps.kt
├── AccountSteps.kt
├── OrderSteps.kt
├── PositionSteps.kt
├── TestWorld.kt
└── BddTest.kt
```

### Phase 3: Implement Swift SDK

#### Step 1: Create Swift Client
```swift
// File: Sources/DecibelSDK/Client/DecibelReadClient.swift
public class DecibelReadClient {
    private let config: DecibelConfig
    private let apiKey: String?

    public func getAllMarkets() async throws -> [PerpMarketConfig]
    public func getMarketByName(name: String) async throws -> PerpMarketConfig
    // ... all other API methods
}
```

#### Step 2: Set up Quick/Nimble (BDD-style testing)
**Package.swift dependencies**:
```swift
dependencies: [
    .package(url: "https://github.com/Quick/Quick.git", from: "7.0.0"),
    .package(url: "https://github.com/Quick/Nimble.git", from: "12.0.0")
]
```

#### Step 3: Create Swift BDD Structure
```
sdk-swift/Tests/DecibelSDKTests/BDD/
├── ConfigSpec.swift
├── MarketDataSpec.swift
├── AccountSpec.swift
├── OrderSpec.swift
└── PositionSpec.swift
```

## Go BDD Implementation Details

### Dependencies
Add to `go.mod`:
```go
require (
    github.com/cucumber/godog v0.14.1
)
```

### Test Structure

**test_world.go**:
```go
package bdd

import (
	"decibel"
	"decibel/models"

	"github.com/cucumber/godog"
)

type TestWorld struct {
    // Configuration
    Config  *decibel.DecibelConfig
    APIKey  string

    // Clients
    ReadClient   *decibel.DecibelReadClient
    WriteClient  *decibel.DecibelWriteClient

    // Error state
    LastError    error

    // Market data
    Markets         []models.PerpMarketConfig
    MarketDepth     *models.MarketDepth
    MarketPrices    []models.MarketPrice
    Candlesticks    []models.Candlestick
    MarketContexts  []models.MarketContext
    MarketTrades    []models.MarketTrade

    // Account data
    AccountOverview *models.AccountOverview
    Positions       []models.UserPosition
    OpenOrders      []models.UserOpenOrder
    Subaccounts     []models.UserSubaccount
    Delegations     []models.Delegation

    // Test data
    TestMarketName      string
    TestSubaccountAddr  string
}

func NewTestWorld() *TestWorld {
    return &TestWorld{
        APIKey: os.Getenv("DECIBEL_API_KEY"),
    }
}

func (w *TestWorld) Clear() {
    w.Config = nil
    w.ReadClient = nil
    w.WriteClient = nil
    w.LastError = nil
    w.Markets = nil
    w.MarketDepth = nil
    w.MarketPrices = nil
    // ... clear other fields
}
```

**bdd_test.go**:
```go
package bdd

import (
    "testing"
    "github.com/cucumber/godog"
)

func TestFeatures(t *testing.T) {
    suite := godog.TestSuite{
        ScenarioInitializer: InitializeScenario,
        Options: &godog.Options{
            Format:   "pretty",
            Paths:    []string{"../../features"},
            TestingT: t,
        },
    }

    if suite.Run() != 0 {
        t.Fatal("failed to run feature suite")
    }
}

func InitializeScenario(ctx *godog.ScenarioContext) {
    world := NewTestWorld()

    // Register step definitions
    configSteps := NewConfigSteps(world)
    configSteps.RegisterSteps(ctx)

    marketDataSteps := NewMarketDataSteps(world)
    marketDataSteps.RegisterSteps(ctx)

    accountSteps := NewAccountSteps(world)
    accountSteps.RegisterSteps(ctx)

    orderSteps := NewOrderSteps(world)
    orderSteps.RegisterSteps(ctx)

    positionSteps := NewPositionSteps(world)
    positionSteps.RegisterSteps(ctx)

    // Clear world before each scenario
    ctx.Before(func(ctx context.Context, sc *godog.Scenario) (context.Context, error) {
        world.Clear()
        return ctx, nil
    })
}
```

## Kotlin BDD Implementation Details

### Cucumber-JVM Setup

**Cucumber Test Runner**:
```kotlin
package trade.decibel.sdk.bdd

import io.cucumber.junit.Cucumber
import io.cucumber.junit.CucumberOptions
import org.junit.runner.RunWith

@RunWith(Cucumber::class)
@CucumberOptions(
    features = ["../../features"],
    glue = ["trade.decibel.sdk.bdd"],
    plugin = ["pretty", "html:target/cucumber-report.html"]
)
class CucumberTest
```

**TestWorld**:
```kotlin
package trade.decibel.sdk.bdd

import trade.decibel.sdk.config.DecibelConfig
import trade.decibel.sdk.models.*

class TestWorld {
    var config: DecibelConfig? = null
    var readClient: DecibelReadClient? = null
    var writeClient: DecibelWriteClient? = null
    var lastError: Throwable? = null

    var markets: List<PerpMarketConfig>? = null
    var marketDepth: MarketDepth? = null
    var marketPrices: List<MarketPrice>? = null
    // ... other state

    fun clear() {
        config = null
        readClient = null
        writeClient = null
        lastError = null
        // ... clear other fields
    }
}
```

**Step Definition Example**:
```kotlin
package trade.decibel.sdk.bdd

import io.cucumber.java8.En
import trade.decibel.sdk.DecibelReadClient
import trade.decibel.sdk.config.DecibelConfig

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
            assertNotNull(world.markets, "Markets should not be null")
            assertTrue(world.markets!!.isNotEmpty(), "Should have at least one market")
        }

        And("each market should have a market name") {
            for (market in world.markets!!) {
                assertTrue(market.marketName.isNotEmpty(), "Market name should not be empty")
            }
        }
    }
}
```

## Swift BDD Implementation Details

### Quick/Nimble Setup

Since Swift doesn't have a native Gherkin/Cucumber implementation, we'll use Quick/Nimble which provides BDD-style testing with `describe`/`context`/`it` syntax.

**Test Spec Example**:
```swift
import Quick
import Nimble
import DecibelSDK

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

            context("when using mainnet preset") {
                it("creates a valid read client") {
                    world.config = DecibelConfig.MAINNET
                    expect{ try DecibelReadClient(config: world.config, apiKey: nil) }.notTo(throwError())
                }

                it("configures for mainnet environment") {
                    world.config = DecibelConfig.MAINNET
                    expect(world.config.network).to(equal(Network.mainnet))
                    expect(world.config.tradingHttpUrl).to(equal("https://api.decibel.trade"))
                }

                it("has correct chain ID") {
                    world.config = DecibelConfig.MAINNET
                    expect(world.config.chainId).to(equal(1))
                }
            }

            context("when using testnet preset") {
                it("creates a valid read client") {
                    world.config = DecibelConfig.TESTNET
                    expect{ try DecibelReadClient(config: world.config, apiKey: nil) }.notTo(throwError())
                }

                it("configures for testnet environment") {
                    world.config = DecibelConfig.TESTNET
                    expect(world.config.network).to(equal(Network.testnet))
                    expect(world.config.tradingHttpUrl).to(equal("https://api.testnet.decibel.trade"))
                }
            }

            context("when requesting all markets") {
                it("receives a list of market configurations") async throws {
                    world.config = DecibelConfig.TESTNET
                    world.readClient = try DecibelReadClient(config: world.config, apiKey: nil)
                    world.markets = try await world.readClient.getAllMarkets()

                    expect(world.markets).toNot(beEmpty())
                    expect(world.markets.first?.marketName).toNot(beEmpty())
                }

                it("validates market properties") async throws {
                    world.config = DecibelConfig.TESTNET
                    world.readClient = try DecibelReadClient(config: world.config, apiKey: nil)
                    world.markets = try await world.readClient.getAllMarkets()

                    for market in world.markets {
                        expect(market.marketName).toNot(beEmpty())
                        expect(market.marketAddr).toNot(beEmpty())
                        expect(market.szDecimals).to(beGreaterThanOrEqualTo(0))
                        expect(market.pxDecimals).to(beGreaterThanOrEqualTo(0))
                        expect(market.maxLeverage).to(beGreaterThan(0))
                    }
                }
            }
        }
    }
}
```

**TestWorld**:
```swift
import Foundation
import DecibelSDK

class TestWorld {
    var config: DecibelConfig?
    var readClient: DecibelReadClient?
    var writeClient: DecibelWriteClient?
    var lastError: Error?

    var markets: [PerpMarketConfig] = []
    var marketDepth: MarketDepth?
    var marketPrices: [MarketPrice] = []
    // ... other state

    func clear() {
        config = nil
        readClient = nil
        writeClient = nil
        lastError = nil
        markets.removeAll()
        marketDepth = nil
        marketPrices.removeAll()
        // ... clear other fields
    }
}
```

## Summary

### Current Progress
- **Rust SDK**: ✅ Complete (106+ functional step definitions)
- **Go SDK**: 🔄 In Progress (client implementation + BDD structure started)
- **Kotlin SDK**: ⏳ Pending (client + BDD framework needed)
- **Swift SDK**: ⏳ Pending (client + BDD framework needed)

### Next Steps
1. Complete Go client implementation with proper model imports
2. Finish Go BDD step definitions for all feature files
3. Implement Kotlin client and Cucumber-JVM test framework
4. Implement Swift client and Quick/Nimble test framework

### Total Coverage Goal
- 13 Gherkin feature files
- ~234 scenarios total
- 4 language SDKs
- **Estimated total functional step definitions: 400+ across all languages**

---

**Last Updated**: 2026-02-23
