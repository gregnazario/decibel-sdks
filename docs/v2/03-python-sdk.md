# Python SDK Specification

**Parent**: [00-overview.md](./00-overview.md)  
**Language**: Python 3.11+  
**Package**: `decibel-sdk`

---

## Philosophy

The Python SDK is the primary SDK for AI agent developers. It prioritizes:

1. **Type completeness** — every parameter, every return value, every error is annotated.
2. **Pydantic everywhere** — all models are Pydantic `BaseModel` subclasses with full JSON Schema export, validation, and serialization.
3. **Async-first** — all I/O operations are `async` using `asyncio`. No synchronous wrappers that hide concurrency bugs.
4. **LLM-friendly** — all objects have rich `__repr__` and `__str__` for easy consumption by language models that inspect runtime state.

---

## Package Structure

```
decibel/
├── __init__.py              # Re-exports: DecibelClient, models, config presets
├── client.py                # DecibelClient (unified entry point)
├── config.py                # DecibelConfig, Deployment, presets
├── models/
│   ├── __init__.py          # Re-exports all models
│   ├── market.py            # PerpMarketConfig, MarketPrice, MarketContext, etc.
│   ├── account.py           # AccountOverview, UserPosition, UserSubaccount
│   ├── order.py             # UserOpenOrder, OrderStatus, PlaceOrderResult, etc.
│   ├── trade.py             # UserTradeHistoryItem, UserFundingHistoryItem, etc.
│   ├── vault.py             # Vault, UserOwnedVault
│   ├── analytics.py         # LeaderboardItem, PortfolioChartPoint
│   ├── twap.py              # UserActiveTwap
│   ├── ws.py                # WebSocket message wrapper types
│   ├── pagination.py        # PageParams, SortParams, PaginatedResponse
│   └── enums.py             # All enumerations
├── read/
│   ├── __init__.py
│   ├── client.py            # DecibelReadClient
│   ├── markets.py           # Market data reader methods
│   ├── account.py           # Account data reader methods
│   ├── history.py           # Historical data reader methods
│   ├── vaults.py            # Vault reader methods
│   └── analytics.py         # Leaderboard, portfolio reader methods
├── write/
│   ├── __init__.py
│   ├── client.py            # DecibelWriteClient
│   ├── orders.py            # Order placement and cancellation
│   ├── positions.py         # TP/SL management
│   ├── accounts.py          # Subaccount management, delegation
│   ├── vaults.py            # Vault operations
│   └── bulk.py              # Bulk order operations
├── ws/
│   ├── __init__.py
│   ├── manager.py           # WebSocketManager
│   └── topics.py            # Topic string builders and parsing
├── tx/
│   ├── __init__.py
│   ├── builder.py           # TransactionBuilder (sync build)
│   ├── signer.py            # Ed25519 transaction signing
│   └── gas.py               # GasPriceManager
├── utils/
│   ├── __init__.py
│   ├── address.py           # Address derivation (market, subaccount, vault share)
│   ├── formatting.py        # Price/size formatting and rounding
│   └── nonce.py             # Replay protection nonce generation
└── errors.py                # All error types
```

---

## Entry Point: DecibelClient

The unified client is the primary entry point for agents. It composes `DecibelReadClient` and `DecibelWriteClient` under a single interface.

```python
from decibel import DecibelClient, MAINNET_CONFIG

# Read-only agent (no private key needed)
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="your-bearer-token",
)

# Full agent (read + write)
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="your-bearer-token",
    private_key="0x...",  # Ed25519 private key hex
)
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `config` | `DecibelConfig` | YES | SDK configuration (use a preset or custom) |
| `bearer_token` | `str` | YES | Bearer token for REST/WS authentication |
| `private_key` | `str` | NO | Ed25519 private key hex for on-chain transactions |
| `node_api_key` | `str` | NO | Aptos node API key for higher rate limits |
| `skip_simulate` | `bool` | NO | Skip tx simulation (default: `False`) |
| `no_fee_payer` | `bool` | NO | Disable gas station (default: `False`) |
| `gas_refresh_interval_s` | `float` | NO | Gas price refresh interval (default: `5.0`) |
| `time_delta_ms` | `int` | NO | Clock drift compensation in ms |
| `request_timeout_s` | `float` | NO | HTTP request timeout (default: `30.0`) |

### Agent Discovery

```python
# Agents can discover what the client can do
client.list_capabilities()
# Returns: ['get_markets', 'get_prices', 'get_positions', 'place_order', ...]

