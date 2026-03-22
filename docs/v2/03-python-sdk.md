# Python SDK Specification

**Parent**: [00-overview.md](./00-overview.md)  
**Language**: Python 3.11+  
**Package**: `decibel-sdk`  
**Primary audience**: Trading bots, AI/ML agents, strategy prototyping

---

## Philosophy

The Python SDK exists for **automated trading systems** — market makers, directional agents, multi-strategy engines, and AI/ML pipelines that trade perpetual futures. It is not a thin REST wrapper. It provides:

1. **PositionStateManager** — a local state aggregator that fuses WebSocket streams into a single coherent snapshot your bot reads synchronously, never awaiting mid-loop.
2. **BulkOrderManager** — per-market quoting engine with automatic sequence numbers, atomic quote replacement, and fill tracking for market making.
3. **Order lifecycle tracking** — place returns `order_id` immediately; `client_order_id` survives restarts; in-session tracking without polling.
4. **Risk monitoring** — liquidation distance, margin warnings, funding accrual, TP/SL presence checks — all computed locally from cached state.
5. **Reconnection with gap detection** — WS drops are invisible to your strategy; the SDK re-subscribes, REST-syncs missed state, and flags gaps.
6. **Human-readable prices by default** — pass `45000.0` and `0.25`; the SDK converts to chain units using cached `PerpMarketConfig`. Raw mode available.
7. **Async-first with Pydantic v2** — every model validates, serializes, and exports JSON Schema. Every I/O call is `async`. No hidden synchronous traps.

---

## Package Structure

```
decibel/
├── __init__.py              # Re-exports: DecibelClient, managers, config presets
├── client.py                # DecibelClient (unified entry point)
├── config.py                # DecibelConfig, Deployment, presets
├── models/
│   ├── __init__.py
│   ├── market.py            # PerpMarketConfig, MarketPrice, MarketContext, MarketDepth
│   ├── account.py           # AccountOverview, UserPosition, UserSubaccount
│   ├── order.py             # UserOpenOrder, OrderStatus, PlaceOrderResult
│   ├── trade.py             # UserTradeHistoryItem, UserFundingHistoryItem
│   ├── vault.py             # Vault, UserOwnedVault
│   ├── risk.py              # LiquidationEstimate, MarginWarning, FundingAccrual
│   ├── ws.py                # WebSocket message wrappers
│   ├── pagination.py        # PageParams, SortParams, PaginatedResponse
│   └── enums.py             # All enumerations
├── state/
│   ├── __init__.py
│   ├── position_manager.py  # PositionStateManager
│   ├── order_tracker.py     # OrderLifecycleTracker
│   └── risk_monitor.py      # RiskMonitor
├── bulk/
│   ├── __init__.py
│   └── order_manager.py     # BulkOrderManager (per-market quoting)
├── read/
│   ├── __init__.py
│   ├── client.py            # DecibelReadClient
│   ├── markets.py           # Market data reader methods
│   ├── account.py           # Account data reader methods
│   └── history.py           # Historical data reader methods
├── write/
│   ├── __init__.py
│   ├── client.py            # DecibelWriteClient
│   ├── orders.py            # Order placement, cancellation
│   ├── positions.py         # TP/SL management
│   ├── accounts.py          # Subaccount management, delegation
│   └── bulk.py              # Bulk order submission
├── ws/
│   ├── __init__.py
│   ├── manager.py           # WebSocketManager (reconnection, subscription restore)
│   └── topics.py            # Topic string builders and parsing
├── tx/
│   ├── __init__.py
│   ├── builder.py           # TransactionBuilder
│   ├── signer.py            # Ed25519 signing
│   └── gas.py               # GasPriceManager
├── utils/
│   ├── __init__.py
│   ├── address.py           # Address derivation (market, subaccount, vault share)
│   ├── formatting.py        # Human ↔ chain unit conversion, tick/lot rounding
│   └── nonce.py             # Replay protection nonce generation
└── errors.py                # All error types
```

---

## Entry Point: DecibelClient

