use std::sync::atomic::{AtomicU64, Ordering};
use parking_lot::RwLock;
use crate::error::DecibelError;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PriceSize {
    pub price: f64,
    pub size: f64,
}

#[derive(Debug, Clone)]
pub struct BulkQuoteResult {
    pub placed_count: usize,
    pub cancelled_count: usize,
    pub errors: Vec<String>,
    pub sequence_number: u64,
}

#[derive(Debug, Clone)]
pub struct FillSummary {
    pub bid_filled_size: f64,
    pub ask_filled_size: f64,
    pub net_size: f64,
    pub avg_bid_price: f64,
    pub avg_ask_price: f64,
    pub fill_count: usize,
}

struct FillState {
    bid_fills: Vec<(f64, f64)>,
    ask_fills: Vec<(f64, f64)>,
}

impl FillState {
    fn new() -> Self {
        Self {
            bid_fills: Vec::new(),
            ask_fills: Vec::new(),
        }
    }

    fn summary(&self) -> FillSummary {
        let bid_filled_size: f64 = self.bid_fills.iter().map(|(_, s)| s).sum();
        let ask_filled_size: f64 = self.ask_fills.iter().map(|(_, s)| s).sum();

        let avg_bid_price = if bid_filled_size > 0.0 {
            self.bid_fills.iter().map(|(p, s)| p * s).sum::<f64>() / bid_filled_size
        } else {
            0.0
        };
        let avg_ask_price = if ask_filled_size > 0.0 {
            self.ask_fills.iter().map(|(p, s)| p * s).sum::<f64>() / ask_filled_size
        } else {
            0.0
        };

        FillSummary {
            bid_filled_size,
            ask_filled_size,
            net_size: bid_filled_size - ask_filled_size,
            avg_bid_price,
            avg_ask_price,
            fill_count: self.bid_fills.len() + self.ask_fills.len(),
        }
    }

    fn clear(&mut self) {
        self.bid_fills.clear();
        self.ask_fills.clear();
    }
}

const MAX_QUOTES_PER_SIDE: usize = 30;

pub struct BulkOrderManager {
    market: String,
    sequence_number: AtomicU64,
    bids: RwLock<Vec<PriceSize>>,
    asks: RwLock<Vec<PriceSize>>,
    fills: RwLock<FillState>,
}

impl BulkOrderManager {
    pub fn new(market: &str) -> Self {
        Self {
            market: market.to_string(),
            sequence_number: AtomicU64::new(1),
            bids: RwLock::new(Vec::new()),
            asks: RwLock::new(Vec::new()),
            fills: RwLock::new(FillState::new()),
        }
    }

    pub fn market(&self) -> &str {
        &self.market
    }

    pub fn sequence_number(&self) -> u64 {
        self.sequence_number.load(Ordering::Relaxed)
    }

    pub fn set_quotes(
        &self,
        bids: &[PriceSize],
        asks: &[PriceSize],
    ) -> crate::error::Result<BulkQuoteResult> {
        if bids.len() > MAX_QUOTES_PER_SIDE || asks.len() > MAX_QUOTES_PER_SIDE {
            return Err(DecibelError::Validation {
                field: "quotes".into(),
                constraint: format!(
                    "max {} quotes per side, got {} bids and {} asks",
                    MAX_QUOTES_PER_SIDE,
                    bids.len(),
                    asks.len()
                ),
                value: None,
            });
        }

        let seq = self.sequence_number.fetch_add(1, Ordering::Relaxed);

        let mut current_bids = self.bids.write();
        let mut current_asks = self.asks.write();

        let cancelled_count = current_bids.len() + current_asks.len();

        *current_bids = bids.to_vec();
        *current_asks = asks.to_vec();

        let placed_count = bids.len() + asks.len();

        Ok(BulkQuoteResult {
            placed_count,
            cancelled_count,
            errors: Vec::new(),
            sequence_number: seq,
        })
    }

