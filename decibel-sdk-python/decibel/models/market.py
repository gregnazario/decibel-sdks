"""Market-related data models."""

from pydantic import BaseModel, ConfigDict, Field


class PerpMarketConfig(BaseModel):
    """Configuration of a perpetual market.

    Attributes:
        market_addr: Market object address
        market_name: Human-readable market name (e.g., "BTC-USD")
        sz_decimals: Size decimal precision
        px_decimals: Price decimal precision
        max_leverage: Maximum allowed leverage
        min_size: Minimum order size
        lot_size: Lot size (order size granularity)
        tick_size: Tick size (price granularity)
        max_open_interest: Maximum open interest
        margin_call_fee_pct: Margin call fee percentage
        taker_in_next_block: Whether taker fills in next block
    """

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    market_addr: str
    market_name: str
    sz_decimals: int = Field(alias="sz_decimals")
    px_decimals: int = Field(alias="px_decimals")
    max_leverage: float
    min_size: float
    lot_size: float
    tick_size: float
    max_open_interest: float
    margin_call_fee_pct: float
    taker_in_next_block: bool

    @property
    def min_size_decimal(self):
        """Minimum order size as a Decimal for precise arithmetic."""
        from decimal import Decimal
        return Decimal(str(self.min_size))

    @property
    def lot_size_decimal(self):
        """Lot size as a Decimal for precise arithmetic."""
        from decimal import Decimal
        return Decimal(str(self.lot_size))

    @property
    def tick_size_decimal(self):
        """Tick size as a Decimal for precise arithmetic."""
        from decimal import Decimal
        return Decimal(str(self.tick_size))

    @property
    def mm_fraction(self) -> float:
        """Margin call fee as a fraction (margin_call_fee_pct / 100)."""
        return self.margin_call_fee_pct / 100.0


class MarketOrder(BaseModel):
    """Single order in the order book.

    Attributes:
        price: Price level
        size: Size at this level
    """

    price: float
    size: float


class MarketDepth(BaseModel):
    """Order book depth.

    Attributes:
        market: Market name
        bids: Bid orders (price descending)
        asks: Ask orders (price ascending)
        unix_ms: Timestamp in milliseconds
    """

    market: str
    bids: list[MarketOrder]
    asks: list[MarketOrder]
    unix_ms: int

    @property
    def best_bid(self) -> float | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> float | None:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> float | None:
        b, a = self.best_bid, self.best_ask
        return (a - b) if b is not None and a is not None else None

    @property
    def mid_price(self) -> float | None:
        b, a = self.best_bid, self.best_ask
        return (a + b) / 2 if b is not None and a is not None else None

    def bid_depth_at(self, percent_from_mid: float) -> float:
        """Total bid size within percent_from_mid% of mid price."""
        mid = self.mid_price
        if mid is None:
            return 0.0
        threshold = mid * (1 - percent_from_mid / 100)
        return sum(level.size for level in self.bids if level.price >= threshold)

    def ask_depth_at(self, percent_from_mid: float) -> float:
        """Total ask size within percent_from_mid% of mid price."""
        mid = self.mid_price
        if mid is None:
            return 0.0
        threshold = mid * (1 + percent_from_mid / 100)
        return sum(level.size for level in self.asks if level.price <= threshold)

    @property
    def imbalance(self) -> float:
        """Bid/ask imbalance: (bid_vol - ask_vol) / (bid_vol + ask_vol). Range [-1, 1]. Returns 0.0 if empty."""
        bid_vol = sum(level.size for level in self.bids)
        ask_vol = sum(level.size for level in self.asks)
        total = bid_vol + ask_vol
        return (bid_vol - ask_vol) / total if total > 0 else 0.0


class MarketPrice(BaseModel):
    """Price data for a market.

    Attributes:
        market: Market name
        mark_px: Mark price
        mid_px: Mid price
        oracle_px: Oracle price
        funding_rate_bps: Funding rate in basis points
        is_funding_positive: Whether funding is positive
        open_interest: Open interest
        transaction_unix_ms: Transaction timestamp in milliseconds
    """

    market: str
    mark_px: float
    mid_px: float
    oracle_px: float
    funding_rate_bps: float
    is_funding_positive: bool
    open_interest: float
    transaction_unix_ms: int

    @property
    def funding_rate_hourly(self) -> float:
        """Funding rate as a per-hour decimal (bps / 10000)."""
        return self.funding_rate_bps / 10_000

    @property
    def funding_direction(self) -> str:
        """'long_pays' if longs pay shorts, 'short_pays' otherwise."""
        return "long_pays" if self.is_funding_positive else "short_pays"

    def __str__(self) -> str:
        return (
            f"MarketPrice({self.market}: mark={self.mark_px}, "
            f"oracle={self.oracle_px}, funding={self.funding_rate_bps}bps)"
        )


class MarketContext(BaseModel):
    """Additional market metadata.

    Attributes:
        market: Market name
        volume_24h: 24-hour volume
        open_interest: Open interest
        previous_day_price: Previous day closing price
        price_change_pct_24h: 24-hour price change percentage
    """

    market: str
    volume_24h: float
    open_interest: float
    previous_day_price: float
    price_change_pct_24h: float


class Candlestick(BaseModel):
    """OHLCV candlestick data.

    Attributes:
        T: Close timestamp
        c: Close price
        h: High price
        i: Interval
        l: Low price
        o: Open price
        t: Open timestamp
        v: Volume
    """

    T: int  # Close timestamp
    c: float  # Close price
    h: float  # High price
    i: str  # Interval
    l: float  # Low price
    o: float  # Open price
    t: int  # Open timestamp
    v: float  # Volume

    @property
    def is_bullish(self) -> bool:
        return self.c >= self.o

    @property
    def body_pct(self) -> float:
        """Body size as fraction of open: abs(close - open) / open."""
        return abs(self.c - self.o) / self.o if self.o != 0 else 0.0

    @property
    def range_pct(self) -> float:
        """High-low range as fraction of low: (high - low) / low."""
        return (self.h - self.l) / self.l if self.l != 0 else 0.0


class MarketTrade(BaseModel):
    """Trade on a market.

    Attributes:
        market: Market name
        price: Trade price
        size: Trade size
        is_buy: Whether the taker was a buyer
        unix_ms: Trade timestamp in milliseconds
    """

    market: str
    price: float
    size: float
    is_buy: bool
    unix_ms: int