```python
from decibel import DecibelClient, MAINNET_CONFIG

async with DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="your-bearer-token",
    private_key="0x...",  # Ed25519 hex — required for write operations
) as client:
    state = client.state          # PositionStateManager
    bulk = client.bulk("BTC-USD") # BulkOrderManager for a specific market
    risk = client.risk            # RiskMonitor
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `config` | `DecibelConfig` | YES | — | Network configuration (use `MAINNET_CONFIG` or `TESTNET_CONFIG`) |
| `bearer_token` | `str` | YES | — | Bearer token for REST/WS authentication |
| `private_key` | `str` | NO | `None` | Ed25519 private key hex for on-chain transactions |
| `subaccount_addrs` | `list[str]` | NO | `[]` | Subaccount addresses to subscribe to at startup |
| `markets` | `list[str]` | NO | `[]` | Market names to prefetch config for (e.g. `["BTC-USD", "ETH-USD"]`) |
| `node_api_key` | `str` | NO | `None` | Aptos node API key for higher rate limits |
| `skip_simulate` | `bool` | NO | `False` | Skip tx simulation before submission |
| `no_fee_payer` | `bool` | NO | `False` | Disable gas station |
| `gas_refresh_interval_s` | `float` | NO | `5.0` | Gas price cache TTL |
| `time_delta_ms` | `int` | NO | `0` | Clock drift compensation |
| `request_timeout_s` | `float` | NO | `10.0` | HTTP request timeout |
| `ws_ping_interval_s` | `float` | NO | `15.0` | WebSocket keepalive ping interval |
| `ws_reconnect_max_delay_s` | `float` | NO | `30.0` | Maximum backoff for WS reconnection |
| `on_event` | `Callable` | NO | `None` | Structured event hook for telemetry |

---

## Configuration

```python
from decibel.config import DecibelConfig, Deployment, MAINNET_CONFIG, TESTNET_CONFIG

config = MAINNET_CONFIG

# Or build custom
config = DecibelConfig(
    network="mainnet",
    fullnode_url="https://fullnode.mainnet.aptoslabs.com",
    trading_http_url="https://api.mainnet.aptoslabs.com/decibel",
    trading_ws_url="wss://api.mainnet.aptoslabs.com/decibel/ws",
    deployment=Deployment(
        package="0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06",
        usdc="0x...",
        testc="0x...",
        perp_engine_global="0x...",
    ),
    compat_version="v0.4",
)
```

### DecibelConfig (Pydantic Model)

```python
class DecibelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    network: Literal["mainnet", "testnet", "devnet", "custom"]
    fullnode_url: str
    trading_http_url: str
    trading_ws_url: str
    deployment: Deployment
    compat_version: str = "v0.4"
    gas_station_url: str | None = None
    gas_station_api_key: str | None = None
    chain_id: int | None = None
```

---

## PositionStateManager

The central piece for any bot. It aggregates three WebSocket streams — **positions**, **orders**, and **account overview** — into a single consistent snapshot that your strategy reads **synchronously** without awaiting. The manager is updated in the background via WS callbacks and REST re-sync on reconnection.

### How It Works

1. On `client.__aenter__`, the SDK subscribes to WS topics for every subaccount in `subaccount_addrs`.
2. Each incoming WS message is deserialized and merged into the manager's internal state.
3. Your strategy loop calls synchronous property accessors — no I/O, no await, no blocking.
4. If the WS drops and reconnects, the manager runs a REST snapshot to fill gaps before resuming WS updates.

### API

```python
class PositionStateManager:
    """Aggregates real-time account state from WebSocket streams.
    
    All read methods are synchronous — safe to call in a hot loop.
    All state is updated in the background by WS subscription handlers.
    """

    # ── Position queries ──────────────────────────────────────────

    def positions(self, subaccount: str) -> dict[str, UserPosition]:
        """All open positions for a subaccount, keyed by market name.
        Returns an empty dict if no positions exist."""

    def position(self, subaccount: str, market: str) -> UserPosition | None:
        """Single position for a subaccount in a specific market.
        Returns None if no position is open."""

    def has_position(self, subaccount: str, market: str) -> bool:
        """True if a position is open in this market."""

    def net_exposure_usd(self, subaccount: str) -> float:
        """Net USD exposure across all positions (long positive, short negative)."""

    def gross_exposure_usd(self, subaccount: str) -> float:
        """Gross USD exposure (sum of abs(notional) across all positions)."""

    # ── Order queries ─────────────────────────────────────────────

    def open_orders(self, subaccount: str) -> list[UserOpenOrder]:
        """All open orders across all markets."""

    def open_orders_by_market(self, subaccount: str, market: str) -> list[UserOpenOrder]:
        """Open orders for a specific market."""

    def order_by_id(self, order_id: str) -> UserOpenOrder | None:
        """Lookup a specific order by exchange order_id."""

    def order_by_client_id(self, client_order_id: str) -> UserOpenOrder | None:
        """Lookup a specific order by client_order_id."""

    # ── Account overview ──────────────────────────────────────────

    def overview(self, subaccount: str) -> AccountOverview | None:
        """Account overview: equity, margin, unrealized PnL, etc.
        Returns None if the overview hasn't been received yet."""

    def equity(self, subaccount: str) -> float:
        """Total account equity (collateral + unrealized PnL)."""

    def available_margin(self, subaccount: str) -> float:
        """Margin available for new positions."""

    def margin_usage_pct(self, subaccount: str) -> float:
        """Margin used as a percentage of total equity (0.0–1.0)."""

    # ── Market data ───────────────────────────────────────────────

    def price(self, market: str) -> MarketPrice | None:
        """Latest price snapshot for a market (if subscribed)."""

    def mark_price(self, market: str) -> float | None:
        """Shorthand for the mark price of a market."""

    def mid_price(self, market: str) -> float | None:
        """Shorthand for the mid price of a market."""

    def depth(self, market: str) -> MarketDepth | None:
        """Latest orderbook depth snapshot (if subscribed)."""

    # ── State metadata ────────────────────────────────────────────

    @property
    def last_update_ms(self) -> int:
        """Unix ms timestamp of the most recent state update from any stream."""

    @property
    def is_connected(self) -> bool:
        """True if the underlying WS connection is alive."""

    @property
    def gap_detected(self) -> bool:
        """True if a sequence gap was detected since last REST re-sync.
        Resets to False after successful re-sync."""

    def subscribe_market(self, market: str) -> None:
        """Add a market to the live subscription set (prices + depth)."""

    def subscribe_subaccount(self, subaccount: str) -> None:
        """Add a subaccount to the live subscription set (positions + orders + overview)."""
