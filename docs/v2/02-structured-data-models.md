# Structured Data Models

**Parent**: [00-overview.md](./00-overview.md)

---

This document defines every data type in the v2 SDK. Beyond the raw API fields, the v2 models include **computed fields** that bots need for decision-making — margin ratios, liquidation distance, funding accrual rates, and net exposure.

## Design Rules

1. **All models are immutable.** Python: `frozen=True`. Rust: not `mut` by convention.
2. **All floating-point fields use `f64`.** Financial precision requires it.
3. **Nullable fields use `Option<T>` / `T | None`.** Wire format uses `null`.
4. **Timestamps are `i64` Unix milliseconds** unless noted as seconds.
5. **Addresses are `String`**, hex with `0x` prefix.
6. **Every model exports JSON Schema** for LLM agent introspection.
7. **Computed fields are methods, not stored fields** — they derive from the raw data plus context (e.g., current mark price).

---

## Enumerations

### TimeInForce

| Variant | Wire Value | Bot Usage |
|---|---|---|
| `GoodTillCanceled` | `0` | Resting limit orders for market making |
| `PostOnly` | `1` | Maker-only orders; rejected if they would take. Used in bulk orders always |
| `ImmediateOrCancel` | `2` | Aggressive execution; unfilled portion cancelled. Used for market orders |

### OrderStatus

| Variant | Description | Bot Action |
|---|---|---|
| `Acknowledged` | Accepted, resting on book | Track; may fill later |
| `Filled` | Completely filled | Update position state, log P&L |
| `PartiallyFilled` | Some filled, remainder resting | Update partial fill, continue tracking |
| `Cancelled` | Cancelled by user or system | Remove from active orders |
| `Rejected` | Rejected by matching engine | Log reason; do not retry without fix |
| `Expired` | Timed out (IOC unfilled portion) | Log; position may be partially updated |
| `Unknown` | Forward-compatibility | Log and investigate |

### TradeAction

| Variant | Position Effect |
|---|---|
| `OpenLong` | Increases long exposure |
| `CloseLong` | Decreases long exposure |
| `OpenShort` | Increases short exposure |
| `CloseShort` | Decreases short exposure |
| `Net` | Ambiguous direction change |

### CandlestickInterval

| Variant | Wire | Seconds |
|---|---|---|
| `OneMinute` | `"1m"` | 60 |
| `FiveMinutes` | `"5m"` | 300 |
| `FifteenMinutes` | `"15m"` | 900 |
| `ThirtyMinutes` | `"30m"` | 1800 |
| `OneHour` | `"1h"` | 3600 |
| `TwoHours` | `"2h"` | 7200 |
| `FourHours` | `"4h"` | 14400 |
| `EightHours` | `"8h"` | 28800 |
| `TwelveHours` | `"12h"` | 43200 |
| `OneDay` | `"1d"` | 86400 |
| `ThreeDays` | `"3d"` | 259200 |
| `OneWeek` | `"1w"` | 604800 |
| `OneMonth` | `"1mo"` | ~2592000 |

### VolumeWindow

| Variant | Wire |
|---|---|
| `SevenDays` | `"7d"` |
| `FourteenDays` | `"14d"` |
| `ThirtyDays` | `"30d"` |
| `NinetyDays` | `"90d"` |

### SortDirection

| Variant | Wire |
|---|---|
| `Ascending` | `"ASC"` |
| `Descending` | `"DESC"` |

### TwapStatus

| Variant | Description |
|---|---|
| `Activated` | Executing slices |
| `Finished` | All slices done |
| `Cancelled` | Cancelled |

### VaultType

| Variant |
|---|
| `User` |
| `Protocol` |

### MarginMode

| Variant |
|---|
| `Cross` |
| `Isolated` |

### DepthAggregationLevel

Values: `1`, `2`, `5`, `10`, `100`, `1000`

---

## Market Data Models

### PerpMarketConfig

Market configuration. **Must be cached by the bot** — needed for every order placement.

