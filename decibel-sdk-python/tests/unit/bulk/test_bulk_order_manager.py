"""TDD tests for BulkOrderManager.

BulkOrderManager handles high-frequency quoting where a market-maker
maintains two-sided quotes (bids and asks) and replaces them atomically
each tick.  It tracks a monotonically increasing sequence_number so the
exchange can discard stale updates, and it accumulates fill statistics
between resets.

These tests define the public API contract; they are expected to fail
until the implementation in ``decibel.bulk.order_manager`` exists.
"""

from __future__ import annotations

import pytest

from decibel.bulk.order_manager import BulkOrderManager, BulkQuoteResult, FillSummary

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MARKET = "BTC-USD"
SUBACCOUNT = "0xaaa1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bid(price: float, size: float) -> dict:
    """Return a bid-level dict in the format expected by set_quotes()."""
    return {"price": price, "size": size}


def _ask(price: float, size: float) -> dict:
    """Return an ask-level dict in the format expected by set_quotes()."""
    return {"price": price, "size": size}


@pytest.fixture
def mgr() -> BulkOrderManager:
    """Return a fresh BulkOrderManager for BTC-USD."""
    return BulkOrderManager(market=MARKET, subaccount=SUBACCOUNT)


# ===================================================================
# Constructor and sequence number
# ===================================================================


class TestConstructor:
    """Tests for initial state after construction."""

    def test_initial_state(self, mgr: BulkOrderManager):
        """A new manager has sequence_number=0, no live quotes, and empty fills.

        Before the first set_quotes() call, the manager is idle and has
        not submitted any orders to the exchange.
        """
        assert mgr.market == MARKET
        assert mgr.sequence_number == 0
        assert mgr.live_bids == []
        assert mgr.live_asks == []
        assert mgr.is_quoting() is False

    def test_sequence_number_increments(self, mgr: BulkOrderManager):
        """Each set_quotes() call increments sequence_number by 1.

        The exchange uses this to detect stale updates — if it receives
        seq=5 after seq=7, it discards the stale one.
        """
        mgr.set_quotes(bids=[_bid(59_900, 1.0)], asks=[_ask(60_100, 1.0)])
        assert mgr.sequence_number == 1

        mgr.set_quotes(bids=[_bid(59_800, 2.0)], asks=[_ask(60_200, 2.0)])
        assert mgr.sequence_number == 2

    def test_sequence_number_monotonically_increasing(self, mgr: BulkOrderManager):
        """sequence_number never decreases, even after cancel_all().

        A cancelled state still advances the sequence to avoid replays.
        """
        mgr.set_quotes(bids=[_bid(59_900, 1.0)], asks=[_ask(60_100, 1.0)])
        seq_after_quote = mgr.sequence_number

        mgr.cancel_all()
        assert mgr.sequence_number > seq_after_quote


# ===================================================================
# Setting quotes
# ===================================================================


class TestSetQuotes:
    """Tests for the core set_quotes() operation."""

    def test_set_quotes_returns_result(self, mgr: BulkOrderManager):
        """set_quotes() returns a BulkQuoteResult confirming submission.

        The result includes the sequence_number used and the number of
        levels on each side, so the caller can verify the update.
        """
        result = mgr.set_quotes(
            bids=[_bid(59_900, 1.0), _bid(59_800, 2.0)],
            asks=[_ask(60_100, 1.0), _ask(60_200, 3.0)],
        )
        assert isinstance(result, BulkQuoteResult)
        assert result.sequence_number == 1
        assert result.bid_count == 2
        assert result.ask_count == 2

    def test_set_quotes_updates_live_levels(self, mgr: BulkOrderManager):
        """After set_quotes(), live_bids and live_asks reflect the latest levels.

        The previous quote set is fully replaced — there is no partial
        amendment.
        """
        mgr.set_quotes(
            bids=[_bid(59_900, 1.0), _bid(59_800, 2.0)],
            asks=[_ask(60_100, 1.5)],
        )
        assert len(mgr.live_bids) == 2
        assert len(mgr.live_asks) == 1

    def test_live_bids_sorted_descending(self, mgr: BulkOrderManager):
        """live_bids are sorted by price descending (best bid first).

        Market-makers need the best bid at index 0 for spread calculations.
        """
        mgr.set_quotes(
            bids=[_bid(59_700, 1.0), _bid(59_900, 1.0), _bid(59_800, 1.0)],
            asks=[_ask(60_100, 1.0)],
        )
        prices = [b["price"] for b in mgr.live_bids]
        assert prices == sorted(prices, reverse=True)

    def test_live_asks_sorted_ascending(self, mgr: BulkOrderManager):
        """live_asks are sorted by price ascending (best ask first).

        Market-makers need the best ask at index 0 for spread calculations.
        """
        mgr.set_quotes(
            bids=[_bid(59_900, 1.0)],
            asks=[_ask(60_300, 1.0), _ask(60_100, 1.0), _ask(60_200, 1.0)],
        )
        prices = [a["price"] for a in mgr.live_asks]
        assert prices == sorted(prices)


