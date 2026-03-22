# Performance for Trading Bots

**Parent**: [00-overview.md](./00-overview.md)

---

## End-to-End Latency Budget: Signal to Confirmation

A trading bot's profitability is directly tied to how fast it can convert a signal into an on-chain order. Here is the full latency budget from signal detection through confirmation, with realistic numbers for each stage.

### The Full Pipeline

```
Signal detected (price cross, fill event, external trigger)
    │
    ├── [1] Decision logic         1–50ms     Strategy computation, risk checks
    │
    ├── [2] Parameter resolution   < 10μs     Market name → address, price rounding
    │
    ├── [3] Transaction build      < 200μs    BCS serialize, nonce, expiration (Rust)
    │                              < 2ms      (Python)
    │
    ├── [4] Transaction sign       < 50μs     Ed25519 (Rust)
    │                              < 500μs    (Python)
    │
    ├── [5] Submission             30–150ms   POST to gas station or fullnode
    │
    ├── [6] Mempool → block        500ms–2s   Aptos block time
    │
    └── [7] Confirmation           0–500ms    Polling or WS event
```

### Realistic Total Latencies

| Path | Python | Rust | Notes |
|---|---|---|---|
| Signal → tx submitted | 35–205ms | 31–155ms | Steps 1–5. Network-dominated. |
| Signal → confirmed on-chain | 530ms–4s | 530ms–4s | Block time is the same regardless of SDK. |
| Signal → WS fill notification | 600ms–5s | 600ms–5s | Block time + WS propagation delay. |

### Where Time Actually Goes

```
┌──────────────────────────────────────────────────────────────────┐
│                     Latency Budget Breakdown                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Decision logic     ████░░░░░░░░░░░░░░░░░░░░░░░░  1–50ms       │
│  Build + sign       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  < 3ms        │
│  Network submit     ████████████████░░░░░░░░░░░░░  30–150ms     │
│  Block confirmation ████████████████████████████░░  500ms–2s     │
│                                                                  │
│  Build+sign is < 1% of total latency.                           │
│  Network + chain is > 99%.                                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Implication**: Optimizing transaction build from 2ms to 200μs saves 1.8ms on a 1000ms+ round trip. Optimizing submission routing (choosing the nearest fullnode, reusing HTTP/2 connections) can save 50ms. Focus on the network path.

---

## What Actually Matters vs What Doesn't

### Matters Enormously

| Component | Why | Target |
|---|---|---|
| **WS message parse latency** | Every price update, fill, and orderbook delta flows through this path. A 1ms parse delay at 10,000 messages/sec means the bot is permanently 10ms behind. | < 100μs (Rust), < 500μs (Python) |
| **WS callback dispatch** | The time between parse completion and the bot's strategy code seeing the data. Must be non-blocking. | < 50μs (Rust), < 200μs (Python) |
| **Transaction build (sync)** | Must be zero-network-call. Any network dependency in the build path adds 30–100ms. | < 200μs (Rust), < 2ms (Python) |
| **Ed25519 signing** | On the critical path for every order. | < 50μs (Rust), < 500μs (Python) |
| **HTTP connection reuse** | Cold TCP+TLS handshake adds 100–300ms. A warm connection saves this on every submission. | Keep-alive pool, HTTP/2 |
| **Gas price freshness** | Stale gas price = stuck transactions. Overpaying gas = wasted money. | Background refresh every 5s |

### Matters Moderately

| Component | Why | Target |
|---|---|---|
| **REST GET for account state** | Used for reconciliation and safety checks. Not on the hot path during normal operation (WS provides this data). | < 50ms warm |
| **Market config cache hit** | First call fetches from network; every subsequent call must be in-memory. | < 1μs after first fetch |
| **JSON serialization of order params** | Only happens once per order. Fast enough in both languages. | < 100μs |

### Does Not Matter

| Component | Why | Don't Optimize |
|---|---|---|
| **REST GET for historical data** | Candle history, trade history, funding rate history. Fetched once at startup or periodically. Latency is irrelevant. | 100ms is fine |
| **Market config fetch latency** | Happens once at startup, cached for 5 minutes. | 200ms is fine |
| **Client construction time** | Happens once. | 10ms–2s is fine |
| **Serialization of historical data models** | 1000 trade history items taking 5ms to deserialize is a non-issue for a batch operation. | Not a concern |
| **WS subscribe/unsubscribe latency** | Happens at startup and on market rotation. Not per-tick. | 100ms is fine |

---

## Hot Path Identification

Code paths in a trading bot fall into three categories. The SDK must optimize paths differently for each.

### Critical Hot Path (every tick / every message)

These execute on every WebSocket message or every order cycle. Nanoseconds matter.

```
WS message received
    → JSON parse to typed struct
    → Route to callback by topic
    → Invoke strategy callback