# Agents can inspect any model's schema
from decibel.models import MarketPrice
MarketPrice.model_json_schema()
# Returns: full JSON Schema dict
```

---

## Configuration

```python
from decibel.config import DecibelConfig, Deployment, MAINNET_CONFIG, TESTNET_CONFIG

# Use a preset
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

## Read Operations

All read operations are async and return typed models.

### Market Data

```python
# List all markets
markets: list[PerpMarketConfig] = await client.get_markets()

# Get a specific market by name
btc: PerpMarketConfig = await client.get_market("BTC-USD")

# Get current prices for all markets
prices: list[MarketPrice] = await client.get_prices()

# Get price for a specific market
btc_price: list[MarketPrice] = await client.get_price("BTC-USD")

# Get orderbook depth
depth: MarketDepth = await client.get_depth("BTC-USD", limit=20)

# Get recent trades
trades: list[MarketTrade] = await client.get_trades("BTC-USD", limit=50)

# Get candlesticks
from decibel.models.enums import CandlestickInterval
candles: list[Candlestick] = await client.get_candlesticks(
    market="BTC-USD",
    interval=CandlestickInterval.OneHour,
    start_time=1710000000000,
    end_time=1710086400000,
)

# Get asset contexts (24h stats)
contexts: list[MarketContext] = await client.get_asset_contexts()
```

### Account Data

```python
# Get account overview
overview: AccountOverview = await client.get_account_overview(
    subaccount_addr="0x...",
    volume_window=VolumeWindow.ThirtyDays,
    include_performance=True,
)

# Get positions
positions: list[UserPosition] = await client.get_positions("0x...")

# Get positions for a specific market
btc_positions: list[UserPosition] = await client.get_positions(
    subaccount_addr="0x...",
    market_addr="0x...",
)

# Get open orders
orders: list[UserOpenOrder] = await client.get_open_orders("0x...")

# Get subaccounts for an owner
subs: list[UserSubaccount] = await client.get_subaccounts("0x...owner")

# Get delegations
delegations: list[Delegation] = await client.get_delegations("0x...")
```

### History (Paginated)

```python
from decibel.models.pagination import PageParams, SortParams

# Trade history with pagination
trades = await client.get_trade_history(
    subaccount_addr="0x...",
    page=PageParams(limit=50, offset=0),
)
# trades.items: list[UserTradeHistoryItem]
# trades.total_count: int

# Order history with filters
orders = await client.get_order_history(
    subaccount_addr="0x...",
    market_addr="0x...",  # optional filter
    page=PageParams(limit=20),
    sort=SortParams(sort_key="transaction_unix_ms", sort_dir=SortDirection.Descending),
)

# Funding history
funding = await client.get_funding_history(
    subaccount_addr="0x...",
    page=PageParams(limit=100),
)

# Fund history (deposits/withdrawals)
funds = await client.get_fund_history(
    subaccount_addr="0x...",
    page=PageParams(limit=50),
)
```

### TWAP Orders

```python
# Get active TWAPs
twaps: list[UserActiveTwap] = await client.get_active_twaps("0x...")

# Get TWAP history
twap_history = await client.get_twap_history(
    subaccount_addr="0x...",
    page=PageParams(limit=20),
)
```

### Vaults

