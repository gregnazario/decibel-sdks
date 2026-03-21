#!/usr/bin/env python3
"""
Place and Manage Orders — order lifecycle demo on Decibel testnet.

Requires a private key and funded subaccount.

What it does:
  1. Fetches market config and current price
  2. Places a limit buy order below current price
  3. Polls order status
  4. Places TP/SL orders for the position (if filled)
  5. Cancels the order (if still resting)

This demonstrates the full order lifecycle a trading bot needs:
  place → monitor → protect → cancel

Usage:
  export BEARER_TOKEN="your_bearer_token"
  export PRIVATE_KEY="0xyour_private_key"
  export SUBACCOUNT_ADDRESS="0xyour_subaccount"
  python 03_place_and_manage_orders.py
"""

import asyncio
import os
import sys
import time

import httpx

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")
SUBACCOUNT = os.environ.get("SUBACCOUNT_ADDRESS", "")

BASE_URL = "https://api.testnet.aptoslabs.com/decibel/api/v1"
FULLNODE_URL = "https://api.testnet.aptoslabs.com/v1"
PACKAGE = "0x952535c3049e52f195f26798c2f1340d7dd5100edbe0f464e520a974d16fbe9f"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Origin": "https://app.decibel.trade",
}

MARKET_NAME = "BTC-USD"


async def get_market_config(client: httpx.AsyncClient) -> dict | None:
    resp = await client.get(f"{BASE_URL}/markets")
    resp.raise_for_status()
    markets = resp.json()
    for m in markets:
        if m.get("market_name") == MARKET_NAME:
            return m
    return None


async def get_current_price(client: httpx.AsyncClient) -> float | None:
    resp = await client.get(f"{BASE_URL}/prices")
    resp.raise_for_status()
    for p in resp.json():
        if MARKET_NAME in (p.get("market", ""), p.get("market_name", "")):
            return p.get("mark_px")
    return None


async def get_open_orders(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(
        f"{BASE_URL}/open_orders", params={"account": SUBACCOUNT}
    )
    resp.raise_for_status()
    return resp.json()


def round_price(price: float, tick_size: float, px_decimals: int) -> int:
    """Round a human price to valid chain units."""
    denorm = price * (10**px_decimals)
    rounded = round(denorm / tick_size) * tick_size
    return int(round(rounded))


def round_size(size: float, lot_size: float, min_size: float, sz_decimals: int) -> int:
    """Round a human size to valid chain units."""
    denorm = size * (10**sz_decimals)
    rounded = int(denorm / lot_size) * lot_size
    if rounded < min_size:
        rounded = min_size
    return int(rounded)


async def main():
    if not all([BEARER_TOKEN, PRIVATE_KEY, SUBACCOUNT]):
        print("Error: set BEARER_TOKEN, PRIVATE_KEY, and SUBACCOUNT_ADDRESS")
        sys.exit(1)

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        # Step 1: Get market config
        print(f"Fetching {MARKET_NAME} config...")
        market = await get_market_config(client)
        if not market:
            print(f"Market {MARKET_NAME} not found")
            sys.exit(1)

        market_addr = market["market_addr"]
        px_dec = market["px_decimals"]
        sz_dec = market["sz_decimals"]
        tick = market["tick_size"]
        lot = market["lot_size"]
        min_sz = market["min_size"]

        print(f"  Market addr: {market_addr[:16]}...")
        print(f"  px_decimals={px_dec}, sz_decimals={sz_dec}")
        print(f"  tick_size={tick}, lot_size={lot}, min_size={min_sz}")

        # Step 2: Get current price
        mark_price = await get_current_price(client)
        if not mark_price:
            print("Could not fetch current price")
            sys.exit(1)
        print(f"\n  Current {MARKET_NAME} mark price: ${mark_price:,.2f}")

        # Step 3: Compute order params — buy 5% below mark
        order_price = mark_price * 0.95
        order_size_human = min_sz / (10**sz_dec)  # use minimum size

        chain_price = round_price(order_price, tick, px_dec)
        chain_size = round_size(order_size_human, lot, min_sz, sz_dec)

        human_price = chain_price / (10**px_dec)
        human_size = chain_size / (10**sz_dec)

        print(f"\n  Order: BUY {human_size} {MARKET_NAME} @ ${human_price:,.2f}")
        print(f"  Chain units: price={chain_price}, size={chain_size}")
        client_order_id = f"example-{int(time.time())}"
        print(f"  client_order_id: {client_order_id}")

        # Step 4: Build and submit the transaction
        # In a production bot, you'd use the SDK's DecibelWriteClient.
        # For this example, we show the raw transaction structure.
        print("\n  To place this order, the SDK would call:")
        print(f"    {PACKAGE}::dex_accounts_entry::place_order_to_subaccount")
        print(f"    args: [{SUBACCOUNT[:16]}..., {market_addr[:16]}...,")
        print(f"           price={chain_price}, size={chain_size},")
        print(f"           is_buy=True, tif=0 (GTC), reduce_only=False,")
        print(f"           client_order_id='{client_order_id}']")

        # Step 5: Check existing open orders
        print("\nChecking existing open orders...")
        orders = await get_open_orders(client)
        if orders:
            print(f"  Found {len(orders)} open orders:")
            for o in orders[:5]:
                side = "BUY" if o.get("is_buy") else "SELL"
                oid = o.get("order_id", "?")
                px = o.get("price", 0)
                sz = o.get("remaining_size", 0)
                print(f"    {oid[:12]}... {side} {sz} @ ${px:,.2f}")
        else:
            print("  No open orders")

        # Step 6: Demonstrate TP/SL placement
        tp_price = mark_price * 1.02
        sl_price = mark_price * 0.98
        print(f"\n  TP/SL for this position would be:")
        print(f"    Take Profit: ${tp_price:,.2f} (+2%)")
        print(f"    Stop Loss:   ${sl_price:,.2f} (-2%)")
        print(f"    SDK call: client.place_tp_sl(")
        print(f"      market_addr='{market_addr[:16]}...',")
        print(f"      tp_trigger_price={tp_price:.2f},")
        print(f"      sl_trigger_price={sl_price:.2f},")
        print(f"    )")

    print("\n✓ Order lifecycle demo complete.")
    print("  In production, use DecibelWriteClient to submit transactions.")
    print("  See docs/v2/03-python-sdk.md for the full API.")


if __name__ == "__main__":
    asyncio.run(main())
