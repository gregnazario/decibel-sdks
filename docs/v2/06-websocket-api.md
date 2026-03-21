# WebSocket API Specification

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

The WebSocket client provides real-time streaming data. Agents use it for live price feeds, position monitoring, order status updates, and market data streaming. The SDK manages a single shared connection with multiplexed subscriptions.

For trading bots, the WebSocket is the primary data source during active operation. REST is for startup and fallback. A bot that relies on REST polling for prices will always be slower than one consuming the WebSocket stream.

## Server URL

| Network | URL |
|---|---|
| Mainnet | `wss://api.mainnet.aptoslabs.com/decibel/ws` |
| Testnet | `wss://api.testnet.aptoslabs.com/decibel/ws` |

## Authentication

WebSocket connections authenticate via the `Sec-Websocket-Protocol` header:

```
Sec-Websocket-Protocol: decibel, <BEARER_TOKEN>
```

## Connection Management

### Requirements

| Feature | Specification |
|---|---|
| **Single connection** | One WebSocket connection per client instance, shared by all subscriptions |
| **Auto-reconnect** | Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max) |
| **Heartbeat** | Server sends ping every 30s; client MUST respond with pong |
| **Session timeout** | Max 1 hour; client MUST handle reconnection |
| **Subscription restore** | After reconnect, re-subscribe to all active topics |
| **Max subscriptions** | 100 per connection (server enforced) |
| **Thread safety** | Subscribe/unsubscribe MUST be safe from any thread/task |
| **Backpressure** | Buffer incoming messages if callbacks are slow; drop oldest if buffer full |

### Connection Lifecycle

```
[Disconnected] → connect() → [Connecting] → auth success → [Connected]
     ↑                                                          |
     |                         reconnect                        |
     +←── [Reconnecting] ←── error/timeout/close ──────────────+
```

### Connection State

