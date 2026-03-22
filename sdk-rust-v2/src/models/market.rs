use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// PerpMarketConfig
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct PerpMarketConfig {
    pub market_addr: String,
    pub market_name: String,
    pub sz_decimals: i32,
    pub px_decimals: i32,
    pub max_leverage: f64,
    pub min_size: f64,
    pub lot_size: f64,
    pub tick_size: f64,
    pub max_open_interest: f64,
    pub margin_call_fee_pct: f64,
    pub taker_in_next_block: bool,
}

impl PerpMarketConfig {
    /// Minimum order size in human-readable decimal units.
    pub fn min_size_decimal(&self) -> f64 {
        self.min_size / 10_f64.powi(self.sz_decimals)
    }

    /// Lot size (size granularity) in human-readable decimal units.
    pub fn lot_size_decimal(&self) -> f64 {
        self.lot_size / 10_f64.powi(self.sz_decimals)
    }

    /// Tick size (price granularity) in human-readable decimal units.
    pub fn tick_size_decimal(&self) -> f64 {
        self.tick_size / 10_f64.powi(self.px_decimals)
    }

    /// Maintenance margin fraction: 1 / (max_leverage * 2).
    pub fn mm_fraction(&self) -> f64 {
        1.0 / (self.max_leverage * 2.0)
    }
}

impl std::fmt::Display for PerpMarketConfig {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}({}x, min={}, tick={})",
            self.market_name,
            self.max_leverage,
            self.min_size_decimal(),
            self.tick_size_decimal()
        )
    }
}

// ---------------------------------------------------------------------------
// MarketOrder (PriceLevel)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct MarketOrder {
    pub price: f64,
    pub size: f64,
}

// ---------------------------------------------------------------------------
// MarketDepth
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct MarketDepth {
    pub market: String,
    pub bids: Vec<MarketOrder>,
    pub asks: Vec<MarketOrder>,
    pub unix_ms: i64,
}

impl MarketDepth {
    pub fn best_bid(&self) -> Option<f64> {
        self.bids.first().map(|l| l.price)
    }

    pub fn best_ask(&self) -> Option<f64> {
        self.asks.first().map(|l| l.price)
    }

    pub fn spread(&self) -> Option<f64> {
        match (self.best_bid(), self.best_ask()) {
            (Some(b), Some(a)) => Some(a - b),
            _ => None,
        }
    }

    pub fn mid_price(&self) -> Option<f64> {
        match (self.best_bid(), self.best_ask()) {
            (Some(b), Some(a)) => Some((a + b) / 2.0),
            _ => None,
        }
    }

    /// Bid/ask volume imbalance in [-1, 1].
    /// Positive = more bid volume (buy pressure).
    pub fn imbalance(&self) -> Option<f64> {
        let bid_vol: f64 = self.bids.iter().map(|l| l.size).sum();
        let ask_vol: f64 = self.asks.iter().map(|l| l.size).sum();
        let total = bid_vol + ask_vol;
        if total > 0.0 {
            Some((bid_vol - ask_vol) / total)
        } else {
            None
        }
    }

    /// Total bid size within `pct`% of mid price.
    pub fn bid_depth_at(&self, pct: f64) -> f64 {
        let mid = match self.mid_price() {
            Some(m) => m,
            None => return 0.0,
        };
        let threshold = mid * (1.0 - pct / 100.0);
        self.bids
            .iter()
            .filter(|l| l.price >= threshold)
            .map(|l| l.size)
            .sum()
    }

    /// Total ask size within `pct`% of mid price.
    pub fn ask_depth_at(&self, pct: f64) -> f64 {
        let mid = match self.mid_price() {
            Some(m) => m,
            None => return 0.0,
        };
        let threshold = mid * (1.0 + pct / 100.0);
        self.asks
            .iter()
            .filter(|l| l.price <= threshold)
            .map(|l| l.size)
            .sum()
    }
}

impl std::fmt::Display for MarketDepth {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "MarketDepth({}, bids={}, asks={}, spread={:?})",
            self.market,
            self.bids.len(),
            self.asks.len(),
            self.spread()
        )
    }
}