| Field | Type | Description |
|---|---|---|
| `market_addr` | string | On-chain market object address |
| `market_name` | string | Human-readable name (e.g., `"BTC-USD"`) |
| `sz_decimals` | i32 | Size precision (chain units = value × 10^sz_decimals) |
| `px_decimals` | i32 | Price precision (chain units = value × 10^px_decimals) |
| `max_leverage` | f64 | Maximum leverage multiplier |
| `min_size` | f64 | Minimum order size in **chain units** |
| `lot_size` | f64 | Size granularity in **chain units** |
| `tick_size` | f64 | Price granularity in **chain units** |
| `max_open_interest` | f64 | Maximum open interest |
| `margin_call_fee_pct` | f64 | Liquidation fee percentage |
| `taker_in_next_block` | bool | Whether taker fills process in next block |

#### Computed Methods

```python
def min_size_decimal(self) -> float:
    """Minimum order size in human-readable units."""
    return self.min_size / (10 ** self.sz_decimals)

def lot_size_decimal(self) -> float:
    """Lot size in human-readable units."""
    return self.lot_size / (10 ** self.sz_decimals)

def tick_size_decimal(self) -> float:
    """Tick size in human-readable units."""
    return self.tick_size / (10 ** self.px_decimals)

def mm_fraction(self) -> float:
    """Maintenance margin fraction: 1 / (max_leverage * 2)."""
    return 1.0 / (self.max_leverage * 2)
```

### MarketPrice

Real-time price snapshot. Most frequently consumed model in any bot.

| Field | Type | Description |
|---|---|---|
| `market` | string | Market name or address |
| `mark_px` | f64 | Mark price (margin calculations, P&L) |
| `mid_px` | f64 | Mid price (average best bid/ask) |
| `oracle_px` | f64 | Oracle price (external feed) |
| `funding_rate_bps` | f64 | Current funding rate in basis points |
| `is_funding_positive` | bool | `true` = longs pay shorts |
| `open_interest` | f64 | Total open interest |
| `transaction_unix_ms` | i64 | Last update timestamp |

#### Computed Methods

```python
def funding_rate_hourly(self) -> float:
    """Annualized funding rate as hourly percentage."""
    return self.funding_rate_bps / 10000 * 365 * 24

def spread_bps(self, depth: MarketDepth) -> float | None:
    """Spread in basis points given orderbook depth."""
    if not depth.bids or not depth.asks:
        return None
    return (depth.asks[0].price - depth.bids[0].price) / self.mid_px * 10000

def funding_direction(self) -> str:
    """'longs_pay' or 'shorts_pay'."""
    return "longs_pay" if self.is_funding_positive else "shorts_pay"
```

### MarketContext

24h statistics.

| Field | Type | Description |
|---|---|---|
| `market` | string | Market name |
| `volume_24h` | f64 | 24h volume |
| `open_interest` | f64 | Current OI |
| `previous_day_price` | f64 | Previous day close |
| `price_change_pct_24h` | f64 | 24h price change % |

### MarketDepth

Orderbook snapshot.

| Field | Type | Description |
|---|---|---|
| `market` | string | Market name |
| `bids` | `Vec<PriceLevel>` | Bid levels (price descending) |
| `asks` | `Vec<PriceLevel>` | Ask levels (price ascending) |
| `unix_ms` | i64 | Snapshot timestamp |

#### Computed Methods

