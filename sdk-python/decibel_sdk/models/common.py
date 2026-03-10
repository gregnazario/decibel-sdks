"""Shared enumerations, pagination, and result types."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# --- Enumerations ---


class TimeInForce(IntEnum):
    GOOD_TILL_CANCELED = 0
    POST_ONLY = 1
    IMMEDIATE_OR_CANCEL = 2


class CandlestickInterval(str, Enum):
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


class VolumeWindow(str, Enum):
    SEVEN_DAYS = "7d"
    FOURTEEN_DAYS = "14d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"


class OrderStatusType(str, Enum):
    ACKNOWLEDGED = "Acknowledged"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    UNKNOWN = "Unknown"

    @classmethod
    def from_str(cls, s: str) -> OrderStatusType:
        if s in ("Cancelled", "Canceled"):
            return cls.CANCELLED
        try:
            return cls(s)
        except ValueError:
            return cls.UNKNOWN

    @property
    def is_success(self) -> bool:
        return self in (self.ACKNOWLEDGED, self.FILLED)

    @property
    def is_failure(self) -> bool:
        return self in (self.CANCELLED, self.REJECTED)

    @property
    def is_final(self) -> bool:
        return self.is_success or self.is_failure


class SortDirection(str, Enum):
    ASCENDING = "ASC"
    DESCENDING = "DESC"


class TwapStatus(str, Enum):
    ACTIVATED = "Activated"
    FINISHED = "Finished"
    CANCELLED = "Cancelled"


class TradeAction(str, Enum):
    OPEN_LONG = "OpenLong"
    CLOSE_LONG = "CloseLong"
    OPEN_SHORT = "OpenShort"
    CLOSE_SHORT = "CloseShort"
    NET = "Net"


class VaultType(str, Enum):
    USER = "user"
    PROTOCOL = "protocol"


class MarketDepthAggregationSize(IntEnum):
    ONE = 1
    TWO = 2
    FIVE = 5
    TEN = 10
    HUNDRED = 100
    THOUSAND = 1000


# --- Pagination ---


class PageParams(BaseModel):
    limit: int | None = None
    offset: int | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total_count: int


class SortParams(BaseModel):
    sort_key: str | None = None
    sort_dir: SortDirection | None = None


class SearchTermParams(BaseModel):
    search_term: str | None = None


# --- Place Order Result ---


class PlaceOrderResult(BaseModel):
    success: bool
    order_id: str | None = None
    transaction_hash: str | None = None
    error: str | None = None

    @classmethod
    def make_success(cls, order_id: str | None, transaction_hash: str) -> PlaceOrderResult:
        return cls(success=True, order_id=order_id, transaction_hash=transaction_hash)

    @classmethod
    def make_failure(cls, error: str) -> PlaceOrderResult:
        return cls(success=False, error=error)


# --- TWAP Order Result ---


class TwapOrderResult(BaseModel):
    success: bool
    order_id: str | None = None
    transaction_hash: str
