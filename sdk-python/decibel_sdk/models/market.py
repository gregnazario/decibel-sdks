"""Market data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerpMarketConfig(BaseModel):
    market_addr: str
    market_name: str
    sz_decimals: int
    px_decimals: int
    max_leverage: float
    min_size: float
    lot_size: float
    tick_size: float
    max_open_interest: float
    margin_call_fee_pct: float
    taker_in_next_block: bool


class MarketOrder(BaseModel):
    price: float
    size: float


class MarketDepth(BaseModel):
    market: str
    bids: list[MarketOrder]
    asks: list[MarketOrder]
    unix_ms: int


class MarketPrice(BaseModel):
    market: str
    mark_px: float
    mid_px: float
    oracle_px: float
    funding_rate_bps: float
    is_funding_positive: bool
    open_interest: float
    transaction_unix_ms: int


class MarketContext(BaseModel):
    market: str
    volume_24h: float
    open_interest: float
    previous_day_price: float
    price_change_pct_24h: float


class Candlestick(BaseModel):
    close_timestamp: int = Field(alias="T")
    c: float
    h: float
    i: str
    l: float
    o: float
    t: int
    v: float

    model_config = {"populate_by_name": True}


class MarketTrade(BaseModel):
    market: str
    price: float
    size: float
    is_buy: bool
    unix_ms: int