Strategy decides to trade
    → Build transaction (sync)
    → Sign transaction
    → Submit (async)
```

**Requirements**:
- Zero allocation in steady state (Rust: use pre-allocated buffers for JSON parse)
- No locks on the WS read loop (Rust: lock-free channel for callback dispatch)
- No string formatting in the parse path (Rust: avoid `format!` in hot loop)
- Pre-validated market config (price/size formatting parameters already resolved)

**Rust hot path optimization targets**:

```rust
// WS message parse: JSON bytes → typed struct
// Target: < 100μs P99
let price: MarketPrice = serde_json::from_str(raw)?;

// Transaction build: params → RawTransaction
// Target: < 500μs P99
let raw_tx = builder.build_place_order(params)?;

// Transaction sign: RawTransaction → SignedTransaction
// Target: < 200μs P99
let signed = signer.sign(&raw_tx)?;
```

**Python hot path optimization targets**:

```python
# WS message parse: JSON string → Pydantic model
# Target: < 500μs P99
price = MarketPrice.model_validate_json(raw_bytes)

# Transaction build: params → RawTransaction
# Target: < 5ms P99
raw_tx = builder.build_place_order(params)

# Transaction sign: RawTransaction → SignedTransaction
# Target: < 2ms P99
signed = signer.sign(raw_tx)
```

### Warm Path (per order cycle, not per tick)

These execute when the bot decides to trade — typically 1–100 times per second for active market makers.

```
Price rounding to tick_size
Size rounding to lot_size
Chain unit conversion (float → u64)
client_order_id generation
Gas price lookup (from cached manager)
```

**Requirements**:
- In-memory only, no network calls
- Can allocate (strings for IDs, etc.)
- < 50μs total for the warm path

### Cold Path (startup, periodic, on-demand)

These execute infrequently. Optimize for correctness, not speed.

```
GET /markets (startup, every 5 min)
GET /candlesticks (strategy initialization)
GET /trade_history (P&L reconciliation)
GET /funding_rate_history (accounting)
Market config cache refresh
WS subscribe/unsubscribe
```

**Requirements**:
- Correct error handling
- Proper timeout and retry
- No latency requirement beyond "reasonable" (< 5s)

---

## Memory Layout for Rust: Cache-Friendly Position State

A market making bot's inner loop reads position state on every tick to compute inventory skew. The layout of position data in memory directly affects cache performance.

### Bad Layout: HashMap of Heap-Allocated Structs

```rust
// Every access chases a pointer. Cache-hostile.
struct BotState {
    positions: HashMap<String, Box<Position>>,  // string key = heap alloc + hash
    orders: HashMap<String, Box<Order>>,
}
```

### Good Layout: Dense Array with Index

```rust
use std::collections::HashMap;

const MAX_MARKETS: usize = 64;

#[repr(C)]
struct PositionEntry {
    market_index: u16,
    size: i64,               // signed: positive = long, negative = short
    entry_price_chain: u64,  // chain units, no float
    unrealized_pnl: i64,    // chain units
    margin_used: u64,
    liquidation_price: u64,
    accrued_funding: i64,
    last_update_ms: u64,
    _padding: [u8; 6],      // align to 64 bytes (cache line)
}

// PositionEntry is exactly 64 bytes = 1 cache line.
// Reading one position = 1 cache line fetch.

struct PositionTable {
    entries: [PositionEntry; MAX_MARKETS],   // dense, stack-allocated, contiguous
    market_to_index: HashMap<String, u16>,   // only used on cold path (setup)
    active_count: u16,
}

