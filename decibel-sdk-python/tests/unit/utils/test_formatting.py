"""TDD tests for price and size formatting utilities.

These tests define the contract for formatting functions that convert
between human-readable prices/sizes and on-chain integer
representations.  Correct rounding is critical — an off-by-one tick
or lot causes order rejections on-chain.

The functions under test do NOT yet exist in ``decibel.utils.formatting``;
they will be implemented to satisfy these tests (test-driven development).
"""

from __future__ import annotations

import pytest

from decibel.utils.formatting import (
    amount_to_chain_units,
    chain_units_to_amount,
    from_chain_price,
    round_to_valid_order_size,
    round_to_valid_price,
    to_chain_price,
)


# ===================================================================
# round_to_valid_price
# ===================================================================


class TestRoundToValidPrice:
    """Contract tests for price rounding to a market's tick_size.

    Limit-order prices must be exact multiples of the tick size.
    These tests cover BTC (tick=0.1), ETH (tick=0.01), and meme
    markets (tick=0.00001).
    """

    def test_round_down_btc(self) -> None:
        """BTC tick=0.1: 95,000.15 rounds down to 95,000.1.

        Default rounding direction is down (conservative for buys).
        """
        result = round_to_valid_price(95_000.15, tick_size=0.1)
        assert result == pytest.approx(95_000.1)

    def test_round_up_btc(self) -> None:
        """BTC tick=0.1: 95,000.15 rounds up to 95,000.2 when requested.

        Used for sell limit prices (conservative = higher).
        """
        result = round_to_valid_price(95_000.15, tick_size=0.1, round_up=True)
        assert result == pytest.approx(95_000.2)

    def test_exact_multiple_unchanged(self) -> None:
        """Price already on a tick boundary should not be modified.

        95,000.0 with tick=0.1 stays 95,000.0.
        """
        result = round_to_valid_price(95_000.0, tick_size=0.1)
        assert result == pytest.approx(95_000.0)

    def test_round_eth_tick(self) -> None:
        """ETH tick=0.01: 3,500.456 rounds down to 3,500.45."""
        result = round_to_valid_price(3_500.456, tick_size=0.01)
        assert result == pytest.approx(3_500.45)

    def test_round_small_tick(self) -> None:
        """Meme-coin tick=0.00001: 0.12345678 rounds down to 0.12345."""
        result = round_to_valid_price(0.12345678, tick_size=0.00001)
        assert result == pytest.approx(0.12345)

    def test_zero_price(self) -> None:
        """Zero price stays zero regardless of tick size."""
        result = round_to_valid_price(0.0, tick_size=0.1)
        assert result == pytest.approx(0.0)

    def test_very_large_price(self) -> None:
        """Large prices (>$1M) round correctly without FP overflow.

        Some assets trade at very high notional; rounding must be stable.
        """
        result = round_to_valid_price(1_234_567.89, tick_size=0.5)
        assert result == pytest.approx(1_234_567.5)


# ===================================================================
# round_to_valid_order_size
# ===================================================================


class TestRoundToValidOrderSize:
    """Contract tests for order size rounding to a market's lot_size.

    Order sizes must be multiples of lot_size and >= min_size.
    Violating either constraint causes on-chain rejection.
    """

    def test_round_to_lot_size(self) -> None:
        """0.00015 with lot=0.0001, min=0.0001 → 0.0001 (truncated).

        Sizes always round down to avoid exceeding available balance.
        """
        result = round_to_valid_order_size(0.00015, lot_size=0.0001, min_size=0.0001)
        assert result == pytest.approx(0.0001)

    def test_enforce_min_size(self) -> None:
        """Size below min_size returns 0.0 (order should not be placed).

        A bot receiving 0.0 must skip the order rather than submit it.
        """
        result = round_to_valid_order_size(0.00005, lot_size=0.0001, min_size=0.0001)
        assert result == pytest.approx(0.0)

    def test_exact_min_size_is_kept(self) -> None:
        """Size exactly equal to min_size is preserved."""
        result = round_to_valid_order_size(0.0001, lot_size=0.0001, min_size=0.0001)
        assert result == pytest.approx(0.0001)

    def test_large_size_rounded(self) -> None:
        """1.2345 with lot=0.001, min=0.001 → 1.234."""
        result = round_to_valid_order_size(1.2345, lot_size=0.001, min_size=0.001)
        assert result == pytest.approx(1.234)

    def test_zero_size(self) -> None:
        """Zero size stays zero."""
        result = round_to_valid_order_size(0.0, lot_size=0.0001, min_size=0.0001)
        assert result == pytest.approx(0.0)

    def test_very_small_value_below_lot(self) -> None:
        """1e-10 with lot=0.0001 rounds to 0.0 (below min_size)."""
        result = round_to_valid_order_size(1e-10, lot_size=0.0001, min_size=0.0001)
        assert result == pytest.approx(0.0)


