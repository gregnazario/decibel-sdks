/// Convert a human-readable amount to on-chain integer units.
///
/// E.g. `amount_to_chain_units(1.5, 6)` => `1_500_000`.
pub fn amount_to_chain_units(amount: f64, decimals: u32) -> u64 {
    let factor = 10u64.pow(decimals) as f64;
    (amount * factor).round() as u64
}

/// Convert on-chain integer units back to a human-readable float.
///
/// E.g. `chain_units_to_amount(1_500_000, 6)` => `1.5`.
pub fn chain_units_to_amount(chain_units: u64, decimals: u32) -> f64 {
    let factor = 10u64.pow(decimals) as f64;
    chain_units as f64 / factor
}

/// Round a price to the nearest valid tick and truncate to the given decimal places.
pub fn round_to_valid_price(price: f64, tick_size: f64, px_decimals: u32) -> f64 {
    if tick_size <= 0.0 {
        return price;
    }
    let ticks = (price / tick_size).round();
    let rounded = ticks * tick_size;
    let factor = 10f64.powi(px_decimals as i32);
    (rounded * factor).round() / factor
}

/// Round an order size down to the nearest valid lot and enforce minimum size.
///
/// Returns 0.0 if the rounded size is below `min_size`.
pub fn round_to_valid_order_size(
    size: f64,
    lot_size: f64,
    min_size: f64,
    sz_decimals: u32,
) -> f64 {
    if lot_size <= 0.0 || size <= 0.0 {
        return 0.0;
    }
    let lots = (size / lot_size).floor();
    let rounded = lots * lot_size;
    let factor = 10f64.powi(sz_decimals as i32);
    let truncated = (rounded * factor).floor() / factor;
    if truncated < min_size {
        return 0.0;
    }
    truncated
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn amount_roundtrip_6_decimals() {
        let original = 1.5;
        let chain = amount_to_chain_units(original, 6);
        let back = chain_units_to_amount(chain, 6);
        assert!((original - back).abs() < 1e-10);
    }

    #[test]
    fn amount_roundtrip_8_decimals() {
        let original = 0.00000001;
        let chain = amount_to_chain_units(original, 8);
        assert_eq!(chain, 1);
        let back = chain_units_to_amount(chain, 8);
        assert!((original - back).abs() < 1e-15);
    }

    #[test]
    fn amount_to_chain_units_zero() {
        assert_eq!(amount_to_chain_units(0.0, 6), 0);
    }

    #[test]
    fn amount_to_chain_units_whole_number() {
        assert_eq!(amount_to_chain_units(100.0, 6), 100_000_000);
    }

    #[test]
    fn amount_to_chain_units_large_value() {
        let chain = amount_to_chain_units(1_000_000.0, 6);
        assert_eq!(chain, 1_000_000_000_000);
    }

    #[test]
    fn chain_units_to_amount_zero() {
        assert!((chain_units_to_amount(0, 6)).abs() < f64::EPSILON);
    }

    #[test]
    fn round_to_valid_price_basic() {
        let result = round_to_valid_price(45001.3, 0.5, 1);
        assert!((result - 45001.5).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_price_exact_tick() {
        let result = round_to_valid_price(100.0, 0.25, 2);
        assert!((result - 100.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_price_rounds_nearest() {
        let result = round_to_valid_price(100.13, 0.25, 2);
        assert!((result - 100.25).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_price_zero_tick() {
        let result = round_to_valid_price(42.0, 0.0, 2);
        assert!((result - 42.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_price_decimals_truncation() {
        let result = round_to_valid_price(0.123456, 0.01, 2);
        assert!((result - 0.12).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_basic() {
        let result = round_to_valid_order_size(1.57, 0.1, 0.1, 1);
        assert!((result - 1.5).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_floors_to_lot() {
        let result = round_to_valid_order_size(1.99, 0.5, 0.1, 1);
        assert!((result - 1.5).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_below_min() {
        let result = round_to_valid_order_size(0.05, 0.1, 0.1, 1);
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_exactly_min() {
        let result = round_to_valid_order_size(0.1, 0.1, 0.1, 1);
        assert!((result - 0.1).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_zero() {
        let result = round_to_valid_order_size(0.0, 0.1, 0.1, 1);
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_negative() {
        let result = round_to_valid_order_size(-1.0, 0.1, 0.1, 1);
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_zero_lot() {
        let result = round_to_valid_order_size(1.0, 0.0, 0.1, 1);
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn round_to_valid_order_size_large() {
        let result = round_to_valid_order_size(1_000_000.7, 1.0, 1.0, 0);
        assert!((result - 1_000_000.0).abs() < 1e-10);
    }

    #[test]
    fn formatting_precision() {
        // 1.025 / 0.05 = 20.5, rounds to 20 or 21 depending on representation.
        // Use a value that cleanly exercises tick + decimal rounding.
        let result = round_to_valid_price(1.03, 0.05, 2);
        assert!((result - 1.05).abs() < 1e-10, "got {}", result);
    }

    #[test]
    fn roundtrip_many_values() {
        for i in 0..100 {
            let original = i as f64 * 0.01;
            let chain = amount_to_chain_units(original, 6);
            let back = chain_units_to_amount(chain, 6);
            assert!(
                (original - back).abs() < 1e-6,
                "roundtrip failed for {}: got {}",
                original,
                back
            );
        }
    }
}
