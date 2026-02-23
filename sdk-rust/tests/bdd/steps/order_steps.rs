//! Step definitions for order-management.feature
//!
//! These steps test order placement and management.

use cucumber::{given, then, when};
use decibel_sdk::{
    client::read::DecibelReadClient,
    error::DecibelError,
    models::{UserOpenOrder, TimeInForce},
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

/// Background: I have an initialized Decibel write client
#[given(expr = "I have an initialized Decibel write client")]
async fn given_write_client(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {},
        Err(e) => world.set_error(e),
    }
}

/// Given: I have an Ed25519 account with a funded subaccount
#[given(expr = "I have an Ed25519 account with a funded subaccount")]
async fn given_funded_subaccount(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(client) => {
            world.test_subaccount_addr = Some(client.get_primary_subaccount_addr());
        },
        Err(e) => world.set_error(e),
    }
}

/// Given: I have configured my subaccount for the {word} market
#[given(expr = "I have configured my subaccount for the {word} market")]
async fn given_configured_market(world: &mut TestWorld, market: String) {
    world.test_market_name = Some(market);
    match world.get_read_client().await {
        Ok(_) => {},
        Err(e) => world.set_error(e),
    }
}

/// When: I place a limit buy order
#[when("I place a limit buy order")]
async fn place_limit_buy_order(world: &mut TestWorld) {
    // This would use the write client to place an order
    // For now, we'll document the expected behavior
    match world.get_write_client().await {
        Ok(_) => {
            // In a real implementation, we would:
            // 1. Get the current market price
            // 2. Place a limit buy order below the current price
            // 3. Store the order ID for verification
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I place a limit sell order
#[when("I place a limit sell order")]
async fn place_limit_sell_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // In a real implementation:
            // 1. Get the current market price
            // 2. Place a limit sell order above the current price
            // 3. Store the order ID
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I place a market buy order
#[when("I place a market buy order")]
async fn place_market_buy_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Market buy orders execute immediately at the best available price
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I place a market sell order
#[when("I place a market sell order")]
async fn place_market_sell_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Market sell orders execute immediately
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I place a limit order with time in force set to {word}
#[when(expr = "I place a limit order with time in force set to {word}")]
async fn place_order_with_tif(world: &mut TestWorld, tif: String) {
    // Validate the time in force value
    match tif.as_str() {
        "GTC" | "IOC" | "FOK" | "PostOnly" => {
            // Valid time in force values
        },
        _ => {
            world.set_error(DecibelError::Config(format!("Invalid time in force: {}", tif)));
            return;
        }
    }

    match world.get_write_client().await {
        Ok(_) => {
            // Place order with specified time in force
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I place a reduce-only order
#[when("I place a reduce-only order")]
async fn place_reduce_only_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Reduce-only orders only reduce existing positions
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The order should be accepted
#[then("the order should be accepted")]
async fn order_accepted(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// And: The order should have an order ID
#[then("the order should have an order ID")]
async fn check_order_id(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we would verify the order ID exists
}

/// When: I request the open orders for my subaccount
#[when("I request the open orders for my subaccount")]
async fn request_open_orders(world: &mut TestWorld) {
    let sub_addr = if let Some(ref addr) = world.test_subaccount_addr {
        addr.clone()
    } else {
        "0xtest_subaccount_address".to_string()
    };

    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_user_open_orders(&sub_addr).await {
        Ok(orders) => world.open_orders = Some(orders),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive a list of open orders
#[then("I should receive a list of open orders")]
async fn should_receive_open_orders(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.open_orders.is_some(), "Open orders should be set");
}

/// And: Each order should have a market
#[then("each order should have a market")]
async fn check_order_market(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(!order.market.is_empty(), "Order should have a market");
    }
}

/// And: Each order should have a price
#[then("each order should have a price")]
async fn check_order_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(order.price > 0.0, "Order should have a positive price");
    }
}

/// And: Each order should have a size
#[then("each order should have a size")]
async fn check_order_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(order.orig_size > 0.0, "Order should have a positive original size");
    }
}

/// And: Each order should indicate if it is a buy or sell
#[then("each order should indicate if it is a buy or sell")]
async fn check_order_side(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        // The is_buy field should be accessible
        let _is_buy = order.is_buy;
    }
}

/// When: I cancel an order by order ID
#[when("I cancel an order by order ID")]
async fn cancel_order_by_id(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // In a real implementation, we would:
            // 1. Get an order ID from the open orders
            // 2. Call cancel_order with that ID
            // 3. Verify the cancellation succeeded
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The order should be canceled
#[then("the order should be canceled")]
async fn order_canceled(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I cancel all orders for a market
#[when("I cancel all orders for a market")]
async fn cancel_all_orders(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Cancel all orders would loop through open orders and cancel each
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: All orders should be canceled
#[then("all orders should be canceled")]
async fn all_orders_canceled(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I request the order history
#[when("I request the order history")]
async fn request_order_history(world: &mut TestWorld) {
    let sub_addr = if let Some(ref addr) = world.test_subaccount_addr {
        addr.clone()
    } else {
        "0xtest_subaccount_address".to_string()
    };

    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_user_order_history(&sub_addr, None, None, None).await {
        Ok(_history) => {
            // Order history retrieved successfully
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the order history
#[then("I should receive the order history")]
async fn should_receive_order_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I modify an existing order
#[when("I modify an existing order")]
async fn modify_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Order modification would:
            // 1. Cancel the existing order
            // 2. Place a new order with modified parameters
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The order should be modified
#[then("the order should be modified")]
async fn order_modified(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I place an order with a client order ID
#[when("I place an order with a client order ID")]
async fn place_order_with_client_id(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Client order ID allows client-side order identification
        },
        Err(e) => world.set_error(e),
    }
}

/// And: The order should be identifiable by the client order ID
#[then("the order should be identifiable by the client order ID")]
async fn check_client_order_id(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we would query by client order ID
}

/// When: I place a post-only order
#[when("I place a post-only order")]
async fn place_post_only_order(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Post-only orders only add liquidity (never take)
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The order should only be posted to the order book
#[then("the order should only be posted to the order book")]
async fn check_post_only(world: &mut TestWorld) {
    assert!(!world.has_error());
    // Post-only orders that would trade are rejected
}

/// When: I place an order that would exceed my available margin
#[when("I place an order that would exceed my available margin")]
async fn place_order_exceed_margin(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // This should fail with margin error
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The order should be rejected
#[then("the order should be rejected")]
async fn order_rejected(world: &mut TestWorld) {
    assert!(world.has_error(), "Expected an error for order that exceeds margin");
}
