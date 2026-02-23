//! BDD Test Runner for Decibel SDK
//!
//! This is the entry point for running Cucumber/Gherkin tests.
//! It uses the cucumber crate to parse feature files and execute step definitions.

use cucumber::cucumber;

// Import our test world and steps
mod bdd;

// Use the TestWorld from our bdd module
use bdd::TestWorld;

#[tokio::main]
async fn main() {
    // Set up tracing for better error output
    tracing_subscriber::fmt()
        .with_test_writer()
        .with_env_filter("decibel_sdk=debug,info")
        .init();

    // Run the cucumber tests
    // The cucumber framework will:
    // 1. Parse .feature files from the configured directory
    // 2. Match Gherkin steps to our step definitions
    // 3. Execute scenarios and report results

    TestWorld::run(|world| {
        // Set up any global test state here
        world.clear();
    }).await;
}

impl TestWorld {
    /// Run the cucumber test suite
    async fn run(setup: impl Fn(&mut Self)) {
        // The cucumber! macro expands to the test runner setup
        // We need to register all our step definitions

        cucumber::TestRunner::<TestWorld>::new(
            TestWorld::default(),
            features(),
        )
        .run(setup)
        .await;
    }
}

/// Register all feature files and step definitions
fn features() -> cucumber::Cucumber<TestWorld> {
    use cucumber::Steps;
    use bdd::steps::*;

    cucumber::Steps!()
}

// Define the features to run
cucumber::Steps! {
    // Import all step definitions so they're registered
    use bdd::steps::*;

    // Register configuration steps
    given async fn sdk_installed(_world: &mut TestWorld);
    given async fn have_ed25519_keypair(_world: &mut TestWorld);
    given async fn have_gas_station_config(_world: &mut TestWorld);
    when async fn create_read_client_with_preset(world: &mut TestWorld, preset: String);
    when async fn create_read_client_custom_config(world: &mut TestWorld);
    when async fn create_read_client_with_api_key(world: &mut TestWorld);
    when async fn create_write_client(world: &mut TestWorld);
    when async fn create_write_client_gas_station(world: &mut TestWorld);
    when async fn create_write_client_no_gas_station(world: &mut TestWorld);
    when async fn invalid_config_missing_network(world: &mut TestWorld);
    when async fn create_write_client_no_account(world: &mut TestWorld);
    when async fn init_client_with_config(world: &mut TestWorld);
    then async fn check_configured_environment(world: &mut TestWorld, env: String);
    then async fn can_sign_transactions(world: &mut TestWorld);
    then async fn uses_gas_station(world: &mut TestWorld);
    then async fn submits_directly(world: &mut TestWorld);
    then async fn check_config_error(world: &mut TestWorld);
    then async fn check_package_address(world: &mut TestWorld);
    then async fn check_compat_version(world: &mut TestWorld);
    then async fn check_chain_id_auto_detect(world: &mut TestWorld);

    // Register market data steps
    given async fn given_read_client(world: &mut TestWorld);
    when async fn request_all_markets(world: &mut TestWorld);
    when async fn request_market_by_name(world: &mut TestWorld, name: String);
    when async fn request_market_depth_no_limit(world: &mut TestWorld, name: String);
    when async fn request_market_depth_with_limit(world: &mut TestWorld, name: String, limit: i64);
    when async fn request_all_prices(world: &mut TestWorld);
    when async fn request_price(world: &mut TestWorld, name: String);
    when async fn request_trades_default(world: &mut TestWorld, name: String);
    when async fn request_candlesticks(world: &mut TestWorld, name: String, interval: String);
    when async fn request_asset_contexts(world: &mut TestWorld);
    when async fn request_invalid_market(world: &mut TestWorld, name: String);
    then async fn should_receive_markets(world: &mut TestWorld);
    then async fn should_receive_market_config(world: &mut TestWorld, name: String);
    then async fn check_market_name_value(world: &mut TestWorld, name: String);
    then async fn check_valid_market_address(world: &mut TestWorld);
    then async fn check_market_address(world: &mut TestWorld);
    then async fn check_market_name(world: &mut TestWorld);
    then async fn check_size_decimals(world: &mut TestWorld);
    then async fn check_price_decimals(world: &mut TestWorld);
    then async fn check_max_leverage(world: &mut TestWorld);
    then async fn check_min_size(world: &mut TestWorld);
    then async fn check_lot_size(world: &mut TestWorld);
    then async fn check_tick_size(world: &mut TestWorld);
    then async fn should_receive_order_book(world: &mut TestWorld);
    then async fn check_bids(world: &mut TestWorld);
    then async fn check_asks(world: &mut TestWorld);
    then async fn check_bids_sorted(world: &mut TestWorld);
    then async fn check_asks_sorted(world: &mut TestWorld);
    then async fn check_price_levels(world: &mut TestWorld);
    then async fn check_limit(world: &mut TestWorld, limit: i64);
    then async fn should_receive_all_prices(world: &mut TestWorld);
    then async fn check_mark_price(world: &mut TestWorld);
    then async fn check_mid_price(world: &mut TestWorld);
    then async fn should_receive_market_price(world: &mut TestWorld, name: String);
    then async fn should_receive_trades(world: &mut TestWorld);
    then async fn check_trade_price(world: &mut TestWorld);
    then async fn check_trade_size(world: &mut TestWorld);
    then async fn check_trade_direction(world: &mut TestWorld);
    then async fn check_trade_timestamp(world: &mut TestWorld);
    then async fn should_receive_candlesticks(world: &mut TestWorld);
    then async fn check_candlestick_open(world: &mut TestWorld);
    then async fn check_candlestick_high(world: &mut TestWorld);
    then async fn check_candlestick_low(world: &mut TestWorld);
    then async fn check_candlestick_close(world: &mut TestWorld);
    then async fn check_candlestick_volume(world: &mut TestWorld);
    then async fn should_receive_contexts(world: &mut TestWorld);
    then async fn check_api_error(world: &mut TestWorld);
    then async fn check_not_found_message(world: &mut TestWorld);
}
