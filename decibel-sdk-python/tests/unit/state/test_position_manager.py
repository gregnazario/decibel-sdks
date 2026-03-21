"""TDD tests for PositionStateManager.

PositionStateManager is the central in-memory cache that aggregates positions,
open orders, account overviews, and market data received from REST snapshots and
WebSocket deltas.  These tests define the public API contract; they are expected
to fail until the implementation in ``decibel.state.position_manager`` exists.
"""

from __future__ import annotations

import threading

import pytest

from decibel.models.account import AccountOverview, UserOpenOrder, UserPosition
from decibel.models.market import MarketDepth, MarketOrder, MarketPrice
from decibel.state.position_manager import PositionStateManager

# ---------------------------------------------------------------------------
# Fixtures – realistic trading data
# ---------------------------------------------------------------------------

SUBACCOUNT = "0xaaa1"
MARKET_BTC = "BTC-USD"
MARKET_ETH = "ETH-USD"


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


def _make_open_order(
    market: str = MARKET_BTC,
    order_id: str = "o1",
    client_order_id: str | None = None,
    is_buy: bool = True,
    price: float = 59_500.0,
    remaining: float = 0.5,
    status: str = "Acknowledged",
) -> UserOpenOrder:
    return UserOpenOrder(
        market=market,
        order_id=order_id,
        client_order_id=client_order_id,
        price=price,
        orig_size=1.0,
        remaining_size=remaining,
        is_buy=is_buy,
        time_in_force="GoodTillCanceled",
        is_reduce_only=False,
        status=status,
        transaction_unix_ms=1_710_000_000_000,
        transaction_version=42,
    )


def _make_price(
    market: str = MARKET_BTC,
    mark: float = 60_000.0,
    mid: float = 60_000.5,
    funding_bps: float = 0.5,
    funding_positive: bool = True,
) -> MarketPrice:
    return MarketPrice(
        market=market,
        mark_px=mark,
        mid_px=mid,
        oracle_px=mark + 1.0,
        funding_rate_bps=funding_bps,
        is_funding_positive=funding_positive,
        open_interest=500.0,
        transaction_unix_ms=1_710_000_000_000,
    )


def _make_depth(market: str = MARKET_BTC) -> MarketDepth:
    return MarketDepth(
        market=market,
        bids=[
            MarketOrder(price=59_999.0, size=2.0),
            MarketOrder(price=59_998.0, size=5.0),
        ],
        asks=[
            MarketOrder(price=60_001.0, size=1.5),
            MarketOrder(price=60_002.0, size=3.0),
        ],
        unix_ms=1_710_000_000_000,
    )


@pytest.fixture
def mgr() -> PositionStateManager:
    """Return a fresh PositionStateManager instance."""
    return PositionStateManager()


# ===================================================================
# Position management
# ===================================================================


