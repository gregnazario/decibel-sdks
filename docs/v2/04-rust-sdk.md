# Rust SDK Specification

**Parent**: [00-overview.md](./00-overview.md)  
**Language**: Rust 2021 Edition  
**Crate**: `decibel-sdk`  
**MSRV**: 1.75+

---

## Philosophy

The Rust SDK is the **high-performance production trading SDK**. It targets market makers, HFT bots, co-located strategies, and production trading infrastructure where microseconds matter. Every API surface is designed around these constraints:

1. **Zero-allocation hot paths** — WebSocket message parsing, order building, and signing never touch the heap allocator in the critical loop. Buffers are pre-allocated; `#[serde(borrow)]` is used for zero-copy deserialization where applicable.
2. **Deterministic latency** — No GC pauses (Rust by nature), no allocation jitter on hot paths, pre-sized ring buffers, and built-in latency histograms so you can prove your p99.
3. **Lock-free reads** — Position state and order state are read 1000x more often than written. `Arc<RwLock<>>` ensures readers never block each other. Writers acquire exclusive access only for state transitions.
4. **Send + Sync everywhere** — All public types are safe for concurrent use across tokio tasks and OS threads.
5. **Transaction building is a pure function** — Takes all inputs, returns bytes. No shared state during build. Callable from any thread without locking.
6. **Compile-time guarantees** — Invalid states are unrepresentable. Position safety flags are checked at the type level where possible.

---

## Crate Structure

```
src/
├── lib.rs                   # Crate root, re-exports
├── config.rs                # DecibelConfig, Deployment, presets
├── client.rs                # DecibelClient (unified entry point)
├── models/
│   ├── mod.rs               # Re-exports all models
│   ├── market.rs            # PerpMarketConfig, MarketPrice, MarketContext
│   ├── account.rs           # AccountOverview, UserPosition, UserSubaccount
│   ├── order.rs             # UserOpenOrder, OrderStatus, PlaceOrderResult
│   ├── trade.rs             # UserTradeHistoryItem, UserFundingHistoryItem
│   ├── vault.rs             # Vault, UserOwnedVault
│   ├── analytics.rs         # LeaderboardItem, PortfolioChartPoint
│   ├── twap.rs              # UserActiveTwap
│   ├── ws.rs                # Zero-copy WebSocket message wrappers
│   ├── pagination.rs        # PageParams, SortParams, PaginatedResponse<T>
│   └── enums.rs             # All enumerations
├── read/
│   ├── mod.rs
│   ├── client.rs            # DecibelReadClient
│   ├── markets.rs           # Market data reader methods
│   ├── account.rs           # Account data reader methods
│   ├── history.rs           # Historical data reader methods
│   ├── vaults.rs            # Vault reader methods
│   └── analytics.rs         # Leaderboard, portfolio reader methods
├── write/
│   ├── mod.rs
│   ├── client.rs            # DecibelWriteClient
│   ├── orders.rs            # Order placement and cancellation
│   ├── positions.rs         # TP/SL management
│   ├── accounts.rs          # Subaccount management, delegation
│   ├── vaults.rs            # Vault operations
│   └── bulk.rs              # BulkOrderManager and atomic batch ops
├── state/
│   ├── mod.rs
│   ├── position_manager.rs  # PositionStateManager (Arc<RwLock<>>)
│   ├── order_manager.rs     # BulkOrderManager (lock-free fill reads)
│   └── risk.rs              # Computed risk metrics, safety flags
├── ws/
│   ├── mod.rs
│   ├── manager.rs           # WebSocketManager
│   ├── parser.rs            # Zero-copy message parser
│   └── topics.rs            # Topic string builders and parsing
├── tx/
│   ├── mod.rs
│   ├── build.rs             # build_transaction() — pure function
│   ├── sign.rs              # sign_transaction() — pure function
│   └── gas.rs               # GasPriceManager
├── utils/
│   ├── mod.rs
│   ├── address.rs           # Address derivation (market, subaccount, vault share)
│   ├── formatting.rs        # Price/size formatting and rounding
│   ├── nonce.rs             # Replay protection nonce generation
│   └── buffers.rs           # Pre-allocated buffer pool
├── bench/
│   └── latency.rs           # LatencyHistogram, hot-path timing
└── error.rs                 # Trading-specific error types with safety flags
```

---

## Zero-Allocation Hot Paths

Every message received on the WebSocket, every order struct built for submission, and every transaction signed must avoid heap allocation in the steady-state loop. This section specifies how.

### Zero-Copy WebSocket Deserialization

WebSocket frames arrive as borrowed byte slices from `tokio-tungstenite`. The SDK deserializes into borrowed structs that reference the original frame buffer, avoiding copies.

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct WsFrame<'a> {
    #[serde(borrow)]
    pub topic: &'a str,
    #[serde(borrow)]
    pub data: &'a serde_json::value::RawValue,
    pub ts: i64,
}

#[derive(Debug, Deserialize)]
pub struct MarketPriceBorrowed<'a> {
    #[serde(borrow)]
    pub market: &'a str,
    pub mark_px: f64,
    pub mid_px: f64,
    pub oracle_px: f64,
    pub funding_rate_bps: f64,
    pub is_funding_positive: bool,
    pub open_interest: f64,
    pub transaction_unix_ms: i64,
}

#[derive(Debug, Deserialize)]
pub struct OrderbookUpdateBorrowed<'a> {
    #[serde(borrow)]
    pub market: &'a str,
    pub bids: Vec<[f64; 2]>,
    pub asks: Vec<[f64; 2]>,
    pub seq: u64,
}
```

`WsFrame` borrows the topic string and defers parsing of `data` until the topic is matched, avoiding deserialization of irrelevant messages entirely.

### Pre-Allocated Buffers

The SDK provides a buffer pool for transaction building and signing. Buffers are allocated once at startup and reused across iterations.

```rust
pub struct BufferPool {
    tx_buf: Vec<u8>,
    sign_buf: Vec<u8>,
    bcs_buf: Vec<u8>,
}

impl BufferPool {
    pub fn new() -> Self {
        Self {
            tx_buf: Vec::with_capacity(4096),
            sign_buf: Vec::with_capacity(256),
            bcs_buf: Vec::with_capacity(2048),
        }
    }

