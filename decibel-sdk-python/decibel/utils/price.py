"""Price rounding utilities."""

import math


def round_to_tick_size(price: float, tick_size: float, px_decimals: int, round_up: bool) -> float:
    """Round a price to the nearest valid tick size.

    Args:
        price: Price to round
        tick_size: Tick size
        px_decimals: Price decimals (unused, for API compatibility)
        round_up: Whether to round up (True) or down (False)

    Returns:
        Rounded price
    """
    if tick_size <= 0:
        return price

    ticks = price / tick_size
    rounded_ticks = math.ceil(ticks) if round_up else math.floor(ticks)
    return rounded_ticks * tick_size
