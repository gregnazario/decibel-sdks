"""Price rounding utilities."""

from decimal import ROUND_DOWN, ROUND_UP, Decimal


def round_to_tick_size(
    price: float, tick_size: float, px_decimals: int, round_up: bool
) -> float:
    """Round a price to the nearest tick size using Decimal arithmetic.

    Args:
        price: Price to round
        tick_size: Minimum price increment
        px_decimals: Number of decimal places for this market
        round_up: If True, round up; if False, round down
    """
    if tick_size == 0:
        return price
    d_price = Decimal(str(price))
    d_tick = Decimal(str(tick_size))
    ticks = d_price / d_tick
    if round_up:
        rounded_ticks = ticks.to_integral_value(rounding=ROUND_UP)
    else:
        rounded_ticks = ticks.to_integral_value(rounding=ROUND_DOWN)
    result = rounded_ticks * d_tick
    quantizer = Decimal(10) ** -px_decimals
    return float(result.quantize(quantizer))
