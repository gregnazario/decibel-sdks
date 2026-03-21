"""
Shared fixtures for the Decibel SDK test suite.

This conftest provides:
- Sample data factories for all core models
- Model-instance fixtures consumed by TDD tests
- Helpers for asserting JSON Schema compliance

Every fixture uses realistic BTC ~$95k / ETH ~$3.5k market data so that
numeric assertions double as sanity checks for trading bot consumers.
"""

from __future__ import annotations

import copy
import time
from typing import Any

import pytest

from decibel.models.account import (
    AccountOverview,
    UserOpenOrder,
    UserPosition,
    UserSubaccount,
    UserTradeHistoryItem,
)
from decibel.models.common import PlaceOrderResult
from decibel.models.enums import TradeAction
from decibel.models.market import (
    Candlestick,
    MarketContext,
    MarketDepth,
    MarketOrder,
    MarketPrice,
    MarketTrade,
    PerpMarketConfig,
)
from decibel.models.order import OrderStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NOW_MS: int = 1_710_000_000_000
"""Fixed reference timestamp (ms) for deterministic age / duration tests."""

# ---------------------------------------------------------------------------
# Raw dict sample data (retained for backward-compatible dict-based fixtures)
# ---------------------------------------------------------------------------

SAMPLE_MARKET_CONFIG: dict[str, Any] = {
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

SAMPLE_MARKET_PRICE: dict[str, Any] = {
    "market": "BTC-USD",
    "mark_px": 45000.0,
    "mid_px": 44999.5,
    "oracle_px": 45001.0,
    "funding_rate_bps": 0.012,
    "is_funding_positive": True,
    "open_interest": 1500000.0,
    "transaction_unix_ms": 1710000000000,
}

SAMPLE_POSITION_LONG: dict[str, Any] = {
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

SAMPLE_POSITION_SHORT: dict[str, Any] = {
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

SAMPLE_POSITION_FLAT: dict[str, Any] = {
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

SAMPLE_ACCOUNT_OVERVIEW: dict[str, Any] = {
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

SAMPLE_OPEN_ORDER: dict[str, Any] = {
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

SAMPLE_TRADE_HISTORY_ITEM: dict[str, Any] = {
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

SAMPLE_DEPTH: dict[str, Any] = {
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

SAMPLE_CANDLESTICK: dict[str, Any] = {
    "t": 1710000000000,
    "T": 1710000060000,
    "o": 44900.0,
    "h": 45100.0,
    "l": 44800.0,
    "c": 45050.0,
    "v": 125.5,
    "i": "1m",
}

SAMPLE_FILL_SUMMARY: dict[str, Any] = {
    "bid_filled_size": 0.1,
    "ask_filled_size": 0.05,
    "net_size": 0.05,
    "avg_bid_price": 44950.0,
    "avg_ask_price": 45050.0,
    "fill_count": 3,
}


# ---------------------------------------------------------------------------
# Dict-level fixtures (backward-compatible)
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
    return copy.deepcopy(SAMPLE_DEPTH)


@pytest.fixture
def candlestick_data() -> dict:
    return SAMPLE_CANDLESTICK.copy()


def now_ms() -> int:
    return int(time.time() * 1000)


# ---------------------------------------------------------------------------
# Model-instance fixtures — used by the TDD test suites
# ---------------------------------------------------------------------------


@pytest.fixture
def btc_perp_config() -> PerpMarketConfig:
    """BTC-USD perpetual config with sz_decimals=4, px_decimals=1."""
    return PerpMarketConfig(
        market_addr="0xabc123",
        market_name="BTC-USD",
        sz_decimals=4,
        px_decimals=1,
        max_leverage=50.0,
        min_size=0.0001,
        lot_size=0.0001,
        tick_size=0.1,
        max_open_interest=500.0,
        margin_call_fee_pct=0.005,
        taker_in_next_block=True,
    )


@pytest.fixture
def btc_market_price() -> MarketPrice:
    """BTC-USD price snapshot: mark=$95,000, funding=+0.75 bps."""
    return MarketPrice(
        market="BTC-USD",
        mark_px=95_000.0,
        mid_px=95_000.0,
        oracle_px=95_001.0,
        funding_rate_bps=0.75,
        is_funding_positive=True,
        open_interest=1_500_000.0,
        transaction_unix_ms=NOW_MS,
    )


@pytest.fixture
def eth_market_price() -> MarketPrice:
    """ETH-USD price snapshot: mark=$3,500, funding negative."""
    return MarketPrice(
        market="ETH-USD",
        mark_px=3_500.0,
        mid_px=3_500.0,
        oracle_px=3_501.0,
        funding_rate_bps=0.50,
        is_funding_positive=False,
        open_interest=500_000.0,
        transaction_unix_ms=NOW_MS,
    )


@pytest.fixture
def btc_market_context() -> MarketContext:
    """BTC-USD 24h market context."""
    return MarketContext(
        market="BTC-USD",
        volume_24h=1_000_000_000.0,
        open_interest=1_500_000.0,
        previous_day_price=94_500.0,
        price_change_pct_24h=0.53,
    )


@pytest.fixture
def btc_market_depth() -> MarketDepth:
    """BTC-USD order book with 3 levels each side, spread = $2."""
    return MarketDepth(
        market="BTC-USD",
        bids=[
            MarketOrder(price=94_999.0, size=1.5),
            MarketOrder(price=94_990.0, size=3.0),
            MarketOrder(price=94_980.0, size=5.0),
        ],
        asks=[
            MarketOrder(price=95_001.0, size=1.0),
            MarketOrder(price=95_010.0, size=2.5),
            MarketOrder(price=95_020.0, size=4.0),
        ],
        unix_ms=NOW_MS,
    )


@pytest.fixture
def empty_market_depth() -> MarketDepth:
    """Empty order book (no bids or asks)."""
    return MarketDepth(
        market="EMPTY-USD",
        bids=[],
        asks=[],
        unix_ms=NOW_MS,
    )


@pytest.fixture
def btc_market_trade() -> MarketTrade:
    """Single BTC-USD trade: 0.25 BTC bought at $95,000."""
    return MarketTrade(
        market="BTC-USD",
        price=95_000.0,
        size=0.25,
        is_buy=True,
        unix_ms=NOW_MS,
    )


@pytest.fixture
def btc_candlestick() -> Candlestick:
    """Bullish 1m BTC candle: open=$94,950 → close=$95,050."""
    return Candlestick(
        t=1_700_000_000_000,
        T=1_700_000_060_000,
        o=94_950.0,
        h=95_100.0,
        l=94_900.0,
        c=95_050.0,
        v=12.5,
        i="1m",
    )


@pytest.fixture
def account_overview() -> AccountOverview:
    """Healthy account: $50k equity, $12.5k margin, $2.5k maintenance."""
    return AccountOverview(
        perp_equity_balance=50_000.0,
        unrealized_pnl=2_000.0,
        unrealized_funding_cost=-50.0,
        cross_margin_ratio=0.25,
        maintenance_margin=2_500.0,
        cross_account_position=150_000.0,
        total_margin=12_500.0,
        usdc_cross_withdrawable_balance=37_500.0,
        usdc_isolated_withdrawable_balance=0.0,
        cross_account_leverage_ratio=3.0,
        volume=500_000.0,
    )


@pytest.fixture
def zero_equity_account() -> AccountOverview:
    """Edge case: account with zero equity (newly created / wiped out)."""
    return AccountOverview(
        perp_equity_balance=0.0,
        unrealized_pnl=0.0,
        unrealized_funding_cost=0.0,
        cross_margin_ratio=0.0,
        maintenance_margin=0.0,
        cross_account_position=0.0,
        total_margin=0.0,
        usdc_cross_withdrawable_balance=0.0,
        usdc_isolated_withdrawable_balance=0.0,
    )


@pytest.fixture
def btc_long_position() -> UserPosition:
    """BTC long: +0.5 BTC @ $94,000, liq=$85,000, with TP+SL."""
    return UserPosition(
        market="0xabc123",
        user="0xsub1",
        size=0.5,
        user_leverage=10.0,
        entry_price=94_000.0,
        is_isolated=False,
        unrealized_funding=-3.2,
        estimated_liquidation_price=85_000.0,
        has_fixed_sized_tpsls=False,
        tp_order_id="tp-001",
        tp_trigger_price=100_000.0,
        tp_limit_price=99_900.0,
        sl_order_id="sl-001",
        sl_trigger_price=90_000.0,
        sl_limit_price=90_100.0,
    )


@pytest.fixture
def eth_short_position() -> UserPosition:
    """ETH short: -5.0 ETH @ $3,600, liq=$4,200, no TP/SL."""
    return UserPosition(
        market="0xdef456",
        user="0xsub1",
        size=-5.0,
        user_leverage=5.0,
        entry_price=3_600.0,
        is_isolated=False,
        unrealized_funding=1.5,
        estimated_liquidation_price=4_200.0,
        has_fixed_sized_tpsls=False,
    )


@pytest.fixture
def flat_position() -> UserPosition:
    """Flat position (size=0): no exposure."""
    return UserPosition(
        market="0xghi789",
        user="0xsub1",
        size=0.0,
        user_leverage=10.0,
        entry_price=0.0,
        is_isolated=False,
        unrealized_funding=0.0,
        estimated_liquidation_price=0.0,
        has_fixed_sized_tpsls=False,
    )


@pytest.fixture
def user_subaccount() -> UserSubaccount:
    """Primary trading subaccount."""
    return UserSubaccount(
        subaccount_address="0xsub1",
        primary_account_address="0xprimary1",
        is_primary=True,
        custom_label="Main Trading",
        is_active=True,
    )


@pytest.fixture
def btc_open_order() -> UserOpenOrder:
    """Partially-filled BTC buy: 1.0 orig, 0.6 remaining, 300s old."""
    return UserOpenOrder(
        market="0xabc123",
        order_id="order_001",
        client_order_id="client_001",
        price=94_500.0,
        orig_size=1.0,
        remaining_size=0.6,
        is_buy=True,
        time_in_force="GoodTillCanceled",
        is_reduce_only=False,
        status="Acknowledged",
        transaction_unix_ms=NOW_MS - 300_000,
        transaction_version=100_001,
    )


@pytest.fixture
def order_status_filled() -> OrderStatus:
    """Fully-filled order status event."""
    return OrderStatus(
        parent="0xprimary1",
        market="0xabc123",
        order_id="order_001",
        status="Filled",
        orig_size=1.0,
        remaining_size=0.0,
        size_delta=1.0,
        price=94_500.0,
        is_buy=True,
        details="Fully filled",
        transaction_version=100_002,
        unix_ms=NOW_MS,
    )


@pytest.fixture
def place_order_success() -> PlaceOrderResult:
    """Successful order placement result."""
    return PlaceOrderResult(
        success=True,
        order_id="order_002",
        transaction_hash="0xtxhash_success",
    )


@pytest.fixture
def place_order_failure() -> PlaceOrderResult:
    """Failed order placement result."""
    return PlaceOrderResult(
        success=False,
        error="Insufficient margin",
    )


@pytest.fixture
def btc_trade_history_item() -> UserTradeHistoryItem:
    """Closed-long trade: 0.5 BTC @ $95,000, +$500 PnL, $7.50 fee."""
    return UserTradeHistoryItem(
        account="0xsub1",
        market="0xabc123",
        action=TradeAction.CLOSE_LONG,
        size=0.5,
        price=95_000.0,
        is_profit=True,
        realized_pnl_amount=500.0,
        is_funding_positive=True,
        realized_funding_amount=5.0,
        is_rebate=False,
        fee_amount=7.5,
        transaction_unix_ms=NOW_MS,
        transaction_version=100_003,
    )


@pytest.fixture
def user_trade_history_item() -> UserTradeHistoryItem:
    """Closed-long trade for test_trade.py: 0.5 BTC @ $96,000.

    net_pnl = realized_pnl(1000) + funding(5) - fee(24) = 981.0
    notional = 0.5 * 96000 = 48000.0
    """
    return UserTradeHistoryItem(
        account="0xsub1",
        market="0xabc123",
        action=TradeAction.CLOSE_LONG,
        size=0.5,
        price=96_000.0,
        is_profit=True,
        realized_pnl_amount=1_000.0,
        is_funding_positive=True,
        realized_funding_amount=5.0,
        is_rebate=False,
        fee_amount=24.0,
        transaction_unix_ms=NOW_MS,
        transaction_version=1_000_010,
    )


@pytest.fixture
def user_funding_history_item():
    """Funding payment: 0.75 bps, $12.50, positive (longs pay)."""
    from decibel.models.account import UserFundingHistoryItem

    return UserFundingHistoryItem(
        market="0xabc123",
        funding_rate_bps=0.75,
        is_funding_positive=True,
        funding_amount=12.50,
        position_size=0.5,
        transaction_unix_ms=NOW_MS,
        transaction_version=1_000_020,
    )


@pytest.fixture
def user_fund_history_deposit():
    """Deposit of $10,000 USDC."""
    from decibel.models.account import UserFundHistoryItem

    return UserFundHistoryItem(
        amount=10_000.0,
        is_deposit=True,
        transaction_unix_ms=NOW_MS,
        transaction_version=1_000_030,
    )


@pytest.fixture
def user_fund_history_withdrawal():
    """Withdrawal of $2,500 USDC."""
    from decibel.models.account import UserFundHistoryItem

    return UserFundHistoryItem(
        amount=2_500.0,
        is_deposit=False,
        transaction_unix_ms=NOW_MS,
        transaction_version=1_000_031,
    )
