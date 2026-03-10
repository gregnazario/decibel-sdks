"""End-to-end integration example for the Decibel Python SDK.

This script demonstrates:
  1. Reading market data (REST)
  2. Streaming live prices (WebSocket)
  3. Placing an order (Write client)

Usage:
    # Read-only (no API key required for public data):
    uv run python examples/integration.py

    # With trading (requires API key and private key):
    DECIBEL_API_KEY=... DECIBEL_PRIVATE_KEY=... uv run python examples/integration.py
"""

from __future__ import annotations

import asyncio
import os

from decibel_sdk import (
    CandlestickInterval,
    DecibelReadClient,
    DecibelWriteClient,
    PlaceOrderArgs,
    TimeInForce,
    mainnet_config,
)


async def read_market_data() -> None:
    """Fetch public market data via REST."""
    config = mainnet_config()

    async with DecibelReadClient(config) as client:
        # List all available markets
        markets = await client.get_all_markets()
        print(f"Available markets ({len(markets)}):")
        for m in markets[:5]:
            print(f"  {m.market_name}  leverage={m.max_leverage}x  tick={m.tick_size}")

        if not markets:
            return

        # Get current prices
        prices = await client.get_all_market_prices()
        print(f"\nCurrent prices ({len(prices)}):")
        for p in prices[:5]:
            print(f"  {p.market}  mark={p.mark_px}  oracle={p.oracle_px}")

        # Get order book depth for the first market
        first = markets[0].market_name
        depth = await client.get_market_depth(first, limit=5)
        print(f"\n{first} order book (top 5):")
        for bid in depth.bids[:5]:
            print(f"  BID  {bid.price}  x{bid.size}")
        for ask in depth.asks[:5]:
            print(f"  ASK  {ask.price}  x{ask.size}")

        # Get recent candlesticks
        import time

        now = int(time.time())
        candles = await client.get_candlesticks(
            first,
            CandlestickInterval.ONE_HOUR,
            start_time=now - 86400,
            end_time=now,
        )
        print(f"\n{first} 1h candles (last 24h): {len(candles)} bars")
        if candles:
            last = candles[-1]
            print(f"  Latest: O={last.open} H={last.high} L={last.low} C={last.close}")


async def stream_prices() -> None:
    """Stream live market prices via WebSocket."""
    config = mainnet_config()

    async with DecibelReadClient(config) as client:
        print("\nStreaming BTC-USD prices (5 ticks)...")
        async with client.subscribe_market_price("BTC-USD") as prices:
            count = 0
            async for price in prices:
                print(f"  mark={price.mark_px}  mid={price.mid_px}  oi={price.open_interest}")
                count += 1
                if count >= 5:
                    break


async def place_order_example() -> None:
    """Place a limit order (requires API key and private key)."""
    api_key = os.environ.get("DECIBEL_API_KEY")
    private_key = os.environ.get("DECIBEL_PRIVATE_KEY")

    if not api_key or not private_key:
        print("\nSkipping order placement (set DECIBEL_API_KEY and DECIBEL_PRIVATE_KEY)")
        return

    config = mainnet_config()
    account_address = os.environ.get("DECIBEL_ACCOUNT_ADDRESS", "")
    if not account_address:
        print("\nSkipping order placement (set DECIBEL_ACCOUNT_ADDRESS)")
        return

    writer = DecibelWriteClient(
        config=config,
        private_key_hex=private_key,
        account_address=account_address,
        api_key=api_key,
    )
    reader = DecibelReadClient(config, api_key=api_key)

    try:
        # Get market info for tick/lot sizes
        market = await reader.get_market_by_name("BTC-USD")

        args = PlaceOrderArgs(
            market_name="BTC-USD",
            is_buy=True,
            size=market.min_size,
            price=30000.0,
            time_in_force=TimeInForce.GOOD_TILL_CANCELED,
            is_reduce_only=False,
        )

        result = await writer.place_order(args)
        if result.success:
            print(f"\nOrder placed! ID: {result.order_id}, TX: {result.transaction_hash}")
        else:
            print(f"\nOrder failed: {result.error}")
    finally:
        await reader.close()


async def main() -> None:
    print("=== Decibel Python SDK Integration Example ===\n")

    await read_market_data()
    await stream_prices()
    await place_order_example()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
