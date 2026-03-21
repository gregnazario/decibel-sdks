"""TDD tests for all SDK enumerations.

Enums are the shared vocabulary between the SDK and the exchange API.
Changing a wire value silently would cause order rejections or data
mis-parsing, so every variant is pinned to its expected wire value here.
"""

from __future__ import annotations

import pytest

from decibel.models.enums import (
    CandlestickInterval,
    OrderStatusType,
    SortDirection,
    TimeInForce,
    TradeAction,
    TwapStatus,
    VolumeWindow,
)


# ===================================================================
# TimeInForce
# ===================================================================


class TestTimeInForce:
    """Contract tests for the TimeInForce IntEnum.

    The exchange expects integer values 0/1/2 on the wire.
    """

    def test_time_in_force_gtc_value(self) -> None:
        """GTC maps to 0 on the wire."""
        assert TimeInForce.GOOD_TILL_CANCELED == 0
        assert TimeInForce.GOOD_TILL_CANCELED.value == 0

    def test_time_in_force_post_only_value(self) -> None:
        """POST_ONLY maps to 1 on the wire."""
        assert TimeInForce.POST_ONLY == 1
        assert TimeInForce.POST_ONLY.value == 1

    def test_time_in_force_ioc_value(self) -> None:
        """IOC maps to 2 on the wire."""
        assert TimeInForce.IMMEDIATE_OR_CANCEL == 2
        assert TimeInForce.IMMEDIATE_OR_CANCEL.value == 2

    def test_time_in_force_names(self) -> None:
        """All three names are accessible."""
        names = [e.name for e in TimeInForce]
        assert "GOOD_TILL_CANCELED" in names
        assert "POST_ONLY" in names
        assert "IMMEDIATE_OR_CANCEL" in names

    def test_time_in_force_member_count(self) -> None:
        """Exactly 3 TIF variants exist."""
        assert len(TimeInForce) == 3

    def test_time_in_force_from_int(self) -> None:
        """Can construct from raw integer (deserialization path)."""
        assert TimeInForce(0) is TimeInForce.GOOD_TILL_CANCELED
        assert TimeInForce(1) is TimeInForce.POST_ONLY
        assert TimeInForce(2) is TimeInForce.IMMEDIATE_OR_CANCEL


# ===================================================================
# OrderStatusType
# ===================================================================


class TestOrderStatusType:
    """Contract tests for the OrderStatusType StrEnum."""

    def test_order_status_acknowledged(self) -> None:
        """Acknowledged maps to wire value 'Acknowledged'."""
        assert OrderStatusType.ACKNOWLEDGED.value == "Acknowledged"

    def test_order_status_filled(self) -> None:
        """Filled maps to wire value 'Filled'."""
        assert OrderStatusType.FILLED.value == "Filled"

    def test_order_status_cancelled(self) -> None:
        """Cancelled maps to wire value 'Cancelled'."""
        assert OrderStatusType.CANCELLED.value == "Cancelled"

    def test_order_status_rejected(self) -> None:
        """Rejected maps to wire value 'Rejected'."""
        assert OrderStatusType.REJECTED.value == "Rejected"

    def test_order_status_unknown(self) -> None:
        """Unknown maps to wire value 'Unknown'."""
        assert OrderStatusType.UNKNOWN.value == "Unknown"

    def test_order_status_all_variants(self) -> None:
        """All 5 variants exist."""
        assert len(OrderStatusType) == 5

    def test_order_status_parse_case_insensitive(self) -> None:
        """parse() handles various casings and US/UK spelling."""
        assert OrderStatusType.parse("acknowledged") == OrderStatusType.ACKNOWLEDGED
        assert OrderStatusType.parse("FILLED") == OrderStatusType.FILLED
        assert OrderStatusType.parse("Cancelled") == OrderStatusType.CANCELLED
        assert OrderStatusType.parse("Canceled") == OrderStatusType.CANCELLED
        assert OrderStatusType.parse("rejected") == OrderStatusType.REJECTED
        assert OrderStatusType.parse("garbage") == OrderStatusType.UNKNOWN

    def test_order_status_is_success(self) -> None:
        """is_success() returns True for ACKNOWLEDGED and FILLED."""
        assert OrderStatusType.ACKNOWLEDGED.is_success() is True
        assert OrderStatusType.FILLED.is_success() is True
        assert OrderStatusType.CANCELLED.is_success() is False
        assert OrderStatusType.REJECTED.is_success() is False
        assert OrderStatusType.UNKNOWN.is_success() is False

    def test_order_status_is_failure(self) -> None:
        """is_failure() returns True for CANCELLED and REJECTED."""
        assert OrderStatusType.CANCELLED.is_failure() is True
        assert OrderStatusType.REJECTED.is_failure() is True
        assert OrderStatusType.ACKNOWLEDGED.is_failure() is False
        assert OrderStatusType.FILLED.is_failure() is False

    def test_order_status_is_final(self) -> None:
        """is_final() returns True for terminal states."""
        assert OrderStatusType.ACKNOWLEDGED.is_final() is True
        assert OrderStatusType.FILLED.is_final() is True
        assert OrderStatusType.CANCELLED.is_final() is True
        assert OrderStatusType.REJECTED.is_final() is True
        assert OrderStatusType.UNKNOWN.is_final() is False


