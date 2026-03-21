"""TDD tests for order data models.

These tests define the API contract for UserOpenOrder, OrderStatus,
PlaceOrderResult, and TransactionResult.  All computed properties
(filled_size, fill_pct, side, notional, age_ms) are specified before
implementation so the model behaviour is locked down by tests.
"""

from __future__ import annotations

import time

import pytest

from decibel.models.account import UserOpenOrder
from decibel.models.common import PlaceOrderResult
from decibel.models.order import OrderStatus

from tests.conftest import NOW_MS


# ===================================================================
# UserOpenOrder
# ===================================================================


class TestUserOpenOrder:
    """Contract tests for the active open-order model.

    Open orders are the primary state for order-management bots; every
    helper must handle partial-fill and edge-case states correctly.
    """

    def test_user_open_order_roundtrip(self, btc_open_order: UserOpenOrder) -> None:
        """Serialise → deserialise must preserve every field.

        Order state is compared across snapshots to detect fills;
        a lossy roundtrip would trigger false-positive fill events.
        """
        data = btc_open_order.model_dump()
        restored = UserOpenOrder(**data)
        assert restored == btc_open_order

    def test_user_open_order_json_roundtrip(self, btc_open_order: UserOpenOrder) -> None:
        """JSON wire-format roundtrip."""
        json_str = btc_open_order.model_dump_json()
        restored = UserOpenOrder.model_validate_json(json_str)
        assert restored == btc_open_order

    def test_user_open_order_filled_size(self, btc_open_order: UserOpenOrder) -> None:
        """filled_size = orig_size - remaining_size.

        1.0 - 0.6 = 0.4 filled.
        """
        assert btc_open_order.filled_size == pytest.approx(0.4)

    def test_user_open_order_fill_pct(self, btc_open_order: UserOpenOrder) -> None:
        """fill_pct = filled_size / orig_size.

        0.4 / 1.0 = 40%.
        """
        assert btc_open_order.fill_pct == pytest.approx(0.4)

    def test_user_open_order_fill_pct_zero_orig(self) -> None:
        """fill_pct must not raise when orig_size == 0.

        Edge case: a cancelled-before-fill order may have zero orig_size
        in some API edge cases.
        """
        order = UserOpenOrder(
            market="0x1",
            order_id="oid",
            price=94_500.0,
            orig_size=0.0,
            remaining_size=0.0,
            is_buy=True,
            time_in_force="GoodTillCanceled",
            is_reduce_only=False,
            status="Cancelled",
            transaction_unix_ms=NOW_MS,
            transaction_version=1,
        )
        assert order.fill_pct == pytest.approx(0.0)

    def test_user_open_order_side_buy(self, btc_open_order: UserOpenOrder) -> None:
        """side returns 'buy' when is_buy is True.

        Human-readable helper for logging and display.
        """
        assert btc_open_order.side == "buy"

    def test_user_open_order_side_sell(self) -> None:
        """side returns 'sell' when is_buy is False."""
        order = UserOpenOrder(
            market="0x1",
            order_id="oid",
            price=96_000.0,
            orig_size=0.5,
            remaining_size=0.5,
            is_buy=False,
            time_in_force="GoodTillCanceled",
            is_reduce_only=True,
            status="Acknowledged",
            transaction_unix_ms=NOW_MS,
            transaction_version=1,
        )
        assert order.side == "sell"

    def test_user_open_order_notional(self, btc_open_order: UserOpenOrder) -> None:
        """notional = price * orig_size.

        $94,500 * 1.0 = $94,500.
        """
        assert btc_open_order.notional == pytest.approx(94_500.0)

    def test_user_open_order_age_ms(self, btc_open_order: UserOpenOrder) -> None:
        """age_ms(now_ms) returns milliseconds since order placement.

        The order was placed 300_000 ms before NOW_MS.
        """
        age = btc_open_order.age_ms(NOW_MS)
        assert age == pytest.approx(300_000)

    def test_user_open_order_age_ms_default(self, btc_open_order: UserOpenOrder) -> None:
        """age_ms() with no argument uses current wall-clock time.

        The result should be at least 0 ms (order is in the past).
        """
        age = btc_open_order.age_ms()
        assert age >= 0


