package models

import (
	"encoding/json"
	"testing"
)

func TestPerpMarketConfig_JSON(t *testing.T) {
	data := `{
		"market_addr": "0xabc",
		"market_name": "BTC-USD",
		"sz_decimals": 8,
		"px_decimals": 2,
		"max_leverage": 50.0,
		"min_size": 0.001,
		"lot_size": 0.001,
		"tick_size": 0.1,
		"max_open_interest": 1000000.0,
		"margin_call_fee_pct": 0.5,
		"taker_in_next_block": false
	}`
	var config PerpMarketConfig
	if err := json.Unmarshal([]byte(data), &config); err != nil {
		t.Fatal(err)
	}
	if config.MarketName != "BTC-USD" {
		t.Errorf("expected BTC-USD, got %s", config.MarketName)
	}
	if config.SzDecimals != 8 {
		t.Errorf("expected 8 sz_decimals, got %d", config.SzDecimals)
	}
	if config.TakerInNextBlock {
		t.Error("expected taker_in_next_block=false")
	}
}

func TestMarketDepth_JSON(t *testing.T) {
	data := `{
		"market": "BTC-USD",
		"bids": [{"price": 45100.0, "size": 2.5}, {"price": 45050.0, "size": 1.0}],
		"asks": [{"price": 45150.0, "size": 3.0}],
		"unix_ms": 1708000000000
	}`
	var depth MarketDepth
	if err := json.Unmarshal([]byte(data), &depth); err != nil {
		t.Fatal(err)
	}
	if depth.Market != "BTC-USD" {
		t.Errorf("expected BTC-USD, got %s", depth.Market)
	}
	if len(depth.Bids) != 2 {
		t.Errorf("expected 2 bids, got %d", len(depth.Bids))
	}
	if len(depth.Asks) != 1 {
		t.Errorf("expected 1 ask, got %d", len(depth.Asks))
	}
	if depth.Bids[0].Price != 45100.0 {
		t.Errorf("expected bid price 45100, got %f", depth.Bids[0].Price)
	}
	if depth.UnixMs != 1708000000000 {
		t.Errorf("expected unix_ms 1708000000000, got %d", depth.UnixMs)
	}
}

func TestMarketPrice_JSON(t *testing.T) {
	data := `{
		"market": "ETH-USD",
		"mark_px": 3000.5,
		"mid_px": 3000.0,
		"oracle_px": 3001.0,
		"funding_rate_bps": 0.0123,
		"is_funding_positive": true,
		"open_interest": 500000.0,
		"transaction_unix_ms": 1708000000000
	}`
	var price MarketPrice
	if err := json.Unmarshal([]byte(data), &price); err != nil {
		t.Fatal(err)
	}
	if price.Market != "ETH-USD" {
		t.Errorf("expected ETH-USD, got %s", price.Market)
	}
	if !price.IsFundingPositive {
		t.Error("expected is_funding_positive=true")
	}
	if price.MarkPx != 3000.5 {
		t.Errorf("expected mark_px 3000.5, got %f", price.MarkPx)
	}
}

func TestMarketContext_JSON(t *testing.T) {
	data := `{
		"market": "SOL-USD",
		"volume_24h": 5000000.0,
		"open_interest": 200000.0,
		"previous_day_price": 100.0,
		"price_change_pct_24h": 5.5
	}`
	var ctx MarketContext
	if err := json.Unmarshal([]byte(data), &ctx); err != nil {
		t.Fatal(err)
	}
	if ctx.Market != "SOL-USD" {
		t.Errorf("expected SOL-USD, got %s", ctx.Market)
	}
	if ctx.Volume24h != 5000000.0 {
		t.Errorf("expected volume 5000000, got %f", ctx.Volume24h)
	}
}

func TestCandlestick_JSON(t *testing.T) {
	data := `{
		"T": 1708000060000,
		"c": 45200.0,
		"h": 45300.0,
		"i": "1m",
		"l": 45100.0,
		"o": 45150.0,
		"t": 1708000000000,
		"v": 125.5
	}`
	var candle Candlestick
	if err := json.Unmarshal([]byte(data), &candle); err != nil {
		t.Fatal(err)
	}
	if candle.Open != 45150.0 {
		t.Errorf("expected open 45150, got %f", candle.Open)
	}
	if candle.High != 45300.0 {
		t.Errorf("expected high 45300, got %f", candle.High)
	}
	if candle.Volume != 125.5 {
		t.Errorf("expected volume 125.5, got %f", candle.Volume)
	}
	if candle.Interval != "1m" {
		t.Errorf("expected interval 1m, got %s", candle.Interval)
	}
}

func TestMarketTrade_JSON(t *testing.T) {
	data := `{
		"market": "BTC-USD",
		"price": 45123.45,
		"size": 0.5,
		"is_buy": true,
		"unix_ms": 1708000000000
	}`
	var trade MarketTrade
	if err := json.Unmarshal([]byte(data), &trade); err != nil {
		t.Fatal(err)
	}
	if trade.Market != "BTC-USD" {
		t.Errorf("expected BTC-USD, got %s", trade.Market)
	}
	if !trade.IsBuy {
		t.Error("expected is_buy=true")
	}
}

func TestMarketDepth_EmptyBook(t *testing.T) {
	data := `{"market": "DOGE-USD", "bids": [], "asks": [], "unix_ms": 0}`
	var depth MarketDepth
	if err := json.Unmarshal([]byte(data), &depth); err != nil {
		t.Fatal(err)
	}
	if len(depth.Bids) != 0 {
		t.Errorf("expected 0 bids, got %d", len(depth.Bids))
	}
	if len(depth.Asks) != 0 {
		t.Errorf("expected 0 asks, got %d", len(depth.Asks))
	}
}
