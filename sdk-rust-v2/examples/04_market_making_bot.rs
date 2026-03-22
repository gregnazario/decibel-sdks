//! # Market Making Bot
//!
//! Demonstrates a market-making loop using the SDK's `BulkOrderManager`.
//! The bot computes symmetric bid/ask quotes around a mid price, applies
//! inventory skew, tracks fills, and checks margin utilization — pulling
//! quotes when risk limits are breached.
//!
//! All data is simulated locally; no on-chain transactions are made.
//!
//! **This is a demo against the Decibel testnet. Do not use with real funds.**
//!
//! ## Usage
//!
//! ```sh
//! cargo run --example 04_market_making_bot
//! ```

use decibel_sdk_v2::bulk::{BulkOrderManager, PriceSize};

struct MmConfig {
    num_levels: usize,
    base_spread_bps: f64,
    level_spacing_bps: f64,
    size_per_level: f64,
    max_inventory: f64,
    inventory_skew_factor: f64,
    max_margin_usage_pct: f64,
    num_cycles: usize,
}

impl Default for MmConfig {
    fn default() -> Self {
        Self {
            num_levels: 5,
            base_spread_bps: 5.0,
            level_spacing_bps: 2.0,
            size_per_level: 0.1,
            max_inventory: 1.0,
            inventory_skew_factor: 0.5,
            max_margin_usage_pct: 60.0,
            num_cycles: 8,
        }
    }
}

fn compute_quotes(
    mid_price: f64,
    net_inventory: f64,
    cfg: &MmConfig,
) -> (Vec<PriceSize>, Vec<PriceSize>) {
    let skew_bps = net_inventory * cfg.inventory_skew_factor * 10.0;

    let mut bids = Vec::with_capacity(cfg.num_levels);
    let mut asks = Vec::with_capacity(cfg.num_levels);

    for i in 0..cfg.num_levels {
        let level_offset_bps = cfg.base_spread_bps + (i as f64) * cfg.level_spacing_bps;

        let bid_offset_bps = level_offset_bps + skew_bps;
        let ask_offset_bps = level_offset_bps - skew_bps;

        let bid_price = mid_price * (1.0 - bid_offset_bps / 10_000.0);
        let ask_price = mid_price * (1.0 + ask_offset_bps.max(1.0) / 10_000.0);

        let inventory_ratio = net_inventory.abs() / cfg.max_inventory;
        let bid_size = if net_inventory > 0.0 {
            cfg.size_per_level * (1.0 - inventory_ratio * 0.5)
        } else {
            cfg.size_per_level
        };
        let ask_size = if net_inventory < 0.0 {
            cfg.size_per_level * (1.0 - inventory_ratio * 0.5)
        } else {
            cfg.size_per_level
        };

        bids.push(PriceSize { price: bid_price, size: bid_size });
        asks.push(PriceSize { price: ask_price, size: ask_size });
    }

    (bids, asks)
}

fn simulate_fills(mgr: &BulkOrderManager, mid_price: f64, cycle: usize) {
    if cycle % 3 == 1 {
        let fill_price = mid_price * 0.9998;
        mgr.apply_fill(true, fill_price, 0.05);
    }
    if cycle % 4 == 2 {
        let fill_price = mid_price * 1.0002;
        mgr.apply_fill(false, fill_price, 0.03);
    }
}

fn print_separator() {
    println!("{}", "─".repeat(72));
}