    pub fn tx_buf(&mut self) -> &mut Vec<u8> {
        self.tx_buf.clear();
        &mut self.tx_buf
    }

    pub fn sign_buf(&mut self) -> &mut Vec<u8> {
        self.sign_buf.clear();
        &mut self.sign_buf
    }

    pub fn bcs_buf(&mut self) -> &mut Vec<u8> {
        self.bcs_buf.clear();
        &mut self.bcs_buf
    }
}
```

Each tokio task that builds transactions owns a thread-local `BufferPool`. No sharing, no locking, no allocation after the first call.

### Order Struct Pre-Allocation

Order parameter structs avoid `String` in the hot path. Market addresses and subaccount addresses are represented as fixed-size `[u8; 32]` after initial resolution from the config cache.

```rust
#[derive(Debug, Clone, Copy)]
pub struct HotOrderParams {
    pub market_idx: u16,
    pub price_raw: u64,
    pub size_raw: u64,
    pub is_buy: bool,
    pub time_in_force: TimeInForce,
    pub is_reduce_only: bool,
    pub client_order_id: u64,
    pub sequence_number: u64,
}
```

No heap allocation. No `String`. Passed by value.

---

## PositionStateManager

Thread-safe local state aggregated from WebSocket streams. Provides synchronous reads for computed risk metrics. This is the single source of truth for position state in a running strategy.

### Architecture

```
WebSocket streams ──► PositionStateManager (Arc<RwLock<Inner>>)
                              │
                              ├── positions: HashMap<MarketIdx, PositionState>
                              ├── balances: BalanceState
                              ├── risk: ComputedRiskMetrics
                              └── last_update_ts: Instant
```

Writers (WebSocket handler task) acquire a write lock only on state transitions. Readers (strategy task, risk task, logging task) acquire read locks that never block each other.

### Full API

```rust
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct PositionStateManager {
    inner: Arc<RwLock<PositionStateInner>>,
}

struct PositionStateInner {
    positions: HashMap<u16, PositionState>,
    balance: BalanceState,
    risk: ComputedRiskMetrics,
    seq: u64,
    last_update: Instant,
}

#[derive(Debug, Clone)]
pub struct PositionState {
    pub market_idx: u16,
    pub market_name: String,
    pub size: f64,
    pub entry_price: f64,
    pub unrealized_pnl: f64,
    pub realized_pnl: f64,
    pub leverage: f64,
    pub liquidation_price: Option<f64>,
    pub margin_used: f64,
    pub is_cross: bool,
    pub last_fill_ts: i64,
}

#[derive(Debug, Clone)]
pub struct BalanceState {
    pub equity: f64,
    pub available_margin: f64,
    pub total_margin_used: f64,
    pub total_unrealized_pnl: f64,
    pub total_realized_pnl: f64,
    pub withdrawable: f64,
}

#[derive(Debug, Clone)]
pub struct ComputedRiskMetrics {
    pub net_exposure: f64,
    pub gross_exposure: f64,
    pub margin_ratio: f64,
    pub leverage_used: f64,
    pub largest_position_pct: f64,
    pub drawdown_from_peak: f64,
    pub position_count: usize,
}
```

### Reader Methods (synchronous, non-blocking between readers)

```rust
impl PositionStateManager {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(RwLock::new(PositionStateInner::default())),
        }
    }

    pub async fn position(&self, market_idx: u16) -> Option<PositionState> {
        self.inner.read().await.positions.get(&market_idx).cloned()
    }

    pub async fn all_positions(&self) -> Vec<PositionState> {
        self.inner.read().await.positions.values().cloned().collect()
    }

    pub async fn balance(&self) -> BalanceState {
        self.inner.read().await.balance.clone()
    }

    pub async fn risk(&self) -> ComputedRiskMetrics {
        self.inner.read().await.risk.clone()
    }

    pub async fn net_exposure(&self) -> f64 {
        self.inner.read().await.risk.net_exposure
    }

    pub async fn margin_ratio(&self) -> f64 {
        self.inner.read().await.risk.margin_ratio
    }

    pub async fn has_position(&self, market_idx: u16) -> bool {
        self.inner.read().await.positions.contains_key(&market_idx)
    }

    pub async fn position_size(&self, market_idx: u16) -> f64 {
        self.inner.read().await
            .positions.get(&market_idx)
            .map(|p| p.size)
            .unwrap_or(0.0)
    }

    pub async fn snapshot(&self) -> PositionSnapshot {
        let inner = self.inner.read().await;
        PositionSnapshot {
            positions: inner.positions.values().cloned().collect(),
            balance: inner.balance.clone(),
            risk: inner.risk.clone(),
            seq: inner.seq,
            ts: inner.last_update,
        }
    }
}
```

### Writer Methods (exclusive, called only by the WS handler)

```rust
impl PositionStateManager {
    pub async fn apply_position_update(&self, update: WsPositionUpdate) {
        let mut inner = self.inner.write().await;
        for pos in update.positions {
            let state = PositionState::from_ws(pos);
            if state.size.abs() < f64::EPSILON {
                inner.positions.remove(&state.market_idx);
            } else {
                inner.positions.insert(state.market_idx, state);
            }
        }
        inner.recompute_risk();
        inner.seq += 1;
        inner.last_update = Instant::now();
    }

    pub async fn apply_balance_update(&self, update: WsBalanceUpdate) {
        let mut inner = self.inner.write().await;
        inner.balance = BalanceState::from_ws(update);
        inner.recompute_risk();
        inner.seq += 1;
        inner.last_update = Instant::now();
    }

    pub async fn apply_fill(&self, fill: WsFillEvent) {
        let mut inner = self.inner.write().await;
        if let Some(pos) = inner.positions.get_mut(&fill.market_idx) {
            pos.apply_fill(&fill);
        }
        inner.recompute_risk();
        inner.seq += 1;
        inner.last_update = Instant::now();
    }
}