```

### Usage in a Strategy Loop

```python
async with DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token=token,
    private_key=pk,
    subaccount_addrs=[my_subaccount],
    markets=["BTC-USD", "ETH-USD"],
) as client:
    state = client.state

    while True:
        pos = state.position(my_subaccount, "BTC-USD")
        mid = state.mid_price("BTC-USD")
        equity = state.equity(my_subaccount)

        if mid is None:
            await asyncio.sleep(0.1)
            continue

        # strategy logic — entirely synchronous reads
        if pos is None and equity > 1000.0:
            await client.place_order(
                market_name="BTC-USD",
                price=mid - 10.0,
                size=0.01,
                is_buy=True,
            )

        await asyncio.sleep(1.0)
```

---

## BulkOrderManager

A per-market manager for **market-making bots** that need to maintain two-sided quotes with atomic replacement. Handles sequence number tracking, order batching, and fill accounting internally.

### How It Works

1. You obtain a `BulkOrderManager` via `client.bulk("BTC-USD")`.
2. Call `set_quotes()` with your desired bid/ask levels. The manager diffs against the current live orders and computes the minimal set of cancel/place operations.
3. The manager tracks a per-market **sequence number** that the exchange requires for bulk operations. On each `set_quotes()` call it auto-increments the sequence number.
4. Fills are tracked via the WS order-update stream. `filled_since_last_reset()` returns the net fill volume since you last called `reset_fill_tracker()`.

### API

```python
class BulkOrderManager:
    """Per-market quoting manager with atomic replacement and fill tracking.
    
    Obtained via client.bulk("MARKET-NAME"). One instance per market.
    """

    @property
    def market(self) -> str:
        """Market name this manager is bound to (e.g. 'BTC-USD')."""

    @property
    def sequence_number(self) -> int:
        """Current sequence number. Auto-incremented on each set_quotes() call."""

    @property
    def live_orders(self) -> list[UserOpenOrder]:
        """Orders currently live on the book, as tracked by this manager."""

    @property
    def live_bids(self) -> list[UserOpenOrder]:
        """Live bid orders, sorted by price descending."""

    @property
    def live_asks(self) -> list[UserOpenOrder]:
        """Live ask orders, sorted by price ascending."""

    # ── Quoting ───────────────────────────────────────────────────

    async def set_quotes(
        self,
        bids: list[tuple[float, float]],  # [(price, size), ...]
        asks: list[tuple[float, float]],
        *,
        time_in_force: TimeInForce = TimeInForce.PostOnly,
        subaccount: str | None = None,
    ) -> BulkQuoteResult:
        """Atomically replace all quotes for this market.
        
        Cancels stale orders and places new ones in a single bulk transaction.
        Sequence number is auto-incremented.
        
        Args:
            bids: List of (price, size) tuples for bid side.
            asks: List of (price, size) tuples for ask side.
            time_in_force: Order type for new quotes (default PostOnly).
            subaccount: Override subaccount (defaults to client primary).
        
        Returns:
            BulkQuoteResult with placed/cancelled counts and any errors.
        """

    async def cancel_all(self, *, subaccount: str | None = None) -> int:
        """Cancel all live orders for this market. Returns count cancelled."""

    # ── Fill tracking ─────────────────────────────────────────────

    def filled_since_last_reset(self) -> FillSummary:
        """Net fills since last reset_fill_tracker() call.
        
        Returns FillSummary with:
            bid_filled_size: float  — total size filled on bid side
            ask_filled_size: float  — total size filled on ask side
            net_size: float         — bid_filled - ask_filled (positive = net bought)
            avg_bid_price: float    — volume-weighted avg fill price on bids
            avg_ask_price: float    — volume-weighted avg fill price on asks
            fill_count: int         — total number of fill events
        """

    def reset_fill_tracker(self) -> FillSummary:
        """Reset the fill tracker and return the summary before reset."""

    # ── Diagnostics ───────────────────────────────────────────────

    def quote_age_ms(self) -> int | None:
        """Milliseconds since the last successful set_quotes() call.
        Returns None if no quotes have been set."""

    def is_quoting(self) -> bool:
        """True if there are live orders on both sides."""