# ===================================================================
# OrderStatus
# ===================================================================


class TestOrderStatus:
    """Contract tests for the order status update model."""

    def test_order_status_roundtrip(self, order_status_filled: OrderStatus) -> None:
        """Serialise → deserialise preserves all fields."""
        data = order_status_filled.model_dump()
        restored = OrderStatus(**data)
        assert restored == order_status_filled

    def test_order_status_json_roundtrip(self, order_status_filled: OrderStatus) -> None:
        """JSON roundtrip."""
        json_str = order_status_filled.model_dump_json()
        restored = OrderStatus.model_validate_json(json_str)
        assert restored == order_status_filled

    def test_order_status_fields(self, order_status_filled: OrderStatus) -> None:
        """Verify key fields after construction."""
        assert order_status_filled.status == "Filled"
        assert order_status_filled.remaining_size == pytest.approx(0.0)
        assert order_status_filled.is_buy is True


# ===================================================================
# PlaceOrderResult
# ===================================================================


class TestPlaceOrderResult:
    """Contract tests for the order placement result model."""

    def test_place_order_result_success(self, place_order_success: PlaceOrderResult) -> None:
        """Successful placement carries order_id and tx hash."""
        assert place_order_success.success is True
        assert place_order_success.order_id == "order_002"
        assert place_order_success.transaction_hash == "0xtxhash_success"
        assert place_order_success.error is None

    def test_place_order_result_failure(self, place_order_failure: PlaceOrderResult) -> None:
        """Failed placement carries error message, no order_id."""
        assert place_order_failure.success is False
        assert place_order_failure.error == "Insufficient margin"
        assert place_order_failure.order_id is None

    def test_place_order_result_roundtrip(self, place_order_success: PlaceOrderResult) -> None:
        """Serialise → deserialise roundtrip."""
        data = place_order_success.model_dump()
        restored = PlaceOrderResult(**data)
        assert restored == place_order_success

    def test_place_order_result_json_roundtrip(self, place_order_success: PlaceOrderResult) -> None:
        """JSON roundtrip."""
        json_str = place_order_success.model_dump_json()
        restored = PlaceOrderResult.model_validate_json(json_str)
        assert restored == place_order_success


# ===================================================================
# TransactionResult
# ===================================================================


class TestTransactionResult:
    """Contract tests for the generic on-chain transaction result.

    TransactionResult wraps the outcome of any on-chain write operation
    (order, cancel, deposit, withdrawal, etc.).
    """

    def test_transaction_result_success(self) -> None:
        """Successful transaction carries hash and version."""
        from decibel.models.common import TransactionResult

        result = TransactionResult(
            success=True,
            transaction_hash="0xtxhash_ok",
            transaction_version=2_000_001,
        )
        assert result.success is True
        assert result.transaction_hash == "0xtxhash_ok"
        assert result.transaction_version == 2_000_001
        assert result.error is None

    def test_transaction_result_failure(self) -> None:
        """Failed transaction carries error string."""
        from decibel.models.common import TransactionResult

        result = TransactionResult(
            success=False,
            error="VM error: INSUFFICIENT_BALANCE",
        )
        assert result.success is False
        assert result.error == "VM error: INSUFFICIENT_BALANCE"
        assert result.transaction_hash is None

    def test_transaction_result_roundtrip(self) -> None:
        """Serialise → deserialise roundtrip."""
        from decibel.models.common import TransactionResult

        result = TransactionResult(
            success=True,
            transaction_hash="0xabc",
            transaction_version=1,
        )
        data = result.model_dump()
        restored = TransactionResult(**data)
        assert restored == result
