"""Price rounding utilities."""

from __future__ import annotations

import math


def round_to_tick_size(price: float, tick_size: float, _px_decimals: int, round_up: bool) -> float:
    """Round a price to the nearest valid tick size."""
    if tick_size <= 0.0:
        return price
    ticks = price / tick_size
    rounded_ticks = math.ceil(ticks) if round_up else math.floor(ticks)
    return rounded_ticks * tick_size
