//! # Risk Watchdog
//!
//! Demonstrates continuous risk monitoring using the SDK's
//! `PositionStateManager` and `RiskMonitor`. The watchdog checks margin
//! usage, liquidation distance, and unprotected positions, then prints
//! alerts at WARN and CRITICAL levels.
//!
//! All data is simulated locally using the state manager's synchronous
//! read/write API — no network calls are made.
//!
//! **This is a demo against the Decibel testnet. Do not use with real funds.**
//!
//! ## Usage
//!
//! ```sh
//! cargo run --example 05_risk_watchdog
//! ```

use decibel_sdk_v2::models::account::{AccountOverview, UserPosition};
use decibel_sdk_v2::models::market::MarketPrice;
use decibel_sdk_v2::state::{PositionStateManager, RiskMonitor};

const SUBACCOUNT: &str = "0xdemo_subaccount";

fn make_position(
    market: &str,
    size: f64,
    entry: f64,
    liq_price: f64,
    has_tp_sl: bool,
) -> UserPosition {
    UserPosition {
        market: market.into(),
        user: SUBACCOUNT.into(),
        size,
        user_leverage: 10.0,
        entry_price: entry,
        is_isolated: false,
        unrealized_funding: 0.0,
        estimated_liquidation_price: liq_price,
        tp_order_id: if has_tp_sl { Some("tp_001".into()) } else { None },
        tp_trigger_price: if has_tp_sl { Some(entry * 1.05) } else { None },
        tp_limit_price: if has_tp_sl { Some(entry * 1.048) } else { None },
        sl_order_id: if has_tp_sl { Some("sl_001".into()) } else { None },
        sl_trigger_price: if has_tp_sl { Some(entry * 0.97) } else { None },
        sl_limit_price: if has_tp_sl { Some(entry * 0.968) } else { None },
        has_fixed_sized_tpsls: false,
    }
}

fn make_price(market: &str, mark_px: f64) -> MarketPrice {
    MarketPrice {
        market: market.into(),
        mark_px,
        mid_px: mark_px,
        oracle_px: mark_px * 1.001,
        funding_rate_bps: 0.3,
        is_funding_positive: true,
        open_interest: 100_000_000.0,
        transaction_unix_ms: 0,
    }
}

fn make_overview(equity: f64, total_margin: f64, maintenance_margin: f64) -> AccountOverview {
    AccountOverview {
        perp_equity_balance: equity,
        unrealized_pnl: 0.0,
        unrealized_funding_cost: 0.0,
        cross_margin_ratio: 0.0,
        maintenance_margin,
        cross_account_leverage_ratio: None,
        cross_account_position: 0.0,
        total_margin,
        usdc_cross_withdrawable_balance: equity - total_margin,
        usdc_isolated_withdrawable_balance: 0.0,
        volume: None,
        net_deposits: None,
        realized_pnl: None,
        liquidation_fees_paid: None,
        liquidation_losses: None,
        all_time_return: None,
        pnl_90d: None,
        sharpe_ratio: None,
        max_drawdown: None,
        weekly_win_rate_12w: None,
        average_cash_position: None,
        average_leverage: None,
    }
}

fn print_separator() {
    println!("{}", "─".repeat(72));
}

