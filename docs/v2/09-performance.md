# Performance Requirements

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

Performance is a first-class concern. AI agents operate in tight decision loops where every millisecond counts: fetch market state → compute decision → execute trade → verify. The SDK MUST be fast by default — no knobs to turn, no advanced configurations to discover.

---

## Latency Targets

### Python SDK

| Operation | P50 Target | P99 Target | Notes |
|---|---|---|---|
| REST GET (warm connection) | < 30ms | < 100ms | Network-bound |
| REST GET (cold connection) | < 200ms | < 500ms | TLS handshake included |
| WebSocket message parse | < 500μs | < 2ms | JSON → typed model |
| WebSocket callback dispatch | < 100μs | < 500μs | Excluding callback body |
| Transaction build (sync) | < 2ms | < 5ms | No network calls |
| Transaction sign | < 1ms | < 3ms | Ed25519 |
| JSON deserialize (MarketPrice) | < 200μs | < 1ms | Pydantic v2 |
| JSON serialize (PlaceOrderParams) | < 100μs | < 500μs | Pydantic v2 |
| Price/size formatting | < 10μs | < 50μs | Pure arithmetic |
| Address derivation | < 100μs | < 500μs | SHA3-256 hash |

### Rust SDK

| Operation | P50 Target | P99 Target | Notes |
|---|---|---|---|
| REST GET (warm connection) | < 5ms | < 30ms | Network-bound |
| REST GET (cold connection) | < 50ms | < 200ms | TLS handshake included |
| WebSocket message parse | < 50μs | < 200μs | serde_json |
| WebSocket callback dispatch | < 10μs | < 50μs | Excluding callback body |
| Transaction build (sync) | < 200μs | < 1ms | No network calls |
| Transaction sign | < 100μs | < 500μs | Ed25519 |
| JSON deserialize (MarketPrice) | < 20μs | < 100μs | serde_json |
| JSON serialize (PlaceOrderParams) | < 10μs | < 50μs | serde_json |
| Price/size formatting | < 1μs | < 5μs | Pure arithmetic |
| Address derivation | < 10μs | < 50μs | SHA3-256 hash |

---

## Connection Management

### HTTP Connection Pooling

| Requirement | Specification |
|---|---|
| **Protocol** | HTTP/2 preferred, HTTP/1.1 fallback |
| **Pool size** | 10 idle connections per host (configurable) |
| **Keep-alive** | Connections persist across requests |
| **TLS session** | Session resumption for faster reconnects |
| **DNS caching** | Cache DNS resolution for pool lifetime |

#### Python

```python
self._client = httpx.AsyncClient(
    http2=True,
    limits=httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
        keepalive_expiry=30.0,
    ),
)
```

#### Rust

```rust
let client = reqwest::Client::builder()
    .pool_max_idle_per_host(10)
    .pool_idle_timeout(Duration::from_secs(30))
    .tcp_keepalive(Duration::from_secs(60))
    .build()?;
```

### WebSocket Connection

| Requirement | Specification |
|---|---|
| **Single connection** | One TCP connection for all subscriptions |
| **Compression** | permessage-deflate if server supports it |
| **Buffer size** | 64KB read buffer (configurable) |
| **Write coalescing** | Batch multiple subscribe messages into single write |

---

## Caching

### Cache Architecture

```
┌──────────────────────────────────────┐
│          SDK Cache Layer             │
├──────────────────────────────────────┤
│ Market Configs    │ TTL: 5 min       │ ← Cached in-memory
│ USDC Decimals     │ TTL: ∞           │ ← Cached forever (immutable)
│ Gas Price         │ TTL: 5 sec       │ ← Background refresh
│ Chain ID          │ TTL: ∞           │ ← Cached forever (per network)
│ ABI Definitions   │ TTL: ∞           │ ← Bundled or cached forever
│ Market Addr Map   │ TTL: 5 min       │ ← Derived from market configs
└──────────────────────────────────────┘
```

### Cache Behavior

| Data | First Access | Subsequent Access | Refresh |
|---|---|---|---|
| Market configs | Async fetch | In-memory read | TTL or manual |
| USDC decimals | Async fetch | In-memory read | Never |
| Gas price | Background fetch | In-memory read | Background task |
| Chain ID | Async fetch or config | In-memory read | Never |
| ABI definitions | Bundled (no fetch) | In-memory read | Never |
| Market address map | Derived from configs | In-memory read | When configs refresh |

### Cache Invalidation

- **TTL-based**: Market configs expire after configurable TTL (default: 5 minutes).
- **Manual**: `client.refresh_markets()` forces a cache refresh.
- **Lazy**: Data is only fetched when first requested — no startup cost.

---

## Transaction Throughput

### Synchronous Build Path

Transaction construction MUST NOT require any network calls. This enables:

```
Build 1 transaction: ~200μs (Rust) / ~2ms (Python)
Build 100 transactions: ~20ms (Rust) / ~200ms (Python)
```

### Parallel Submission

Orderless transactions (random replay nonces) enable parallel submission:

