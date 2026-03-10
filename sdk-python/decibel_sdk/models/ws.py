"""WebSocket message wrappers for subscription topics."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

from decibel_sdk.models.account import (
    AccountOverview,
    UserFundingHistoryItem,
    UserTradeHistoryItem,
)
from decibel_sdk.models.market import (
    Candlestick,
    MarketDepth,
    MarketPrice,
    MarketTrade,
)
from decibel_sdk.models.order import (
    UserActiveTwap,
    UserOpenOrder,
    UserOrderHistoryItem,
)
from decibel_sdk.models.position import UserPosition

T = TypeVar("T")


class WsMessage(BaseModel, Generic[T]):
    channel: str
    data: T


class AccountOverviewWsMessage(BaseModel):
    account_overview: AccountOverview


class UserPositionsWsMessage(BaseModel):
    positions: list[UserPosition]


class UserOpenOrdersWsMessage(BaseModel):
    orders: list[UserOpenOrder]


class UserOrderHistoryWsMessage(BaseModel):
    orders: list[UserOrderHistoryItem]


class UserTradeHistoryWsMessage(BaseModel):
    trades: list[UserTradeHistoryItem]


class UserFundingHistoryWsMessage(BaseModel):
    funding: list[UserFundingHistoryItem]


class MarketPriceWsMessage(MarketPrice):
    pass


class AllMarketPricesWsMessage(BaseModel):
    prices: list[MarketPrice]


class MarketTradesWsMessage(BaseModel):
    trades: list[MarketTrade]


class CandlestickWsMessage(BaseModel):
    candle: Candlestick


class MarketDepthWsMessage(MarketDepth):
    pass


class UserActiveTwapsWsMessage(BaseModel):
    twaps: list[UserActiveTwap]


class WsSubscribeRequest(BaseModel):
    method: str
    subscription: str

    @classmethod
    def subscribe(cls, topic: str) -> WsSubscribeRequest:
        return cls(method="subscribe", subscription=topic)

    @classmethod
    def unsubscribe(cls, topic: str) -> WsSubscribeRequest:
        return cls(method="unsubscribe", subscription=topic)