```python
class ConnectionState(StrEnum):
    Disconnected = "disconnected"
    Connecting = "connecting"
    Connected = "connected"
    Reconnecting = "reconnecting"
    Closing = "closing"
    Closed = "closed"
```

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConnectionState {
    Disconnected,
    Connecting,
    Connected,
    Reconnecting,
    Closing,
    Closed,
}
```

---

## Subscribe/Unsubscribe Protocol

### Subscribe Message

```json
{
  "method": "subscribe",
  "topic": "<topic_string>"
}
```

### Unsubscribe Message

```json
{
  "method": "unsubscribe",
  "topic": "<topic_string>"
}
```

### Success Response

```json
{
  "success": true,
  "method": "subscribe",
  "topic": "<topic_string>"
}
```

### Error Response

```json
{
  "success": false,
  "method": "subscribe",
  "topic": "<topic_string>",
  "error": "Error description"
}
```

---

## Topic Catalog

### Market Data Topics

| Topic Pattern | Payload Type | Description |
|---|---|---|
| `market_price:{marketAddr}` | `MarketPrice` | Real-time price for one market |
| `all_market_prices` | `AllMarketPricesUpdate` | Prices for all markets |
| `depth:{marketAddr}` | `MarketDepth` | Orderbook at finest granularity |
| `depth:{marketAddr}:{level}` | `MarketDepth` | Aggregated orderbook. Level: `1`, `2`, `5`, `10`, `100`, `1000` |
| `trades:{marketAddr}` | `MarketTradesUpdate` | Trade stream for one market |
| `market_candlestick:{marketAddr}:{interval}` | `CandlestickUpdate` | OHLCV updates. Intervals: `1m`-`1mo` |

### Account Topics

| Topic Pattern | Payload Type | Description |
|---|---|---|
| `account_overview:{accountAddr}` | `AccountOverview` | Account equity, margin, PnL |
| `account_positions:{accountAddr}` | `PositionsUpdate` | Position changes |
| `account_open_orders:{accountAddr}` | `OpenOrdersUpdate` | Open order changes |
| `order_updates:{accountAddr}` | `OrderUpdate` | Order status change events |
| `user_trades:{accountAddr}` | `UserTradesUpdate` | Trade fills |
| `notifications:{accountAddr}` | `NotificationEvent` | System notifications |

### Bulk Order Topics

| Topic Pattern | Payload Type | Description |
|---|---|---|
| `bulk_orders:{accountAddr}` | `BulkOrdersUpdate` | Bulk order status |
| `bulk_order_fills:{accountAddr}` | `BulkOrderFillsUpdate` | Bulk order fills |
| `bulk_order_rejections:{accountAddr}` | `BulkOrderRejectionsUpdate` | Bulk order rejections |

### TWAP Topics

| Topic Pattern | Payload Type | Description |
|---|---|---|
| `user_active_twaps:{accountAddr}` | `ActiveTwapsUpdate` | TWAP order updates |

---

## Subscription Priority for Trading Bots

The 100-topic limit means bots must be strategic about what they subscribe to. Not every topic is equally important.

### Tier 1: MUST subscribe (bot cannot function without these)

| Topic | Why |
|---|---|
| `order_updates:{accountAddr}` | Know immediately when orders fill, cancel, or reject. Without this, the bot is flying blind on order state. |
| `account_positions:{accountAddr}` | Real-time position changes — fill events update position size, entry price, and unrealized PnL. |
| `account_overview:{accountAddr}` | Margin usage and equity changes. Essential for risk management — detect liquidation proximity. |
| `market_price:{marketAddr}` (for each active market) | Real-time mark/index/bid/ask prices. Needed for pricing decisions. |

### Tier 2: SHOULD subscribe (significantly improves bot quality)

| Topic | Why |
|---|---|
| `depth:{marketAddr}` (finest granularity) | Local orderbook for market makers. Needed for spread calculation and queue position estimation. |
| `user_trades:{accountAddr}` | Fill details including price, size, fee, and trade action. More detail than `order_updates`. |
| `bulk_orders:{accountAddr}` | Market makers using bulk orders need confirmation of atomic replacements. |
| `bulk_order_fills:{accountAddr}` | Track which levels of bulk orders are getting hit. |

### Tier 3: NICE-TO-HAVE (subscribe if topic budget allows)

| Topic | Why |
|---|---|
| `all_market_prices` | Convenient but costs 1 topic for all markets. Prefer per-market subscriptions for markets you trade. |
| `trades:{marketAddr}` | Market trade flow — useful for detecting aggressor-side pressure. |
| `market_candlestick:{marketAddr}:{interval}` | Live candle updates — only needed if strategy relies on candle closes. |
| `bulk_order_rejections:{accountAddr}` | Rejection tracking — log-only for most bots. |
| `notifications:{accountAddr}` | System alerts — informational. |

### Per Bot Type: Required vs Optional Topics

**Market Maker** — needs all Tier 1 + depth + bulk order topics:

| Topic | Required | Notes |
|---|---|---|
| `order_updates` | REQUIRED | Must know instantly when quotes are hit |
| `account_positions` | REQUIRED | Inventory tracking drives skew |
| `account_overview` | REQUIRED | Margin headroom for new quotes |
| `market_price` (per market) | REQUIRED | Mid-price reference for quoting |
| `depth` (per market, finest) | REQUIRED | Spread calculation, liquidity detection |
| `bulk_orders` | REQUIRED (if using bulk orders) | Confirm atomic quote replacements |
| `bulk_order_fills` | REQUIRED (if using bulk orders) | Track which levels are being hit |
| `user_trades` | RECOMMENDED | Fee details for P&L tracking |
| `trades` (per market) | OPTIONAL | Flow toxicity / adverse selection detection |

**Directional / Momentum Bot** — needs price data and account state, not depth:

| Topic | Required | Notes |
|---|---|---|
| `order_updates` | REQUIRED | Confirm entries and exits |
| `account_positions` | REQUIRED | Track position after fills |
| `account_overview` | REQUIRED | Track equity, margin |
| `market_price` (per market) | REQUIRED | Signal input |
| `user_trades` | RECOMMENDED | Fill price for P&L |
| `depth` | OPTIONAL | Only for pre-trade market impact estimation |
| `market_candlestick` | OPTIONAL | Live candle closes for signal strategies |

**Risk Monitor** — reads state from many subaccounts, never places orders:

| Topic | Required | Notes |
|---|---|---|
| `account_positions` (per subaccount) | REQUIRED | Aggregate exposure monitoring |
| `account_overview` (per subaccount) | REQUIRED | Aggregate margin/equity |
| `market_price` (per market) | REQUIRED | Compute liquidation distances |
| `order_updates` | OPTIONAL | Audit trail for order activity |
| `depth` | NOT NEEDED | Risk monitors don't need orderbook |

### Topic Budget Planning

For a market maker quoting 5 markets:

| Topic Type | Count | Notes |
|---|---|---|
| `order_updates` | 1 | Per subaccount |
| `account_positions` | 1 | Per subaccount |
| `account_overview` | 1 | Per subaccount |
| `market_price` per market | 5 | One per active market |
| `depth` per market | 5 | Finest granularity for spread calculation |
| `bulk_orders` | 1 | Per subaccount |
| `bulk_order_fills` | 1 | Per subaccount |
| `user_trades` | 1 | Per subaccount |
| **Total** | **16** | Well within 100-topic limit |

For a multi-strategy bot running 3 subaccounts across 15 markets:

| Topic Type | Count | Notes |
|---|---|---|
| Account topics (4 per subaccount) | 12 | positions, overview, order_updates, user_trades |
| Market prices | 15 | One per market |
| Depth (top 5 markets only) | 5 | Budget: only subscribe to depth for actively-quoted markets |
| Bulk order topics (2 per subaccount) | 6 | Only for subaccounts doing market making |
| **Total** | **38** | Comfortable headroom |

---

## Local Orderbook Management

Market makers need to maintain a local mirror of the on-chain orderbook to calculate spreads, estimate queue position, and detect liquidity changes. The SDK provides a `LocalOrderbook` that stays synchronized via WebSocket depth updates.

### How Decibel Depth Messages Work

Decibel sends **full orderbook snapshots** on the `depth:{marketAddr}` topic, not incremental deltas. Each message contains the complete visible book at that instant. This is fundamentally different from exchanges like Binance or dYdX that send incremental updates.

**Implications for bot developers:**

| Property | Decibel (Full Snapshots) | Delta-Based Exchanges |
|---|---|---|
| Message size | Larger (full book every time) | Smaller (only changes) |
| Missed message impact | Benign — next snapshot replaces state cleanly | Catastrophic — local book diverges permanently |
| Sequence number tracking | Not required | Required to detect gaps |
| Initialization | Subscribe and use first message directly | Must request snapshot + buffer deltas |
| Local state management | Replace entire book on each update | Merge updates into existing book |

Because Decibel sends full snapshots, the `LocalOrderbook` implementation is simpler than on delta-based exchanges: each incoming depth message **replaces** local state rather than being merged into it.

### Initialization Protocol

1. Subscribe to `depth:{marketAddr}` (finest granularity, level=1).
2. Fetch a REST snapshot via `GET /depth/{marketName}?limit=50` as the initial baseline.
3. Buffer any WS messages that arrive before the REST snapshot returns.
4. Apply the REST snapshot as the baseline.
5. Apply any buffered WS messages that are newer than the REST snapshot (each one is a full replacement).
6. From this point, each incoming WS depth message replaces the local book entirely.

The buffer-and-apply step (3–5) handles the race condition between subscribing and fetching the REST snapshot. Once initialized, the full-snapshot nature of Decibel's depth messages means each update is a clean replacement — no delta application logic is needed.

```python
class LocalOrderbook:
    def __init__(self, market_addr: str):
        self.market_addr = market_addr
        self.bids: dict[float, float] = {}   # price -> size
        self.asks: dict[float, float] = {}   # price -> size
        self.last_update_ms: int = 0
        self._initialized = False
        self._buffer: list[MarketDepth] = []

    def apply_snapshot(self, depth: MarketDepth):
        """Replace the entire local book with a full snapshot.

        Used for both REST snapshots and WS depth messages,
        since Decibel sends full snapshots on both.
        """
        self.bids = {level.price: level.size for level in depth.bids if level.size > 0}
        self.asks = {level.price: level.size for level in depth.asks if level.size > 0}
        self.last_update_ms = depth.timestamp_ms
        for buffered in self._buffer:
            if buffered.timestamp_ms > depth.timestamp_ms:
                self._replace_book(buffered)
        self._buffer.clear()
        self._initialized = True

    def apply_update(self, depth: MarketDepth):
        """Handle an incoming WS depth message.

        Since Decibel sends full snapshots, this replaces the local book entirely.
        No delta merging is needed.
        """
        if not self._initialized:
            self._buffer.append(depth)
            return
        if depth.timestamp_ms <= self.last_update_ms:
            return  # stale message, ignore
        self._replace_book(depth)

    def _replace_book(self, depth: MarketDepth):
        """Replace both sides of the local book with the snapshot."""
        self.bids = {level.price: level.size for level in depth.bids if level.size > 0}
        self.asks = {level.price: level.size for level in depth.asks if level.size > 0}
        self.last_update_ms = depth.timestamp_ms

    @property
    def best_bid(self) -> float | None:
        return max(self.bids.keys()) if self.bids else None

    @property
    def best_ask(self) -> float | None:
        return min(self.asks.keys()) if self.asks else None

    @property
    def mid_price(self) -> float | None:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2.0
        return None

    @property
    def spread_bps(self) -> float | None:
        if self.best_bid and self.best_ask:
            return (self.best_ask - self.best_bid) / self.mid_price * 10_000
        return None

    def depth_at_price(self, price: float, side: str) -> float:
        book = self.bids if side == "bid" else self.asks
        return book.get(price, 0.0)

    def total_depth(self, side: str, levels: int = 10) -> float:
        book = self.bids if side == "bid" else self.asks
        prices = sorted(book.keys(), reverse=(side == "bid"))[:levels]
        return sum(book[p] for p in prices)

    def estimated_fill_price(self, side: str, size: float) -> float | None:
        """Walk the book to estimate average fill price for a given size."""
        book = self.asks if side == "buy" else self.bids
        prices = sorted(book.keys(), reverse=(side == "sell"))
        remaining = size
        total_cost = 0.0
        for price in prices:
            available = book[price]
            fill = min(remaining, available)
            total_cost += fill * price
            remaining -= fill
            if remaining <= 0:
                return total_cost / size
        return None  # insufficient liquidity
