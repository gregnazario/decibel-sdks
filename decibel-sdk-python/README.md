# Decibel Python SDK

Python SDK for the [Decibel](https://decibel.trade) perpetual futures trading platform on Aptos.

## Features

- **Async-first API** with full `asyncio` support
- **REST API client** for market data and account queries
- **WebSocket client** for real-time data streaming
- **On-chain transaction builder** for placing orders and managing accounts
- **Type-safe models** using Pydantic v2
- **Ed25519 signing** for Aptos transactions

## Installation

```bash
pip install decibel-sdk
```

## Quick Start

### Reading Market Data

```python
import asyncio
from decibel import DecibelConfig, DecibelReadClient

async def main():
    # Connect to testnet
    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    # Get all markets
    markets = await client.get_all_markets()
    for market in markets:
        print(f"{market.market_name}: {market.mark_px}")

    # Get market prices
    prices = await client.get_all_market_prices()
    print(f"BTC price: ${prices[0].mark_px}")

asyncio.run(main())
```

### Placing Orders

```python
from decibel import DecibelConfig, DecibelWriteClient
from decibel.models import TimeInForce

async def main():
    # Initialize write client with private key
    config = DecibelConfig.testnet()
    write_client = DecibelWriteClient(config, private_key=your_private_key_bytes)

    # Place a limit order
    result = await write_client.place_order(
        market_name="BTC-USD",
        price=45000.0,
        size=0.01,
        is_buy=True,
        time_in_force=TimeInForce.GOOD_TILL_CANCELED,
        is_reduce_only=False,
    )

    if result.success:
        print(f"Order placed: {result.order_id}")
    else:
        print(f"Order failed: {result.error}")

asyncio.run(main())
```

### WebSocket Subscriptions

```python
from decibel import DecibelConfig, DecibelReadClient

async def main():
    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    # Subscribe to market prices
    async def on_price_update(price_data):
        print(f"BTC price: ${price_data.mark_px}")

    await client.ws.connect()
    await client.ws.subscribe_market_price("BTC-USD", on_price_update)

    # Keep running
    await asyncio.Event().wait()

asyncio.run(main())
```

## Configuration

The SDK provides preset configurations for different networks:

```python
from decibel import DecibelConfig

# Mainnet
config = DecibelConfig.mainnet()

# Testnet
config = DecibelConfig.testnet()

# Local development
config = DecibelConfig.local()

# Custom configuration
config = DecibelConfig(
    network=DecibelConfig.Network.CUSTOM,
    fullnode_url="https://fullnode.mainnet.aptoslabs.com/v1",
    trading_http_url="https://api.decibel.trade",
    trading_ws_url="wss://api.decibel.trade/ws",
    deployment=DecibelConfig.Deployment(
        package="0x...",
        usdc="0x...",
        testc="0x...",
        perp_engine_global="0x...",
    ),
)
```

## API Reference

### DecibelReadClient

REST API client for reading market data and account information.

**Market Data:**
- `get_all_markets()` - List all markets
- `get_market_by_name(name)` - Get market configuration
- `get_market_depth(market_name, limit)` - Get order book
- `get_all_market_prices()` - Get all market prices
- `get_market_price(market_name)` - Get specific market price
- `get_market_trades(market_name, limit)` - Get recent trades
- `get_candlesticks(market_name, interval, start_time, end_time)` - Get OHLCV data

**Account Data:**
- `get_account_overview(subaccount_addr)` - Get account overview
- `get_positions(subaccount_addr)` - Get open positions
- `get_open_orders(subaccount_addr)` - Get open orders
- `get_order_history(subaccount_addr, page_params)` - Get order history
- `get_trade_history(subaccount_addr, page_params)` - Get trade history
- `get_funding_history(subaccount_addr, page_params)` - Get funding history

**Vault Data:**
- `get_vaults(filters)` - List all vaults
- `get_user_owned_vaults(account_addr, page_params)` - Get user's vaults
- `get_vault_performance(account_addr)` - Get vault performance

### DecibelWriteClient

Client for on-chain operations (requires Ed25519 private key).

**Account Management:**
- `create_subaccount()` - Create new subaccount
- `deposit(amount, subaccount_addr)` - Deposit collateral
- `withdraw(amount, subaccount_addr)` - Withdraw collateral

**Order Management:**
- `place_order(...)` - Place limit order
- `cancel_order(order_id, market_name, subaccount_addr)` - Cancel order
- `cancel_client_order(client_order_id, market_name, subaccount_addr)` - Cancel by client ID

**TWAP Orders:**
- `place_twap_order(...)` - Place TWAP order
- `cancel_twap_order(order_id, market_addr, subaccount_addr)` - Cancel TWAP order

**TP/SL Orders:**
- `place_tp_sl_order(...)` - Place take-profit/stop-loss order
- `update_tp_order(...)` - Update take-profit order
- `update_sl_order(...)` - Update stop-loss order
- `cancel_tp_sl_order(...)` - Cancel TP/SL order

**Delegation:**
- `delegate_trading(subaccount_addr, account_to_delegate_to, expiration_timestamp_secs)` - Delegate trading
- `revoke_delegation(subaccount_addr, account_to_revoke)` - Revoke delegation

**Vault Operations:**
- `create_vault(...)` - Create new vault
- `activate_vault(vault_address)` - Activate vault
- `deposit_to_vault(vault_address, amount)` - Deposit to vault
- `withdraw_from_vault(vault_address, shares)` - Withdraw from vault

### WebSocketManager

WebSocket client for real-time data streaming.

**Subscriptions:**
- `subscribe_account_overview(subaccount_addr, callback)` - Account overview updates
- `subscribe_user_positions(subaccount_addr, callback)` - Position updates
- `subscribe_user_open_orders(subaccount_addr, callback)` - Open order updates
- `subscribe_order_updates(subaccount_addr, callback)` - Order status updates
- `subscribe_market_depth(market_name, agg_size, callback)` - Order book updates
- `subscribe_market_price(market_name, callback)` - Price updates
- `subscribe_all_market_prices(callback)` - All market prices
- `subscribe_market_trades(market_name, callback)` - Trade updates
- `subscribe_candlesticks(market_name, interval, callback)` - Candlestick updates

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Type checking
mypy decibel
```

## License

MIT
