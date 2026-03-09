"""Integration examples for the Decibel Python SDK.

This file demonstrates how to use the SDK for common operations.
"""

import asyncio
from datetime import datetime, timedelta

from decibel import (
    CandlestickInterval,
    DecibelConfig,
    DecibelReadClient,
    DecibelWriteClient,
    Ed25519Signer,
    TimeInForce,
    VolumeWindow,
    get_market_addr,
    get_primary_subaccount_addr,
)


async def example_market_data():
    """Example: Fetch market data."""
    print("=== Market Data Example ===")

    # Connect to testnet
    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    try:
        # Get all markets
        markets = await client.get_all_markets()
        print(f"Found {len(markets)} markets")
        for market in markets[:3]:  # Show first 3
            print(f"  - {market.market_name}: max_leverage={market.max_leverage}x")

        # Get market prices
        prices = await client.get_all_market_prices()
        print(f"\nCurrent prices:")
        for price in prices[:5]:  # Show first 5
            print(f"  - {price.market}: ${price.mark_px:.2f}")

        # Get market depth (order book)
        depth = await client.get_market_depth("BTC-USD", limit=10)
        print(f"\nBTC-USD Order Book:")
        print(f"  Bids: {len(depth.bids)} levels")
        if depth.bids:
            print(f"    Best bid: ${depth.bids[0].price:.2f} ({depth.bids[0].size:.4f})")
        print(f"  Asks: {len(depth.asks)} levels")
        if depth.asks:
            print(f"    Best ask: ${depth.asks[0].price:.2f} ({depth.asks[0].size:.4f})")

        # Get recent trades
        trades = await client.get_market_trades("BTC-USD", limit=5)
        print(f"\nRecent BTC-USD trades:")
        for trade in trades:
            side = "BUY" if trade.is_buy else "SELL"
            print(f"  - {side} ${trade.price:.2f} x {trade.size:.4f}")

    finally:
        await client.close()


async def example_account_data():
    """Example: Fetch account data."""
    print("\n=== Account Data Example ===")

    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    try:
        # Replace with actual subaccount address
        subaccount_addr = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234"

        # Get account overview
        overview = await client.get_account_overview(
            subaccount_addr,
            volume_window=VolumeWindow.SEVEN_DAYS,
            include_performance=False,
        )
        print(f"Account Overview:")
        print(f"  Equity: ${overview.perp_equity_balance:.2f}")
        print(f"  Unrealized PnL: ${overview.unrealized_pnl:.2f}")
        print(f"  Cross Margin Ratio: {overview.cross_margin_ratio:.2%}")

        # Get positions
        positions = await client.get_positions(subaccount_addr)
        print(f"\nOpen Positions: {len(positions)}")
        for pos in positions:
            side = "LONG" if pos.size > 0 else "SHORT"
            print(f"  - {pos.market}: {side} {abs(pos.size):.4f} @ ${pos.entry_price:.2f}")

        # Get open orders
        orders = await client.get_open_orders(subaccount_addr)
        print(f"\nOpen Orders: {len(orders)}")
        for order in orders[:5]:  # Show first 5
            side = "BUY" if order.is_buy else "SELL"
            print(f"  - {side} ${order.price:.2f} x {order.remaining_size:.4f} ({order.status})")

    finally:
        await client.close()


async def example_websocket_subscriptions():
    """Example: WebSocket subscriptions for real-time data."""
    print("\n=== WebSocket Subscription Example ===")

    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    try:
        # Connect WebSocket
        await client.ws.connect()

        # Subscribe to BTC-USD price updates
        async def on_price_update(data):
            price_data = data
            if isinstance(price_data, dict):
                print(f"BTC-USD Price Update: ${price_data.get('mark_px', 0):.2f}")

        await client.ws.subscribe_market_price("BTC-USD", on_price_update)

        # Subscribe to account overview updates
        subaccount_addr = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234"

        async def on_account_update(data):
            overview = data
            if isinstance(overview, dict):
                print(f"Account Equity: ${overview.get('perp_equity_balance', 0):.2f}")

        await client.ws.subscribe_account_overview(subaccount_addr, on_account_update)

        # Keep connection alive for 30 seconds
        print("Listening for updates for 30 seconds...")
        await asyncio.sleep(30)

        await client.ws.disconnect()

    finally:
        await client.close()


