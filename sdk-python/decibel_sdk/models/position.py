"""Position models."""

from __future__ import annotations

from pydantic import BaseModel


class UserPosition(BaseModel):
    market: str
    user: str
    size: float
    user_leverage: float
    entry_price: float
    is_isolated: bool
    unrealized_funding: float
    estimated_liquidation_price: float
    tp_order_id: str | None = None
    tp_trigger_price: float | None = None
    tp_limit_price: float | None = None
    sl_order_id: str | None = None
    sl_trigger_price: float | None = None
    sl_limit_price: float | None = None
    has_fixed_sized_tpsls: bool


class PerpPosition(BaseModel):
    size: float
    sz_decimals: int
    entry_px: float
    max_leverage: float
    is_long: bool
    token_type: str


class CrossedPosition(BaseModel):
    positions: list[PerpPosition]
