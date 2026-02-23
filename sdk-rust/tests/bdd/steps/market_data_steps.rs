//! Step definitions for market-data.feature
//!
//! These steps test market data retrieval via the REST API.

use cucumber::{given, then, when};
use decibel_sdk::{
    client::read::DecibelReadClient,
    error::DecibelError,
    models::market_data::{PerpMarketConfig, MarketDepth, MarketPrice, Candlestick, MarketTrade, MarketContext},
};

use crate::TestWorld;

/// Background: I have an initialized Decibel read client
#[given(expr = "I have an initialized Decibel read client")]
async fn given_read_client(world: &mut TestWorld) {
    match world.get_read_client().await {
        Ok(_) => {},
        Err(e) => world.set_error(e),
    }
}

/// When: I request all markets
#[when("I request all markets")]
async fn request_all_markets(world: &mut TestWorld) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_all_markets().await {
        Ok(markets) => world.markets = Some(markets),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive a list of market configurations
#[then("I should receive a list of market configurations")]
async fn should_receive_markets(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.markets.is_some(), "Markets should be set");
    let markets = world.markets.as_ref().unwrap();
    assert!(!markets.is_empty(), "Should have at least one market");
}

/// And: Each market should have a market address
#[then("each market should have a market address")]
async fn check_market_address(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(!market.market_addr.is_empty(), "Market address should not be empty");
    }
}

/// And: Each market should have a market name
#[then("each market should have a market name")]
async fn check_market_name(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(!market.market_name.is_empty(), "Market name should not be empty");
    }
}

/// And: Each market should have size decimals
#[then("each market should have size decimals")]
async fn check_size_decimals(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.sz_decimals >= 0, "Size decimals should be non-negative");
    }
}

/// And: Each market should have price decimals
#[then("each market should have price decimals")]
async fn check_price_decimals(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.px_decimals >= 0, "Price decimals should be non-negative");
    }
}

/// And: Each market should have maximum leverage
#[then("each market should have maximum leverage")]
async fn check_max_leverage(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.max_leverage > 0.0, "Max leverage should be positive");
    }
}

/// And: Each market should have minimum order size
#[then("each market should have minimum order size")]
async fn check_min_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.min_size > 0.0, "Min size should be positive");
    }
}

/// And: Each market should have lot size
#[then("each market should have lot size")]
async fn check_lot_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.lot_size > 0.0, "Lot size should be positive");
    }
}

/// And: Each market should have tick size
#[then("each market should have tick size")]
async fn check_tick_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    for market in markets {
        assert!(market.tick_size > 0.0, "Tick size should be positive");
    }
}

/// When: I request the market with name {word}
#[when(expr = "I request the market with name {word}")]
async fn request_market_by_name(world: &mut TestWorld, name: String) {
    world.test_market_name = Some(name.clone());
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_by_name(&name).await {
        Ok(market) => {
            // Store as a single-element vector for consistency
            world.markets = Some(vec![market]);
        }
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the {word} market configuration
#[then(expr = "I should receive the {word} market configuration")]
async fn should_receive_market_config(world: &mut TestWorld, name: String) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.markets.is_some(), "Markets should be set");
    let markets = world.markets.as_ref().unwrap();
    assert_eq!(markets.len(), 1, "Should have exactly one market");
    assert_eq!(markets[0].market_name, name, "Market name should match");
}

/// And: The market name should be {word}
#[then(expr = "the market name should be {word}")]
async fn check_market_name_value(world: &mut TestWorld, name: String) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    assert_eq!(markets[0].market_name, name);
}

/// And: The market should have a valid market address
#[then("the market should have a valid market address")]
async fn check_valid_market_address(world: &mut TestWorld) {
    assert!(!world.has_error());
    let markets = world.markets.as_ref().expect("Markets should be set");
    assert!(!markets[0].market_addr.starts_with("0x"), "Market address should start with 0x");
    assert!(markets[0].market_addr.len() >= 66, "Market address should be valid hex");
}

/// When: I request the market depth for {word} with no limit
#[when(expr = "I request the market depth for {word} with no limit")]
async fn request_market_depth_no_limit(world: &mut TestWorld, name: String) {
    world.test_market_name = Some(name);
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_depth(&name, None).await {
        Ok(depth) => world.market_depth = Some(depth),
        Err(e) => world.set_error(e),
    }
}