class TestPositionManagement:
    """Tests for position CRUD operations."""

    def test_empty_state_returns_empty(self, mgr: PositionStateManager):
        """A freshly created manager has no positions and no overviews."""
        assert mgr.positions(SUBACCOUNT) == {}
        assert mgr.overview(SUBACCOUNT) is None

    def test_merge_position(self, mgr: PositionStateManager):
        """After merging a position, it is retrievable via position()."""
        pos = _make_position()
        mgr.merge_position(pos)
        assert mgr.position(MARKET_BTC, SUBACCOUNT) == pos

    def test_merge_position_replaces_existing(self, mgr: PositionStateManager):
        """A second merge for the same market replaces the first snapshot."""
        pos1 = _make_position(size=1.0)
        pos2 = _make_position(size=2.0)
        mgr.merge_position(pos1)
        mgr.merge_position(pos2)
        assert mgr.position(MARKET_BTC, SUBACCOUNT).size == 2.0

    def test_remove_position_on_zero_size(self, mgr: PositionStateManager):
        """Merging a position with size=0 removes it from state."""
        mgr.merge_position(_make_position(size=1.0))
        mgr.merge_position(_make_position(size=0.0))
        assert mgr.position(MARKET_BTC, SUBACCOUNT) is None
        assert MARKET_BTC not in mgr.positions(SUBACCOUNT)

    def test_positions_returns_dict_keyed_by_market(self, mgr: PositionStateManager):
        """positions() returns a dict whose keys are market names."""
        mgr.merge_position(_make_position(market=MARKET_BTC))
        mgr.merge_position(_make_position(market=MARKET_ETH, entry_price=3_000.0, liq_price=2_500.0))
        positions = mgr.positions(SUBACCOUNT)
        assert set(positions.keys()) == {MARKET_BTC, MARKET_ETH}

    def test_has_position(self, mgr: PositionStateManager):
        """has_position() returns True when a non-zero position exists."""
        assert mgr.has_position(MARKET_BTC, SUBACCOUNT) is False
        mgr.merge_position(_make_position())
        assert mgr.has_position(MARKET_BTC, SUBACCOUNT) is True

    def test_position_returns_none_for_unknown(self, mgr: PositionStateManager):
        """position() returns None for an unknown market or subaccount."""
        assert mgr.position("DOGE-USD", SUBACCOUNT) is None
        assert mgr.position(MARKET_BTC, "0xunknown") is None


# ===================================================================
# Exposure calculations
# ===================================================================


class TestExposureCalculations:
    """Tests for net/gross exposure derived from positions and prices."""

    def test_net_exposure_single_long(self, mgr: PositionStateManager):
        """A single long position yields positive net exposure."""
        mgr.merge_position(_make_position(size=2.0, entry_price=60_000.0))
        mgr.merge_price(_make_price(mark=61_000.0))
        exposure = mgr.net_exposure(SUBACCOUNT)
        assert exposure == pytest.approx(2.0 * 61_000.0)

    def test_net_exposure_single_short(self, mgr: PositionStateManager):
        """A single short position yields negative net exposure."""
        mgr.merge_position(_make_position(size=-1.5, entry_price=60_000.0))
        mgr.merge_price(_make_price(mark=60_000.0))
        exposure = mgr.net_exposure(SUBACCOUNT)
        assert exposure == pytest.approx(-1.5 * 60_000.0)

    def test_net_exposure_mixed(self, mgr: PositionStateManager):
        """Long + short positions partially cancel in net exposure."""
        mgr.merge_position(_make_position(market=MARKET_BTC, size=2.0))
        mgr.merge_position(
            _make_position(market=MARKET_ETH, size=-10.0, entry_price=3_000.0, liq_price=3_500.0)
        )
        mgr.merge_price(_make_price(market=MARKET_BTC, mark=60_000.0))
        mgr.merge_price(_make_price(market=MARKET_ETH, mark=3_000.0))
        expected = 2.0 * 60_000.0 + (-10.0) * 3_000.0  # 120k - 30k = 90k
        assert mgr.net_exposure(SUBACCOUNT) == pytest.approx(expected)

    def test_gross_exposure(self, mgr: PositionStateManager):
        """Gross exposure is the sum of absolute notional values."""
        mgr.merge_position(_make_position(market=MARKET_BTC, size=2.0))
        mgr.merge_position(
            _make_position(market=MARKET_ETH, size=-10.0, entry_price=3_000.0, liq_price=3_500.0)
        )
        mgr.merge_price(_make_price(market=MARKET_BTC, mark=60_000.0))
        mgr.merge_price(_make_price(market=MARKET_ETH, mark=3_000.0))
        expected = abs(2.0 * 60_000.0) + abs(-10.0 * 3_000.0)  # 120k + 30k
        assert mgr.gross_exposure(SUBACCOUNT) == pytest.approx(expected)

    def test_exposure_empty(self, mgr: PositionStateManager):
        """Exposure is zero when no positions exist."""
        assert mgr.net_exposure(SUBACCOUNT) == pytest.approx(0.0)
        assert mgr.gross_exposure(SUBACCOUNT) == pytest.approx(0.0)