```python
def best_bid(self) -> float | None:
    return self.bids[0].price if self.bids else None

def best_ask(self) -> float | None:
    return self.asks[0].price if self.asks else None

def spread(self) -> float | None:
    b, a = self.best_bid(), self.best_ask()
    return (a - b) if b is not None and a is not None else None

def mid_price(self) -> float | None:
    b, a = self.best_bid(), self.best_ask()
    return (a + b) / 2 if b is not None and a is not None else None

def bid_depth_at(self, percent_from_mid: float) -> float:
    """Total bid size within `percent_from_mid`% of mid price."""
    mid = self.mid_price()
    if mid is None:
        return 0.0
    threshold = mid * (1 - percent_from_mid / 100)
    return sum(l.size for l in self.bids if l.price >= threshold)

def ask_depth_at(self, percent_from_mid: float) -> float:
    """Total ask size within `percent_from_mid`% of mid price."""
    mid = self.mid_price()
    if mid is None:
        return 0.0
    threshold = mid * (1 + percent_from_mid / 100)
    return sum(l.size for l in self.asks if l.price <= threshold)

def imbalance(self) -> float | None:
    """Bid/ask imbalance: (bid_volume - ask_volume) / (bid_volume + ask_volume).
    Positive = more bids (buy pressure). Range [-1, 1]."""
    bid_vol = sum(l.size for l in self.bids)
    ask_vol = sum(l.size for l in self.asks)
    total = bid_vol + ask_vol
    return (bid_vol - ask_vol) / total if total > 0 else None
```

### PriceLevel

| Field | Type | Description |
|---|---|---|
| `price` | f64 | Price at this level |
| `size` | f64 | Aggregate size |

### MarketTrade

| Field | Type | Description |
|---|---|---|
| `market` | string | Market name |
| `price` | f64 | Execution price |
| `size` | f64 | Trade size |
| `is_buy` | bool | Taker was buyer |
| `unix_ms` | i64 | Timestamp |

### Candlestick

OHLCV data. Wire uses single-char keys; SDK uses readable names with serde aliases.

| Field | Type | Wire Key | Description |
|---|---|---|---|
| `open_time` | i64 | `t` | Interval start |
| `close_time` | i64 | `T` | Interval end |
| `open` | f64 | `o` | Open price |
| `high` | f64 | `h` | High price |
| `low` | f64 | `l` | Low price |
| `close` | f64 | `c` | Close price |
| `volume` | f64 | `v` | Volume |
| `interval` | string | `i` | Interval string |

#### Computed Methods

```python
def body_pct(self) -> float:
    """Body size as % of open. Positive = bullish."""
    return (self.close - self.open) / self.open * 100 if self.open != 0 else 0

def range_pct(self) -> float:
    """High-low range as % of open."""
    return (self.high - self.low) / self.open * 100 if self.open != 0 else 0

def is_bullish(self) -> bool:
    return self.close >= self.open
```

---

## Account Models

### AccountOverview

Comprehensive account state. The most important model for risk management.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `perp_equity_balance` | f64 | NO | Total equity (collateral + unrealized P&L) |
| `unrealized_pnl` | f64 | NO | Unrealized P&L from mark-to-market |
| `unrealized_funding_cost` | f64 | NO | Unrealized funding accrual |
| `cross_margin_ratio` | f64 | NO | Current cross margin ratio |
| `maintenance_margin` | f64 | NO | Maintenance margin requirement |
| `cross_account_leverage_ratio` | f64 | YES | Effective leverage |
| `cross_account_position` | f64 | NO | Cross account position value |
| `total_margin` | f64 | NO | Total margin used |
| `usdc_cross_withdrawable_balance` | f64 | NO | Withdrawable from cross |
| `usdc_isolated_withdrawable_balance` | f64 | NO | Withdrawable from isolated |
| `volume` | f64 | YES | Trading volume (per window) |
| `net_deposits` | f64 | YES | Net deposits |
| `realized_pnl` | f64 | YES | Realized P&L |
| `liquidation_fees_paid` | f64 | YES | Liquidation fees paid |
| `liquidation_losses` | f64 | YES | Losses from liquidations |
| `all_time_return` | f64 | YES | All-time return % |
| `pnl_90d` | f64 | YES | 90-day P&L |
| `sharpe_ratio` | f64 | YES | Sharpe ratio |
| `max_drawdown` | f64 | YES | Maximum drawdown |
| `weekly_win_rate_12w` | f64 | YES | 12-week win rate |
| `average_cash_position` | f64 | YES | Average cash |
| `average_leverage` | f64 | YES | Average leverage |