```

### BulkQuoteResult / FillSummary

```python
class BulkQuoteResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    placed_count: int
    cancelled_count: int
    errors: list[str]
    sequence_number: int
    transaction_hash: str | None

class FillSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    bid_filled_size: float = 0.0
    ask_filled_size: float = 0.0
    net_size: float = 0.0
    avg_bid_price: float = 0.0
    avg_ask_price: float = 0.0
    fill_count: int = 0
```

### Market Making Example

```python
async with DecibelClient(...) as client:
    bulk = client.bulk("BTC-USD")
    state = client.state

    while True:
        mid = state.mid_price("BTC-USD")
        if mid is None:
            await asyncio.sleep(0.1)
            continue

        spread = 2.0  # $2 half-spread
        size = 0.01

        result = await bulk.set_quotes(
            bids=[(mid - spread, size), (mid - spread * 2, size * 2)],
            asks=[(mid + spread, size), (mid + spread * 2, size * 2)],
        )

        fills = bulk.filled_since_last_reset()
        if abs(fills.net_size) > 0.05:
            # inventory skewed — widen on the heavy side
            bulk.reset_fill_tracker()

        await asyncio.sleep(0.5)
```

---

## Order Lifecycle Tracking

Every order placed through the SDK is tracked in-session without polling.

### place_order Returns Immediately

```python
result: PlaceOrderResult = await client.place_order(
    market_name="BTC-USD",
    price=45_000.0,
    size=0.25,
    is_buy=True,
    time_in_force=TimeInForce.GoodTillCanceled,
    client_order_id="strat-a-1",
)

# result.order_id  — exchange-assigned ID, available immediately after ack
# result.success   — True if the order was accepted
# result.tx_hash   — on-chain transaction hash (if applicable)
```

### client_order_id Correlation Across Restarts

`client_order_id` is a string you set. It is stored on-chain and returned in all WS updates and REST queries for that order. Use it to correlate orders across bot restarts:

```python
# After a restart, find your orders by client_order_id
orders = await client.get_open_orders(my_subaccount)
my_orders = [o for o in orders if o.client_order_id.startswith("strat-a-")]
```

### In-Session Tracking via OrderLifecycleTracker

The `PositionStateManager` automatically feeds order updates from the WS stream into the `OrderLifecycleTracker`. You query it through the state manager:

```python
state = client.state

# By exchange order ID
order = state.order_by_id("12345")

# By client order ID
order = state.order_by_client_id("strat-a-1")

# All open orders for a market
orders = state.open_orders_by_market(my_subaccount, "BTC-USD")
```

Order states flow through: `Pending → Acknowledged → PartiallyFilled → Filled | Cancelled | Expired`. The tracker stores the full history for the current session.

### OrderLifecycleTracker API

```python
class OrderLifecycleTracker:
    """Tracks order state transitions within the current session."""

    def track(self, order_id: str) -> None:
        """Explicitly track an order by ID (auto-called by place_order)."""

    def status(self, order_id: str) -> OrderStatus | None:
        """Current status of a tracked order."""

    def history(self, order_id: str) -> list[OrderStatusEvent]:
        """Full state transition history for an order within this session."""

    def pending_orders(self) -> list[str]:
        """Order IDs that have been submitted but not yet acknowledged."""

    def active_orders(self) -> list[str]:
        """Order IDs that are acknowledged or partially filled."""

    def completed_orders(self) -> list[str]:
        """Order IDs that reached a terminal state (filled, cancelled, expired)."""

    def on_status_change(
        self,
        callback: Callable[[str, OrderStatus, OrderStatus], Awaitable[None]],
    ) -> None:
        """Register a callback for order state transitions.
        callback(order_id, old_status, new_status)."""