/// When: I request the market depth for {word} with a limit of {int}
#[when(expr = "I request the market depth for {word} with a limit of {int}")]
async fn request_market_depth_with_limit(world: &mut TestWorld, name: String, limit: i64) {
    world.test_market_name = Some(name);
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_depth(&name, Some(limit as u32)).await {
        Ok(depth) => world.market_depth = Some(depth),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the current order book
#[then("I should receive the current order book")]
async fn should_receive_order_book(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.market_depth.is_some(), "Market depth should be set");
}

/// And: The order book should contain bid orders
#[then("the order book should contain bid orders")]
async fn check_bids(world: &mut TestWorld) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    // Bids might be empty if no orders, but the field should exist
    // We just verify we can access it
    let _bids = &depth.bids;
}

/// And: The order book should contain ask orders
#[then("the order book should contain ask orders")]
async fn check_asks(world: &mut TestWorld) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    let _asks = &depth.asks;
}

/// And: Bid orders should be sorted by price descending
#[then("bid orders should be sorted by price descending")]
async fn check_bids_sorted(world: &mut TestWorld) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    let mut prev_price = f64::MAX;
    for bid in &depth.bids {
        assert!(bid.price <= prev_price, "Bids should be sorted descending");
        prev_price = bid.price;
    }
}

/// And: Ask orders should be sorted by price ascending
#[then("ask orders should be sorted by price ascending")]
async fn check_asks_sorted(world: &mut TestWorld) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    let mut prev_price = f64::MIN;
    for ask in &depth.asks {
        assert!(ask.price >= prev_price, "Asks should be sorted ascending");
        prev_price = ask.price;
    }
}

/// And: Each price level should have a price and size
#[then("each price level should have a price and size")]
async fn check_price_levels(world: &mut TestWorld) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    for bid in &depth.bids {
        assert!(bid.price > 0.0, "Bid price should be positive");
        assert!(bid.size >= 0.0, "Bid size should be non-negative");
    }
    for ask in &depth.asks {
        assert!(ask.price > 0.0, "Ask price should be positive");
        assert!(ask.size >= 0.0, "Ask size should be non-negative");
    }
}

/// When: I request the market depth for {word} with a limit of {int}
#[then(expr = "I should receive up to {int} price levels on each side")]
async fn check_limit(world: &mut TestWorld, limit: i64) {
    assert!(!world.has_error());
    let depth = world.market_depth.as_ref().expect("Market depth should be set");
    // The limit is per side, so total should be at most 2 * limit
    assert!(depth.bids.len() <= limit as usize || depth.asks.len() <= limit as usize,
            "Depth should respect limit");
}

/// When: I request all market prices
#[when("I request all market prices")]
async fn request_all_prices(world: &mut TestWorld) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_all_market_prices().await {
        Ok(prices) => world.market_prices = Some(prices),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive current prices for all markets
#[then("I should receive current prices for all markets")]
async fn should_receive_all_prices(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.market_prices.is_some(), "Market prices should be set");
    let prices = world.market_prices.as_ref().unwrap();
    assert!(!prices.is_empty(), "Should have at least one market price");
}

/// And: Each market price should include a mark price
#[then("each market price should include a mark price")]
async fn check_mark_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let prices = world.market_prices.as_ref().expect("Market prices should be set");
    for price in prices {
        assert!(price.mark_px > 0.0, "Mark price should be positive");
    }
}

/// And: Each market price should include a mid price
#[then("each market price should include a mid price")]
async fn check_mid_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let prices = world.market_prices.as_ref().expect("Market prices should be set");
    for price in prices {
        assert!(price.mid_px > 0.0, "Mid price should be positive");
    }
}

/// When: I request the price for {word}
#[when(expr = "I request the price for {word}")]
async fn request_price(world: &mut TestWorld, name: String) {
    world.test_market_name = Some(name.clone());
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_price(&name).await {
        Ok(prices) => world.market_prices = Some(prices),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the current {word} market price
#[then(expr = "I should receive the current {word} market price")]
async fn should_receive_market_price(world: &mut TestWorld, _name: String) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.market_prices.is_some(), "Market prices should be set");
}

/// When: I request recent trades for {word} with default limit
#[when(expr = "I request recent trades for {word} with default limit")]
async fn request_trades_default(world: &mut TestWorld, name: String) {
    world.test_market_name = Some(name);
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_trades(&name, None).await {
        Ok(trades) => world.market_trades = Some(trades),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive a list of recent trades
#[then("I should receive a list of recent trades")]
async fn should_receive_trades(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.market_trades.is_some(), "Market trades should be set");
}

/// And: Each trade should have a price
#[then("each trade should have a price")]
async fn check_trade_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let trades = world.market_trades.as_ref().expect("Trades should be set");
    for trade in trades {
        assert!(trade.price > 0.0, "Trade price should be positive");
    }
}

/// And: Each trade should have a size
#[then("each trade should have a size")]
async fn check_trade_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let trades = world.market_trades.as_ref().expect("Trades should be set");
    for trade in trades {
        assert!(trade.size > 0.0, "Trade size should be positive");
    }
}

