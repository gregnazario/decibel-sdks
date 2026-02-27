//! Test world/context for BDD tests

use cucumber::World as CucumberWorld;
use decibel_sdk::{
    client::read::DecibelReadClient,
    config::DecibelConfig,
    models::{
        PerpMarketConfig, MarketDepth, MarketPrice, Candlestick, MarketTrade, MarketContext,
        AccountOverview,
        UserOpenOrder,
        UserPosition,
    },
    error::DecibelError,
};

/// The test world maintains state across scenario steps
#[derive(Default, CucumberWorld)]
pub struct TestWorld {
    #[world(skip)]
    pub read_client: Option<DecibelReadClient>,
    pub config: Option<DecibelConfig>,
    #[world(skip)]
    pub last_error: Option<DecibelError>,
    pub markets: Option<Vec<PerpMarketConfig>>,
    pub market_depth: Option<MarketDepth>,
    pub market_prices: Option<Vec<MarketPrice>>,
    pub candlesticks: Option<Vec<Candlestick>>,
    pub market_trades: Option<Vec<MarketTrade>>,
    pub market_contexts: Option<Vec<MarketContext>>,
    pub account_overview: Option<AccountOverview>,
    pub positions: Option<Vec<UserPosition>>,
    pub open_orders: Option<Vec<UserOpenOrder>>,
    pub test_market_name: Option<String>,
    pub test_subaccount_addr: Option<String>,
    pub test_market_addr: Option<String>,
}

impl std::fmt::Debug for TestWorld {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TestWorld")
            .field("has_read_client", &self.read_client.is_some())
            .field("has_error", &self.last_error.is_some())
            .field("test_market_name", &self.test_market_name)
            .finish()
    }
}

impl TestWorld {
    pub fn get_or_create_read_client(&mut self) -> Result<&DecibelReadClient, DecibelError> {
        if self.read_client.is_none() {
            let config = self.config.clone().unwrap_or_else(decibel_sdk::config::testnet_config);
            let api_key = std::env::var("DECIBEL_API_KEY").ok();
            self.read_client = Some(DecibelReadClient::new(config, api_key, None)?);
        }
        Ok(self.read_client.as_ref().unwrap())
    }

    pub fn set_error(&mut self, error: DecibelError) {
        self.last_error = Some(error);
    }

    pub fn has_error(&self) -> bool {
        self.last_error.is_some()
    }

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