# ===================================================================
# TradeAction
# ===================================================================


class TestTradeAction:
    """Contract tests for the TradeAction StrEnum."""

    def test_trade_action_open_long(self) -> None:
        """OpenLong wire value."""
        assert TradeAction.OPEN_LONG.value == "OpenLong"

    def test_trade_action_close_long(self) -> None:
        """CloseLong wire value."""
        assert TradeAction.CLOSE_LONG.value == "CloseLong"

    def test_trade_action_open_short(self) -> None:
        """OpenShort wire value."""
        assert TradeAction.OPEN_SHORT.value == "OpenShort"

    def test_trade_action_close_short(self) -> None:
        """CloseShort wire value."""
        assert TradeAction.CLOSE_SHORT.value == "CloseShort"

    def test_trade_action_net(self) -> None:
        """Net wire value (netting / mixed action)."""
        assert TradeAction.NET.value == "Net"

    def test_trade_action_all_variants(self) -> None:
        """All 5 TradeAction variants exist."""
        assert len(TradeAction) == 5


# ===================================================================
# CandlestickInterval
# ===================================================================


class TestCandlestickInterval:
    """Contract tests for candlestick interval wire values.

    The WebSocket subscription and REST query use these string values
    to specify the desired interval.
    """

    @pytest.mark.parametrize(
        "member,wire",
        [
            (CandlestickInterval.ONE_MINUTE, "1m"),
            (CandlestickInterval.FIVE_MINUTES, "5m"),
            (CandlestickInterval.FIFTEEN_MINUTES, "15m"),
            (CandlestickInterval.THIRTY_MINUTES, "30m"),
            (CandlestickInterval.ONE_HOUR, "1h"),
            (CandlestickInterval.TWO_HOURS, "2h"),
            (CandlestickInterval.FOUR_HOURS, "4h"),
            (CandlestickInterval.EIGHT_HOURS, "8h"),
            (CandlestickInterval.TWELVE_HOURS, "12h"),
            (CandlestickInterval.ONE_DAY, "1d"),
            (CandlestickInterval.THREE_DAYS, "3d"),
            (CandlestickInterval.ONE_WEEK, "1w"),
            (CandlestickInterval.ONE_MONTH, "1mo"),
        ],
    )
    def test_candlestick_interval_wire_values(
        self, member: CandlestickInterval, wire: str
    ) -> None:
        """Each interval member maps to its expected wire string."""
        assert member.value == wire

    def test_candlestick_interval_count(self) -> None:
        """All 13 intervals are defined."""
        assert len(CandlestickInterval) == 13

    def test_candlestick_interval_from_string(self) -> None:
        """Can construct from raw wire string."""
        assert CandlestickInterval("1m") is CandlestickInterval.ONE_MINUTE
        assert CandlestickInterval("4h") is CandlestickInterval.FOUR_HOURS


# ===================================================================
# VolumeWindow
# ===================================================================


class TestVolumeWindow:
    """Contract tests for volume window wire values."""

    @pytest.mark.parametrize(
        "member,wire",
        [
            (VolumeWindow.SEVEN_DAYS, "7d"),
            (VolumeWindow.FOURTEEN_DAYS, "14d"),
            (VolumeWindow.THIRTY_DAYS, "30d"),
            (VolumeWindow.NINETY_DAYS, "90d"),
        ],
    )
    def test_volume_window_wire_values(self, member: VolumeWindow, wire: str) -> None:
        """Each window maps to its expected wire string."""
        assert member.value == wire

    def test_volume_window_count(self) -> None:
        """All 4 windows are defined."""
        assert len(VolumeWindow) == 4


# ===================================================================
# SortDirection
# ===================================================================


class TestSortDirection:
    """Contract tests for sort direction wire values."""

    def test_sort_direction_ascending(self) -> None:
        """ASC wire value."""
        assert SortDirection.ASCENDING.value == "ASC"

    def test_sort_direction_descending(self) -> None:
        """DESC wire value."""
        assert SortDirection.DESCENDING.value == "DESC"

    def test_sort_direction_count(self) -> None:
        """Exactly 2 directions."""
        assert len(SortDirection) == 2


# ===================================================================
# TwapStatus
# ===================================================================


class TestTwapStatus:
    """Contract tests for TWAP order status variants."""

    def test_twap_status_activated(self) -> None:
        """Activated wire value."""
        assert TwapStatus.ACTIVATED.value == "Activated"

    def test_twap_status_finished(self) -> None:
        """Finished wire value."""
        assert TwapStatus.FINISHED.value == "Finished"

    def test_twap_status_cancelled(self) -> None:
        """Cancelled wire value."""
        assert TwapStatus.CANCELLED.value == "Cancelled"

    def test_twap_status_all_variants(self) -> None:
        """All 3 TWAP status variants exist."""
        assert len(TwapStatus) == 3
