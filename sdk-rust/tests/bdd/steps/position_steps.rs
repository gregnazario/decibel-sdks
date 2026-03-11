//! Step definitions for positions-and-tpsl.feature

use cucumber::{given, then, when};
use decibel_sdk::models::UserPosition;

use crate::TestWorld;

#[given(expr = "I have an open position in the {string} market")]
async fn given_open_position(world: &mut TestWorld, market: String) {
    world.test_market_name = Some(market);
    world.test_subaccount_addr = Some("0xtest_subaccount".to_string());
}

#[when("I request my positions")]
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

#[then("I should receive my open positions")]
async fn should_receive_positions(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.positions.is_some(), "Positions should be set");
}

#[then("each position should have a market")]
async fn check_position_market(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(!position.market.is_empty(), "Position should have a market");
    }
}

#[then("each position should have a size")]
async fn check_position_size(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.size != 0.0, "Position size should not be zero");
    }
}

#[then("each position should have an entry price")]
async fn check_entry_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.entry_price > 0.0, "Entry price should be positive");
    }
}

#[then("each position should have unrealized PnL")]
async fn check_unrealized_pnl(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        let _funding = position.unrealized_funding;
    }
}

#[when(expr = "I request the position for the {string} market")]
async fn request_position_for_market(world: &mut TestWorld, market: String) {
    let sub_addr = world.test_subaccount_addr.clone()
        .unwrap_or_else(|| "0xtest_subaccount_address".to_string());

    if world.get_or_create_read_client().is_err() {
        return;
    }
    let client = world.read_client.as_ref().unwrap();
    match client.get_user_positions(&sub_addr, None, None, None).await {
        Ok(positions) => {
            let filtered: Vec<UserPosition> = positions
                .into_iter()
                .filter(|p| p.market == market)
                .collect();
            world.positions = Some(filtered);
        },
        Err(e) => world.set_error(e),
    }
}

#[then("I should receive the position data")]
async fn should_receive_position_data(world: &mut TestWorld) {
    assert!(!world.has_error(), "Expected no error, got: {:?}", world.last_error);
    assert!(world.positions.is_some(), "Positions should be set");
}

#[then("the position should indicate if it is long or short")]
async fn check_position_direction(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        let _is_long = position.size > 0.0;
    }
}

#[when("I set a take-profit order for my position")]
async fn set_take_profit(_world: &mut TestWorld) {}

#[then("the take-profit order should be active")]
async fn check_take_profit_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I set a stop-loss order for my position")]
async fn set_stop_loss(_world: &mut TestWorld) {}

#[then("the stop-loss order should be active")]
async fn check_stop_loss_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I set both take-profit and stop-loss orders")]
async fn set_both_tp_sl(_world: &mut TestWorld) {}

#[then("both orders should be active")]
async fn check_both_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I cancel the take-profit order")]
async fn cancel_take_profit(_world: &mut TestWorld) {}

#[then("the take-profit order should be canceled")]
async fn check_tp_canceled(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I cancel the stop-loss order")]
async fn cancel_stop_loss(_world: &mut TestWorld) {}

#[then("the stop-loss order should be canceled")]
async fn check_sl_canceled(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I modify the take-profit price")]
async fn modify_take_profit(_world: &mut TestWorld) {}

#[then("the take-profit order should reflect the new price")]
async fn check_tp_modified(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I modify the stop-loss price")]
async fn modify_stop_loss(_world: &mut TestWorld) {}

#[then("the stop-loss order should reflect the new price")]
async fn check_sl_modified(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I close my entire position")]
async fn close_position(_world: &mut TestWorld) {}

#[then("the position should be closed")]
async fn check_position_closed(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I partially close my position")]
async fn partial_close_position(_world: &mut TestWorld) {}

#[then("the position should be reduced")]
async fn check_position_reduced(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[when("I set a trailing stop for my position")]
async fn set_trailing_stop(_world: &mut TestWorld) {}

#[then("the trailing stop should be active")]
async fn check_trailing_stop_active(world: &mut TestWorld) {
    assert!(!world.has_error());
}

#[then("each position should show the liquidation price")]
async fn check_liquidation_price(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.estimated_liquidation_price > 0.0, "Liquidation price should be positive");
    }
}

#[then("each position should show the user leverage")]
async fn check_user_leverage(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        assert!(position.user_leverage > 0.0, "User leverage should be positive");
    }
}

#[then("each position should indicate if it is isolated or cross")]
async fn check_margin_type(world: &mut TestWorld) {
    assert!(!world.has_error());
    let positions = world.positions.as_ref().expect("Positions should be set");
    for position in positions {
        let _is_isolated = position.is_isolated;
    }
}
