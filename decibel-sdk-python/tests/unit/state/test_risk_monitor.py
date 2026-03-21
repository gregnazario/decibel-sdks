"""TDD tests for RiskMonitor.

RiskMonitor sits on top of PositionStateManager and answers risk-related
questions that a trading bot needs in real-time:

* How close is each position to liquidation?
* Is margin usage at a dangerous level?
* What is the funding cost per hour?
* Which positions lack protective orders (TP/SL)?

These tests define the public API contract; they are expected to fail until
the implementation in ``decibel.state.risk_monitor`` exists.
"""

from __future__ import annotations

import pytest

from decibel.models.account import AccountOverview, UserOpenOrder, UserPosition
from decibel.models.market import MarketDepth, MarketOrder, MarketPrice
from decibel.state.position_manager import PositionStateManager
from decibel.state.risk_monitor import RiskMonitor

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUBACCOUNT = "0xaaa1"
MARKET_BTC = "BTC-USD"
MARKET_ETH = "ETH-USD"


# ---------------------------------------------------------------------------
# Helpers — realistic trading data
# ---------------------------------------------------------------------------


def _make_position(
    market: str = MARKET_BTC,
    size: float = 1.0,
    entry_price: float = 60_000.0,
    liq_price: float = 55_000.0,
    *,
    tp_order_id: str | None = None,
    sl_order_id: str | None = None,
) -> UserPosition:
    return UserPosition(
        market=market,
        user=SUBACCOUNT,
        size=size,
        user_leverage=10.0,
        entry_price=entry_price,
        is_isolated=False,
        unrealized_funding=0.0,
        estimated_liquidation_price=liq_price,
        has_fixed_sized_tpsls=False,
        tp_order_id=tp_order_id,
        sl_order_id=sl_order_id,
    )


def _make_overview(
    equity: float = 100_000.0,
    total_margin: float = 20_000.0,
    maintenance_margin: float = 5_000.0,
) -> AccountOverview:
    return AccountOverview(
        perp_equity_balance=equity,
        unrealized_pnl=500.0,
        unrealized_funding_cost=10.0,
        cross_margin_ratio=total_margin / equity if equity else 0.0,
        maintenance_margin=maintenance_margin,
        cross_account_position=50_000.0,
        total_margin=total_margin,
        usdc_cross_withdrawable_balance=equity - total_margin,
        usdc_isolated_withdrawable_balance=0.0,
    )


def _make_price(
    market: str = MARKET_BTC,
    mark: float = 60_000.0,
    funding_bps: float = 0.5,
    funding_positive: bool = True,
) -> MarketPrice:
    return MarketPrice(
        market=market,
        mark_px=mark,
        mid_px=mark + 0.5,
        oracle_px=mark + 1.0,
        funding_rate_bps=funding_bps,
        is_funding_positive=funding_positive,
        open_interest=500.0,
        transaction_unix_ms=1_710_000_000_000,
    )


def _make_open_order(
    market: str = MARKET_BTC,
    order_id: str = "o1",
    is_buy: bool = True,
    price: float = 59_500.0,
) -> UserOpenOrder:
    return UserOpenOrder(
        market=market,
        order_id=order_id,
        price=price,
        orig_size=1.0,
        remaining_size=0.5,
        is_buy=is_buy,
        time_in_force="GoodTillCanceled",
        is_reduce_only=False,
        status="Acknowledged",
        transaction_unix_ms=1_710_000_000_000,
        transaction_version=42,
    )


@pytest.fixture
def state() -> PositionStateManager:
    """Return a fresh PositionStateManager pre-loaded for risk tests."""
    return PositionStateManager()


@pytest.fixture
def monitor(state: PositionStateManager) -> RiskMonitor:
    """Return a RiskMonitor wired to the shared state manager."""
    return RiskMonitor(state)


# ===================================================================
# Liquidation distance
# ===================================================================