impl PositionTable {
    #[inline]
    fn get(&self, market_index: u16) -> &PositionEntry {
        &self.entries[market_index as usize]
    }

    #[inline]
    fn update_from_fill(&mut self, market_index: u16, fill_size: i64, fill_price: u64) {
        let entry = &mut self.entries[market_index as usize];
        let old_size = entry.size;
        let new_size = old_size + fill_size;

        if old_size.signum() == new_size.signum() || old_size == 0 {
            // Same direction or fresh entry — VWAP the entry price
            let old_notional = old_size.unsigned_abs() as u128 * entry.entry_price_chain as u128;
            let fill_notional = fill_size.unsigned_abs() as u128 * fill_price as u128;
            let new_notional = old_notional + fill_notional;
            entry.entry_price_chain = (new_notional / new_size.unsigned_abs() as u128) as u64;
        } else {
            // Direction flip — realize PnL, reset entry
            entry.entry_price_chain = fill_price;
        }

        entry.size = new_size;
        entry.last_update_ms = current_time_ms();
    }
}
```

### Why This Matters

For a market maker iterating over 10 positions to compute aggregate inventory:

| Layout | Cache Lines Touched | Approximate Time |
|---|---|---|
| HashMap<String, Box<Position>> | 10 pointer chases + 10 random cache lines | ~500ns |
| Dense array (64-byte entries) | 10 sequential cache lines (prefetch-friendly) | ~50ns |

At 10,000 ticks/second, this is the difference between 5ms/sec and 0.5ms/sec spent on position reads.

### Order Tracking: Slab Allocator Pattern

For tracking active orders (which are created and destroyed frequently), use a slab allocator to avoid heap fragmentation:

```rust
struct OrderSlab {
    entries: Vec<Option<ActiveOrder>>,  // pre-allocated, reused slots
    free_list: Vec<usize>,
    id_to_slot: HashMap<u64, usize>,   // order_id → slot index
}

impl OrderSlab {
    fn insert(&mut self, order: ActiveOrder) -> usize {
        let slot = self.free_list.pop().unwrap_or_else(|| {
            self.entries.push(None);
            self.entries.len() - 1
        });
        let order_id = order.order_id;
        self.entries[slot] = Some(order);
        self.id_to_slot.insert(order_id, slot);
        slot
    }

    fn remove(&mut self, order_id: u64) -> Option<ActiveOrder> {
        let slot = self.id_to_slot.remove(&order_id)?;
        let order = self.entries[slot].take();
        self.free_list.push(slot);
        order
    }
}
```

---

## Gas Cost Analysis

On-chain trading means every operation costs gas. For bots running at scale, gas is a significant operational cost that must be budgeted.

### Cost Per Operation

Gas costs on Aptos depend on the operation type and current gas price. Typical costs at 100 gas unit price:

| Operation | Gas Units (typical) | Cost at 100 GUP | Cost at 150 GUP | Notes |
|---|---|---|---|---|
| Place order | 3,000–8,000 | 0.0003–0.0008 APT | 0.00045–0.0012 APT | Varies with order complexity (triggers, builder fees) |
| Cancel order | 2,000–4,000 | 0.0002–0.0004 APT | 0.0003–0.0006 APT | |
| Place bulk order (30 levels) | 15,000–30,000 | 0.0015–0.003 APT | 0.00225–0.0045 APT | One tx replaces all quotes on one side |
| Place TP/SL | 4,000–7,000 | 0.0004–0.0007 APT | 0.0006–0.00105 APT | |
| Deposit | 2,000–3,000 | 0.0002–0.0003 APT | 0.0003–0.00045 APT | |
| Withdraw | 2,000–3,000 | 0.0002–0.0003 APT | 0.0003–0.00045 APT | |

### Market Maker Gas Budget Example

A market maker quoting 5 markets, updating quotes every 2 seconds:

```
Quote updates per side per market:     1 every 2s
Sides:                                  2 (bid + ask)
Markets:                                5
Method:                                 bulk_order (1 tx per side per market)

