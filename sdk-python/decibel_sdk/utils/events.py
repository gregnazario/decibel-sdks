"""Transaction event parsing utilities."""

from __future__ import annotations

from typing import Any


def extract_order_id_from_events(events: list[dict[str, Any]], subaccount_addr: str) -> str | None:
    """Extract an order ID from OrderEvent in transaction events."""
    for event in events:
        event_type = event.get("type", "")
        if "::market_types::OrderEvent" in event_type:
            data = event.get("data", {})
            if data.get("user") == subaccount_addr:
                order_id = data.get("order_id")
                if isinstance(order_id, str):
                    return order_id
    return None