#### Computed Methods

```python
def margin_usage_pct(self) -> float:
    """Percentage of equity used as margin. 100% = fully utilized."""
    if self.perp_equity_balance == 0:
        return 0.0
    return (self.total_margin / self.perp_equity_balance) * 100

def liquidation_buffer_usd(self) -> float:
    """USD between current equity and maintenance margin."""
    return self.perp_equity_balance - self.maintenance_margin

def liquidation_buffer_pct(self) -> float:
    """Percentage buffer above maintenance margin."""
    if self.maintenance_margin == 0:
        return float('inf')
    return (self.perp_equity_balance / self.maintenance_margin - 1) * 100

def is_liquidation_warning(self, threshold_pct: float = 50.0) -> bool:
    """True if within `threshold_pct` of liquidation."""
    return self.liquidation_buffer_pct() < threshold_pct

def total_withdrawable(self) -> float:
    """Total withdrawable USDC across cross and isolated."""
    return self.usdc_cross_withdrawable_balance + self.usdc_isolated_withdrawable_balance
```

### UserPosition

Open position. Core state for any bot.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `user` | string | NO | Subaccount address |
| `size` | f64 | NO | Position size (negative = short) |
| `user_leverage` | f64 | NO | Leverage setting |
| `entry_price` | f64 | NO | Average entry price |
| `is_isolated` | bool | NO | Isolated margin mode |
| `unrealized_funding` | f64 | NO | Unrealized funding |
| `estimated_liquidation_price` | f64 | NO | Est. liquidation price |
| `tp_order_id` | string | YES | Take-profit order ID |
| `tp_trigger_price` | f64 | YES | TP trigger price |
| `tp_limit_price` | f64 | YES | TP limit price |
| `sl_order_id` | string | YES | Stop-loss order ID |
| `sl_trigger_price` | f64 | YES | SL trigger price |
| `sl_limit_price` | f64 | YES | SL limit price |
| `has_fixed_sized_tpsls` | bool | NO | TP/SL have fixed sizes |

#### Computed Methods

```python
def is_long(self) -> bool:
    return self.size > 0

def is_short(self) -> bool:
    return self.size < 0

def is_flat(self) -> bool:
    return self.size == 0

def direction(self) -> str:
    if self.size > 0: return "long"
    if self.size < 0: return "short"
    return "flat"

def notional(self, mark_price: float) -> float:
    """Position notional value at current mark price."""
    return abs(self.size) * mark_price

def unrealized_pnl(self, mark_price: float) -> float:
    """Unrealized P&L excluding funding."""
    return (mark_price - self.entry_price) * self.size

def unrealized_pnl_pct(self, mark_price: float) -> float:
    """Unrealized P&L as percentage of entry notional."""
    entry_notional = abs(self.size) * self.entry_price
    if entry_notional == 0:
        return 0.0
    return self.unrealized_pnl(mark_price) / entry_notional * 100

def total_unrealized_pnl(self, mark_price: float) -> float:
    """Unrealized P&L including funding."""
    return self.unrealized_pnl(mark_price) + self.unrealized_funding

def liquidation_distance_pct(self, mark_price: float) -> float:
    """Percentage distance from current price to estimated liquidation."""
    if self.estimated_liquidation_price == 0 or mark_price == 0:
        return float('inf')
    return abs(mark_price - self.estimated_liquidation_price) / mark_price * 100

def has_tp(self) -> bool:
    return self.tp_order_id is not None

def has_sl(self) -> bool:
    return self.sl_order_id is not None

def has_protection(self) -> bool:
    """True if position has both TP and SL."""
    return self.has_tp() and self.has_sl()
```

### UserSubaccount

| Field | Type | Nullable | Description |
|---|---|---|---|
| `subaccount_address` | string | NO | Subaccount address |
| `primary_account_address` | string | NO | Owner address |
| `is_primary` | bool | NO | Is primary subaccount |
| `custom_label` | string | YES | User label |
| `is_active` | bool | YES | Active status |

