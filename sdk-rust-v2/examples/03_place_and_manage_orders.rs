//! # Place and Manage Orders
//!
//! Demonstrates how to compute valid order parameters for the Decibel
//! perpetual exchange using the SDK's formatting utilities and market config.
//!
//! This example does **not** submit transactions on-chain. It shows the
//! exact Move function call payload that a bot would construct to place a
//! limit order, including take-profit and stop-loss prices.
//!
//! **This is a demo against the Decibel testnet. Do not use with real funds.**
//!
//! ## Usage
//!
//! ```sh
//! cargo run --example 03_place_and_manage_orders
//! ```

use decibel_sdk_v2::models::market::{MarketPrice, PerpMarketConfig};
use decibel_sdk_v2::utils::formatting::{
    amount_to_chain_units, round_to_valid_order_size, round_to_valid_price,
};

fn sample_btc_config() -> PerpMarketConfig {
    PerpMarketConfig {
        market_addr: "0xabc123".into(),
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

fn sample_btc_price() -> MarketPrice {
    MarketPrice {
        market: "BTC-USD".into(),
        mark_px: 67_500.0,
        mid_px: 67_498.0,
        oracle_px: 67_510.0,
        funding_rate_bps: 0.35,
        is_funding_positive: true,
        open_interest: 280_000_000.0,
        transaction_unix_ms: 1_710_000_000_000,
    }
}

fn print_separator() {
    println!("{}", "─".repeat(72));
}

fn demonstrate_order_sizing(cfg: &PerpMarketConfig, mark_price: f64) {
    println!("\n  1) ORDER SIZING");
    print_separator();

    let desired_usd_notional = 1_000.0;
    let raw_size = desired_usd_notional / mark_price;
    println!("  Target notional: ${:.2}", desired_usd_notional);
    println!("  Raw size:        {:.8} BTC", raw_size);

    let valid_size = round_to_valid_order_size(
        raw_size,
        cfg.lot_size_decimal(),
        cfg.min_size_decimal(),
        cfg.sz_decimals as u32,
    );
    println!(
        "  Valid size:      {:.4} BTC (lot={}, min={})",
        valid_size,
        cfg.lot_size_decimal(),
        cfg.min_size_decimal(),
    );

    let chain_size = amount_to_chain_units(valid_size, cfg.sz_decimals as u32);
    println!("  Chain units:     {} (sz_decimals={})", chain_size, cfg.sz_decimals);

    if valid_size == 0.0 {
        println!("  ⚠ Size below minimum — order would be rejected.");
        println!("  Minimum order: {} BTC (${:.2})", cfg.min_size_decimal(), cfg.min_size_decimal() * mark_price);
    }

    println!();
}

fn demonstrate_limit_order(cfg: &PerpMarketConfig, price: &MarketPrice) {
    println!("  2) LIMIT BUY ORDER — 5% below mark");
    print_separator();

    let discount_pct = 5.0;
    let raw_limit_price = price.mark_px * (1.0 - discount_pct / 100.0);
    println!("  Mark price:      ${:.2}", price.mark_px);
    println!("  Raw limit price: ${:.6}", raw_limit_price);

    let valid_price = round_to_valid_price(
        raw_limit_price,
        cfg.tick_size_decimal(),
        cfg.px_decimals as u32,
    );
    println!(
        "  Valid price:     ${:.2} (tick={})",
        valid_price,
        cfg.tick_size_decimal(),
    );

    let chain_price = amount_to_chain_units(valid_price, cfg.px_decimals as u32);
    println!(
        "  Chain units:     {} (px_decimals={})",
        chain_price, cfg.px_decimals
    );

    let order_size = cfg.min_size_decimal();
    let chain_size = amount_to_chain_units(order_size, cfg.sz_decimals as u32);

    println!("\n  Order summary:");
    println!("    Side:  BUY");
    println!("    Price: ${:.2} ({} chain units)", valid_price, chain_price);
    println!("    Size:  {} BTC ({} chain units)", order_size, chain_size);
    println!(
        "    Notional: ${:.2}",
        valid_price * order_size
    );

    println!("\n  Move entry function call (would be submitted on-chain):");
    println!("    function: {}::perp_trading::place_limit_order", cfg.market_addr);
    println!("    args: [");
    println!("      market_addr: \"{}\"", cfg.market_addr);
    println!("      is_buy:      true");
    println!("      price:       {chain_price}");
    println!("      size:        {chain_size}");
    println!("      tif:         0  // GoodTillCanceled");
    println!("    ]");

    println!();
}

fn demonstrate_tp_sl(cfg: &PerpMarketConfig, price: &MarketPrice) {
    println!("  3) TAKE-PROFIT / STOP-LOSS COMPUTATION");
    print_separator();

    let entry_price = price.mark_px;
    let tp_pct = 3.0;
    let sl_pct = 1.5;

    let raw_tp = entry_price * (1.0 + tp_pct / 100.0);
    let raw_sl = entry_price * (1.0 - sl_pct / 100.0);

    let tp_price = round_to_valid_price(raw_tp, cfg.tick_size_decimal(), cfg.px_decimals as u32);
    let sl_price = round_to_valid_price(raw_sl, cfg.tick_size_decimal(), cfg.px_decimals as u32);

    println!("  Entry:        ${:.2}", entry_price);
    println!("  TP target:    +{tp_pct}% → ${:.2} (raw {:.6})", tp_price, raw_tp);
    println!("  SL target:    -{sl_pct}% → ${:.2} (raw {:.6})", sl_price, raw_sl);

    let chain_tp = amount_to_chain_units(tp_price, cfg.px_decimals as u32);
    let chain_sl = amount_to_chain_units(sl_price, cfg.px_decimals as u32);
    println!("  TP chain:     {}", chain_tp);
    println!("  SL chain:     {}", chain_sl);

    let risk_reward = (tp_price - entry_price) / (entry_price - sl_price);
    println!("  Risk/Reward:  {:.2}:1", risk_reward);

    println!();
}

fn demonstrate_leverage_check(cfg: &PerpMarketConfig, price: &MarketPrice) {
    println!("  4) LEVERAGE & MARGIN CHECK");
    print_separator();

    let equity = 10_000.0;
    let position_size_btc = 0.5;
    let notional = position_size_btc * price.mark_px;
    let leverage = notional / equity;
    let mm_fraction = cfg.mm_fraction();
    let maintenance_margin = notional * mm_fraction;

    println!("  Account equity:     ${:.2}", equity);
    println!("  Position:           {} BTC @ ${:.2}", position_size_btc, price.mark_px);
    println!("  Notional:           ${:.2}", notional);
    println!("  Effective leverage:  {:.2}x (max: {}x)", leverage, cfg.max_leverage);
    println!("  MM fraction:         {:.4} (1/{})", mm_fraction, (cfg.max_leverage * 2.0) as u32);
    println!("  Maintenance margin: ${:.2}", maintenance_margin);
    println!(
        "  Buffer above MM:    ${:.2}",
        equity - maintenance_margin
    );

    if leverage > cfg.max_leverage {
        println!("  ⚠ REJECTED: Leverage exceeds maximum allowed!");
    } else if leverage > cfg.max_leverage * 0.8 {
        println!("  ⚠ WARNING: Leverage near maximum ({:.0}% of limit)", leverage / cfg.max_leverage * 100.0);
    } else {
        println!("  ✓ Leverage within safe limits.");
    }

    println!();
}

fn main() {
    let cfg = sample_btc_config();
    let price = sample_btc_price();

    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║              DECIBEL TESTNET — ORDER PARAMETER DEMO                 ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝\n");

    println!("  Market: {}", cfg);
    println!("  Price:  {}\n", price);

    demonstrate_order_sizing(&cfg, price.mark_px);
    demonstrate_limit_order(&cfg, &price);
    demonstrate_tp_sl(&cfg, &price);
    demonstrate_leverage_check(&cfg, &price);

    println!("{}", "─".repeat(72));
    println!("  Order parameter demo complete. No transactions were submitted.\n");
}