Transactions per second:    5 markets × 2 sides / 2s = 5 tx/s
Gas per tx (bulk order):    ~20,000 gas units
Gas unit price:             100–150

Hourly cost:
  5 tx/s × 3600s × 20,000 gas × 100 GUP / 10^8
  = 5 × 3600 × 0.002 APT
  = 36 APT/hour

Daily cost:
  36 × 24 = 864 APT/day

At APT = $10:
  $8,640/day for continuous quoting on 5 markets
```

### Cost Optimization Strategies

| Strategy | Savings | Trade-off |
|---|---|---|
| **Use bulk orders** instead of individual place + cancel | 60–80% for market makers | Only available for PostOnly orders; max 30 levels per side |
| **Gas Station** (sponsored transactions) | 100% gas cost | Dependent on gas station availability; adds ~20ms latency |
| **Reduce update frequency** (3s instead of 1s) | 66% | Wider effective spread, more adverse selection |
| **Skip simulation** | ~30ms latency saved, no extra gas | Risk of on-chain failure (wasted gas on VM errors) |
| **Batch multiple operations** in one tx | 30–50% vs separate txs | Only possible for some operation pairs |
| **Lower gas multiplier** during low-congestion periods | 20–40% | Risk of stuck transactions during sudden congestion |

### Gas Budget Planning Template

```python
@dataclass
class GasBudget:
    max_daily_apt: float
    gas_unit_price: int
    operations_per_hour: dict[str, int]  # operation_type → count

    def estimate_daily_cost(self) -> float:
        GAS_PER_OP = {
            "place_order": 5_000,
            "cancel_order": 3_000,
            "place_bulk_order": 20_000,
            "cancel_bulk_order": 10_000,
            "place_tp_sl": 5_000,
        }
        total_gas = 0
        for op, count_per_hour in self.operations_per_hour.items():
            gas = GAS_PER_OP.get(op, 5_000)
            total_gas += gas * count_per_hour * 24

        return total_gas * self.gas_unit_price / 1e8

    def is_within_budget(self) -> bool:
        return self.estimate_daily_cost() <= self.max_daily_apt

    def remaining_budget_apt(self, spent_today: float) -> float:
        return self.max_daily_apt - spent_today
