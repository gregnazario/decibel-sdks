"""TDD tests for SDK enum types.

These tests lock down the wire-format values that every enum variant
serialises to.  A changed wire value would silently break order
placement, candlestick subscriptions, or status parsing — so each
variant is asserted individually.
"""

from __future__ import annotations

from decibel.models.enums import (
    CandlestickInterval,
    MarketDepthAggregationSize,
    OrderStatusType,
    SortDirection,
    TimeInForce,
    TradeAction,
    TwapStatus,
    VaultType,
    VolumeWindow,
)

# ===================================================================
# TimeInForce (IntEnum)
# ===================================================================


class TestTimeInForce:
    """Contract tests for order time-in-force variants.

    These integer values are serialised directly into on-chain
    transactions; a wrong value places a different order type.
    """

    def test_good_till_canceled_value(self) -> None:
        """GTC = 0 on the wire."""
        assert TimeInForce.GOOD_TILL_CANCELED == 0

    def test_post_only_value(self) -> None:
        """Post-only = 1 on the wire."""
        assert TimeInForce.POST_ONLY == 1

    def test_immediate_or_cancel_value(self) -> None:
        """IOC = 2 on the wire."""
        assert TimeInForce.IMMEDIATE_OR_CANCEL == 2

    def test_all_variants_exist(self) -> None:
        """TimeInForce must have exactly 3 variants.

        Adding a variant without updating tests is a signal to review
        transaction builder code.
        """
        assert len(TimeInForce) == 3

    def test_roundtrip_from_int(self) -> None:
        """int → enum → int roundtrip for every variant.

        Ensures enum members can be constructed from their wire values.
        """
        for member in TimeInForce:
            assert TimeInForce(member.value) is member


# ===================================================================
# CandlestickInterval (StrEnum)
# ===================================================================