```

---

## Risk Monitoring

The `RiskMonitor` computes risk metrics locally from the `PositionStateManager` data. No additional network calls. Updated continuously as new state arrives.

### API

```python
class RiskMonitor:
    """Continuous risk computation from local state.
    
    Access via client.risk. All methods are synchronous.
    """

    # ── Liquidation ───────────────────────────────────────────────

    def liquidation_distance(
        self, subaccount: str, market: str
    ) -> LiquidationEstimate | None:
        """Distance to liquidation for a specific position.
        
        Returns LiquidationEstimate:
            liquidation_price: float   — estimated liquidation price
            current_price: float       — current mark price
            distance_pct: float        — percentage distance (0.05 = 5%)
            distance_usd: float        — absolute price distance
        
        Returns None if no position exists in this market.
        """

    def min_liquidation_distance(self, subaccount: str) -> LiquidationEstimate | None:
        """The position closest to liquidation across all markets.
        Returns None if no positions are open."""

    # ── Margin warnings ───────────────────────────────────────────

    def margin_warning(
        self,
        subaccount: str,
        *,
        warn_threshold: float = 0.80,
        critical_threshold: float = 0.90,
    ) -> MarginWarning | None:
        """Check if margin usage exceeds warning thresholds.
        
        Returns MarginWarning:
            level: Literal["ok", "warn", "critical"]
            margin_usage_pct: float
            available_margin: float
            equity: float
        
        Returns None if overview data is not yet available.
        """

    # ── Funding ───────────────────────────────────────────────────

    def funding_accrual_rate(
        self, subaccount: str, market: str
    ) -> FundingAccrual | None:
        """Estimated hourly funding accrual for a position.
        
        Returns FundingAccrual:
            hourly_usd: float      — estimated hourly funding payment (negative = paying)
            annualized_pct: float  — annualized rate as percentage of notional
            funding_rate_bps: float — current market funding rate in bps
            position_notional: float
        
        Returns None if no position exists.
        """

    def total_funding_accrual_rate(self, subaccount: str) -> float:
        """Total estimated hourly funding across all positions (USD).
        Negative means the account is a net payer."""

    # ── Position protection ───────────────────────────────────────

    def positions_without_tp_sl(self, subaccount: str) -> list[str]:
        """Market names where the subaccount has an open position but no
        take-profit or stop-loss order."""

    def unprotected_exposure_usd(self, subaccount: str) -> float:
        """Total notional of positions that lack TP/SL protection."""

    # ── Aggregate ─────────────────────────────────────────────────

    def risk_summary(self, subaccount: str) -> dict:
        """One-call snapshot of all risk metrics for logging/display.
        Returns a dict with all fields from the above methods."""
```

### Risk Check Before Trading

```python
risk = client.risk

warning = risk.margin_warning(my_subaccount)
if warning and warning.level == "critical":
    logger.warning("Margin critical — skipping new orders")
    continue

liq = risk.min_liquidation_distance(my_subaccount)
if liq and liq.distance_pct < 0.10:
    logger.warning(f"Liquidation within 10% on {liq.market}")
    await client.place_tp_sl(...)

unprotected = risk.positions_without_tp_sl(my_subaccount)
if unprotected:
    for market in unprotected:
        logger.warning(f"No TP/SL on {market} — adding protection")
```

---

## Reconnection Strategy

WebSocket connections drop. The SDK handles this transparently.

### Sequence of Events on Disconnect

```
1. WS connection lost
   ├── state.is_connected → False
   └── on_event fires: {"type": "ws_disconnect", "timestamp": ...}

2. Exponential backoff reconnection (1s, 2s, 4s, ... up to ws_reconnect_max_delay_s)
   └── Each attempt fires: {"type": "ws_reconnect_attempt", "attempt": N}

3. WS connection re-established
   ├── Re-subscribe to all previous topics (positions, orders, overview, prices, depth)
   └── on_event fires: {"type": "ws_reconnect", "timestamp": ...}

4. REST re-sync to fill gaps
   ├── GET /positions for each subscribed subaccount
   ├── GET /open-orders for each subscribed subaccount
   ├── GET /account-overview for each subscribed subaccount
   └── Merge REST state into PositionStateManager

5. Gap detection
   ├── If WS sequence numbers show a gap → state.gap_detected = True
   ├── After REST re-sync completes → state.gap_detected = False
   └── on_event fires: {"type": "state_resync_complete", "gap_orders": [...]}

6. Normal WS flow resumes
   └── state.is_connected → True
```

### What Your Bot Should Do

```python
while True:
    if not state.is_connected:
        # SDK is reconnecting — state is stale
        # Option A: pause trading
        await asyncio.sleep(1.0)
        continue

    if state.gap_detected:
        # REST re-sync in progress — state is being rebuilt
        await asyncio.sleep(0.1)
        continue

    # Safe to trade — state is current
    mid = state.mid_price("BTC-USD")
    ...
```

### Tuning Reconnection

```python
client = DecibelClient(
    ...,
    ws_ping_interval_s=10.0,     # more aggressive keepalive
    ws_reconnect_max_delay_s=15.0, # cap backoff at 15s
)
```

---

## Human-Readable Price/Size by Default

All SDK methods that accept price or size parameters take **human-readable floats** and convert internally.

```python
# You write:
await client.place_order(
    market_name="BTC-USD",
    price=45000.0,   # dollars
    size=0.25,       # BTC
    is_buy=True,
)

# The SDK internally:
# 1. Looks up cached PerpMarketConfig for BTC-USD
# 2. Rounds price to tick_size granularity
# 3. Rounds size to lot_size granularity (clamps to min_size)
# 4. Converts to chain units: price * 10^px_decimals, size * 10^sz_decimals
# 5. Builds and submits the transaction with chain-unit integers
```

### Raw Mode

For latency-sensitive bots that pre-compute chain units:

```python
await client.place_order(
    market_name="BTC-USD",
    price=4500000000,  # pre-computed chain units
    size=25000000,
    is_buy=True,
    raw=True,          # skip conversion
)
```

### Conversion Utilities

```python
from decibel.utils.formatting import (
    to_chain_price,
    to_chain_size,
    from_chain_price,
    from_chain_size,
    round_to_tick,
    round_to_lot,
)