class TestLiquidationDistance:
    """Tests for liquidation proximity calculations."""

    def test_liquidation_distance_long(self, state: PositionStateManager, monitor: RiskMonitor):
        """liquidation_distance() returns a LiquidationEstimate for a known position.

        For a long BTC position with mark=60_000 and liq=55_000, the distance
        is (60_000 - 55_000) / 60_000 ≈ 8.33% and distance_usd = 5_000 * size.
        """
        state.merge_position(_make_position(size=1.0, liq_price=55_000.0))
        state.merge_price(_make_price(mark=60_000.0))

        est = monitor.liquidation_distance(MARKET_BTC, SUBACCOUNT)
        assert est is not None
        assert est.distance_pct == pytest.approx((60_000 - 55_000) / 60_000 * 100, rel=1e-3)
        assert est.distance_usd == pytest.approx(5_000.0 * 1.0, rel=1e-3)

    def test_liquidation_distance_short(self, state: PositionStateManager, monitor: RiskMonitor):
        """For a short position, distance is (liq - mark) / mark.

        Short ETH at mark=3_000 with liq=3_500 → distance = 500/3000 ≈ 16.67%.
        """
        state.merge_position(
            _make_position(
                market=MARKET_ETH, size=-10.0,
                entry_price=3_000.0, liq_price=3_500.0,
            )
        )
        state.merge_price(_make_price(market=MARKET_ETH, mark=3_000.0))

        est = monitor.liquidation_distance(MARKET_ETH, SUBACCOUNT)
        assert est is not None
        assert est.distance_pct == pytest.approx((3_500 - 3_000) / 3_000 * 100, rel=1e-3)

    def test_liquidation_distance_returns_none_for_nonexistent(
        self, state: PositionStateManager, monitor: RiskMonitor
    ):
        """liquidation_distance() returns None when no position exists for the market.

        A bot querying risk for a market it doesn't trade should get None, not
        an exception, so it can use a simple `if est:` guard.
        """
        assert monitor.liquidation_distance("DOGE-USD", SUBACCOUNT) is None

    def test_min_liquidation_distance(self, state: PositionStateManager, monitor: RiskMonitor):
        """min_liquidation_distance() returns the position closest to liquidation.

        With BTC 8.33% away and ETH 16.67% away, min should be BTC.
        """
        state.merge_position(_make_position(market=MARKET_BTC, size=1.0, liq_price=55_000.0))
        state.merge_position(
            _make_position(
                market=MARKET_ETH, size=-10.0,
                entry_price=3_000.0, liq_price=3_500.0,
            )
        )
        state.merge_price(_make_price(market=MARKET_BTC, mark=60_000.0))
        state.merge_price(_make_price(market=MARKET_ETH, mark=3_000.0))

        closest = monitor.min_liquidation_distance(SUBACCOUNT)
        assert closest is not None
        assert closest.market == MARKET_BTC


# ===================================================================
# Margin warnings
# ===================================================================


class TestMarginWarning:
    """Tests for margin usage threshold warnings."""

    def test_margin_warning_ok(self, state: PositionStateManager, monitor: RiskMonitor):
        """margin_warning() returns 'ok' when margin usage is below 80%.

        20% usage = 20_000 / 100_000 — well within safe limits.
        """
        state.merge_overview(_make_overview(equity=100_000.0, total_margin=20_000.0), SUBACCOUNT)
        assert monitor.margin_warning(SUBACCOUNT) == "ok"

    def test_margin_warning_warn_at_80pct(self, state: PositionStateManager, monitor: RiskMonitor):
        """margin_warning() returns 'warn' when margin usage reaches 80%.

        80_000 / 100_000 = 80% — the bot should reduce exposure.
        """
        state.merge_overview(_make_overview(equity=100_000.0, total_margin=80_000.0), SUBACCOUNT)
        assert monitor.margin_warning(SUBACCOUNT) == "warn"

    def test_margin_warning_critical_at_90pct(
        self, state: PositionStateManager, monitor: RiskMonitor
    ):
        """margin_warning() returns 'critical' at 90%+ margin usage.

        90_000 / 100_000 = 90% — the bot should urgently de-risk.
        """
        state.merge_overview(_make_overview(equity=100_000.0, total_margin=90_000.0), SUBACCOUNT)
        assert monitor.margin_warning(SUBACCOUNT) == "critical"

    def test_margin_warning_none_before_overview(
        self, state: PositionStateManager, monitor: RiskMonitor
    ):
        """margin_warning() returns None if no overview has been received yet.

        Before the first REST snapshot, the monitor cannot assess margin
        health — returning None signals "data not available".
        """
        assert monitor.margin_warning(SUBACCOUNT) is None


# ===================================================================
# Funding accrual
# ===================================================================


