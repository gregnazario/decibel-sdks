//! Test world/context for BDD tests
//!
//! This module defines the TestWorld struct that maintains state across
//! Gherkin scenario steps, including SDK clients, responses, and test data.

use cucumber::World as CucumberWorld;
use decibel_sdk::{
    client::{read::DecibelReadClient, write::DecibelWriteClient},
    config::DecibelConfig,
    models::{
        market_data::{PerpMarketConfig, MarketDepth, MarketPrice, Candlestick, MarketTrade, MarketContext},
        account::AccountOverview,
        order::UserOpenOrder,
        position::UserPosition,
    },
    error::DecibelError,
};
use std::sync::Arc;
use tokio::sync::Mutex;

/// The test world maintains state across scenario steps
#[derive(CucumberWorld)]
pub struct TestWorld {
    /// The read client for API calls (no private key required)
    pub read_client: Option<DecibelReadClient>,
    /// The write client for on-chain transactions (requires private key)
    pub write_client: Option<DecibelWriteClient>,
    /// Current configuration being used
    pub config: Option<DecibelConfig>,
    /// Last error encountered (for testing error scenarios)
    pub last_error: Option<DecibelError>,
    /// Last response from market data queries
    pub markets: Option<Vec<PerpMarketConfig>>,
    pub market_depth: Option<MarketDepth>,
    pub market_prices: Option<Vec<MarketPrice>>,
    pub candlesticks: Option<Vec<Candlestick>>,
    pub market_trades: Option<Vec<MarketTrade>>,
    pub market_contexts: Option<Vec<MarketContext>>,
    /// Last response from account queries
    pub account_overview: Option<AccountOverview>,
    pub positions: Option<Vec<UserPosition>>,
    pub open_orders: Option<Vec<UserOpenOrder>>,
    /// Test data storage
    pub test_market_name: Option<String>,
    pub test_subaccount_addr: Option<String>,
    pub test_market_addr: Option<String>,
}

impl TestWorld {
    /// Create a new empty test world
    pub fn new() -> Self {
        Self {
            read_client: None,
            write_client: None,
            config: None,
            last_error: None,
            markets: None,
            market_depth: None,
            market_prices: None,
            candlesticks: None,
            market_trades: None,
            market_contexts: None,
            account_overview: None,
            positions: None,
            open_orders: None,
            test_market_name: None,
            test_subaccount_addr: None,
            test_market_addr: None,
        }
    }

    /// Initialize with testnet configuration
    pub fn with_testnet_config() -> Self {
        let config = DecibelConfig::testnet();
        Self {
            config: Some(config.clone()),
            ..Self::new()
        }
    }

    /// Get or create a read client
    pub async fn get_read_client(&mut self) -> Result<&DecibelReadClient, DecibelError> {
        if self.read_client.is_none() {
            let config = self.config.clone().unwrap_or_else(|| DecibelConfig::testnet());
            let api_key = std::env::var("DECIBEL_API_KEY").ok();
            self.read_client = Some(DecibelReadClient::new(config, api_key.as_deref()).await?);
        }
        Ok(self.read_client.as_ref().unwrap())
    }

    /// Get or create a write client
    pub async fn get_write_client(&mut self) -> Result<&DecibelWriteClient, DecibelError> {
        if self.write_client.is_none() {
            let config = self.config.clone().unwrap_or_else(|| DecibelConfig::testnet());
            let private_key = std::env::var("DECIBEL_PRIVATE_KEY")
                .expect("DECIBEL_PRIVATE_KEY must be set for write operations");
            self.write_client = Some(DecibelWriteClient::new(config, &private_key).await?);
        }
        Ok(self.write_client.as_ref().unwrap())
    }

    /// Store an error for testing
    pub fn set_error(&mut self, error: DecibelError) {
        self.last_error = Some(error);
    }

    /// Check if an error occurred
    pub fn has_error(&self) -> bool {
        self.last_error.is_some()
    }

    /// Clear stored data between scenarios
    pub fn clear(&mut self) {
        self.last_error = None;
        self.markets = None;
        self.market_depth = None;
        self.market_prices = None;
        self.candlesticks = None;
        self.market_trades = None;
        self.market_contexts = None;
        self.account_overview = None;
        self.positions = None;
        self.open_orders = None;
    }
}

impl Default for TestWorld {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper macro to assert an error occurred
#[macro_export]
macro_rules! assert_error {
    ($world:expr) => {
        assert!($world.has_error(), "Expected an error but none occurred");
    };
}

/// Helper macro to assert no error occurred
#[macro_export]
macro_rules! assert_no_error {
    ($world:expr) => {
        assert!(!$world.has_error(), "Unexpected error: {:?}", $world.last_error);
    };
}

/// Helper macro to assert an error of a specific type
#[macro_export]
macro_rules! assert_error_type {
    ($world:expr, $error_type:pat) => {
        match &$world.last_error {
            Some($error_type) => {},
            Some(other) => panic!("Expected error type {}, got {:?}", stringify!($error_type), other),
            None => panic!("Expected an error but none occurred"),
        }
    };
}
