//! # Account Dashboard
//!
//! Fetches account overview, positions, and open orders from the Decibel
//! testnet REST API, then displays a formatted dashboard with margin usage,
//! liquidation buffer, unrealized P&L, and order status.
//!
//! **This is a demo against the Decibel testnet. Do not use with real funds.**
//!
//! ## Environment Variables
//!
//! - `BEARER_TOKEN`         — API bearer token for the testnet.
//! - `SUBACCOUNT_ADDRESS`   — On-chain subaccount address to inspect.
//!
//! ## Usage
//!
//! ```sh
//! export BEARER_TOKEN="your_token_here"
//! export SUBACCOUNT_ADDRESS="0xYourSubaccountAddress"
//! cargo run --example 02_account_dashboard
//! ```

use decibel_sdk_v2::models::account::{AccountOverview, UserOpenOrder, UserPosition};
use decibel_sdk_v2::models::market::MarketPrice;

const BASE_URL: &str = "https://api.testnet.aptoslabs.com/decibel/api/v1";

struct Env {
    token: String,
    subaccount: String,
}

fn load_env() -> Env {
    let token = std::env::var("BEARER_TOKEN").unwrap_or_else(|_| {
        eprintln!("WARNING: BEARER_TOKEN not set — requests may fail");
        String::new()
    });
    let subaccount = std::env::var("SUBACCOUNT_ADDRESS").unwrap_or_else(|_| {
        eprintln!("WARNING: SUBACCOUNT_ADDRESS not set — using placeholder");
        "0x0000000000000000000000000000000000000000000000000000000000000000".into()
    });
    Env { token, subaccount }
}

fn client(token: &str) -> reqwest::Client {
    let mut headers = reqwest::header::HeaderMap::new();
    if !token.is_empty() {
        let val = format!("Bearer {token}");
        headers.insert(
            reqwest::header::AUTHORIZATION,
            reqwest::header::HeaderValue::from_str(&val).expect("invalid token"),
        );
    }
    reqwest::Client::builder()
        .default_headers(headers)
        .build()
        .expect("failed to build HTTP client")
}

async fn fetch_overview(
    client: &reqwest::Client,
    subaccount: &str,
) -> Option<AccountOverview> {
    let url = format!("{BASE_URL}/account/overview?subaccount={subaccount}");
    match client.get(&url).send().await {
        Ok(r) if r.status().is_success() => r.json().await.ok(),
        Ok(r) => {
            eprintln!("[overview] HTTP {}", r.status());
            None
        }
        Err(e) => {
            eprintln!("[overview] {e}");
            None
        }
    }
}

async fn fetch_positions(
    client: &reqwest::Client,
    subaccount: &str,
) -> Vec<UserPosition> {
    let url = format!("{BASE_URL}/account/positions?subaccount={subaccount}");
    match client.get(&url).send().await {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_default(),
        Ok(r) => {
            eprintln!("[positions] HTTP {}", r.status());
            Vec::new()
        }
        Err(e) => {
            eprintln!("[positions] {e}");
            Vec::new()
        }
    }
}

async fn fetch_open_orders(
    client: &reqwest::Client,
    subaccount: &str,
) -> Vec<UserOpenOrder> {
    let url = format!("{BASE_URL}/account/orders?subaccount={subaccount}");
    match client.get(&url).send().await {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_default(),
        Ok(r) => {
            eprintln!("[orders] HTTP {}", r.status());
            Vec::new()
        }
        Err(e) => {
            eprintln!("[orders] {e}");
            Vec::new()
        }
    }
}

async fn fetch_prices(client: &reqwest::Client) -> Vec<MarketPrice> {
    let url = format!("{BASE_URL}/prices");
    match client.get(&url).send().await {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_default(),
        _ => Vec::new(),
    }
}

fn print_separator() {
    println!("{}", "─".repeat(72));
}

