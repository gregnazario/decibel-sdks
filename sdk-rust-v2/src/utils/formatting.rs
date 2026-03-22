/// Convert a decimal amount to integer chain units.
///
/// Uses string-based conversion to avoid binary floating-point
/// representation errors that can cause off-by-one chain units.
///
/// # Examples
/// ```
/// use decibel_sdk_v2::utils::formatting::amount_to_chain_units;
/// assert_eq!(amount_to_chain_units(5.67, 9), 5_670_000_000);
/// assert_eq!(amount_to_chain_units(1.005, 6), 1_005_000);
/// ```
pub fn amount_to_chain_units(amount: f64, decimals: u32) -> u64 {
    let formatted = format!("{:.prec$}", amount, prec = decimals as usize);
    let without_dot = formatted.replace('.', "");
    let cleaned = without_dot.trim_start_matches('-');
    cleaned.parse::<u64>().unwrap_or_else(|_| {
        (amount.abs() * 10_f64.powi(decimals as i32)).round() as u64
    })
}

/// Convert on-chain integer units back to a human-readable float.
///
/// E.g. `chain_units_to_amount(1_500_000, 6)` => `1.5`.
pub fn chain_units_to_amount(chain_units: u64, decimals: u32) -> f64 {
    let factor = 10u64.pow(decimals) as f64;
    chain_units as f64 / factor
}

/// Round a price to the nearest valid tick and truncate to the given decimal places.
///
/// Uses string formatting for the final decimal truncation to avoid
/// compounding float errors from `(rounded * factor).round() / factor`.
pub fn round_to_valid_price(price: f64, tick_size: f64, px_decimals: u32) -> f64 {
    if tick_size <= 0.0 {
        return price;
    }
    let ticks = (price / tick_size).round();
    let rounded = ticks * tick_size;
    let formatted = format!("{:.prec$}", rounded, prec = px_decimals as usize);
    formatted.parse::<f64>().unwrap_or(rounded)
}

/// Round an order size down to the nearest valid lot and enforce minimum size.
///
/// Returns 0.0 if the rounded size is below `min_size`.
///
/// Uses string-based truncation for the final decimal floor to avoid
/// float noise from `(rounded * factor).floor() / factor`.
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

    // Format with extra precision so that format!'s rounding cleans up float
    // noise, then truncate the string to exactly `sz_decimals` fractional digits.
    let extra = sz_decimals as usize + 6;
    let formatted = format!("{:.prec$}", rounded, prec = extra);
    let truncated = if let Some(dot_pos) = formatted.find('.') {
        if sz_decimals == 0 {
            formatted[..dot_pos].parse::<f64>().unwrap_or(0.0)
        } else {
            let end = (dot_pos + 1 + sz_decimals as usize).min(formatted.len());
            formatted[..end].parse::<f64>().unwrap_or(0.0)
        }
    } else {
        formatted.parse::<f64>().unwrap_or(0.0)
    };

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
    fn amount_to_chain_units_string_precision() {
        assert_eq!(amount_to_chain_units(5.67, 9), 5_670_000_000);
        assert_eq!(amount_to_chain_units(1.005, 6), 1_005_000);
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
