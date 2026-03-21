#!/usr/bin/env python3
"""
Market Making Bot — two-sided quoting with inventory management on Decibel testnet.

Demonstrates the core market making loop:
  1. Subscribe to price feed
  2. Compute bid/ask quotes based on mid price + spread
  3. Skew quotes based on current inventory
  4. Track fills and adjust
  5. Monitor risk limits

This example uses REST polling for simplicity. A production bot would use
WebSocket subscriptions and the BulkOrderManager for atomic quote updates.

Usage:
  export BEARER_TOKEN="your_bearer_token"
  export PRIVATE_KEY="0xyour_private_key"
  export SUBACCOUNT_ADDRESS="0xyour_subaccount"
  python 04_market_making_bot.py
"""

import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
SUBACCOUNT = os.environ.get("SUBACCOUNT_ADDRESS", "")

BASE_URL = "https://api.testnet.aptoslabs.com/decibel/api/v1"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Origin": "https://app.decibel.trade",
}


@dataclass
class MarketMakerConfig:
    market: str = "BTC-USD"
    base_spread_bps: float = 5.0
    levels: int = 3
    size_per_level: float = 0.001
    max_inventory: float = 0.01
    max_margin_usage_pct: float = 80.0
    quote_interval_s: float = 2.0
    max_cycles: int = 15


@dataclass
class InventoryState:
    position_size: float = 0.0
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    total_buys: float = 0.0
    total_sells: float = 0.0
    num_fills: int = 0


@dataclass
class QuoteLevel:
    price: float
    size: float
    side: str


def compute_quotes(
    mid: float,
    config: MarketMakerConfig,
    inventory: InventoryState,
) -> tuple[list[QuoteLevel], list[QuoteLevel]]:
    """Compute bid/ask levels with inventory skew."""
    half_spread = mid * config.base_spread_bps / 10_000

    inventory_ratio = inventory.position_size / config.max_inventory if config.max_inventory else 0
    skew = inventory_ratio * half_spread

    bids = []
    asks = []

    for i in range(config.levels):
        offset = half_spread * (i + 1)

        bid_price = mid - offset + skew
        ask_price = mid + offset + skew

        bids.append(QuoteLevel(price=bid_price, size=config.size_per_level, side="BUY"))
        asks.append(QuoteLevel(price=ask_price, size=config.size_per_level, side="SELL"))

    return bids, asks


async def fetch_mid_price(client: httpx.AsyncClient, market_name: str) -> float | None:
    """Fetch the mid price from the REST API."""
    try:
        resp = await client.get(f"{BASE_URL}/prices")
        resp.raise_for_status()
        for p in resp.json():
            if market_name in str(p.get("market", "")):
                return p.get("mid_px")
    except httpx.HTTPStatusError:
        pass
    return None


async def fetch_position(client: httpx.AsyncClient) -> dict | None:
    """Fetch current position for the subaccount."""
    try:
        resp = await client.get(
            f"{BASE_URL}/account_positions",
            params={"account": SUBACCOUNT},
        )
        resp.raise_for_status()
        positions = resp.json()
        return positions[0] if positions else None
    except httpx.HTTPStatusError:
        return None


async def fetch_margin_usage(client: httpx.AsyncClient) -> float:
    """Fetch current margin usage percentage."""
    try:
        resp = await client.get(
            f"{BASE_URL}/account_overviews",
            params={"account": SUBACCOUNT},
        )
        resp.raise_for_status()
        overview = resp.json()
        equity = overview.get("perp_equity_balance", 0)
        margin = overview.get("total_margin", 0)
        return (margin / equity * 100) if equity > 0 else 0
    except httpx.HTTPStatusError:
        return 0


def print_quote_update(
    cycle: int,
    mid: float,
    bids: list[QuoteLevel],
    asks: list[QuoteLevel],
    inventory: InventoryState,
    margin_pct: float,
):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    inv_dir = "LONG" if inventory.position_size > 0 else "SHORT" if inventory.position_size < 0 else "FLAT"

    print(f"\n  [{ts}] Cycle {cycle}")
    print(f"  Mid: ${mid:,.2f} | Inventory: {inventory.position_size:+.6f} ({inv_dir}) | Margin: {margin_pct:.1f}%")

    print(f"  {'BIDS':^30} | {'ASKS':^30}")
    for i in range(len(bids)):
        b = bids[i]
        a = asks[i]
        print(
            f"  {b.size:.4f} @ ${b.price:>10,.2f}  "
            f"|  ${a.price:>10,.2f} @ {a.size:.4f}"
        )

    spread = asks[0].price - bids[0].price
    spread_bps = spread / mid * 10_000
    print(f"  Effective spread: ${spread:.2f} ({spread_bps:.1f} bps)")


async def run_market_maker():
    config = MarketMakerConfig()
    inventory = InventoryState()

    print("=" * 60)
    print("  DECIBEL MARKET MAKING BOT (Demo)")
    print("=" * 60)
    print(f"  Market:        {config.market}")
    print(f"  Base spread:   {config.base_spread_bps} bps")
    print(f"  Levels:        {config.levels}")
    print(f"  Size/level:    {config.size_per_level}")
    print(f"  Max inventory: {config.max_inventory}")
    print(f"  Max margin:    {config.max_margin_usage_pct}%")
    print(f"  Interval:      {config.quote_interval_s}s")
    print(f"  Demo cycles:   {config.max_cycles}")
    print()
    print("  NOTE: This demo computes quotes but does NOT submit them.")
    print("  In production, use BulkOrderManager.set_quotes() to submit.")
    print("=" * 60)

    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        pos = await fetch_position(client)
        if pos:
            inventory.position_size = pos.get("size", 0)
            inventory.entry_price = pos.get("entry_price", 0)
            print(f"\n  Loaded existing position: {inventory.position_size:+.6f}")

        for cycle in range(1, config.max_cycles + 1):
            mid = await fetch_mid_price(client, config.market)
            if mid is None:
                print(f"  Cycle {cycle}: no price available, waiting...")
                await asyncio.sleep(config.quote_interval_s)
                continue

            margin_pct = await fetch_margin_usage(client)

            if margin_pct > config.max_margin_usage_pct:
                print(f"\n  ⚠️ Margin usage {margin_pct:.1f}% > {config.max_margin_usage_pct}% — PULLING QUOTES")
                print("  In production: bulk.cancel_all()")
                await asyncio.sleep(config.quote_interval_s)
                continue

            if abs(inventory.position_size) > config.max_inventory:
                print(f"\n  ⚠️ Inventory {inventory.position_size:+.6f} exceeds limit — skewing aggressively")

            bids, asks = compute_quotes(mid, config, inventory)
            print_quote_update(cycle, mid, bids, asks, inventory, margin_pct)

            print("  → Would call: bulk.set_quotes(bids=[...], asks=[...])")

            await asyncio.sleep(config.quote_interval_s)

    print("\n" + "=" * 60)
    print("  Market making demo complete.")
    print("  In production, integrate with BulkOrderManager for atomic quotes.")
    print("  See docs/v2/10-agent-patterns.md Pattern 1 for the full architecture.")
    print("=" * 60)


async def main():
    if not BEARER_TOKEN:
        print("Error: set BEARER_TOKEN environment variable")
        sys.exit(1)
    if not SUBACCOUNT:
        print("Error: set SUBACCOUNT_ADDRESS environment variable")
        sys.exit(1)

    await run_market_maker()


if __name__ == "__main__":
    asyncio.run(main())
