# Decibel Cross-Platform SDK Implementation Plan

## Overview

Build SDKs for Decibel (on-chain perpetual futures exchange on Aptos) in **Rust**, **Swift**, **Kotlin**, and **Go** based on the comprehensive specification in `docs/specification.md` and the reference TypeScript SDK (`@decibeltrade/sdk` v0.3.1).

## Methodology

- **TDD (Test-Driven Development)**: Write tests first, then implement to pass them
- **BDD (Behavior-Driven Development)**: Write behavior specifications as test scenarios
- **Language Idiomatic**: Each SDK follows the conventions and best practices of its language
- **High Performance**: Connection pooling, caching, zero-copy where possible
- **Full API Coverage**: REST, WebSocket, and on-chain transaction support

## Phase 1: Specification & Design (COMPLETE)

- [x] Research Decibel documentation at docs.decibel.trade
- [x] Analyze TypeScript SDK (`@decibeltrade/sdk` v0.3.1)
- [x] Create comprehensive specification document (`docs/specification.md`)
- [x] Iterate specification 5 times for completeness
- [x] Document all data models, API endpoints, WebSocket topics
- [x] Define required vs optional features

## Phase 2: BDD Test Suites

Write comprehensive behavior-driven test suites for each SDK before implementation.

### Test Categories
1. **Configuration Tests**: Preset configs, custom configs, validation
2. **Model Tests**: Serialization/deserialization of all data types
3. **REST Client Tests**: All API endpoint calls with mock responses
4. **WebSocket Tests**: Connection, subscription, unsubscription, reconnection
5. **Transaction Builder Tests**: Order placement, cancellation, all write operations
6. **Utility Tests**: Address derivation, price rounding, nonce generation
7. **Error Handling Tests**: All error scenarios
8. **Integration Tests**: End-to-end flows (mock server)

### Per-SDK Test Structure
```
sdk-{lang}/tests/
  ├── config_test         # Configuration and initialization
  ├── models_test         # Data model serialization
  ├── rest_client_test    # REST API operations
  ├── ws_client_test      # WebSocket operations
  ├── write_client_test   # Transaction/write operations
  ├── utils_test          # Utility functions
  └── integration_test    # End-to-end scenarios
```

## Phase 3: Rust SDK Implementation

### Structure
```
sdk-rust/
  ├── Cargo.toml
  ├── src/
  │   ├── lib.rs
  │   ├── config.rs           # DecibelConfig, presets
  │   ├── models/             # All data types
  │   │   ├── mod.rs
  │   │   ├── market.rs
  │   │   ├── account.rs
  │   │   ├── order.rs
  │   │   ├── position.rs
  │   │   ├── vault.rs
  │   │   └── ...
  │   ├── client/
  │   │   ├── mod.rs
  │   │   ├── read.rs         # DecibelReadClient
  │   │   ├── write.rs        # DecibelWriteClient
  │   │   └── ws.rs           # WebSocket manager
  │   ├── transaction/
  │   │   ├── mod.rs
  │   │   ├── builder.rs      # Transaction builder
  │   │   └── signer.rs       # Ed25519 signing
  │   ├── gas/
  │   │   └── manager.rs      # Gas price manager
  │   ├── utils.rs            # Utility functions
  │   └── error.rs            # Error types
  └── tests/
      ├── config_test.rs
      ├── models_test.rs
      ├── rest_client_test.rs
      ├── ws_client_test.rs
      ├── write_client_test.rs
      └── utils_test.rs
```

### Dependencies
- `tokio` (async runtime)
- `reqwest` (HTTP client)
- `tokio-tungstenite` (WebSocket)
- `serde` + `serde_json` (serialization)
- `aptos-sdk` (blockchain interaction)
- `thiserror` (error handling)
- `tracing` (logging)

## Phase 4: Swift SDK Implementation