struct Scenario {
    name: &'static str,
    equity: f64,
    total_margin: f64,
    maintenance_margin: f64,
    positions: Vec<(&'static str, f64, f64, f64, bool)>,
    prices: Vec<(&'static str, f64)>,
}

fn run_risk_check(state: &PositionStateManager) {
    let risk = RiskMonitor::new(state);

    println!("\n  --- Margin Check ---");
    match risk.margin_warning(SUBACCOUNT) {
        Some(warning) => {
            let tag = if warning.level == "critical" { "CRITICAL" } else { "WARN" };
            println!(
                "  [{tag}] Margin usage: {:.1}% | Available: ${:.2} | Equity: ${:.2}",
                warning.margin_usage_pct, warning.available_margin, warning.equity,
            );
        }
        None => {
            let usage = state.margin_usage_pct(SUBACCOUNT);
            println!("  [OK] Margin usage: {:.1}% — within safe limits", usage);
        }
    }

    println!("\n  --- Liquidation Distance ---");
    let positions = state.positions(SUBACCOUNT);
    for (market, _pos) in &positions {
        if let Some(est) = risk.liquidation_distance(SUBACCOUNT, market) {
            let tag = if est.distance_pct < 10.0 {
                "CRITICAL"
            } else if est.distance_pct < 20.0 {
                "WARN"
            } else {
                "OK"
            };
            println!(
                "  [{tag}] {market}: liq=${:.2} current=${:.2} distance={:.1}% (${:.2})",
                est.liquidation_price, est.current_price, est.distance_pct, est.distance_usd,
            );
        }
    }

    if let Some(min_est) = risk.min_liquidation_distance(SUBACCOUNT) {
        println!(
            "  Closest liquidation: {:.1}% away (${:.2})",
            min_est.distance_pct, min_est.distance_usd,
        );
    }

    println!("\n  --- Unprotected Positions ---");
    let unprotected = risk.positions_without_tp_sl(SUBACCOUNT);
    if unprotected.is_empty() {
        println!("  [OK] All positions have TP/SL protection.");
    } else {
        let exposure = risk.unprotected_exposure_usd(SUBACCOUNT);
        println!(
            "  [WARN] {} position(s) without TP/SL: {}",
            unprotected.len(),
            unprotected.join(", "),
        );
        println!("  [WARN] Unprotected notional exposure: ${:.2}", exposure);
    }

    println!("\n  --- Exposure Summary ---");
    println!(
        "  Net exposure:   ${:.2}",
        state.net_exposure_usd(SUBACCOUNT)
    );
    println!(
        "  Gross exposure: ${:.2}",
        state.gross_exposure_usd(SUBACCOUNT)
    );
    println!(
        "  Equity:         ${:.2}",
        state.equity(SUBACCOUNT)
    );
    println!(
        "  Connected:      {}",
        state.is_connected()
    );
    println!(
        "  Gap detected:   {}",
        state.gap_detected()
    );
}

fn main() {
    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║              DECIBEL TESTNET — RISK WATCHDOG DEMO                   ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝");

    let scenarios = vec![
        Scenario {
            name: "Healthy Account",
            equity: 100_000.0,
            total_margin: 25_000.0,
            maintenance_margin: 5_000.0,
            positions: vec![
                ("BTC-USD", 1.0, 65_000.0, 58_500.0, true),
                ("ETH-USD", 10.0, 3_400.0, 3_060.0, true),
            ],
            prices: vec![
                ("BTC-USD", 67_000.0),
                ("ETH-USD", 3_500.0),
            ],
        },
        Scenario {
            name: "High Margin Usage + Unprotected Position",
            equity: 50_000.0,
            total_margin: 35_000.0,
            maintenance_margin: 10_000.0,
            positions: vec![
                ("BTC-USD", 2.0, 66_000.0, 59_400.0, true),
                ("SOL-USD", -500.0, 150.0, 165.0, false),
            ],
            prices: vec![
                ("BTC-USD", 67_000.0),
                ("SOL-USD", 155.0),
            ],
        },
        Scenario {
            name: "Near Liquidation",
            equity: 20_000.0,
            total_margin: 18_000.0,
            maintenance_margin: 15_000.0,
            positions: vec![
                ("BTC-USD", 3.0, 60_000.0, 58_000.0, false),
                ("ETH-USD", -20.0, 3_200.0, 3_500.0, false),
            ],
            prices: vec![
                ("BTC-USD", 59_000.0),
                ("ETH-USD", 3_450.0),
            ],
        },
    ];

    for scenario in &scenarios {
        print_separator();
        println!("\n  SCENARIO: {}", scenario.name);
        print_separator();

        let state = PositionStateManager::new();
        state.set_connected();

        state.merge_overview(
            make_overview(scenario.equity, scenario.total_margin, scenario.maintenance_margin),
            SUBACCOUNT,
        );

        for &(market, size, entry, liq, has_tp_sl) in &scenario.positions {
            state.merge_position(
                SUBACCOUNT,
                market,
                make_position(market, size, entry, liq, has_tp_sl),
            );
        }

        for &(market, mark_px) in &scenario.prices {
            state.merge_price(market, make_price(market, mark_px));
        }

        run_risk_check(&state);
        println!();
    }

    print_separator();
    println!("  Risk watchdog demo complete. No transactions were submitted.\n");
}