# ===================================================================
# Cancel all
# ===================================================================


class TestCancelAll:
    """Tests for cancel_all() — pulling all quotes."""

    def test_cancel_all_clears_levels(self, mgr: BulkOrderManager):
        """cancel_all() removes all live quotes and sets is_quoting() to False.

        After a cancel, the manager has zero market exposure.
        """
        mgr.set_quotes(
            bids=[_bid(59_900, 1.0)],
            asks=[_ask(60_100, 1.0)],
        )
        assert mgr.is_quoting() is True

        mgr.cancel_all()
        assert mgr.live_bids == []
        assert mgr.live_asks == []
        assert mgr.is_quoting() is False


# ===================================================================
# Quoting state
# ===================================================================


class TestIsQuoting:
    """Tests for the is_quoting() readiness check."""

    def test_is_quoting_true_when_both_sides(self, mgr: BulkOrderManager):
        """is_quoting() returns True when both bids and asks are present.

        Two-sided quoting is the normal operating mode for a market-maker.
        """
        mgr.set_quotes(
            bids=[_bid(59_900, 1.0)],
            asks=[_ask(60_100, 1.0)],
        )
        assert mgr.is_quoting() is True

    def test_is_quoting_false_one_side_only(self, mgr: BulkOrderManager):
        """is_quoting() returns False when only one side has orders.

        One-sided quoting is not considered "quoting" — the market-maker
        should be aware it has directional exposure.
        """
        mgr.set_quotes(bids=[_bid(59_900, 1.0)], asks=[])
        assert mgr.is_quoting() is False

        mgr.set_quotes(bids=[], asks=[_ask(60_100, 1.0)])
        assert mgr.is_quoting() is False


# ===================================================================
# Fill tracking
# ===================================================================


class TestFillTracking:
    """Tests for fill accumulation between resets."""

    def test_initial_fill_summary_is_zero(self, mgr: BulkOrderManager):
        """filled_since_last_reset() returns a FillSummary with all zeros initially.

        Before any fills occur, the tracker reports zero activity.
        """
        summary = mgr.filled_since_last_reset()
        assert isinstance(summary, FillSummary)
        assert summary.bid_filled_size == 0.0
        assert summary.ask_filled_size == 0.0
        assert summary.net_size == 0.0
        assert summary.fill_count == 0

    def test_apply_fill_updates_tracker(self, mgr: BulkOrderManager):
        """Applying a fill event increments the fill tracker.

        The market-maker needs to know how much inventory it has accumulated
        since the last reset so it can adjust its quoting skew.
        """
        mgr.apply_fill(is_buy=True, size=0.5, price=59_950.0)
        mgr.apply_fill(is_buy=False, size=0.3, price=60_050.0)

        summary = mgr.filled_since_last_reset()
        assert summary.bid_filled_size == pytest.approx(0.5)
        assert summary.ask_filled_size == pytest.approx(0.3)
        assert summary.net_size == pytest.approx(0.5 - 0.3)
        assert summary.fill_count == 2

    def test_reset_fill_tracker(self, mgr: BulkOrderManager):
        """reset_fill_tracker() returns the current summary and resets to zero.

        The market-maker calls this at the start of each quoting cycle to
        measure inventory drift and adjust.
        """
        mgr.apply_fill(is_buy=True, size=1.0, price=59_950.0)
        old = mgr.reset_fill_tracker()
        assert old.bid_filled_size == pytest.approx(1.0)
        assert old.fill_count == 1

        current = mgr.filled_since_last_reset()
        assert current.bid_filled_size == 0.0
        assert current.fill_count == 0


# ===================================================================
# Validation
# ===================================================================


class TestValidation:
    """Tests for input validation on quote levels."""

    def test_max_30_levels_per_side(self, mgr: BulkOrderManager):
        """set_quotes() raises ValueError if more than 30 levels per side.

        Exchange protocols typically limit the number of levels in a single
        bulk update.  Exceeding this should fail fast, not silently truncate.
        """
        too_many_bids = [_bid(59_900 - i, 1.0) for i in range(31)]
        with pytest.raises(ValueError, match="30"):
            mgr.set_quotes(bids=too_many_bids, asks=[_ask(60_100, 1.0)])

        too_many_asks = [_ask(60_100 + i, 1.0) for i in range(31)]
        with pytest.raises(ValueError, match="30"):
            mgr.set_quotes(bids=[_bid(59_900, 1.0)], asks=too_many_asks)
