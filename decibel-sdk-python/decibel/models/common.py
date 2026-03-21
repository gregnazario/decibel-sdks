"""Common data models for the Decibel SDK."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .enums import SortDirection

T = TypeVar("T")


class PageParams(BaseModel):
    """Pagination parameters.

    Attributes:
        limit: Number of items per page
        offset: Offset for pagination
    """

    limit: int | None = Field(default=10, ge=1, le=1000)
    offset: int | None = Field(default=0, ge=0)


class SortParams(BaseModel):
    """Sorting parameters.

    Attributes:
        sort_key: Field to sort by
        sort_dir: Sort direction
    """

    sort_key: str | None = None
    sort_dir: SortDirection | None = None


class SearchTermParams(BaseModel):
    """Search term parameters.

    Attributes:
        search_term: Term to search for
    """

    search_term: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response.

    Attributes:
        items: List of items
        total_count: Total count of items across all pages
    """

    items: list[T]
    total_count: int


class PlaceOrderResult(BaseModel):
    """Result of placing an order.

    Attributes:
        success: Whether order was placed successfully
        order_id: Order ID (if successful)
        transaction_hash: Transaction hash
        error: Error message (if failed)
    """

    success: bool
    order_id: str | None = None
    transaction_hash: str | None = None
    error: str | None = None


class TwapOrderResult(BaseModel):
    """Result of placing a TWAP order.

    Attributes:
        success: Whether order was placed successfully
        order_id: Order ID (if successful)
        transaction_hash: Transaction hash
    """

    success: bool
    order_id: str | None = None
    transaction_hash: str


class TransactionResult(BaseModel):
    """Generic result for any on-chain transaction."""
    success: bool
    transaction_hash: str
    gas_used: int | None = None
    vm_status: str | None = None
