# REST API Client Specification

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

The REST API client handles all HTTP communication with the Decibel trading API. It is the backbone of read operations and provides the foundation for market data queries, account state inspection, and historical data retrieval.

For trading bots, the REST API serves two critical roles: (1) startup initialization — warming caches, fetching market configs, and establishing baseline state — and (2) fallback data source when WebSocket data is stale or unavailable.

## Base URL

All endpoints are under `{config.trading_http_url}/api/v1/`.

| Network | Base URL |
|---|---|
| Mainnet | `https://api.mainnet.aptoslabs.com/decibel/api/v1/` |
| Testnet | `https://api.testnet.aptoslabs.com/decibel/api/v1/` |

## Authentication

Every request MUST include:

| Header | Value | Required |
|---|---|---|
| `Authorization` | `Bearer <token>` | YES |
| `Origin` | Application origin URL | YES |

## HTTP Client Requirements

| Requirement | Description |
|---|---|
| **Connection pooling** | MUST reuse TCP connections. HTTP/2 preferred. |
| **Timeouts** | Default 30s per request, configurable. |
| **Retries** | Automatic retry on 5xx and network errors with exponential backoff. |
| **Compression** | MUST accept `gzip` responses. |
| **Content type** | All requests send/receive `application/json`. |

### Python Implementation

```python
import httpx

class HttpClient:
    def __init__(self, base_url: str, bearer_token: str, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Origin": "https://app.decibel.trade",
                "Accept-Encoding": "gzip",
            },
            timeout=timeout,
            http2=True,
        )
```

### Rust Implementation

```rust
use reqwest::Client;

pub struct HttpClient {
    client: Client,
    base_url: String,
}

impl HttpClient {
    pub fn new(base_url: &str, bearer_token: &str, timeout: Duration) -> Self {
        let client = Client::builder()
            .default_headers({
                let mut h = reqwest::header::HeaderMap::new();
                h.insert("Authorization", format!("Bearer {}", bearer_token).parse().unwrap());
                h.insert("Origin", "https://app.decibel.trade".parse().unwrap());
                h
            })
            .timeout(timeout)
            .pool_max_idle_per_host(10)
            .gzip(true)
            .build()
            .unwrap();
        Self { client, base_url: base_url.to_string() }
    }
}
```

## Generic Request Methods

The HTTP client MUST expose typed generic methods. The return type is always deserialized before reaching the caller.

### Method Signatures

```
async get<T>(path, query_params?) -> Result<T, DecibelError>
async post<T>(path, body) -> Result<T, DecibelError>
async patch<T>(path, body) -> Result<T, DecibelError>
```

### Error Mapping

| HTTP Status | SDK Error |
|---|---|
| 200-299 | Success — deserialize body to `T` |
| 400 | `ValidationError` |
| 401 | `AuthenticationError` |
| 404 | `ApiError::NotFound` |
| 429 | `RateLimitError` (parse `Retry-After` header) |
| 500-599 | `ApiError::Server` (retryable) |
| Timeout | `TimeoutError` (retryable) |
| Connection refused | `ConnectionError` (retryable) |

---

## Bot Startup: Cache Warming Strategy

When a trading bot starts, it needs to establish baseline state as fast as possible. The SDK provides a structured startup sequence that parallelizes independent fetches and orders dependent ones correctly.

### Phase 1: Critical Path (parallel, block until complete)

These three requests execute concurrently. No trading can happen until all complete:

```python
async def warm_caches(client: DecibelClient, subaccount: str):
    markets, prices, positions = await asyncio.gather(
        client.get_markets(),                        # GET /markets
        client.get_prices(market="all"),              # GET /prices?market=all
        client.get_positions(account=subaccount),     # GET /account_positions?account=...
    )
    return markets, prices, positions
```

```rust
let (markets, prices, positions) = tokio::join!(
    client.get_markets(),
    client.get_prices(Some("all")),
    client.get_positions(subaccount),
);
```

| Request | Why it's critical | Typical latency |
|---|---|---|
| `GET /markets` | Needed to resolve market names → addresses, get tick_size/lot_size for order formatting | 30–80ms |
| `GET /prices?market=all` | Baseline mark prices for every market — needed before any order pricing decision | 20–50ms |
| `GET /account_positions?account=...` | Must know current exposure before placing any new orders | 30–80ms |

### Phase 2: Important (parallel, needed before active trading)

After Phase 1 completes, fetch account-level data:

```python
overview, open_orders, active_twaps = await asyncio.gather(
    client.get_account_overview(account=subaccount),    # GET /account_overviews
    client.get_open_orders(account=subaccount),         # GET /open_orders
    client.get_active_twaps(account=subaccount),        # GET /active_twaps
)
```

| Request | Why it matters |
|---|---|
| `GET /account_overviews` | Equity, margin usage, fee tier — needed for position sizing and fee calculation |
| `GET /open_orders` | Must reconcile any resting orders from a previous session before placing new ones |
| `GET /active_twaps` | Avoid duplicate TWAP submissions if the bot restarted mid-execution |

### Phase 3: Deferred (can happen after trading starts)

These can be fetched lazily or in the background:

| Request | When to fetch |
|---|---|
| `GET /asset-contexts` | Before any market-scanning logic needs 24h volume/OI data |
| `GET /candlesticks/{market}` | When the strategy needs historical OHLCV for signal computation |
| `GET /bulk_orders` | Only if running a market-making strategy with bulk orders |
| `GET /order_history` | Only for reconciliation or P&L calculation |
| `GET /vaults` | Only if managing a vault |

### Startup Timing Budget

| Phase | Target (Python) | Target (Rust) |
|---|---|---|
| Phase 1 (parallel) | < 200ms | < 100ms |
| Phase 2 (parallel) | < 200ms | < 100ms |
| Phase 3 (background) | Non-blocking | Non-blocking |
| Total time to first trade | < 500ms | < 250ms |

---

## Rate Limit Budget Allocation

The API enforces per-IP rate limits. Bots must budget their request allocation across categories to avoid starving critical paths.

### Budget Framework

Assuming a total budget of **60 requests/second** (actual limit may vary — monitor 429 responses):

| Category | Allocation | Requests/sec | Endpoints |
|---|---|---|---|
| **Market data** | 30% | 18 req/s | `/prices`, `/depth`, `/trades`, `/candlesticks`, `/asset-contexts` |
| **Account state** | 25% | 15 req/s | `/account_overviews`, `/account_positions`, `/open_orders` |
| **Order status** | 20% | 12 req/s | `/orders`, `/bulk_order_status` |
| **History** | 10% | 6 req/s | `/order_history`, `/trade_history`, `/funding_rate_history` |
| **Reserve** | 15% | 9 req/s | Emergency checks, one-off queries, retry headroom |

### Implementation: Token Bucket per Category

```python
from asyncio import Semaphore
from collections import defaultdict

class RateLimitBudget:
    def __init__(self, total_rps: float = 60.0):
        self._budgets = {
            "market_data": TokenBucket(rate=total_rps * 0.30),
            "account":     TokenBucket(rate=total_rps * 0.25),
            "order_status": TokenBucket(rate=total_rps * 0.20),
            "history":     TokenBucket(rate=total_rps * 0.10),
            "reserve":     TokenBucket(rate=total_rps * 0.15),
        }

    async def acquire(self, category: str):
        bucket = self._budgets.get(category, self._budgets["reserve"])
        await bucket.acquire()
```

```rust
pub struct RateLimitBudget {
    buckets: HashMap<&'static str, TokenBucket>,
}

impl RateLimitBudget {
    pub fn new(total_rps: f64) -> Self {
        let mut buckets = HashMap::new();
        buckets.insert("market_data", TokenBucket::new(total_rps * 0.30));
        buckets.insert("account", TokenBucket::new(total_rps * 0.25));
        buckets.insert("order_status", TokenBucket::new(total_rps * 0.20));
        buckets.insert("history", TokenBucket::new(total_rps * 0.10));
        buckets.insert("reserve", TokenBucket::new(total_rps * 0.15));
        Self { buckets }
    }

    pub async fn acquire(&self, category: &str) -> Result<(), DecibelError> {
        let bucket = self.buckets.get(category)
            .unwrap_or(self.buckets.get("reserve").unwrap());
        bucket.acquire().await
    }
}
```

### Dynamic Reallocation

During high-activity periods (e.g., mass cancellation after a liquidation scare), temporarily steal from lower-priority budgets:

```python
async def emergency_rebalance(self):
    self._budgets["order_status"].rate += self._budgets["history"].rate
    self._budgets["history"].rate = 0.0
```

### Polling Schedule Templates

Different bot types have different optimal polling patterns. These templates show which endpoints to poll and at what frequency, assuming WebSocket is the primary data feed and REST is supplementary.

#### Market Maker Polling Schedule

A market maker quotes on both sides and needs tight state reconciliation:

```python
MARKET_MAKER_SCHEDULE = {
    "account_positions":   {"interval_s": 5,   "category": "account",      "reason": "cross-check WS positions every tick"},
    "open_orders":         {"interval_s": 10,  "category": "account",      "reason": "detect phantom orders missed by WS"},
    "account_overviews":   {"interval_s": 30,  "category": "account",      "reason": "margin usage and fee tier"},
    "bulk_orders":         {"interval_s": 15,  "category": "order_status", "reason": "verify bulk order state matches expectations"},
    "bulk_order_status":   {"interval_s": 0,   "category": "order_status", "reason": "on-demand after each bulk submission"},
    "markets":             {"interval_s": 300, "category": "reserve",      "reason": "market config changes are rare"},
    "depth":               {"interval_s": 0,   "category": "market_data",  "reason": "only on WS reconnect to re-init orderbook"},
}
```

#### Directional Bot Polling Schedule

A directional/momentum bot places fewer orders but cares deeply about position accuracy:

```python
DIRECTIONAL_SCHEDULE = {
    "account_positions":   {"interval_s": 10,  "category": "account",      "reason": "confirm position after each trade"},
    "open_orders":         {"interval_s": 30,  "category": "account",      "reason": "fewer resting orders to reconcile"},
    "account_overviews":   {"interval_s": 60,  "category": "account",      "reason": "track equity curve"},
    "orders":              {"interval_s": 0,   "category": "order_status", "reason": "on-demand: poll after submission if WS late"},
    "prices":              {"interval_s": 0,   "category": "market_data",  "reason": "only when WS price stale > 5s"},
    "asset-contexts":      {"interval_s": 300, "category": "market_data",  "reason": "market scanning for opportunities"},
    "candlesticks":        {"interval_s": 60,  "category": "market_data",  "reason": "update signal inputs"},
}
```

