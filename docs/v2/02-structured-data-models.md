# Structured Data Models

**Parent**: [00-overview.md](./00-overview.md)

---

This document defines every data type in the Decibel v2 SDK. All models are the canonical source of truth — both the Python and Rust SDKs implement these exactly. Field names use `snake_case` in both JSON wire format and language bindings.

## Design Rules

1. **All models are immutable by default.** Python uses `frozen=True` on Pydantic models. Rust structs are not `mut` by convention; builder patterns are used for construction.
2. **All floating-point fields use `f64`.** No `f32` anywhere — precision matters for financial data.
3. **Nullable fields use `Option<T>` (Rust) or `T | None` (Python).** The JSON wire format uses `null` for absent optional fields.
4. **Timestamps are `i64` Unix milliseconds** unless explicitly noted as seconds.
5. **Addresses are `str` (Python) or `String` (Rust)**, always hex-encoded with `0x` prefix.
6. **Every model exports a JSON Schema** for agent introspection.

---

## Enumerations

### TimeInForce

Controls how long an order remains active.

| Variant | Wire Value | Description |
|---|---|---|
| `GoodTillCanceled` | `0` | Remains on book until filled or canceled |
| `PostOnly` | `1` | Rejected if it would immediately match (maker only) |
| `ImmediateOrCancel` | `2` | Fill what's available immediately, cancel the rest |

### OrderSide

| Variant | Wire Value |
|---|---|
| `Buy` | `true` |
| `Sell` | `false` |

### OrderStatus

| Variant | Description |
|---|---|
| `Acknowledged` | Accepted by matching engine, resting on book |
| `Filled` | Completely filled |
| `PartiallyFilled` | Partially filled, remainder resting |
| `Cancelled` | Cancelled by user or system |
| `Rejected` | Rejected by matching engine |
| `Expired` | Expired (e.g., IOC unfilled portion) |
| `Unknown` | Unrecognized status — forward compatibility |

### TradeAction

| Variant | Description |
|---|---|
| `OpenLong` | Opening a long position |
| `CloseLong` | Closing a long position |
| `OpenShort` | Opening a short position |
| `CloseShort` | Closing a short position |
| `Net` | Net position change (ambiguous direction) |

### CandlestickInterval

| Variant | Wire Value | Duration |
|---|---|---|
| `OneMinute` | `"1m"` | 60s |
| `FiveMinutes` | `"5m"` | 300s |
| `FifteenMinutes` | `"15m"` | 900s |
| `ThirtyMinutes` | `"30m"` | 1800s |
| `OneHour` | `"1h"` | 3600s |
| `TwoHours` | `"2h"` | 7200s |
| `FourHours` | `"4h"` | 14400s |
| `EightHours` | `"8h"` | 28800s |
| `TwelveHours` | `"12h"` | 43200s |
| `OneDay` | `"1d"` | 86400s |
| `ThreeDays` | `"3d"` | 259200s |
| `OneWeek` | `"1w"` | 604800s |
| `OneMonth` | `"1mo"` | ~2592000s |

### VolumeWindow

| Variant | Wire Value |
|---|---|
| `SevenDays` | `"7d"` |
| `FourteenDays` | `"14d"` |
| `ThirtyDays` | `"30d"` |
| `NinetyDays` | `"90d"` |

### SortDirection

| Variant | Wire Value |
|---|---|
| `Ascending` | `"ASC"` |
| `Descending` | `"DESC"` |

### TwapStatus

| Variant | Description |
|---|---|
| `Activated` | Currently executing slices |
| `Finished` | All slices executed |
| `Cancelled` | Cancelled by user |

### VaultType

| Variant | Description |
|---|---|
| `User` | User-created vault |
| `Protocol` | Protocol-managed vault (e.g., DLP) |

### VaultStatus

| Variant | Description |
|---|---|
| `Active` | Accepting contributions and trading |
| `Inactive` | Created but not yet activated |
| `Closed` | No longer accepting contributions |

### MarketMode

| Variant | Description |
|---|---|
| `Open` | Full trading enabled |
| `ReduceOnly` | Only reduce-position orders accepted |
| `CloseOnly` | Only close-position orders accepted |