### Structure
```
sdk-swift/
  ├── Package.swift
  ├── Sources/DecibelSDK/
  │   ├── Config/
  │   │   ├── DecibelConfig.swift
  │   │   └── Presets.swift
  │   ├── Models/
  │   │   ├── Market.swift
  │   │   ├── Account.swift
  │   │   ├── Order.swift
  │   │   ├── Position.swift
  │   │   └── Vault.swift
  │   ├── Client/
  │   │   ├── DecibelReadClient.swift
  │   │   ├── DecibelWriteClient.swift
  │   │   └── WebSocketManager.swift
  │   ├── Transaction/
  │   │   ├── TransactionBuilder.swift
  │   │   └── Ed25519Signer.swift
  │   ├── Gas/
  │   │   └── GasPriceManager.swift
  │   ├── Utils/
  │   │   └── AddressUtils.swift
  │   └── Errors/
  │       └── DecibelError.swift
  └── Tests/DecibelSDKTests/
      ├── ConfigTests.swift
      ├── ModelTests.swift
      ├── RestClientTests.swift
      ├── WebSocketTests.swift
      ├── WriteClientTests.swift
      └── UtilsTests.swift
```

### Dependencies
- Foundation (HTTP, JSON)
- Combine (reactive streams)
- CryptoKit (Ed25519 signing)

## Phase 5: Kotlin SDK Implementation

### Structure
```
sdk-kotlin/
  ├── build.gradle.kts
  ├── src/main/kotlin/trade/decibel/sdk/
  │   ├── config/
  │   │   ├── DecibelConfig.kt
  │   │   └── Presets.kt
  │   ├── models/
  │   │   ├── Market.kt
  │   │   ├── Account.kt
  │   │   ├── Order.kt
  │   │   ├── Position.kt
  │   │   └── Vault.kt
  │   ├── client/
  │   │   ├── DecibelReadClient.kt
  │   │   ├── DecibelWriteClient.kt
  │   │   └── WebSocketManager.kt
  │   ├── transaction/
  │   │   ├── TransactionBuilder.kt
  │   │   └── Ed25519Signer.kt
  │   ├── gas/
  │   │   └── GasPriceManager.kt
  │   ├── utils/
  │   │   └── AddressUtils.kt
  │   └── errors/
  │       └── DecibelError.kt
  └── src/test/kotlin/trade/decibel/sdk/
      ├── ConfigTest.kt
      ├── ModelTest.kt
      ├── RestClientTest.kt
      ├── WebSocketTest.kt
      ├── WriteClientTest.kt
      └── UtilsTest.kt
```

### Dependencies
- Ktor (HTTP + WebSocket)
- kotlinx.serialization (JSON)
- kotlinx.coroutines (async)
- BouncyCastle / TweetNaCl (Ed25519)

## Phase 6: Go SDK Implementation

### Structure
```
sdk-go/
  ├── go.mod
  ├── go.sum
  ├── config.go          # DecibelConfig, presets
  ├── models/
  │   ├── market.go
  │   ├── account.go
  │   ├── order.go
  │   ├── position.go
  │   └── vault.go
  ├── client/
  │   ├── read.go        # DecibelReadClient
  │   ├── write.go       # DecibelWriteClient
  │   └── websocket.go   # WebSocket manager
  ├── transaction/
  │   ├── builder.go
  │   └── signer.go
  ├── gas/
  │   └── manager.go
  ├── utils/
  │   └── address.go
  ├── errors.go
  ├── config_test.go
  ├── models_test.go
  ├── client_test.go
  └── utils_test.go
```

### Dependencies
- gorilla/websocket (WebSocket)
- net/http (HTTP client)
- encoding/json (JSON)
- crypto/ed25519 (signing)

## Implementation Order

1. **Models** - Define all data types first (shared across read/write)
2. **Configuration** - Preset configs and validation
3. **Utilities** - Address derivation, formatting
4. **Error Types** - All error categories
5. **REST Client** - HTTP client with typed responses
6. **WebSocket Client** - Connection manager with subscriptions
7. **Read Client** - Combine REST + WS for all readers
8. **Transaction Builder** - Build Aptos transactions
9. **Write Client** - All trading operations
10. **Gas Manager** - Background gas price updates

## Testing Strategy

### Unit Tests (per module)
- Model serialization/deserialization
- Configuration validation
- Utility function correctness
- Error type construction

### Integration Tests (mock server)
- REST API request/response cycles
- WebSocket connect/subscribe/receive/unsubscribe
- Full order lifecycle (place -> status -> cancel)
- Account management flow

### BDD Scenarios
- "Given a valid config, When I create a read client, Then it connects successfully"
- "Given market data, When I subscribe to prices, Then I receive real-time updates"
- "Given a funded account, When I place a limit order, Then I get an order ID back"
- etc. (full suite in test files)