// ---------------------------------------------------------------------------
// MarketPrice
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct MarketPrice {
    pub market: String,
    pub mark_px: f64,
    pub mid_px: f64,
    pub oracle_px: f64,
    pub funding_rate_bps: f64,
    pub is_funding_positive: bool,
    pub open_interest: f64,
    pub transaction_unix_ms: i64,
}

impl MarketPrice {
    /// Annualized funding rate expressed as hourly percentage.
    pub fn funding_rate_hourly(&self) -> f64 {
        self.funding_rate_bps / 10_000.0 * 365.0 * 24.0
    }

    /// Human-readable funding direction.
    pub fn funding_direction(&self) -> &str {
        if self.is_funding_positive {
            "longs_pay"
        } else {
            "shorts_pay"
        }
    }
}

impl std::fmt::Display for MarketPrice {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}(mark={}, mid={}, oracle={}, funding={}bps {})",
            self.market,
            self.mark_px,
            self.mid_px,
            self.oracle_px,
            self.funding_rate_bps,
            self.funding_direction()
        )
    }
}

// ---------------------------------------------------------------------------
// MarketContext
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct MarketContext {
    pub market: String,
    pub volume_24h: f64,
    pub open_interest: f64,
    pub previous_day_price: f64,
    pub price_change_pct_24h: f64,
}

impl std::fmt::Display for MarketContext {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}(vol24h={:.0}, oi={:.0}, chg={:.2}%)",
            self.market, self.volume_24h, self.open_interest, self.price_change_pct_24h
        )
    }
}

// ---------------------------------------------------------------------------
// Candlestick
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct Candlestick {
    #[serde(alias = "t")]
    pub open_time: i64,
    #[serde(alias = "T")]
    pub close_time: i64,
    #[serde(alias = "o")]
    pub open: f64,
    #[serde(alias = "h")]
    pub high: f64,
    #[serde(alias = "l")]
    pub low: f64,
    #[serde(alias = "c")]
    pub close: f64,
    #[serde(alias = "v")]
    pub volume: f64,
    #[serde(alias = "i")]
    pub interval: String,
}

impl Candlestick {
    pub fn is_bullish(&self) -> bool {
        self.close >= self.open
    }

    /// Body size as percentage of open. Positive = bullish.
    pub fn body_pct(&self) -> f64 {
        if self.open == 0.0 {
            return 0.0;
        }
        (self.close - self.open) / self.open * 100.0
    }

    /// High-low range as percentage of open.
    pub fn range_pct(&self) -> f64 {
        if self.open == 0.0 {
            return 0.0;
        }
        (self.high - self.low) / self.open * 100.0
    }
}

impl std::fmt::Display for Candlestick {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let dir = if self.is_bullish() { "+" } else { "-" };
        write!(
            f,
            "Candle({} O={} H={} L={} C={} {}{:.2}%)",
            self.interval,
            self.open,
            self.high,
            self.low,
            self.close,
            dir,
            self.body_pct().abs()
        )
    }
}

// ---------------------------------------------------------------------------
// MarketTrade
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct MarketTrade {
    pub market: String,
    pub price: f64,
    pub size: f64,
    pub is_buy: bool,
    pub unix_ms: i64,
}

impl std::fmt::Display for MarketTrade {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let side = if self.is_buy { "BUY" } else { "SELL" };
        write!(
            f,
            "Trade({} {} {} @ {})",
            self.market, side, self.size, self.price
        )
    }
}

