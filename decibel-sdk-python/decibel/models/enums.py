"""Enum definitions for the Decibel SDK."""

from enum import IntEnum, StrEnum


class TimeInForce(IntEnum):
    """Order time-in-force types."""

    GOOD_TILL_CANCELED = 0
    """Order remains on book until filled or canceled."""

    POST_ONLY = 1
    """Order rejected if it would immediately match."""

    IMMEDIATE_OR_CANCEL = 2
    """Fill what's possible immediately, cancel the rest."""


class CandlestickInterval(StrEnum):
    """OHLC candlestick intervals."""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    TWO_HOURS = "2h"
    FOUR_HOURS = "4h"
    EIGHT_HOURS = "8h"
    TWELVE_HOURS = "12h"
    ONE_DAY = "1d"
    THREE_DAYS = "3d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1mo"


class VolumeWindow(StrEnum):
    """Time windows for volume calculation."""

    SEVEN_DAYS = "7d"
    FOURTEEN_DAYS = "14d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"


class OrderStatusType(StrEnum):
    """Order status types."""

    ACKNOWLEDGED = "Acknowledged"
    """Order accepted by matching engine."""

    FILLED = "Filled"
    """Order fully filled."""

    CANCELLED = "Cancelled"
    """Order cancelled."""

    REJECTED = "Rejected"
    """Order rejected."""

    UNKNOWN = "Unknown"
    """Unknown status."""

    @classmethod
    def parse(cls, s: str) -> "OrderStatusType":
        """Parse a string to an OrderStatusType.

        Args:
            s: String to parse

        Returns:
            Parsed OrderStatusType
        """
        normalized = s.lower()
        if normalized == "acknowledged":
            return cls.ACKNOWLEDGED
        if normalized == "filled":
            return cls.FILLED
        if normalized in ("cancelled", "canceled"):
            return cls.CANCELLED
        if normalized == "rejected":
            return cls.REJECTED
        return cls.UNKNOWN

    def is_success(self) -> bool:
        """Check if status indicates success.

        Returns:
            True if status is acknowledged or filled
        """
        return self in (self.ACKNOWLEDGED, self.FILLED)

    def is_failure(self) -> bool:
        """Check if status indicates failure.

        Returns:
            True if status is cancelled or rejected
        """
        return self in (self.CANCELLED, self.REJECTED)

    def is_final(self) -> bool:
        """Check if status is terminal.

        Returns:
            True if status is final (success or failure)
        """
        return self.is_success() or self.is_failure()


class SortDirection(StrEnum):
    """Sort direction for pagination."""

    ASCENDING = "ASC"
    DESCENDING = "DESC"


class TwapStatus(StrEnum):
    """TWAP order status types."""

    ACTIVATED = "Activated"
    FINISHED = "Finished"
    CANCELLED = "Cancelled"


class TradeAction(StrEnum):
    """Trade action types."""

    OPEN_LONG = "OpenLong"
    CLOSE_LONG = "CloseLong"
    OPEN_SHORT = "OpenShort"
    CLOSE_SHORT = "CloseShort"
    NET = "Net"


class VaultType(StrEnum):
    """Vault types."""

    USER = "user"
    PROTOCOL = "protocol"


class MarketDepthAggregationSize(IntEnum):
    """Valid market depth aggregation sizes."""

    SIZE_1 = 1
    SIZE_2 = 2
    SIZE_5 = 5
    SIZE_10 = 10
    SIZE_100 = 100
    SIZE_1000 = 1000

    @classmethod
    def all_sizes(cls) -> list["MarketDepthAggregationSize"]:
        """Get all valid aggregation sizes.

        Returns:
            List of all aggregation sizes
        """
        return list(cls)
