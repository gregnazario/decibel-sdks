"""Order-related data models."""

from pydantic import BaseModel

from .enums import TwapStatus


class OrderStatus(BaseModel):
    """Status of an order.

    Attributes:
        parent: Parent account address
        market: Market address
        order_id: Order ID
        status: Status string
        orig_size: Original size
        remaining_size: Remaining size
        size_delta: Size delta
        price: Price
        is_buy: Buy or sell
        details: Status details
        transaction_version: Transaction version
        unix_ms: Timestamp in milliseconds
    """

    parent: str
    market: str
    order_id: str
    status: str
    orig_size: float
    remaining_size: float
    size_delta: float
    price: float
    is_buy: bool
    details: str
    transaction_version: int
    unix_ms: int


class UserActiveTwap(BaseModel):
    """Active TWAP order.

    Attributes:
        market: Market address
        is_buy: Buy or sell
        order_id: TWAP order ID
        client_order_id: Client order ID
        is_reduce_only: Reduce only
        start_unix_ms: Start timestamp in milliseconds
        frequency_s: Execution frequency in seconds
        duration_s: Total duration in seconds
        orig_size: Original size
        remaining_size: Remaining size
        status: TWAP status
        transaction_unix_ms: Last transaction timestamp in milliseconds
        transaction_version: Transaction version
    """

    market: str
    is_buy: bool
    order_id: str
    client_order_id: str
    is_reduce_only: bool
    start_unix_ms: int
    frequency_s: int
    duration_s: int
    orig_size: float
    remaining_size: float
    status: TwapStatus
    transaction_unix_ms: int
    transaction_version: int