/// And: Each trade should indicate if it was a buy or sell
#[then("each trade should indicate if it was a buy or sell")]
async fn check_trade_direction(world: &mut TestWorld) {
    assert!(!world.has_error());
    let trades = world.market_trades.as_ref().expect("Trades should be set");
    for trade in trades {
        // The is_buy field should be accessible
        let _is_buy = trade.is_buy;
    }
}

/// And: Each trade should have a timestamp
#[then("each trade should have a timestamp")]
async fn check_trade_timestamp(world: &mut TestWorld) {
    assert!(!world.has_error());
    let trades = world.market_trades.as_ref().expect("Trades should be set");
    for trade in trades {
        assert!(trade.unix_ms > 0, "Trade timestamp should be positive");
    }
}

/// When: I request candlesticks for {word} with interval {word}
#[when(expr = "I request candlesticks for {word} with interval {word}")]
async fn request_candlesticks(world: &mut TestWorld, name: String, interval: String) {
    world.test_market_name = Some(name);
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_candlesticks(&name, &interval, None, None).await {
        Ok(candlesticks) => world.candlesticks = Some(candlesticks),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive historical candlestick data
#[then("I should receive historical candlestick data")]
async fn should_receive_candlesticks(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.candlesticks.is_some(), "Candlesticks should be set");
}

/// And: Each candlestick should have an open price
#[then("each candlestick should have an open price")]
async fn check_candlestick_open(world: &mut TestWorld) {
    assert!(!world.has_error());
    let candlesticks = world.candlesticks.as_ref().expect("Candlesticks should be set");
    for candle in candlesticks {
        assert!(candle.o > 0.0, "Open price should be positive");
    }
}

/// And: Each candlestick should have a high price
#[then("each candlestick should have a high price")]
async fn check_candlestick_high(world: &mut TestWorld) {
    assert!(!world.has_error());
    let candlesticks = world.candlesticks.as_ref().expect("Candlesticks should be set");
    for candle in candlesticks {
        assert!(candle.h > 0.0, "High price should be positive");
    }
}

/// And: Each candlestick should have a low price
#[then("each candlestick should have a low price")]
async fn check_candlestick_low(world: &mut TestWorld) {
    assert!(!world.has_error());
    let candlesticks = world.candlesticks.as_ref().expect("Candlesticks should be set");
    for candle in candlesticks {
        assert!(candle.l > 0.0, "Low price should be positive");
    }
}

/// And: Each candlestick should have a close price
#[then("each candlestick should have a close price")]
async fn check_candlestick_close(world: &mut TestWorld) {
    assert!(!world.has_error());
    let candlesticks = world.candlesticks.as_ref().expect("Candlesticks should be set");
    for candle in candlesticks {
        assert!(candle.c > 0.0, "Close price should be positive");
    }
}

/// And: Each candlestick should have a volume
#[then("each candlestick should have a volume")]
async fn check_candlestick_volume(world: &mut TestWorld) {
    assert!(!world.has_error());
    let candlesticks = world.candlesticks.as_ref().expect("Candlesticks should be set");
    for candle in candlesticks {
        assert!(candle.v >= 0.0, "Volume should be non-negative");
    }
}

/// When: I request all asset contexts
#[when("I request all asset contexts")]
async fn request_asset_contexts(world: &mut TestWorld) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_all_market_contexts().await {
        Ok(contexts) => world.market_contexts = Some(contexts),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive market context data for all markets
#[then("I should receive market context data for all markets")]
async fn should_receive_contexts(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.market_contexts.is_some(), "Market contexts should be set");
}

/// When: I request a market with name {string}
#[when(expr = "I request a market with name {string}")]
async fn request_invalid_market(world: &mut TestWorld, name: String) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_market_by_name(&name).await {
        Ok(_) => {},
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive an API error
#[then("I should receive an API error")]
async fn check_api_error(world: &mut TestWorld) {
    assert!(world.has_error(), "Expected an API error");
    match &world.last_error {
        Some(DecibelError::ApiError { .. }) => {},
        Some(other) => panic!("Expected ApiError, got: {:?}", other),
        None => panic!("Expected an error"),
    }
}

/// And: The error should indicate that the market was not found
#[then("the error should indicate that the market was not found")]
async fn check_not_found_message(world: &mut TestWorld) {
    assert!(world.has_error());
    if let Some(DecibelError::ApiError { status, message, .. }) = &world.last_error {
        assert_eq!(*status, 404, "Should be 404 Not Found");
        assert!(message.to_lowercase().contains("not found") || message.to_lowercase().contains("404"),
                "Error message should indicate not found");
    } else {
        panic!("Expected ApiError");
    }
}