```

```rust
pub struct LocalOrderbook {
    pub market_addr: String,
    pub bids: BTreeMap<OrderedFloat<f64>, f64>,
    pub asks: BTreeMap<OrderedFloat<f64>, f64>,
    pub last_update_ms: i64,
    initialized: bool,
    buffer: Vec<MarketDepth>,
}

impl LocalOrderbook {
    pub fn best_bid(&self) -> Option<f64> {
        self.bids.keys().next_back().map(|p| p.0)
    }

    pub fn best_ask(&self) -> Option<f64> {
        self.asks.keys().next().map(|p| p.0)
    }

    pub fn spread_bps(&self) -> Option<f64> {
        let bid = self.best_bid()?;
        let ask = self.best_ask()?;
        let mid = (bid + ask) / 2.0;
        Some((ask - bid) / mid * 10_000.0)
    }

    pub fn apply_snapshot(&mut self, depth: &MarketDepth) {
        self.bids.clear();
        for level in &depth.bids {
            if level.size > 0.0 {
                self.bids.insert(OrderedFloat(level.price), level.size);
            }
        }
        self.asks.clear();
        for level in &depth.asks {
            if level.size > 0.0 {
                self.asks.insert(OrderedFloat(level.price), level.size);
            }
        }
        self.last_update_ms = depth.timestamp_ms;
        // Drain buffer, applying any messages newer than this snapshot
        let buffered: Vec<_> = self.buffer.drain(..).collect();
        for msg in buffered {
            if msg.timestamp_ms > depth.timestamp_ms {
                self.replace_book(&msg);
            }
        }
        self.initialized = true;
    }

    pub fn apply_update(&mut self, depth: &MarketDepth) {
        if !self.initialized {
            self.buffer.push(depth.clone());
            return;
        }
        if depth.timestamp_ms <= self.last_update_ms {
            return; // stale, ignore
        }
        self.replace_book(depth);
    }

    fn replace_book(&mut self, depth: &MarketDepth) {
        self.bids.clear();
        for level in &depth.bids {
            if level.size > 0.0 {
                self.bids.insert(OrderedFloat(level.price), level.size);
            }
        }
        self.asks.clear();
        for level in &depth.asks {
            if level.size > 0.0 {
                self.asks.insert(OrderedFloat(level.price), level.size);
            }
        }
        self.last_update_ms = depth.timestamp_ms;
    }
}
```

### Consistency Checks

Because Decibel sends full snapshots, consistency errors are less likely than on delta-based exchanges. However, the local orderbook should still satisfy these invariants after every update:

1. **No crossed book**: `best_bid < best_ask` (if both exist). A crossed book after a full snapshot indicates a server-side issue — log at ERROR and use the data but flag it.
2. **No zero-size entries**: The `_replace_book` method filters these out. Zero sizes should not appear in snapshots, but defensive filtering costs nothing.
3. **Monotonic timestamps**: `last_update_ms` should only increase. Out-of-order messages are silently dropped.

If the book appears crossed, do NOT trigger a full re-sync — unlike delta-based exchanges, the next snapshot will correct the state automatically. Log the anomaly and continue.

### Performance: Full Snapshot Replacement Cost

Since each depth update replaces the entire book, the cost per update is proportional to book depth:

| Book Depth | Replace Cost (Python) | Replace Cost (Rust) | Notes |
|---|---|---|---|
| 10 levels/side | < 50μs | < 5μs | Typical for most markets |
| 50 levels/side | < 200μs | < 15μs | Deep book markets (BTC, ETH) |
| 100 levels/side | < 500μs | < 30μs | Maximum useful depth |

For bots that only need top-of-book, subscribe to `depth:{marketAddr}:10` or `depth:{marketAddr}:5` to reduce message size and replacement cost.

---

## Sequence Gap Detection

WebSocket messages can be lost due to network issues. The SDK must detect gaps and trigger re-synchronization.

### Why Gaps Happen

| Cause | Frequency | Duration | Impact |
|---|---|---|---|
| Transient network blip | Common (multiple per day) | < 1s | Missed 0–2 messages |
| Server-side load shedding | Rare (during extreme volume) | 1–5s | Missed messages on busy topics |
| TCP connection reset | Uncommon | Triggers full reconnect | All topics affected |
| WS server restart | Rare (deployments) | 2–10s | Full reconnect required |
| Client-side GC pause (Python) | Occasional | 50–200ms | Usually no gap (messages buffered in OS) |

### Detection Mechanisms

Decibel does not provide sequence numbers on WS messages, so gap detection relies on heuristics:

1. **Timestamp gaps**: If the time between consecutive messages on the same topic exceeds a threshold (configurable, default 5 seconds for price topics, 30 seconds for account topics), assume a gap occurred.

2. **Orderbook inconsistency**: If the local orderbook has a crossed book (best_bid >= best_ask) after applying a snapshot, something is wrong server-side — log but do not re-sync (next snapshot will correct it).

3. **Position mismatch**: If a `user_trades` fill event references a position size that doesn't match local tracking, state is inconsistent.

4. **Order count mismatch**: If the bot's local count of open orders diverges from the `account_open_orders` update count, a fill or cancel was missed.

```python
class GapDetector:
    def __init__(self):
        self._last_seen: dict[str, int] = {}  # topic -> timestamp_ms
        self._thresholds: dict[str, int] = {
            "market_price": 5_000,       # 5s — prices should update frequently
            "depth": 5_000,              # 5s — depth updates are frequent
            "account_positions": 30_000, # 30s — positions update on fills
            "account_overview": 30_000,  # 30s
            "order_updates": 60_000,     # 60s — only fires on order events
        }
        self._gap_count: int = 0

    def check(self, topic: str, timestamp_ms: int) -> bool:
        topic_type = topic.split(":")[0]
        threshold = self._thresholds.get(topic_type, 30_000)
        last = self._last_seen.get(topic, 0)
        self._last_seen[topic] = timestamp_ms
        if last > 0 and (timestamp_ms - last) > threshold:
            self._gap_count += 1
            return True  # gap detected
        return False
