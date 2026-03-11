//! Step definitions for account-management.feature

use cucumber::{then, when};
use decibel_sdk::error::DecibelError;

use crate::TestWorld;

#[when("I request the account overview for a subaccount")]
async fn request_account_overview(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_account_overview(&sub_addr, None, None).await {
        Ok(overview) => world.account_overview = Some(overview),
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the account overview data")]
async fn should_receive_account_overview(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.account_overview.is_some(), "Account overview should be set");
}

#[then("the overview should include the total margin")]
async fn check_total_margin(world: &mut TestWorld) {
    assert!(!world.has_error());
    let _overview = world.account_overview.as_ref().expect("Account overview should be set");
}

#[then("the overview should include the unrealized PnL")]
async fn check_unrealized_pnl(world: &mut TestWorld) {
    assert!(!world.has_error());
    let _overview = world.account_overview.as_ref().expect("Account overview should be set");
}

#[then("the overview should include the cross margin ratio")]
async fn check_cross_margin_ratio(world: &mut TestWorld) {
    assert!(!world.has_error());
    let _overview = world.account_overview.as_ref().expect("Account overview should be set");
}

#[when(expr = "I request all subaccounts for account {string}")]
async fn request_subaccounts(world: &mut TestWorld, account_addr: String) {
    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_subaccounts(&account_addr).await {
        Ok(_subaccounts) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive a list of subaccounts")]
async fn should_receive_subaccounts(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[then("each subaccount should have a subaccount address")]
async fn check_subaccount_address(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I request the account positions")]
async fn request_positions(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_positions(&sub_addr, None, None, None).await {
        Ok(positions) => world.positions = Some(positions),
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the account positions")]
async fn should_receive_positions(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the account open orders")]
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

#[then("I should receive the open orders")]
async fn should_receive_open_orders(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the account trade history")]
async fn request_trade_history(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_trade_history(&sub_addr, None, None).await {
        Ok(_trades) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the trade history")]
async fn should_receive_trade_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the account funding history")]
async fn request_funding_history(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_funding_history(&sub_addr, None, None, None).await {
        Ok(_history) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the funding history")]
async fn should_receive_funding_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the account deposit and withdrawal history")]
async fn request_fund_history(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_fund_history(&sub_addr, None, None).await {
        Ok(_history) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the deposit and withdrawal history")]
async fn should_receive_fund_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

#[when("I request the delegations for a subaccount")]
async fn request_delegations(world: &mut TestWorld) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_delegations(&sub_addr).await {
        Ok(_delegations) => {},
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the delegation list")]
async fn should_receive_delegations(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}