```python
# List public vaults
vaults = await client.get_vaults(
    page=PageParams(limit=20),
    sort=SortParams(sort_key="tvl", sort_dir=SortDirection.Descending),
)

# Get user-owned vaults
owned = await client.get_owned_vaults("0x...account")

# Get vault performance
perf = await client.get_vault_performance("0x...account")
```

### Analytics

```python
# Leaderboard
lb = await client.get_leaderboard(
    page=PageParams(limit=50),
    sort=SortParams(sort_key="roi", sort_dir=SortDirection.Descending),
)

# Portfolio chart
chart: list[PortfolioChartPoint] = await client.get_portfolio_chart("0x...")
```

### Order Status

```python
# Check specific order status
status: OrderStatus = await client.get_order_status(
    order_id="12345",
    market_address="0x...",
    user_address="0x...",
)
```

---

## Write Operations

Write operations require a private key. All return `TransactionResult` or a specialized result type.

### Account Management

```python
# Create a new subaccount
result: TransactionResult = await client.create_subaccount()

# Deposit USDC (amount in raw u64 chain units)
result = await client.deposit(amount=1_000_000, subaccount_addr="0x...")

# Withdraw USDC
result = await client.withdraw(amount=500_000, subaccount_addr="0x...")

# Configure margin mode and leverage for a market
result = await client.configure_market_settings(
    market_addr="0x...",
    subaccount_addr="0x...",
    is_cross=True,
    user_leverage=10_000,  # basis points: 10000 = 100x
)
```

### Order Management

```python
from decibel.models.enums import TimeInForce

# Place a limit order
result: PlaceOrderResult = await client.place_order(
    market_name="BTC-USD",
    price=45_000.0,
    size=0.25,
    is_buy=True,
    time_in_force=TimeInForce.GoodTillCanceled,
    is_reduce_only=False,
    client_order_id="agent-order-001",
)

if result.success:
    print(f"Order placed: {result.order_id}")

# Cancel by exchange order ID
result = await client.cancel_order(
    order_id=result.order_id,
    market_name="BTC-USD",
)

# Cancel by client order ID
result = await client.cancel_client_order(
    client_order_id="agent-order-001",
    market_name="BTC-USD",
)
```

#### Price/Size Formatting

The SDK provides helpers that use `PerpMarketConfig` to format values correctly:

```python
from decibel.utils.formatting import (
    round_to_valid_price,
    round_to_valid_order_size,
    amount_to_chain_units,
    chain_units_to_amount,
)

market = await client.get_market("BTC-USD")

# Round a price to the nearest valid tick
price = round_to_valid_price(45_123.456, market)
# Result: 45123.456 rounded to tick_size granularity

# Round a size to the nearest valid lot
size = round_to_valid_order_size(0.1234, market)
# Result: 0.1234 rounded to lot_size granularity, >= min_size

# Convert to chain units for direct transaction building
chain_price = amount_to_chain_units(price, market.px_decimals)
chain_size = amount_to_chain_units(size, market.sz_decimals)
```

**Agent convenience**: `place_order` accepts human-readable prices and sizes by default. The SDK internally fetches market config (cached) and performs rounding. Agents can opt into raw chain units by passing `raw=True`.

### TWAP Orders

```python
# Place a TWAP order
result = await client.place_twap_order(
    market_name="BTC-USD",
    size=2.0,
    is_buy=True,
    is_reduce_only=False,
    twap_frequency_seconds=30,
    twap_duration_seconds=15 * 60,  # 15 minutes
    client_order_id="twap-001",
)

# Cancel a TWAP
result = await client.cancel_twap_order(
    order_id="...",
    market_addr="0x...",
)
```

### Position Management (TP/SL)