// ===========================================================================
// Tests
// ===========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -- PerpMarketConfig ---------------------------------------------------

    fn btc_market_config() -> PerpMarketConfig {
        PerpMarketConfig {
            market_addr: "0xmarket_btc".into(),
            market_name: "BTC-USD".into(),
            sz_decimals: 4,
            px_decimals: 2,
            max_leverage: 50.0,
            min_size: 1000.0,
            lot_size: 1000.0,
            tick_size: 10.0,
            max_open_interest: 500_000_000.0,
            margin_call_fee_pct: 0.5,
            taker_in_next_block: true,
        }
    }

    /// BTC config: sz_decimals=4 → min_size 1000 chain units = 0.1 BTC.
    /// This conversion is used every time an order is placed.
    #[test]
    fn perp_market_config_min_size_decimal() {
        let cfg = btc_market_config();
        let val = cfg.min_size_decimal();
        assert!((val - 0.1).abs() < 1e-10);
    }

    /// Lot size in decimal units defines the smallest position increment.
    #[test]
    fn perp_market_config_lot_size_decimal() {
        let cfg = btc_market_config();
        let val = cfg.lot_size_decimal();
        assert!((val - 0.1).abs() < 1e-10);
    }

    /// Tick size in decimal defines the minimum price movement for limit orders.
    #[test]
    fn perp_market_config_tick_size_decimal() {
        let cfg = btc_market_config();
        let val = cfg.tick_size_decimal();
        assert!((val - 0.1).abs() < 1e-10);
    }

    /// Maintenance margin fraction at 50x leverage = 1/100 = 1%.
    #[test]
    fn perp_market_config_mm_fraction() {
        let cfg = btc_market_config();
        let val = cfg.mm_fraction();
        assert!((val - 0.01).abs() < 1e-10);
    }

    /// JSON roundtrip for PerpMarketConfig — bots cache this locally.
    #[test]
    fn perp_market_config_roundtrip() {
        let cfg = btc_market_config();
        let json = serde_json::to_string(&cfg).unwrap();
        let restored: PerpMarketConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.market_name, "BTC-USD");
        assert_eq!(restored.sz_decimals, 4);
        assert_eq!(restored.max_leverage, 50.0);
        assert!(restored.taker_in_next_block);
    }

    #[test]
    fn perp_market_config_display() {
        let cfg = btc_market_config();
        let s = cfg.to_string();
        assert!(s.contains("BTC-USD"));
        assert!(s.contains("50"));
    }

    // -- MarketDepth --------------------------------------------------------

    fn sample_depth() -> MarketDepth {
        MarketDepth {
            market: "BTC-USD".into(),
            bids: vec![
                MarketOrder { price: 44_990.0, size: 1.5 },
                MarketOrder { price: 44_980.0, size: 2.0 },
                MarketOrder { price: 44_950.0, size: 5.0 },
            ],
            asks: vec![
                MarketOrder { price: 45_010.0, size: 1.0 },
                MarketOrder { price: 45_020.0, size: 3.0 },
                MarketOrder { price: 45_050.0, size: 4.0 },
            ],
            unix_ms: 1_710_000_000_000,
        }
    }

    /// Best bid/ask are used for spread calculation and quote placement.
    #[test]
    fn market_depth_best_bid_ask() {
        let d = sample_depth();
        assert!((d.best_bid().unwrap() - 44_990.0).abs() < 1e-10);
        assert!((d.best_ask().unwrap() - 45_010.0).abs() < 1e-10);
    }

    /// Spread = best_ask - best_bid. A tight spread is essential for MM bots.
    #[test]
    fn market_depth_spread() {
        let d = sample_depth();
        let spread = d.spread().unwrap();
        assert!((spread - 20.0).abs() < 1e-10);
    }

    /// Mid price = (best_bid + best_ask) / 2. Used as the fair value
    /// reference for quoting.
    #[test]
    fn market_depth_mid_price() {
        let d = sample_depth();
        let mid = d.mid_price().unwrap();
        assert!((mid - 45_000.0).abs() < 1e-10);
    }

    /// Imbalance measures buy vs. sell pressure. Positive = more bids.
    #[test]
    fn market_depth_imbalance() {
        let d = sample_depth();
        let imb = d.imbalance().unwrap();
        let bid_vol: f64 = d.bids.iter().map(|l| l.size).sum();
        let ask_vol: f64 = d.asks.iter().map(|l| l.size).sum();
        let expected = (bid_vol - ask_vol) / (bid_vol + ask_vol);
        assert!((imb - expected).abs() < 1e-10);
    }

    /// Bid depth within 0.1% of mid — measures near-market liquidity.
    #[test]
    fn market_depth_bid_depth_at() {
        let d = sample_depth();
        let depth = d.bid_depth_at(0.1);
        assert!(depth >= 1.5);
    }

    /// Ask depth within 0.1% of mid.
    #[test]
    fn market_depth_ask_depth_at() {
        let d = sample_depth();
        let depth = d.ask_depth_at(0.1);
        assert!(depth >= 1.0);
    }

    /// Empty orderbook returns None for all computed values.
    #[test]
    fn market_depth_empty() {
        let d = MarketDepth {
            market: "BTC-USD".into(),
            bids: vec![],
            asks: vec![],
            unix_ms: 0,
        };
        assert!(d.best_bid().is_none());
        assert!(d.best_ask().is_none());
        assert!(d.spread().is_none());
        assert!(d.mid_price().is_none());
        assert!(d.imbalance().is_none());
        assert_eq!(d.bid_depth_at(1.0), 0.0);
        assert_eq!(d.ask_depth_at(1.0), 0.0);
    }

    /// JSON roundtrip for MarketDepth.
    #[test]
    fn market_depth_roundtrip() {
        let d = sample_depth();
        let json = serde_json::to_string(&d).unwrap();
        let restored: MarketDepth = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.bids.len(), 3);
        assert_eq!(restored.asks.len(), 3);
        assert_eq!(restored.market, "BTC-USD");
    }

    #[test]
    fn market_depth_display() {
        let d = sample_depth();
        let s = d.to_string();
        assert!(s.contains("BTC-USD"));
        assert!(s.contains("bids=3"));
    }

    // -- MarketPrice --------------------------------------------------------

    fn sample_market_price() -> MarketPrice {
        MarketPrice {
            market: "BTC-USD".into(),
            mark_px: 45_000.0,
            mid_px: 44_999.5,
            oracle_px: 45_001.0,
            funding_rate_bps: 0.5,
            is_funding_positive: true,
            open_interest: 150_000_000.0,
            transaction_unix_ms: 1_710_000_000_000,
        }
    }

    /// Funding rate hourly: 0.5bps → 0.5/10000 * 365 * 24 = 0.438.
    /// Bots use this to decide whether to hold or hedge.
    #[test]
    fn market_price_funding_rate_hourly() {
        let mp = sample_market_price();
        let hourly = mp.funding_rate_hourly();
        let expected = 0.5 / 10_000.0 * 365.0 * 24.0;
        assert!((hourly - expected).abs() < 1e-10);
    }

    /// Funding direction tells the bot who pays whom.
    #[test]
    fn market_price_funding_direction() {
        let mp = sample_market_price();
        assert_eq!(mp.funding_direction(), "longs_pay");

        let mut mp2 = mp.clone();
        mp2.is_funding_positive = false;
        assert_eq!(mp2.funding_direction(), "shorts_pay");
    }

    /// JSON roundtrip for MarketPrice.
    #[test]
    fn market_price_roundtrip() {
        let mp = sample_market_price();
        let json = serde_json::to_string(&mp).unwrap();
        let restored: MarketPrice = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.market, "BTC-USD");
        assert!((restored.mark_px - 45_000.0).abs() < 1e-10);
        assert!(restored.is_funding_positive);
    }

    #[test]
    fn market_price_display() {
        let mp = sample_market_price();
        let s = mp.to_string();
        assert!(s.contains("BTC-USD"));
        assert!(s.contains("longs_pay"));
    }

    // -- MarketContext ------------------------------------------------------

    /// JSON roundtrip for MarketContext.
    #[test]
    fn market_context_roundtrip() {
        let mc = MarketContext {
            market: "ETH-USD".into(),
            volume_24h: 500_000_000.0,
            open_interest: 250_000_000.0,
            previous_day_price: 3_400.0,
            price_change_pct_24h: 2.5,
        };
        let json = serde_json::to_string(&mc).unwrap();
        let restored: MarketContext = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.market, "ETH-USD");
        assert!((restored.volume_24h - 500_000_000.0).abs() < 1e-10);
        assert!((restored.price_change_pct_24h - 2.5).abs() < 1e-10);
    }

    // -- Candlestick --------------------------------------------------------

    fn sample_bullish_candle() -> Candlestick {
        Candlestick {
            open_time: 1_710_000_000_000,
            close_time: 1_710_000_060_000,
            open: 45_000.0,
            high: 45_200.0,
            low: 44_900.0,
            close: 45_100.0,
            volume: 123.45,
            interval: "1m".into(),
        }
    }

    fn sample_bearish_candle() -> Candlestick {
        Candlestick {
            open_time: 1_710_000_060_000,
            close_time: 1_710_000_120_000,
            open: 45_100.0,
            high: 45_150.0,
            low: 44_800.0,
            close: 44_900.0,
            volume: 200.0,
            interval: "1m".into(),
        }
    }

    /// Bullish detection is fundamental for trend-following bots.
    #[test]
    fn candlestick_is_bullish() {
        assert!(sample_bullish_candle().is_bullish());
        assert!(!sample_bearish_candle().is_bullish());
    }

    /// Body percentage quantifies the candle's directional strength.
    #[test]
    fn candlestick_body_pct() {
        let c = sample_bullish_candle();
        let pct = c.body_pct();
        let expected = (45_100.0 - 45_000.0) / 45_000.0 * 100.0;
        assert!((pct - expected).abs() < 1e-6);
        assert!(pct > 0.0);

        let bc = sample_bearish_candle();
        assert!(bc.body_pct() < 0.0);
    }

    /// Range percentage measures volatility within the candle.
    #[test]
    fn candlestick_range_pct() {
        let c = sample_bullish_candle();
        let pct = c.range_pct();
        let expected = (45_200.0 - 44_900.0) / 45_000.0 * 100.0;
        assert!((pct - expected).abs() < 1e-6);
    }

    /// Candlestick with zero open should not panic — returns 0.
    #[test]
    fn candlestick_zero_open_safety() {
        let c = Candlestick {
            open_time: 0,
            close_time: 0,
            open: 0.0,
            high: 10.0,
            low: 0.0,
            close: 5.0,
            volume: 1.0,
            interval: "1m".into(),
        };
        assert_eq!(c.body_pct(), 0.0);
        assert_eq!(c.range_pct(), 0.0);
    }

    /// Serde alias deserialization from wire single-char keys.
    #[test]
    fn candlestick_wire_format_aliases() {
        let json = r#"{
            "t": 1710000000000,
            "T": 1710000060000,
            "o": 45000.0,
            "h": 45200.0,
            "l": 44900.0,
            "c": 45100.0,
            "v": 123.45,
            "i": "1m"
        }"#;
        let c: Candlestick = serde_json::from_str(json).unwrap();
        assert_eq!(c.open_time, 1_710_000_000_000);
        assert_eq!(c.close_time, 1_710_000_060_000);
        assert!((c.open - 45_000.0).abs() < 1e-10);
        assert!((c.high - 45_200.0).abs() < 1e-10);
        assert_eq!(c.interval, "1m");
    }

    /// Roundtrip with full field names (not aliases).
    #[test]
    fn candlestick_roundtrip() {
        let c = sample_bullish_candle();
        let json = serde_json::to_string(&c).unwrap();
        let restored: Candlestick = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.open_time, c.open_time);
        assert!((restored.close - c.close).abs() < 1e-10);
    }

    #[test]
    fn candlestick_display() {
        let c = sample_bullish_candle();
        let s = c.to_string();
        assert!(s.contains("1m"));
        assert!(s.contains("+"));
    }

    // -- MarketTrade --------------------------------------------------------

    /// JSON roundtrip for MarketTrade.
    #[test]
    fn market_trade_roundtrip() {
        let t = MarketTrade {
            market: "BTC-USD".into(),
            price: 45_000.0,
            size: 0.5,
            is_buy: true,
            unix_ms: 1_710_000_000_000,
        };
        let json = serde_json::to_string(&t).unwrap();
        let restored: MarketTrade = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.market, "BTC-USD");
        assert!(restored.is_buy);
        assert!((restored.size - 0.5).abs() < 1e-10);
    }

    #[test]
    fn market_trade_display() {
        let t = MarketTrade {
            market: "ETH-USD".into(),
            price: 3500.0,
            size: 10.0,
            is_buy: false,
            unix_ms: 0,
        };
        let s = t.to_string();
        assert!(s.contains("SELL"));
        assert!(s.contains("ETH-USD"));
    }
}