#### Risk Monitor Polling Schedule

A risk monitor reads state across multiple subaccounts without placing orders:

```python
RISK_MONITOR_SCHEDULE = {
    "account_positions":   {"interval_s": 5,   "category": "account",      "reason": "aggregate exposure across subaccounts"},
    "account_overviews":   {"interval_s": 10,  "category": "account",      "reason": "detect margin pressure on any subaccount"},
    "open_orders":         {"interval_s": 30,  "category": "account",      "reason": "total order exposure"},
    "prices":              {"interval_s": 5,   "category": "market_data",  "reason": "compute liquidation distances"},
    "active_twaps":        {"interval_s": 60,  "category": "account",      "reason": "track TWAP exposure"},
}
```

### Staying Under the Limit: Practical Patterns

**Pattern 1: Stagger periodic polls.** Do not fire all 30s polls at the same second. Offset each endpoint by a few seconds:

```python
class StaggeredPoller:
    def __init__(self, schedule: dict, client):
        self._tasks = []
        offset = 0.0
        for endpoint, config in schedule.items():
            if config["interval_s"] > 0:
                self._tasks.append(asyncio.create_task(
                    self._poll_loop(endpoint, config, initial_delay=offset)
                ))
                offset += 1.0  # stagger by 1s

    async def _poll_loop(self, endpoint: str, config: dict, initial_delay: float):
        await asyncio.sleep(initial_delay)
        while True:
            await self._rate_budget.acquire(config["category"])
            try:
                await self._fetch(endpoint)
            except RateLimitError:
                await asyncio.sleep(5.0)  # back off aggressively
            await asyncio.sleep(config["interval_s"])
```

**Pattern 2: Batch correlated requests.** When you need positions AND open orders for reconciliation, fetch both in parallel within a single reconciliation cycle rather than on independent timers:

```python
async def reconcile_cycle(self, subaccount: str):
    await self._rate_budget.acquire("account")
    positions, orders = await asyncio.gather(
        self._client.get_positions(account=subaccount),
        self._client.get_open_orders(account=subaccount),
    )
    self._position_state.reconcile(positions)
    self._order_state.reconcile(orders)
```

**Pattern 3: Conditional polling.** Only poll an endpoint if there's reason to suspect drift:

```python
async def maybe_poll_positions(self, subaccount: str):
    if self._freshness.is_ws_stale("account_positions:" + subaccount, threshold_ms=10_000):
        return await self._client.get_positions(account=subaccount)
    return None  # WS data is fresh, skip the poll
```

---

## Stale Data Detection

When running both REST polling and WebSocket streams, bots must detect when REST data falls behind WebSocket data (or vice versa).

### Timestamp Comparison Protocol

Every REST response and WebSocket message includes a timestamp. The SDK tracks the latest timestamp seen from each source:

```python
class FreshnessTracker:
    def __init__(self, max_drift_ms: int = 5000):
        self._max_drift_ms = max_drift_ms
        self._ws_timestamps: dict[str, int] = {}    # topic -> last_update_ms
        self._rest_timestamps: dict[str, int] = {}   # endpoint -> last_fetch_ms

    def record_ws(self, topic: str, timestamp_ms: int):
        self._ws_timestamps[topic] = timestamp_ms

    def record_rest(self, endpoint: str, timestamp_ms: int):
        self._rest_timestamps[endpoint] = timestamp_ms

    def is_rest_stale(self, endpoint: str, ws_topic: str) -> bool:
        rest_ts = self._rest_timestamps.get(endpoint, 0)
        ws_ts = self._ws_timestamps.get(ws_topic, 0)
        return ws_ts - rest_ts > self._max_drift_ms

    def is_ws_stale(self, topic: str, threshold_ms: int = 10000) -> bool:
        last_ts = self._ws_timestamps.get(topic, 0)
        now = int(time.time() * 1000)
        return now - last_ts > threshold_ms
```

### When to Trigger REST Fallback

| Condition | Action |
|---|---|
| No WS price update for > 5s on an active market | Poll `GET /prices/{market}` immediately |
| WS position data older than REST data by > 2s | Use REST data, log warning |
| WS reconnecting | Switch all reads to REST polling until WS stabilizes |
| REST returns 5xx for > 3 consecutive attempts | Use cached WS data, escalate to error handler |

### Bot-Level Freshness Check Before Trading

```python
async def ensure_fresh_state(client, tracker, market: str, subaccount: str):
    if tracker.is_ws_stale(f"market_price:{market}", threshold_ms=3000):
        prices = await client.get_price(market)
        tracker.record_rest(f"/prices/{market}", prices[0].timestamp_ms)
        return prices[0]
    return client.latest_prices.get(market)
```

---

## State Reconciliation: REST as the Source of Truth After WebSocket Gaps

WebSocket provides real-time streaming, but it offers no delivery guarantees. Messages can be lost during network blips, reconnections, or server-side load shedding. REST is the authoritative source for reconciling state after any gap.

### When to Reconcile

