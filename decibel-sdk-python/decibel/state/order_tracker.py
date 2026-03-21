"""Order lifecycle tracking with state transitions and callbacks."""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)


class OrderState(enum.Enum):
    """Possible states of a tracked order."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class HistoryEntry:
    """Single entry in an order's state-transition history."""

    state: OrderState
    timestamp: float


@dataclass
class TrackedOrder:
    """An order tracked by the lifecycle tracker."""

    order_id: str
    client_order_id: str | None
    market: str
    subaccount: str
    is_buy: bool
    price: float
    size: float
    state: OrderState
    history: list[HistoryEntry] = field(default_factory=list)


StatusChangeCallback = Callable[[str, OrderState, OrderState], None]


class OrderLifecycleTracker:
    """Tracks order lifecycles from submission to terminal state."""

    def __init__(self) -> None:
        self._orders: dict[str, TrackedOrder] = {}
        self._client_id_index: dict[str, str] = {}
        self._callbacks: list[StatusChangeCallback] = []

    def track(
        self,
        order_id: str,
        *,
        client_order_id: str | None = None,
        market: str = "",
        subaccount: str = "",
        is_buy: bool = True,
        price: float = 0.0,
        size: float = 0.0,
        state: OrderState = OrderState.PENDING,
    ) -> None:
        if order_id in self._orders:
            logger.warning("Duplicate track for order %s", order_id)
            return

        entry = HistoryEntry(state=state, timestamp=time.time())
        order = TrackedOrder(
            order_id=order_id,
            client_order_id=client_order_id,
            market=market,
            subaccount=subaccount,
            is_buy=is_buy,
            price=price,
            size=size,
            state=state,
            history=[entry],
        )
        self._orders[order_id] = order
        if client_order_id is not None:
            self._client_id_index[client_order_id] = order_id

    def transition(self, order_id: str, new_state: OrderState) -> None:
        order = self._orders.get(order_id)
        if order is None:
            return
        if order.state == new_state:
            return

        old_state = order.state
        order.state = new_state
        order.history.append(HistoryEntry(state=new_state, timestamp=time.time()))

        for cb in self._callbacks:
            cb(order_id, old_state, new_state)

    def get(self, order_id: str) -> TrackedOrder | None:
        return self._orders.get(order_id)

    def get_by_client_id(self, client_order_id: str) -> TrackedOrder | None:
        order_id = self._client_id_index.get(client_order_id)
        if order_id is None:
            return None
        return self._orders.get(order_id)

    def history(self, order_id: str) -> list[HistoryEntry]:
        order = self._orders.get(order_id)
        if order is None:
            return []
        return list(order.history)

    def pending_orders(self) -> list[TrackedOrder]:
        return [o for o in self._orders.values() if o.state == OrderState.PENDING]

    def active_orders(self) -> list[TrackedOrder]:
        active_states = {OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED}
        return [o for o in self._orders.values() if o.state in active_states]

    def completed_orders(self) -> list[TrackedOrder]:
        terminal_states = {OrderState.FILLED, OrderState.CANCELLED, OrderState.EXPIRED}
        return [o for o in self._orders.values() if o.state in terminal_states]

    def on_status_change(self, callback: StatusChangeCallback) -> None:
        self._callbacks.append(callback)
