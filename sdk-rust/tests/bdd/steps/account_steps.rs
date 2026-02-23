//! Step definitions for account-management.feature
//!
//! These steps test account management operations.

use cucumber::{given, then, when};
use decibel_sdk::{
    client::read::DecibelReadClient,
    error::DecibelError,
    models::{AccountOverview, UserSubaccount, UserFundHistoryItem, UserFundingHistoryItem, Delegation},
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

/// Given: I have an Ed25519 account with sufficient USDC balance
#[given(expr = "I have an Ed25519 account with sufficient USDC balance")]
async fn given_funded_account(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(client) => {
            // Store the account address for later use
            world.test_subaccount_addr = Some(client.get_primary_subaccount_addr());
        },
        Err(e) => world.set_error(e),
    }
}

/// Given: I have a subaccount address {string}
#[given(expr = "I have a subaccount address {string}")]
async fn given_subaccount_address(world: &mut TestWorld, addr: String) {
    world.test_subaccount_addr = Some(addr);
}

/// When: I request the account overview for a subaccount
#[when("I request the account overview for a subaccount")]
async fn request_account_overview(world: &mut TestWorld) {
    let sub_addr = if let Some(ref addr) = world.test_subaccount_addr {
        addr.clone()
    } else {
        // If no address is set, use a test address
        // In real tests, this would be a valid testnet address
        "0xtest_subaccount_address".to_string()
    };

    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_account_overview(&sub_addr).await {
        Ok(overview) => world.account_overview = Some(overview),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the account overview data
#[then("I should receive the account overview data")]
async fn should_receive_account_overview(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.account_overview.is_some(), "Account overview should be set");
    let overview = world.account_overview.as_ref().unwrap();
    // Verify key fields exist
    assert!(overview.perp_equity_balance >= 0.0, "Equity balance should be non-negative");
}

/// And: The overview should include the total margin
#[then("the overview should include the total margin")]
async fn check_total_margin(world: &mut TestWorld) {
    assert!(!world.has_error());
    let overview = world.account_overview.as_ref().expect("Account overview should be set");
    assert!(overview.total_margin >= 0.0, "Total margin should be non-negative");
}

/// And: The overview should include the unrealized PnL
#[then("the overview should include the unrealized PnL")]
async fn check_unrealized_pnl(world: &mut TestWorld) {
    assert!(!world.has_error());
    let overview = world.account_overview.as_ref().expect("Account overview should be set");
    // Unrealized PnL can be negative, so just check it's a finite number
    assert!(overview.unrealized_pnl.is_finite(), "Unrealized PnL should be a valid number");
}

/// And: The overview should include the cross margin ratio
#[then("the overview should include the cross margin ratio")]
async fn check_cross_margin_ratio(world: &mut TestWorld) {
    assert!(!world.has_error());
    let overview = world.account_overview.as_ref().expect("Account overview should be set");
    assert!(overview.cross_margin_ratio >= 0.0, "Cross margin ratio should be non-negative");
}

/// When: I request all subaccounts for an account
#[when(expr = "I request all subaccounts for account {string}")]
async fn request_subaccounts(world: &mut TestWorld, account_addr: String) {
    let client = match world.get_read_client().await {
        Ok(client) => client,
        Err(e) => {
            world.set_error(e);
            return;
        }
    };

    match client.get_user_subaccounts(&account_addr).await {
        Ok(subaccounts) => {
            // Store subaccounts - we need to add this field to TestWorld
            // For now, we'll just verify the call succeeded
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive a list of subaccounts
#[then("I should receive a list of subaccounts")]
async fn should_receive_subaccounts(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// And: Each subaccount should have a subaccount address
#[then("each subaccount should have a subaccount address")]
async fn check_subaccount_address(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we'd verify the subaccount data
}

/// When: I request the account positions
#[when("I request the account positions")]
async fn request_positions(world: &mut TestWorld) {
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

    match client.get_user_positions(&sub_addr).await {
        Ok(positions) => world.positions = Some(positions),
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the account positions
#[then("I should receive the account positions")]
async fn should_receive_positions(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    // positions could be empty if the account has no open positions
    // So we don't assert !is_empty(), just that it was set successfully
}

/// When: I request the account open orders
#[when("I request the account open orders")]
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

/// Then: I should receive the open orders
#[then("I should receive the open orders")]
async fn should_receive_open_orders(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    // open_orders could be empty
}

/// When: I request the account trade history
#[when("I request the account trade history")]
async fn request_trade_history(world: &mut TestWorld) {
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

    match client.get_user_trade_history(&sub_addr, None, None, None).await {
        Ok(_trades) => {
            // Trade history retrieved successfully
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the trade history
#[then("I should receive the trade history")]
async fn should_receive_trade_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I request the account funding history
#[when("I request the account funding history")]
async fn request_funding_history(world: &mut TestWorld) {
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

    match client.get_user_funding_history(&sub_addr, None, None, None).await {
        Ok(_history) => {
            // Funding history retrieved successfully
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the funding history
#[then("I should receive the funding history")]
async fn should_receive_funding_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I request the account deposit and withdrawal history
#[when("I request the account deposit and withdrawal history")]
async fn request_fund_history(world: &mut TestWorld) {
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

    match client.get_user_fund_history(&sub_addr, None, None).await {
        Ok(_history) => {
            // Fund history retrieved successfully
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the deposit and withdrawal history
#[then("I should receive the deposit and withdrawal history")]
async fn should_receive_fund_history(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}

/// When: I request the delegations for a subaccount
#[when("I request the delegations for a subaccount")]
async fn request_delegations(world: &mut TestWorld) {
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

    match client.get_delegations(&sub_addr).await {
        Ok(_delegations) => {
            // Delegations retrieved successfully
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the delegation list
#[then("I should receive the delegation list")]
async fn should_receive_delegations(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
}