```python
import asyncio

orders = [
    client.place_order(market_name="BTC-USD", price=45000, size=0.1, is_buy=True, ...),
    client.place_order(market_name="ETH-USD", price=3000, size=1.0, is_buy=True, ...),
    client.place_order(market_name="SOL-USD", price=150, size=10.0, is_buy=True, ...),
]
results = await asyncio.gather(*orders)
```

```rust
let (r1, r2, r3) = tokio::join!(
    client.place_order(btc_params),
    client.place_order(eth_params),
    client.place_order(sol_params),
);
```

### Throughput Targets

| Metric | Python Target | Rust Target |
|---|---|---|
| Orders built per second | > 500 | > 5000 |
| Orders submitted per second | > 50 | > 200 |
| WebSocket messages processed per second | > 10,000 | > 100,000 |

---

## Serialization Performance

### Python (Pydantic v2)

Pydantic v2 uses Rust-backed validators for performance. The SDK MUST:

- Use `model_validate()` (not `__init__`) for deserialization from dicts.
- Use `model_validate_json()` for direct JSON string deserialization (avoids intermediate dict).
- Use `model_dump()` for serialization.
- Use `model_dump_json()` for direct JSON string serialization.
- Use `frozen=True` models to enable hash caching and immutability.

### Rust (serde)

The Rust SDK MUST:

- Use `#[derive(Serialize, Deserialize)]` for all models.
- Use `#[serde(rename_all = "snake_case")]` for field name convention.
- Use `serde_json::from_str` / `serde_json::to_string` for JSON.
- Avoid `serde_json::Value` in hot paths — always deserialize to concrete types.
- Use `#[serde(borrow)]` for zero-copy string deserialization where applicable.

### Benchmarks

Both SDKs MUST include serialization benchmarks:

```rust
// Rust: criterion benchmark
fn bench_market_price_deser(c: &mut Criterion) {
    let json = r#"{"market":"BTC-USD","mark_px":45000.0,...}"#;
    c.bench_function("MarketPrice deserialize", |b| {
        b.iter(|| serde_json::from_str::<MarketPrice>(json).unwrap())
    });
}
```

```python
# Python: pytest-benchmark
def test_market_price_deser(benchmark):
    data = '{"market":"BTC-USD","mark_px":45000.0,...}'
    benchmark(MarketPrice.model_validate_json, data)
```

---

## WebSocket Performance

### Message Processing Pipeline

```
Network → Read Buffer → JSON Parse → Type Dispatch → Callback Queue → Agent Callback
                         < 100μs      < 10μs          < 10μs
                        (Rust)
```

### Requirements

| Requirement | Specification |
|---|---|
| **Read loop** | Runs on dedicated background task |
| **Callback dispatch** | Non-blocking; queued if slow |
| **Buffer size** | Per-topic bounded queue (default: 100 messages) |
| **Overflow policy** | Drop oldest message, emit warning |
| **Parse errors** | Log and skip (don't crash the read loop) |

### Backpressure

If an agent's callback processes messages slower than they arrive:

1. Messages queue in a bounded per-topic buffer.
2. If the buffer fills, the oldest messages are dropped.
3. A `WARN` log is emitted with the number of dropped messages.
4. The WebSocket read loop is never blocked.

---

## Memory

### Python

| Component | Expected Memory |
|---|---|
| Client (no subscriptions) | < 5MB |
| Per WebSocket subscription | < 1KB overhead |
| Per cached market config | < 2KB |
| 100 MarketPrice objects | < 50KB |
| 1000 UserTradeHistoryItem objects | < 500KB |

### Rust

| Component | Expected Memory |
|---|---|
| Client (no subscriptions) | < 2MB |
| Per WebSocket subscription | < 256B overhead |
| Per cached market config | < 512B |
| 100 MarketPrice objects | < 10KB |
| 1000 UserTradeHistoryItem objects | < 100KB |

---

## Startup Performance

| Phase | Python Target | Rust Target |
|---|---|---|
| Client construction | < 10ms | < 1ms |
| First HTTP request | < 300ms | < 100ms |
| WebSocket connection | < 500ms | < 200ms |
| Full initialization (all caches warm) | < 2s | < 500ms |

### Lazy Initialization

The SDK uses lazy initialization for all cached data:
- Market configs are fetched on first access, not at construction time.
- Gas price manager starts on first transaction build, not at construction time.
- WebSocket connects on first subscription, not at construction time.

This keeps client construction fast and avoids unnecessary network calls for agents that only use a subset of features.

---

## Benchmarking Infrastructure

Both SDKs MUST ship with benchmarks that measure:

1. **Serialization**: JSON parse/emit for all model types.
2. **Formatting**: Price/size rounding and chain unit conversion.
3. **Address derivation**: SHA3-256 hashing for market/subaccount addresses.
4. **Transaction build**: End-to-end sync build without signing.
5. **Full order lifecycle**: Build → sign → serialize for submission.

### Running Benchmarks

```bash
# Rust
cargo bench

# Python
pytest tests/bench/ --benchmark-only
```