async def example_place_order():
    """Example: Place an order (requires private key)."""
    print("\n=== Place Order Example ===")

    config = DecibelConfig.testnet()

    # Generate a new keypair (in production, load from secure storage)
    signer = Ed25519Signer.generate()
    print(f"Generated new account: {signer.to_hex()[:20]}...")

    client = DecibelWriteClient(config, signer)

    try:
        # Get primary subaccount address
        sender = client._sender
        subaccount_addr = get_primary_subaccount_addr(
            sender, config.compat_version.value, config.deployment.package
        )
        print(f"Primary subaccount: {subaccount_addr}")

        # Place a limit order
        result = await client.place_order(
            market_name="BTC-USD",
            price=45000.0,
            size=0.001,
            is_buy=True,
            time_in_force=TimeInForce.GOOD_TILL_CANCELED,
            is_reduce_only=False,
        )

        if result.success:
            print(f"Order placed successfully!")
            print(f"  Order ID: {result.order_id}")
            print(f"  Transaction: {result.transaction_hash}")
        else:
            print(f"Order failed: {result.error}")

    finally:
        await client.close()


async def example_candlesticks():
    """Example: Fetch candlestick data."""
    print("\n=== Candlestick Data Example ===")

    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    try:
        # Get candlesticks for the last 24 hours
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)

        candlesticks = await client.get_candlesticks(
            market_name="BTC-USD",
            interval=CandlestickInterval.ONE_HOUR,
            start_time=start_time,
            end_time=end_time,
        )

        print(f"BTC-USD 1H Candlesticks (last 24h): {len(candlesticks)} candles")
        for candle in candlesticks[-5:]:  # Show last 5
            print(f"  - {candle.t}: O=${candle.o:.2f} H=${candle.h:.2f} L=${candle.l:.2f} C=${candle.c:.2f} V={candle.v:.2f}")

    finally:
        await client.close()


async def example_vaults():
    """Example: Fetch vault data."""
    print("\n=== Vaults Example ===")

    config = DecibelConfig.testnet()
    client = DecibelReadClient(config)

    try:
        # Get all vaults
        vaults_resp = await client.get_vaults()
        print(f"Total vaults: {vaults_resp.total_count}")
        print(f"Total TVL: ${vaults_resp.total_value_locked:,.2f}")
        print(f"Total Volume: ${vaults_resp.total_volume:,.2f}")

        print(f"\nTop 5 vaults by TVL:")
        for vault in vaults_resp.items[:5]:
            print(f"  - {vault.name}: ${vault.tvl or 0:,.2f} TVL ({vault.status})")

    finally:
        await client.close()


async def example_utility_functions():
    """Example: Use utility functions."""
    print("\n=== Utility Functions Example ===")

    # Derive addresses
    market_addr = get_market_addr("BTC-USD", "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234")
    print(f"Market address for BTC-USD: {market_addr[:20]}...")

    sub_addr = get_primary_subaccount_addr(
        "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234",
        "v0.4",
        "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    print(f"Primary subaccount: {sub_addr[:20]}...")

    vault_share_addr = get_vault_share_address("0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234")
    print(f"Vault share address: {vault_share_addr[:20]}...")

    # Round price to tick size
    rounded = round_to_tick_size(45001.73, 0.5, 2, True)
    print(f"Rounded price (45001.73 -> tick 0.5, round up): ${rounded:.2f}")

    # Generate nonce
    from decibel import generate_random_replay_protection_nonce

    nonce = generate_random_replay_protection_nonce()
    print(f"Generated nonce: {nonce}")


async def main():
    """Run all examples."""
    print("Decibel Python SDK - Integration Examples")
    print("=" * 50)

    # Run examples that don't require authentication
    await example_market_data()
    await example_candlesticks()
    await example_vaults()
    await example_utility_functions()

    # Note: The following examples require valid addresses and/or private keys
    # Uncomment to run with actual values:

    # await example_account_data()
    # await example_websocket_subscriptions()
    # await example_place_order()

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