class TestCandlestickInterval:
    """Contract tests for candlestick interval variants.

    Intervals are sent as query parameters and WebSocket subscription
    keys; a wrong string means no data or wrong resolution.
    """

    def test_one_minute_value(self) -> None:
        """1m interval wire value."""
        assert CandlestickInterval.ONE_MINUTE == "1m"

    def test_five_minutes_value(self) -> None:
        """5m interval wire value."""
        assert CandlestickInterval.FIVE_MINUTES == "5m"

    def test_fifteen_minutes_value(self) -> None:
        """15m interval wire value."""
        assert CandlestickInterval.FIFTEEN_MINUTES == "15m"

    def test_thirty_minutes_value(self) -> None:
        """30m interval wire value."""
        assert CandlestickInterval.THIRTY_MINUTES == "30m"

    def test_one_hour_value(self) -> None:
        """1h interval wire value."""
        assert CandlestickInterval.ONE_HOUR == "1h"

    def test_two_hours_value(self) -> None:
        """2h interval wire value."""
        assert CandlestickInterval.TWO_HOURS == "2h"

    def test_four_hours_value(self) -> None:
        """4h interval wire value."""
        assert CandlestickInterval.FOUR_HOURS == "4h"

    def test_eight_hours_value(self) -> None:
        """8h interval wire value."""
        assert CandlestickInterval.EIGHT_HOURS == "8h"

    def test_twelve_hours_value(self) -> None:
        """12h interval wire value."""
        assert CandlestickInterval.TWELVE_HOURS == "12h"

    def test_one_day_value(self) -> None:
        """1d interval wire value."""
        assert CandlestickInterval.ONE_DAY == "1d"

    def test_three_days_value(self) -> None:
        """3d interval wire value."""
        assert CandlestickInterval.THREE_DAYS == "3d"

    def test_one_week_value(self) -> None:
        """1w interval wire value."""
        assert CandlestickInterval.ONE_WEEK == "1w"

    def test_one_month_value(self) -> None:
        """1mo interval wire value."""
        assert CandlestickInterval.ONE_MONTH == "1mo"

    def test_all_variants_exist(self) -> None:
        """CandlestickInterval must have exactly 13 variants."""
        assert len(CandlestickInterval) == 13

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip for every variant."""
        for member in CandlestickInterval:
            assert CandlestickInterval(member.value) is member


# ===================================================================
# VolumeWindow (StrEnum)
# ===================================================================


class TestVolumeWindow:
    """Contract tests for volume calculation window variants."""

    def test_seven_days_value(self) -> None:
        """7d window wire value."""
        assert VolumeWindow.SEVEN_DAYS == "7d"

    def test_fourteen_days_value(self) -> None:
        """14d window wire value."""
        assert VolumeWindow.FOURTEEN_DAYS == "14d"

    def test_thirty_days_value(self) -> None:
        """30d window wire value."""
        assert VolumeWindow.THIRTY_DAYS == "30d"

    def test_ninety_days_value(self) -> None:
        """90d window wire value."""
        assert VolumeWindow.NINETY_DAYS == "90d"

    def test_all_variants_exist(self) -> None:
        """VolumeWindow must have exactly 4 variants."""
        assert len(VolumeWindow) == 4

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in VolumeWindow:
            assert VolumeWindow(member.value) is member


# ===================================================================
# OrderStatusType (StrEnum)
# ===================================================================


class TestOrderStatusType:
    """Contract tests for order status type variants and helpers.

    Bots branch on order status to decide whether to retry, cancel, or
    update internal state.  Misidentifying a status is critical.
    """

    def test_acknowledged_value(self) -> None:
        """Acknowledged wire value."""
        assert OrderStatusType.ACKNOWLEDGED == "Acknowledged"

    def test_filled_value(self) -> None:
        """Filled wire value."""
        assert OrderStatusType.FILLED == "Filled"

    def test_cancelled_value(self) -> None:
        """Cancelled wire value."""
        assert OrderStatusType.CANCELLED == "Cancelled"

    def test_rejected_value(self) -> None:
        """Rejected wire value."""
        assert OrderStatusType.REJECTED == "Rejected"

    def test_unknown_value(self) -> None:
        """Unknown wire value."""
        assert OrderStatusType.UNKNOWN == "Unknown"

    def test_all_variants_exist(self) -> None:
        """OrderStatusType must have exactly 5 variants."""
        assert len(OrderStatusType) == 5

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in OrderStatusType:
            assert OrderStatusType(member.value) is member

    # -- parse() --

    def test_parse_acknowledged(self) -> None:
        """parse('Acknowledged') → ACKNOWLEDGED."""
        assert OrderStatusType.parse("Acknowledged") == OrderStatusType.ACKNOWLEDGED

    def test_parse_filled(self) -> None:
        """parse('Filled') → FILLED."""
        assert OrderStatusType.parse("Filled") == OrderStatusType.FILLED

    def test_parse_cancelled_british(self) -> None:
        """parse('Cancelled') → CANCELLED (British spelling)."""
        assert OrderStatusType.parse("Cancelled") == OrderStatusType.CANCELLED

    def test_parse_canceled_american(self) -> None:
        """parse('Canceled') → CANCELLED (American spelling).

        The API may use either spelling; both must parse correctly.
        """
        assert OrderStatusType.parse("Canceled") == OrderStatusType.CANCELLED

    def test_parse_rejected(self) -> None:
        """parse('Rejected') → REJECTED."""
        assert OrderStatusType.parse("Rejected") == OrderStatusType.REJECTED

    def test_parse_unknown_string(self) -> None:
        """parse('SomeGarbage') → UNKNOWN.

        Graceful degradation for unexpected API responses.
        """
        assert OrderStatusType.parse("SomeGarbage") == OrderStatusType.UNKNOWN

    def test_parse_case_insensitive(self) -> None:
        """parse is case-insensitive (API may vary case)."""
        assert OrderStatusType.parse("acknowledged") == OrderStatusType.ACKNOWLEDGED
        assert OrderStatusType.parse("FILLED") == OrderStatusType.FILLED

    # -- is_success / is_failure / is_final --

    def test_is_success_acknowledged(self) -> None:
        """ACKNOWLEDGED is a success status (order accepted)."""
        assert OrderStatusType.ACKNOWLEDGED.is_success() is True

    def test_is_success_filled(self) -> None:
        """FILLED is a success status (order executed)."""
        assert OrderStatusType.FILLED.is_success() is True

    def test_is_success_cancelled(self) -> None:
        """CANCELLED is not a success status."""
        assert OrderStatusType.CANCELLED.is_success() is False

    def test_is_failure_cancelled(self) -> None:
        """CANCELLED is a failure status."""
        assert OrderStatusType.CANCELLED.is_failure() is True

    def test_is_failure_rejected(self) -> None:
        """REJECTED is a failure status."""
        assert OrderStatusType.REJECTED.is_failure() is True

    def test_is_failure_acknowledged(self) -> None:
        """ACKNOWLEDGED is not a failure status."""
        assert OrderStatusType.ACKNOWLEDGED.is_failure() is False

    def test_is_final_acknowledged(self) -> None:
        """ACKNOWLEDGED is final (success)."""
        assert OrderStatusType.ACKNOWLEDGED.is_final() is True

    def test_is_final_filled(self) -> None:
        """FILLED is final (success)."""
        assert OrderStatusType.FILLED.is_final() is True

    def test_is_final_cancelled(self) -> None:
        """CANCELLED is final (failure)."""
        assert OrderStatusType.CANCELLED.is_final() is True

    def test_is_final_unknown(self) -> None:
        """UNKNOWN is not final (still in-flight or indeterminate).

        Bots must not assume an UNKNOWN status is terminal.
        """
        assert OrderStatusType.UNKNOWN.is_final() is False


# ===================================================================
# SortDirection (StrEnum)
# ===================================================================


class TestSortDirection:
    """Contract tests for pagination sort direction."""

    def test_ascending_value(self) -> None:
        """ASC wire value for ascending sort."""
        assert SortDirection.ASCENDING == "ASC"

    def test_descending_value(self) -> None:
        """DESC wire value for descending sort."""
        assert SortDirection.DESCENDING == "DESC"

    def test_all_variants_exist(self) -> None:
        """SortDirection must have exactly 2 variants."""
        assert len(SortDirection) == 2

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in SortDirection:
            assert SortDirection(member.value) is member


# ===================================================================
# TwapStatus (StrEnum)
# ===================================================================


class TestTwapStatus:
    """Contract tests for TWAP order status variants.

    TWAP orders run over time; their status drives the polling loop
    in algorithmic execution engines.
    """

    def test_activated_value(self) -> None:
        """Activated wire value."""
        assert TwapStatus.ACTIVATED == "Activated"

    def test_finished_value(self) -> None:
        """Finished wire value."""
        assert TwapStatus.FINISHED == "Finished"

    def test_cancelled_value(self) -> None:
        """Cancelled wire value."""
        assert TwapStatus.CANCELLED == "Cancelled"

    def test_all_variants_exist(self) -> None:
        """TwapStatus must have exactly 3 variants."""
        assert len(TwapStatus) == 3

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in TwapStatus:
            assert TwapStatus(member.value) is member


# ===================================================================
# TradeAction (StrEnum)
# ===================================================================


class TestTradeAction:
    """Contract tests for trade action type variants.

    Trade actions classify each fill in the trade history; bots use
    them to separate opens from closes in PnL accounting.
    """

    def test_open_long_value(self) -> None:
        """OpenLong wire value."""
        assert TradeAction.OPEN_LONG == "OpenLong"

    def test_close_long_value(self) -> None:
        """CloseLong wire value."""
        assert TradeAction.CLOSE_LONG == "CloseLong"

    def test_open_short_value(self) -> None:
        """OpenShort wire value."""
        assert TradeAction.OPEN_SHORT == "OpenShort"

    def test_close_short_value(self) -> None:
        """CloseShort wire value."""
        assert TradeAction.CLOSE_SHORT == "CloseShort"

    def test_net_value(self) -> None:
        """Net wire value (position flip)."""
        assert TradeAction.NET == "Net"

    def test_all_variants_exist(self) -> None:
        """TradeAction must have exactly 5 variants."""
        assert len(TradeAction) == 5

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in TradeAction:
            assert TradeAction(member.value) is member


# ===================================================================
# VaultType (StrEnum)
# ===================================================================


class TestVaultType:
    """Contract tests for vault type variants."""

    def test_user_value(self) -> None:
        """user wire value."""
        assert VaultType.USER == "user"

    def test_protocol_value(self) -> None:
        """protocol wire value."""
        assert VaultType.PROTOCOL == "protocol"

    def test_all_variants_exist(self) -> None:
        """VaultType must have exactly 2 variants."""
        assert len(VaultType) == 2

    def test_roundtrip_from_string(self) -> None:
        """str → enum → str roundtrip."""
        for member in VaultType:
            assert VaultType(member.value) is member


# ===================================================================
# MarketDepthAggregationSize (IntEnum)
# ===================================================================


class TestMarketDepthAggregationSize:
    """Contract tests for market depth aggregation size variants.

    These integers are sent as query parameters when requesting
    aggregated order book snapshots.
    """

    def test_size_1_value(self) -> None:
        """SIZE_1 = 1 on the wire."""
        assert MarketDepthAggregationSize.SIZE_1 == 1

    def test_size_2_value(self) -> None:
        """SIZE_2 = 2 on the wire."""
        assert MarketDepthAggregationSize.SIZE_2 == 2

    def test_size_5_value(self) -> None:
        """SIZE_5 = 5 on the wire."""
        assert MarketDepthAggregationSize.SIZE_5 == 5

    def test_size_10_value(self) -> None:
        """SIZE_10 = 10 on the wire."""
        assert MarketDepthAggregationSize.SIZE_10 == 10

    def test_size_100_value(self) -> None:
        """SIZE_100 = 100 on the wire."""
        assert MarketDepthAggregationSize.SIZE_100 == 100

    def test_size_1000_value(self) -> None:
        """SIZE_1000 = 1000 on the wire."""
        assert MarketDepthAggregationSize.SIZE_1000 == 1000

    def test_all_variants_exist(self) -> None:
        """MarketDepthAggregationSize must have exactly 6 variants."""
        assert len(MarketDepthAggregationSize) == 6

    def test_all_sizes_class_method(self) -> None:
        """all_sizes() returns a list containing every variant.

        Used by UI components to populate aggregation-size dropdowns.
        """
        sizes = MarketDepthAggregationSize.all_sizes()
        assert len(sizes) == 6
        assert MarketDepthAggregationSize.SIZE_1 in sizes
        assert MarketDepthAggregationSize.SIZE_1000 in sizes

    def test_roundtrip_from_int(self) -> None:
        """int → enum → int roundtrip for every variant."""
        for member in MarketDepthAggregationSize:
            assert MarketDepthAggregationSize(member.value) is member
