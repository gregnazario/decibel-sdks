"""
Shared fixtures for the Decibel SDK test suite.

This conftest provides:
- Sample data factories for all core models
- Mock clients for unit testing
- Testnet client fixture for integration tests
- Helpers for asserting JSON Schema compliance
"""

import asyncio
import os
import time
from typing import Any

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Core model factories – every test can call these to get valid model instances
# ---------------------------------------------------------------------------

SAMPLE_MARKET_CONFIG = {
    "market_addr": "0xabc123",
    "market_name": "BTC-USD",
    "sz_decimals": 9,
    "px_decimals": 9,
    "max_leverage": 40.0,
    "min_size": 1000000000.0,
    "lot_size": 100000000.0,
    "tick_size": 1000000.0,
    "max_open_interest": 100000000.0,
    "margin_call_fee_pct": 1.25,
    "taker_in_next_block": False,
}

SAMPLE_MARKET_PRICE = {
    "market": "BTC-USD",
    "mark_px": 45000.0,
    "mid_px": 44999.5,
    "oracle_px": 45001.0,
    "funding_rate_bps": 0.012,
    "is_funding_positive": True,
    "open_interest": 1500000.0,
    "transaction_unix_ms": 1710000000000,
}

SAMPLE_POSITION_LONG = {
    "market": "0xabc123",
    "user": "0xsub1",
    "size": 1.5,
    "user_leverage": 10.0,
    "entry_price": 44000.0,
    "is_isolated": False,
    "unrealized_funding": -5.25,
    "estimated_liquidation_price": 40000.0,
    "tp_order_id": "tp-001",
    "tp_trigger_price": 48000.0,
    "tp_limit_price": 47900.0,
    "sl_order_id": "sl-001",
    "sl_trigger_price": 42000.0,
    "sl_limit_price": 42100.0,
    "has_fixed_sized_tpsls": False,
}

SAMPLE_POSITION_SHORT = {
    "market": "0xdef456",
    "user": "0xsub1",
    "size": -10.0,
    "user_leverage": 5.0,
    "entry_price": 3200.0,
    "is_isolated": False,
    "unrealized_funding": 2.10,
    "estimated_liquidation_price": 3600.0,
    "tp_order_id": None,
    "tp_trigger_price": None,
    "tp_limit_price": None,
    "sl_order_id": None,
    "sl_trigger_price": None,
    "sl_limit_price": None,
    "has_fixed_sized_tpsls": False,
}

SAMPLE_POSITION_FLAT = {
    "market": "0xghi789",
    "user": "0xsub1",
    "size": 0.0,
    "user_leverage": 10.0,
    "entry_price": 0.0,
    "is_isolated": False,
    "unrealized_funding": 0.0,
    "estimated_liquidation_price": 0.0,
    "tp_order_id": None,
    "tp_trigger_price": None,
    "tp_limit_price": None,
    "sl_order_id": None,
    "sl_trigger_price": None,
    "sl_limit_price": None,
    "has_fixed_sized_tpsls": False,
}

SAMPLE_ACCOUNT_OVERVIEW = {
    "perp_equity_balance": 10000.0,
    "unrealized_pnl": 500.0,
    "unrealized_funding_cost": -25.0,
    "cross_margin_ratio": 0.15,
    "maintenance_margin": 1500.0,
    "cross_account_leverage_ratio": 3.5,
    "cross_account_position": 35000.0,
    "total_margin": 3500.0,
    "usdc_cross_withdrawable_balance": 5000.0,
    "usdc_isolated_withdrawable_balance": 1000.0,
    "volume": 500000.0,
    "net_deposits": 8000.0,
    "realized_pnl": 2000.0,
    "liquidation_fees_paid": 0.0,
    "liquidation_losses": 0.0,
    "all_time_return": 0.25,
    "pnl_90d": 1500.0,
    "sharpe_ratio": 1.8,
    "max_drawdown": 0.12,
    "weekly_win_rate_12w": 0.67,
    "average_cash_position": 6000.0,
    "average_leverage": 2.5,
}

SAMPLE_OPEN_ORDER = {
    "market": "0xabc123",
    "order_id": "order-001",
    "client_order_id": "client-001",
    "price": 44500.0,
    "orig_size": 0.5,
    "remaining_size": 0.3,
    "is_buy": True,
    "time_in_force": "GoodTillCanceled",
    "is_reduce_only": False,
    "status": "Acknowledged",
    "transaction_unix_ms": 1710000000000,
    "transaction_version": 12345,
}

SAMPLE_TRADE_HISTORY_ITEM = {
    "account": "0xsub1",
    "market": "0xabc123",
    "action": "OpenLong",
    "size": 0.5,
    "price": 44500.0,
    "is_profit": True,
    "realized_pnl_amount": 250.0,
    "is_funding_positive": True,
    "realized_funding_amount": 5.0,
    "is_rebate": False,
    "fee_amount": 7.5,
    "transaction_unix_ms": 1710000000000,
    "transaction_version": 12345,
}

SAMPLE_DEPTH = {
    "market": "BTC-USD",
    "bids": [
        {"price": 44990.0, "size": 2.5},
        {"price": 44980.0, "size": 5.0},
        {"price": 44970.0, "size": 10.0},
    ],
    "asks": [
        {"price": 45010.0, "size": 3.0},
        {"price": 45020.0, "size": 6.0},
        {"price": 45030.0, "size": 8.0},
    ],
    "unix_ms": 1710000000000,
}

SAMPLE_CANDLESTICK = {
    "t": 1710000000000,
    "T": 1710000060000,
    "o": 44900.0,
    "h": 45100.0,
    "l": 44800.0,
    "c": 45050.0,
    "v": 125.5,
    "i": "1m",
}

SAMPLE_FILL_SUMMARY = {
    "bid_filled_size": 0.1,
    "ask_filled_size": 0.05,
    "net_size": 0.05,
    "avg_bid_price": 44950.0,
    "avg_ask_price": 45050.0,
    "fill_count": 3,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def market_config_data() -> dict:
    return SAMPLE_MARKET_CONFIG.copy()


@pytest.fixture
def market_price_data() -> dict:
    return SAMPLE_MARKET_PRICE.copy()


@pytest.fixture
def position_long_data() -> dict:
    return SAMPLE_POSITION_LONG.copy()


@pytest.fixture
def position_short_data() -> dict:
    return SAMPLE_POSITION_SHORT.copy()


@pytest.fixture
def position_flat_data() -> dict:
    return SAMPLE_POSITION_FLAT.copy()


@pytest.fixture
def account_overview_data() -> dict:
    return SAMPLE_ACCOUNT_OVERVIEW.copy()


@pytest.fixture
def open_order_data() -> dict:
    return SAMPLE_OPEN_ORDER.copy()


@pytest.fixture
def depth_data() -> dict:
    import copy
    return copy.deepcopy(SAMPLE_DEPTH)


@pytest.fixture
def candlestick_data() -> dict:
    return SAMPLE_CANDLESTICK.copy()


def now_ms() -> int:
    return int(time.time() * 1000)