```

### Re-Sync Protocol on Gap Detection

1. Mark affected data as `STALE` (see error handling doc for safety classification).
2. Immediately fetch fresh state via REST:
   - Price gap → `GET /prices/{market}`
   - Depth gap → `GET /depth/{market}` (full snapshot re-init). Note: since Decibel sends full depth snapshots, the next WS depth message will also correct state — but waiting for it introduces uncertainty.
   - Position gap → `GET /account_positions`
   - Order gap → `GET /open_orders`
3. Apply REST data as new baseline.
4. Resume processing WS messages.

```python
async def handle_gap(self, topic: str, client: DecibelClient):
    topic_type = topic.split(":")[0]
    if topic_type == "depth":
        market_name = self._addr_to_name[topic.split(":")[1]]
        snapshot = await client.get_depth(market_name, limit=50)
        self._orderbook.apply_snapshot(snapshot)
    elif topic_type == "account_positions":
        account = topic.split(":")[1]
        positions = await client.get_positions(account=account)
        self._position_state.replace_all(positions)
    elif topic_type == "market_price":
        market_name = self._addr_to_name[topic.split(":")[1]]
        prices = await client.get_price(market_name)
        self._price_state.update(prices[0])
    elif topic_type == "order_updates":
        account = topic.split(":")[1]
        orders = await client.get_open_orders(account=account)
        self._order_state.replace_all(orders)
```

### Gap Detection vs Full-Snapshot Topics

Because Decibel's `depth` topic sends full snapshots (not deltas), a missed depth message is self-correcting: the next message contains the entire book. This means depth gaps are less dangerous than on delta-based exchanges. The bot can choose to:

1. **Eagerly re-sync** (safer): Immediately fetch `GET /depth/{market}` from REST on gap detection. This guarantees the book is correct within ~50ms.
2. **Wait for next WS message** (simpler): Since the next depth message is a full snapshot, it will correct the local book automatically. The tradeoff is quoting on a stale book for 1–3 seconds.

For price and account topics, which do not carry full state snapshots, REST re-sync is always required on gap detection.

---

## Message Processing Pipeline

The SDK processes incoming WebSocket messages through a multi-stage pipeline designed to never block the network read loop.

### Architecture

```
Network Socket
    │
    ▼
┌──────────────────┐
│  Read Loop        │  Single task, never blocks
│  (raw bytes)      │  Reads frames as fast as the network delivers
│                   │
│  ┌─────────────┐  │
│  │ Parse JSON   │  │  < 100μs (Rust) / < 500μs (Python)
│  │ Extract topic│  │
│  └──────┬──────┘  │
│         │         │
│  ┌──────▼──────┐  │
│  │ Route to    │  │  O(1) HashMap lookup by topic string
│  │ topic queue  │  │
│  └──────┬──────┘  │
└─────────┼─────────┘
          │
    ┌─────▼─────┐
    │ Per-Topic  │  Bounded channel (default: 100 messages)
    │ Queue      │  MPSC: read loop produces, callback task consumes
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │ Callback   │  Per-topic consumer task
    │ Executor   │  Deserializes to typed model, invokes user callback
    └───────────┘
```

### Backpressure Behavior

| Queue State | Behavior |
|---|---|
| Below 80% capacity | Normal operation |
| Above 80% capacity | Log `WARN`: "Topic {topic} queue at {pct}% capacity" |
| Full (100%) | Drop oldest message, log `WARN` with drop count |
| Sustained drops (>10/s) | Log `ERROR`: "Callback for {topic} cannot keep up" |

### Type Dispatch

The read loop extracts the `topic` field from the JSON envelope and routes to the correct deserializer:

```python
_TOPIC_DESERIALIZERS = {
    "market_price":        MarketPrice.model_validate,
    "all_market_prices":   AllMarketPricesUpdate.model_validate,
    "depth":               MarketDepth.model_validate,
    "trades":              MarketTradesUpdate.model_validate,
    "account_overview":    AccountOverview.model_validate,
    "account_positions":   PositionsUpdate.model_validate,
    "account_open_orders": OpenOrdersUpdate.model_validate,
    "order_updates":       OrderUpdate.model_validate,
    "user_trades":         UserTradesUpdate.model_validate,
    "bulk_orders":         BulkOrdersUpdate.model_validate,
    "bulk_order_fills":    BulkOrderFillsUpdate.model_validate,
    "bulk_order_rejections": BulkOrderRejectionsUpdate.model_validate,
    "user_active_twaps":   ActiveTwapsUpdate.model_validate,
    "notifications":       NotificationEvent.model_validate,
}

async def _dispatch(self, raw_msg: str):
    envelope = json.loads(raw_msg)
    topic_str = envelope.get("topic", "")
    topic_type = topic_str.split(":")[0]
    deserializer = _TOPIC_DESERIALIZERS.get(topic_type)
    if deserializer is None:
        logger.warning(f"Unknown topic type: {topic_type}")
        return
    typed_data = deserializer(envelope["data"])
    queue = self._topic_queues.get(topic_str)
    if queue is not None:
        if queue.full():
            queue.get_nowait()  # drop oldest
            self._drop_counts[topic_str] += 1
        await queue.put(typed_data)