    pub fn cancel_all(&self) -> BulkQuoteResult {
        let mut current_bids = self.bids.write();
        let mut current_asks = self.asks.write();

        let cancelled_count = current_bids.len() + current_asks.len();
        current_bids.clear();
        current_asks.clear();

        let seq = self.sequence_number.fetch_add(1, Ordering::Relaxed);

        BulkQuoteResult {
            placed_count: 0,
            cancelled_count,
            errors: Vec::new(),
            sequence_number: seq,
        }
    }

    pub fn is_quoting(&self) -> bool {
        let bids = self.bids.read();
        let asks = self.asks.read();
        !bids.is_empty() || !asks.is_empty()
    }

    pub fn apply_fill(&self, is_buy: bool, price: f64, size: f64) {
        let mut fills = self.fills.write();
        if is_buy {
            fills.bid_fills.push((price, size));
        } else {
            fills.ask_fills.push((price, size));
        }
    }

    pub fn filled_since_last_reset(&self) -> FillSummary {
        self.fills.read().summary()
    }

    pub fn reset_fill_tracker(&self) -> FillSummary {
        let mut fills = self.fills.write();
        let summary = fills.summary();
        fills.clear();
        summary
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constructor() {
        let mgr = BulkOrderManager::new("BTC-USD");
        assert_eq!(mgr.market(), "BTC-USD");
        assert_eq!(mgr.sequence_number(), 1);
        assert!(!mgr.is_quoting());
    }

    #[test]
    fn sequence_increment() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids = vec![PriceSize { price: 50000.0, size: 1.0 }];
        let asks = vec![PriceSize { price: 51000.0, size: 1.0 }];

        let r1 = mgr.set_quotes(&bids, &asks).unwrap();
        let r2 = mgr.set_quotes(&bids, &asks).unwrap();
        assert!(r2.sequence_number > r1.sequence_number);
    }

    #[test]
    fn set_quotes_basic() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids = vec![
            PriceSize { price: 50000.0, size: 1.0 },
            PriceSize { price: 49900.0, size: 0.5 },
        ];
        let asks = vec![PriceSize { price: 51000.0, size: 1.0 }];