| Trigger | What to reconcile | REST endpoints |
|---|---|---|
| WS reconnect completed | Everything | positions, open_orders, account_overviews, depth (per tracked market) |
| WS gap detected on `order_updates` | Order state | `GET /open_orders` |
| WS gap detected on `account_positions` | Position state | `GET /account_positions` |
| WS gap detected on `depth` | Orderbook | `GET /depth/{market}` (full snapshot re-init) |
| After order submission with no WS confirmation within 3s | Single order | `GET /orders?order_id=...` |
| Periodic safety net (every 30–60s) | Positions + orders | positions, open_orders |

### Full Reconciliation Protocol

After a WS reconnect or when multiple topics are suspect, run a full reconciliation:

```python
async def full_reconcile(
    self,
    client: DecibelClient,
    subaccount: str,
    tracked_markets: list[str],
):
    """Reconcile all bot state against REST after a WS gap.

    This replaces local state wholesale — do not merge, replace.
    """
    positions, orders, overview = await asyncio.gather(
        client.get_positions(account=subaccount),
        client.get_open_orders(account=subaccount),
        client.get_account_overview(account=subaccount),
    )

    self._position_state.replace_all(positions)

    local_order_ids = set(self._order_state.all_order_ids())
    rest_order_ids = {o.order_id for o in orders}
    phantom_local = local_order_ids - rest_order_ids
    if phantom_local:
        logger.warning(f"Orders in local state but not on exchange: {phantom_local}")
        for oid in phantom_local:
            self._order_state.mark_terminal(oid, reason="reconciliation_removed")
    missing_local = rest_order_ids - local_order_ids
    if missing_local:
        logger.warning(f"Orders on exchange but not in local state: {missing_local}")
    self._order_state.replace_all(orders)

    self._account_state.update(overview)

    depth_tasks = [
        client.get_depth(market, limit=50) for market in tracked_markets
    ]
    depth_snapshots = await asyncio.gather(*depth_tasks, return_exceptions=True)
    for market, snapshot in zip(tracked_markets, depth_snapshots):
        if isinstance(snapshot, Exception):
            logger.error(f"Failed to re-sync depth for {market}: {snapshot}")
            continue
        self._orderbooks[market].apply_snapshot(snapshot)

    self._freshness.mark_all_fresh()
    logger.info("Full reconciliation complete")
```

### Single-Order Reconciliation

When a specific order submission has no WS confirmation:

```python
async def reconcile_single_order(
    self,
    client: DecibelClient,
    order_id: str,
    market_address: str,
    user_address: str,
    timeout_ms: int = 5000,
):
    """Poll REST for a single order's status after WS confirmation timeout."""
    start = time.monotonic()
    interval = 0.5
    while (time.monotonic() - start) * 1000 < timeout_ms:
        try:
            status = await client.get_order_status(
                order_id=order_id,
                market_address=market_address,
                user_address=user_address,
            )
            return status
        except ApiError as e:
            if e.status_code == 404:
                await asyncio.sleep(interval)
                interval = min(interval * 1.5, 2.0)
                continue
            raise
    return None  # order not found within timeout
```

### Reconciliation Safety Rules

1. **Never merge — always replace.** When reconciling, replace local state with REST state. Merging creates risk of stale entries persisting.
2. **Log discrepancies.** Every difference between local and REST state is a signal that something was missed. Log at WARNING level with order IDs and position sizes.
3. **Halt trading during reconciliation.** Between marking state as STALE and completing reconciliation, do not place new orders. An order placed against stale state could double an existing position.
4. **Reconciliation is idempotent.** If reconciliation fails midway (e.g., one REST call errors), it is safe to retry the entire sequence.

---

## Endpoint Priority for Bots

Not all endpoints are equally important. This table ranks them by how often a typical trading bot should call them:

### Tier 1: Continuous (every loop iteration or on-demand)

| Endpoint | Poll Frequency | Purpose |
|---|---|---|
| `GET /prices/{market}` | Fallback only (use WS) | Price data — should come from WebSocket |
| `GET /orders?order_id=...` | After every order submission | Confirm order status when WS confirmation is late |
| `GET /account_positions` | Every 5–10s as safety check | Cross-check WS position state |

### Tier 2: Periodic (every 30s–5min)

| Endpoint | Poll Frequency | Purpose |
|---|---|---|
| `GET /account_overviews` | Every 30s | Monitor equity, margin usage, fee tier changes |
| `GET /open_orders` | Every 60s | Reconcile resting orders — catch any missed cancellations |
| `GET /depth/{market}` | Fallback only (use WS) | Orderbook snapshot for WS re-sync |
| `GET /bulk_orders` | Every 60s (market makers) | Verify bulk order state |
| `GET /active_twaps` | Every 60s (TWAP agents) | Monitor TWAP progress |

### Tier 3: Infrequent (startup, daily, or on-demand)

| Endpoint | Poll Frequency | Purpose |
|---|---|---|
| `GET /markets` | Startup + every 5min | Market config rarely changes |
| `GET /asset-contexts` | Every 5min | 24h stats for market scanning |
| `GET /candlesticks/{market}` | On strategy signal | Historical data for analysis |
| `GET /trade_history` | Daily or on-demand | P&L reconciliation |
| `GET /funding_rate_history` | Daily or on-demand | Funding cost accounting |
| `GET /subaccounts` | Startup only | Enumerate subaccounts |

