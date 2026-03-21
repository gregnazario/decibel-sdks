"""TDD tests for market data models.

These tests define the API contract for every market-related Pydantic model.
They will fail until the corresponding computed properties and methods are
implemented on the models.  Each test uses realistic BTC / ETH price data so
the assertions double as sanity-checks for trading bot consumers.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from decibel.models.market import (
    Candlestick,
    MarketContext,
    MarketDepth,
    MarketOrder,
    MarketPrice,
    MarketTrade,
    PerpMarketConfig,
)

# ===================================================================
# PerpMarketConfig
# ===================================================================


class TestPerpMarketConfig:
    """Contract tests for the perpetual market configuration model."""

    def test_perp_market_config_roundtrip(self, btc_perp_config: PerpMarketConfig) -> None:
        """Serialise → deserialise must preserve every field.

        Trading bots cache market configs; a lossy roundtrip would silently
        corrupt order-sizing logic.
        """
        data = btc_perp_config.model_dump()
        restored = PerpMarketConfig(**data)
        assert restored == btc_perp_config

    def test_perp_market_config_json_roundtrip(self, btc_perp_config: PerpMarketConfig) -> None:
        """JSON export → re-import roundtrip.

        Ensures the model survives a JSON wire format used by the REST API.
        """
        json_str = btc_perp_config.model_dump_json()
        restored = PerpMarketConfig.model_validate_json(json_str)
        assert restored == btc_perp_config

    def test_perp_market_config_json_schema_export(self) -> None:
        """JSON Schema generation must not raise.

        SDK consumers may use the schema for codegen or documentation.
        """
        schema = PerpMarketConfig.model_json_schema()
        assert "properties" in schema
        assert "market_name" in schema["properties"]

    def test_perp_market_config_min_size_decimal(self, btc_perp_config: PerpMarketConfig) -> None:
        """min_size_decimal returns min_size as a Decimal for precise arithmetic.

        Avoids floating-point drift when computing minimum notional values.
        """
        from decimal import Decimal

        result = btc_perp_config.min_size_decimal
        assert result == Decimal("0.0001")

    def test_perp_market_config_lot_size_decimal(self, btc_perp_config: PerpMarketConfig) -> None:
        """lot_size_decimal returns lot_size as a Decimal.

        Order sizes must be multiples of lot_size; Decimal avoids FP errors.
        """
        from decimal import Decimal

        result = btc_perp_config.lot_size_decimal
        assert result == Decimal("0.0001")

    def test_perp_market_config_tick_size_decimal(self, btc_perp_config: PerpMarketConfig) -> None:
        """tick_size_decimal returns tick_size as a Decimal.

        Limit-order prices must be multiples of tick_size.
        """
        from decimal import Decimal

        result = btc_perp_config.tick_size_decimal
        assert result == Decimal("0.1")

    def test_perp_market_config_mm_fraction(self, btc_perp_config: PerpMarketConfig) -> None:
        """mm_fraction returns margin_call_fee_pct as a ratio.

        Used by risk engines to compute the margin-call fee buffer.
        """
        assert btc_perp_config.mm_fraction == pytest.approx(0.005)

    def test_perp_market_config_frozen(self) -> None:
        """PerpMarketConfig should be immutable once created.

        Market configs are shared across threads; mutation is a bug.
        """
        config = PerpMarketConfig(
            market_addr="0x1",
            market_name="BTC-USD",
            sz_decimals=4,
            px_decimals=1,
            max_leverage=50.0,
            min_size=0.0001,
            lot_size=0.0001,
            tick_size=0.1,
            max_open_interest=500.0,
            margin_call_fee_pct=0.005,
            taker_in_next_block=True,
        )
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            config.market_name = "ETH-USD"  # type: ignore[misc]


# ===================================================================
# MarketPrice
# ===================================================================


class TestMarketPrice:
    """Contract tests for the market price snapshot model."""

    def test_market_price_roundtrip(self, btc_market_price: MarketPrice) -> None:
        """Serialise → deserialise must preserve every field."""
        data = btc_market_price.model_dump()
        restored = MarketPrice(**data)
        assert restored == btc_market_price

    def test_market_price_json_roundtrip(self, btc_market_price: MarketPrice) -> None:
        """JSON roundtrip for wire-format fidelity."""
        json_str = btc_market_price.model_dump_json()
        restored = MarketPrice.model_validate_json(json_str)
        assert restored == btc_market_price

    def test_market_price_funding_rate_hourly(self, btc_market_price: MarketPrice) -> None:
        """funding_rate_hourly converts bps to a per-hour decimal rate.

        Bots use the hourly rate to decide whether to collect funding.
        0.75 bps = 0.75 / 10_000 = 0.000075 per funding interval.
        """
        expected = 0.75 / 10_000
        assert btc_market_price.funding_rate_hourly == pytest.approx(expected)

    def test_market_price_funding_direction_positive(self, btc_market_price: MarketPrice) -> None:
        """funding_direction returns 'long_pays' when funding is positive.

        Positive funding means longs pay shorts.
        """
        assert btc_market_price.funding_direction == "long_pays"

    def test_market_price_funding_direction_negative(self, eth_market_price: MarketPrice) -> None:
        """funding_direction returns 'short_pays' when funding is negative."""
        assert eth_market_price.funding_direction == "short_pays"

    def test_market_price_str(self, btc_market_price: MarketPrice) -> None:
        """__str__ should produce a human-readable summary for logging.

        Operators tail bot logs; a useful repr saves debugging time.
        """
        s = str(btc_market_price)
        assert "BTC-USD" in s
        assert "95000" in s


# ===================================================================
# MarketContext
# ===================================================================


class TestMarketContext:
    """Contract tests for the 24h market context model."""

    def test_market_context_roundtrip(self, btc_market_context: MarketContext) -> None:
        """Serialise → deserialise preserves all fields."""
        data = btc_market_context.model_dump()
        restored = MarketContext(**data)
        assert restored == btc_market_context

    def test_market_context_json_roundtrip(self, btc_market_context: MarketContext) -> None:
        """JSON roundtrip."""
        json_str = btc_market_context.model_dump_json()
        restored = MarketContext.model_validate_json(json_str)
        assert restored == btc_market_context


# ===================================================================
# MarketDepth (order book)
# ===================================================================


class TestMarketDepth:
    """Contract tests for the order-book depth model.

    All computed helpers must handle both populated and empty books.
    """

    def test_market_depth_roundtrip(self, btc_market_depth: MarketDepth) -> None:
        """Serialise → deserialise preserves levels and metadata."""
        data = btc_market_depth.model_dump()
        restored = MarketDepth(**data)
        assert restored == btc_market_depth

    def test_market_depth_json_roundtrip(self, btc_market_depth: MarketDepth) -> None:
        """JSON roundtrip."""
        json_str = btc_market_depth.model_dump_json()
        restored = MarketDepth.model_validate_json(json_str)
        assert restored == btc_market_depth

    def test_market_depth_best_bid(self, btc_market_depth: MarketDepth) -> None:
        """best_bid returns the highest bid price.

        Bids are assumed sorted descending; best_bid is bids[0].price.
        """
        assert btc_market_depth.best_bid == pytest.approx(94_999.0)

    def test_market_depth_best_ask(self, btc_market_depth: MarketDepth) -> None:
        """best_ask returns the lowest ask price.

        Asks are assumed sorted ascending; best_ask is asks[0].price.
        """
        assert btc_market_depth.best_ask == pytest.approx(95_001.0)

    def test_market_depth_spread(self, btc_market_depth: MarketDepth) -> None:
        """spread returns best_ask - best_bid.

        The spread is a core liquidity metric for market-making bots.
        """
        assert btc_market_depth.spread == pytest.approx(2.0)

    def test_market_depth_mid_price(self, btc_market_depth: MarketDepth) -> None:
        """mid_price returns (best_bid + best_ask) / 2.

        Used as fair-value reference by many trading strategies.
        """
        assert btc_market_depth.mid_price == pytest.approx(95_000.0)

    def test_market_depth_bid_depth_at(self, btc_market_depth: MarketDepth) -> None:
        """bid_depth_at(pct) returns cumulative bid size within pct of best bid.

        Measures liquidity depth; critical for slippage estimation.
        """
        depth = btc_market_depth.bid_depth_at(0.01)
        assert depth >= 1.5

    def test_market_depth_ask_depth_at(self, btc_market_depth: MarketDepth) -> None:
        """ask_depth_at(pct) returns cumulative ask size within pct of best ask.

        Mirrors bid_depth_at for the ask side.
        """
        depth = btc_market_depth.ask_depth_at(0.01)
        assert depth >= 1.0

    def test_market_depth_imbalance(self, btc_market_depth: MarketDepth) -> None:
        """imbalance returns (bid_vol - ask_vol) / (bid_vol + ask_vol).

        A positive imbalance signals buying pressure; used by signal models.
        """
        imb = btc_market_depth.imbalance
        assert -1.0 <= imb <= 1.0

    def test_market_depth_empty_best_bid(self, empty_market_depth: MarketDepth) -> None:
        """best_bid on an empty book returns None (no bids)."""
        assert empty_market_depth.best_bid is None

    def test_market_depth_empty_best_ask(self, empty_market_depth: MarketDepth) -> None:
        """best_ask on an empty book returns None (no asks)."""
        assert empty_market_depth.best_ask is None

    def test_market_depth_empty_spread(self, empty_market_depth: MarketDepth) -> None:
        """spread on an empty book returns None."""
        assert empty_market_depth.spread is None

    def test_market_depth_empty_mid_price(self, empty_market_depth: MarketDepth) -> None:
        """mid_price on an empty book returns None."""
        assert empty_market_depth.mid_price is None

    def test_market_depth_empty_imbalance(self, empty_market_depth: MarketDepth) -> None:
        """imbalance on an empty book returns 0.0 (no pressure)."""
        assert empty_market_depth.imbalance == pytest.approx(0.0)


# ===================================================================
# PriceLevel (alias for MarketOrder)
# ===================================================================


class TestPriceLevel:
    """Contract tests for the PriceLevel / MarketOrder model."""

    def test_price_level_roundtrip(self) -> None:
        """Basic roundtrip of a single price level."""
        level = MarketOrder(price=95_000.0, size=1.25)
        data = level.model_dump()
        restored = MarketOrder(**data)
        assert restored.price == pytest.approx(95_000.0)
        assert restored.size == pytest.approx(1.25)


# ===================================================================
# MarketTrade
# ===================================================================


class TestMarketTrade:
    """Contract tests for the single-trade model."""

    def test_market_trade_roundtrip(self, btc_market_trade: MarketTrade) -> None:
        """Serialise → deserialise preserves all fields."""
        data = btc_market_trade.model_dump()
        restored = MarketTrade(**data)
        assert restored == btc_market_trade

    def test_market_trade_json_roundtrip(self, btc_market_trade: MarketTrade) -> None:
        """JSON roundtrip."""
        json_str = btc_market_trade.model_dump_json()
        restored = MarketTrade.model_validate_json(json_str)
        assert restored == btc_market_trade


# ===================================================================
# Candlestick
# ===================================================================


class TestCandlestick:
    """Contract tests for the OHLCV candlestick model.

    The wire format uses single-character keys (t, T, o, h, l, c, v, i)
    to minimise WebSocket bandwidth.
    """

    def test_candlestick_roundtrip(self, btc_candlestick: Candlestick) -> None:
        """Serialise → deserialise preserves all fields."""
        data = btc_candlestick.model_dump()
        restored = Candlestick(**data)
        assert restored == btc_candlestick

    def test_candlestick_json_roundtrip(self, btc_candlestick: Candlestick) -> None:
        """JSON roundtrip."""
        json_str = btc_candlestick.model_dump_json()
        restored = Candlestick.model_validate_json(json_str)
        assert restored == btc_candlestick

    def test_candlestick_wire_aliases(self) -> None:
        """Model accepts single-char wire keys matching the WebSocket payload.

        The API sends {"t": ..., "T": ..., "o": ..., ...} and the model
        must parse these without requiring long-form names.
        """
        wire = {
            "t": 1_700_000_000_000,
            "T": 1_700_000_060_000,
            "o": 94_950.0,
            "h": 95_100.0,
            "l": 94_900.0,
            "c": 95_050.0,
            "v": 12.5,
            "i": "1m",
        }
        candle = Candlestick(**wire)
        assert candle.o == pytest.approx(94_950.0)
        assert candle.c == pytest.approx(95_050.0)
        assert candle.h == pytest.approx(95_100.0)
        assert candle.l == pytest.approx(94_900.0)
        assert candle.v == pytest.approx(12.5)
        assert candle.i == "1m"
        assert candle.t == 1_700_000_000_000
        assert candle.T == 1_700_000_060_000

    def test_candlestick_body_pct(self, btc_candlestick: Candlestick) -> None:
        """body_pct returns |close - open| / open as a percentage.

        Useful for filtering out doji candles (body_pct ≈ 0).
        """
        expected = abs(95_050.0 - 94_950.0) / 94_950.0
        assert btc_candlestick.body_pct == pytest.approx(expected, rel=1e-6)

    def test_candlestick_range_pct(self, btc_candlestick: Candlestick) -> None:
        """range_pct returns (high - low) / low as a percentage.

        Measures volatility of the candle period.
        """
        expected = (95_100.0 - 94_900.0) / 94_900.0
        assert btc_candlestick.range_pct == pytest.approx(expected, rel=1e-6)

    def test_candlestick_is_bullish(self, btc_candlestick: Candlestick) -> None:
        """is_bullish returns True when close >= open."""
        assert btc_candlestick.is_bullish is True

    def test_candlestick_is_bearish(self) -> None:
        """is_bullish returns False when close < open."""
        candle = Candlestick(
            t=1_700_000_000_000,
            T=1_700_000_060_000,
            o=95_050.0,
            h=95_100.0,
            l=94_900.0,
            c=94_950.0,
            v=10.0,
            i="1m",
        )
        assert candle.is_bullish is False
