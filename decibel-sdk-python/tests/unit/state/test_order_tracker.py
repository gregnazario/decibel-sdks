"""TDD tests for OrderLifecycleTracker.

OrderLifecycleTracker maintains the full lifecycle of every order that passes
through the SDK — from submission to terminal state — and fires callbacks on
state transitions.  These tests define the public contract and are expected to
fail until the implementation in ``decibel.state.order_tracker`` exists.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from decibel.state.order_tracker import OrderLifecycleTracker, OrderState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORDER_ID_1 = "exch-001"
ORDER_ID_2 = "exch-002"
CLIENT_ID_1 = "cli-abc"
MARKET = "BTC-USD"
SUBACCOUNT = "0xaaa1"


def _new_order_kwargs(
    order_id: str = ORDER_ID_1,
    client_order_id: str | None = CLIENT_ID_1,
    market: str = MARKET,
    is_buy: bool = True,
    price: float = 60_000.0,
    size: float = 1.0,
) -> dict:
    """Return kwargs suitable for ``tracker.track(...)``."""
    return dict(
        order_id=order_id,
        client_order_id=client_order_id,
        market=market,
        subaccount=SUBACCOUNT,
        is_buy=is_buy,
        price=price,
        size=size,
    )


@pytest.fixture
def tracker() -> OrderLifecycleTracker:
    return OrderLifecycleTracker()


# ===================================================================
# Core lifecycle
# ===================================================================


class TestCoreLifecycle:
    """Track, look up, and transition orders."""

    def test_track_new_order(self, tracker: OrderLifecycleTracker):
        """Tracking an order makes it findable by order_id."""
        tracker.track(**_new_order_kwargs())
        order = tracker.get(ORDER_ID_1)
        assert order is not None
        assert order.order_id == ORDER_ID_1
        assert order.state == OrderState.PENDING

    def test_status_transitions(self, tracker: OrderLifecycleTracker):
        """An order transitions Pending → Acknowledged → PartiallyFilled → Filled."""
        tracker.track(**_new_order_kwargs())

        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)
        assert tracker.get(ORDER_ID_1).state == OrderState.ACKNOWLEDGED

        tracker.transition(ORDER_ID_1, OrderState.PARTIALLY_FILLED)
        assert tracker.get(ORDER_ID_1).state == OrderState.PARTIALLY_FILLED

        tracker.transition(ORDER_ID_1, OrderState.FILLED)
        assert tracker.get(ORDER_ID_1).state == OrderState.FILLED

    def test_history_records_all_transitions(self, tracker: OrderLifecycleTracker):
        """The full history of state changes is preserved per order."""
        tracker.track(**_new_order_kwargs())
        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)
        tracker.transition(ORDER_ID_1, OrderState.FILLED)

        history = tracker.history(ORDER_ID_1)
        states = [entry.state for entry in history]
        assert states == [OrderState.PENDING, OrderState.ACKNOWLEDGED, OrderState.FILLED]


# ===================================================================
# Queries
# ===================================================================


class TestStatusLookup:
    """Tests for looking up the current status of an order."""

    def test_status_returns_none_for_untracked(self, tracker: OrderLifecycleTracker):
        """status() returns None when the order_id has never been tracked.

        A bot that queries an unknown order should get None rather than an
        exception, enabling a simple `if status:` guard pattern.
        """
        assert tracker.get("nonexistent") is None

    def test_cancel_transition(self, tracker: OrderLifecycleTracker):
        """An order transitions Pending → Acknowledged → Cancelled.

        This is the normal path when a bot cancels its own limit order
        before it fills.
        """
        tracker.track(**_new_order_kwargs())
        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)
        tracker.transition(ORDER_ID_1, OrderState.CANCELLED)
        assert tracker.get(ORDER_ID_1).state == OrderState.CANCELLED

        history = tracker.history(ORDER_ID_1)
        states = [entry.state for entry in history]
        assert states == [OrderState.PENDING, OrderState.ACKNOWLEDGED, OrderState.CANCELLED]

    def test_duplicate_status_ignored(self, tracker: OrderLifecycleTracker):
        """A duplicate status transition is ignored — no duplicate callback fires.

        The exchange may send redundant status updates (e.g. two Acknowledged
        messages due to retransmission).  The tracker should deduplicate them
        so downstream callbacks fire exactly once per real transition.
        """
        cb = MagicMock()
        tracker.on_status_change(cb)

        tracker.track(**_new_order_kwargs())
        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)
        cb.reset_mock()

        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)
        cb.assert_not_called()

        history = tracker.history(ORDER_ID_1)
        ack_count = sum(1 for e in history if e.state == OrderState.ACKNOWLEDGED)
        assert ack_count == 1


# ===================================================================
# Queries
# ===================================================================


class TestQueries:
    """Filtered views over tracked orders."""

    def test_pending_orders(self, tracker: OrderLifecycleTracker):
        """pending_orders() lists orders not yet acknowledged."""
        tracker.track(**_new_order_kwargs(order_id="o1"))
        tracker.track(**_new_order_kwargs(order_id="o2"))
        tracker.transition("o2", OrderState.ACKNOWLEDGED)

        pending = tracker.pending_orders()
        assert len(pending) == 1
        assert pending[0].order_id == "o1"

    def test_active_orders(self, tracker: OrderLifecycleTracker):
        """active_orders() lists acknowledged and partially filled orders."""
        tracker.track(**_new_order_kwargs(order_id="o1"))
        tracker.track(**_new_order_kwargs(order_id="o2"))
        tracker.track(**_new_order_kwargs(order_id="o3"))

        tracker.transition("o1", OrderState.ACKNOWLEDGED)
        tracker.transition("o2", OrderState.ACKNOWLEDGED)
        tracker.transition("o2", OrderState.PARTIALLY_FILLED)
        # o3 stays PENDING

        active = tracker.active_orders()
        active_ids = {o.order_id for o in active}
        assert active_ids == {"o1", "o2"}

    def test_completed_orders(self, tracker: OrderLifecycleTracker):
        """completed_orders() lists filled, cancelled, and expired orders."""
        tracker.track(**_new_order_kwargs(order_id="o1"))
        tracker.track(**_new_order_kwargs(order_id="o2"))
        tracker.track(**_new_order_kwargs(order_id="o3"))

        tracker.transition("o1", OrderState.ACKNOWLEDGED)
        tracker.transition("o1", OrderState.FILLED)
        tracker.transition("o2", OrderState.CANCELLED)
        tracker.transition("o3", OrderState.EXPIRED)

        completed = tracker.completed_orders()
        completed_ids = {o.order_id for o in completed}
        assert completed_ids == {"o1", "o2", "o3"}


# ===================================================================
# Callbacks
# ===================================================================


class TestCallbacks:
    """on_status_change callback integration."""

    def test_on_status_change_callback(self, tracker: OrderLifecycleTracker):
        """Callback fires on every state transition with (order_id, old, new)."""
        cb = MagicMock()
        tracker.on_status_change(cb)
        tracker.track(**_new_order_kwargs())
        tracker.transition(ORDER_ID_1, OrderState.ACKNOWLEDGED)

        cb.assert_called_once_with(ORDER_ID_1, OrderState.PENDING, OrderState.ACKNOWLEDGED)


# ===================================================================
# Edge cases
# ===================================================================


class TestEdgeCases:
    """Duplicate tracking and client-id lookups."""

    def test_duplicate_track_warning(self, tracker: OrderLifecycleTracker, caplog):
        """Tracking the same order_id twice logs a warning."""
        tracker.track(**_new_order_kwargs())
        with caplog.at_level(logging.WARNING):
            tracker.track(**_new_order_kwargs())
        assert any("duplicate" in r.message.lower() or ORDER_ID_1 in r.message for r in caplog.records)

    def test_client_order_id_lookup(self, tracker: OrderLifecycleTracker):
        """Can find an order by its client_order_id."""
        tracker.track(**_new_order_kwargs(client_order_id="my-client-1"))
        result = tracker.get_by_client_id("my-client-1")
        assert result is not None
        assert result.order_id == ORDER_ID_1