### MarginMode

| Variant | Description |
|---|---|
| `Cross` | Shared margin across positions |
| `Isolated` | Margin isolated to individual position |

### DepthAggregationLevel

Orderbook price level grouping. The value specifies the multiplier applied to the tick size.

| Value | Description |
|---|---|
| `1` | No aggregation (finest granularity) |
| `2` | 2x tick size grouping |
| `5` | 5x tick size grouping |
| `10` | 10x tick size grouping |
| `100` | 100x tick size grouping |
| `1000` | 1000x tick size grouping |

---

## Market Data Models

### PerpMarketConfig

Complete configuration for a perpetual futures market. Fetched from `GET /api/v1/markets`.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market_addr` | string | NO | On-chain market object address |
| `market_name` | string | NO | Human-readable name (e.g., `"BTC-USD"`) |
| `sz_decimals` | i32 | NO | Size decimal precision (e.g., `9` → 10^9 chain units per 1.0) |
| `px_decimals` | i32 | NO | Price decimal precision (e.g., `9` → 10^9 chain units per 1.0) |
| `max_leverage` | f64 | NO | Maximum leverage multiplier |
| `min_size` | f64 | NO | Minimum order size in chain units |
| `lot_size` | f64 | NO | Order size granularity in chain units |
| `tick_size` | f64 | NO | Price granularity in chain units |
| `max_open_interest` | f64 | NO | Maximum open interest |
| `margin_call_fee_pct` | f64 | NO | Margin call fee as percentage |
| `taker_in_next_block` | bool | NO | Whether taker fills process in next block |

#### Agent Notes

Agents MUST fetch market config before placing orders. The `sz_decimals`, `px_decimals`, `tick_size`, `lot_size`, and `min_size` fields are required for correct price/size formatting. The SDK caches this data and provides helper methods for conversion.

### MarketPrice

Real-time price snapshot for a market.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name or address |
| `mark_px` | f64 | NO | Mark price (used for margin calculations) |
| `mid_px` | f64 | NO | Mid price (average of best bid/ask) |
| `oracle_px` | f64 | NO | Oracle price (external price feed) |
| `funding_rate_bps` | f64 | NO | Current funding rate in basis points |
| `is_funding_positive` | bool | NO | `true` if longs pay shorts |
| `open_interest` | f64 | NO | Total open interest |
| `transaction_unix_ms` | i64 | NO | Timestamp of last price update |

### MarketContext

Extended market context with 24h statistics.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `volume_24h` | f64 | NO | 24-hour trading volume |
| `open_interest` | f64 | NO | Current open interest |
| `previous_day_price` | f64 | NO | Previous day closing price |
| `price_change_pct_24h` | f64 | NO | 24h price change percentage |

### MarketDepth

Orderbook snapshot at a point in time.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `bids` | `Vec<PriceLevel>` | NO | Bid levels, price descending |
| `asks` | `Vec<PriceLevel>` | NO | Ask levels, price ascending |
| `unix_ms` | i64 | NO | Snapshot timestamp |

### PriceLevel

Single price level in the orderbook.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `price` | f64 | NO | Price at this level |
| `size` | f64 | NO | Aggregate size at this level |

### MarketTrade

A single executed trade on the exchange.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `price` | f64 | NO | Execution price |
| `size` | f64 | NO | Trade size |
| `is_buy` | bool | NO | `true` if the taker was a buyer |
| `unix_ms` | i64 | NO | Execution timestamp |

### Candlestick

OHLCV data for a time interval.

| Field | Type | Nullable | JSON Key | Description |
|---|---|---|---|---|
| `open_time` | i64 | NO | `t` | Interval open timestamp |
| `close_time` | i64 | NO | `T` | Interval close timestamp |
| `open` | f64 | NO | `o` | Open price |
| `high` | f64 | NO | `h` | High price |
| `low` | f64 | NO | `l` | Low price |
| `close` | f64 | NO | `c` | Close price |
| `volume` | f64 | NO | `v` | Volume |
| `interval` | string | NO | `i` | Interval string (e.g., `"1m"`) |

#### Agent Notes

The wire format uses single-character keys (`t`, `T`, `o`, `h`, `l`, `c`, `v`, `i`) for compactness. The SDK MUST alias these to readable field names in the typed model while preserving the short keys for serialization via `serde(rename)` / Pydantic `alias`.

---

## Account Models

### AccountOverview

Comprehensive account state including equity, margin, and performance metrics.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `perp_equity_balance` | f64 | NO | Total perpetual equity balance |
| `unrealized_pnl` | f64 | NO | Unrealized profit/loss across all positions |
| `unrealized_funding_cost` | f64 | NO | Unrealized funding cost |
| `cross_margin_ratio` | f64 | NO | Current cross margin ratio |
| `maintenance_margin` | f64 | NO | Maintenance margin requirement |
| `cross_account_leverage_ratio` | f64 | YES | Effective cross-account leverage |
| `cross_account_position` | f64 | NO | Cross account position value |
| `total_margin` | f64 | NO | Total margin used |
| `usdc_cross_withdrawable_balance` | f64 | NO | USDC withdrawable from cross margin |
| `usdc_isolated_withdrawable_balance` | f64 | NO | USDC withdrawable from isolated positions |
| `volume` | f64 | YES | Trading volume (within requested window) |
| `net_deposits` | f64 | YES | Net deposits (deposits minus withdrawals) |
| `realized_pnl` | f64 | YES | Realized PnL |
| `liquidation_fees_paid` | f64 | YES | Liquidation fees paid |
| `liquidation_losses` | f64 | YES | Losses from liquidations |
| `all_time_return` | f64 | YES | All-time return (requires `include_performance`) |
| `pnl_90d` | f64 | YES | 90-day PnL (requires `include_performance`) |
| `sharpe_ratio` | f64 | YES | Sharpe ratio (requires `include_performance`) |
| `max_drawdown` | f64 | YES | Maximum drawdown (requires `include_performance`) |
| `weekly_win_rate_12w` | f64 | YES | 12-week weekly win rate |
| `average_cash_position` | f64 | YES | Average cash position |
| `average_leverage` | f64 | YES | Average leverage |

### UserPosition

An open position on a market.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `user` | string | NO | Subaccount address |
| `size` | f64 | NO | Position size (negative = short) |
| `user_leverage` | f64 | NO | User's leverage setting |
| `entry_price` | f64 | NO | Average entry price |
| `is_isolated` | bool | NO | Whether using isolated margin |
| `unrealized_funding` | f64 | NO | Unrealized funding payments |
| `estimated_liquidation_price` | f64 | NO | Estimated liquidation price |
| `tp_order_id` | string | YES | Take-profit order ID (if set) |
| `tp_trigger_price` | f64 | YES | Take-profit trigger price |
| `tp_limit_price` | f64 | YES | Take-profit limit price |
| `sl_order_id` | string | YES | Stop-loss order ID (if set) |
| `sl_trigger_price` | f64 | YES | Stop-loss trigger price |
| `sl_limit_price` | f64 | YES | Stop-loss limit price |
| `has_fixed_sized_tpsls` | bool | NO | Whether TP/SL orders have fixed sizes |

#### Agent Notes

- `size > 0` means long, `size < 0` means short, `size == 0` means the position is closed.
- The `estimated_liquidation_price` is an approximation — do not use it as a hard guarantee.
- Agents should always check if `tp_order_id` / `sl_order_id` is `None` before attempting updates.

### UserSubaccount

A trading account (subaccount) belonging to an owner.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `subaccount_address` | string | NO | Subaccount on-chain address |
| `primary_account_address` | string | NO | Owner account address |
| `is_primary` | bool | NO | Whether this is the primary subaccount |
| `custom_label` | string | YES | User-assigned label |
| `is_active` | bool | YES | Whether the subaccount is active |

---

## Order Models

### UserOpenOrder

A currently resting order on the orderbook.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `order_id` | string | NO | Exchange-assigned order ID |
| `client_order_id` | string | YES | Client-assigned order ID |
| `price` | f64 | NO | Limit price |
| `orig_size` | f64 | NO | Original order size |
| `remaining_size` | f64 | NO | Remaining unfilled size |
| `is_buy` | bool | NO | `true` for buy, `false` for sell |
| `time_in_force` | string | NO | Time in force (stringified) |
| `is_reduce_only` | bool | NO | Whether reduce-only |
| `status` | string | NO | Current status string |
| `transaction_unix_ms` | i64 | NO | Placement timestamp |
| `transaction_version` | i64 | NO | Aptos transaction version |

### UserOrderHistoryItem

A historical order (filled, cancelled, or expired).

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `client_order_id` | string | YES | Client order ID |
| `price` | f64 | NO | Limit price |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size at terminal state |
| `is_buy` | bool | NO | Buy or sell |
| `time_in_force` | string | NO | Time in force |
| `is_reduce_only` | bool | NO | Reduce only flag |
| `status` | string | NO | Terminal status |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

### OrderStatus

Detailed status of a specific order.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `parent` | string | NO | Parent (owner) account address |
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `status` | string | NO | Current status |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `size_delta` | f64 | NO | Size change in last update |
| `price` | f64 | NO | Order price |
| `is_buy` | bool | NO | Buy or sell |
| `details` | string | NO | Human-readable status details |
| `transaction_version` | i64 | NO | Transaction version |
| `unix_ms` | i64 | NO | Timestamp |

---

## Trade History Models

### UserTradeHistoryItem

A single executed trade for a user.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `account` | string | NO | Account address |
| `market` | string | NO | Market address |
| `action` | TradeAction | NO | Trade action type |
| `size` | f64 | NO | Trade size |
| `price` | f64 | NO | Execution price |
| `is_profit` | bool | NO | Whether the trade was profitable |
| `realized_pnl_amount` | f64 | NO | Realized PnL from this trade |
| `is_funding_positive` | bool | NO | Funding direction |
| `realized_funding_amount` | f64 | NO | Realized funding |
| `is_rebate` | bool | NO | Whether fee was a maker rebate |
| `fee_amount` | f64 | NO | Fee amount |
| `transaction_unix_ms` | i64 | NO | Execution timestamp |
| `transaction_version` | i64 | NO | Transaction version |

### UserFundingHistoryItem

A funding rate payment event.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `funding_rate_bps` | f64 | NO | Funding rate in basis points |
| `is_funding_positive` | bool | NO | `true` if longs pay shorts |
| `funding_amount` | f64 | NO | Amount paid or received |
| `position_size` | f64 | NO | Position size at time of funding |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

### UserFundHistoryItem

A deposit or withdrawal event.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `amount` | f64 | NO | Amount deposited or withdrawn |
| `is_deposit` | bool | NO | `true` for deposit, `false` for withdrawal |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

---

## TWAP Models

### UserActiveTwap

An active or historical TWAP order.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `is_buy` | bool | NO | Buy or sell |
| `order_id` | string | NO | TWAP order ID |
| `client_order_id` | string | NO | Client-assigned order ID |
| `is_reduce_only` | bool | NO | Reduce only flag |
| `start_unix_ms` | i64 | NO | TWAP start timestamp |
| `frequency_s` | i64 | NO | Slice execution frequency in seconds |
| `duration_s` | i64 | NO | Total TWAP duration in seconds |
| `orig_size` | f64 | NO | Original total size |
| `remaining_size` | f64 | NO | Remaining size to execute |
| `status` | TwapStatus | NO | Current TWAP status |
| `transaction_unix_ms` | i64 | NO | Last update timestamp |
| `transaction_version` | i64 | NO | Transaction version |

---

## Delegation Models

### Delegation

A trading delegation from one account to another.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `delegated_account` | string | NO | Account that has been granted trading permission |
| `permission_type` | string | NO | Type of permission granted |
| `expiration_time_s` | i64 | YES | Expiration in Unix seconds (`None` = no expiry) |

---

## Vault Models

### Vault

A trading vault with pooled capital.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `address` | string | NO | Vault on-chain address |
| `name` | string | NO | Vault name |
| `description` | string | YES | Vault description |
| `manager` | string | NO | Manager account address |
| `status` | string | NO | Vault status |
| `created_at` | i64 | NO | Creation timestamp |
| `tvl` | f64 | YES | Total value locked |
| `volume` | f64 | YES | All-time trading volume |
| `volume_30d` | f64 | YES | 30-day volume |
| `all_time_pnl` | f64 | YES | All-time PnL |
| `net_deposits` | f64 | YES | Net deposits |
| `all_time_return` | f64 | YES | All-time return percentage |
| `past_month_return` | f64 | YES | Past month return |
| `sharpe_ratio` | f64 | YES | Sharpe ratio |
| `max_drawdown` | f64 | YES | Maximum drawdown |
| `weekly_win_rate_12w` | f64 | YES | 12-week weekly win rate |
| `profit_share` | f64 | YES | Manager profit share percentage |
| `pnl_90d` | f64 | YES | 90-day PnL |
| `manager_cash_pct` | f64 | YES | Manager cash percentage |
| `average_leverage` | f64 | YES | Average leverage used |
| `depositors` | i64 | YES | Number of depositors |
| `perp_equity` | f64 | YES | Perpetual equity |
| `vault_type` | VaultType | YES | User or Protocol vault |
| `social_links` | `Vec<string>` | YES | Social media links |

### UserOwnedVault

Summary of a vault owned by the user.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `vault_address` | string | NO | Vault address |
| `vault_name` | string | NO | Vault name |
| `vault_share_symbol` | string | NO | Share token symbol |
| `status` | string | NO | Vault status |
| `age_days` | i64 | NO | Vault age in days |
| `num_managers` | i64 | NO | Number of managers |
| `tvl` | f64 | YES | Total value locked |
| `apr` | f64 | YES | Annual percentage rate |
| `manager_equity` | f64 | YES | Manager's equity |
| `manager_stake` | f64 | YES | Manager's stake |

---

## Analytics Models

### LeaderboardItem

A single entry on the trading leaderboard.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `rank` | i64 | NO | Leaderboard rank |
| `account` | string | NO | Account address |
| `account_value` | f64 | NO | Current account value |
| `realized_pnl` | f64 | NO | Realized PnL |
| `roi` | f64 | NO | Return on investment |
| `volume` | f64 | NO | Trading volume |

### PortfolioChartPoint

A single data point in a portfolio time series.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `timestamp` | i64 | NO | Unix timestamp |
| `value` | f64 | NO | Portfolio value at this point |

---

## Transaction Result Models

### PlaceOrderResult

Result of a `place_order` operation.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `success` | bool | NO | Whether the order was placed |
| `order_id` | string | YES | Exchange-assigned order ID (if successful) |
| `transaction_hash` | string | YES | Aptos transaction hash |
| `error` | string | YES | Error message (if failed) |

### TransactionResult

Generic result for any on-chain transaction.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `success` | bool | NO | Whether the transaction succeeded |
| `transaction_hash` | string | NO | Aptos transaction hash |
| `gas_used` | u64 | YES | Gas consumed |
| `vm_status` | string | YES | Move VM status string |
| `events` | `Vec<TransactionEvent>` | YES | Emitted events |

### TransactionEvent

A single event emitted by a transaction.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `type` | string | NO | Event type string |
| `data` | object | NO | Event data (JSON object) |
| `sequence_number` | i64 | NO | Event sequence number |

---

## Pagination and Query Models

### PageParams

Pagination parameters for list endpoints.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | i32 | NO | `10` | Items per page (max 200) |
| `offset` | i32 | NO | `0` | Number of items to skip |

### SortParams

Sorting parameters.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `sort_key` | string | NO | endpoint-specific | Field to sort by |
| `sort_dir` | SortDirection | NO | `Descending` | Sort direction |

### PaginatedResponse\<T\>

Generic paginated response wrapper.

| Field | Type | Description |
|---|---|---|
| `items` | `Vec<T>` | Page of results |
| `total_count` | i64 | Total items matching the query |

---

## WebSocket Message Wrappers

All WebSocket messages arrive in an envelope:

```json
{
  "topic": "<topic_string>",
  "data": { ... }
}
```

### Topic → Payload Mapping

| Topic Pattern | Payload Type | Description |
|---|---|---|
| `account_overview:{addr}` | `AccountOverview` | Account state update |
| `account_positions:{addr}` | `PositionsUpdate` | Position changes |
| `account_open_orders:{addr}` | `OpenOrdersUpdate` | Open order changes |
| `order_updates:{addr}` | `OrderUpdate` | Order status change event |
| `user_trades:{addr}` | `UserTradesUpdate` | Trade execution events |
| `notifications:{addr}` | `NotificationEvent` | System notifications |
| `depth:{addr}` | `MarketDepth` | Orderbook snapshot |
| `depth:{addr}:{level}` | `MarketDepth` | Aggregated orderbook snapshot |
| `market_price:{addr}` | `MarketPrice` | Price update |
| `all_market_prices` | `AllMarketPricesUpdate` | All market prices |
| `trades:{addr}` | `MarketTradesUpdate` | Market trade stream |
| `market_candlestick:{addr}:{interval}` | `CandlestickUpdate` | Candlestick update |
| `bulk_orders:{addr}` | `BulkOrdersUpdate` | Bulk order status |
| `bulk_order_fills:{addr}` | `BulkOrderFillsUpdate` | Bulk order fills |
| `bulk_order_rejections:{addr}` | `BulkOrderRejectionsUpdate` | Bulk order rejections |
| `user_active_twaps:{addr}` | `ActiveTwapsUpdate` | TWAP order updates |

### PositionsUpdate

| Field | Type |
|---|---|
| `positions` | `Vec<UserPosition>` |

### OpenOrdersUpdate

| Field | Type |
|---|---|
| `orders` | `Vec<UserOpenOrder>` |

### OrderUpdate

| Field | Type |
|---|---|
| `order` | `OrderStatus` |

### UserTradesUpdate

| Field | Type |
|---|---|
| `trades` | `Vec<UserTradeHistoryItem>` |

### AllMarketPricesUpdate

| Field | Type |
|---|---|
| `prices` | `Vec<MarketPrice>` |

### MarketTradesUpdate

| Field | Type |
|---|---|
| `trades` | `Vec<MarketTrade>` |

### CandlestickUpdate

| Field | Type |
|---|---|
| `candle` | `Candlestick` |

### NotificationEvent

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | string | NO | Notification ID |
| `type` | string | NO | Notification type |
| `message` | string | NO | Human-readable message |
| `timestamp` | i64 | NO | Timestamp |
| `read` | bool | NO | Whether the notification has been read |

---

## Configuration Models

### DecibelConfig

SDK configuration. See [03-python-sdk.md](./03-python-sdk.md) and [04-rust-sdk.md](./04-rust-sdk.md) for language-specific construction.

| Field | Type | Required | Description |
|---|---|---|---|
| `network` | NetworkType | YES | `Mainnet`, `Testnet`, `Devnet`, `Custom` |
| `fullnode_url` | string | YES | Aptos fullnode RPC URL |
| `trading_http_url` | string | YES | Decibel REST API base URL |
| `trading_ws_url` | string | YES | Decibel WebSocket URL |
| `gas_station_url` | string | NO | Gas station URL for sponsored transactions |
| `gas_station_api_key` | string | NO | API key for gas station |
| `deployment` | Deployment | YES | Smart contract addresses |
| `chain_id` | u8 | NO | Override chain ID (auto-detected if absent) |
| `compat_version` | string | YES | Protocol compatibility version (`"v0.4"`) |

### Deployment

Smart contract deployment addresses.

| Field | Type | Required | Description |
|---|---|---|---|
| `package` | string | YES | Published Move package address |
| `usdc` | string | YES | USDC token address |
| `testc` | string | YES | Test collateral address |
| `perp_engine_global` | string | YES | Global perp engine object address |

### Preset Configurations

| Preset | Network | Description |
|---|---|---|
| `MAINNET_CONFIG` | Mainnet | Production environment |
| `TESTNET_CONFIG` | Testnet | Testnet with free funds |
| `DEVNET_CONFIG` | Devnet | Development environment |

#### Mainnet Contract Addresses

```
package: "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06"
```

#### Testnet Contract Addresses

```
package: "0x952535c3049e52f195f26798c2f1340d7dd5100edbe0f464e520a974d16fbe9f"
```
