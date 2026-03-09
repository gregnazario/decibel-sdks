"""Market-related data models."""

from pydantic import BaseModel, Field


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