---

## Order Models

### UserOpenOrder

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `order_id` | string | NO | Exchange order ID |
| `client_order_id` | string | YES | Client order ID |
| `price` | f64 | NO | Limit price |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `is_buy` | bool | NO | Buy side |
| `time_in_force` | string | NO | TIF type |
| `is_reduce_only` | bool | NO | Reduce only |
| `status` | string | NO | Status |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Tx version |

#### Computed Methods

```python
def filled_size(self) -> float:
    return self.orig_size - self.remaining_size

def fill_pct(self) -> float:
    if self.orig_size == 0:
        return 0.0
    return (self.filled_size() / self.orig_size) * 100

def side(self) -> str:
    return "buy" if self.is_buy else "sell"

def notional(self) -> float:
    """Order notional = remaining_size × price."""
    return self.remaining_size * self.price

def age_ms(self, now_ms: int) -> int:
    """Milliseconds since order was placed."""
    return now_ms - self.transaction_unix_ms
```

### OrderStatus

Detailed status from `GET /orders`.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `parent` | string | NO | Owner address |
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `status` | string | NO | Current status |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `size_delta` | f64 | NO | Size change |
| `price` | f64 | NO | Price |
| `is_buy` | bool | NO | Buy/sell |
| `details` | string | NO | Status details |
| `transaction_version` | i64 | NO | Tx version |
| `unix_ms` | i64 | NO | Timestamp |

### PlaceOrderResult

| Field | Type | Nullable | Description |
|---|---|---|---|
| `success` | bool | NO | Order was placed |
| `order_id` | string | YES | Exchange order ID |
| `transaction_hash` | string | YES | Tx hash |
| `error` | string | YES | Error message |

### TransactionResult

| Field | Type | Nullable | Description |
|---|---|---|---|
| `success` | bool | NO | Tx succeeded |
| `transaction_hash` | string | NO | Tx hash |
| `gas_used` | u64 | YES | Gas consumed |
| `vm_status` | string | YES | VM status |

---

## History Models

### UserTradeHistoryItem

| Field | Type | Description |
|---|---|---|
| `account` | string | Account address |
| `market` | string | Market address |
| `action` | TradeAction | Trade action |
| `size` | f64 | Trade size |
| `price` | f64 | Execution price |
| `is_profit` | bool | Profitable trade |
| `realized_pnl_amount` | f64 | Realized P&L |
| `is_funding_positive` | bool | Funding direction |
| `realized_funding_amount` | f64 | Realized funding |
| `is_rebate` | bool | Fee was maker rebate |
| `fee_amount` | f64 | Fee amount |
| `transaction_unix_ms` | i64 | Timestamp |
| `transaction_version` | i64 | Tx version |

#### Computed Methods

```python
def net_pnl(self) -> float:
    """Net P&L after fees and funding."""
    pnl = self.realized_pnl_amount
    fee = -self.fee_amount if not self.is_rebate else self.fee_amount
    funding = self.realized_funding_amount if not self.is_funding_positive else -self.realized_funding_amount
    return pnl + fee + funding

def notional(self) -> float:
    return self.size * self.price
```

### UserFundingHistoryItem

| Field | Type | Description |
|---|---|---|
| `market` | string | Market address |
| `funding_rate_bps` | f64 | Funding rate bps |
| `is_funding_positive` | bool | Direction |
| `funding_amount` | f64 | Amount |
| `position_size` | f64 | Position at time |
| `transaction_unix_ms` | i64 | Timestamp |
| `transaction_version` | i64 | Tx version |

### UserFundHistoryItem

| Field | Type | Description |
|---|---|---|
| `amount` | f64 | Amount |
| `is_deposit` | bool | Deposit or withdrawal |
| `transaction_unix_ms` | i64 | Timestamp |
| `transaction_version` | i64 | Tx version |

---

## TWAP Models

