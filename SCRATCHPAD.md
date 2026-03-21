# Scratchpad

## Task: Enhance v2 SDK specification documents for trading bots

**Status**: Complete

Enhanced three specification documents (05-rest-api.md, 06-websocket-api.md, 07-transaction-builder.md) with deep bot-focused content.

### 05-rest-api.md enhancements:
1. Polling schedule templates per bot type (market maker, directional, risk monitor)
2. Staying under rate limits: staggered polling, batch correlated requests, conditional polling
3. State reconciliation protocol: full reconciliation after WS gaps, single-order reconciliation, safety rules
4. Endpoint matrix by bot type: CRITICAL/IMPORTANT/USEFUL/UNUSED mapping for market maker, directional, risk monitor, TWAP agent
5. Bot-specific caching rules with detailed rationale per data category
6. Cache implementation with forced refresh for post-maintenance scenarios

### 06-websocket-api.md enhancements:
1. Orderbook management clarification: Decibel sends full snapshots (not deltas), with comparison table and implications
2. Rewritten LocalOrderbook to use replace-based updates instead of delta merging
3. Performance benchmarks for full snapshot replacement cost
4. Latency measurement: WsLatencyTracker with p50/p99, clock drift correction
5. Stale data detection: StalenessDetector with per-topic thresholds, content validation checks
6. Bot actions on stale data: different responses for market maker vs directional bot
7. Multi-subaccount subscription management: tiered subscriptions, promote/demote, aggregation pattern
8. Enhanced reconnection protocol: timing constraints, repeated disconnection handling
9. Per bot type topic requirements: market maker vs directional vs risk monitor

### 07-transaction-builder.md enhancements:
1. Clock drift handling: ClockDriftManager, time_delta_ms computation, recommended TTL by order type, alerting thresholds
2. Bulk order specifics: sequence number management, constraints table, partial failure handling, both-sides update pattern
3. Bulk order vs individual orders comparison table
4. Gas station vs self-paid comparison with recommendation per bot type, fallback pattern
5. Gas cost budgeting for market makers
6. Latency optimization guide: where time is spent (visual breakdown), practical techniques table
7. Parallel submission patterns: multi-market refresh, emergency close, nonce independence
8. ABI versioning strategy: version fields, additive parameter handling, runtime compatibility check

---

## Previous Task: Rewrite docs/v2/04-rust-sdk.md

**Status**: Complete

Rewrote the Rust SDK specification (04-rust-sdk.md) from 936 lines to 1603 lines, focusing on high-performance production trading. Key sections added/rewritten:

1. Zero-allocation hot paths — `#[serde(borrow)]` zero-copy WS deserialization, `BufferPool`, `HotOrderParams` as Copy type
2. PositionStateManager — full API with `Arc<RwLock<>>`, reader/writer methods, `ComputedRiskMetrics`, `recompute_risk()`
3. BulkOrderManager — atomic `replace_quotes()`, `FillTracker`, sequence numbers via `AtomicU64`, `LiveOrder` lifecycle
4. Lock-free patterns — pattern guide table, `Arc<RwLock<>>` for read-heavy state, `tokio::mpsc` for events
5. Transaction building as pure function — `build_transaction()` and `sign_transaction()` take inputs, return bytes
6. Deterministic latency — `HotPathBuffers`, `LatencyHistogram` with p50/p99/p999, `HotPathMetrics`
7. Real market making example — full async loop with inventory skew, risk checks, fill handling
8. Benchmark specifications — table of 10 required benchmarks with target latencies, criterion implementation
9. Trading-specific error handling — `PositionSafety` enum, `requires_resync()`, `requires_halt()`, `SequenceGap` variant

Kept: crate structure, dependencies (added dashmap + crossbeam-channel), testing, configuration, observability.
