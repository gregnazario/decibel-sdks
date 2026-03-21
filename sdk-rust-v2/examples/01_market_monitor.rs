//! # Market Monitor
//!
//! A read-only market monitoring dashboard that fetches live data from the
//! Decibel testnet REST API and displays prices, funding rates, open interest,
//! and orderbook depth.
//!
//! **This is a demo against the Decibel testnet. Do not use with real funds.**
//!
//! ## Environment Variables
//!
//! - `BEARER_TOKEN` — API bearer token for the testnet.
//!
//! ## Usage
//!
//! ```sh
//! export BEARER_TOKEN="your_token_here"
//! cargo run --example 01_market_monitor
//! ```

use decibel_sdk_v2::models::market::{MarketDepth, MarketPrice, PerpMarketConfig};

const BASE_URL: &str = "https://api.testnet.aptoslabs.com/decibel/api/v1";

fn bearer_token() -> String {
    std::env::var("BEARER_TOKEN").unwrap_or_else(|_| {
        eprintln!("WARNING: BEARER_TOKEN not set — requests may fail with 401");
        String::new()
    })
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

async fn fetch_markets(client: &reqwest::Client) -> Vec<PerpMarketConfig> {
    let url = format!("{BASE_URL}/markets");
    let resp = client.get(&url).send().await;
    match resp {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_default(),
        Ok(r) => {
            eprintln!("[markets] HTTP {}: {}", r.status(), r.text().await.unwrap_or_default());
            Vec::new()
        }
        Err(e) => {
            eprintln!("[markets] request failed: {e}");
            Vec::new()
        }
    }
}

async fn fetch_prices(client: &reqwest::Client) -> Vec<MarketPrice> {
    let url = format!("{BASE_URL}/prices");
    let resp = client.get(&url).send().await;
    match resp {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_default(),
        Ok(r) => {
            eprintln!("[prices] HTTP {}: {}", r.status(), r.text().await.unwrap_or_default());
            Vec::new()
        }
        Err(e) => {
            eprintln!("[prices] request failed: {e}");
            Vec::new()
        }
    }
}

async fn fetch_depth(client: &reqwest::Client, market: &str) -> Option<MarketDepth> {
    let url = format!("{BASE_URL}/depth?market={market}");
    let resp = client.get(&url).send().await;
    match resp {
        Ok(r) if r.status().is_success() => r.json().await.ok(),
        Ok(r) => {
            eprintln!("[depth] HTTP {}: {}", r.status(), r.text().await.unwrap_or_default());
            None
        }
        Err(e) => {
            eprintln!("[depth] request failed: {e}");
            None
        }
    }
}

fn print_separator() {
    println!("{}", "─".repeat(72));
}

fn print_market_dashboard(configs: &[PerpMarketConfig], prices: &[MarketPrice]) {
    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║                     DECIBEL TESTNET — MARKET MONITOR               ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝\n");

    if configs.is_empty() {
        println!("  (no markets available)\n");
        return;
    }

    println!(
        "  {:<12} {:>12} {:>12} {:>10} {:>14} {:>8}",
        "MARKET", "MARK", "ORACLE", "FUND bps", "OI", "MAX LEV"
    );
    print_separator();

    for cfg in configs {
        let price = prices.iter().find(|p| p.market == cfg.market_name || p.market == cfg.market_addr);
        match price {
            Some(px) => {
                let funding_sign = if px.is_funding_positive { "+" } else { "-" };
                println!(
                    "  {:<12} {:>12.2} {:>12.2} {:>9}{} {:>14.0} {:>7.0}x",
                    cfg.market_name,
                    px.mark_px,
                    px.oracle_px,
                    px.funding_rate_bps,
                    funding_sign,
                    px.open_interest,
                    cfg.max_leverage,
                );
            }
            None => {
                println!(
                    "  {:<12} {:>12} {:>12} {:>10} {:>14} {:>7.0}x",
                    cfg.market_name, "—", "—", "—", "—", cfg.max_leverage,
                );
            }
        }
    }

    println!();
}

fn print_market_details(cfg: &PerpMarketConfig) {
    println!("  Market Config: {}", cfg);
    println!(
        "    min size  = {} (decimal: {})",
        cfg.min_size,
        cfg.min_size_decimal()
    );
    println!(
        "    lot size  = {} (decimal: {})",
        cfg.lot_size,
        cfg.lot_size_decimal()
    );
    println!(
        "    tick size = {} (decimal: {})",
        cfg.tick_size,
        cfg.tick_size_decimal()
    );
    println!(
        "    maintenance margin fraction = {:.4}",
        cfg.mm_fraction()
    );
    println!();
}

fn print_depth(depth: &MarketDepth) {
    println!("  Orderbook: {}", depth);
    if let (Some(bid), Some(ask)) = (depth.best_bid(), depth.best_ask()) {
        println!("    Best Bid: {:.2}  |  Best Ask: {:.2}", bid, ask);
        println!(
            "    Spread: {:.2}  |  Mid: {:.2}",
            depth.spread().unwrap_or(0.0),
            depth.mid_price().unwrap_or(0.0)
        );
    }
    if let Some(imb) = depth.imbalance() {
        println!("    Imbalance: {:.4} (positive = buy pressure)", imb);
    }
    println!(
        "    Bid depth ±0.5%: {:.4}  |  Ask depth ±0.5%: {:.4}",
        depth.bid_depth_at(0.5),
        depth.ask_depth_at(0.5)
    );

    let top_n = 5;
    println!("\n    {:>12}  {:>12}  |  {:>12}  {:>12}", "BID SIZE", "BID PRICE", "ASK PRICE", "ASK SIZE");
    println!("    {}", "─".repeat(56));
    for i in 0..top_n {
        let bid_str = depth
            .bids
            .get(i)
            .map(|l| format!("{:>12.4}  {:>12.2}", l.size, l.price))
            .unwrap_or_else(|| format!("{:>12}  {:>12}", "", ""));
        let ask_str = depth
            .asks
            .get(i)
            .map(|l| format!("{:>12.2}  {:>12.4}", l.price, l.size))
            .unwrap_or_else(|| format!("{:>12}  {:>12}", "", ""));
        println!("    {}  |  {}", bid_str, ask_str);
    }
    println!();
}

#[tokio::main]
async fn main() {
    let token = bearer_token();
    let http = client(&token);

    let (configs, prices) = tokio::join!(fetch_markets(&http), fetch_prices(&http));

    print_market_dashboard(&configs, &prices);

    for cfg in configs.iter().take(3) {
        print_separator();
        print_market_details(cfg);

        if let Some(depth) = fetch_depth(&http, &cfg.market_addr).await {
            print_depth(&depth);
        } else {
            println!("  (no depth data for {})\n", cfg.market_name);
        }
    }

    print_separator();
    println!("  Done. Fetched {} markets, {} prices.\n", configs.len(), prices.len());
}