impl PositionStateInner {
    fn recompute_risk(&mut self) {
        let mut net = 0.0;
        let mut gross = 0.0;
        let mut largest = 0.0f64;
        for pos in self.positions.values() {
            let notional = pos.size * pos.entry_price;
            net += notional;
            gross += notional.abs();
            largest = largest.max(notional.abs());
        }
        self.risk.net_exposure = net;
        self.risk.gross_exposure = gross;
        self.risk.position_count = self.positions.len();
        self.risk.margin_ratio = if self.balance.equity > 0.0 {
            self.balance.total_margin_used / self.balance.equity
        } else {
            f64::INFINITY
        };
        self.risk.leverage_used = if self.balance.equity > 0.0 {
            gross / self.balance.equity
        } else {
            f64::INFINITY
        };
        self.risk.largest_position_pct = if gross > 0.0 {
            largest / gross
        } else {
            0.0
        };
    }
}
```

---

## BulkOrderManager

Atomic quote replacement for market making. Manages sequence numbers, tracks fill state with lock-free reads, and provides atomic batch cancel-and-replace semantics.

### Architecture

```
Strategy loop ──► BulkOrderManager
                      │
                      ├── active_orders: Arc<RwLock<HashMap<OrderKey, LiveOrder>>>
                      ├── sequence: AtomicU64
                      ├── fill_state: Arc<RwLock<FillTracker>>
                      └── pending_batches: DashMap<BatchId, BatchState>
```

### Full API

```rust
use std::sync::atomic::{AtomicU64, Ordering};