```python
# Set TP/SL for a position
result = await client.place_tp_sl(
    market_addr="0x...",
    tp_trigger_price=47_000.0,
    tp_limit_price=46_950.0,
    sl_trigger_price=43_000.0,
    sl_limit_price=43_050.0,
)

# Update just the take-profit
result = await client.update_tp_order(
    market_addr="0x...",
    prev_order_id="...",
    tp_trigger_price=48_000.0,
    tp_limit_price=47_950.0,
)

# Update just the stop-loss
result = await client.update_sl_order(
    market_addr="0x...",
    prev_order_id="...",
    sl_trigger_price=42_000.0,
    sl_limit_price=42_050.0,
)

# Cancel a TP/SL order
result = await client.cancel_tp_sl(
    market_addr="0x...",
    order_id="...",
)
```

### Delegation

```python
# Delegate trading to another account
result = await client.delegate_trading(
    subaccount_addr="0x...",
    delegate_to="0x...operator",
    expiration_timestamp_secs=1710000000,  # optional
)

# Revoke delegation
result = await client.revoke_delegation(
    account_to_revoke="0x...operator",
    subaccount_addr="0x...",
)
```

### Builder Fees

```python
# Approve a builder fee
result = await client.approve_builder_fee(
    builder_addr="0x...builder",
    max_fee=100,  # basis points
)

# Revoke builder fee
result = await client.revoke_builder_fee(
    builder_addr="0x...builder",
)
```

### Vault Operations

```python
# Create a vault
result = await client.create_vault(
    vault_name="Agent Alpha",
    vault_description="AI-managed momentum strategy",
    vault_social_links=[],
    vault_share_symbol="ALPHA",
    fee_bps=1000,  # 10%
    fee_interval_s=604800,  # weekly
    contribution_lockup_duration_s=86400,  # 1 day
    initial_funding=10_000_000,
    accepts_contributions=True,
    delegate_to_creator=True,
)

# Activate a vault
result = await client.activate_vault("0x...vault")

# Deposit to a vault
result = await client.deposit_to_vault("0x...vault", amount=5_000_000)

# Withdraw from a vault
result = await client.withdraw_from_vault("0x...vault", shares=1_000)
```

---

## WebSocket Subscriptions

All subscriptions are managed through the client. Each returns an unsubscribe callable.

```python
# Subscribe to market prices
unsub = await client.subscribe_market_price("BTC-USD", callback=on_price)

async def on_price(price: MarketPrice) -> None:
    print(f"BTC: {price.mark_px}")

# Subscribe to all market prices
unsub = await client.subscribe_all_market_prices(callback=on_all_prices)

# Subscribe to orderbook depth
unsub = await client.subscribe_depth(
    market_name="BTC-USD",
    aggregation_level=1,
    callback=on_depth,
)

# Subscribe to account overview
unsub = await client.subscribe_account_overview("0x...", callback=on_overview)

# Subscribe to positions
unsub = await client.subscribe_positions("0x...", callback=on_positions)

# Subscribe to order updates
unsub = await client.subscribe_order_updates("0x...", callback=on_order_update)

# Subscribe to user trades
unsub = await client.subscribe_user_trades("0x...", callback=on_trade)

# Unsubscribe when done
await unsub()
```

### Async Iterator Alternative

For agents that prefer iteration over callbacks:

```python
async for price in client.stream_market_price("BTC-USD"):
    # Process each price update
    if price.mark_px > threshold:
        await client.place_order(...)
        break
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
)

try:
    result = await client.place_order(...)
except RateLimitError as e:
    # e.retryable == True
    # e.retry_after_ms tells you when to retry
    await asyncio.sleep(e.retry_after_ms / 1000)
    result = await client.place_order(...)
except TransactionError as e:
    # e.transaction_hash, e.vm_status, e.gas_used
    logger.error(f"TX failed: {e.vm_status}")
except ValidationError as e:
    # e.field, e.constraint
    logger.error(f"Invalid {e.field}: {e.constraint}")
except DecibelError as e:
    # Catch-all for any SDK error
    logger.error(f"SDK error: {e.code} - {e}")
```

---

## Logging and Observability

The SDK uses Python's `logging` module under the `decibel` logger name.

