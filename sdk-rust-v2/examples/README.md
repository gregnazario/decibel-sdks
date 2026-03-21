# Decibel SDK v2 — Example Trading Bots

Example programs demonstrating trading bot patterns against the Decibel testnet
using the Rust v2 SDK.

> **Warning**: These examples target the Decibel testnet. They are for
> educational purposes only and should not be used with real funds without
> thorough review and modification.

## Prerequisites

- Rust 1.75+
- A Decibel testnet bearer token (for examples that hit the REST API)

## Setup

```bash
# Clone and enter the SDK directory
cd sdk-rust-v2

# Set environment variables (examples 01 & 02 need these)
export BEARER_TOKEN="your_testnet_api_token"
export SUBACCOUNT_ADDRESS="0xYourSubaccountAddress"
```

## Examples

### 01 — Market Monitor

Read-only dashboard that fetches market configs, prices, and orderbook depth
from the testnet REST API.

```bash
cargo run --example 01_market_monitor
```

**Uses**: `PerpMarketConfig`, `MarketPrice`, `MarketDepth`
**Env vars**: `BEARER_TOKEN`

### 02 — Account Dashboard

Fetches account overview, open positions, and orders. Computes margin usage,
liquidation buffer, and unrealized PnL using SDK model methods.

```bash
cargo run --example 02_account_dashboard
```

**Uses**: `AccountOverview`, `UserPosition`, `UserOpenOrder`
**Env vars**: `BEARER_TOKEN`, `SUBACCOUNT_ADDRESS`

### 03 — Place and Manage Orders

Offline demo that computes order parameters (sizing, rounding, chain-unit
conversion) and shows the exact Move function call that would be submitted.
Includes TP/SL price computation and leverage checks.

```bash
cargo run --example 03_place_and_manage_orders
```

**Uses**: `amount_to_chain_units`, `round_to_valid_price`, `round_to_valid_order_size`
**Env vars**: (none)

### 04 — Market Making Bot

Simulated market-making loop that computes multi-level bid/ask quotes with
inventory skew, tracks fills, and checks margin limits — pulling quotes when
risk thresholds are exceeded.

```bash
cargo run --example 04_market_making_bot
```

**Uses**: `BulkOrderManager`, `PriceSize`
**Env vars**: (none)

### 05 — Risk Watchdog

Runs multiple risk scenarios through the SDK's `PositionStateManager` and
`RiskMonitor`. Checks margin usage, liquidation distance, and unprotected
positions, printing alerts at WARN and CRITICAL levels.

```bash
cargo run --example 05_risk_watchdog
```

**Uses**: `PositionStateManager`, `RiskMonitor`
**Env vars**: (none)

## Build All Examples

```bash
cargo build --examples
```

## Testnet API

The examples that make HTTP calls target:

```
https://api.testnet.aptoslabs.com/decibel/api/v1
```

Endpoints used:
- `GET /markets` — list perpetual market configurations
- `GET /prices` — current mark, oracle, and funding data
- `GET /depth?market=<addr>` — orderbook depth
- `GET /account/overview?subaccount=<addr>` — account summary
- `GET /account/positions?subaccount=<addr>` — open positions
- `GET /account/orders?subaccount=<addr>` — open orders