```

```rust
async fn dispatch(&self, raw: &str) -> Result<(), DecibelError> {
    let envelope: WsEnvelope = serde_json::from_str(raw)?;
    let topic_type = envelope.topic.split(':').next().unwrap_or("");
    match topic_type {
        "market_price" => {
            let data: MarketPrice = serde_json::from_value(envelope.data)?;
            self.route(&envelope.topic, data).await;
        }
        "depth" => {
            let data: MarketDepth = serde_json::from_value(envelope.data)?;
            self.route(&envelope.topic, data).await;
        }
        // ... other topic types
        _ => tracing::warn!("Unknown topic: {}", topic_type),
    }
    Ok(())
}
```

---

## State Synchronization on Reconnect

When the WebSocket connection drops and reconnects, the bot's streaming state has a gap. The SDK must handle this systematically to avoid trading on stale data.

### Step-by-Step Reconnection Protocol

```
1. Connection drops
   ├── Record disconnect timestamp (monotonic clock)
   ├── Mark all WS-sourced state as STALE
   ├── Halt any pending order submissions (cannot confirm via WS)
   ├── Pull all resting quotes (market makers)
   └── Start reconnection with exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)

2. Connection re-established
   ├── Record reconnect timestamp (compute gap duration)
   ├── Re-subscribe to ALL active topics (batch subscribe messages)
   └── Wait for subscription confirmations (timeout: 10s per batch of 20)

3. After all subscriptions confirmed
   ├── Evaluate gap impact (LOW / MEDIUM / HIGH)
   ├── Fetch REST snapshots for critical state (always, regardless of gap size):
   │   ├── GET /account_positions?account={subaccount}
   │   ├── GET /open_orders?account={subaccount}
   │   ├── GET /account_overviews?account={subaccount}
   │   └── GET /depth/{market} (for each orderbook being tracked)
   ├── Apply REST snapshots as new baseline (replace, not merge)
   └── Mark state as FRESH

4. Resume normal operation
   ├── Process incoming WS messages normally
   ├── Resume order submissions
   ├── For HIGH gap impact: cancel all resting orders before resuming
   └── Log reconnection metrics (gap_duration_ms, topics_restored, rest_sync_duration_ms)
```

### Reconnection Timing Constraints

| Phase | Target Duration | Timeout |
|---|---|---|
| TCP + WS handshake | 200–500ms | 5s |
| Authentication | < 100ms | 2s |
| Re-subscribe all topics (batched) | 200–500ms | 10s |
| REST state sync (parallel fetches) | 100–300ms | 5s |
| **Total reconnect-to-trading** | **< 2s** | **30s (abort and retry)** |

If the total reconnection takes longer than 30 seconds, the bot should log an ERROR and attempt a fresh connection from scratch (new WebSocket, new subscriptions, full REST sync).

### Python Implementation

```python
async def _on_reconnect(self):
    reconnect_start = time.monotonic()
    gap_ms = (reconnect_start - self._disconnect_timestamp) * 1000
    self._state_freshness = StateFreshness.STALE
    logger.warning(f"WS reconnected after {gap_ms:.0f}ms gap, re-syncing state")

    await self._resubscribe_all()

    positions, orders, overview = await asyncio.gather(
        self._http.get(f"/account_positions?account={self._subaccount}"),
        self._http.get(f"/open_orders?account={self._subaccount}"),
        self._http.get(f"/account_overviews?account={self._subaccount}"),
    )

    self._position_state.replace_all(positions)
    self._order_state.replace_all(orders)
    self._account_state.update(overview)

    for market_addr, orderbook in self._orderbooks.items():
        market_name = self._addr_to_name[market_addr]
        snapshot = await self._http.get(f"/depth/{market_name}?limit=50")
        orderbook.apply_snapshot(snapshot)

    impact = self.estimate_gap_impact(int(gap_ms))
    if impact == "HIGH":
        await self._cancel_all_resting_orders()
        logger.warning("HIGH gap impact: cancelled all resting orders before resuming")

    self._state_freshness = StateFreshness.FRESH
    sync_ms = (time.monotonic() - reconnect_start) * 1000
    logger.info(f"State re-sync complete in {sync_ms:.0f}ms, gap impact={impact}")
    self._metrics.record_reconnect(gap_ms=gap_ms, sync_ms=sync_ms, impact=impact)
```

### Gap Estimation

After reconnection, estimate the gap duration to decide if additional reconciliation is needed:

```python
def estimate_gap_impact(self, disconnect_duration_ms: int) -> str:
    if disconnect_duration_ms < 2_000:
        return "LOW"    # likely missed 0-2 price ticks, positions unchanged
    elif disconnect_duration_ms < 30_000:
        return "MEDIUM" # may have missed fills, funding accrual, price moves
    else:
        return "HIGH"   # significant state divergence possible, full re-sync required
```

| Gap Duration | Impact Level | What May Have Changed | Bot Action After Sync |
|---|---|---|---|
| < 2s | LOW | 1–2 price updates missed | Resume immediately after REST sync |
| 2–30s | MEDIUM | Possible fills, cancel events, price movements | Resume after REST sync + verify all open order states |
| > 30s | HIGH | Fills, liquidation events, significant price moves, funding accrual | Cancel all resting orders, full REST sync, recompute risk, then resume cautiously |

### Handling Repeated Disconnections

If the WS connection drops and reconnects more than 3 times within 60 seconds, the bot should:

1. Enter a **degraded mode**: switch entirely to REST polling for critical data.
2. Stop placing new orders until WS stability is confirmed (5 minutes of uninterrupted connection).
3. Alert the operator via the configured alert channel.

```python
class ReconnectionTracker:
    def __init__(self, max_reconnects: int = 3, window_s: float = 60.0):
        self._timestamps: collections.deque = collections.deque(maxlen=max_reconnects + 1)
        self._max = max_reconnects
        self._window = window_s

    def record_reconnect(self) -> bool:
        now = time.monotonic()
        self._timestamps.append(now)
        recent = [t for t in self._timestamps if now - t < self._window]
        if len(recent) > self._max:
            return True  # too many reconnects, enter degraded mode
        return False
