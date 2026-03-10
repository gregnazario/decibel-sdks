"""Order and TWAP models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UserOpenOrder(BaseModel):
    market: str
    order_id: str
    client_order_id: str | None = None
    price: float
    orig_size: float
    remaining_size: float
    is_buy: bool
    time_in_force: str
    is_reduce_only: bool
    status: str
    transaction_unix_ms: int
    transaction_version: int


class UserOrderHistoryItem(BaseModel):
    market: str
    order_id: str
    client_order_id: str | None = None
    price: float
    orig_size: float
    remaining_size: float
    is_buy: bool
    time_in_force: str
    is_reduce_only: bool
    status: str
    transaction_unix_ms: int
    transaction_version: int


class OrderStatus(BaseModel):
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
    status: str
    transaction_unix_ms: int
    transaction_version: int


class OrderEvent(BaseModel):
    client_order_id: Any
    details: str
    is_bid: bool
    is_taker: bool
    market: str
    metadata_bytes: str
    order_id: str
    orig_size: str
    parent: str
    price: str
    remaining_size: str
    size_delta: str
    status: Any
    time_in_force: Any
    trigger_condition: Any
    user: str


class TwapEvent(BaseModel):
    account: str
    duration_s: str
    frequency_s: str
    is_buy: bool
    is_reduce_only: bool
    market: str
    order_id: Any
    orig_size: str
    remain_size: str
    start_time_s: str
    status: Any
    client_order_id: Any
