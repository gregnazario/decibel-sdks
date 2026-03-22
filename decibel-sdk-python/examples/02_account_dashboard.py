#!/usr/bin/env python3
"""
Account Dashboard — monitor positions, orders, margin, and risk on Decibel testnet.

Read-only bot. No private key required.

What it does:
  1. Fetches account overview (equity, margin, PnL)
  2. Lists all open positions with unrealized PnL
  3. Lists all open orders
  4. Computes risk metrics: margin usage, liquidation distance, funding costs

Usage:
  export BEARER_TOKEN="your_bearer_token"
  export SUBACCOUNT_ADDRESS="0xyour_subaccount"
  python 02_account_dashboard.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import httpx

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
SUBACCOUNT = os.environ.get("SUBACCOUNT_ADDRESS", "")
BASE_URL = "https://api.testnet.aptoslabs.com/decibel/api/v1"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Origin": "https://app.decibel.trade",
}


async def fetch_account_overview(client: httpx.AsyncClient) -> dict | None:
    try:
        resp = await client.get(
            f"{BASE_URL}/account_overviews",
            params={"account": SUBACCOUNT, "include_performance": "true"},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        print(f"  Could not fetch overview: {e.response.status_code}")
        return None


async def fetch_positions(client: httpx.AsyncClient) -> list[dict]:
    try:
        resp = await client.get(
            f"{BASE_URL}/account_positions",
            params={"account": SUBACCOUNT},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError:
        return []


async def fetch_open_orders(client: httpx.AsyncClient) -> list[dict]:
    try:
        resp = await client.get(
            f"{BASE_URL}/open_orders",
            params={"account": SUBACCOUNT},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError:
        return []


async def fetch_prices(client: httpx.AsyncClient) -> dict[str, dict]:
    try:
        resp = await client.get(f"{BASE_URL}/prices")
        resp.raise_for_status()
        prices = resp.json()
        return {p.get("market", ""): p for p in prices}
    except httpx.HTTPStatusError:
        return {}


def print_overview(overview: dict | None):
    print("\n" + "=" * 70)
    print(f"  ACCOUNT DASHBOARD — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Subaccount: {SUBACCOUNT[:10]}...{SUBACCOUNT[-6:]}")
    print("=" * 70)

    if not overview:
        print("  No account data available (subaccount may not exist yet)")
        return

    equity = overview.get("perp_equity_balance", 0)
    margin = overview.get("total_margin", 0)
    mm = overview.get("maintenance_margin", 0)
    upnl = overview.get("unrealized_pnl", 0)
    funding_cost = overview.get("unrealized_funding_cost", 0)
    withdrawable = (
        overview.get("usdc_cross_withdrawable_balance", 0)
        + overview.get("usdc_isolated_withdrawable_balance", 0)
    )

    margin_pct = (margin / equity * 100) if equity > 0 else 0
    liq_buffer = equity - mm
    liq_buffer_pct = (liq_buffer / equity * 100) if equity > 0 else 0

    print(f"\n  {'Equity:':<25} ${equity:>12,.2f}")
    print(f"  {'Unrealized PnL:':<25} ${upnl:>+12,.2f}")
    print(f"  {'Unrealized Funding:':<25} ${funding_cost:>+12,.2f}")
    print(f"  {'Margin Used:':<25} ${margin:>12,.2f}  ({margin_pct:.1f}%)")
    print(f"  {'Maintenance Margin:':<25} ${mm:>12,.2f}")
    print(f"  {'Liquidation Buffer:':<25} ${liq_buffer:>12,.2f}  ({liq_buffer_pct:.1f}%)")
    print(f"  {'Withdrawable:':<25} ${withdrawable:>12,.2f}")

    if liq_buffer_pct < 20:
        print("\n  ⚠️  WARNING: Liquidation buffer below 20% — consider reducing exposure")
    elif liq_buffer_pct < 50:
        print("\n  ⚡ Margin is getting tight — monitor closely")


def print_positions(positions: list[dict], prices: dict[str, dict]):
    print(f"\n  OPEN POSITIONS ({len(positions)})")
    print("-" * 70)

    if not positions:
        print("  No open positions")
        return

    print(f"  {'Market':<12} {'Side':<6} {'Size':>10} {'Entry':>12} {'Mark':>12} {'PnL':>12}")
    print("  " + "-" * 64)

    for pos in positions:
        market = pos.get("market", "?")
        size = pos.get("size", 0)
        entry = pos.get("entry_price", 0)
        side = "LONG" if size > 0 else "SHORT" if size < 0 else "FLAT"
        liq = pos.get("estimated_liquidation_price", 0)

        px = prices.get(market, {})
        mark = px.get("mark_px", entry)
        pnl = (mark - entry) * size

        tp = "✓" if pos.get("tp_order_id") else "✗"
        sl = "✓" if pos.get("sl_order_id") else "✗"

        market_short = market[:10] + "..." if len(market) > 12 else market
        print(
            f"  {market_short:<12} {side:<6} {abs(size):>10.4f} "
            f"${entry:>11,.2f} ${mark:>11,.2f} ${pnl:>+11,.2f}"
        )
        print(f"  {'':>12} Liq: ${liq:,.2f}  TP:{tp} SL:{sl}")


def print_orders(orders: list[dict]):
    print(f"\n  OPEN ORDERS ({len(orders)})")
    print("-" * 70)

    if not orders:
        print("  No open orders")
        return

    print(f"  {'Market':<12} {'Side':<6} {'Price':>12} {'Size':>10} {'Filled':>8} {'Type':<8}")
    print("  " + "-" * 56)

    for order in orders:
        market = order.get("market", "?")[:12]
        side = "BUY" if order.get("is_buy") else "SELL"
        price = order.get("price", 0)
        orig = order.get("orig_size", 0)
        remaining = order.get("remaining_size", 0)
        filled_pct = ((orig - remaining) / orig * 100) if orig > 0 else 0
        tif = order.get("time_in_force", "?")

        print(
            f"  {market:<12} {side:<6} ${price:>11,.2f} {orig:>10.4f} "
            f"{filled_pct:>6.1f}% {tif:<8}"
        )


async def main():
    if not BEARER_TOKEN:
        print("Error: set BEARER_TOKEN environment variable")
        sys.exit(1)
    if not SUBACCOUNT:
        print("Error: set SUBACCOUNT_ADDRESS environment variable")
        print("Create one at https://app.decibel.trade")
        sys.exit(1)

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        overview, positions, orders, prices = await asyncio.gather(
            fetch_account_overview(client),
            fetch_positions(client),
            fetch_open_orders(client),
            fetch_prices(client),
        )

        print_overview(overview)
        print_positions(positions, prices)
        print_orders(orders)

    print("\n  Dashboard complete. Run again to refresh, or integrate")
    print("  into a loop with WebSocket subscriptions for live updates.")


if __name__ == "__main__":
    asyncio.run(main())