# ===================================================================
# Order tracking
# ===================================================================


class TestOrderTracking:
    """Tests for open-order management inside the position manager."""

    def test_merge_open_orders(self, mgr: PositionStateManager):
        """Merged orders are available via open_orders()."""
        orders = [_make_open_order(order_id="o1"), _make_open_order(order_id="o2")]
        mgr.merge_open_orders(orders, SUBACCOUNT)
        assert len(mgr.open_orders(SUBACCOUNT)) == 2

    def test_open_orders_by_market(self, mgr: PositionStateManager):
        """open_orders_by_market() filters orders to a single market."""
        mgr.merge_open_orders(
            [
                _make_open_order(market=MARKET_BTC, order_id="o1"),
                _make_open_order(market=MARKET_ETH, order_id="o2"),
            ],
            SUBACCOUNT,
        )
        btc_orders = mgr.open_orders_by_market(MARKET_BTC, SUBACCOUNT)
        assert len(btc_orders) == 1
        assert btc_orders[0].market == MARKET_BTC

    def test_order_by_id(self, mgr: PositionStateManager):
        """order_by_id() looks up an order by its exchange-assigned order_id."""
        order = _make_open_order(order_id="o42")
        mgr.merge_open_orders([order], SUBACCOUNT)
        assert mgr.order_by_id("o42", SUBACCOUNT) == order
        assert mgr.order_by_id("nonexistent", SUBACCOUNT) is None

    def test_order_by_client_id(self, mgr: PositionStateManager):
        """order_by_client_id() looks up an order by its client_order_id."""
        order = _make_open_order(order_id="o1", client_order_id="my-cid-1")
        mgr.merge_open_orders([order], SUBACCOUNT)
        assert mgr.order_by_client_id("my-cid-1", SUBACCOUNT) == order
        assert mgr.order_by_client_id("missing", SUBACCOUNT) is None

    def test_order_removal_on_cancel(self, mgr: PositionStateManager):
        """Cancelled orders are removed from the open set on merge.

        After merging a cancellation for o1, the open orders list should
        only contain o2. A cancelled order is not an open order.
        """
        mgr.merge_open_orders(
            [_make_open_order(order_id="o1"), _make_open_order(order_id="o2")],
            SUBACCOUNT,
        )
        mgr.merge_open_orders(
            [_make_open_order(order_id="o1", status="Cancelled")],
            SUBACCOUNT,
        )
        remaining = mgr.open_orders(SUBACCOUNT)
        remaining_ids = [o.order_id for o in remaining]
        assert "o1" not in remaining_ids, "Cancelled order o1 should be removed from open orders"
        assert "o2" in remaining_ids, "Non-cancelled order o2 should remain in open orders"
        assert len(remaining) == 1, f"Expected 1 open order after cancel, got {len(remaining)}"


# ===================================================================
# Account overview
# ===================================================================


class TestAccountOverview:
    """Tests for account overview / equity / margin helpers."""

    def test_merge_overview(self, mgr: PositionStateManager):
        """Overview is accessible after merge."""
        ov = _make_overview(equity=100_000.0)
        mgr.merge_overview(ov, SUBACCOUNT)
        assert mgr.overview(SUBACCOUNT) is not None
        assert mgr.overview(SUBACCOUNT).perp_equity_balance == 100_000.0

    def test_equity_from_overview(self, mgr: PositionStateManager):
        """equity() returns perp_equity_balance from the merged overview."""
        mgr.merge_overview(_make_overview(equity=42_000.0), SUBACCOUNT)
        assert mgr.equity(SUBACCOUNT) == pytest.approx(42_000.0)

    def test_margin_usage_pct(self, mgr: PositionStateManager):
        """margin_usage_pct is total_margin / perp_equity_balance as 0.0-1.0 fraction."""
        mgr.merge_overview(
            _make_overview(equity=100_000.0, total_margin=20_000.0),
            SUBACCOUNT,
        )
        assert mgr.margin_usage_pct(SUBACCOUNT) == pytest.approx(0.20)

    def test_available_margin(self, mgr: PositionStateManager):
        """available_margin is equity minus total_margin."""
        mgr.merge_overview(
            _make_overview(equity=100_000.0, total_margin=20_000.0),
            SUBACCOUNT,
        )
        assert mgr.available_margin(SUBACCOUNT) == pytest.approx(80_000.0)


