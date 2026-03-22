"""Price and size formatting utilities using Decimal arithmetic for precision.

All chain unit conversions use decimal.Decimal internally to avoid
binary floating-point representation errors that can cause off-by-one
chain units (which would be rejected on-chain for tick/lot violations).
"""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, ROUND_UP, Decimal


def _to_decimal(value: float | int | str | Decimal) -> Decimal:
    """Convert a value to Decimal via string to avoid float representation errors."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def amount_to_chain_units(amount: float | Decimal, *, decimals: int) -> int:
    """Convert a decimal amount to integer chain units using Decimal arithmetic.

    Example: amount_to_chain_units(5.67, decimals=9) == 5_670_000_000
    """
    d = _to_decimal(amount)
    factor = Decimal(10) ** decimals
    return int((d * factor).to_integral_value(rounding=ROUND_HALF_UP))


def chain_units_to_amount(chain_units: int, *, decimals: int) -> float:
    """Convert integer chain units back to a decimal amount."""
    d = Decimal(chain_units)
    factor = Decimal(10) ** decimals
    return float(d / factor)


def round_to_valid_price(
    price: float | Decimal,
    *,
    tick_size: float | Decimal,
    round_up: bool = False,
) -> float:
    """Round a price to the nearest valid tick size using Decimal arithmetic."""
    if price == 0:
        return 0.0
    d_price = _to_decimal(price)
    d_tick = _to_decimal(tick_size)
    ticks = d_price / d_tick
    if round_up:
        rounded_ticks = ticks.to_integral_value(rounding=ROUND_UP)
    else:
        rounded_ticks = ticks.to_integral_value(rounding=ROUND_DOWN)
    return float(rounded_ticks * d_tick)


def round_to_valid_order_size(
    size: float | Decimal,
    *,
    lot_size: float | Decimal,
    min_size: float | Decimal,
) -> float:
    """Round an order size down to the nearest valid lot size using Decimal.

    Returns 0.0 when the rounded result is below min_size.
    """
    if size == 0:
        return 0.0
    d_size = _to_decimal(size)
    d_lot = _to_decimal(lot_size)
    d_min = _to_decimal(min_size)
    lots = (d_size / d_lot).to_integral_value(rounding=ROUND_DOWN)
    rounded = lots * d_lot
    if rounded < d_min:
        return 0.0
    return float(rounded)


def to_chain_price(price: float | Decimal, *, px_decimals: int) -> int:
    """Convert a human-readable price to chain units."""
    return amount_to_chain_units(price, decimals=px_decimals)


def from_chain_price(chain_units: int, *, px_decimals: int) -> float:
    """Convert chain units back to a human-readable price."""
    return chain_units_to_amount(chain_units, decimals=px_decimals)


def to_chain_size(size: float | Decimal, *, sz_decimals: int) -> int:
    """Convert a human-readable size to chain units."""
    return amount_to_chain_units(size, decimals=sz_decimals)


def from_chain_size(chain_units: int, *, sz_decimals: int) -> float:
    """Convert chain units back to a human-readable size."""
    return chain_units_to_amount(chain_units, decimals=sz_decimals)
