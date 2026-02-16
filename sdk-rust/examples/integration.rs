///! Integration example: list markets, check balance, place a trade, check balance again.
///!
///! Usage:
///!   export DECIBEL_PRIVATE_KEY="0x..."
///!   export DECIBEL_ACCOUNT_ADDRESS="0x..."
///!   export APTOS_NODE_API_KEY="..."          # optional, for higher rate limits
///!   cargo run --example integration
use decibel_sdk::client::read::DecibelReadClient;
use decibel_sdk::client::write::{DecibelWriteClient, PlaceOrderArgs};
use decibel_sdk::config::testnet_config;
use decibel_sdk::models::{TimeInForce, VolumeWindow};
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = testnet_config();
    let api_key = env::var("APTOS_NODE_API_KEY").ok();
    let private_key = env::var("DECIBEL_PRIVATE_KEY")
        .expect("Set DECIBEL_PRIVATE_KEY env var");
    let account_address = env::var("DECIBEL_ACCOUNT_ADDRESS")
        .expect("Set DECIBEL_ACCOUNT_ADDRESS env var");

    // ── 1. Read client ─────────────────────────────────────────────────
    let read = DecibelReadClient::new(config.clone(), api_key.clone(), None)?;

    // ── List all available markets ──────────────────────────────────────
    println!("=== Available Markets ===");
    let markets = read.get_all_markets().await?;
    for m in &markets {
        println!(
            "  {} (addr: {}…)  max_leverage: {}x  tick: {}  lot: {}",
            m.market_name,
            &m.market_addr[..10],
            m.max_leverage,
            m.tick_size,
            m.lot_size,
        );
    }
    println!("Total markets: {}\n", markets.len());

    // Pick the first market for the rest of the demo.
    let market = markets
        .first()
        .expect("No markets found — is the testnet deployment live?");
    let market_name = &market.market_name;

    // ── Fetch current price ─────────────────────────────────────────────
    let prices = read.get_market_price_by_name(market_name).await?;
    if let Some(p) = prices.first() {
        println!(
            "=== {market_name} Prices ===\n  mark: {}  mid: {}  oracle: {}  funding: {} bps\n",
            p.mark_px, p.mid_px, p.oracle_px, p.funding_rate_bps,
        );
    }

    // ── Fetch order-book depth ──────────────────────────────────────────
    let depth = read.get_market_depth(market_name, Some(5)).await?;
    println!("=== {market_name} Order Book (top 5) ===");
    println!("  Bids:");
    for b in &depth.bids {
        println!("    {} @ {}", b.size, b.price);
    }
    println!("  Asks:");
    for a in &depth.asks {
        println!("    {} @ {}", a.size, a.price);
    }
    println!();

    // ── 2. Write client ─────────────────────────────────────────────────
    let write = DecibelWriteClient::new(
        config,
        &private_key,
        &account_address,
        false, // skip_simulate
        false, // no_fee_payer
        api_key,
        None,  // gas_price_manager
        None,  // time_delta_ms
    )?;

    let subaccount = write.get_primary_subaccount_addr();
    println!("=== Account ===");
    println!("  address:    {account_address}");
    println!("  subaccount: {subaccount}\n");

    // ── Check balance BEFORE the trade ──────────────────────────────────
    let before = read
        .get_account_overview(&subaccount, Some(VolumeWindow::ThirtyDays), None)
        .await?;
    println!("=== Balance BEFORE Trade ===");
    println!("  equity:       {}", before.perp_equity_balance);
    println!("  margin:       {}", before.total_margin);
    println!("  unrealised:   {}", before.unrealized_pnl);
    println!("  withdrawable: {}\n", before.usdc_cross_withdrawable_balance);

    // ── Place a small limit order well below market (won't fill) ────────
    let limit_price = if let Some(p) = prices.first() {
        (p.mid_px * 0.90 * 100.0).round() / 100.0   // 10 % below mid
    } else {
        1.0
    };
    let order_size = market.min_size;

    println!("=== Placing Order ===");
    println!(
        "  market: {market_name}  side: BUY  price: {limit_price}  size: {order_size}  tif: GTC"
    );

    let result = write
        .place_order(PlaceOrderArgs {
            market_name: market_name.clone(),
            price: limit_price,
            size: order_size,
            is_buy: true,
            time_in_force: TimeInForce::GoodTillCanceled,
            is_reduce_only: false,
            client_order_id: Some("rust-example-001".into()),
            stop_price: None,
            tp_trigger_price: None,
            tp_limit_price: None,
            sl_trigger_price: None,
            sl_limit_price: None,
            builder_addr: None,
            builder_fee: None,
            subaccount_addr: Some(subaccount.clone()),
            tick_size: Some(market.tick_size),
        })
        .await?;

    if result.success {
        println!("  ✓ order_id: {:?}", result.order_id);
        println!("  tx_hash:    {:?}\n", result.transaction_hash);
    } else {
        println!("  ✗ error: {:?}\n", result.error);
    }

    // ── Check balance AFTER the trade ───────────────────────────────────
    let after = read
        .get_account_overview(&subaccount, Some(VolumeWindow::ThirtyDays), None)
        .await?;
    println!("=== Balance AFTER Trade ===");
    println!("  equity:       {}", after.perp_equity_balance);
    println!("  margin:       {}", after.total_margin);
    println!("  unrealised:   {}", after.unrealized_pnl);
    println!("  withdrawable: {}\n", after.usdc_cross_withdrawable_balance);

    // ── Show open orders ────────────────────────────────────────────────
    let open = read.get_user_open_orders(&subaccount).await?;
    println!("=== Open Orders ({}) ===", open.len());
    for o in &open {
        println!(
            "  {} {} {} @ {} (remaining: {})",
            o.order_id,
            if o.is_buy { "BUY" } else { "SELL" },
            o.market,
            o.price,
            o.remaining_size,
        );
    }

    println!("\nDone.");
    Ok(())
}