# ===================================================================
# amount_to_chain_units / chain_units_to_amount
# ===================================================================


class TestChainUnitConversion:
    """Contract tests for human ↔ chain-unit conversion.

    On-chain, amounts are unsigned integers scaled by 10^decimals.
    Incorrect conversion leads to orders that are too large/small
    by orders of magnitude.
    """

    def test_amount_to_chain_units_basic(self) -> None:
        """1.5 with 9 decimals → 1_500_000_000 chain units.

        Standard BTC sz_decimals = 9.
        """
        result = amount_to_chain_units(1.5, decimals=9)
        assert result == 1_500_000_000

    def test_chain_units_to_amount_basic(self) -> None:
        """1_500_000_000 chain units with 9 decimals → 1.5.

        Inverse of amount_to_chain_units.
        """
        result = chain_units_to_amount(1_500_000_000, decimals=9)
        assert result == pytest.approx(1.5)

    def test_roundtrip_amount(self) -> None:
        """amount → chain → amount roundtrip preserves value.

        Critical invariant: conversion must not lose precision within
        the supported decimal range.
        """
        original = 0.123456789
        chain = amount_to_chain_units(original, decimals=9)
        restored = chain_units_to_amount(chain, decimals=9)
        assert restored == pytest.approx(original)

    def test_zero_amount(self) -> None:
        """0.0 converts to 0 chain units and back."""
        assert amount_to_chain_units(0.0, decimals=9) == 0
        assert chain_units_to_amount(0, decimals=9) == pytest.approx(0.0)

    def test_very_large_amount(self) -> None:
        """100,000 BTC (extreme) with 9 decimals.

        Must not overflow standard 64-bit integers.
        """
        result = amount_to_chain_units(100_000.0, decimals=9)
        assert result == 100_000_000_000_000
        assert result < 2**64

    def test_six_decimals(self) -> None:
        """USDC-like 6 decimals: 1000.50 → 1_000_500_000."""
        result = amount_to_chain_units(1000.50, decimals=6)
        assert result == 1_000_500_000


# ===================================================================
# to_chain_price / from_chain_price
# ===================================================================


class TestChainPriceConversion:
    """Contract tests for price ↔ chain-price conversion.

    Prices on-chain use px_decimals scaling.  These convenience
    wrappers are thin shims over amount_to_chain_units but are
    tested separately for clarity in order-building code.
    """

    def test_to_chain_price_btc(self) -> None:
        """$95,000 with px_decimals=9 → 95_000_000_000_000.

        Matches the on-chain price representation.
        """
        result = to_chain_price(95_000.0, px_decimals=9)
        assert result == 95_000_000_000_000

    def test_from_chain_price_btc(self) -> None:
        """95_000_000_000_000 with px_decimals=9 → $95,000.0."""
        result = from_chain_price(95_000_000_000_000, px_decimals=9)
        assert result == pytest.approx(95_000.0)

    def test_price_roundtrip(self) -> None:
        """price → chain → price roundtrip."""
        original = 3_456.789
        chain = to_chain_price(original, px_decimals=9)
        restored = from_chain_price(chain, px_decimals=9)
        assert restored == pytest.approx(original)

    def test_zero_price(self) -> None:
        """$0 converts cleanly."""
        assert to_chain_price(0.0, px_decimals=9) == 0
        assert from_chain_price(0, px_decimals=9) == pytest.approx(0.0)

    def test_very_small_price(self) -> None:
        """Fractional penny price: $0.00001 with 9 decimals.

        Relevant for meme-coin perps.
        """
        result = to_chain_price(0.00001, px_decimals=9)
        assert result == 10_000
        restored = from_chain_price(result, px_decimals=9)
        assert restored == pytest.approx(0.00001)
