"""Bulk order management for high-frequency two-sided quoting."""

from __future__ import annotations

from pydantic import BaseModel

MAX_LEVELS_PER_SIDE = 30


class BulkQuoteResult(BaseModel):
    """Result of a set_quotes() call."""

    bid_count: int
    ask_count: int
    sequence_number: int


class FillSummary(BaseModel):
    """Accumulated fill statistics between resets."""

    bid_filled_size: float = 0.0
    ask_filled_size: float = 0.0
    net_size: float = 0.0
    avg_bid_price: float = 0.0
    avg_ask_price: float = 0.0
    fill_count: int = 0


class BulkOrderManager:
    """Manages two-sided quoting with atomic replacement and fill tracking."""

    def __init__(self, market: str, subaccount: str = "") -> None:
        self._market = market
        self._subaccount = subaccount
        self._sequence_number = 0
        self._live_bids: list[dict] = []
        self._live_asks: list[dict] = []
        self._bid_filled_size = 0.0
        self._ask_filled_size = 0.0
        self._bid_cost = 0.0
        self._ask_cost = 0.0
        self._fill_count = 0

    @property
    def market(self) -> str:
        return self._market

    @property
    def sequence_number(self) -> int:
        return self._sequence_number

    @property
    def live_bids(self) -> list[dict]:
        return list(self._live_bids)

    @property
    def live_asks(self) -> list[dict]:
        return list(self._live_asks)

    def set_quotes(
        self, bids: list[dict], asks: list[dict]
    ) -> BulkQuoteResult:
        if len(bids) > MAX_LEVELS_PER_SIDE:
            raise ValueError(
                f"Too many bid levels: {len(bids)} exceeds max {MAX_LEVELS_PER_SIDE} (30)"
            )
        if len(asks) > MAX_LEVELS_PER_SIDE:
            raise ValueError(
                f"Too many ask levels: {len(asks)} exceeds max {MAX_LEVELS_PER_SIDE} (30)"
            )

        self._sequence_number += 1
        self._live_bids = sorted(bids, key=lambda x: x["price"], reverse=True)
        self._live_asks = sorted(asks, key=lambda x: x["price"])

        return BulkQuoteResult(
            bid_count=len(bids),
            ask_count=len(asks),
            sequence_number=self._sequence_number,
        )

    def cancel_all(self) -> None:
        self._sequence_number += 1
        self._live_bids = []
        self._live_asks = []

    def is_quoting(self) -> bool:
        return len(self._live_bids) > 0 and len(self._live_asks) > 0

    def apply_fill(self, *, is_buy: bool, size: float, price: float) -> None:
        if is_buy:
            self._bid_cost += size * price
            self._bid_filled_size += size
        else:
            self._ask_cost += size * price
            self._ask_filled_size += size
        self._fill_count += 1

    def filled_since_last_reset(self) -> FillSummary:
        return FillSummary(
            bid_filled_size=self._bid_filled_size,
            ask_filled_size=self._ask_filled_size,
            net_size=self._bid_filled_size - self._ask_filled_size,
            avg_bid_price=(
                self._bid_cost / self._bid_filled_size
                if self._bid_filled_size > 0
                else 0.0
            ),
            avg_ask_price=(
                self._ask_cost / self._ask_filled_size
                if self._ask_filled_size > 0
                else 0.0
            ),
            fill_count=self._fill_count,
        )

    def reset_fill_tracker(self) -> FillSummary:
        summary = self.filled_since_last_reset()
        self._bid_filled_size = 0.0
        self._ask_filled_size = 0.0
        self._bid_cost = 0.0
        self._ask_cost = 0.0
        self._fill_count = 0
        return summary