---

## Endpoint Matrix by Bot Type

Different bot archetypes need different subsets of the REST API. This matrix maps every endpoint to whether each bot type needs it, and how.

### Legend

- **CRITICAL** — Bot cannot function without this endpoint. Fetch on startup and poll/fallback continuously.
- **IMPORTANT** — Significantly improves bot quality. Fetch on startup and periodically.
- **USEFUL** — Nice to have. Fetch on-demand or in background.
- **UNUSED** — This bot type does not need this endpoint.

### Market Data Endpoints

| Endpoint | Market Maker | Directional Bot | Risk Monitor | TWAP Agent |
|---|---|---|---|---|
| `GET /markets` | CRITICAL (tick/lot sizes for order formatting) | CRITICAL (same) | IMPORTANT (market metadata) | CRITICAL (same) |
| `GET /prices` | CRITICAL (fallback pricing) | CRITICAL (signal input) | CRITICAL (mark-to-market) | IMPORTANT (slice pricing) |
| `GET /depth/{market}` | CRITICAL (orderbook init, WS re-sync) | USEFUL (market impact check) | USEFUL (liquidity monitoring) | UNUSED |
| `GET /trades/{market}` | USEFUL (flow toxicity analysis) | USEFUL (momentum confirmation) | UNUSED | UNUSED |
| `GET /candlesticks/{market}` | USEFUL (volatility estimation) | CRITICAL (signal computation) | UNUSED | UNUSED |
| `GET /asset-contexts` | IMPORTANT (volume/OI for market selection) | IMPORTANT (market scanning) | IMPORTANT (OI monitoring) | UNUSED |

### Account Endpoints

| Endpoint | Market Maker | Directional Bot | Risk Monitor | TWAP Agent |
|---|---|---|---|---|
| `GET /account_overviews` | CRITICAL (margin, fee tier) | CRITICAL (margin, equity) | CRITICAL (aggregate risk) | IMPORTANT (margin check) |
| `GET /account_positions` | CRITICAL (inventory tracking) | CRITICAL (position management) | CRITICAL (exposure monitoring) | IMPORTANT (progress tracking) |
| `GET /open_orders` | CRITICAL (reconcile resting quotes) | IMPORTANT (verify orders) | IMPORTANT (order exposure) | IMPORTANT (verify slices) |
| `GET /subaccounts` | IMPORTANT (startup enumeration) | USEFUL (startup) | CRITICAL (enumerate all accounts) | USEFUL (startup) |
| `GET /delegations` | USEFUL | UNUSED | IMPORTANT (delegation audit) | UNUSED |

### Order Endpoints

| Endpoint | Market Maker | Directional Bot | Risk Monitor | TWAP Agent |
|---|---|---|---|---|
| `GET /orders` | CRITICAL (confirm order status) | CRITICAL (confirm fills) | UNUSED | IMPORTANT (confirm slices) |
| `GET /bulk_orders` | CRITICAL (verify bulk state) | UNUSED | USEFUL (monitor MM activity) | UNUSED |
| `GET /bulk_order_status` | CRITICAL (post-submission check) | UNUSED | UNUSED | UNUSED |
| `GET /bulk_order_fills` | CRITICAL (fill tracking) | UNUSED | UNUSED | UNUSED |
| `GET /active_twaps` | UNUSED | USEFUL (avoid conflicts) | IMPORTANT (exposure tracking) | CRITICAL (dedup check) |

### History Endpoints

| Endpoint | Market Maker | Directional Bot | Risk Monitor | TWAP Agent |
|---|---|---|---|---|
| `GET /order_history` | USEFUL (daily reconciliation) | IMPORTANT (P&L tracking) | USEFUL (audit trail) | USEFUL (slice history) |
| `GET /trade_history` | IMPORTANT (fill + fee accounting) | IMPORTANT (P&L calculation) | USEFUL (audit) | USEFUL |
| `GET /funding_rate_history` | IMPORTANT (funding cost analysis) | IMPORTANT (carry cost) | CRITICAL (funding exposure) | UNUSED |

### Typical Request Counts per Bot Type

Estimated steady-state requests/second assuming 5 actively-traded markets:

| Bot Type | Market Data | Account | Orders | History | Total |
|---|---|---|---|---|---|
| Market Maker | 3 req/s | 4 req/s | 5 req/s | 0.1 req/s | ~12 req/s |
| Directional Bot | 1 req/s | 1 req/s | 0.5 req/s | 0.05 req/s | ~3 req/s |
| Risk Monitor | 2 req/s | 5 req/s | 0 req/s | 0.02 req/s | ~7 req/s |
| TWAP Agent | 0.5 req/s | 1 req/s | 0.5 req/s | 0 req/s | ~2 req/s |

These counts assume WebSocket is handling real-time data. A bot relying solely on REST for pricing would consume 10–20x more requests.

---

## Endpoint Catalog

### Market Data Endpoints

#### GET /markets

List all available perpetual futures markets.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters |

**Response**: `Vec<PerpMarketConfig>`