```

---

## Throughput Targets

### Orders Per Second

| Metric | Python Target | Rust Target | Limiting Factor |
|---|---|---|---|
| Orders built per second | > 500 | > 5,000 | CPU (BCS serialization) |
| Orders signed per second | > 2,000 | > 20,000 | CPU (Ed25519) |
| Orders submitted per second | > 50 | > 200 | Network + gas station rate limit |
| Orders confirmed per second | ~2–5 (per block) | ~2–5 (per block) | Aptos block time (shared by all users) |

The bottleneck is always submission and confirmation, not building or signing. A bot that can build 5,000 orders/sec but only submit 200/sec should focus on submission routing, not build optimization.

### WebSocket Throughput

| Metric | Python Target | Rust Target |
|---|---|---|
| Messages parsed per second | > 10,000 | > 100,000 |
| Callback invocations per second | > 5,000 | > 50,000 |
| Max sustained message rate (no drops) | 10,000/s | 100,000/s |

For context: a bot subscribing to depth for 10 markets receives roughly 500–2,000 messages/sec during active trading. The SDK must handle 10x this without dropping messages.

---

## Connection Management

### HTTP Connection Pool

| Setting | Value | Why |
|---|---|---|
| Protocol | HTTP/2 preferred | Multiplexed streams over one TCP connection |
| Pool size | 10 idle connections per host | Enough for parallel requests during startup |
| Keep-alive | 30s idle expiry | Prevent stale connections |
| TLS session resumption | Enabled | Saves ~100ms on reconnect |
| DNS cache | Pool lifetime | Avoid repeated DNS lookups |

### WebSocket Connection

| Setting | Value | Why |
|---|---|---|
| Single connection | 1 per client | All subscriptions multiplexed |
| Read buffer | 64KB | Handle burst messages without backpressure |
| Compression | permessage-deflate | 60–80% bandwidth savings on depth data |
| Ping interval | 30s (server-initiated) | Detect dead connections |

---

## Real-World Benchmarks

### What to Measure

These are the benchmarks a market making bot should run to validate SDK performance:

#### 1. Tick-to-Trade Latency

The most important benchmark. Measures the time from receiving a WS price update to having a signed transaction ready for submission.

```rust
// Rust benchmark with criterion
fn bench_tick_to_trade(c: &mut Criterion) {
    let builder = TransactionBuilder::new(/* cached config */);
    let signer = Signer::new(test_private_key());
    let raw_ws_msg = r#"{"topic":"market_price:0xabc","data":{"mark_px":"68000.5",...}}"#;

    c.bench_function("tick_to_trade", |b| {
        b.iter(|| {
            // Step 1: Parse WS message
            let price: MarketPrice = serde_json::from_str(raw_ws_msg).unwrap();

            // Step 2: Compute quote (trivial spread calculation)
            let bid = price.mark_px * 0.9999;
            let ask = price.mark_px * 1.0001;

            // Step 3: Build transaction
            let raw_tx = builder.build_place_order(PlaceOrderParams {
                market_name: "BTC-USD".into(),
                price: bid,
                size: 0.01,
                is_buy: true,
                time_in_force: TimeInForce::PostOnly,
                ..Default::default()
            }).unwrap();

            // Step 4: Sign
            let _signed = signer.sign(&raw_tx).unwrap();
        })
    });
}
```

**Target**: < 300μs P50, < 1ms P99 (Rust). < 5ms P50, < 10ms P99 (Python).

```python
# Python benchmark with pytest-benchmark
def test_tick_to_trade(benchmark, builder, signer):
    raw_msg = '{"topic":"market_price:0xabc","data":{"mark_px":"68000.5",...}}'

    def tick_to_trade():
        price = MarketPrice.model_validate_json(raw_msg)
        bid = price.mark_px * 0.9999
        raw_tx = builder.build_place_order(
            market_name="BTC-USD", price=bid, size=0.01,
            is_buy=True, time_in_force=TimeInForce.PostOnly,
        )
        return signer.sign(raw_tx)

    benchmark(tick_to_trade)
