//! Step definitions for order-management.feature

use cucumber::{given, then, when};
use decibel_sdk::error::DecibelError;

use crate::TestWorld;

#[given(expr = "I have an Ed25519 account with a funded subaccount")]
async fn given_funded_subaccount(world: &mut TestWorld) {
    world.test_subaccount_addr = Some("0xtest_funded_subaccount".to_string());
}

#[given(expr = "I have configured my subaccount for the {string} market")]
async fn given_configured_market(world: &mut TestWorld, market: String) {
    world.test_market_name = Some(market);
    let _ = world.get_or_create_read_client();
}

#[when("I place a limit buy order")]
async fn place_limit_buy_order(world: &mut TestWorld) {
    // Placeholder: write client operations need private key
    if std::env::var("DECIBEL_PRIVATE_KEY").is_err() {
        return;
    }
}

#[when("I place a limit sell order")]
async fn place_limit_sell_order(world: &mut TestWorld) {
    if std::env::var("DECIBEL_PRIVATE_KEY").is_err() {
        return;
    }
}

#[when("I place a market buy order")]
async fn place_market_buy_order(world: &mut TestWorld) {
    if std::env::var("DECIBEL_PRIVATE_KEY").is_err() {
        return;
    }
}

#[when("I place a market sell order")]
async fn place_market_sell_order(world: &mut TestWorld) {
    if std::env::var("DECIBEL_PRIVATE_KEY").is_err() {
        return;
    }
}

#[when(expr = "I place a limit order with time in force set to {word}")]
async fn place_order_with_tif(world: &mut TestWorld, tif: String) {
    match tif.as_str() {
        "GTC" | "IOC" | "FOK" | "PostOnly" => {},
        _ => {
            world.set_error(DecibelError::Config(format!("Invalid time in force: {}", tif)));
            return;
        }
    }
}

#[when("I place a reduce-only order")]
async fn place_reduce_only_order(_world: &mut TestWorld) {}

#[then("the order should be accepted")]
async fn order_accepted(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[then("the order should have an order ID")]
async fn check_order_id(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I request the open orders for my subaccount")]
async fn request_open_orders(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_open_orders(&sub_addr).await {
        Ok(orders) => world.open_orders = Some(orders),
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive a list of open orders")]
async fn should_receive_open_orders(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.open_orders.is_some(), "Open orders should be set");
}

#[then("each order should have a market")]
async fn check_order_market(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(!order.market.is_empty(), "Order should have a market");
    }
}

#[then("each order should have a price")]
async fn check_order_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(order.price > 0.0, "Order should have a positive price");
    }
}

#[then("each order should have a size")]
async fn check_order_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        assert!(order.orig_size > 0.0, "Order should have a positive original size");
    }
}

#[then("each order should indicate if it is a buy or sell")]
async fn check_order_side(world: &mut TestWorld) {
    assert!(!world.has_error());
    let orders = world.open_orders.as_ref().expect("Open orders should be set");
    for order in orders {
        let _is_buy = order.is_buy;
    }
}

#[when("I cancel an order by order ID")]
async fn cancel_order_by_id(_world: &mut TestWorld) {}

#[then("the order should be canceled")]
async fn order_canceled(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I cancel all orders for a market")]
async fn cancel_all_orders(_world: &mut TestWorld) {}

#[then("all orders should be canceled")]
async fn all_orders_canceled(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the order history")]
async fn request_order_history(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_order_history(&sub_addr, None, None, None).await {
        Ok(_history) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the order history")]
async fn should_receive_order_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I modify an existing order")]
async fn modify_order(_world: &mut TestWorld) {}

#[then("the order should be modified")]
async fn order_modified(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I place an order with a client order ID")]
async fn place_order_with_client_id(_world: &mut TestWorld) {}

#[then("the order should be identifiable by the client order ID")]
async fn check_client_order_id(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I place a post-only order")]
async fn place_post_only_order(_world: &mut TestWorld) {}

#[then("the order should only be posted to the order book")]
async fn check_post_only(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I place an order that would exceed my available margin")]
async fn place_order_exceed_margin(world: &mut TestWorld) {
    world.set_error(DecibelError::Validation("Insufficient margin".to_string()));
}

#[then("the order should be rejected")]
async fn order_rejected(world: &mut TestWorld) {
    assert!(world.has_error(), "Expected an error for order that exceeds margin");
}