**Bot Usage**: Fetch once at startup, cache with 5min TTL. Use to resolve market names to addresses and to get formatting parameters (`tick_size`, `lot_size`, `min_size`, `px_decimals`, `sz_decimals`). Without this data, the bot cannot format prices or sizes for on-chain transactions.

**Critical fields for bots**:
- `tick_size` — minimum price increment; orders at non-tick prices are rejected
- `lot_size` — minimum size increment; orders at non-lot sizes are rejected
- `min_size` — absolute minimum order size
- `market_address` — needed for WS subscriptions and order status queries
- `px_decimals` / `sz_decimals` — for chain unit conversion

---

#### GET /markets/{name}

Get a specific market by name.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | path | YES | Market name (e.g., `"BTC-USD"`) |

**Response**: `PerpMarketConfig`

---

#### GET /prices

Get current prices for all markets.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `market` | query | NO | Filter by market name or `"all"` |

**Response**: `Vec<MarketPrice>`

**Bot Usage**: On startup, fetch with `market=all` to get baseline prices for all markets. After startup, rely on WS `all_market_prices` or per-market `market_price:{addr}` topics. Only poll this endpoint as a fallback when WS data is stale.

**Key fields**:
- `mark_px` — the reference price for PnL and liquidation calculations (median of oracle, mid, basis)
- `index_px` — oracle price, important for funding rate direction
- `best_bid` / `best_ask` — top-of-book, used for aggressive pricing
- `funding_rate_bps` — current funding rate in basis points per hour; continuous accrual means this compounds ~every second

---

#### GET /prices/{marketName}

Get price for a specific market.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |

**Response**: `Vec<MarketPrice>`

---

#### GET /depth/{marketName}

Get orderbook depth snapshot.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `limit` | query | NO | Number of levels per side |

**Response**: `MarketDepth`

**Bot Usage**: Fetch a full depth snapshot on startup or after a WS reconnect to initialize local orderbook state. Then maintain incrementally via `depth:{marketAddr}` WS topic. Also useful for computing market impact before large orders.

---

#### GET /trades/{marketName}

Get recent market trades.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `limit` | query | NO | Number of trades |

**Response**: `Vec<MarketTrade>`

---

#### GET /candlesticks/{marketName}

