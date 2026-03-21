"""Price and size formatting utilities for converting between human-readable
values and on-chain integer representations."""

from __future__ import annotations

import math


def amount_to_chain_units(amount: float, *, decimals: int) -> int:
    """Convert a decimal amount to integer chain units.

    Example: amount_to_chain_units(5.67, decimals=9) == 5_670_000_000
    """
    return int(round(amount * (10 ** decimals)))


def chain_units_to_amount(chain_units: int, *, decimals: int) -> float:
    """Convert integer chain units back to a decimal amount."""
    return chain_units / (10 ** decimals)


def round_to_valid_price(
    price: float,
    *,
    tick_size: float,
    round_up: bool = False,
) -> float:
    """Round a price to the nearest valid tick size.

    By default rounds down (conservative for buys).  Set *round_up=True*
    for sell-side prices (conservative = higher).
    """
    if price == 0:
        return 0.0
    ticks = price / tick_size
    rounded_ticks = math.ceil(ticks) if round_up else math.floor(ticks)
    return rounded_ticks * tick_size


def round_to_valid_order_size(
    size: float,
    *,
    lot_size: float,
    min_size: float,
) -> float:
    """Round an order size down to the nearest valid lot size.

    Returns 0.0 when the rounded result is below *min_size*, signalling
    that the order should not be placed.
    """
    if size == 0:
        return 0.0
    lots = math.floor(size / lot_size)
    rounded = lots * lot_size
    if rounded < min_size:
        return 0.0
    return rounded


def to_chain_price(price: float, *, px_decimals: int) -> int:
    """Convert a human-readable price to chain units."""
    return amount_to_chain_units(price, decimals=px_decimals)


def from_chain_price(chain_units: int, *, px_decimals: int) -> float:
    """Convert chain units back to a human-readable price."""
    return chain_units_to_amount(chain_units, decimals=px_decimals)


def to_chain_size(size: float, *, sz_decimals: int) -> int:
    """Convert a human-readable size to chain units."""
    return amount_to_chain_units(size, decimals=sz_decimals)


def from_chain_size(chain_units: int, *, sz_decimals: int) -> float:
    """Convert chain units back to a human-readable size."""
    return chain_units_to_amount(chain_units, decimals=sz_decimals)
