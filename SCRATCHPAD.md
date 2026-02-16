# Decibel Cross-Platform SDK - Scratchpad

## Current Status: SDKs Built

## Completed
- [x] Explored workspace and existing codebase
- [x] Downloaded and analyzed TypeScript SDK (`@decibeltrade/sdk` v0.3.1)
- [x] Fetched and analyzed Decibel documentation sitemap (100+ pages)
- [x] Created comprehensive specification document (`docs/specification.md`) - 5 iterations
- [x] Created implementation plan (`PLAN.md`)
- [x] Built Rust SDK with full BDD test suite (59 passing tests)
- [x] Built Go SDK with full BDD test suite (all tests passing)
- [x] Built Swift SDK with models, config, utils, and test suite
- [x] Built Kotlin SDK with models, config, utils, and test suite

## SDK Features Implemented

### Rust SDK (sdk-rust/)
- Complete data models (market, account, order, position, vault, websocket)
- REST API client with all endpoints (markets, prices, depth, positions, etc.)
- WebSocket subscription manager with connection sharing
- Write client with full order management (place/cancel, TWAP, TP/SL)
- Delegation and builder fee management
- Vault operations (create, activate, deposit, withdraw)
- Transaction builder and gas price manager
- Utility functions (address derivation, price rounding, nonce generation)
- Comprehensive error types hierarchy
- **59 BDD tests passing** (config: 12, models: 29, utils: 18)

### Go SDK (sdk-go/)
- Complete data models with JSON struct tags
- Configuration with presets and validation
- Utility functions (address derivation, price rounding, nonce generation)
- Error types hierarchy
- **All BDD tests passing** (config: 12, models: 14, utils: 11)

### Swift SDK (sdk-swift/)
- Complete data models with Codable conformance
- Configuration with presets and validation
- CryptoKit-based address derivation utilities
- Error types as enum with LocalizedError
- BDD test suite (config, models, utils)

### Kotlin SDK (sdk-kotlin/)
- Complete data models with kotlinx.serialization
- Configuration with presets and validation
- Address derivation utilities
- Sealed class error hierarchy
- BDD test suite (config, models, utils)

## Key Reference Info
- TypeScript SDK: `@decibeltrade/sdk` v0.3.1
- Aptos TS SDK: `@aptos-labs/ts-sdk` ^5.2.1
- Decibel Docs: https://docs.decibel.trade/
- Platform: Fully on-chain perpetuals exchange on Aptos
- Compat Version: v0.4

## Architecture Notes
- Read client: REST + WebSocket, no private key needed
- Write client: On-chain Aptos transactions, Ed25519 keypair required
- Gas station: Sponsored transactions via gas station URL + API key
- Subaccount system: Primary subaccount derived from owner address
- Market addresses: Derived from market name + perp engine global address