Get OHLCV candlestick data.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `interval` | query | YES | Candle interval (`1m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `1d`, `1w`, `1mo`) |
| `startTime` | query | YES | Start timestamp (Unix ms) |
| `endTime` | query | YES | End timestamp (Unix ms) |

**Response**: `Vec<Candlestick>`

**Limits**: Maximum 1000 candles per request. Missing intervals are interpolated using last known close price.

**Bot Usage**: Fetch historical candles on startup for signal computation (e.g., moving averages, volatility estimation). For a 200-period 1h moving average, request the last 200 hours: `interval=1h&startTime={now - 200*3600*1000}&endTime={now}`. Subscribe to `market_candlestick:{addr}:1h` via WS for ongoing updates.

---

#### GET /asset-contexts

Get extended market context with 24h statistics.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters |

**Response**: `Vec<MarketContext>`

**Bot Usage**: Provides 24h volume, open interest, price change percentage — useful for multi-market scanners that rank markets by activity. Poll every 5 minutes.

---

### Account Endpoints

#### GET /account_overviews

Get account overview including equity, margin, and performance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |
| `volume_window` | query | NO | Volume window (`7d`, `14d`, `30d`, `90d`) |
| `include_performance` | query | NO | Include performance metrics (`true`/`false`) |

**Response**: `AccountOverview`

**Bot Usage**: Critical for risk management. Key fields:
- `account_equity` — total account value after unrealized PnL
- `cross_margin_usage` — fraction of equity used as margin
- `available_margin` — how much more exposure the bot can take
- `fee_tier` — current fee tier based on rolling volume (affects profitability calculation)
- `volume_30d` — rolling volume, determines fee tier (Tier 0: <$250M = 3.40bps taker / 1.10bps maker; up to Tier 7: >$15B = 1.80bps / 0bps)

---

#### GET /account_positions

Get open positions for an account.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |
| `market` | query | NO | Filter by market address |
| `limit` | query | NO | Number of positions |

**Response**: `Vec<UserPosition>`

**Bot Usage**: Fetch on startup (Phase 1) and periodically as a safety cross-check against WS state. Key fields per position:
- `size` — signed position size (positive = long, negative = short)
- `entry_price` — volume-weighted average entry
- `unrealized_pnl` — current unrealized PnL based on mark price
- `margin_used` — margin allocated to this position under cross-margin
- `liquidation_price` — estimated liquidation price (depends on total account state under cross margin)
- `accrued_funding` — cumulative funding payments received/paid

---

#### GET /open_orders

Get currently open orders.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |

**Response**: `Vec<UserOpenOrder>`

**Bot Usage**: Reconciliation endpoint. On startup, fetch all open orders to avoid placing duplicates. Periodically (every 60s) cross-check against local order tracking state. If an order appears here but not in local state, the bot missed a fill/cancel event.

---

#### GET /subaccounts

Get all subaccounts for an owner.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `owner` | query | YES | Owner address |

**Response**: `Vec<UserSubaccount>`

---

#### GET /delegations

Get active delegations for a subaccount.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |

**Response**: `Vec<Delegation>`

---

### History Endpoints (Paginated)

All history endpoints support the following common query parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | query | NO | `10` | Items per page (max 200) |
| `offset` | query | NO | `0` | Pagination offset |
| `sort_by` | query | NO | `transaction_unix_ms` | Sort key |
| `sort_dir` | query | NO | `DESC` | Sort direction |

#### GET /order_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `order_type` | query | NO |
| `status` | query | NO |
| `side` | query | NO |
| `is_reduce_only` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserOrderHistoryItem>`

---

#### GET /trade_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `order_id` | query | NO |
| `side` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserTradeHistoryItem>`

**Bot Usage**: Use for end-of-session P&L reconciliation. Filter by `start_time` and `end_time` to get fills for a specific trading period. Each fill includes `fee_amount` — aggregate these for accurate fee accounting.

---

#### GET /funding_rate_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `side` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserFundingHistoryItem>`

**Bot Usage**: Decibel's continuous funding accrues every oracle update (~1 second). Over a 24h period, a position may have thousands of micro-accruals. This endpoint aggregates them. Use for funding cost analysis — a long position in a market with +10bps/hr funding rate costs ~24bps/day, which can dominate strategy P&L.

---

#### GET /account_fund_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserFundHistoryItem>`

---

### TWAP Endpoints

#### GET /active_twaps

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |

**Response**: `Vec<UserActiveTwap>`

**Bot Usage**: Check on startup to avoid duplicate TWAP submissions. Monitor progress: each TWAP includes `filled_size`, `remaining_size`, and `estimated_completion_time`.

---

#### GET /twap_history

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `limit` | query | NO |
| `offset` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserActiveTwap>`

---

### Bulk Order Endpoints

#### GET /bulk_orders

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |

**Response**: Bulk orders response

**Bot Usage**: For market makers using `place_bulk_order`. Bulk orders atomically replace all quotes on one side (up to 30 levels per side). This endpoint returns the current state of all active bulk orders — prices, sizes, and sequence numbers. Use to verify that the latest bulk order submission was applied correctly.

---

#### GET /bulk_order_status

| Parameter | Type | Required |
|---|---|---|
| `sequence_number` | query | YES |

**Response**: Bulk order status

**Bot Usage**: Poll this after submitting a bulk order to confirm it was accepted. The `sequence_number` is returned by the `place_bulk_order` transaction. If the status shows rejection, check the rejection reason — common causes are: all orders crossed the spread (PostOnly violation), invalid price/size formatting, or exceeding the 30-level-per-side limit.

---

#### GET /bulk_order_fills

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `sequence_number` | query | NO |

**Response**: Bulk order fills

**Bot Usage**: Track which levels of a bulk order have been filled. Market makers use this to adjust inventory tracking and skew future quotes based on which side is being hit.

---

### Vault Endpoints

#### GET /vaults

| Parameter | Type | Required | Description |
|---|---|---|---|
| `limit` | query | NO | Page size |
| `offset` | query | NO | Offset |
| `sort_key` | query | NO | Sort field |
| `sort_dir` | query | NO | Sort direction |
| `search` | query | NO | Search term |
| `vault_type` | query | NO | `"user"` or `"protocol"` |
| `vault_address` | query | NO | Exact vault address |
| `status` | query | NO | Vault status filter |

**Response**: `PaginatedResponse<Vault>`

---

#### GET /account_owned_vaults

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `limit` | query | NO |
| `offset` | query | NO |

**Response**: `PaginatedResponse<UserOwnedVault>`

---

#### GET /account_vault_performance

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |

**Response**: Vault performance data

---

### Analytics Endpoints

#### GET /leaderboard

| Parameter | Type | Required |
|---|---|---|
| `limit` | query | NO |
| `offset` | query | NO |
| `sort_key` | query | NO |
| `sort_dir` | query | NO |
| `search_term` | query | NO |

**Response**: `PaginatedResponse<LeaderboardItem>`

---

#### GET /portfolio_chart

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `interval` | query | NO |

**Response**: `Vec<PortfolioChartPoint>`

---

### Order Status Endpoint

#### GET /orders

| Parameter | Type | Required | Description |
|---|---|---|---|
| `order_id` | query | YES | Order ID |
| `market_address` | query | YES | Market address |
| `user_address` | query | YES | User address |

**Response**: `OrderStatus`

**Bot Usage**: The most latency-sensitive REST endpoint for bots. After submitting an order transaction, if the WS `order_updates` confirmation doesn't arrive within 2 seconds, poll this endpoint directly. Include this in the "order status" rate limit budget (20% allocation). The response includes `status`, `filled_size`, `remaining_size`, and `average_fill_price`.

---

## Caching Strategy

The SDK MUST implement these caching behaviors:

| Data | Cache Strategy | TTL | Invalidation |
|---|---|---|---|
| Market configs | Cache after first fetch | 5 minutes | Manual refresh or TTL expiry |
| USDC decimals | Cache forever | ∞ | Immutable value |
| Prices | No cache (real-time) | — | Use WebSocket for streaming |
| Positions | No cache | — | Use WebSocket for streaming |
| Orders | No cache | — | Use WebSocket for streaming |

### Bot-Specific Caching Rules

Trading bots have different caching needs than a UI client. The core principle: **cache configuration, never cache state**.

| Data Category | Cache? | Rationale |
|---|---|---|
| Market configs (`tick_size`, `lot_size`, `min_size`, `decimals`) | **YES — aggressively** (5min TTL) | These change only when the exchange adds/modifies a market. Fetching this per-order wastes rate limit budget. |
| Market addresses | **YES — aggressively** (5min TTL, same lifecycle as market configs) | Derived from market config. Cache alongside it. |
| Fee tier schedule | **YES** (5min TTL) | Fee tiers change rarely. The bot's own tier may change with volume, but the tier schedule itself is static. |
| USDC decimals / chain constants | **YES — forever** | Immutable on-chain values. |
| Prices (mark, index, bid, ask) | **NEVER cache** | Stale prices lead to mispriced orders. Always use the latest WS value or a fresh REST fetch. |
| Positions | **NEVER cache** | A cached position size can cause the bot to double-enter or miss an exit. |
| Open orders | **NEVER cache** | Caching open orders means the bot doesn't know about fills or cancels. |
| Account overview (equity, margin) | **NEVER cache** | Margin calculations with stale equity can cause over-leverage. |
| Orderbook depth | **NEVER cache** | The orderbook changes every few hundred milliseconds. Any cached depth is immediately stale. |
| Candlestick history | **YES** (short TTL, 30s–60s) | Historical candles don't change. Only the latest candle updates. Cache closed candles indefinitely; re-fetch the open candle periodically. |
| Asset contexts (24h stats) | **YES** (5min TTL) | 24h volume and OI change slowly. Useful for market scanning without burning rate limit. |

### Cache Miss Behavior

On a cache miss, the SDK fetches data from the API and populates the cache before returning. This means the first call to any cached endpoint is async (network I/O), but subsequent calls within the TTL window return immediately from memory.

```python
async def get_market_config(self, market_name: str) -> PerpMarketConfig:
    cached = self._cache.get(f"market:{market_name}")
    if cached and not cached.expired:
        return cached.value
    markets = await self._http.get("/markets")
    for m in markets:
        self._cache.set(f"market:{m.market_name}", m, ttl_s=300)
    return self._cache.get(f"market:{market_name}").value
```

### Cache Implementation for Bots

```python
class BotCache:
    """Simple TTL cache for bot-safe data categories only.

    Only stores data that is safe to cache (configs, constants, historical data).
    Real-time data (prices, positions, orders) MUST NOT pass through this cache.
    """
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_s: float):
        self._store[key] = (value, time.monotonic() + ttl_s)

    def set_permanent(self, key: str, value: Any):
        self._store[key] = (value, float('inf'))

    def invalidate_prefix(self, prefix: str):
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._store[k]
```

### Forced Cache Refresh

Bots should expose a way to force-refresh cached data, needed after exchange maintenance or market parameter changes:

```python
async def refresh_market_configs(self):
    """Force-refresh all cached market configs. Call after exchange maintenance."""
    self._cache.invalidate_prefix("market:")
    markets = await self._http.get("/markets")
    for m in markets:
        self._cache.set(f"market:{m.market_name}", m, ttl_s=300)
    logger.info(f"Refreshed {len(markets)} market configs")