        let result = mgr.set_quotes(&bids, &asks).unwrap();
        assert_eq!(result.placed_count, 3);
        assert_eq!(result.cancelled_count, 0);
        assert!(result.errors.is_empty());
        assert!(mgr.is_quoting());
    }

    #[test]
    fn set_quotes_replaces_existing() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids1 = vec![PriceSize { price: 50000.0, size: 1.0 }];
        let asks1 = vec![PriceSize { price: 51000.0, size: 1.0 }];

        let r1 = mgr.set_quotes(&bids1, &asks1).unwrap();
        assert_eq!(r1.placed_count, 2);
        assert_eq!(r1.cancelled_count, 0);

        let bids2 = vec![PriceSize { price: 49900.0, size: 0.5 }];
        let asks2 = vec![PriceSize { price: 51100.0, size: 0.5 }];

        let r2 = mgr.set_quotes(&bids2, &asks2).unwrap();
        assert_eq!(r2.placed_count, 2);
        assert_eq!(r2.cancelled_count, 2);
    }

    #[test]
    fn cancel_all() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids = vec![PriceSize { price: 50000.0, size: 1.0 }];
        let asks = vec![PriceSize { price: 51000.0, size: 1.0 }];
        mgr.set_quotes(&bids, &asks).unwrap();
        assert!(mgr.is_quoting());

        let result = mgr.cancel_all();
        assert_eq!(result.cancelled_count, 2);
        assert_eq!(result.placed_count, 0);
        assert!(!mgr.is_quoting());
    }

    #[test]
    fn cancel_all_empty() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let result = mgr.cancel_all();
        assert_eq!(result.cancelled_count, 0);
        assert_eq!(result.placed_count, 0);
    }

    #[test]
    fn fill_tracking() {
        let mgr = BulkOrderManager::new("BTC-USD");
        mgr.apply_fill(true, 50000.0, 0.5);
        mgr.apply_fill(true, 50100.0, 0.5);
        mgr.apply_fill(false, 51000.0, 0.3);

        let summary = mgr.filled_since_last_reset();
        assert!((summary.bid_filled_size - 1.0).abs() < 0.001);
        assert!((summary.ask_filled_size - 0.3).abs() < 0.001);
        assert!((summary.net_size - 0.7).abs() < 0.001);
        assert_eq!(summary.fill_count, 3);
        // avg_bid = (50000*0.5 + 50100*0.5) / 1.0 = 50050
        assert!((summary.avg_bid_price - 50050.0).abs() < 0.01);
        // avg_ask = 51000*0.3 / 0.3 = 51000
        assert!((summary.avg_ask_price - 51000.0).abs() < 0.01);
    }

    #[test]
    fn reset_fill_tracker() {
        let mgr = BulkOrderManager::new("BTC-USD");
        mgr.apply_fill(true, 50000.0, 1.0);
        mgr.apply_fill(false, 51000.0, 0.5);

        let summary = mgr.reset_fill_tracker();
        assert!((summary.bid_filled_size - 1.0).abs() < 0.001);
        assert!((summary.ask_filled_size - 0.5).abs() < 0.001);
        assert_eq!(summary.fill_count, 2);

        let after = mgr.filled_since_last_reset();
        assert!((after.bid_filled_size).abs() < 0.001);
        assert!((after.ask_filled_size).abs() < 0.001);
        assert_eq!(after.fill_count, 0);
    }

    #[test]
    fn max_30_per_side_validation() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids: Vec<PriceSize> = (0..31)
            .map(|i| PriceSize {
                price: 50000.0 - i as f64,
                size: 0.1,
            })
            .collect();
        let asks: Vec<PriceSize> = Vec::new();
        assert!(mgr.set_quotes(&bids, &asks).is_err());
    }

    #[test]
    fn max_30_asks_validation() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids: Vec<PriceSize> = Vec::new();
        let asks: Vec<PriceSize> = (0..31)
            .map(|i| PriceSize {
                price: 51000.0 + i as f64,
                size: 0.1,
            })
            .collect();
        assert!(mgr.set_quotes(&bids, &asks).is_err());
    }

    #[test]
    fn exactly_30_per_side_ok() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let bids: Vec<PriceSize> = (0..30)
            .map(|i| PriceSize {
                price: 50000.0 - i as f64,
                size: 0.1,
            })
            .collect();
        let asks: Vec<PriceSize> = (0..30)
            .map(|i| PriceSize {
                price: 51000.0 + i as f64,
                size: 0.1,
            })
            .collect();
        let result = mgr.set_quotes(&bids, &asks).unwrap();
        assert_eq!(result.placed_count, 60);
    }

    #[test]
    fn is_quoting_reflects_state() {
        let mgr = BulkOrderManager::new("BTC-USD");
        assert!(!mgr.is_quoting());

        mgr.set_quotes(
            &[PriceSize { price: 50000.0, size: 1.0 }],
            &[],
        )
        .unwrap();
        assert!(mgr.is_quoting());

        mgr.cancel_all();
        assert!(!mgr.is_quoting());
    }

    #[test]
    fn empty_fill_summary() {
        let mgr = BulkOrderManager::new("BTC-USD");
        let summary = mgr.filled_since_last_reset();
        assert_eq!(summary.fill_count, 0);
        assert!((summary.bid_filled_size).abs() < f64::EPSILON);
        assert!((summary.ask_filled_size).abs() < f64::EPSILON);
        assert!((summary.net_size).abs() < f64::EPSILON);
        assert!((summary.avg_bid_price).abs() < f64::EPSILON);
        assert!((summary.avg_ask_price).abs() < f64::EPSILON);
    }

    #[test]
    fn send_sync_assertion() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<BulkOrderManager>();
    }
}