market = await client.get_market("BTC-USD")

chain_px = to_chain_price(45000.0, market)       # int
chain_sz = to_chain_size(0.25, market)            # int
human_px = from_chain_price(chain_px, market)     # float
human_sz = from_chain_size(chain_sz, market)      # float

rounded_px = round_to_tick(45000.123, market)     # snapped to tick_size
rounded_sz = round_to_lot(0.1234567, market)      # snapped to lot_size, >= min_size
```

The SDK caches `PerpMarketConfig` on first access and refreshes every 60 seconds in the background.

---

## Real Bot Patterns

### Pattern 1: Market Making Loop

A two-sided quoter that adjusts spread based on inventory.

```python
import asyncio
from decibel import DecibelClient, MAINNET_CONFIG
from decibel.models.enums import TimeInForce

MARKET = "BTC-USD"
BASE_SPREAD = 1.5      # $1.50 half-spread
SIZE_PER_LEVEL = 0.01  # BTC per quote level
LEVELS = 3
MAX_INVENTORY = 0.1    # max net BTC before skewing

async def run_market_maker():
    async with DecibelClient(
        config=MAINNET_CONFIG,
        bearer_token=TOKEN,
        private_key=PK,
        subaccount_addrs=[SUBACCOUNT],
        markets=[MARKET],
    ) as client:
        bulk = client.bulk(MARKET)
        state = client.state
        risk = client.risk

        while True:
            mid = state.mid_price(MARKET)
            if mid is None or not state.is_connected:
                await asyncio.sleep(0.2)
                continue

            warning = risk.margin_warning(SUBACCOUNT)
            if warning and warning.level == "critical":
                await bulk.cancel_all()
                await asyncio.sleep(5.0)
                continue

            pos = state.position(SUBACCOUNT, MARKET)
            inventory = pos.size if pos else 0.0

            # Skew spread based on inventory
            skew = (inventory / MAX_INVENTORY) * BASE_SPREAD
            bid_spread = BASE_SPREAD + skew   # wider when long
            ask_spread = BASE_SPREAD - skew   # tighter when long

            bids = [
                (mid - bid_spread * (i + 1), SIZE_PER_LEVEL)
                for i in range(LEVELS)
            ]
            asks = [
                (mid + ask_spread * (i + 1), SIZE_PER_LEVEL)
                for i in range(LEVELS)
            ]

            await bulk.set_quotes(bids=bids, asks=asks)

            fills = bulk.filled_since_last_reset()
            if fills.fill_count > 0:
                spread_pnl = fills.avg_ask_price - fills.avg_bid_price
                # log fill activity for monitoring
                bulk.reset_fill_tracker()

            await asyncio.sleep(0.5)

asyncio.run(run_market_maker())
```

### Pattern 2: Directional Agent with Position Management

An AI signal consumer that enters positions and manages risk.

```python
async def run_directional_agent(signal_queue: asyncio.Queue):
    async with DecibelClient(
        config=MAINNET_CONFIG,
        bearer_token=TOKEN,
        private_key=PK,
        subaccount_addrs=[SUBACCOUNT],
        markets=["BTC-USD", "ETH-USD", "SOL-USD"],
    ) as client:
        state = client.state
        risk = client.risk

        while True:
            signal = await signal_queue.get()
            market = signal["market"]
            direction = signal["direction"]  # "long" or "short"
            confidence = signal["confidence"]  # 0.0-1.0

            # Pre-trade risk checks
            warning = risk.margin_warning(SUBACCOUNT)
            if warning and warning.level != "ok":
                continue

            existing = state.position(SUBACCOUNT, market)
            if existing is not None:
                # Already positioned — only add if same direction
                is_same = (existing.size > 0) == (direction == "long")
                if not is_same:
                    continue

            equity = state.equity(SUBACCOUNT)
            notional = equity * 0.05 * confidence  # 5% per unit confidence
            mark = state.mark_price(market)
            if mark is None:
                continue
            size = notional / mark

            is_buy = direction == "long"
            result = await client.place_order(
                market_name=market,
                price=mark * (0.999 if is_buy else 1.001),
                size=size,
                is_buy=is_buy,
                time_in_force=TimeInForce.ImmediateOrCancel,
                client_order_id=f"signal-{signal['id']}",
            )

            if result.success:
                tp_pct = 0.02
                sl_pct = 0.01
                tp_price = mark * (1 + tp_pct if is_buy else 1 - tp_pct)
                sl_price = mark * (1 - sl_pct if is_buy else 1 + sl_pct)

                await client.place_tp_sl(
                    market_name=market,
                    tp_trigger_price=tp_price,
                    tp_limit_price=tp_price * (0.999 if is_buy else 1.001),
                    sl_trigger_price=sl_price,
                    sl_limit_price=sl_price * (1.001 if is_buy else 0.999),
                )
