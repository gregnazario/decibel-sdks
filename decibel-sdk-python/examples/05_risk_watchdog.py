#!/usr/bin/env python3
"""
Risk Watchdog — monitor positions and take emergency action on Decibel testnet.

Runs as a background service monitoring all positions across subaccounts.
When risk limits are breached, it logs alerts and (in production) would
cancel orders and close positions.

Risk rules checked:
  1. Margin usage > 80% → WARN; > 90% → CRITICAL (cancel all orders)
  2. Liquidation distance < 15% → WARN; < 10% → CRITICAL (close position)
  3. Unprotected positions (no TP/SL) → WARN (add protection)
  4. Total exposure > 5x equity → CRITICAL (reduce positions)
  5. Funding cost > $10/hr → WARN (consider closing)

Usage:
  export BEARER_TOKEN="your_bearer_token"
  export SUBACCOUNT_ADDRESS="0xyour_subaccount"
  python 05_risk_watchdog.py
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

import httpx

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
SUBACCOUNT = os.environ.get("SUBACCOUNT_ADDRESS", "")

BASE_URL = "https://api.testnet.aptoslabs.com/decibel/api/v1"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Origin": "https://app.decibel.trade",
}


class AlertLevel(StrEnum):
    OK = "OK"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


@dataclass
class RiskAlert:
    level: AlertLevel
    rule: str
    message: str
    action: str


@dataclass
class RiskConfig:
    margin_warn_pct: float = 80.0
    margin_critical_pct: float = 90.0
    liq_distance_warn_pct: float = 15.0
    liq_distance_critical_pct: float = 10.0
    max_leverage: float = 5.0
    max_funding_cost_hourly: float = 10.0
    check_interval_s: float = 5.0
    max_checks: int = 20


async def fetch_overview(client: httpx.AsyncClient) -> dict | None:
    try:
        resp = await client.get(
            f"{BASE_URL}/account_overviews",
            params={"account": SUBACCOUNT},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError:
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


async def fetch_prices(client: httpx.AsyncClient) -> dict[str, dict]:
    try:
        resp = await client.get(f"{BASE_URL}/prices")
        resp.raise_for_status()
        return {p["market"]: p for p in resp.json()}
    except httpx.HTTPStatusError:
        return {}


def check_margin(overview: dict, config: RiskConfig) -> list[RiskAlert]:
    alerts = []
    equity = overview.get("perp_equity_balance", 0)
    margin = overview.get("total_margin", 0)

    if equity <= 0:
        return alerts

    usage_pct = margin / equity * 100

    if usage_pct >= config.margin_critical_pct:
        alerts.append(RiskAlert(
            level=AlertLevel.CRITICAL,
            rule="margin_usage",
            message=f"Margin usage {usage_pct:.1f}% >= {config.margin_critical_pct}%",
            action="CANCEL all open orders immediately",
        ))
    elif usage_pct >= config.margin_warn_pct:
        alerts.append(RiskAlert(
            level=AlertLevel.WARN,
            rule="margin_usage",
            message=f"Margin usage {usage_pct:.1f}% >= {config.margin_warn_pct}%",
            action="Consider reducing positions",
        ))

    return alerts


def check_liquidation_distance(
    positions: list[dict],
    prices: dict[str, dict],
    config: RiskConfig,
) -> list[RiskAlert]:
    alerts = []

    for pos in positions:
        size = pos.get("size", 0)
        if size == 0:
            continue

        market = pos.get("market", "?")
        liq_price = pos.get("estimated_liquidation_price", 0)
        px = prices.get(market, {})
        mark = px.get("mark_px", 0)

        if mark <= 0 or liq_price <= 0:
            continue

        distance_pct = abs(mark - liq_price) / mark * 100

        if distance_pct < config.liq_distance_critical_pct:
            alerts.append(RiskAlert(
                level=AlertLevel.CRITICAL,
                rule="liquidation_distance",
                message=f"{market[:16]}...: liq distance {distance_pct:.1f}% < {config.liq_distance_critical_pct}%",
                action=f"CLOSE position on {market[:16]}... immediately",
            ))
        elif distance_pct < config.liq_distance_warn_pct:
            alerts.append(RiskAlert(
                level=AlertLevel.WARN,
                rule="liquidation_distance",
                message=f"{market[:16]}...: liq distance {distance_pct:.1f}% < {config.liq_distance_warn_pct}%",
                action="Add collateral or reduce position size",
            ))

    return alerts


def check_unprotected_positions(positions: list[dict]) -> list[RiskAlert]:
    alerts = []
    for pos in positions:
        size = pos.get("size", 0)
        if size == 0:
            continue

        has_tp = pos.get("tp_order_id") is not None
        has_sl = pos.get("sl_order_id") is not None
        market = pos.get("market", "?")

        if not has_tp or not has_sl:
            missing = []
            if not has_tp:
                missing.append("TP")
            if not has_sl:
                missing.append("SL")
            alerts.append(RiskAlert(
                level=AlertLevel.WARN,
                rule="unprotected_position",
                message=f"{market[:16]}...: missing {'/'.join(missing)}",
                action=f"Add {'and '.join(missing)} orders for protection",
            ))

    return alerts


def check_leverage(
    overview: dict,
    positions: list[dict],
    prices: dict[str, dict],
    config: RiskConfig,
) -> list[RiskAlert]:
    alerts = []
    equity = overview.get("perp_equity_balance", 0)
    if equity <= 0:
        return alerts

    total_notional = 0
    for pos in positions:
        size = pos.get("size", 0)
        market = pos.get("market", "?")
        px = prices.get(market, {})
        mark = px.get("mark_px", pos.get("entry_price", 0))
        total_notional += abs(size) * mark

    effective_leverage = total_notional / equity if equity > 0 else 0

    if effective_leverage > config.max_leverage:
        alerts.append(RiskAlert(
            level=AlertLevel.CRITICAL,
            rule="leverage",
            message=f"Effective leverage {effective_leverage:.1f}x > {config.max_leverage}x limit",
            action="Reduce positions to bring leverage within limits",
        ))

    return alerts


def check_funding_cost(
    positions: list[dict],
    prices: dict[str, dict],
    config: RiskConfig,
) -> list[RiskAlert]:
    alerts = []
    total_hourly = 0

    for pos in positions:
        size = pos.get("size", 0)
        if size == 0:
            continue

        market = pos.get("market", "?")
        px = prices.get(market, {})
        funding_bps = px.get("funding_rate_bps", 0)
        mark = px.get("mark_px", 0)
        notional = abs(size) * mark
        hourly_cost = notional * abs(funding_bps) / 10_000
        total_hourly += hourly_cost

    if total_hourly > config.max_funding_cost_hourly:
        alerts.append(RiskAlert(
            level=AlertLevel.WARN,
            rule="funding_cost",
            message=f"Total funding cost ${total_hourly:.2f}/hr > ${config.max_funding_cost_hourly:.2f}/hr",
            action="Review positions paying high funding",
        ))

    return alerts


def print_alerts(alerts: list[RiskAlert], check_num: int):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

    criticals = [a for a in alerts if a.level == AlertLevel.CRITICAL]
    warns = [a for a in alerts if a.level == AlertLevel.WARN]

    if not alerts:
        print(f"  [{ts}] Check #{check_num}: ✓ All clear — no risk alerts")
        return

    print(f"\n  [{ts}] Check #{check_num}: {len(criticals)} CRITICAL, {len(warns)} WARN")
    print("  " + "-" * 60)

    for alert in criticals:
        print(f"  🔴 CRITICAL [{alert.rule}]")
        print(f"     {alert.message}")
        print(f"     → {alert.action}")

    for alert in warns:
        print(f"  🟡 WARN [{alert.rule}]")
        print(f"     {alert.message}")
        print(f"     → {alert.action}")


async def run_watchdog():
    config = RiskConfig()

    print("=" * 60)
    print("  DECIBEL RISK WATCHDOG (Demo)")
    print("=" * 60)
    print(f"  Subaccount:    {SUBACCOUNT[:10]}...{SUBACCOUNT[-6:]}")
    print(f"  Margin warn:   {config.margin_warn_pct}%")
    print(f"  Margin crit:   {config.margin_critical_pct}%")
    print(f"  Liq warn:      {config.liq_distance_warn_pct}%")
    print(f"  Liq crit:      {config.liq_distance_critical_pct}%")
    print(f"  Max leverage:  {config.max_leverage}x")
    print(f"  Max funding:   ${config.max_funding_cost_hourly}/hr")
    print(f"  Interval:      {config.check_interval_s}s")
    print(f"  Demo checks:   {config.max_checks}")
    print("=" * 60)

    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        for check_num in range(1, config.max_checks + 1):
            overview, positions, prices = await asyncio.gather(
                fetch_overview(client),
                fetch_positions(client),
                fetch_prices(client),
            )

            alerts: list[RiskAlert] = []

            if overview:
                alerts.extend(check_margin(overview, config))
                alerts.extend(check_leverage(overview, positions, prices, config))

            alerts.extend(check_liquidation_distance(positions, prices, config))
            alerts.extend(check_unprotected_positions(positions))
            alerts.extend(check_funding_cost(positions, prices, config))

            print_alerts(alerts, check_num)

            criticals = [a for a in alerts if a.level == AlertLevel.CRITICAL]
            if criticals:
                print("\n  ⚠️  CRITICAL alerts detected!")
                print("  In production, the watchdog would now:")
                for c in criticals:
                    print(f"    → {c.action}")

            await asyncio.sleep(config.check_interval_s)

    print("\n" + "=" * 60)
    print("  Risk watchdog demo complete.")
    print("  In production, run this continuously with WebSocket subscriptions.")
    print("  See docs/v2/10-agent-patterns.md Pattern 5 for the full architecture.")
    print("=" * 60)


async def main():
    if not BEARER_TOKEN:
        print("Error: set BEARER_TOKEN environment variable")
        sys.exit(1)
    if not SUBACCOUNT:
        print("Error: set SUBACCOUNT_ADDRESS environment variable")
        sys.exit(1)

    await run_watchdog()


if __name__ == "__main__":
    asyncio.run(main())
