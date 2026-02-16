package models

// PerpMarketConfig holds the configuration of a perpetual market.
type PerpMarketConfig struct {
	MarketAddr       string  `json:"market_addr"`
	MarketName       string  `json:"market_name"`
	SzDecimals       int32   `json:"sz_decimals"`
	PxDecimals       int32   `json:"px_decimals"`
	MaxLeverage      float64 `json:"max_leverage"`
	MinSize          float64 `json:"min_size"`
	LotSize          float64 `json:"lot_size"`
	TickSize         float64 `json:"tick_size"`
	MaxOpenInterest  float64 `json:"max_open_interest"`
	MarginCallFeePct float64 `json:"margin_call_fee_pct"`
	TakerInNextBlock bool    `json:"taker_in_next_block"`
}

// MarketDepth represents the order book depth.
type MarketDepth struct {
	Market string        `json:"market"`
	Bids   []MarketOrder `json:"bids"`
	Asks   []MarketOrder `json:"asks"`
	UnixMs int64         `json:"unix_ms"`
}

// MarketOrder represents a single order in the book.
type MarketOrder struct {
	Price float64 `json:"price"`
	Size  float64 `json:"size"`
}

// MarketPrice represents price data for a market.
type MarketPrice struct {
	Market            string  `json:"market"`
	MarkPx            float64 `json:"mark_px"`
	MidPx             float64 `json:"mid_px"`
	OraclePx          float64 `json:"oracle_px"`
	FundingRateBps    float64 `json:"funding_rate_bps"`
	IsFundingPositive bool    `json:"is_funding_positive"`
	OpenInterest      float64 `json:"open_interest"`
	TransactionUnixMs int64   `json:"transaction_unix_ms"`
}

// MarketContext provides additional market metadata.
type MarketContext struct {
	Market           string  `json:"market"`
	Volume24h        float64 `json:"volume_24h"`
	OpenInterest     float64 `json:"open_interest"`
	PreviousDayPrice float64 `json:"previous_day_price"`
	PriceChangePct   float64 `json:"price_change_pct_24h"`
}

// Candlestick represents OHLCV data.
type Candlestick struct {
	CloseTimestamp int64   `json:"T"`
	Close          float64 `json:"c"`
	High           float64 `json:"h"`
	Interval       string  `json:"i"`
	Low            float64 `json:"l"`
	Open           float64 `json:"o"`
	OpenTimestamp   int64   `json:"t"`
	Volume         float64 `json:"v"`
}

// MarketTrade represents a trade on a market.
type MarketTrade struct {
	Market string  `json:"market"`
	Price  float64 `json:"price"`
	Size   float64 `json:"size"`
	IsBuy  bool    `json:"is_buy"`
	UnixMs int64   `json:"unix_ms"`
}