```

---

## Rate Limiting

The SDK MUST handle rate limiting gracefully:

1. Detect `429` responses.
2. Parse `Retry-After` header if present.
3. Return `RateLimitError` with `retry_after_ms`.
4. Optionally implement automatic retry with backoff (configurable).

### Proactive Rate Limit Avoidance

Rather than hitting 429s and reacting, the SDK should proactively throttle using the token bucket system described above. The `RateLimitBudget` prevents bursts from exhausting the rate limit before critical requests can be served.

```python
async def _request(self, method: str, path: str, category: str, **kwargs):
    await self._rate_budget.acquire(category)
    try:
        return await self._http.request(method, path, **kwargs)
    except RateLimitError as e:
        self._rate_budget.penalize(category, penalty_ms=e.retry_after_ms)
        raise
```

---

## Parallel Request Batching

The SDK provides a convenience method for issuing multiple REST requests in parallel, useful for bots that need to gather state from several endpoints atomically:

```python
async def batch_fetch(self, requests: list[tuple[str, dict]]) -> list:
    tasks = [self._http.get(path, params=params) for path, params in requests]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

```rust
pub async fn batch_fetch<T: DeserializeOwned>(
    &self,
    requests: Vec<(&str, Vec<(&str, &str)>)>,
) -> Vec<Result<T, DecibelError>> {
    let futures = requests.into_iter()
        .map(|(path, params)| self.get::<T>(path, &params));
    futures::future::join_all(futures).await
}
```

---

## Query Parameter Construction

The SDK provides a utility to build query strings from typed parameters:

```python
def build_query_params(
    page: PageParams | None = None,
    sort: SortParams | None = None,
    search: str | None = None,
    **kwargs: Any,
) -> dict[str, str]:
    """Build URL query parameters from typed inputs.

    Omits None values. Converts enums to their wire values.
    """
    ...
```

```rust
fn build_query_params(
    page: Option<&PageParams>,
    sort: Option<&SortParams>,
    search: Option<&str>,
    extra: &[(&str, &str)],
) -> Vec<(String, String)> {
    // Omits None values. Converts enums to wire values.
    ...
}
```