fn print_overview(overview: &AccountOverview) {
    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║                  DECIBEL TESTNET — ACCOUNT DASHBOARD                ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝\n");

    println!("  {}", overview);
    println!();
    println!("  Equity:              ${:>14.2}", overview.perp_equity_balance);
    println!("  Unrealized PnL:      ${:>14.2}", overview.unrealized_pnl);
    println!("  Unrealized Funding:  ${:>14.2}", overview.unrealized_funding_cost);
    println!("  Total Margin:        ${:>14.2}", overview.total_margin);
    print_separator();
    println!(
        "  Margin Usage:        {:>14.2}%",
        overview.margin_usage_pct()
    );
    println!(
        "  Liquidation Buffer:  ${:>14.2} ({:.1}%)",
        overview.liquidation_buffer_usd(),
        overview.liquidation_buffer_pct()
    );
    println!(
        "  Withdrawable:        ${:>14.2}",
        overview.total_withdrawable()
    );

    if overview.is_liquidation_warning(25.0) {
        println!("\n  ⚠ WARNING: Liquidation buffer is below 25%!");
    }
    println!();
}

fn print_positions(positions: &[UserPosition], prices: &[MarketPrice]) {
    println!("  POSITIONS ({} active)", positions.len());
    print_separator();

    if positions.is_empty() {
        println!("  (no open positions)\n");
        return;
    }

    println!(
        "  {:<12} {:>6} {:>10} {:>12} {:>12} {:>12} {:>6}",
        "MARKET", "SIDE", "SIZE", "ENTRY", "MARK", "UNREAL PnL", "PROT"
    );

    for pos in positions {
        let mark_px = prices
            .iter()
            .find(|p| p.market == pos.market)
            .map(|p| p.mark_px)
            .unwrap_or(pos.entry_price);

        let pnl = pos.unrealized_pnl(mark_px);
        let pnl_sign = if pnl >= 0.0 { "+" } else { "" };
        let protection = if pos.has_protection() {
            "TP+SL"
        } else if pos.has_tp() {
            "TP"
        } else if pos.has_sl() {
            "SL"
        } else {
            "NONE"
        };

        println!(
            "  {:<12} {:>6} {:>10.4} {:>12.2} {:>12.2} {:>11}{:.2} {:>6}",
            pos.market,
            pos.direction().to_uppercase(),
            pos.size.abs(),
            pos.entry_price,
            mark_px,
            pnl_sign,
            pnl,
            protection,
        );
    }

    println!();

    for pos in positions {
        let mark_px = prices
            .iter()
            .find(|p| p.market == pos.market)
            .map(|p| p.mark_px)
            .unwrap_or(pos.entry_price);

        let notional = pos.notional(mark_px);
        let liq_dist = pos.liquidation_distance_pct(mark_px);

        println!("    {} | notional=${:.2} | leverage={}x | liq_price={:.2} ({:.1}% away)",
            pos.market,
            notional,
            pos.user_leverage,
            pos.estimated_liquidation_price,
            liq_dist,
        );
    }

    println!();
}

fn print_orders(orders: &[UserOpenOrder]) {
    println!("  OPEN ORDERS ({} active)", orders.len());
    print_separator();

    if orders.is_empty() {
        println!("  (no open orders)\n");
        return;
    }

    println!(
        "  {:<12} {:>6} {:>10} {:>12} {:>12} {:>10} {:>8}",
        "MARKET", "SIDE", "REMAINING", "PRICE", "NOTIONAL", "FILLED%", "TIF"
    );

    for order in orders {
        println!(
            "  {:<12} {:>6} {:>10.4} {:>12.2} {:>12.2} {:>9.1}% {:>8}",
            order.market,
            order.side().to_uppercase(),
            order.remaining_size,
            order.price,
            order.notional(),
            order.fill_pct(),
            order.time_in_force,
        );
    }

    println!();
}

#[tokio::main]
async fn main() {
    let env = load_env();
    let http = client(&env.token);

    println!("  Fetching data for subaccount: {}", env.subaccount);

    let (overview, positions, orders, prices) = tokio::join!(
        fetch_overview(&http, &env.subaccount),
        fetch_positions(&http, &env.subaccount),
        fetch_open_orders(&http, &env.subaccount),
        fetch_prices(&http),
    );

    match overview {
        Some(ref ov) => print_overview(ov),
        None => {
            println!("\n  Could not fetch account overview (check token and subaccount).\n");
        }
    }

    print_positions(&positions, &prices);
    print_orders(&orders);

    print_separator();
    println!("  Dashboard complete.\n");
}
