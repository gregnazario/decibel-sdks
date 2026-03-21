# WebSocket API Specification

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

The WebSocket client provides real-time streaming data. Agents use it for live price feeds, position monitoring, order status updates, and market data streaming. The SDK manages a single shared connection with multiplexed subscriptions.

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

## Subscription API

Each subscription method returns an **unsubscribe handle**. The handle can be called to stop receiving updates for that topic.

### Python API

```python
class DecibelClient:
    # Market data
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

    # Account data
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

    # TWAP
    async def subscribe_active_twaps(
        self,
        account_addr: str,
        callback: Callable[[ActiveTwapsUpdate], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    # Bulk orders
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

/// Handle returned by subscribe methods.
/// Call `unsubscribe()` to stop receiving updates.
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
    # Each iteration yields a MarketPrice
    if price.mark_px > target:
        break

async for depth in client.stream_depth("BTC-USD", aggregation_level=1):
    # Each iteration yields a MarketDepth
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
| `Maximum client topic subscription count of 100 reached` | Too many subscriptions | Unsubscribe unused topics |

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
# Context manager (recommended)
async with DecibelClient(...) as client:
    unsub = await client.subscribe_market_price("BTC-USD", callback)
    # ... use client ...
# Connection automatically closed, all subscriptions cleaned up

# Manual cleanup
await client.close()
```

```rust
// Drop-based cleanup (Rust)
{
    let client = DecibelClient::builder().build().await?;
    let unsub = client.subscribe_market_price("BTC-USD", callback).await?;
    // ...
} // client dropped, connection closed

// Manual cleanup
client.close().await?;
```
