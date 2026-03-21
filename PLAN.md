# Plan

## V2 SDK Specification — Trading Bot & Agent First

### Phase 1: Specification (COMPLETE)
- [x] Analyze docs.decibel.trade API surface (REST, WS, on-chain, fees, funding, margin, liquidation)
- [x] Document trading-bot-specific design principles (position state, bulk orders, funding, margins, fees)
- [x] Define all data models with computed fields for risk management
- [x] Specify Python SDK (PositionStateManager, BulkOrderManager, risk monitoring)
- [x] Specify Rust SDK (zero-allocation hot paths, lock-free patterns, PositionSafety)
- [x] Specify Go SDK (future — channels, goroutines, infrastructure use cases)
- [x] Specify REST API client with rate limit strategy and bot-type-specific priorities
- [x] Specify WebSocket with orderbook management, state sync, multi-subaccount
- [x] Specify transaction builder with latency optimization and bulk order specifics
- [x] Define error handling with position safety classification
- [x] Set performance targets with end-to-end latency budgets and gas cost analysis
- [x] Document 5 production-ready agent patterns + anti-patterns

### Phase 2: Implementation (NEXT)
- [ ] Implement Python SDK
  - [ ] Core models (Pydantic v2)
  - [ ] REST client with caching
  - [ ] WebSocket client with reconnection
  - [ ] PositionStateManager
  - [ ] BulkOrderManager
  - [ ] Transaction builder
  - [ ] Error types with position safety
- [ ] Implement Rust SDK
  - [ ] Core models (serde)
  - [ ] REST client (reqwest)
  - [ ] WebSocket client (tokio-tungstenite)
  - [ ] PositionStateManager (Arc<RwLock<>>)
  - [ ] BulkOrderManager (AtomicU64 sequence)
  - [ ] Transaction builder (pure functions)
  - [ ] Error types with PositionSafety enum
- [ ] Testing
    - [x] TDD test files for all models (market, account, order, enums, trade, pagination)
    - [x] conftest.py with fixtures, factories, mock state managers
    - [x] BDD feature files (7 Gherkin files covering position state, order lifecycle, bulk orders, risk monitoring, reconnection, error safety, price formatting)
    - [ ] BDD step definitions (pytest-bdd step implementations)
    - [ ] Unit tests for formatting, address derivation
    - [ ] Integration tests against testnet
    - [ ] Benchmarks (serialization, tx build, sign)
    - [ ] Agent scenario tests

### Phase 3: Go SDK (Future)
- [ ] Implement Go SDK based on spec
- [ ] Channel-based WebSocket subscriptions
- [ ] goroutine-per-strategy examples
- [ ] Integration tests

### Phase 4: Validation
- [ ] Run all benchmarks, compare to spec targets
- [ ] Market making bot end-to-end test on testnet
- [ ] LLM agent integration test
- [ ] Gas cost analysis validation