# ===================================================================
# Market data
# ===================================================================


class TestMarketData:
    """Tests for price and depth caching."""

    def test_merge_price(self, mgr: PositionStateManager):
        """Price is accessible via price() and mark_price() after merge."""
        px = _make_price(mark=61_234.5)
        mgr.merge_price(px)
        assert mgr.price(MARKET_BTC) == px
        assert mgr.mark_price(MARKET_BTC) == pytest.approx(61_234.5)

    def test_mid_price(self, mgr: PositionStateManager):
        """mid_price() returns mid_px from the cached MarketPrice."""
        mgr.merge_price(_make_price(mid=60_100.25))
        assert mgr.mid_price(MARKET_BTC) == pytest.approx(60_100.25)

    def test_merge_depth(self, mgr: PositionStateManager):
        """Depth is accessible via depth() after merge."""
        d = _make_depth()
        mgr.merge_depth(d)
        result = mgr.depth(MARKET_BTC)
        assert result is not None
        assert len(result.bids) == 2
        assert len(result.asks) == 2


# ===================================================================
# State metadata
# ===================================================================


class TestStateMetadata:
    """Tests for last_update_ms and gap_detected flags."""

    def test_last_update_ms(self, mgr: PositionStateManager):
        """last_update_ms advances after every merge operation."""
        t0 = mgr.last_update_ms
        mgr.merge_position(_make_position())
        t1 = mgr.last_update_ms
        assert t1 >= t0

    def test_gap_detected_default(self, mgr: PositionStateManager):
        """gap_detected is False on a fresh manager."""
        assert mgr.gap_detected is False

    def test_gap_detected_set_on_disconnect(self, mgr: PositionStateManager):
        """gap_detected becomes True after a simulated disconnect signal."""
        mgr.notify_disconnect()
        assert mgr.gap_detected is True

    def test_gap_detected_cleared_after_resync(self, mgr: PositionStateManager):
        """gap_detected resets to False after a full REST re-sync."""
        mgr.notify_disconnect()
        assert mgr.gap_detected is True
        mgr.notify_resync_complete()
        assert mgr.gap_detected is False


# ===================================================================
# Thread safety
# ===================================================================