```

### Pattern 3: Multi-Strategy, Multi-Subaccount

Run multiple strategies in isolated subaccounts from a single connection.

```python
async def run_multi_strategy():
    SUBACCOUNTS = {
        "mm": "0x...subaccount_mm",
        "trend": "0x...subaccount_trend",
        "arb": "0x...subaccount_arb",
    }

    async with DecibelClient(
        config=MAINNET_CONFIG,
        bearer_token=TOKEN,
        private_key=PK,
        subaccount_addrs=list(SUBACCOUNTS.values()),
        markets=["BTC-USD", "ETH-USD", "SOL-USD"],
    ) as client:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(market_making_loop(client, SUBACCOUNTS["mm"]))
            tg.create_task(trend_following_loop(client, SUBACCOUNTS["trend"]))
            tg.create_task(basis_arb_loop(client, SUBACCOUNTS["arb"]))
            tg.create_task(risk_watchdog(client, SUBACCOUNTS))

async def risk_watchdog(client: DecibelClient, subaccounts: dict[str, str]):
    """Global risk monitor — kills all positions if aggregate drawdown exceeds limit."""
    risk = client.risk
    state = client.state

    while True:
        total_equity = sum(
            state.equity(sa) for sa in subaccounts.values()
        )
        total_exposure = sum(
            state.gross_exposure_usd(sa) for sa in subaccounts.values()
        )

        if total_equity > 0 and total_exposure / total_equity > 5.0:
            for name, sa in subaccounts.items():
                for market in state.positions(sa):
                    await client.bulk(market).cancel_all(subaccount=sa)

        for name, sa in subaccounts.items():
            unprotected = risk.positions_without_tp_sl(sa)
            if unprotected:
                # alert or auto-add protection
                pass

        await asyncio.sleep(5.0)
```

---

## Error Handling

All errors inherit from `DecibelError`. See [08-error-handling.md](./08-error-handling.md) for the full taxonomy.

```python
from decibel.errors import (
    DecibelError,
    ApiError,
    RateLimitError,
    TransactionError,
    ValidationError,
    ReconnectionError,
    SequenceError,
)

try:
    result = await client.place_order(...)
except RateLimitError as e:
    await asyncio.sleep(e.retry_after_ms / 1000)
    result = await client.place_order(...)
except SequenceError as e:
    # Bulk order sequence number mismatch — manager auto-recovers
    # but you may want to skip this quoting cycle
    pass
except TransactionError as e:
    logger.error(f"TX failed: {e.vm_status} (hash={e.transaction_hash})")
except ValidationError as e:
    logger.error(f"Invalid {e.field}: {e.constraint}")
except DecibelError as e:
    logger.error(f"SDK error: {e.code} - {e}")
```

---

## Logging and Observability

```python
import logging

logging.getLogger("decibel").setLevel(logging.INFO)
logging.getLogger("decibel.ws").setLevel(logging.DEBUG)       # WS frame-level logs
logging.getLogger("decibel.bulk").setLevel(logging.DEBUG)     # bulk order diffs
logging.getLogger("decibel.state").setLevel(logging.DEBUG)    # state manager updates
logging.getLogger("decibel.risk").setLevel(logging.WARNING)   # risk alerts only
```

### Event Hooks for Bot Telemetry

```python
async def telemetry_handler(event: dict) -> None:
    match event["type"]:
        case "ws_disconnect":
            metrics.increment("ws.disconnects")
        case "ws_reconnect":
            metrics.gauge("ws.reconnect_latency_ms", event["latency_ms"])
        case "state_resync_complete":
            metrics.increment("state.resyncs")
        case "order_fill":
            metrics.increment("fills.count")
            metrics.observe("fills.size", event["size"])
        case "bulk_quote_sent":
            metrics.observe("bulk.placed", event["placed_count"])
        case "risk_warning":
            alerting.fire(event)

client = DecibelClient(
    ...,
    on_event=telemetry_handler,
)
```

---

## Testing

### Unit Tests: Model Validation

```python
import pytest
from decibel.models import MarketPrice, UserPosition
from decibel.models.risk import LiquidationEstimate

def test_market_price_roundtrip():
    data = {
        "market": "BTC-USD",
        "mark_px": 45000.0,
        "mid_px": 44999.5,
        "oracle_px": 45001.0,
        "funding_rate_bps": 0.01,
        "is_funding_positive": True,
        "open_interest": 1500000.0,
        "transaction_unix_ms": 1710000000000,
    }
    model = MarketPrice.model_validate(data)
    assert model.model_dump() == data

def test_liquidation_estimate_frozen():
    est = LiquidationEstimate(
        liquidation_price=42000.0,
        current_price=45000.0,
        distance_pct=0.0667,
        distance_usd=3000.0,
    )
    with pytest.raises(Exception):
        est.distance_pct = 0.1  # frozen model
