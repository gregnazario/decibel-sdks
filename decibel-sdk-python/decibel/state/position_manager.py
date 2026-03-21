"""In-memory cache aggregating positions, orders, overviews, and market data."""

from __future__ import annotations

import threading
import time

from decibel.models.account import AccountOverview, UserOpenOrder, UserPosition
from decibel.models.market import MarketDepth, MarketPrice


class PositionStateManager:
    """Central state manager for positions, orders, overviews, and market data.

    All public methods are thread-safe via a reentrant lock.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._positions: dict[str, dict[str, UserPosition]] = {}
        self._open_orders: dict[str, dict[str, UserOpenOrder]] = {}
        self._overviews: dict[str, AccountOverview] = {}
        self._prices: dict[str, MarketPrice] = {}
        self._depths: dict[str, MarketDepth] = {}
        self._last_update_ms: int = 0
        self._is_connected: bool = False
        self._gap_detected: bool = False

    def _touch(self) -> None:
        self._last_update_ms = int(time.time() * 1000)
        self._is_connected = True

    # ----- positions -----

    def merge_position(self, position: UserPosition) -> None:
        with self._lock:
            subaccount = position.user
            market = position.market
            if subaccount not in self._positions:
                self._positions[subaccount] = {}
            if position.size == 0:
                self._positions[subaccount].pop(market, None)
            else:
                self._positions[subaccount][market] = position
            self._touch()

    def positions(self, subaccount: str) -> dict[str, UserPosition]:
        with self._lock:
            return dict(self._positions.get(subaccount, {}))

    def position(self, market: str, subaccount: str) -> UserPosition | None:
        with self._lock:
            return self._positions.get(subaccount, {}).get(market)

    def has_position(self, market: str, subaccount: str) -> bool:
        with self._lock:
            return market in self._positions.get(subaccount, {})

    # ----- exposure -----

    def net_exposure(self, subaccount: str) -> float:
        with self._lock:
            total = 0.0
            for market, pos in self._positions.get(subaccount, {}).items():
                px = self._prices.get(market)
                mark = px.mark_px if px else pos.entry_price
                total += pos.size * mark
            return total

    def gross_exposure(self, subaccount: str) -> float:
        with self._lock:
            total = 0.0
            for market, pos in self._positions.get(subaccount, {}).items():
                px = self._prices.get(market)
                mark = px.mark_px if px else pos.entry_price
                total += abs(pos.size * mark)
            return total

    # ----- open orders -----

    TERMINAL_STATUSES = {"Cancelled", "Canceled", "Filled", "Expired", "Rejected"}

    def merge_open_orders(self, orders: list[UserOpenOrder], subaccount: str) -> None:
        with self._lock:
            if subaccount not in self._open_orders:
                self._open_orders[subaccount] = {}
            store = self._open_orders[subaccount]
            for order in orders:
                if order.status in self.TERMINAL_STATUSES:
                    store.pop(order.order_id, None)
                else:
                    store[order.order_id] = order
            self._touch()

    def open_orders(self, subaccount: str) -> list[UserOpenOrder]:
        with self._lock:
            return list(self._open_orders.get(subaccount, {}).values())

    def open_orders_by_market(self, market: str, subaccount: str) -> list[UserOpenOrder]:
        with self._lock:
            return [
                o for o in self._open_orders.get(subaccount, {}).values()
                if o.market == market
            ]

    def order_by_id(self, order_id: str, subaccount: str) -> UserOpenOrder | None:
        with self._lock:
            return self._open_orders.get(subaccount, {}).get(order_id)

    def order_by_client_id(
        self, client_order_id: str, subaccount: str
    ) -> UserOpenOrder | None:
        with self._lock:
            for order in self._open_orders.get(subaccount, {}).values():
                if order.client_order_id == client_order_id:
                    return order
            return None

    # ----- account overview -----

    def merge_overview(self, overview: AccountOverview, subaccount: str) -> None:
        with self._lock:
            self._overviews[subaccount] = overview
            self._touch()

    def overview(self, subaccount: str) -> AccountOverview | None:
        with self._lock:
            return self._overviews.get(subaccount)

    def equity(self, subaccount: str) -> float:
        with self._lock:
            ov = self._overviews.get(subaccount)
            return ov.perp_equity_balance if ov else 0.0

    def margin_usage_pct(self, subaccount: str) -> float:
        """Return margin usage as a 0.0-1.0 fraction, matching AccountOverview."""
        with self._lock:
            ov = self._overviews.get(subaccount)
            if not ov or ov.perp_equity_balance == 0:
                return 0.0
            return ov.total_margin / ov.perp_equity_balance

    def available_margin(self, subaccount: str) -> float:
        with self._lock:
            ov = self._overviews.get(subaccount)
            if not ov:
                return 0.0
            return ov.perp_equity_balance - ov.total_margin

    # ----- market data -----

    def merge_price(self, price: MarketPrice) -> None:
        with self._lock:
            self._prices[price.market] = price
            self._touch()

    def price(self, market: str) -> MarketPrice | None:
        with self._lock:
            return self._prices.get(market)

    def mark_price(self, market: str) -> float | None:
        with self._lock:
            px = self._prices.get(market)
            return px.mark_px if px else None

    def mid_price(self, market: str) -> float | None:
        with self._lock:
            px = self._prices.get(market)
            return px.mid_px if px else None

    def merge_depth(self, depth: MarketDepth) -> None:
        with self._lock:
            self._depths[depth.market] = depth
            self._touch()

    def depth(self, market: str) -> MarketDepth | None:
        with self._lock:
            return self._depths.get(market)

    # ----- state metadata -----

    @property
    def last_update_ms(self) -> int:
        with self._lock:
            return self._last_update_ms

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._is_connected

    @property
    def gap_detected(self) -> bool:
        with self._lock:
            return self._gap_detected

    def notify_disconnect(self) -> None:
        with self._lock:
            self._is_connected = False
            self._gap_detected = True

    def notify_resync_complete(self) -> None:
        with self._lock:
            self._is_connected = True
            self._gap_detected = False