class TestMultipleSubaccounts:
    """Tests for independent tracking across multiple subaccounts."""

    SUBACCOUNT_A = "0xaaa1"
    SUBACCOUNT_B = "0xbbb2"

    def test_positions_tracked_independently(self, mgr: PositionStateManager):
        """Positions for different subaccounts do not interfere with each other.

        A market-making bot often manages multiple sub-accounts — one per
        strategy.  Merging a BTC position for sub-A must not affect sub-B.
        """
        pos_a = UserPosition(
            market=MARKET_BTC,
            user=self.SUBACCOUNT_A,
            size=5.0,
            user_leverage=10.0,
            entry_price=60_000.0,
            is_isolated=False,
            unrealized_funding=0.0,
            estimated_liquidation_price=55_000.0,
            has_fixed_sized_tpsls=False,
        )
        pos_b = UserPosition(
            market=MARKET_BTC,
            user=self.SUBACCOUNT_B,
            size=-3.0,
            user_leverage=5.0,
            entry_price=61_000.0,
            is_isolated=False,
            unrealized_funding=0.0,
            estimated_liquidation_price=65_000.0,
            has_fixed_sized_tpsls=False,
        )
        mgr.merge_position(pos_a)
        mgr.merge_position(pos_b)

        assert mgr.position(MARKET_BTC, self.SUBACCOUNT_A).size == 5.0
        assert mgr.position(MARKET_BTC, self.SUBACCOUNT_B).size == -3.0

    def test_overviews_tracked_independently(self, mgr: PositionStateManager):
        """Each subaccount has its own AccountOverview snapshot.

        equity() for sub-A must reflect sub-A's overview, not sub-B's.
        """
        ov_a = _make_overview(equity=100_000.0)
        ov_b = _make_overview(equity=50_000.0)
        mgr.merge_overview(ov_a, self.SUBACCOUNT_A)
        mgr.merge_overview(ov_b, self.SUBACCOUNT_B)

        assert mgr.equity(self.SUBACCOUNT_A) == pytest.approx(100_000.0)
        assert mgr.equity(self.SUBACCOUNT_B) == pytest.approx(50_000.0)

    def test_open_orders_tracked_independently(self, mgr: PositionStateManager):
        """Open orders for one subaccount are invisible to the other.

        Querying orders for sub-A should not return orders belonging to sub-B.
        """
        order_a = _make_open_order(order_id="oa1")
        order_b = _make_open_order(order_id="ob1")
        mgr.merge_open_orders([order_a], self.SUBACCOUNT_A)
        mgr.merge_open_orders([order_b], self.SUBACCOUNT_B)

        assert len(mgr.open_orders(self.SUBACCOUNT_A)) == 1
        assert mgr.open_orders(self.SUBACCOUNT_A)[0].order_id == "oa1"
        assert len(mgr.open_orders(self.SUBACCOUNT_B)) == 1
        assert mgr.open_orders(self.SUBACCOUNT_B)[0].order_id == "ob1"


class TestConnectionState:
    """Tests for is_connected flag tracking."""

    def test_is_connected_default(self, mgr: PositionStateManager):
        """A fresh manager reports is_connected as False (not yet connected).

        Until the first successful WebSocket message is received, the SDK
        should not claim connectivity.
        """
        assert mgr.is_connected is False

    def test_is_connected_after_data(self, mgr: PositionStateManager):
        """is_connected becomes True once any data merge occurs.

        Receiving data (positions, prices, etc.) implies an active connection.
        """
        mgr.merge_price(_make_price())
        assert mgr.is_connected is True

    def test_is_connected_false_after_disconnect(self, mgr: PositionStateManager):
        """is_connected becomes False after notify_disconnect().

        When the WebSocket drops, the manager should reflect that so the
        bot can pause trading or switch to REST polling.
        """
        mgr.merge_price(_make_price())
        assert mgr.is_connected is True
        mgr.notify_disconnect()
        assert mgr.is_connected is False

    def test_is_connected_restored_after_resync(self, mgr: PositionStateManager):
        """is_connected is restored to True after a full re-sync.

        After a REST re-sync completes, the manager should report connected
        so the bot can resume normal operations.
        """
        mgr.merge_price(_make_price())
        mgr.notify_disconnect()
        assert mgr.is_connected is False
        mgr.notify_resync_complete()
        assert mgr.is_connected is True


# ===================================================================
# Thread safety
# ===================================================================


class TestThreadSafety:
    """Basic concurrency smoke test."""

    def test_concurrent_reads_during_write(self, mgr: PositionStateManager):
        """Multiple readers do not block or crash while a writer mutates state."""
        mgr.merge_position(_make_position())
        mgr.merge_price(_make_price())

        errors: list[Exception] = []

        def reader():
            try:
                for _ in range(200):
                    mgr.positions(SUBACCOUNT)
                    mgr.net_exposure(SUBACCOUNT)
                    mgr.mark_price(MARKET_BTC)
            except Exception as exc:
                errors.append(exc)

        def writer():
            try:
                for i in range(200):
                    mgr.merge_position(_make_position(size=float(i)))
                    mgr.merge_price(_make_price(mark=60_000.0 + i))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        threads.append(threading.Thread(target=writer))
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == [], f"Concurrent access raised: {errors}"