```python
import logging

# Enable debug logging for the SDK
logging.getLogger("decibel").setLevel(logging.DEBUG)

# Or configure specific subsystems
logging.getLogger("decibel.http").setLevel(logging.DEBUG)
logging.getLogger("decibel.ws").setLevel(logging.DEBUG)
logging.getLogger("decibel.tx").setLevel(logging.INFO)
```

### Event Hooks

```python
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="...",
    on_event=my_event_handler,
)

async def my_event_handler(event: dict) -> None:
    """Receives structured events for custom telemetry."""
    # event["type"]: "http_request", "ws_message", "tx_submitted", "error", etc.
    # event["timestamp"]: Unix ms
    # event["data"]: event-specific payload
    ...
```

---

## Testing

### Unit Test Conventions

```python
import pytest
from decibel.models import MarketPrice

def test_market_price_roundtrip():
    """Models serialize and deserialize identically."""
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

def test_market_price_schema_export():
    """Agents can inspect JSON Schema."""
    schema = MarketPrice.model_json_schema()
    assert "properties" in schema
    assert "mark_px" in schema["properties"]
```

### Integration Test Conventions

```python
@pytest.mark.integration
async def test_place_and_cancel_order(client: DecibelClient):
    """Full lifecycle: place → check → cancel."""
    result = await client.place_order(
        market_name="BTC-USD",
        price=10.0,
        size=1.0,
        is_buy=True,
        time_in_force=TimeInForce.GoodTillCanceled,
        is_reduce_only=False,
        client_order_id="test-001",
    )
    assert result.success
    assert result.order_id is not None

    status = await client.get_order_status(
        order_id=result.order_id,
        market_address="0x...",
        user_address="0x...",
    )
    assert status.status == "Acknowledged"

    cancel = await client.cancel_order(
        order_id=result.order_id,
        market_name="BTC-USD",
    )
    assert cancel.success
```

---

## Dependencies

```toml
[project]
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
```

---

## Idioms

### Pydantic Model Pattern

```python
from pydantic import BaseModel, ConfigDict, Field

class MarketPrice(BaseModel):
    """Real-time price snapshot for a perpetual futures market.

    Received from REST GET /api/v1/prices or WebSocket market_price:{addr} topic.
    """
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    market: str = Field(description="Market name or address")
    mark_px: float = Field(description="Mark price for margin calculations")
    mid_px: float = Field(description="Mid price (average of best bid/ask)")
    oracle_px: float = Field(description="Oracle price from external feed")
    funding_rate_bps: float = Field(description="Funding rate in basis points")
    is_funding_positive: bool = Field(description="True if longs pay shorts")
    open_interest: float = Field(description="Total open interest")
    transaction_unix_ms: int = Field(description="Timestamp of last update (Unix ms)")

    def __str__(self) -> str:
        return (
            f"MarketPrice({self.market}: mark={self.mark_px}, "
            f"oracle={self.oracle_px}, funding={self.funding_rate_bps}bps)"
        )
```

### Enum Pattern

```python
from enum import IntEnum, StrEnum

class TimeInForce(IntEnum):
    """Controls how long an order remains active on the orderbook."""
    GoodTillCanceled = 0
    PostOnly = 1
    ImmediateOrCancel = 2

class CandlestickInterval(StrEnum):
    """Time interval for candlestick/OHLCV data."""
    OneMinute = "1m"
    FiveMinutes = "5m"
    FifteenMinutes = "15m"
    ThirtyMinutes = "30m"
    OneHour = "1h"
    TwoHours = "2h"
    FourHours = "4h"
    EightHours = "8h"
    TwelveHours = "12h"
    OneDay = "1d"
    ThreeDays = "3d"
    OneWeek = "1w"
    OneMonth = "1mo"
```

### Context Manager Pattern

```python
async with DecibelClient(config=MAINNET_CONFIG, bearer_token="...") as client:
    prices = await client.get_prices()
    # WebSocket connections and HTTP pools are automatically cleaned up
```