```

---

## Latency Measurement and Stale Data Detection

For trading bots, knowing the age of data is as important as having the data. A price update that arrived 500ms ago is usable for a directional bot but potentially dangerous for a market maker quoting tight spreads.

### Measuring WebSocket Message Latency

Every WS message includes a server-side timestamp. By comparing this to local receipt time, the bot can measure one-way latency:

```python
class WsLatencyTracker:
    def __init__(self, time_delta_ms: int = 0):
        self._time_delta_ms = time_delta_ms
        self._latencies: dict[str, collections.deque] = defaultdict(
            lambda: collections.deque(maxlen=100)
        )

    def record(self, topic: str, server_timestamp_ms: int):
        local_now_ms = int(time.time() * 1000) + self._time_delta_ms
        latency_ms = local_now_ms - server_timestamp_ms
        self._latencies[topic].append(latency_ms)

    def p50(self, topic: str) -> float:
        samples = self._latencies.get(topic)
        if not samples:
            return 0.0
        s = sorted(samples)
        return s[len(s) // 2]

    def p99(self, topic: str) -> float:
        samples = self._latencies.get(topic)
        if not samples:
            return 0.0
        s = sorted(samples)
        return s[int(len(s) * 0.99)]

    def is_degraded(self, topic: str, threshold_ms: float = 500) -> bool:
        return self.p50(topic) > threshold_ms
```

**Important**: The `time_delta_ms` parameter corrects for clock drift between the bot's host and the server. See [07-transaction-builder.md](./07-transaction-builder.md) for how to compute and maintain this value. Without clock correction, latency measurements can be wildly inaccurate — a bot whose clock is 200ms behind the server will report all messages as having 200ms latency even if delivery is instantaneous.

### Detecting Stale Data

Stale data detection operates at two levels:

**Level 1: Message gap detection** — no message received on a topic for longer than expected:

```python
class StalenessDetector:
    EXPECTED_INTERVALS_MS = {
        "market_price":     2_000,   # prices update ~500ms, 2s gap is unusual
        "depth":            3_000,   # depth updates every 1-2s
        "account_positions": 30_000, # only fires on fills
        "account_overview":  30_000, # only fires on state changes
        "order_updates":    60_000,  # only fires on order events
    }

    def __init__(self):
        self._last_seen: dict[str, float] = {}

    def record(self, topic: str):
        self._last_seen[topic] = time.monotonic()

    def stale_topics(self) -> list[tuple[str, float]]:
        """Return list of (topic, seconds_since_last_update) for stale topics."""
        now = time.monotonic()
        stale = []
        for topic, last in self._last_seen.items():
            topic_type = topic.split(":")[0]
            threshold_s = self.EXPECTED_INTERVALS_MS.get(topic_type, 30_000) / 1000.0
            gap_s = now - last
            if gap_s > threshold_s:
                stale.append((topic, gap_s))
        return stale
```

**Level 2: Data content validation** — the message arrived but the data looks wrong:

| Check | Condition | Action |
|---|---|---|
| Price sanity | `mark_px` moved > 10% from last value in a single update | Log WARNING, use data but flag for review |
| Book integrity | `best_bid >= best_ask` | Log ERROR, wait for next snapshot |
| Position sign flip | Position went from long to short (or vice versa) in one update without a corresponding fill | Trigger REST reconciliation |
| Equity spike | `account_equity` changed > 50% in one update | Trigger REST reconciliation |

### Bot Actions on Stale Data

When data is detected as stale, the bot's response depends on which data is stale:

| Stale Data | Market Maker Response | Directional Bot Response |
|---|---|---|
| Prices stale > 2s | **Pull all quotes immediately** — quoting on stale prices is the #1 cause of adverse selection. | Pause signal evaluation. Do not enter new positions. |
| Depth stale > 5s | Continue quoting but widen spreads by 2x as a safety buffer. | No immediate impact (directional bots rarely use depth). |
| Positions stale > 10s | Pull all quotes. Cannot quote safely without knowing inventory. | Halt new entries. Existing positions remain (no panic close). |
| Account overview stale > 30s | Reduce position limits by 50% (margin data is uncertain). | Reduce position limits by 50%. |
| Order updates stale > 10s | Pull all quotes, switch to REST polling for order status. | Switch to REST polling for order status. |

```python
async def handle_stale_data(self, stale_topics: list[tuple[str, float]]):
    for topic, gap_s in stale_topics:
        topic_type = topic.split(":")[0]
        if topic_type == "market_price" and gap_s > 2.0:
            market_addr = topic.split(":")[1]
            await self._pull_quotes(market_addr)
            logger.warning(f"Pulled quotes for {market_addr}: price stale {gap_s:.1f}s")
        elif topic_type == "account_positions" and gap_s > 10.0:
            await self._pull_all_quotes()
            await self._reconcile_positions_from_rest()
            logger.error(f"Position data stale {gap_s:.1f}s, pulled all quotes")
```

### Latency Alerting Thresholds

| Metric | Warning | Critical | Action at Critical |
|---|---|---|---|
| WS message p50 latency | > 200ms | > 500ms | Widen spreads / reduce position size |
| WS message p99 latency | > 1s | > 3s | Consider secondary WS connection |
| Time since last heartbeat (pong) | > 45s | > 60s | Force reconnect |
| Gap between consecutive price updates | > 3s | > 10s | Switch to REST polling for that market |

---

## Topic Budget Management

With a 100-topic server-enforced limit, bots that operate across many markets or subaccounts must manage their subscription budget carefully.

### Dynamic Subscription Management

Market makers that rotate between markets should subscribe/unsubscribe dynamically:

```python
class TopicBudgetManager:
    def __init__(self, ws_client, max_topics: int = 100):
        self._ws = ws_client
        self._max_topics = max_topics
        self._active: dict[str, int] = {}   # topic -> priority (1=highest)
        self._handles: dict[str, Callable] = {}  # topic -> unsubscribe handle

    @property
    def remaining(self) -> int:
        return self._max_topics - len(self._active)

    async def subscribe(self, topic: str, priority: int, callback) -> bool:
        if topic in self._active:
            return True  # already subscribed

        if self.remaining <= 0:
            evicted = await self._evict_lowest_priority()
            if not evicted:
                logger.error(f"Cannot subscribe to {topic}: budget exhausted, nothing to evict")
                return False

        handle = await self._ws.subscribe(topic, callback)
        self._active[topic] = priority
        self._handles[topic] = handle
        return True

    async def _evict_lowest_priority(self) -> bool:
        if not self._active:
            return False
        lowest_topic = max(self._active, key=self._active.get)  # highest number = lowest priority
        await self._handles[lowest_topic]()
        del self._active[lowest_topic]
        del self._handles[lowest_topic]
        logger.info(f"Evicted low-priority topic: {lowest_topic}")
        return True
```

### Static Budget Allocation for Multi-Market Bots

For a bot that trades N markets with M subaccounts:

```
Required topics = M × 4 (account topics) + N × 2 (price + depth) + M × 2 (bulk order topics)

Example: 3 subaccounts, 20 markets
  = 3×4 + 20×2 + 3×2
  = 12 + 40 + 6
  = 58 topics (42 remaining for optional subscriptions)
```

If the budget would exceed 100, the bot must either:
1. Reduce the number of actively-traded markets (subscribe to depth only for top markets by volume).
2. Use `all_market_prices` instead of per-market price subscriptions (saves N-1 topics).
3. Share subaccount topic data across strategies using local fan-out.

### Multi-Subaccount Subscription Management

Bots that trade across many subaccounts (common for fund structures or segregated-risk strategies) face a specific challenge: account topics multiply by subaccount count, quickly consuming the 100-topic budget.

#### The Problem

Each subaccount needs up to 7 topics for full coverage:

| Topic | Required? |
|---|---|
| `order_updates:{addr}` | YES — order confirmations |
| `account_positions:{addr}` | YES — position tracking |
| `account_overview:{addr}` | YES — margin monitoring |
| `user_trades:{addr}` | Recommended — fill details |
| `account_open_orders:{addr}` | Optional — can use REST |
| `bulk_orders:{addr}` | Only for MM subaccounts |
| `bulk_order_fills:{addr}` | Only for MM subaccounts |

At 4–7 topics per subaccount, a bot managing 15+ subaccounts exceeds the 100-topic limit on account topics alone, with nothing left for market data.

#### Strategy 1: Tiered Subaccount Subscriptions

Not every subaccount needs full WS coverage. Classify subaccounts by activity level:

```python
class SubaccountTier:
    ACTIVE = "active"       # currently trading — full WS coverage
    MONITORED = "monitored" # has positions but not actively trading — reduced WS
    DORMANT = "dormant"     # no positions, no orders — REST-only

TIER_TOPICS = {
    SubaccountTier.ACTIVE: [
        "order_updates", "account_positions", "account_overview", "user_trades",
    ],
    SubaccountTier.MONITORED: [
        "account_positions", "account_overview",
    ],
    SubaccountTier.DORMANT: [],
}
```

A bot with 20 subaccounts where only 5 are active:

```
Active (5 subaccounts × 4 topics)    = 20 topics
Monitored (10 subaccounts × 2 topics) = 20 topics
Dormant (5 subaccounts × 0 topics)   = 0 topics
Market data (10 markets × 2 topics)  = 20 topics
Total                                 = 60 topics (40 remaining)
```

#### Strategy 2: Promote/Demote on Activity

When a dormant subaccount needs to trade, promote it to ACTIVE and demote an ACTIVE subaccount that has finished its current task:

```python
class SubaccountSubscriptionManager:
    def __init__(self, ws_client, budget_manager: TopicBudgetManager):
        self._ws = ws_client
        self._budget = budget_manager
        self._tiers: dict[str, str] = {}  # subaccount_addr -> tier
        self._handles: dict[str, list] = {}

    async def promote(self, subaccount: str, tier: str):
        old_tier = self._tiers.get(subaccount, SubaccountTier.DORMANT)
        if old_tier == tier:
            return

        await self._unsubscribe_tier_topics(subaccount, old_tier)

        new_topics = TIER_TOPICS[tier]
        handles = []
        for topic_type in new_topics:
            topic = f"{topic_type}:{subaccount}"
            priority = 1 if topic_type == "order_updates" else 2
            success = await self._budget.subscribe(
                topic, priority, self._dispatch
            )
            if success:
                handles.append(topic)
            else:
                logger.warning(f"Failed to subscribe {topic}: budget exhausted")
        self._handles[subaccount] = handles
        self._tiers[subaccount] = tier

    async def demote(self, subaccount: str, tier: str):
        await self._unsubscribe_tier_topics(
            subaccount, self._tiers.get(subaccount, SubaccountTier.DORMANT)
        )
        self._tiers[subaccount] = tier
        if tier != SubaccountTier.DORMANT:
            await self.promote(subaccount, tier)
```

#### Strategy 3: Single Aggregation Connection

For monitoring-only use cases (risk dashboards, P&L trackers), use a single WS connection that subscribes to `account_positions` and `account_overview` for all subaccounts, and fans out locally:

```python
class AggregatedAccountMonitor:
    def __init__(self, ws_client, subaccounts: list[str]):
        self._ws = ws_client
        self._state: dict[str, AccountState] = {}
        self._callbacks: list[Callable] = []

    async def start(self, subaccounts: list[str]):
        for addr in subaccounts:
            await self._ws.subscribe(
                f"account_positions:{addr}", self._on_position_update
            )
            await self._ws.subscribe(
                f"account_overview:{addr}", self._on_overview_update
            )

    def on_aggregate_update(self, callback: Callable):
        self._callbacks.append(callback)

    async def _on_position_update(self, update: PositionsUpdate):
        self._state[update.account].positions = update.positions
        aggregate = self._compute_aggregate()
        for cb in self._callbacks:
            await cb(aggregate)

    def _compute_aggregate(self) -> AggregateRisk:
        total_equity = sum(s.equity for s in self._state.values())
        total_margin = sum(s.margin_used for s in self._state.values())
        return AggregateRisk(
            total_equity=total_equity,
            total_margin_used=total_margin,
            margin_utilization=total_margin / total_equity if total_equity > 0 else 0,
            subaccount_count=len(self._state),
        )
```

#### Budget Limits by Architecture

| Architecture | Max Subaccounts | Max Markets | Topic Usage |
|---|---|---|---|
| Single MM subaccount, 5 markets | 1 | 5 | 16 topics |
| Multi-strategy, 3 subaccounts active | 3 active + N monitored | 15 | 38–60 topics |
| Fund with 20 subaccounts | 5 active + 15 monitored | 10 | 70–80 topics |
| Risk monitor only (no trading) | 0 active + 40 monitored | 0 | 80 topics |
| Maximum practical (single connection) | 5 active + 20 monitored | 10 | ~95 topics |

If you need more than 100 topics, you MUST use multiple WebSocket connections (each with its own authentication). Partition by subaccount group or by data type (one connection for market data, another for account data).

---

## Subscription API

Each subscription method returns an **unsubscribe handle**. The handle can be called to stop receiving updates for that topic.

### Python API

```python
class DecibelClient:
    async def subscribe_market_price(
        self,
        market_name: str,
        callback: Callable[[MarketPrice], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]:
        """Subscribe to real-time price updates for a market.

        Args:
            market_name: Market name (e.g., "BTC-USD"). Resolved to address internally.
            callback: Async function called with each MarketPrice update.

        Returns:
            An async callable that unsubscribes when awaited.
        """
        ...

    async def subscribe_all_market_prices(
        self,
        callback: Callable[[AllMarketPricesUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_depth(
        self,
        market_name: str,
        aggregation_level: int = 1,
        callback: Callable[[MarketDepth], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_trades(
        self,
        market_name: str,
        callback: Callable[[MarketTradesUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_candlestick(
        self,
        market_name: str,
        interval: CandlestickInterval,
        callback: Callable[[CandlestickUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_account_overview(
        self,
        account_addr: str,
        callback: Callable[[AccountOverview], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_positions(
        self,
        account_addr: str,
        callback: Callable[[PositionsUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_open_orders(
        self,
        account_addr: str,
        callback: Callable[[OpenOrdersUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_order_updates(
        self,
        account_addr: str,
        callback: Callable[[OrderUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_user_trades(
        self,
        account_addr: str,
        callback: Callable[[UserTradesUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_notifications(
        self,
        account_addr: str,
        callback: Callable[[NotificationEvent], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_active_twaps(
        self,
        account_addr: str,
        callback: Callable[[ActiveTwapsUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_bulk_orders(
        self,
        account_addr: str,
        callback: Callable[[BulkOrdersUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    async def subscribe_bulk_order_fills(
        self,
        account_addr: str,
        callback: Callable[[BulkOrderFillsUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...
```

### Rust API

```rust
impl DecibelClient {
    pub async fn subscribe_market_price<F>(
        &self,
        market_name: &str,
        callback: F,
    ) -> Result<SubscriptionHandle, DecibelError>
    where
        F: Fn(MarketPrice) + Send + Sync + 'static;

    pub async fn subscribe_all_market_prices<F>(
        &self,
        callback: F,
    ) -> Result<SubscriptionHandle, DecibelError>
    where
        F: Fn(AllMarketPricesUpdate) + Send + Sync + 'static;

    pub async fn subscribe_depth<F>(
        &self,
        market_name: &str,
        aggregation_level: u16,
        callback: F,
    ) -> Result<SubscriptionHandle, DecibelError>
    where
        F: Fn(MarketDepth) + Send + Sync + 'static;

    // ... similar pattern for all other topics
}

pub struct SubscriptionHandle { /* ... */ }

impl SubscriptionHandle {
    pub async fn unsubscribe(self) -> Result<(), DecibelError>;
}
```

---

## Async Iterator / Stream Alternative

For agents that prefer pull-based consumption over callbacks:

### Python

```python
async for price in client.stream_market_price("BTC-USD"):
    if price.mark_px > target:
        break

async for depth in client.stream_depth("BTC-USD", aggregation_level=1):
    best_bid = depth.bids[0].price if depth.bids else None
    ...
```

### Rust

```rust
use futures::StreamExt;

let mut stream = client.stream_market_price("BTC-USD").await?;
while let Some(price) = stream.next().await {
    let price = price?;
    if price.mark_px > target {
        break;
    }
}
```

---

## Message Dispatch Architecture

```
WebSocket Connection (single)
    │
    ├─ Read Loop (background task)
    │   ├─ Parse JSON envelope { "topic": "...", "data": { ... } }
    │   ├─ Route by topic to registered callback
    │   └─ If callback is slow, buffer in per-topic queue
    │
    ├─ Write Queue
    │   ├─ Subscribe/unsubscribe messages
    │   └─ Pong responses
    │
    └─ Reconnection Manager
        ├─ Detect disconnection (ping timeout, error, close frame)
        ├─ Exponential backoff reconnection
        └─ Re-subscribe all active topics on reconnection
```

### Performance Requirements

| Metric | Target (Python) | Target (Rust) |
|---|---|---|
| Message parse latency | < 1ms | < 100μs |
| Callback dispatch latency | < 500μs | < 50μs |
| Reconnection time | < 5s | < 2s |
| Memory per subscription | < 1KB overhead | < 256B overhead |

### Backpressure

If a callback processes messages slower than they arrive:

1. Messages are buffered in a per-topic bounded queue (default: 100 messages).
2. If the queue is full, the oldest message is dropped and a warning is logged.
3. The WebSocket read loop is never blocked by slow callbacks.

---

## Error Handling

### Common WebSocket Errors

| Error | Description | Recovery |
|---|---|---|
| `Unknown topic type '{name}'` | Invalid channel name | Fix topic string |
| `Missing user address for {topic} topic` | Topic requires address | Include address |
| `Missing market address for {topic} topic` | Topic requires market | Include market |
| `Invalid user address '{addr}'` | Malformed address | Fix address format |
| `Invalid market address '{addr}'` | Malformed address | Fix address format |
| `Invalid aggregation level '{level}'` | Invalid depth level | Use 1, 2, 5, 10, 100, or 1000 |
| `Invalid interval '{interval}'` | Invalid candlestick interval | Use valid interval string |
| `Maximum client topic subscription count of 100 reached` | Too many subscriptions | Unsubscribe unused topics first |

### Error Callback

The client accepts an optional error callback for WebSocket-level errors:

```python
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="...",
    on_ws_error=lambda e: logger.error(f"WS error: {e}"),
)
```

```rust
let client = DecibelClient::builder()
    .config(MAINNET_CONFIG)
    .bearer_token("...")
    .on_ws_error(|e| tracing::error!("WS error: {}", e))
    .build()
    .await?;
```

---

## Lifecycle Management

### Cleanup

The client MUST properly clean up WebSocket resources:

```python
async with DecibelClient(...) as client:
    unsub = await client.subscribe_market_price("BTC-USD", callback)
    # ... use client ...
# Connection automatically closed, all subscriptions cleaned up

await client.close()
```

```rust
{
    let client = DecibelClient::builder().build().await?;
    let unsub = client.subscribe_market_price("BTC-USD", callback).await?;
    // ...
} // client dropped, connection closed

client.close().await?;
```