```

#### 2. WS Message Parse Throughput

How many messages can the SDK parse per second? This sets the ceiling on how many market data updates the bot can consume.

```rust
fn bench_ws_parse_throughput(c: &mut Criterion) {
    let messages: Vec<String> = (0..10_000)
        .map(|i| format!(r#"{{"topic":"market_price:0xabc","data":{{"mark_px":"{}"}}}}"#, 68000.0 + i as f64 * 0.01))
        .collect();

    c.bench_function("ws_parse_10k_messages", |b| {
        b.iter(|| {
            for msg in &messages {
                let _: MarketPrice = serde_json::from_str(msg).unwrap();
            }
        })
    });
}
```

**Target**: > 100,000 messages/sec (Rust), > 10,000 messages/sec (Python).

#### 3. Position State Update

How fast can the bot update its position table from a fill event?

```rust
fn bench_position_update(c: &mut Criterion) {
    let mut table = PositionTable::new();
    table.initialize_market("BTC-USD", 0);

    c.bench_function("position_update_from_fill", |b| {
        b.iter(|| {
            table.update_from_fill(0, 1_000_000, 68_000_000_000_000);
        })
    });
}
```

**Target**: < 50ns (Rust), < 1μs (Python).

#### 4. Bulk Order Build

Market makers using bulk orders need to build a transaction with up to 30 price levels per side.

```rust
fn bench_bulk_order_build(c: &mut Criterion) {
    let builder = TransactionBuilder::new(/* config */);
    let levels: Vec<(f64, f64)> = (0..30)
        .map(|i| (68000.0 - i as f64 * 0.5, 0.01))
        .collect();

    c.bench_function("bulk_order_30_levels", |b| {
        b.iter(|| {
            builder.build_bulk_order(BulkOrderParams {
                market_name: "BTC-USD".into(),
                levels: levels.clone(),
                is_buy: true,
                ..Default::default()
            }).unwrap()
        })
    });
}
```

**Target**: < 500μs (Rust), < 5ms (Python).

#### 5. End-to-End Submission Latency (Integration)

This requires a live testnet connection. Measures actual wall-clock time from `place_order()` call to confirmed transaction.

```python
async def bench_e2e_submission(client):
    """Measure real submission latency on testnet."""
    timings = []
    for _ in range(20):
        start = time.monotonic()
        result = await client.place_order(
            market_name="BTC-USD",
            price=1.0,  # far from market, won't fill
            size=0.001,
            is_buy=True,
            time_in_force=TimeInForce.GoodTillCanceled,
            is_reduce_only=False,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        timings.append(elapsed_ms)

        # Cancel to clean up
        if result.order_id:
            await client.cancel_order(order_id=result.order_id, market_name="BTC-USD")

    p50 = sorted(timings)[len(timings) // 2]
    p99 = sorted(timings)[int(len(timings) * 0.99)]
    print(f"E2E submission: P50={p50:.0f}ms, P99={p99:.0f}ms")
```

**Target**: P50 < 800ms, P99 < 4s (dominated by block confirmation time).

### Running Benchmarks

```bash
# Rust (using criterion)
cargo bench --bench trading_benchmarks

# Python (using pytest-benchmark)
pytest tests/bench/ --benchmark-only --benchmark-columns=mean,stddev,min,max

# Integration benchmarks (requires testnet credentials)
pytest tests/bench/test_e2e.py --benchmark-only -k "e2e"
```

---

## Serialization Performance

### Python: Pydantic v2 Best Practices

Pydantic v2's Rust-backed validators are fast, but only if used correctly:

| Method | Speed | Use When |
|---|---|---|
| `model_validate_json(raw_bytes)` | Fastest | WS message parse (hot path). Deserializes JSON bytes directly. |
| `model_validate(dict)` | Fast | REST response parse (dict already available from httpx). |
| `Model(**kwargs)` | Slow | Avoid on hot path. Use for test fixtures. |
| `model_dump_json()` | Fastest | Log serialization, telemetry output. |
| `model_dump()` | Fast | When you need a dict (e.g., for LLM context). |

Key rules:
- Use `frozen=True` on all models (enables hash caching, enforces immutability)
- Use `model_validate_json()` on the WS parse path — it avoids creating an intermediate dict
- Never use `json.loads()` + `Model(**data)` — this is 2x slower than `model_validate_json()`

### Rust: serde Best Practices

| Practice | Why |
|---|---|
| `#[serde(borrow)]` on string fields | Zero-copy deserialization — the string borrows from the input buffer instead of allocating |
| Concrete types, never `serde_json::Value` on hot path | `Value` is heap-allocated and untyped. 3–5x slower than deserializing to a concrete struct. |
| `#[serde(rename_all = "snake_case")]` | Avoid per-field rename attributes |
| Pre-size `Vec` with `with_capacity` when size is known | Avoid reallocations during deserialization |

---

## Startup Performance

| Phase | Python Target | Rust Target |
|---|---|---|
| Client construction | < 10ms | < 1ms |
| Phase 1 cache warm (markets + prices + positions) | < 200ms | < 100ms |
| Phase 2 (overview + open orders + TWAPs) | < 200ms | < 100ms |
| WebSocket connected + subscribed | < 500ms | < 200ms |
| **Total time to first trade** | **< 1s** | **< 500ms** |

Lazy initialization is critical: don't fetch market configs until someone asks for them. Don't start the gas price manager until the first transaction build. Don't connect the WebSocket until the first subscription.

---

## Memory Targets

### Python

| Component | Expected Memory |
|---|---|
| Client (no subscriptions) | < 5MB |
| Per WebSocket subscription | < 1KB overhead |
| Per cached market config | < 2KB |
| 100 MarketPrice objects | < 50KB |
| Full local orderbook (50 levels) | < 10KB |
| Position table (20 markets) | < 20KB |

### Rust

| Component | Expected Memory |
|---|---|
| Client (no subscriptions) | < 2MB |
| Per WebSocket subscription | < 256B overhead |
| Per cached market config | < 512B |
| 100 MarketPrice objects | < 10KB |
| Full local orderbook (50 levels) | < 4KB |
| Position table (64 markets, dense array) | 4KB (64 × 64B entries) |