fn main() {
    let mm_cfg = MmConfig::default();
    let mgr = BulkOrderManager::new("BTC-USD");

    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║            DECIBEL TESTNET — MARKET MAKING BOT DEMO                 ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝\n");

    println!("  Config:");
    println!("    Levels per side:    {}", mm_cfg.num_levels);
    println!("    Base spread:        {} bps", mm_cfg.base_spread_bps);
    println!("    Level spacing:      {} bps", mm_cfg.level_spacing_bps);
    println!("    Size per level:     {} BTC", mm_cfg.size_per_level);
    println!("    Max inventory:      {} BTC", mm_cfg.max_inventory);
    println!("    Skew factor:        {}", mm_cfg.inventory_skew_factor);
    println!("    Max margin usage:   {}%", mm_cfg.max_margin_usage_pct);
    println!("    Cycles:             {}", mm_cfg.num_cycles);
    println!();

    let base_mid = 67_500.0;
    let mut net_inventory = 0.0;
    let simulated_equity = 50_000.0;

    for cycle in 0..mm_cfg.num_cycles {
        let price_jitter = ((cycle as f64) * 1.7).sin() * 15.0;
        let mid_price = base_mid + price_jitter;

        print_separator();
        println!("  CYCLE {}/{}", cycle + 1, mm_cfg.num_cycles);
        println!("    Mid price:     ${:.2}", mid_price);
        println!("    Net inventory: {:.4} BTC", net_inventory);

        simulate_fills(&mgr, mid_price, cycle);

        let fills = mgr.reset_fill_tracker();
        if fills.fill_count > 0 {
            println!("    Fills since last cycle: {}", fills.fill_count);
            println!(
                "      Bid filled: {:.4} @ avg ${:.2}",
                fills.bid_filled_size, fills.avg_bid_price
            );
            println!(
                "      Ask filled: {:.4} @ avg ${:.2}",
                fills.ask_filled_size, fills.avg_ask_price
            );
            net_inventory += fills.net_size;
            println!("      Net delta: {:.4} → inventory now {:.4}", fills.net_size, net_inventory);
        }

        if net_inventory.abs() >= mm_cfg.max_inventory {
            println!("    ⚠ INVENTORY LIMIT REACHED — pulling all quotes");
            let cancel_result = mgr.cancel_all();
            println!(
                "    Cancelled {} quotes (seq={})",
                cancel_result.cancelled_count, cancel_result.sequence_number
            );
            continue;
        }

        let notional = net_inventory.abs() * mid_price;
        let margin_usage_pct = (notional / simulated_equity) * 100.0;
        println!("    Margin usage:  {:.1}% (notional=${:.0})", margin_usage_pct, notional);

        if margin_usage_pct > mm_cfg.max_margin_usage_pct {
            println!("    ⚠ MARGIN LIMIT — pulling quotes");
            mgr.cancel_all();
            continue;
        }

        let (bids, asks) = compute_quotes(mid_price, net_inventory, &mm_cfg);

        println!("\n    Bids:");
        for (i, b) in bids.iter().enumerate() {
            let offset_bps = (mid_price - b.price) / mid_price * 10_000.0;
            println!(
                "      L{}: ${:.2} x {:.4}  ({:.1} bps from mid)",
                i + 1, b.price, b.size, offset_bps
            );
        }
        println!("    Asks:");
        for (i, a) in asks.iter().enumerate() {
            let offset_bps = (a.price - mid_price) / mid_price * 10_000.0;
            println!(
                "      L{}: ${:.2} x {:.4}  ({:.1} bps from mid)",
                i + 1, a.price, a.size, offset_bps
            );
        }

        match mgr.set_quotes(&bids, &asks) {
            Ok(result) => {
                println!(
                    "\n    Placed {} quotes, cancelled {} (seq={})",
                    result.placed_count, result.cancelled_count, result.sequence_number
                );
            }
            Err(e) => {
                println!("\n    ⚠ Quote error: {e}");
            }
        }
    }

    print_separator();
    println!("  Final state:");
    println!("    Is quoting: {}", mgr.is_quoting());
    println!("    Sequence:   {}", mgr.sequence_number());
    println!("    Net inventory: {:.4} BTC", net_inventory);

    let cancel = mgr.cancel_all();
    println!("    Cancelled {} remaining quotes\n", cancel.cancelled_count);

    println!("  Market making demo complete. No transactions were submitted.\n");
}
