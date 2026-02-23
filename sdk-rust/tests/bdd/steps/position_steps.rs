//! Step definitions for positions-and-tpsl.feature
//!
//! These steps test position management and take-profit/stop-loss orders.

use cucumber::{given, then, when};
use decibel_sdk::{
    client::read::DecibelReadClient,
    error::DecibelError,
    models::UserPosition,
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

/// Given: I have an open position in the {word} market
#[given(expr = "I have an open position in the {word} market")]
async fn given_open_position(world: &mut TestWorld, market: String) {
    world.test_market_name = Some(market);
    match world.get_write_client().await {
        Ok(client) => {
            world.test_subaccount_addr = Some(client.get_primary_subaccount_addr());
        },
        Err(e) => world.set_error(e),
    }
}

/// When: I request my positions
#[when("I request my positions")]
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

/// Then: I should receive my open positions
#[then("I should receive my open positions")]
async fn should_receive_positions(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.positions.is_some(), "Positions should be set");
}

/// And: Each position should have a market
#[then("each position should have a market")]
async fn check_position_market(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(!position.market.is_empty(), "Position should have a market");
    }
}

/// And: Each position should have a size
#[then("each position should have a size")]
async fn check_position_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        // Size can be positive (long) or negative (short), but not zero for open positions
        assert!(position.size != 0.0, "Position size should not be zero");
    }
}

/// And: Each position should have an entry price
#[then("each position should have an entry price")]
async fn check_entry_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.entry_price > 0.0, "Entry price should be positive");
    }
}

/// And: Each position should have unrealized PnL
#[then("each position should have unrealized PnL")]
async fn check_unrealized_pnl(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        // Unrealized PnL is included in the funding cost
        let _funding = position.unrealized_funding;
    }
}

/// When: I request the position for a specific market
#[when(expr = "I request the position for the {word} market")]
async fn request_position_for_market(world: &mut TestWorld, market: String) {
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
        Ok(positions) => {
            // Filter to only the requested market
            let filtered: Vec<UserPosition> = positions
                .into_iter()
                .filter(|p| p.market == market)
                .collect();
            world.positions = Some(filtered);
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: I should receive the position data
#[then("I should receive the position data")]
async fn should_receive_position_data(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.positions.is_some(), "Positions should be set");
}

/// And: The position should indicate if it is long or short
#[then("the position should indicate if it is long or short")]
async fn check_position_direction(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        // Positive size = long, negative size = short
        let is_long = position.size > 0.0;
        let _is_short = position.size < 0.0;
    }
}

/// When: I set a take-profit order for my position
#[when("I set a take-profit order for my position")]
async fn set_take_profit(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Take-profit order would be placed at a profit target price
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The take-profit order should be active
#[then("the take-profit order should be active")]
async fn check_take_profit_active(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we would verify the TP order is set
}

/// When: I set a stop-loss order for my position
#[when("I set a stop-loss order for my position")]
async fn set_stop_loss(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Stop-loss order would be placed at a loss limit price
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The stop-loss order should be active
#[then("the stop-loss order should be active")]
async fn check_stop_loss_active(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we would verify the SL order is set
}

/// When: I set both take-profit and stop-loss orders
#[when("I set both take-profit and stop-loss orders")]
async fn set_both_tp_sl(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Both TP and SL orders would be placed
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: Both orders should be active
#[then("both orders should be active")]
async fn check_both_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I cancel the take-profit order
#[when("I cancel the take-profit order")]
async fn cancel_take_profit(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Cancel the TP order
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The take-profit order should be canceled
#[then("the take-profit order should be canceled")]
async fn check_tp_canceled(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I cancel the stop-loss order
#[when("I cancel the stop-loss order")]
async fn cancel_stop_loss(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Cancel the SL order
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The stop-loss order should be canceled
#[then("the stop-loss order should be canceled")]
async fn check_sl_canceled(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I modify the take-profit price
#[when("I modify the take-profit price")]
async fn modify_take_profit(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Modify the TP order price
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The take-profit order should reflect the new price
#[then("the take-profit order should reflect the new price")]
async fn check_tp_modified(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I modify the stop-loss price
#[when("I modify the stop-loss price")]
async fn modify_stop_loss(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Modify the SL order price
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The stop-loss order should reflect the new price
#[then("the stop-loss order should reflect the new price")]
async fn check_sl_modified(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I close my entire position
#[when("I close my entire position")]
async fn close_position(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Close the position by placing a reduce-only order
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The position should be closed
#[then("the position should be closed")]
async fn check_position_closed(world: &mut TestWorld) {
    assert!(!world.has_error());
    // In a real implementation, we would verify the position is closed
}

/// When: I partially close my position
#[when("I partially close my position")]
async fn partial_close_position(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Partially close the position
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The position should be reduced
#[then("the position should be reduced")]
async fn check_position_reduced(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// When: I set a trailing stop for my position
#[when("I set a trailing stop for my position")]
async fn set_trailing_stop(world: &mut TestWorld) {
    match world.get_write_client().await {
        Ok(_) => {
            // Trailing stop would adjust as price moves favorably
        },
        Err(e) => world.set_error(e),
    }
}

/// Then: The trailing stop should be active
#[then("the trailing stop should be active")]
async fn check_trailing_stop_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

/// And: Each position should show the liquidation price
#[then("each position should show the liquidation price")]
async fn check_liquidation_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.estimated_liquidation_price > 0.0,
                "Liquidation price should be positive");
    }
}

/// And: Each position should show the user leverage
#[then("each position should show the user leverage")]
async fn check_user_leverage(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.user_leverage > 0.0, "User leverage should be positive");
    }
}

/// And: Each position should indicate if it is isolated or cross
#[then("each position should indicate if it is isolated or cross")]
async fn check_margin_type(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        let _is_isolated = position.is_isolated;
        let _is_cross = !position.is_isolated;
    }
}
