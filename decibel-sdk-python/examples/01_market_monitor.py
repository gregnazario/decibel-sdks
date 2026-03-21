#!/usr/bin/env python3
"""
Market Monitor — stream live prices and orderbook depth from Decibel testnet.

This is a read-only bot. No private key required.

What it does:
  1. Connects to the Decibel REST API and fetches all available markets
  2. Fetches current prices and 24h context for each market
  3. Subscribes to real-time price updates via WebSocket
  4. Displays a live dashboard of prices, funding rates, and orderbook state

Usage:
  export BEARER_TOKEN="your_bearer_token"
  python 01_market_monitor.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import httpx

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
BASE_URL = "https://api.testnet.aptoslabs.com/decibel/api/v1"
WS_URL = "wss://api.testnet.aptoslabs.com/decibel/ws"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Origin": "https://app.decibel.trade",
}


async def fetch_markets(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"{BASE_URL}/markets")
    resp.raise_for_status()
    return resp.json()


async def fetch_prices(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"{BASE_URL}/prices")
    resp.raise_for_status()
    return resp.json()


async def fetch_depth(client: httpx.AsyncClient, market_addr: str, limit: int = 5) -> dict:
    resp = await client.get(f"{BASE_URL}/depth/{market_addr}", params={"limit": limit})
    resp.raise_for_status()
    return resp.json()


async def fetch_asset_contexts(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"{BASE_URL}/asset_contexts")
    resp.raise_for_status()
    return resp.json()


def format_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}"
    else:
        return f"${price:.6f}"


def print_dashboard(markets: list[dict], prices: list[dict], contexts: list[dict]):
    price_map = {p.get("market", ""): p for p in prices}
    ctx_map = {c.get("market", ""): c for c in contexts}

    print("\n" + "=" * 90)
    print(f"  DECIBEL MARKET DASHBOARD — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 90)
    print(f"  {'Market':<12} {'Mark Price':>14} {'Oracle':>14} {'Funding':>10} {'24h Vol':>14} {'OI':>14}")
    print("-" * 90)

    for mkt in sorted(markets, key=lambda m: m.get("market_name", "")):
        name = mkt.get("market_name", "?")
        addr = mkt.get("market_addr", "")

        px = price_map.get(addr, {})
        ctx = ctx_map.get(name, ctx_map.get(addr, {}))

        mark = px.get("mark_px", 0)
        oracle = px.get("oracle_px", 0)
        funding_bps = px.get("funding_rate_bps", 0)
        funding_dir = "L→S" if px.get("is_funding_positive", True) else "S→L"
        vol_24h = ctx.get("volume_24h", 0)
        oi = px.get("open_interest", 0)

        print(
            f"  {name:<12} {format_price(mark):>14} {format_price(oracle):>14} "
            f"{funding_bps:>+7.3f}bp {funding_dir} {vol_24h:>12,.0f} {oi:>12,.0f}"
        )

    print("=" * 90)


async def print_orderbook(client: httpx.AsyncClient, market: dict):
    name = market.get("market_name", "?")
    addr = market.get("market_addr", "")
    try:
        depth = await fetch_depth(client, addr, limit=5)
    except httpx.HTTPStatusError:
        print(f"\n  Could not fetch depth for {name}")
        return

    bids = depth.get("bids", [])
    asks = depth.get("asks", [])

    print(f"\n  Orderbook: {name}")
    print(f"  {'Ask Price':>14} {'Size':>10}  |  {'Bid Price':>14} {'Size':>10}")
    print("  " + "-" * 56)

    max_levels = max(len(bids), len(asks))
    for i in range(min(max_levels, 5)):
        ask_str = ""
        bid_str = ""
        if i < len(asks):
            a = asks[i]
            ask_str = f"  {a['price']:>14.4f} {a['size']:>10.4f}"
        else:
            ask_str = " " * 28

        if i < len(bids):
            b = bids[i]
            bid_str = f"  {b['price']:>14.4f} {b['size']:>10.4f}"

        print(f"{ask_str}  |{bid_str}")


async def stream_prices():
    """Subscribe to real-time price updates via WebSocket."""
    import json

    import websockets

    print("\n  Connecting to WebSocket for live price updates...")
    uri = f"{WS_URL}"
    extra_headers = {"Sec-Websocket-Protocol": f"decibel, {BEARER_TOKEN}"}

    try:
        async with websockets.connect(uri, additional_headers=extra_headers) as ws:
            sub_msg = json.dumps({"method": "subscribe", "topic": "all_market_prices"})
            await ws.send(sub_msg)

            resp = await asyncio.wait_for(ws.recv(), timeout=10)
            resp_data = json.loads(resp)
            if resp_data.get("success"):
                print("  ✓ Subscribed to all_market_prices")
            else:
                print(f"  ✗ Subscribe failed: {resp_data}")
                return

            count = 0
            async for msg in ws:
                data = json.loads(msg)
                topic = data.get("topic", "")
                if "all_market_prices" in topic:
                    prices_data = data.get("data", {}).get("prices", [])
                    if prices_data:
                        count += 1
                        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
                        sample = prices_data[0]
                        mkt = sample.get("market", "?")
                        mark = sample.get("mark_px", 0)
                        print(
                            f"  [{ts}] Update #{count}: {len(prices_data)} markets "
                            f"(first: {mkt} mark={format_price(mark)})"
                        )
                    if count >= 20:
                        print("\n  Received 20 updates, stopping stream demo.")
                        break
    except Exception as e:
        print(f"  WebSocket error: {e}")


async def main():
    if not BEARER_TOKEN:
        print("Error: set BEARER_TOKEN environment variable")
        print("Get one from https://geomi.dev (Decibel Devnet)")
        sys.exit(1)

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        print("Fetching markets...")
        markets = await fetch_markets(client)
        print(f"  Found {len(markets)} markets")

        print("Fetching prices...")
        prices = await fetch_prices(client)

        print("Fetching 24h context...")
        try:
            contexts = await fetch_asset_contexts(client)
        except httpx.HTTPStatusError:
            contexts = []

        print_dashboard(markets, prices, contexts)

        if markets:
            await print_orderbook(client, markets[0])

    await stream_prices()


if __name__ == "__main__":
    asyncio.run(main())
