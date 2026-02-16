# Decibel Cross-Platform SDK Specification

**Version**: 1.0.0 (Iteration 5 - Final)
**Date**: 2026-02-16
**Target Languages**: Rust, Swift, Kotlin, Go
**Reference Implementation**: `@decibeltrade/sdk` v0.3.1 (TypeScript)

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [SDK Architecture](#2-sdk-architecture)
3. [Configuration & Initialization](#3-configuration--initialization)
4. [Data Types & Models](#4-data-types--models)
5. [REST API Client](#5-rest-api-client)
6. [WebSocket Client](#6-websocket-client)
7. [On-Chain Transaction Builder](#7-on-chain-transaction-builder)
8. [Write Operations (Trading)](#8-write-operations-trading)
9. [Read Operations (Market Data)](#9-read-operations-market-data)
10. [Error Handling](#10-error-handling)
11. [Utility Functions](#11-utility-functions)
12. [Performance Requirements](#12-performance-requirements)
13. [Language-Specific Idioms](#13-language-specific-idioms)

---

## 1. Platform Overview

Decibel is a **fully on-chain perpetual futures exchange** built on the **Aptos blockchain**. The platform provides:

- **Perpetual futures trading** with cross and isolated margin modes
- **CLOB (Central Limit Order Book)** matching engine
- **Multi-collateral support** (primarily USDC)
- **Subaccount system** for position isolation
- **Vault system** for fund management
- **TWAP (Time-Weighted Average Price)** order support
- **Bulk order** support for market makers
- **Trading delegation** for automated strategies
- **Builder fee** system for frontend integrators

### Blockchain Details
- **Chain**: Aptos (Move-based)
- **Smart Contracts**: Published as Move packages
- **Transaction Type**: Entry function calls via Aptos SDK
- **Fee Model**: Gas station (sponsored transactions) or self-paid
- **Oracle**: Pyth, Chainlink, Internal composite oracles

### API Architecture
- **REST API**: `https://{tradingHttpUrl}/api/v1/...` for read operations
- **WebSocket API**: `wss://{tradingWsUrl}/ws` for real-time streaming
- **On-Chain**: Direct Aptos transaction submission for write operations
- **Authentication**: API key header (`x-api-key`) for REST/WS, Ed25519 private key signing for on-chain

---

## 2. SDK Architecture

### 2.1 Module Structure (REQUIRED)

Each SDK MUST implement the following module structure:

```
decibel-sdk/
  ├── config/           # Configuration types and presets
  ├── models/           # All data type definitions
  ├── client/
  │   ├── read/         # DecibelReadClient (REST + WS subscriptions)
  │   ├── write/        # DecibelWriteClient (on-chain transactions)
  │   └── ws/           # WebSocket connection manager
  ├── transaction/      # Transaction builder and signer
  ├── gas/              # Gas price manager
  ├── utils/            # Utility functions (address derivation, etc.)
  └── errors/           # Error types and handling
```

### 2.2 Primary Entry Points (REQUIRED)

| Entry Point | Purpose | Auth Required |
|---|---|---|
| `DecibelReadClient` | Market data queries, account state, WS subscriptions | API Key (optional but recommended) |
| `DecibelWriteClient` | Place/cancel orders, manage subaccounts, vaults, delegation | Ed25519 Private Key (REQUIRED) |

### 2.3 Separation of Concerns (REQUIRED)

- **Read Client**: No private key required. Reads via REST API and WebSocket subscriptions.
- **Write Client**: Requires an Aptos account (Ed25519 keypair). Builds, signs, and submits on-chain transactions.
- Both clients share the same `DecibelConfig` configuration.

---

## 3. Configuration & Initialization

### 3.1 DecibelConfig (REQUIRED)

Every SDK MUST define this configuration structure:

| Field | Type | Required | Description |
|---|---|---|---|
| `network` | enum | YES | Aptos network: `Mainnet`, `Testnet`, `Devnet`, `Custom` |
| `fullnode_url` | string | YES | Aptos fullnode RPC URL |
| `trading_http_url` | string | YES | Decibel REST API base URL |
| `trading_ws_url` | string | YES | Decibel WebSocket URL |
| `gas_station_url` | string | NO | Gas station URL for sponsored transactions |
| `gas_station_api_key` | string | NO | API key for Aptos Labs Gas Station |
| `deployment` | Deployment | YES | Smart contract deployment addresses |
| `chain_id` | u8 | NO | Override chain ID (auto-detected if not provided) |
| `compat_version` | string | YES | SDK compatibility version (currently `"v0.4"`) |

### 3.2 Deployment (REQUIRED)

| Field | Type | Required | Description |
|---|---|---|---|
| `package` | string (hex address) | YES | Published Move package address |
| `usdc` | string (hex address) | YES | USDC token address |
| `testc` | string (hex address) | YES | Test collateral address |
| `perp_engine_global` | string (hex address) | YES | Global perp engine object address |

### 3.3 Preset Configurations (REQUIRED)

Each SDK MUST provide these preset configurations:

| Preset | Network | Description |
|---|---|---|
| `MAINNET_CONFIG` | Mainnet | Production environment |
| `TESTNET_CONFIG` | Testnet | Testnet environment |
| `NETNA_CONFIG` | Custom (Devnet) | Netna devnet environment |
| `LOCAL_CONFIG` | Local | Local development |
| `DOCKER_CONFIG` | Custom | Docker development environment |

#### Mainnet Deployment Addresses (REQUIRED)
```
package: "0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d"
usdc: "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b"
testc: "0x..."
perp_engine_global: "0x..."
```

#### Testnet Deployment Addresses (REQUIRED)
```
package: "0x..."
usdc: "0x..."
testc: "0x..."
perp_engine_global: "0x..."
```

### 3.4 ReadClient Constructor Options (REQUIRED)

| Option | Type | Required | Description |
|---|---|---|---|
| `config` | DecibelConfig | YES | SDK configuration |
| `node_api_key` | string | NO | Aptos node API key for higher rate limits |
| `on_ws_error` | callback | NO | WebSocket error handler |

### 3.5 WriteClient Constructor Options (REQUIRED)

| Option | Type | Required | Description |
|---|---|---|---|
| `config` | DecibelConfig | YES | SDK configuration |
| `account` | Ed25519Account | YES | Signing account with private key |
| `skip_simulate` | bool | NO | Skip transaction simulation (default: false) |
| `no_fee_payer` | bool | NO | Disable gas station/fee payer (default: false) |
| `node_api_key` | string | NO | Aptos node API key |
| `gas_price_manager` | GasPriceManager | NO | Custom gas price manager |
| `time_delta_ms` | i64 | NO | Clock drift compensation in milliseconds |

---

## 4. Data Types & Models

### 4.1 Enumerations (REQUIRED)

#### 4.1.1 TimeInForce
| Variant | Value | Description |
|---|---|---|
| `GoodTillCanceled` | 0 | Order remains on book until filled or canceled |
| `PostOnly` | 1 | Order rejected if it would immediately match |
| `ImmediateOrCancel` | 2 | Fill what's possible immediately, cancel the rest |

#### 4.1.2 CandlestickInterval
| Variant | String Value |
|---|---|
| `OneMinute` | `"1m"` |
| `FiveMinutes` | `"5m"` |
| `FifteenMinutes` | `"15m"` |
| `ThirtyMinutes` | `"30m"` |
| `OneHour` | `"1h"` |
| `TwoHours` | `"2h"` |
| `FourHours` | `"4h"` |
| `EightHours` | `"8h"` |
| `TwelveHours` | `"12h"` |
| `OneDay` | `"1d"` |
| `ThreeDays` | `"3d"` |
| `OneWeek` | `"1w"` |
| `OneMonth` | `"1mo"` |

#### 4.1.3 VolumeWindow
| Variant | String Value |
|---|---|
| `SevenDays` | `"7d"` |
| `FourteenDays` | `"14d"` |
| `ThirtyDays` | `"30d"` |
| `NinetyDays` | `"90d"` |

#### 4.1.4 OrderStatusType
| Variant | Description |
|---|---|
| `Acknowledged` | Order accepted by matching engine |
| `Filled` | Order fully filled |
| `Cancelled` | Order cancelled |
| `Rejected` | Order rejected |
| `Unknown` | Unknown status |

#### 4.1.5 SortDirection
| Variant | String Value |
|---|---|
| `Ascending` | `"ASC"` |
| `Descending` | `"DESC"` |

#### 4.1.6 TwapStatus
| Variant |
|---|
| `Activated` |
| `Finished` |
| `Cancelled` |

#### 4.1.7 TradeAction
| Variant |
|---|
| `OpenLong` |
| `CloseLong` |
| `OpenShort` |
| `CloseShort` |
| `Net` |

#### 4.1.8 VaultType
| Variant |
|---|
| `User` |
| `Protocol` |

#### 4.1.9 MarketDepthAggregationSize
| Value |
|---|
| 1, 2, 5, 10, 100, 1000 |

### 4.2 Core Data Models (REQUIRED)

All models MUST be serializable/deserializable to/from JSON. Field names in JSON use `snake_case`.

#### 4.2.1 PerpMarketConfig
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market_addr` | string | NO | Market object address |
| `market_name` | string | NO | Human-readable market name (e.g., "BTC-USD") |
| `sz_decimals` | i32 | NO | Size decimal precision |
| `px_decimals` | i32 | NO | Price decimal precision |
| `max_leverage` | f64 | NO | Maximum allowed leverage |
| `min_size` | f64 | NO | Minimum order size |
| `lot_size` | f64 | NO | Lot size (order size granularity) |
| `tick_size` | f64 | NO | Tick size (price granularity) |
| `max_open_interest` | f64 | NO | Maximum open interest |
| `margin_call_fee_pct` | f64 | NO | Margin call fee percentage |
| `taker_in_next_block` | bool | NO | Whether taker fills in next block |

#### 4.2.2 AccountOverview
| Field | Type | Nullable | Description |
|---|---|---|---|
| `perp_equity_balance` | f64 | NO | Perpetual equity balance |
| `unrealized_pnl` | f64 | NO | Unrealized profit/loss |
| `unrealized_funding_cost` | f64 | NO | Unrealized funding cost |
| `cross_margin_ratio` | f64 | NO | Cross margin ratio |
| `maintenance_margin` | f64 | NO | Maintenance margin |
| `cross_account_leverage_ratio` | f64 | YES | Cross account leverage |
| `volume` | f64 | YES | Trading volume (per window) |
| `net_deposits` | f64 | YES | Net deposits |
| `all_time_return` | f64 | YES | All-time return |
| `pnl_90d` | f64 | YES | 90-day PnL |
| `sharpe_ratio` | f64 | YES | Sharpe ratio |
| `max_drawdown` | f64 | YES | Maximum drawdown |
| `weekly_win_rate_12w` | f64 | YES | 12-week weekly win rate |
| `average_cash_position` | f64 | YES | Average cash position |
| `average_leverage` | f64 | YES | Average leverage |
| `cross_account_position` | f64 | NO | Cross account position value |
| `total_margin` | f64 | NO | Total margin |
| `usdc_cross_withdrawable_balance` | f64 | NO | USDC cross withdrawable |
| `usdc_isolated_withdrawable_balance` | f64 | NO | USDC isolated withdrawable |
| `realized_pnl` | f64 | YES | Realized PnL |
| `liquidation_fees_paid` | f64 | YES | Liquidation fees paid |
| `liquidation_losses` | f64 | YES | Liquidation losses |

#### 4.2.3 UserPosition
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `user` | string | NO | Subaccount address |
| `size` | f64 | NO | Position size (negative = short) |
| `user_leverage` | f64 | NO | User leverage setting |
| `entry_price` | f64 | NO | Entry price |
| `is_isolated` | bool | NO | Whether position is isolated margin |
| `unrealized_funding` | f64 | NO | Unrealized funding |
| `estimated_liquidation_price` | f64 | NO | Estimated liquidation price |
| `tp_order_id` | string | YES | Take-profit order ID |
| `tp_trigger_price` | f64 | YES | Take-profit trigger price |
| `tp_limit_price` | f64 | YES | Take-profit limit price |
| `sl_order_id` | string | YES | Stop-loss order ID |
| `sl_trigger_price` | f64 | YES | Stop-loss trigger price |
| `sl_limit_price` | f64 | YES | Stop-loss limit price |
| `has_fixed_sized_tpsls` | bool | NO | Whether TP/SL has fixed sizes |

#### 4.2.4 MarketDepth
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `bids` | Vec<MarketOrder> | NO | Bid orders (price descending) |
| `asks` | Vec<MarketOrder> | NO | Ask orders (price ascending) |
| `unix_ms` | i64 | NO | Timestamp in milliseconds |

#### 4.2.5 MarketOrder
| Field | Type | Nullable | Description |
|---|---|---|---|
| `price` | f64 | NO | Price level |
| `size` | f64 | NO | Size at this level |

#### 4.2.6 MarketPrice
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `mark_px` | f64 | NO | Mark price |
| `mid_px` | f64 | NO | Mid price |
| `oracle_px` | f64 | NO | Oracle price |
| `funding_rate_bps` | f64 | NO | Funding rate in basis points |
| `is_funding_positive` | bool | NO | Whether funding is positive |
| `open_interest` | f64 | NO | Open interest |
| `transaction_unix_ms` | i64 | NO | Transaction timestamp |

#### 4.2.7 MarketContext
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `volume_24h` | f64 | NO | 24h volume |
| `open_interest` | f64 | NO | Open interest |
| `previous_day_price` | f64 | NO | Previous day closing price |
| `price_change_pct_24h` | f64 | NO | 24h price change percentage |

#### 4.2.8 Candlestick
| Field | Type | Nullable | Description |
|---|---|---|---|
| `T` | i64 | NO | Close timestamp |
| `c` | f64 | NO | Close price |
| `h` | f64 | NO | High price |
| `i` | string | NO | Interval |
| `l` | f64 | NO | Low price |
| `o` | f64 | NO | Open price |
| `t` | i64 | NO | Open timestamp |
| `v` | f64 | NO | Volume |

#### 4.2.9 MarketTrade
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market name |
| `price` | f64 | NO | Trade price |
| `size` | f64 | NO | Trade size |
| `is_buy` | bool | NO | Whether the taker was a buyer |
| `unix_ms` | i64 | NO | Trade timestamp |

#### 4.2.10 UserOpenOrder
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `client_order_id` | string | YES | Client-assigned order ID |
| `price` | f64 | NO | Limit price |
| `orig_size` | f64 | NO | Original order size |
| `remaining_size` | f64 | NO | Remaining unfilled size |
| `is_buy` | bool | NO | Buy or sell |
| `time_in_force` | string | NO | Time in force type |
| `is_reduce_only` | bool | NO | Whether reduce-only |
| `status` | string | NO | Order status |
| `transaction_unix_ms` | i64 | NO | Transaction timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.11 UserOrderHistoryItem
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `client_order_id` | string | YES | Client-assigned order ID |
| `price` | f64 | NO | Limit price |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `is_buy` | bool | NO | Buy or sell |
| `time_in_force` | string | NO | Time in force |
| `is_reduce_only` | bool | NO | Reduce only flag |
| `status` | string | NO | Order status |
| `transaction_unix_ms` | i64 | NO | Transaction timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.12 UserTradeHistoryItem
| Field | Type | Nullable | Description |
|---|---|---|---|
| `account` | string | NO | Account address |
| `market` | string | NO | Market address |
| `action` | TradeAction | NO | Trade action type |
| `size` | f64 | NO | Trade size |
| `price` | f64 | NO | Trade price |
| `is_profit` | bool | NO | Whether trade was profitable |
| `realized_pnl_amount` | f64 | NO | Realized PnL |
| `is_funding_positive` | bool | NO | Funding direction |
| `realized_funding_amount` | f64 | NO | Realized funding |
| `is_rebate` | bool | NO | Whether fee was a rebate |
| `fee_amount` | f64 | NO | Fee amount |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.13 UserFundingHistoryItem
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `funding_rate_bps` | f64 | NO | Funding rate in bps |
| `is_funding_positive` | bool | NO | Funding direction |
| `funding_amount` | f64 | NO | Funding amount |
| `position_size` | f64 | NO | Position size at time |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.14 UserSubaccount
| Field | Type | Nullable | Description |
|---|---|---|---|
| `subaccount_address` | string | NO | Subaccount address |
| `primary_account_address` | string | NO | Owner account address |
| `is_primary` | bool | NO | Whether primary subaccount |
| `custom_label` | string | YES | Custom label/name |
| `is_active` | bool | YES | Whether subaccount is active |

#### 4.2.15 UserActiveTwap
| Field | Type | Nullable | Description |
|---|---|---|---|
| `market` | string | NO | Market address |
| `is_buy` | bool | NO | Buy or sell |
| `order_id` | string | NO | TWAP order ID |
| `client_order_id` | string | NO | Client order ID |
| `is_reduce_only` | bool | NO | Reduce only |
| `start_unix_ms` | i64 | NO | Start timestamp |
| `frequency_s` | i64 | NO | Execution frequency in seconds |
| `duration_s` | i64 | NO | Total duration in seconds |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `status` | TwapStatus | NO | TWAP status |
| `transaction_unix_ms` | i64 | NO | Last transaction timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.16 Delegation
| Field | Type | Nullable | Description |
|---|---|---|---|
| `delegated_account` | string | NO | Delegated account address |
| `permission_type` | string | NO | Permission type |
| `expiration_time_s` | i64 | YES | Expiration timestamp in seconds |

#### 4.2.17 UserFundHistoryItem
| Field | Type | Nullable | Description |
|---|---|---|---|
| `amount` | f64 | NO | Deposit/withdrawal amount |
| `is_deposit` | bool | NO | Whether deposit (true) or withdrawal (false) |
| `transaction_unix_ms` | i64 | NO | Timestamp |
| `transaction_version` | i64 | NO | Transaction version |

#### 4.2.18 OrderStatus
| Field | Type | Nullable | Description |
|---|---|---|---|
| `parent` | string | NO | Parent account address |
| `market` | string | NO | Market address |
| `order_id` | string | NO | Order ID |
| `status` | string | NO | Status string |
| `orig_size` | f64 | NO | Original size |
| `remaining_size` | f64 | NO | Remaining size |
| `size_delta` | f64 | NO | Size delta |
| `price` | f64 | NO | Price |
| `is_buy` | bool | NO | Buy or sell |
| `details` | string | NO | Status details |
| `transaction_version` | i64 | NO | Transaction version |
| `unix_ms` | i64 | NO | Timestamp |

#### 4.2.19 PlaceOrderResult
| Field | Type | Nullable | Description |
|---|---|---|---|
| `success` | bool | NO | Whether order was placed successfully |
| `order_id` | string | YES | Order ID (if successful) |
| `transaction_hash` | string | YES | Transaction hash |
| `error` | string | YES | Error message (if failed) |

#### 4.2.20 Vault
| Field | Type | Nullable | Description |
|---|---|---|---|
| `address` | string | NO | Vault address |
| `name` | string | NO | Vault name |
| `description` | string | YES | Vault description |
| `manager` | string | NO | Manager account address |
| `status` | string | NO | Vault status |
| `created_at` | i64 | NO | Creation timestamp |
| `tvl` | f64 | YES | Total value locked |
| `volume` | f64 | YES | Trading volume |
| `volume_30d` | f64 | YES | 30-day volume |
| `all_time_pnl` | f64 | YES | All-time PnL |
| `net_deposits` | f64 | YES | Net deposits |
| `all_time_return` | f64 | YES | All-time return |
| `past_month_return` | f64 | YES | Past month return |
| `sharpe_ratio` | f64 | YES | Sharpe ratio |
| `max_drawdown` | f64 | YES | Maximum drawdown |
| `weekly_win_rate_12w` | f64 | YES | 12-week weekly win rate |
| `profit_share` | f64 | YES | Profit share percentage |
| `pnl_90d` | f64 | YES | 90-day PnL |
| `manager_cash_pct` | f64 | YES | Manager cash percentage |
| `average_leverage` | f64 | YES | Average leverage |
| `depositors` | i64 | YES | Number of depositors |
| `perp_equity` | f64 | YES | Perp equity |
| `vault_type` | VaultType | YES | Vault type |
| `social_links` | Vec<string> | YES | Social media links |

#### 4.2.21 UserOwnedVault
| Field | Type | Nullable | Description |
|---|---|---|---|
| `vault_address` | string | NO | Vault address |
| `vault_name` | string | NO | Vault name |
| `vault_share_symbol` | string | NO | Share token symbol |
| `status` | string | NO | Status |
| `age_days` | i64 | NO | Age in days |
| `num_managers` | i64 | NO | Number of managers |
| `tvl` | f64 | YES | Total value locked |
| `apr` | f64 | YES | Annual percentage rate |
| `manager_equity` | f64 | YES | Manager equity |
| `manager_stake` | f64 | YES | Manager stake |

#### 4.2.22 LeaderboardItem
| Field | Type | Nullable | Description |
|---|---|---|---|
| `rank` | i64 | NO | Leaderboard rank |
| `account` | string | NO | Account address |
| `account_value` | f64 | NO | Account value |
| `realized_pnl` | f64 | NO | Realized PnL |
| `roi` | f64 | NO | Return on investment |
| `volume` | f64 | NO | Trading volume |

#### 4.2.23 PortfolioChartData
| Field | Type | Nullable | Description |
|---|---|---|---|
| `timestamp` | i64 | NO | Data point timestamp |
| `value` | f64 | NO | Portfolio value |

#### 4.2.24 UserNotification
| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | string | NO | Notification ID |
| `type` | string | NO | Notification type |
| `message` | string | NO | Message content |
| `timestamp` | i64 | NO | Timestamp |
| `read` | bool | NO | Whether read |

### 4.3 WebSocket Message Wrappers (REQUIRED)

All WebSocket messages are wrapped in a topic-specific envelope. Each subscription topic has a corresponding message type:

| WS Topic Pattern | Message Type |
|---|---|
| `accountOverview:{subAddr}` | `{ account_overview: AccountOverview }` |
| `userPositions:{subAddr}` | `{ positions: Vec<UserPosition> }` |
| `userOpenOrders:{subAddr}` | `{ orders: Vec<UserOpenOrder> }` |
| `userOrderHistory:{subAddr}` | `{ orders: Vec<UserOrderHistoryItem> }` |
| `userTradeHistory:{subAddr}` | `{ trades: Vec<UserTradeHistoryItem> }` |
| `userFundingRateHistory:{subAddr}` | `{ funding: Vec<UserFundingHistoryItem> }` |
| `marketDepth:{marketName}` | `MarketDepth` (full snapshot) |
| `marketPrice:{marketName}` | `MarketPrice` |
| `allMarketPrices` | `{ prices: Vec<MarketPrice> }` |
| `marketTrades:{marketName}` | `{ trades: Vec<MarketTrade> }` |
| `marketCandlestick:{marketName}:{interval}` | `{ candle: Candlestick }` |
| `orderUpdate:{subAddr}` | Order update event |
| `notifications:{subAddr}` | Notification event |
| `bulkOrders:{subAddr}` | Bulk order update |
| `bulkOrderFills:{subAddr}` | Bulk order fill update |
| `userActiveTwaps:{subAddr}` | TWAP order update |

### 4.4 Pagination Types (REQUIRED)

#### PageParams
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | i32 | NO | 10 | Number of items per page |
| `offset` | i32 | NO | 0 | Offset for pagination |

#### PaginatedResponse<T>
| Field | Type | Description |
|---|---|---|
| `items` | Vec<T> | List of items |
| `total_count` | i64 | Total count of items |

#### SortParams
| Field | Type | Required |
|---|---|---|
| `sort_key` | string | NO |
| `sort_dir` | SortDirection | NO |

#### SearchTermParams
| Field | Type | Required |
|---|---|---|
| `search_term` | string | NO |

---

## 5. REST API Client

### 5.1 Base URL Construction (REQUIRED)

All REST endpoints are relative to `{config.trading_http_url}/api/v1/`.

### 5.2 Authentication (REQUIRED)

- Header: `x-api-key: {api_key}` (when API key is provided)
- All requests MUST include `Content-Type: application/json`

### 5.3 HTTP Methods (REQUIRED)

The SDK MUST implement generic typed HTTP request methods:

- `get_request<T>(url, query_params, schema) -> Result<ApiResponse<T>>`
- `post_request<T>(url, body, schema) -> Result<ApiResponse<T>>`
- `patch_request<T>(url, body, schema) -> Result<ApiResponse<T>>`

Where `ApiResponse<T>` contains:
| Field | Type |
|---|---|
| `data` | T |
| `status` | i32 |
| `status_text` | string |

### 5.4 REST Endpoints (REQUIRED)

#### Market Data Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/markets` | none | `Vec<PerpMarketConfig>` |
| GET | `/markets/{name}` | none | `PerpMarketConfig` |
| GET | `/asset-contexts` | none | `Vec<MarketContext>` |
| GET | `/depth/{marketName}` | `limit` | `MarketDepth` |
| GET | `/prices` | none | `Vec<MarketPrice>` |
| GET | `/prices/{marketName}` | none | `Vec<MarketPrice>` |
| GET | `/trades/{marketName}` | `limit` | `Vec<MarketTrade>` |
| GET | `/candlesticks/{marketName}` | `interval`, `startTime`, `endTime` | `Vec<Candlestick>` |

#### Account Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/account/{subAddr}` | `volume_window`, `include_performance` | `AccountOverview` |
| GET | `/positions/{subAddr}` | `market_addr`, `include_deleted`, `limit` | `Vec<UserPosition>` |
| GET | `/open-orders/{subAddr}` | none | `Vec<UserOpenOrder>` |
| GET | `/order-history/{subAddr}` | `market_addr`, `limit`, `offset` | `PaginatedResponse<UserOrderHistoryItem>` |
| GET | `/trade-history/{subAddr}` | `limit`, `offset` | `PaginatedResponse<UserTradeHistoryItem>` |
| GET | `/funding-history/{subAddr}` | `market_addr`, `limit`, `offset` | `PaginatedResponse<UserFundingHistoryItem>` |
| GET | `/fund-history/{subAddr}` | `limit`, `offset` | `PaginatedResponse<UserFundHistoryItem>` |
| GET | `/subaccounts/{ownerAddr}` | none | `Vec<UserSubaccount>` |
| GET | `/delegations/{subAddr}` | none | `Vec<Delegation>` |

#### TWAP Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/active-twaps/{subAddr}` | none | `Vec<UserActiveTwap>` |
| GET | `/twap-history/{subAddr}` | `limit`, `offset` | `PaginatedResponse<UserActiveTwap>` |

#### Vault Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/vaults` | `limit`, `offset`, `sort_key`, `sort_dir`, `search_term` | `VaultsResponse` |
| GET | `/vaults/owned/{accountAddr}` | `limit`, `offset` | `PaginatedResponse<UserOwnedVault>` |
| GET | `/vaults/performance/{accountAddr}` | none | `Vec<UserPerformanceOnVault>` |

#### Analytics Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/leaderboard` | `limit`, `offset`, `sort_key`, `sort_dir`, `search_term` | `PaginatedResponse<LeaderboardItem>` |
| GET | `/portfolio-chart/{subAddr}` | `interval` | `Vec<PortfolioChartData>` |

#### Order Status Endpoint
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/orders/{orderId}` | `market_address`, `user_address` | `OrderStatus` |

#### Bulk Order Endpoints
| Method | Path | Query Params | Response Type |
|---|---|---|---|
| GET | `/bulk-orders/{subAddr}` | none | Bulk orders response |
| GET | `/bulk-order-status/{orderId}` | none | Bulk order status |
| GET | `/bulk-order-fills/{orderId}` | none | Bulk order fills |

---

## 6. WebSocket Client

### 6.1 Connection Management (REQUIRED)

| Feature | Requirement |
|---|---|
| URL | `{config.trading_ws_url}` |
| Authentication | `x-api-key` query param or header |
| Auto-reconnect | REQUIRED with exponential backoff |
| Ping/pong | REQUIRED to keep connection alive |
| Connection sharing | Single connection for all subscriptions |
| Thread safety | REQUIRED - concurrent subscribe/unsubscribe |

### 6.2 Subscription Protocol (REQUIRED)

**Subscribe message format:**
```json
{
  "method": "subscribe",
  "subscription": "{topic}"
}
```

**Unsubscribe message format:**
```json
{
  "method": "unsubscribe",
  "subscription": "{topic}"
}
```

### 6.3 Subscription Methods (REQUIRED)

Each subscription method MUST return an unsubscribe function/handle.

| Method | Topic Pattern | Data Type |
|---|---|---|
| `subscribe_account_overview(sub_addr, callback)` | `accountOverview:{sub_addr}` | AccountOverview WS message |
| `subscribe_user_positions(sub_addr, callback)` | `userPositions:{sub_addr}` | UserPositions WS message |
| `subscribe_user_open_orders(sub_addr, callback)` | `userOpenOrders:{sub_addr}` | UserOpenOrders WS message |
| `subscribe_user_order_history(sub_addr, callback)` | `userOrderHistory:{sub_addr}` | UserOrderHistory WS message |
| `subscribe_user_trade_history(sub_addr, callback)` | `userTradeHistory:{sub_addr}` | UserTradeHistory WS message |
| `subscribe_user_trades(sub_addr, callback)` | `userTrades:{sub_addr}` | UserTrades WS message |
| `subscribe_user_funding_history(sub_addr, callback)` | `userFundingRateHistory:{sub_addr}` | FundingHistory WS message |
| `subscribe_market_depth(market_name, agg_size, callback)` | `marketDepth:{market_name}` | MarketDepth |
| `subscribe_market_price(market_name, callback)` | `marketPrice:{market_name}` | MarketPrice WS message |
| `subscribe_all_market_prices(callback)` | `allMarketPrices` | AllMarketPrices WS message |
| `subscribe_market_trades(market_name, callback)` | `marketTrades:{market_name}` | MarketTrades WS message |
| `subscribe_candlestick(market_name, interval, callback)` | `marketCandlestick:{market_name}:{interval}` | Candlestick WS message |
| `subscribe_order_update(sub_addr, callback)` | `orderUpdate:{sub_addr}` | OrderUpdate event |
| `subscribe_notifications(sub_addr, callback)` | `notifications:{sub_addr}` | Notification event |
| `subscribe_bulk_orders(sub_addr, callback)` | `bulkOrders:{sub_addr}` | BulkOrders event |
| `subscribe_bulk_order_fills(sub_addr, callback)` | `bulkOrderFills:{sub_addr}` | BulkOrderFills event |
| `subscribe_user_active_twaps(sub_addr, callback)` | `userActiveTwaps:{sub_addr}` | ActiveTwaps event |

### 6.4 WebSocket Lifecycle (REQUIRED)

| Method | Description |
|---|---|
| `close()` | Close WebSocket connection and clean up all subscriptions |
| `reset(topic)` | Reset subscription for a specific topic (re-subscribe) |
| `ready_state()` | Return current connection state (Connecting/Open/Closing/Closed) |

---

## 7. On-Chain Transaction Builder

### 7.1 Transaction Building (REQUIRED)

The SDK MUST support building Aptos transactions for Decibel smart contract calls.

#### Build Transaction Parameters
| Field | Type | Required | Description |
|---|---|---|---|
| `function` | string | YES | Fully qualified Move function name |
| `type_arguments` | Vec<string> | YES | Move type arguments (usually empty) |
| `function_arguments` | Vec<any> | YES | Move function arguments |
| `max_gas_amount` | u64 | NO | Maximum gas amount |
| `gas_unit_price` | u64 | NO | Gas unit price |

### 7.2 Transaction Simulation (OPTIONAL but RECOMMENDED)

When `skip_simulate` is false:
1. Build transaction with estimated gas
2. Simulate transaction to get gas estimates
3. Rebuild with actual gas estimates
4. Sign and submit

### 7.3 Fee Payer / Gas Station (REQUIRED)

Two modes of fee payment:

**Mode 1: Gas Station Client (API key based)**
- Use `gas_station_url` + `gas_station_api_key`
- Submit via Aptos Labs Gas Station API

**Mode 2: Legacy Gas Station**
- POST to `{gas_station_url}/transactions`
- Body: `{ signature: byte[], transaction: byte[] }`

**Mode 3: Self-paid**
- When `no_fee_payer` is true, submit directly to Aptos

### 7.4 Transaction Signing (REQUIRED)

- Use Ed25519 signature scheme
- Sign raw transaction bytes
- Support `account_override` for session/delegated accounts

### 7.5 Smart Contract Entry Points (REQUIRED)

All Move function calls use the pattern: `{package}::{module}::{function}`

| Module | Function | Description |
|---|---|---|
| `dex_accounts` | `create_new_subaccount` | Create subaccount |
| `dex_accounts` | `deposit_to_subaccount_at` | Deposit collateral |
| `dex_accounts` | `withdraw_from_subaccount` | Withdraw collateral |
| `dex_accounts` | `configure_user_settings_for_market` | Configure margin/leverage |
| `dex_accounts_entry` | `place_order_to_subaccount` | Place an order |
| `dex_accounts` | `cancel_order_to_subaccount` | Cancel an order |
| `dex_accounts` | `cancel_client_order_to_subaccount` | Cancel by client order ID |
| `dex_accounts` | `place_twap_order_to_subaccount` | Place TWAP order |
| `dex_accounts` | `cancel_twap_order_to_subaccount` | Cancel TWAP order |
| `dex_accounts` | `place_tp_sl_order_for_position` | Place TP/SL order |
| `dex_accounts` | `update_tp_order_for_position` | Update TP order |
| `dex_accounts` | `update_sl_order_for_position` | Update SL order |
| `dex_accounts` | `cancel_tp_sl_order_for_position` | Cancel TP/SL order |
| `dex_accounts` | `delegate_trading_to_for_subaccount` | Delegate trading |
| `dex_accounts` | `revoke_delegation` | Revoke delegation |
| `dex_accounts` | `approve_max_builder_fee` | Approve builder fee |
| `dex_accounts` | `revoke_max_builder_fee` | Revoke builder fee |

#### Vault Module Functions
| Module | Function | Description |
|---|---|---|
| `vaults` | `create_and_fund_vault` | Create and fund a vault |
| `vaults` | `activate_vault` | Activate a vault |
| `vaults` | `contribute_to_vault` | Deposit to vault |
| `vaults` | `redeem_from_vault` | Withdraw from vault |
| `vaults` | `delegate_dex_actions_to` | Delegate vault trading |

---

## 8. Write Operations (Trading)

### 8.1 Account Management (REQUIRED)

#### create_subaccount() -> TransactionResponse
Creates a new subaccount for the signing account.
- **Arguments**: None
- **Returns**: Transaction response with subaccount creation event

#### deposit(amount: u64, subaccount_addr?: string) -> TransactionResponse
Deposits collateral (USDC) to a subaccount.
- **amount**: Amount in smallest unit (raw u64)
- **subaccount_addr**: Optional, defaults to primary subaccount

#### withdraw(amount: u64, subaccount_addr?: string) -> TransactionResponse
Withdraws collateral from a subaccount.
- **amount**: Amount in smallest unit (raw u64)
- **subaccount_addr**: Optional, defaults to primary subaccount

#### rename_subaccount(subaccount_addr: string, new_name: string) -> ApiResponse
Renames a subaccount via REST API.
- **Note**: This is a REST call, not an on-chain transaction

#### configure_user_settings_for_market(args) -> TransactionResponse
| Arg | Type | Required | Description |
|---|---|---|---|
| `market_addr` | string | YES | Market object address |
| `subaccount_addr` | string | YES | Subaccount address |
| `is_cross` | bool | YES | Cross margin mode |
| `user_leverage` | u64 | YES | Leverage in basis points (1000 = 10x) |

### 8.2 Order Management (REQUIRED)

#### place_order(args) -> PlaceOrderResult
| Arg | Type | Required | Description |
|---|---|---|---|
| `market_name` | string | YES | Market name (e.g., "BTC-USD") |
| `price` | f64 | YES | Limit price |
| `size` | f64 | YES | Order size |
| `is_buy` | bool | YES | True for buy, false for sell |
| `time_in_force` | TimeInForce | YES | GTC, PostOnly, or IOC |
| `is_reduce_only` | bool | YES | Whether reduce-only order |
| `client_order_id` | string | NO | Client-assigned order ID |
| `stop_price` | f64 | NO | Stop trigger price |
| `tp_trigger_price` | f64 | NO | Take-profit trigger price |
| `tp_limit_price` | f64 | NO | Take-profit limit price |
| `sl_trigger_price` | f64 | NO | Stop-loss trigger price |
| `sl_limit_price` | f64 | NO | Stop-loss limit price |
| `builder_addr` | string | NO | Builder fee recipient |
| `builder_fee` | u64 | NO | Builder fee in basis points |
| `subaccount_addr` | string | NO | Subaccount (default: primary) |
| `account_override` | Account | NO | Session account override |
| `tick_size` | f64 | NO | Tick size for price rounding |

**Returns**: `PlaceOrderResult` with `success`, `order_id`, `transaction_hash`, `error`

#### cancel_order(args) -> TransactionResponse
| Arg | Type | Required | Description |
|---|---|---|---|
| `order_id` | string/u64 | YES | Order ID to cancel |
| `market_name` | string | ONE OF | Market name |
| `market_addr` | string | ONE OF | Market address |
| `subaccount_addr` | string | NO | Subaccount address |
| `account_override` | Account | NO | Session account |

**Note**: Either `market_name` OR `market_addr` MUST be provided.

#### cancel_client_order(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `client_order_id` | string | YES |
| `market_name` | string | YES |
| `subaccount_addr` | string | NO |
| `account_override` | Account | NO |

### 8.3 TWAP Orders (REQUIRED)

#### place_twap_order(args) -> TwapOrderResult
| Arg | Type | Required | Description |
|---|---|---|---|
| `market_name` | string | YES | Market name |
| `size` | f64 | YES | Total size |
| `is_buy` | bool | YES | Buy or sell |
| `is_reduce_only` | bool | YES | Reduce only |
| `client_order_id` | string | NO | Client order ID |
| `twap_frequency_seconds` | u64 | YES | Execution frequency |
| `twap_duration_seconds` | u64 | YES | Total duration |
| `builder_address` | string | NO | Builder address |
| `builder_fees` | u64 | NO | Builder fee bps |
| `subaccount_addr` | string | NO | Subaccount |
| `account_override` | Account | NO | Session account |

#### cancel_twap_order(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `order_id` | string | YES |
| `market_addr` | string | YES |
| `subaccount_addr` | string | NO |
| `account_override` | Account | NO |

### 8.4 Position Management (REQUIRED)

#### place_tp_sl_order_for_position(args) -> TransactionResponse
| Arg | Type | Required | Description |
|---|---|---|---|
| `market_addr` | string | YES | Market address |
| `tp_trigger_price` | f64 | NO | Take-profit trigger |
| `tp_limit_price` | f64 | NO | Take-profit limit |
| `tp_size` | f64 | NO | Take-profit size |
| `sl_trigger_price` | f64 | NO | Stop-loss trigger |
| `sl_limit_price` | f64 | NO | Stop-loss limit |
| `sl_size` | f64 | NO | Stop-loss size |
| `subaccount_addr` | string | NO | Subaccount |
| `account_override` | Account | NO | Session account |
| `tick_size` | f64 | NO | Tick size for rounding |

#### update_tp_order_for_position(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `market_addr` | string | YES |
| `prev_order_id` | string/u64 | YES |
| `tp_trigger_price` | f64 | NO |
| `tp_limit_price` | f64 | NO |
| `tp_size` | f64 | NO |
| `subaccount_addr` | string | NO |
| `account_override` | Account | NO |

#### update_sl_order_for_position(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `market_addr` | string | YES |
| `prev_order_id` | string/u64 | YES |
| `sl_trigger_price` | f64 | NO |
| `sl_limit_price` | f64 | NO |
| `sl_size` | f64 | NO |
| `subaccount_addr` | string | NO |
| `account_override` | Account | NO |

#### cancel_tp_sl_order_for_position(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `market_addr` | string | YES |
| `order_id` | string/u64 | YES |
| `subaccount_addr` | string | NO |
| `account_override` | Account | NO |

### 8.5 Delegation (REQUIRED)

#### delegate_trading_to(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `subaccount_addr` | string | YES |
| `account_to_delegate_to` | string | YES |
| `expiration_timestamp_secs` | u64 | NO |

#### revoke_delegation(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `subaccount_addr` | string | NO |
| `account_to_revoke` | string | YES |

### 8.6 Builder Fee Management (REQUIRED)

#### approve_max_builder_fee(args) -> TransactionResponse
| Arg | Type | Required | Description |
|---|---|---|---|
| `builder_addr` | string | YES | Builder address |
| `max_fee` | u64 | YES | Max fee in basis points |
| `subaccount_addr` | string | NO | Subaccount |

#### revoke_max_builder_fee(args) -> TransactionResponse
| Arg | Type | Required |
|---|---|---|
| `builder_addr` | string | YES |
| `subaccount_addr` | string | NO |

### 8.7 Vault Operations (REQUIRED)

#### create_vault(args) -> TransactionResponse
| Arg | Type | Required | Description |
|---|---|---|---|
| `vault_name` | string | YES | Vault name |
| `vault_description` | string | YES | Description |
| `vault_social_links` | Vec<string> | YES | Social links |
| `vault_share_symbol` | string | YES | Share token symbol |
| `vault_share_icon_uri` | string | NO | Icon URI |
| `vault_share_project_uri` | string | NO | Project URI |
| `fee_bps` | u64 | YES | Fee in basis points |
| `fee_interval_s` | u64 | YES | Fee interval seconds |
| `contribution_lockup_duration_s` | u64 | YES | Lockup period |
| `initial_funding` | u64 | YES | Initial funding amount |
| `accepts_contributions` | bool | YES | Whether accepts deposits |
| `delegate_to_creator` | bool | YES | Auto-delegate to creator |
| `contribution_asset_type` | string | NO | Asset type |

#### activate_vault(vault_address: string) -> TransactionResponse
#### deposit_to_vault(vault_address: string, amount: u64) -> TransactionResponse
#### withdraw_from_vault(vault_address: string, shares: u64) -> TransactionResponse
#### delegate_dex_actions_to(vault_address: string, account: string, expiration?: u64) -> TransactionResponse

### 8.8 Trigger Matching (OPTIONAL)

#### trigger_matching(market_addr: string, max_work_unit: u64) -> Result
Triggers matching engine for a market. Returns success/failure with transaction hash.

---

## 9. Read Operations (Market Data)

### 9.1 Markets Reader (REQUIRED)

| Method | REST Call | WS Subscription | Returns |
|---|---|---|---|
| `get_all()` | GET `/markets` | - | `Vec<PerpMarketConfig>` |
| `get_by_name(name)` | GET `/markets/{name}` | - | `PerpMarketConfig` |
| `list_market_addresses()` | Derived from get_all | - | `Vec<string>` |
| `market_name_by_address(addr)` | Derived from get_all | - | `string` |

### 9.2 Account Overview Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, volume_window?, include_performance?)` | REST | `AccountOverview` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.3 Market Depth Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_name(market_name, limit?)` | REST | `MarketDepth` |
| `subscribe_by_name(market_name, agg_size, callback)` | WS | Unsubscribe handle |
| `reset_subscription_by_name(market_name, agg_size?)` | WS | void |
| `get_aggregation_sizes()` | Local | `[1, 2, 5, 10, 100, 1000]` |

### 9.4 Market Prices Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_all()` | REST | `Vec<MarketPrice>` |
| `get_by_name(market_name)` | REST | `Vec<MarketPrice>` |
| `subscribe_by_name(market_name, callback)` | WS | Unsubscribe handle |
| `subscribe_by_address(market_addr, callback)` | WS | Unsubscribe handle |
| `subscribe_all(callback)` | WS | Unsubscribe handle |

### 9.5 Market Trades Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_name(market_name, limit?)` | REST | `Vec<MarketTrade>` |
| `subscribe_by_name(market_name, callback)` | WS | Unsubscribe handle |

### 9.6 Candlesticks Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_name(market_name, interval, start_time, end_time)` | REST | `Vec<Candlestick>` |
| `subscribe_by_name(market_name, interval, callback)` | WS | Unsubscribe handle |

### 9.7 Market Contexts Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_all()` | REST | `Vec<MarketContext>` |

### 9.8 User Positions Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, market_addr?, include_deleted?, limit?)` | REST | `Vec<UserPosition>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.9 User Open Orders Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr)` | REST | `Vec<UserOpenOrder>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.10 User Order History Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, market_addr?, limit?, offset?)` | REST | `PaginatedResponse<UserOrderHistoryItem>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.11 User Trade History Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, limit?, offset?)` | REST | `PaginatedResponse<UserTradeHistoryItem>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.12 User Funding History Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, market_addr?, limit?, offset?)` | REST | `PaginatedResponse<UserFundingHistoryItem>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.13 User Fund History Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, limit?, offset?)` | REST | `PaginatedResponse<UserFundHistoryItem>` |

### 9.14 User Subaccounts Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(owner_addr)` | REST | `Vec<UserSubaccount>` |

### 9.15 Delegations Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_all(sub_addr)` | REST | `Vec<Delegation>` |

### 9.16 User Active TWAPs Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr)` | REST | `Vec<UserActiveTwap>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.17 User TWAP History Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, limit?, offset?)` | REST | `PaginatedResponse<UserActiveTwap>` |

### 9.18 Vaults Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_vaults(limit?, offset?, sort_key?, sort_dir?, search_term?)` | REST | `VaultsResponse` |
| `get_user_owned_vaults(account_addr, limit?, offset?)` | REST | `PaginatedResponse<UserOwnedVault>` |
| `get_user_performances_on_vaults(account_addr)` | REST | `Vec<UserPerformanceOnVault>` |
| `get_vault_share_price(vault_address)` | REST | `f64` |

### 9.19 Leaderboard Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_leaderboard(limit?, offset?, sort_key?, sort_dir?, search_term?)` | REST | `PaginatedResponse<LeaderboardItem>` |

### 9.20 Portfolio Chart Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr, interval?)` | REST | `Vec<PortfolioChartData>` |

### 9.21 User Notifications Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr)` | REST | `Vec<UserNotification>` |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.22 Trading Points Reader (OPTIONAL)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr)` | REST | Trading points data |

### 9.23 Bulk Orders Reader (REQUIRED)

| Method | REST/WS | Returns |
|---|---|---|
| `get_by_addr(sub_addr)` | REST | Bulk orders |
| `subscribe_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |
| `subscribe_fills_by_addr(sub_addr, callback)` | WS | Unsubscribe handle |

### 9.24 On-Chain View Functions (REQUIRED)

These read directly from the blockchain via Aptos view functions:

| Method | Description |
|---|---|
| `global_perp_engine_state()` | Get global perp engine state |
| `collateral_balance_decimals()` | Get collateral balance decimal precision |
| `usdc_decimals()` | Get USDC decimals (should be cached) |
| `usdc_balance(addr)` | Get USDC balance for an address |
| `account_balance(addr)` | Get account balance |
| `position_size(addr, market_addr)` | Get position size |
| `get_crossed_position(addr)` | Get crossed positions |
| `token_balance(addr, token_addr, decimals)` | Get generic token balance |

---

## 10. Error Handling

### 10.1 Error Types (REQUIRED)

Each SDK MUST define the following error categories:

| Error Type | Description |
|---|---|
| `ConfigError` | Invalid configuration |
| `NetworkError` | HTTP/WS connection failures |
| `ApiError` | REST API returned non-2xx status |
| `ValidationError` | Response schema validation failure |
| `TransactionError` | On-chain transaction failure |
| `SimulationError` | Transaction simulation failure |
| `SigningError` | Transaction signing failure |
| `GasEstimationError` | Gas estimation failure |
| `WebSocketError` | WebSocket connection/subscription error |
| `SerializationError` | JSON serialization/deserialization error |
| `TimeoutError` | Request/transaction timeout |

### 10.2 ApiError Details (REQUIRED)
| Field | Type | Description |
|---|---|---|
| `status` | i32 | HTTP status code |
| `status_text` | string | HTTP status text |
| `message` | string | Error message from server |

### 10.3 TransactionError Details (REQUIRED)
| Field | Type | Description |
|---|---|---|
| `transaction_hash` | string | Transaction hash (if submitted) |
| `vm_status` | string | Move VM error status |
| `message` | string | Human-readable error message |

---

## 11. Utility Functions

### 11.1 Address Derivation (REQUIRED)

#### get_market_addr(name: string, perp_engine_global_addr: string) -> string
Derives market object address from market name using Aptos `create_object_address`:
1. BCS-serialize market name as MoveString
2. Call `create_object_address(perp_engine_global_addr, serialized_name)`

#### get_primary_subaccount_addr(account_addr: string, compat_version: string, package_addr: string) -> string
Derives the primary subaccount address for an account.

#### get_vault_share_address(vault_address: string) -> string
Derives the vault share token address.

### 11.2 Price/Size Formatting (REQUIRED)

#### round_to_tick_size(price: f64, tick_size: f64, px_decimals: i32, round_up: bool) -> f64
Rounds a price to the nearest valid tick size.

### 11.3 Random Nonce Generation (REQUIRED)

#### generate_random_replay_protection_nonce() -> u64
Generates a random nonce for replay protection in transactions.

### 11.4 Order ID Extraction (REQUIRED)

#### extract_order_id_from_transaction(tx_response, subaccount_addr) -> Option<string>
Extracts order ID from `OrderEvent` in transaction events.

### 11.5 Query Parameter Construction (REQUIRED)

#### construct_query_params(page_params, sort_params, search_params) -> URLSearchParams
Builds URL query parameters from pagination, sort, and search parameters.

---

## 12. Performance Requirements

### 12.1 Connection Pooling (REQUIRED)
- HTTP client MUST reuse connections (HTTP/2 preferred)
- WebSocket MUST use a single shared connection for all subscriptions

### 12.2 Caching (REQUIRED)
- USDC decimals MUST be cached after first fetch
- Market configurations SHOULD be cacheable

### 12.3 Gas Price Management (REQUIRED)

The `GasPriceManager` MUST:
| Feature | Requirement |
|---|---|
| Periodic refresh | Configurable interval (default: 5s) |
| Multiplier | Apply configurable multiplier to estimates |
| Thread safety | Safe for concurrent access |
| Lazy initialization | Only start fetching when first needed |
| Cleanup | Provide `destroy()` to stop background tasks |

### 12.4 Transaction Throughput (REQUIRED)
- Transaction builder MUST support synchronous building (no async for building step)
- Replay protection nonce MUST be locally generated (no network call)
- Expiration timestamp MUST be locally computed

### 12.5 Serialization Performance (REQUIRED)
- Use zero-copy deserialization where possible (Rust)
- Use code generation for JSON serialization where possible
- Minimize allocations in hot paths (order placement, WS message handling)

### 12.6 WebSocket Performance (REQUIRED)
- Message parsing MUST happen on a background thread/goroutine/task
- Callback dispatch MUST NOT block the WebSocket read loop
- Buffer incoming messages if callbacks are slow

---

## 13. Language-Specific Idioms

### 13.1 Rust
- Use `Result<T, DecibelError>` for all fallible operations
- Use `async/await` with `tokio` runtime
- Implement `Send + Sync` for all public types
- Use `serde` for JSON serialization with `#[serde(rename_all = "snake_case")]`
- Use `Arc<Mutex<>>` or `Arc<RwLock<>>` for shared state
- WebSocket: use `tokio-tungstenite`
- HTTP: use `reqwest` with connection pooling
- Aptos: use `aptos-sdk` crate
- Expose builder patterns for complex argument structs
- Use `thiserror` for error types

### 13.2 Swift
- Use `async/await` (Swift concurrency)
- Use `Codable` protocol for JSON serialization
- Use `URLSession` for HTTP requests
- Use `URLSessionWebSocketTask` for WebSocket
- Define protocols for mockability (`DecibelReadClientProtocol`, `DecibelWriteClientProtocol`)
- Use `@Published` properties for reactive bindings
- Use `Combine` framework for subscription streams as an alternative to callbacks
- Package as Swift Package Manager (SPM) package
- Support iOS 15+, macOS 12+

### 13.3 Kotlin
- Use `suspend fun` for all async operations
- Use `kotlinx.serialization` for JSON
- Use `Ktor` for HTTP client
- Use `Ktor WebSocket` or `OkHttp` for WebSocket
- Use `Flow<T>` for WebSocket subscriptions (alternative to callbacks)
- Use `sealed class` for error types and enums
- Use data classes for all models
- Package as Maven/Gradle library
- Support Kotlin Multiplatform (JVM + Android)
- Use `kotlinx.coroutines` for async orchestration

### 13.4 Go
- Return `(T, error)` for all fallible operations
- Use `context.Context` for cancellation and timeouts
- Use `gorilla/websocket` or `nhooyr.io/websocket` for WebSocket
- Use `net/http` with connection pooling for HTTP
- Use `encoding/json` struct tags for serialization
- Use `chan` for WebSocket subscription delivery
- Use `sync.RWMutex` for shared state
- Use interfaces for mockability
- Use `go.uber.org/zap` or `log/slog` for logging
- Package as Go module with proper `go.mod`
- Use functional options pattern for configuration

---

## Appendix A: WebSocket Message Examples

### Subscribe Request
```json
{"method":"subscribe","subscription":"marketPrice:BTC-USD"}
```

### Market Price Message
```json
{
  "channel": "marketPrice:BTC-USD",
  "data": {
    "market": "BTC-USD",
    "mark_px": 45123.45,
    "mid_px": 45120.00,
    "oracle_px": 45125.00,
    "funding_rate_bps": 0.0123,
    "is_funding_positive": true,
    "open_interest": 1500000.00,
    "transaction_unix_ms": 1708000000000
  }
}
```

### Market Depth Message
```json
{
  "channel": "marketDepth:BTC-USD",
  "data": {
    "market": "BTC-USD",
    "bids": [{"price": 45100.0, "size": 2.5}, {"price": 45050.0, "size": 1.0}],
    "asks": [{"price": 45150.0, "size": 3.0}, {"price": 45200.0, "size": 0.5}],
    "unix_ms": 1708000000000
  }
}
```

## Appendix B: Transaction Payload Examples

### Place Order Payload
```json
{
  "function": "0x{package}::dex_accounts_entry::place_order_to_subaccount",
  "type_arguments": [],
  "function_arguments": [
    "0x{subaccount_addr}",
    "0x{market_addr}",
    45000000000,
    1000000000,
    true,
    0,
    false,
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    []
  ]
}
```

### Cancel Order Payload
```json
{
  "function": "0x{package}::dex_accounts::cancel_order_to_subaccount",
  "type_arguments": [],
  "function_arguments": [
    "0x{subaccount_addr}",
    12345,
    "0x{market_addr}"
  ]
}
```

## Appendix C: Feature Matrix

| Feature | Required | Rust | Swift | Kotlin | Go |
|---|---|---|---|---|---|
| REST Client | YES | reqwest | URLSession | Ktor | net/http |
| WebSocket Client | YES | tokio-tungstenite | URLSessionWebSocketTask | Ktor/OkHttp | gorilla/websocket |
| Transaction Builder | YES | aptos-sdk | Custom BCS | Custom BCS | Custom BCS |
| Transaction Signing | YES | Ed25519 | Ed25519 | Ed25519 | Ed25519 |
| Gas Station | YES | HTTP POST | HTTP POST | HTTP POST | HTTP POST |
| JSON Serialization | YES | serde_json | Codable | kotlinx.serialization | encoding/json |
| Schema Validation | RECOMMENDED | serde + custom | Codable | kotlinx.serialization | json + custom |
| Connection Pooling | YES | reqwest built-in | URLSession built-in | Ktor built-in | http.Client |
| Async/Concurrent | YES | tokio async | Swift concurrency | coroutines | goroutines |
| Type Safety | YES | Rust type system | Swift generics | Kotlin generics | Go generics |
| Error Handling | YES | Result<T,E> | throws/async throws | Result/exceptions | (T, error) |