```

### Unit Tests: State Manager

```python
from decibel.state.position_manager import PositionStateManager
from decibel.models.account import UserPosition

def test_position_merge():
    mgr = PositionStateManager()
    pos = UserPosition.model_validate({...})
    mgr._merge_position("0xsub", "BTC-USD", pos)
    assert mgr.position("0xsub", "BTC-USD") == pos

def test_exposure_calculation():
    mgr = PositionStateManager()
    # inject two positions
    mgr._merge_position("0xsub", "BTC-USD", mock_position(size=1.0, mark=45000))
    mgr._merge_position("0xsub", "ETH-USD", mock_position(size=-10.0, mark=3000))
    assert mgr.net_exposure_usd("0xsub") == 45000.0 - 30000.0
    assert mgr.gross_exposure_usd("0xsub") == 45000.0 + 30000.0
```

### Integration Tests: Order Lifecycle

```python
@pytest.mark.integration
async def test_place_track_cancel(client: DecibelClient):
    state = client.state
    result = await client.place_order(
        market_name="BTC-USD",
        price=10.0,
        size=1.0,
        is_buy=True,
        time_in_force=TimeInForce.GoodTillCanceled,
        client_order_id="test-lifecycle-001",
    )
    assert result.success
    assert result.order_id is not None

    await asyncio.sleep(1.0)
    order = state.order_by_client_id("test-lifecycle-001")
    assert order is not None

    cancel = await client.cancel_order(
        order_id=result.order_id,
        market_name="BTC-USD",
    )
    assert cancel.success

@pytest.mark.integration
async def test_bulk_quote_cycle(client: DecibelClient):
    bulk = client.bulk("BTC-USD")
    state = client.state

    mid = state.mid_price("BTC-USD")
    assert mid is not None

    result = await bulk.set_quotes(
        bids=[(mid - 100, 0.001)],
        asks=[(mid + 100, 0.001)],
    )
    assert result.placed_count == 2
    assert result.errors == []

    cancelled = await bulk.cancel_all()
    assert cancelled == 2
```

### Simulation / Backtest Harness

The `PositionStateManager` and `RiskMonitor` accept injected state, so you can drive them from historical data without a live connection:

```python
from decibel.state.position_manager import PositionStateManager
from decibel.state.risk_monitor import RiskMonitor

state = PositionStateManager()
risk = RiskMonitor(state)

for snapshot in historical_snapshots:
    state._inject_snapshot(snapshot)
    liq = risk.min_liquidation_distance(SUBACCOUNT)
    # evaluate strategy decisions against historical state
```

---

## Dependencies

```toml
[project]
name = "decibel-sdk"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "websockets>=13.0",
    "pydantic>=2.6",
    "cryptography>=43.0",
    "aptos-sdk>=0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
    "mypy>=1.13",
]
ml = [
    "numpy>=1.26",
    "pandas>=2.2",
]
```

---

## Idioms

### Pydantic Model Pattern

```python
from pydantic import BaseModel, ConfigDict, Field

class UserPosition(BaseModel):
    """A single open perpetual futures position.

    Populated from REST GET /positions or WS positions:{subaccount} topic.
    All prices and sizes are in human-readable units.
    """
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    market: str = Field(description="Market name (e.g. 'BTC-USD')")
    size: float = Field(description="Position size (positive=long, negative=short)")
    avg_entry_price: float = Field(description="Average entry price")
    mark_price: float = Field(description="Current mark price")
    unrealized_pnl: float = Field(description="Unrealized PnL in USD")
    leverage: float = Field(description="Effective leverage")
    margin_mode: str = Field(description="'cross' or 'isolated'")
    liquidation_price: float | None = Field(default=None, description="Estimated liquidation price")
    tp_order_id: str | None = Field(default=None, description="Take-profit order ID if set")
    sl_order_id: str | None = Field(default=None, description="Stop-loss order ID if set")

    @property
    def notional(self) -> float:
        return abs(self.size) * self.mark_price

    @property
    def is_long(self) -> bool:
        return self.size > 0

    @property
    def has_tp_sl(self) -> bool:
        return self.tp_order_id is not None and self.sl_order_id is not None

    def __str__(self) -> str:
        side = "LONG" if self.is_long else "SHORT"
        return (
            f"Position({self.market} {side} {abs(self.size)} "
            f"@ {self.avg_entry_price}, PnL={self.unrealized_pnl:+.2f})"
        )
```

### Enum Pattern

```python
from enum import IntEnum, StrEnum

class TimeInForce(IntEnum):
    GoodTillCanceled = 0
    PostOnly = 1
    ImmediateOrCancel = 2

class OrderSide(StrEnum):
    Buy = "buy"
    Sell = "sell"
```

### Context Manager Pattern

```python
async with DecibelClient(config=MAINNET_CONFIG, bearer_token="...") as client:
    # WS connections established, state manager running, market configs cached
    ...
# All connections closed, background tasks cancelled, state flushed
```