### UserActiveTwap

| Field | Type | Description |
|---|---|---|
| `market` | string | Market address |
| `is_buy` | bool | Direction |
| `order_id` | string | TWAP order ID |
| `client_order_id` | string | Client ID |
| `is_reduce_only` | bool | Reduce only |
| `start_unix_ms` | i64 | Start timestamp |
| `frequency_s` | i64 | Slice frequency (seconds) |
| `duration_s` | i64 | Total duration (seconds) |
| `orig_size` | f64 | Original size |
| `remaining_size` | f64 | Remaining |
| `status` | TwapStatus | Status |
| `transaction_unix_ms` | i64 | Last update |
| `transaction_version` | i64 | Tx version |

#### Computed Methods

```python
def progress_pct(self) -> float:
    if self.orig_size == 0:
        return 0.0
    return (1 - self.remaining_size / self.orig_size) * 100

def estimated_completion_ms(self) -> int | None:
    if self.status != TwapStatus.Activated:
        return None
    return self.start_unix_ms + self.duration_s * 1000

def elapsed_pct(self, now_ms: int) -> float:
    elapsed = now_ms - self.start_unix_ms
    return min(elapsed / (self.duration_s * 1000) * 100, 100.0)
```

---

## Bulk Order Models

### BulkOrderSet

Represents the current bulk order state for a market.

| Field | Type | Description |
|---|---|---|
| `market` | string | Market address |
| `sequence_number` | u64 | Current sequence number |
| `bid_prices` | `Vec<f64>` | Bid prices |
| `bid_sizes` | `Vec<f64>` | Bid sizes |
| `ask_prices` | `Vec<f64>` | Ask prices |
| `ask_sizes` | `Vec<f64>` | Ask sizes |

### BulkOrderFill

| Field | Type | Description |
|---|---|---|
| `market` | string | Market address |
| `is_buy` | bool | Fill side |
| `price` | f64 | Fill price |
| `size` | f64 | Fill size |
| `sequence_number` | u64 | Bulk order sequence |
| `unix_ms` | i64 | Fill timestamp |

---

## Delegation Models

### Delegation

| Field | Type | Nullable | Description |
|---|---|---|---|
| `delegated_account` | string | NO | Delegated address |
| `permission_type` | string | NO | Permission type |
| `expiration_time_s` | i64 | YES | Expiry (Unix seconds) |

---

## Vault Models

### Vault

| Field | Type | Nullable | Description |
|---|---|---|---|
| `address` | string | NO | Vault address |
| `name` | string | NO | Name |
| `description` | string | YES | Description |
| `manager` | string | NO | Manager address |
| `status` | string | NO | Status |
| `created_at` | i64 | NO | Creation timestamp |
| `tvl` | f64 | YES | Total value locked |
| `volume` | f64 | YES | All-time volume |
| `volume_30d` | f64 | YES | 30d volume |
| `all_time_pnl` | f64 | YES | All-time P&L |
| `net_deposits` | f64 | YES | Net deposits |
| `all_time_return` | f64 | YES | All-time return % |
| `past_month_return` | f64 | YES | Month return % |
| `sharpe_ratio` | f64 | YES | Sharpe |
| `max_drawdown` | f64 | YES | Max drawdown |
| `weekly_win_rate_12w` | f64 | YES | Win rate |
| `profit_share` | f64 | YES | Manager profit share % |
| `pnl_90d` | f64 | YES | 90d P&L |
| `manager_cash_pct` | f64 | YES | Cash % |
| `average_leverage` | f64 | YES | Avg leverage |
| `depositors` | i64 | YES | Depositor count |
| `perp_equity` | f64 | YES | Perp equity |
| `vault_type` | VaultType | YES | User/Protocol |
| `social_links` | `Vec<string>` | YES | Links |

### UserOwnedVault