class TestFundingAccrual:
    """Tests for funding rate cost calculations."""

    def test_funding_accrual_rate_long(self, state: PositionStateManager, monitor: RiskMonitor):
        """funding_accrual_rate() computes the hourly USD cost for a single position.

        For a 1.0 BTC long at mark=60_000 with funding_rate_bps=0.5 (positive),
        hourly cost = size * mark * funding_bps / 10_000.
        Longs pay when funding is positive.
        """
        state.merge_position(_make_position(size=1.0))
        state.merge_price(_make_price(mark=60_000.0, funding_bps=0.5, funding_positive=True))

        rate = monitor.funding_accrual_rate(MARKET_BTC, SUBACCOUNT)
        assert rate is not None
        expected = 1.0 * 60_000.0 * 0.5 / 10_000
        assert rate == pytest.approx(expected, rel=1e-3)

    def test_funding_accrual_rate_none_for_nonexistent(
        self, state: PositionStateManager, monitor: RiskMonitor
    ):
        """funding_accrual_rate() returns None for a market with no position.

        The bot should not assume zero funding — None means "unknown".
        """
        assert monitor.funding_accrual_rate("DOGE-USD", SUBACCOUNT) is None

    def test_total_funding_accrual_rate(self, state: PositionStateManager, monitor: RiskMonitor):
        """total_funding_accrual_rate() sums funding cost across all positions.

        With positions in BTC and ETH, the total is the sum of individual
        per-market funding accruals.
        """
        state.merge_position(_make_position(market=MARKET_BTC, size=2.0))
        state.merge_position(
            _make_position(
                market=MARKET_ETH, size=-10.0,
                entry_price=3_000.0, liq_price=3_500.0,
            )
        )
        state.merge_price(
            _make_price(market=MARKET_BTC, mark=60_000.0, funding_bps=0.5, funding_positive=True)
        )
        state.merge_price(
            _make_price(market=MARKET_ETH, mark=3_000.0, funding_bps=1.0, funding_positive=True)
        )

        total = monitor.total_funding_accrual_rate(SUBACCOUNT)
        assert total is not None
        btc_rate = 2.0 * 60_000.0 * 0.5 / 10_000
        eth_rate = -(-10.0) * 3_000.0 * 1.0 / 10_000
        assert total == pytest.approx(btc_rate + eth_rate, rel=1e-3)


# ===================================================================
# Unprotected positions
# ===================================================================


class TestUnprotectedPositions:
    """Tests for identifying positions without take-profit or stop-loss."""

    def test_positions_without_tp_sl(self, state: PositionStateManager, monitor: RiskMonitor):
        """positions_without_tp_sl() identifies positions missing TP and SL orders.

        A position without both tp_order_id and sl_order_id is "unprotected" —
        the bot has no automatic exit strategy if the market moves against it.
        """
        state.merge_position(_make_position(market=MARKET_BTC, tp_order_id=None, sl_order_id=None))
        state.merge_position(
            _make_position(
                market=MARKET_ETH, entry_price=3_000.0,
                liq_price=2_500.0, tp_order_id="tp-1", sl_order_id="sl-1",
            )
        )

        unprotected = monitor.positions_without_tp_sl(SUBACCOUNT)
        assert len(unprotected) == 1
        assert unprotected[0].market == MARKET_BTC

    def test_unprotected_exposure_usd(self, state: PositionStateManager, monitor: RiskMonitor):
        """unprotected_exposure_usd() sums the notional of unprotected positions.

        If only BTC (size=2, mark=60_000) is unprotected, the exposure is
        |2 * 60_000| = 120_000 USD.
        """
        state.merge_position(
            _make_position(market=MARKET_BTC, size=2.0, tp_order_id=None, sl_order_id=None)
        )
        state.merge_position(
            _make_position(
                market=MARKET_ETH, size=-10.0, entry_price=3_000.0,
                liq_price=3_500.0, tp_order_id="tp-1", sl_order_id="sl-1",
            )
        )
        state.merge_price(_make_price(market=MARKET_BTC, mark=60_000.0))
        state.merge_price(_make_price(market=MARKET_ETH, mark=3_000.0))

        exposure = monitor.unprotected_exposure_usd(SUBACCOUNT)
        assert exposure == pytest.approx(120_000.0, rel=1e-3)


# ===================================================================
# Risk summary
# ===================================================================


class TestRiskSummary:
    """Tests for the comprehensive risk snapshot."""

    def test_risk_summary_returns_dict(self, state: PositionStateManager, monitor: RiskMonitor):
        """risk_summary() returns a dict with all key risk metrics.

        The summary aggregates liquidation distances, margin usage, funding
        costs, and unprotected exposure into a single dict that can be
        logged, displayed, or fed to an LLM agent for decision-making.
        """
        state.merge_position(_make_position(size=1.0, liq_price=55_000.0))
        state.merge_price(_make_price(mark=60_000.0, funding_bps=0.5))
        state.merge_overview(_make_overview(equity=100_000.0, total_margin=20_000.0), SUBACCOUNT)

        summary = monitor.risk_summary(SUBACCOUNT)
        assert isinstance(summary, dict)
        assert "margin_warning" in summary
        assert "gross_exposure_usd" in summary
        assert "net_exposure_usd" in summary
        assert "total_funding_accrual_rate" in summary
        assert "unprotected_exposure_usd" in summary
        assert "min_liquidation_distance_pct" in summary

    def test_risk_summary_with_no_positions(
        self, state: PositionStateManager, monitor: RiskMonitor
    ):
        """risk_summary() works with zero positions — returns safe defaults.

        A bot should be able to call risk_summary() at any time without
        worrying about whether positions exist.
        """
        state.merge_overview(_make_overview(equity=100_000.0, total_margin=0.0), SUBACCOUNT)
        summary = monitor.risk_summary(SUBACCOUNT)
        assert isinstance(summary, dict)
        assert summary["gross_exposure_usd"] == pytest.approx(0.0)
        assert summary["unprotected_exposure_usd"] == pytest.approx(0.0)