pub struct BulkOrderManager {
    active_orders: Arc<RwLock<HashMap<OrderKey, LiveOrder>>>,
    sequence: AtomicU64,
    fill_state: Arc<RwLock<FillTracker>>,
    config: BulkConfig,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderKey {
    pub market_idx: u16,
    pub side: Side,
    pub level: u8,
}

#[derive(Debug, Clone)]
pub struct LiveOrder {
    pub order_id: u64,
    pub client_order_id: u64,
    pub price: f64,
    pub size: f64,
    pub filled_size: f64,
    pub sequence: u64,
    pub submitted_at: Instant,
    pub confirmed_at: Option<Instant>,
    pub status: OrderLifecycle,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderLifecycle {
    Building,
    Submitted,
    Confirmed,
    PartialFill,
    Filled,
    Canceled,
    Rejected,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side { Bid, Ask }

pub struct BulkConfig {
    pub max_orders_per_batch: usize,
    pub max_pending_batches: usize,
    pub stale_order_timeout: Duration,
}

pub struct QuoteLevel {
    pub side: Side,
    pub level: u8,
    pub price: f64,
    pub size: f64,
}

pub struct QuoteReplacementResult {
    pub cancels_submitted: usize,
    pub orders_submitted: usize,
    pub sequence: u64,
    pub batch_id: u64,
}

pub struct FillTracker {
    pub total_buy_filled: f64,
    pub total_sell_filled: f64,
    pub net_filled: f64,
    pub recent_fills: VecDeque<FillRecord>,
}

pub struct FillRecord {
    pub market_idx: u16,
    pub side: Side,
    pub price: f64,
    pub size: f64,
    pub ts: i64,
    pub order_id: u64,
}
```

### Core Methods

```rust
impl BulkOrderManager {
    pub fn new(config: BulkConfig) -> Self {
        Self {
            active_orders: Arc::new(RwLock::new(HashMap::new())),
            sequence: AtomicU64::new(1),
            fill_state: Arc::new(RwLock::new(FillTracker::default())),
            config,
        }
    }

    pub fn next_sequence(&self) -> u64 {
        self.sequence.fetch_add(1, Ordering::Relaxed)
    }

    /// Atomic quote replacement: cancel all existing quotes for the market,
    /// then place new quotes at the specified levels. Returns only after
    /// both cancel and place transactions are submitted (not confirmed).
    pub async fn replace_quotes(
        &self,
        client: &DecibelClient,
        market_idx: u16,
        new_quotes: &[QuoteLevel],
    ) -> Result<QuoteReplacementResult, DecibelError> {
        let seq = self.next_sequence();

        let cancel_ids: Vec<u64> = {
            let orders = self.active_orders.read().await;
            orders.iter()
                .filter(|(k, _)| k.market_idx == market_idx)
                .map(|(_, v)| v.order_id)
                .collect()
        };

        if !cancel_ids.is_empty() {
            client.bulk_cancel(&cancel_ids).await?;
        }

        let hot_params: Vec<HotOrderParams> = new_quotes.iter().map(|q| {
            HotOrderParams {
                market_idx,
                price_raw: price_to_raw(q.price),
                size_raw: size_to_raw(q.size),
                is_buy: q.side == Side::Bid,
                time_in_force: TimeInForce::PostOnly,
                is_reduce_only: false,
                client_order_id: self.next_sequence(),
                sequence_number: seq,
            }
        }).collect();

        let results = client.bulk_place(&hot_params).await?;

        {
            let mut orders = self.active_orders.write().await;
            for k in orders.keys().filter(|k| k.market_idx == market_idx).cloned().collect::<Vec<_>>() {
                orders.remove(&k);
            }
            for (i, q) in new_quotes.iter().enumerate() {
                let key = OrderKey { market_idx, side: q.side, level: q.level };
                orders.insert(key, LiveOrder {
                    order_id: results[i].order_id,
                    client_order_id: hot_params[i].client_order_id,
                    price: q.price,
                    size: q.size,
                    filled_size: 0.0,
                    sequence: seq,
                    submitted_at: Instant::now(),
                    confirmed_at: None,
                    status: OrderLifecycle::Submitted,
                });
            }
        }

        Ok(QuoteReplacementResult {
            cancels_submitted: cancel_ids.len(),
            orders_submitted: new_quotes.len(),
            sequence: seq,
            batch_id: seq,
        })
    }

    /// Read current fill state. Lock-free between concurrent readers.
    pub async fn fill_state(&self) -> FillTracker {
        self.fill_state.read().await.clone()
    }

    /// Read net inventory accumulated from fills.
    pub async fn net_inventory(&self) -> f64 {
        self.fill_state.read().await.net_filled
    }

    /// Apply a fill event from the WebSocket stream.
    pub async fn apply_fill(&self, fill: &FillRecord) {
        {
            let mut state = self.fill_state.write().await;
            match fill.side {
                Side::Bid => state.total_buy_filled += fill.size,
                Side::Ask => state.total_sell_filled += fill.size,
            }
            state.net_filled = state.total_buy_filled - state.total_sell_filled;
            state.recent_fills.push_back(fill.clone());
            if state.recent_fills.len() > 1000 {
                state.recent_fills.pop_front();
            }
        }
        {
            let mut orders = self.active_orders.write().await;
            for order in orders.values_mut() {
                if order.order_id == fill.order_id {
                    order.filled_size += fill.size;
                    order.status = if (order.filled_size - order.size).abs() < f64::EPSILON {
                        OrderLifecycle::Filled
                    } else {
                        OrderLifecycle::PartialFill
                    };
                    break;
                }
            }
        }
    }

    pub async fn active_order_count(&self) -> usize {
        self.active_orders.read().await.len()
    }

    pub async fn active_orders_snapshot(&self) -> Vec<LiveOrder> {
        self.active_orders.read().await.values().cloned().collect()
    }
}
```

---

## Lock-Free Patterns

### Read-Heavy Shared State

Position state and order state are read by the strategy loop, risk monitor, and logging infrastructure on every tick. Writes happen only when a WebSocket update arrives.

```rust
// Pattern: Arc<RwLock<T>> for read-heavy shared state
let position_mgr = Arc::new(PositionStateManager::new());

// Writer task (WS handler) — acquires write lock ~10-50 times/sec
let pos_writer = position_mgr.clone();
tokio::spawn(async move {
    while let Some(msg) = ws_rx.recv().await {
        pos_writer.apply_position_update(msg).await;
    }
});

// Reader task (strategy) — acquires read lock ~1000 times/sec
let pos_reader = position_mgr.clone();
tokio::spawn(async move {
    loop {
        let risk = pos_reader.risk().await;
        let exposure = pos_reader.net_exposure().await;
        // fast, non-blocking between readers
    }
});
```

### Message Passing Between Tasks

Use `tokio::mpsc` for ordered event delivery and `crossbeam-channel` for ultra-low-latency cross-thread communication when not in an async context.

```rust
use tokio::sync::mpsc;

#[derive(Debug)]
enum StrategyEvent {
    PriceUpdate { market_idx: u16, mid: f64, ts: i64 },
    Fill(FillRecord),
    OrderAck { client_order_id: u64, order_id: u64 },
    RiskBreach(RiskBreachKind),
}

let (event_tx, mut event_rx) = mpsc::channel::<StrategyEvent>(4096);

// WS parser task publishes events
let tx = event_tx.clone();
tokio::spawn(async move {
    while let Some(frame) = ws_stream.next().await {
        let event = parse_to_strategy_event(&frame);
        let _ = tx.try_send(event); // non-blocking, drops if full
    }
});

// Strategy consumes events sequentially
tokio::spawn(async move {
    while let Some(event) = event_rx.recv().await {
        match event {
            StrategyEvent::PriceUpdate { market_idx, mid, .. } => {
                // requote
            }
            StrategyEvent::Fill(fill) => {
                bulk_mgr.apply_fill(&fill).await;
            }
            _ => {}
        }
    }
});
```

### When to Use What

| Pattern | Use Case | Contention Profile |
|---|---|---|
| `Arc<RwLock<T>>` | Position state, order book snapshots | Many readers, rare writers |
| `AtomicU64` | Sequence numbers, counters | Lock-free, single-word updates |
| `tokio::mpsc` | Event delivery between async tasks | Single consumer, bounded back-pressure |
| `crossbeam::channel` | Cross-thread comms outside tokio | Blocking recv in non-async threads |
| `DashMap` | Concurrent map with fine-grained locking | Many keys, low per-key contention |
| Thread-local `BufferPool` | Transaction building scratch space | No contention (per-task owned) |

---

## Transaction Building as a Pure Function

Transaction building does not live on `self`. It is a standalone function that takes all inputs and returns serialized bytes. This design means:

- No lock acquisition during build.
- Callable from any thread or task without coordination.
- Trivially testable and benchmarkable.
- Composable with any signing implementation.

### API

```rust
pub struct TransactionInputs {
    pub sender: [u8; 32],
    pub sequence_number: u64,
    pub module_address: [u8; 32],
    pub function_name: &'static str,
    pub type_args: Vec<TypeTag>,
    pub args: Vec<Vec<u8>>,
    pub max_gas_amount: u64,
    pub gas_unit_price: u64,
    pub expiration_timestamp_secs: u64,
    pub chain_id: u8,
}

pub struct SigningInputs {
    pub raw_tx_bytes: Vec<u8>,
    pub private_key: &ed25519_dalek::SigningKey,
}

pub struct SignedTransactionBytes {
    pub bytes: Vec<u8>,
    pub tx_hash: [u8; 32],
}

/// Build a raw transaction. Pure function. No side effects.
/// Uses the provided buffer to avoid allocation when called with a pre-sized Vec.
pub fn build_transaction(
    inputs: &TransactionInputs,
    buf: &mut Vec<u8>,
) -> Result<(), DecibelError> {
    buf.clear();
    bcs_serialize_transaction(inputs, buf)?;
    Ok(())
}

/// Sign a raw transaction. Pure function. No side effects.
pub fn sign_transaction(
    inputs: &SigningInputs,
) -> Result<SignedTransactionBytes, DecibelError> {
    let signature = inputs.private_key.sign(&inputs.raw_tx_bytes);
    let public_key = inputs.private_key.verifying_key();

    let mut bytes = Vec::with_capacity(inputs.raw_tx_bytes.len() + 128);
    bytes.extend_from_slice(&inputs.raw_tx_bytes);
    bcs_append_authenticator(&mut bytes, &public_key, &signature)?;

    let tx_hash = sha3_hash(&bytes);

    Ok(SignedTransactionBytes { bytes, tx_hash })
}
```

### Usage in Hot Path

```rust
let mut buf = BufferPool::new();

loop {
    let inputs = TransactionInputs { /* ... */ };

    build_transaction(&inputs, buf.tx_buf())?;

    let signed = sign_transaction(&SigningInputs {
        raw_tx_bytes: buf.tx_buf().clone(),
        private_key: &signing_key,
    })?;

    submit_tx(&signed.bytes).await?;
}
```

---

## Entry Point: DecibelClient

```rust
use decibel_sdk::{DecibelClient, DecibelConfig, MAINNET_CONFIG};

let client = DecibelClient::builder()
    .config(MAINNET_CONFIG)
    .bearer_token("your-bearer-token")
    .private_key("0x...")
    .build()
    .await?;
```

### Builder Parameters

| Method | Type | Required | Description |
|---|---|---|---|
| `.config()` | `DecibelConfig` | YES | SDK configuration |
| `.bearer_token()` | `&str` | YES | Bearer token for REST/WS auth |
| `.private_key()` | `&str` | NO | Ed25519 private key hex |
| `.node_api_key()` | `&str` | NO | Aptos node API key |
| `.skip_simulate()` | `bool` | NO | Skip tx simulation (default: `false`) |
| `.no_fee_payer()` | `bool` | NO | Disable gas station (default: `false`) |
| `.gas_refresh_interval()` | `Duration` | NO | Gas price refresh (default: 5s) |
| `.time_delta_ms()` | `i64` | NO | Clock drift compensation |
| `.request_timeout()` | `Duration` | NO | HTTP timeout (default: 30s) |

---

## Configuration

```rust
use decibel_sdk::config::{DecibelConfig, Deployment, Network};

let config = decibel_sdk::MAINNET_CONFIG;

let config = DecibelConfig {
    network: Network::Mainnet,
    fullnode_url: "https://fullnode.mainnet.aptoslabs.com".into(),
    trading_http_url: "https://api.mainnet.aptoslabs.com/decibel".into(),
    trading_ws_url: "wss://api.mainnet.aptoslabs.com/decibel/ws".into(),
    deployment: Deployment {
        package: "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06".into(),
        usdc: "0x...".into(),
        testc: "0x...".into(),
        perp_engine_global: "0x...".into(),
    },
    compat_version: "v0.4".into(),
    gas_station_url: None,
    gas_station_api_key: None,
    chain_id: None,
};
```

---

## Error Handling — Trading-Specific with Position Safety Flags

Errors carry position safety metadata. Every error variant answers the question: **is my position state still valid?**

```rust
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PositionSafety {
    /// Position state is known-good. No action required.
    Safe,
    /// Position state may be stale. Re-fetch before trading.
    Stale,
    /// Position state is unknown. Halt trading, re-sync from REST.
    Unknown,
    /// Position safety cannot be determined. Emergency flatten recommended.
    Critical,
}

#[derive(Debug, Error)]
pub enum DecibelError {
    #[error("configuration error: {message}")]
    Config {
        message: String,
        safety: PositionSafety,
    },

    #[error("authentication error: {message}")]
    Authentication {
        message: String,
        safety: PositionSafety,
    },

    #[error("network error: {source}")]
    Network {
        #[source]
        source: reqwest::Error,
        retryable: bool,
        safety: PositionSafety,
    },

    #[error("rate limited, retry after {retry_after_ms}ms")]
    RateLimit {
        retry_after_ms: u64,
        safety: PositionSafety,
    },

    #[error("API error {status}: {message}")]
    Api {
        status: u16,
        message: String,
        retryable: bool,
        safety: PositionSafety,
    },

    #[error("transaction error: {vm_status}")]
    Transaction {
        hash: String,
        vm_status: String,
        gas_used: Option<u64>,
        safety: PositionSafety,
    },

    #[error("order rejected: {reason}")]
    OrderRejected {
        reason: String,
        order_client_id: Option<u64>,
        safety: PositionSafety,
    },

    #[error("position state error: {message}")]
    PositionState {
        message: String,
        safety: PositionSafety,
    },

    #[error("WebSocket error: {message}")]
    WebSocket {
        message: String,
        retryable: bool,
        safety: PositionSafety,
    },

    #[error("WebSocket desync: expected seq {expected}, got {actual}")]
    SequenceGap {
        expected: u64,
        actual: u64,
        safety: PositionSafety,
    },

    #[error("serialization error: {source}")]
    Serialization {
        #[source]
        source: serde_json::Error,
        safety: PositionSafety,
    },
}

impl DecibelError {
    pub fn safety(&self) -> PositionSafety {
        match self {
            Self::Config { safety, .. } => *safety,
            Self::Authentication { safety, .. } => *safety,
            Self::Network { safety, .. } => *safety,
            Self::RateLimit { safety, .. } => *safety,
            Self::Api { safety, .. } => *safety,
            Self::Transaction { safety, .. } => *safety,
            Self::OrderRejected { safety, .. } => *safety,
            Self::PositionState { safety, .. } => *safety,
            Self::WebSocket { safety, .. } => *safety,
            Self::SequenceGap { safety, .. } => *safety,
            Self::Serialization { safety, .. } => *safety,
        }
    }

    pub fn is_retryable(&self) -> bool {
        match self {
            Self::Network { retryable, .. } => *retryable,
            Self::RateLimit { .. } => true,
            Self::Api { retryable, .. } => *retryable,
            Self::WebSocket { retryable, .. } => *retryable,
            _ => false,
        }
    }

    pub fn requires_resync(&self) -> bool {
        matches!(
            self.safety(),
            PositionSafety::Unknown | PositionSafety::Critical
        )
    }

    pub fn requires_halt(&self) -> bool {
        self.safety() == PositionSafety::Critical
    }
}
```

### Usage in Trading Loop

```rust
match client.place_order(params).await {
    Ok(result) if result.success => { /* continue */ }
    Ok(result) => {
        tracing::warn!("order rejected: {:?}", result.error);
    }
    Err(e) if e.requires_halt() => {
        tracing::error!("CRITICAL: halting trading: {}", e);
        cancel_all_orders(&client).await;
        return Err(e);
    }
    Err(e) if e.requires_resync() => {
        tracing::warn!("position state unknown, resyncing: {}", e);
        position_mgr.resync_from_rest(&client).await?;
    }
    Err(e) if e.is_retryable() => {
        tokio::time::sleep(Duration::from_millis(
            e.retry_after_ms().unwrap_or(100)
        )).await;
    }
    Err(e) => {
        tracing::error!("unrecoverable: {}", e);
        return Err(e);
    }
}
```

---

## Deterministic Latency

### No Allocation in Hot Paths

The hot path — receive WS frame, parse, decide, build tx, sign, submit — touches zero heap allocations in steady state. All buffers are pre-sized. All types in the critical path are `Copy` or use pre-allocated storage.

### Pre-Sized Buffers

```rust
const WS_READ_BUF_SIZE: usize = 65536;
const TX_BUILD_BUF_SIZE: usize = 4096;
const BCS_BUF_SIZE: usize = 2048;
const ORDERBOOK_DEPTH: usize = 50;

pub struct HotPathBuffers {
    ws_read: Vec<u8>,
    tx_build: Vec<u8>,
    bcs_scratch: Vec<u8>,
    bid_levels: Vec<[f64; 2]>,
    ask_levels: Vec<[f64; 2]>,
}

impl HotPathBuffers {
    pub fn new() -> Self {
        Self {
            ws_read: Vec::with_capacity(WS_READ_BUF_SIZE),
            tx_build: Vec::with_capacity(TX_BUILD_BUF_SIZE),
            bcs_scratch: Vec::with_capacity(BCS_BUF_SIZE),
            bid_levels: Vec::with_capacity(ORDERBOOK_DEPTH),
            ask_levels: Vec::with_capacity(ORDERBOOK_DEPTH),
        }
    }
}
```

### Latency Histogram

Built-in latency tracking for every stage of the hot path.

```rust
pub struct LatencyHistogram {
    buckets: [AtomicU64; 32],
    min_ns: AtomicU64,
    max_ns: AtomicU64,
    count: AtomicU64,
    sum_ns: AtomicU64,
}

impl LatencyHistogram {
    pub fn record(&self, duration: Duration) { /* ... */ }
    pub fn p50(&self) -> Duration { /* ... */ }
    pub fn p99(&self) -> Duration { /* ... */ }
    pub fn p999(&self) -> Duration { /* ... */ }
    pub fn mean(&self) -> Duration { /* ... */ }
    pub fn max(&self) -> Duration { /* ... */ }
    pub fn count(&self) -> u64 { /* ... */ }
    pub fn reset(&self) { /* ... */ }
}

pub struct HotPathMetrics {
    pub ws_parse: LatencyHistogram,
    pub orderbook_update: LatencyHistogram,
    pub quote_decision: LatencyHistogram,
    pub tx_build: LatencyHistogram,
    pub tx_sign: LatencyHistogram,
    pub tx_submit: LatencyHistogram,
    pub total_tick_to_wire: LatencyHistogram,
}
```

---

## Real Market Making Example

Full async market making loop with quote updates, fill handling, inventory management, and risk checks.

```rust
use decibel_sdk::*;
use std::sync::Arc;
use tokio::sync::mpsc;

const MARKET: &str = "BTC-USD";
const MARKET_IDX: u16 = 0;
const HALF_SPREAD_BPS: f64 = 3.0;
const QUOTE_SIZE: f64 = 0.1;
const MAX_INVENTORY: f64 = 1.0;
const MAX_LEVERAGE: f64 = 5.0;
const REQUOTE_INTERVAL: Duration = Duration::from_millis(100);

#[tokio::main]
async fn main() -> Result<(), DecibelError> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let client = Arc::new(
        DecibelClient::builder()
            .config(MAINNET_CONFIG)
            .bearer_token(&std::env::var("DECIBEL_TOKEN").unwrap())
            .private_key(&std::env::var("DECIBEL_KEY").unwrap())
            .build()
            .await?,
    );

    let position_mgr = Arc::new(PositionStateManager::new());
    let bulk_mgr = Arc::new(BulkOrderManager::new(BulkConfig {
        max_orders_per_batch: 10,
        max_pending_batches: 4,
        stale_order_timeout: Duration::from_secs(5),
    }));
    let metrics = Arc::new(HotPathMetrics::default());

    let (event_tx, mut event_rx) = mpsc::channel::<StrategyEvent>(4096);

    // --- WS feed task ---
    let ws_client = client.clone();
    let ws_pos = position_mgr.clone();
    let ws_bulk = bulk_mgr.clone();
    let ws_tx = event_tx.clone();
    tokio::spawn(async move {
        let mut stream = ws_client.stream_all(MARKET).await.unwrap();
        while let Some(frame) = stream.next().await {
            match frame {
                WsEvent::Price(p) => {
                    let _ = ws_tx.try_send(StrategyEvent::PriceUpdate {
                        market_idx: MARKET_IDX,
                        mid: p.mid_px,
                        ts: p.transaction_unix_ms,
                    });
                }
                WsEvent::Position(update) => {
                    ws_pos.apply_position_update(update).await;
                }
                WsEvent::Fill(fill) => {
                    let record = FillRecord::from_ws(&fill);
                    ws_bulk.apply_fill(&record).await;
                    let _ = ws_tx.try_send(StrategyEvent::Fill(record));
                }
                _ => {}
            }
        }
    });

    // --- Strategy loop ---
    let mut last_mid: f64 = 0.0;
    let mut interval = tokio::time::interval(REQUOTE_INTERVAL);
    let mut bufs = HotPathBuffers::new();

    loop {
        tokio::select! {
            _ = interval.tick() => {
                if last_mid <= 0.0 { continue; }

                // Risk check
                let risk = position_mgr.risk().await;
                if risk.leverage_used > MAX_LEVERAGE {
                    tracing::warn!(
                        leverage = risk.leverage_used,
                        "leverage limit breached, skipping requote"
                    );
                    continue;
                }

                // Inventory skew
                let inventory = bulk_mgr.net_inventory().await;
                let skew_bps = (inventory / MAX_INVENTORY) * HALF_SPREAD_BPS;

                let bid_price = last_mid * (1.0 - (HALF_SPREAD_BPS + skew_bps) / 10_000.0);
                let ask_price = last_mid * (1.0 + (HALF_SPREAD_BPS - skew_bps) / 10_000.0);

                // Size adjustment based on inventory
                let bid_size = if inventory < MAX_INVENTORY { QUOTE_SIZE } else { 0.0 };
                let ask_size = if inventory > -MAX_INVENTORY { QUOTE_SIZE } else { 0.0 };

                let mut quotes = Vec::with_capacity(2);
                if bid_size > 0.0 {
                    quotes.push(QuoteLevel {
                        side: Side::Bid, level: 0,
                        price: bid_price, size: bid_size,
                    });
                }
                if ask_size > 0.0 {
                    quotes.push(QuoteLevel {
                        side: Side::Ask, level: 0,
                        price: ask_price, size: ask_size,
                    });
                }

                let t0 = Instant::now();
                match bulk_mgr.replace_quotes(&client, MARKET_IDX, &quotes).await {
                    Ok(result) => {
                        metrics.total_tick_to_wire.record(t0.elapsed());
                        tracing::debug!(
                            seq = result.sequence,
                            cancels = result.cancels_submitted,
                            orders = result.orders_submitted,
                            "quotes replaced"
                        );
                    }
                    Err(e) if e.requires_halt() => {
                        tracing::error!("HALT: {}", e);
                        break;
                    }
                    Err(e) if e.requires_resync() => {
                        tracing::warn!("resync required: {}", e);
                        position_mgr.resync_from_rest(&client).await.ok();
                    }
                    Err(e) => {
                        tracing::warn!("requote error: {}", e);
                    }
                }
            }

            Some(event) = event_rx.recv() => {
                match event {
                    StrategyEvent::PriceUpdate { mid, .. } => {
                        last_mid = mid;
                    }
                    StrategyEvent::Fill(fill) => {
                        tracing::info!(
                            side = ?fill.side,
                            price = fill.price,
                            size = fill.size,
                            "fill received"
                        );
                    }
                    StrategyEvent::RiskBreach(kind) => {
                        tracing::error!(?kind, "risk breach, cancelling all");
                        client.cancel_all_orders(MARKET).await.ok();
                    }
                    _ => {}
                }
            }
        }
    }

    client.cancel_all_orders(MARKET).await?;
    tracing::info!(
        p99 = ?metrics.total_tick_to_wire.p99(),
        mean = ?metrics.total_tick_to_wire.mean(),
        "shutdown complete"
    );
    Ok(())
}
```

---

## Benchmark Specifications

All benchmarks use `criterion` with statistical rigor. The following must be benchmarked and tracked across releases.

### Required Benchmarks

| Benchmark | Target | What It Measures |
|---|---|---|
| `ws_frame_deserialize` | < 500 ns | `WsFrame` zero-copy parse from raw bytes |
| `market_price_deserialize` | < 1 μs | `MarketPriceBorrowed` from JSON bytes |
| `orderbook_update_apply` | < 5 μs | Apply a 20-level orderbook delta to local state |
| `tx_build` | < 10 μs | `build_transaction()` with pre-allocated buffer |
| `tx_sign` | < 50 μs | Ed25519 sign of a typical trading transaction |
| `tx_build_and_sign` | < 60 μs | Combined build + sign pipeline |
| `position_state_read` | < 100 ns | `PositionStateManager::risk()` read lock acquire + clone |
| `position_state_write` | < 1 μs | `apply_position_update` with risk recomputation |
| `bulk_replace_quotes_local` | < 5 μs | Local state update portion of `replace_quotes` (no network) |
| `price_formatting` | < 200 ns | `round_to_valid_price` + `amount_to_chain_units` |

### Benchmark Implementation

```rust
use criterion::{criterion_group, criterion_main, Criterion, black_box};

fn bench_ws_frame_deserialize(c: &mut Criterion) {
    let raw = br#"{"topic":"market_price:0x1234","data":{"market":"BTC-USD","mark_px":45000.0,"mid_px":44999.5,"oracle_px":45001.0,"funding_rate_bps":0.01,"is_funding_positive":true,"open_interest":1500000.0,"transaction_unix_ms":1710000000000},"ts":1710000000000}"#;

    c.bench_function("ws_frame_deserialize", |b| {
        b.iter(|| {
            let _: WsFrame = serde_json::from_slice(black_box(raw)).unwrap();
        })
    });
}

fn bench_market_price_deserialize(c: &mut Criterion) {
    let json = br#"{"market":"BTC-USD","mark_px":45000.0,"mid_px":44999.5,"oracle_px":45001.0,"funding_rate_bps":0.01,"is_funding_positive":true,"open_interest":1500000.0,"transaction_unix_ms":1710000000000}"#;

    c.bench_function("market_price_deserialize", |b| {
        b.iter(|| {
            let _: MarketPriceBorrowed = serde_json::from_slice(black_box(json)).unwrap();
        })
    });
}

fn bench_tx_build(c: &mut Criterion) {
    let inputs = TransactionInputs { /* ... populated with realistic data ... */ };
    let mut buf = Vec::with_capacity(4096);

    c.bench_function("tx_build", |b| {
        b.iter(|| {
            build_transaction(black_box(&inputs), &mut buf).unwrap();
        })
    });
}

fn bench_tx_sign(c: &mut Criterion) {
    let signing_key = ed25519_dalek::SigningKey::generate(&mut rand::thread_rng());
    let raw_tx = vec![0u8; 512]; // realistic tx size

    c.bench_function("tx_sign", |b| {
        b.iter(|| {
            sign_transaction(&SigningInputs {
                raw_tx_bytes: black_box(raw_tx.clone()),
                private_key: &signing_key,
            }).unwrap();
        })
    });
}

fn bench_position_state_read(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let mgr = PositionStateManager::new();
    // pre-populate with 10 positions
    rt.block_on(async { /* populate */ });

    c.bench_function("position_state_read", |b| {
        b.to_async(&rt).iter(|| async {
            let _ = black_box(mgr.risk().await);
        })
    });
}

fn bench_orderbook_update(c: &mut Criterion) {
    let mut book = LocalOrderbook::new(50);
    let update = generate_random_update(20);

    c.bench_function("orderbook_update_apply", |b| {
        b.iter(|| {
            book.apply_update(black_box(&update));
        })
    });
}

criterion_group!(
    benches,
    bench_ws_frame_deserialize,
    bench_market_price_deserialize,
    bench_tx_build,
    bench_tx_sign,
    bench_position_state_read,
    bench_orderbook_update,
);
criterion_main!(benches);
```

---

## Dependencies

```toml
[package]
name = "decibel-sdk"
version = "2.0.0"
edition = "2021"
rust-version = "1.75"

[dependencies]
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
tokio-tungstenite = { version = "0.24", features = ["rustls-tls-native-roots"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
ed25519-dalek = { version = "2", features = ["rand_core"] }
bcs = "0.1"
thiserror = "2"
tracing = "0.1"
schemars = { version = "0.8", features = ["derive"] }
futures = "0.3"
url = "2"
rand = "0.8"
sha3 = "0.10"
hex = "0.4"
dashmap = "6"
crossbeam-channel = "0.5"

[dev-dependencies]
tokio = { version = "1", features = ["test-util", "macros"] }
tracing-subscriber = "0.3"
wiremock = "0.6"
pretty_assertions = "1"
proptest = "1"
criterion = { version = "0.5", features = ["async_tokio"] }

[[bench]]
name = "hot_path"
harness = false

[[bench]]
name = "serialization"
harness = false
```

---

## Testing

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_copy_ws_frame_parse() {
        let raw = r#"{"topic":"market_price:0x1234","data":{"mark_px":45000},"ts":1710000000000}"#;
        let frame: WsFrame = serde_json::from_str(raw).unwrap();
        assert_eq!(frame.topic, "market_price:0x1234");
        assert_eq!(frame.ts, 1710000000000);
    }

    #[test]
    fn hot_order_params_is_copy() {
        let p = HotOrderParams {
            market_idx: 0,
            price_raw: 45000_000000,
            size_raw: 100_000000,
            is_buy: true,
            time_in_force: TimeInForce::PostOnly,
            is_reduce_only: false,
            client_order_id: 1,
            sequence_number: 1,
        };
        let p2 = p; // Copy, not move
        assert_eq!(p.market_idx, p2.market_idx);
    }

    #[test]
    fn risk_recomputation() {
        let mut inner = PositionStateInner::default();
        inner.balance = BalanceState {
            equity: 100_000.0,
            available_margin: 80_000.0,
            total_margin_used: 20_000.0,
            total_unrealized_pnl: 0.0,
            total_realized_pnl: 0.0,
            withdrawable: 80_000.0,
        };
        inner.positions.insert(0, PositionState {
            market_idx: 0,
            market_name: "BTC-USD".into(),
            size: 1.0,
            entry_price: 45_000.0,
            unrealized_pnl: 0.0,
            realized_pnl: 0.0,
            leverage: 2.0,
            liquidation_price: Some(22_500.0),
            margin_used: 20_000.0,
            is_cross: true,
            last_fill_ts: 0,
        });
        inner.recompute_risk();
        assert!((inner.risk.gross_exposure - 45_000.0).abs() < 0.01);
        assert!((inner.risk.margin_ratio - 0.2).abs() < 0.01);
    }

    #[test]
    fn position_safety_flags() {
        let err = DecibelError::SequenceGap {
            expected: 10,
            actual: 15,
            safety: PositionSafety::Unknown,
        };
        assert!(err.requires_resync());
        assert!(!err.requires_halt());

        let err = DecibelError::WebSocket {
            message: "connection lost".into(),
            retryable: true,
            safety: PositionSafety::Critical,
        };
        assert!(err.requires_halt());
    }

    #[test]
    fn buffer_pool_reuse() {
        let mut pool = BufferPool::new();
        let buf = pool.tx_buf();
        buf.extend_from_slice(&[1, 2, 3]);
        assert_eq!(buf.len(), 3);
        let buf = pool.tx_buf();
        assert_eq!(buf.len(), 0); // cleared
        assert!(buf.capacity() >= 4096); // still pre-allocated
    }
}
```

### Integration Tests

```rust
#[tokio::test]
#[ignore] // requires testnet access
async fn test_bulk_replace_quotes() {
    let client = DecibelClient::builder()
        .config(TESTNET_CONFIG)
        .bearer_token(&std::env::var("DECIBEL_BEARER_TOKEN").unwrap())
        .private_key(&std::env::var("DECIBEL_PRIVATE_KEY").unwrap())
        .build()
        .await
        .unwrap();

    let bulk_mgr = BulkOrderManager::new(BulkConfig {
        max_orders_per_batch: 10,
        max_pending_batches: 4,
        stale_order_timeout: Duration::from_secs(5),
    });

    let quotes = vec![
        QuoteLevel { side: Side::Bid, level: 0, price: 10.0, size: 1.0 },
        QuoteLevel { side: Side::Ask, level: 0, price: 20.0, size: 1.0 },
    ];

    let result = bulk_mgr.replace_quotes(&client, 0, &quotes).await.unwrap();
    assert_eq!(result.orders_submitted, 2);
    assert_eq!(result.cancels_submitted, 0);
    assert_eq!(bulk_mgr.active_order_count().await, 2);

    let quotes2 = vec![
        QuoteLevel { side: Side::Bid, level: 0, price: 11.0, size: 1.0 },
        QuoteLevel { side: Side::Ask, level: 0, price: 19.0, size: 1.0 },
    ];

    let result2 = bulk_mgr.replace_quotes(&client, 0, &quotes2).await.unwrap();
    assert_eq!(result2.cancels_submitted, 2);
    assert_eq!(result2.orders_submitted, 2);
    assert!(result2.sequence > result.sequence);
}

#[tokio::test]
#[ignore]
async fn test_position_state_manager_ws_integration() {
    let client = DecibelClient::builder()
        .config(TESTNET_CONFIG)
        .bearer_token(&std::env::var("DECIBEL_BEARER_TOKEN").unwrap())
        .build()
        .await
        .unwrap();

    let pos_mgr = Arc::new(PositionStateManager::new());
    let pos_writer = pos_mgr.clone();

    let _unsub = client.subscribe_positions("0x...", move |update| {
        let mgr = pos_writer.clone();
        tokio::spawn(async move { mgr.apply_position_update(update).await });
    }).await.unwrap();

    tokio::time::sleep(Duration::from_secs(5)).await;

    let risk = pos_mgr.risk().await;
    assert!(risk.margin_ratio >= 0.0);
}
```

---

## Observability

```rust
use tracing_subscriber;

tracing_subscriber::fmt()
    .with_max_level(tracing::Level::DEBUG)
    .with_target(true)
    .init();

// The SDK emits spans and events at these targets:
// decibel::ws       — WebSocket frame parse, reconnect
// decibel::tx       — Transaction build, sign, submit
// decibel::state    — PositionStateManager, BulkOrderManager updates
// decibel::risk     — Risk metric recomputation, safety flag changes
// decibel::latency  — Hot path timing (when metrics feature enabled)
// decibel::http     — REST request/response
// decibel::gas      — Gas price updates
```