| Field | Type | Nullable | Description |
|---|---|---|---|
| `vault_address` | string | NO | Address |
| `vault_name` | string | NO | Name |
| `vault_share_symbol` | string | NO | Share symbol |
| `status` | string | NO | Status |
| `age_days` | i64 | NO | Age |
| `num_managers` | i64 | NO | Manager count |
| `tvl` | f64 | YES | TVL |
| `apr` | f64 | YES | APR |
| `manager_equity` | f64 | YES | Manager equity |
| `manager_stake` | f64 | YES | Manager stake |

---

## Analytics Models

### LeaderboardItem

| Field | Type | Description |
|---|---|---|
| `rank` | i64 | Rank |
| `account` | string | Address |
| `account_value` | f64 | Value |
| `realized_pnl` | f64 | Realized P&L |
| `roi` | f64 | ROI |
| `volume` | f64 | Volume |

### PortfolioChartPoint

| Field | Type | Description |
|---|---|---|
| `timestamp` | i64 | Timestamp |
| `value` | f64 | Portfolio value |

---

## Pagination

### PageParams

| Field | Type | Default | Description |
|---|---|---|---|
| `limit` | i32 | `10` | Items per page (max 200) |
| `offset` | i32 | `0` | Offset |

### SortParams

| Field | Type | Default |
|---|---|---|
| `sort_key` | string | endpoint-specific |
| `sort_dir` | SortDirection | `Descending` |

### PaginatedResponse\<T\>

| Field | Type | Description |
|---|---|---|
| `items` | `Vec<T>` | Page of results |
| `total_count` | i64 | Total matching |

---

## WebSocket Envelope

```json
{"topic": "<topic_string>", "data": { ... }}
```

### Topic → Payload Mapping

| Topic | Payload |
|---|---|
| `account_overview:{addr}` | `AccountOverview` |
| `account_positions:{addr}` | `{ positions: Vec<UserPosition> }` |
| `account_open_orders:{addr}` | `{ orders: Vec<UserOpenOrder> }` |
| `order_updates:{addr}` | `OrderStatus` |
| `user_trades:{addr}` | `{ trades: Vec<UserTradeHistoryItem> }` |
| `notifications:{addr}` | `NotificationEvent` |
| `depth:{addr}` | `MarketDepth` |
| `depth:{addr}:{level}` | `MarketDepth` (aggregated) |
| `market_price:{addr}` | `MarketPrice` |
| `all_market_prices` | `{ prices: Vec<MarketPrice> }` |
| `trades:{addr}` | `{ trades: Vec<MarketTrade> }` |
| `market_candlestick:{addr}:{interval}` | `{ candle: Candlestick }` |
| `bulk_orders:{addr}` | Bulk order update |
| `bulk_order_fills:{addr}` | Bulk fill update |
| `bulk_order_rejections:{addr}` | Bulk rejection update |
| `user_active_twaps:{addr}` | TWAP update |

---

## Configuration Models

### DecibelConfig

| Field | Type | Required | Description |
|---|---|---|---|
| `network` | enum | YES | `Mainnet`, `Testnet`, `Devnet`, `Custom` |
| `fullnode_url` | string | YES | Aptos fullnode RPC |
| `trading_http_url` | string | YES | REST API base |
| `trading_ws_url` | string | YES | WebSocket URL |
| `gas_station_url` | string | NO | Gas station URL |
| `gas_station_api_key` | string | NO | Gas station key |
| `deployment` | Deployment | YES | Contract addresses |
| `chain_id` | u8 | NO | Override chain ID |
| `compat_version` | string | YES | Protocol version (`"v0.4"`) |

### Deployment

| Field | Type | Required | Description |
|---|---|---|---|
| `package` | string | YES | Move package address |
| `usdc` | string | YES | USDC token address |
| `testc` | string | YES | Test collateral address |
| `perp_engine_global` | string | YES | Global perp engine address |

### Presets

| Preset | Network |
|---|---|
| `MAINNET_CONFIG` | Production |
| `TESTNET_CONFIG` | Testnet (free funds) |
| `DEVNET_CONFIG` | Development |
