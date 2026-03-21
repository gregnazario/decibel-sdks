# Scratchpad

## Task: Rewrite docs/v2/04-rust-sdk.md

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
