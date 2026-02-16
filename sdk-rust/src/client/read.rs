use std::sync::Arc;

use crate::config::DecibelConfig;
use crate::error::{ApiResponse, DecibelError, Result};
use crate::models::*;
use crate::client::ws::WebSocketManager;

pub struct DecibelReadClient {
    config: DecibelConfig,
    http: reqwest::Client,
    ws: Arc<WebSocketManager>,
    api_key: Option<String>,
    usdc_decimals_cache: tokio::sync::OnceCell<u32>,
}

impl DecibelReadClient {
    pub fn new(
        config: DecibelConfig,
        api_key: Option<String>,
        on_ws_error: Option<Arc<dyn Fn(String) + Send + Sync>>,
    ) -> Result<Self> {
        config.validate()?;

        let http = reqwest::Client::builder()
            .pool_max_idle_per_host(10)
            .build()
            .map_err(|e| DecibelError::Network(e))?;

        let ws = Arc::new(WebSocketManager::new(
            config.clone(),
            api_key.clone(),
            on_ws_error,
        ));

        Ok(Self {
            config,
            http,
            ws,
            api_key,
            usdc_decimals_cache: tokio::sync::OnceCell::new(),
        })
    }

    fn api_url(&self, path: &str) -> String {
        format!("{}/api/v1{}", self.config.trading_http_url, path)
    }

    async fn get<T: serde::de::DeserializeOwned>(
        &self,
        path: &str,
        query_params: &[(String, String)],
    ) -> Result<ApiResponse<T>> {
        let url = self.api_url(path);
        let mut req = self.http.get(&url);

        if let Some(ref key) = self.api_key {
            req = req.header("x-api-key", key);
        }

        if !query_params.is_empty() {
            req = req.query(query_params);
        }

        let response = req.send().await.map_err(DecibelError::Network)?;
        let status = response.status();
        let status_text = status.to_string();

        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(DecibelError::Api {
                status: status.as_u16(),
                status_text: status_text.clone(),
                message: body,
            });
        }

        let data: T = response.json().await.map_err(DecibelError::Network)?;

        Ok(ApiResponse {
            data,
            status: status.as_u16(),
            status_text,
        })
    }

    // --- Markets ---

    pub async fn get_all_markets(&self) -> Result<Vec<PerpMarketConfig>> {
        let resp: ApiResponse<Vec<PerpMarketConfig>> = self.get("/markets", &[]).await?;
        Ok(resp.data)
    }

    pub async fn get_market_by_name(&self, name: &str) -> Result<PerpMarketConfig> {
        let resp: ApiResponse<PerpMarketConfig> =
            self.get(&format!("/markets/{}", name), &[]).await?;
        Ok(resp.data)
    }

    // --- Market Contexts ---

    pub async fn get_all_market_contexts(&self) -> Result<Vec<MarketContext>> {
        let resp: ApiResponse<Vec<MarketContext>> = self.get("/asset-contexts", &[]).await?;
        Ok(resp.data)
    }

    // --- Market Depth ---

    pub async fn get_market_depth(
        &self,
        market_name: &str,
        limit: Option<i32>,
    ) -> Result<MarketDepth> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        let resp: ApiResponse<MarketDepth> =
            self.get(&format!("/depth/{}", market_name), &params).await?;
        Ok(resp.data)
    }

    // --- Market Prices ---

    pub async fn get_all_market_prices(&self) -> Result<Vec<MarketPrice>> {
        let resp: ApiResponse<Vec<MarketPrice>> = self.get("/prices", &[]).await?;
        Ok(resp.data)
    }

    pub async fn get_market_price_by_name(&self, market_name: &str) -> Result<Vec<MarketPrice>> {
        let resp: ApiResponse<Vec<MarketPrice>> =
            self.get(&format!("/prices/{}", market_name), &[]).await?;
        Ok(resp.data)
    }

    // --- Market Trades ---

    pub async fn get_market_trades(
        &self,
        market_name: &str,
        limit: Option<i32>,
    ) -> Result<Vec<MarketTrade>> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        let resp: ApiResponse<Vec<MarketTrade>> =
            self.get(&format!("/trades/{}", market_name), &params).await?;
        Ok(resp.data)
    }

    // --- Candlesticks ---

    pub async fn get_candlesticks(
        &self,
        market_name: &str,
        interval: CandlestickInterval,
        start_time: i64,
        end_time: i64,
    ) -> Result<Vec<Candlestick>> {
        let params = vec![
            ("interval".to_string(), interval.as_str().to_string()),
            ("startTime".to_string(), start_time.to_string()),
            ("endTime".to_string(), end_time.to_string()),
        ];
        let resp: ApiResponse<Vec<Candlestick>> =
            self.get(&format!("/candlesticks/{}", market_name), &params).await?;
        Ok(resp.data)
    }

    // --- Account Overview ---

    pub async fn get_account_overview(
        &self,
        sub_addr: &str,
        volume_window: Option<VolumeWindow>,
        include_performance: Option<bool>,
    ) -> Result<AccountOverview> {
        let mut params = vec![];
        if let Some(w) = volume_window {
            params.push(("volume_window".to_string(), w.as_str().to_string()));
        }
        if let Some(p) = include_performance {
            params.push(("include_performance".to_string(), p.to_string()));
        }
        let resp: ApiResponse<AccountOverview> =
            self.get(&format!("/account/{}", sub_addr), &params).await?;
        Ok(resp.data)
    }

    // --- User Positions ---

    pub async fn get_user_positions(
        &self,
        sub_addr: &str,
        market_addr: Option<&str>,
        include_deleted: Option<bool>,
        limit: Option<i32>,
    ) -> Result<Vec<UserPosition>> {
        let mut params = vec![];
        if let Some(m) = market_addr {
            params.push(("market_addr".to_string(), m.to_string()));
        }
        if let Some(d) = include_deleted {
            params.push(("include_deleted".to_string(), d.to_string()));
        }
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        let resp: ApiResponse<Vec<UserPosition>> =
            self.get(&format!("/positions/{}", sub_addr), &params).await?;
        Ok(resp.data)
    }

    // --- User Open Orders ---

    pub async fn get_user_open_orders(&self, sub_addr: &str) -> Result<Vec<UserOpenOrder>> {
        let resp: ApiResponse<Vec<UserOpenOrder>> =
            self.get(&format!("/open-orders/{}", sub_addr), &[]).await?;
        Ok(resp.data)
    }

    // --- User Order History ---

    pub async fn get_user_order_history(
        &self,
        sub_addr: &str,
        market_addr: Option<&str>,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserOrderHistoryItem>> {
        let mut params = vec![];
        if let Some(m) = market_addr {
            params.push(("market_addr".to_string(), m.to_string()));
        }
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserOrderHistoryItem>> = self
            .get(&format!("/order-history/{}", sub_addr), &params)
            .await?;
        Ok(resp.data)
    }

    // --- User Trade History ---

    pub async fn get_user_trade_history(
        &self,
        sub_addr: &str,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserTradeHistoryItem>> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserTradeHistoryItem>> = self
            .get(&format!("/trade-history/{}", sub_addr), &params)
            .await?;
        Ok(resp.data)
    }

    // --- User Funding History ---

    pub async fn get_user_funding_history(
        &self,
        sub_addr: &str,
        market_addr: Option<&str>,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserFundingHistoryItem>> {
        let mut params = vec![];
        if let Some(m) = market_addr {
            params.push(("market_addr".to_string(), m.to_string()));
        }
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserFundingHistoryItem>> = self
            .get(&format!("/funding-history/{}", sub_addr), &params)
            .await?;
        Ok(resp.data)
    }

    // --- User Fund History ---

    pub async fn get_user_fund_history(
        &self,
        sub_addr: &str,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserFundHistoryItem>> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserFundHistoryItem>> = self
            .get(&format!("/fund-history/{}", sub_addr), &params)
            .await?;
        Ok(resp.data)
    }

    // --- Subaccounts ---

    pub async fn get_user_subaccounts(&self, owner_addr: &str) -> Result<Vec<UserSubaccount>> {
        let resp: ApiResponse<Vec<UserSubaccount>> =
            self.get(&format!("/subaccounts/{}", owner_addr), &[]).await?;
        Ok(resp.data)
    }

    // --- Delegations ---

    pub async fn get_delegations(&self, sub_addr: &str) -> Result<Vec<Delegation>> {
        let resp: ApiResponse<Vec<Delegation>> =
            self.get(&format!("/delegations/{}", sub_addr), &[]).await?;
        Ok(resp.data)
    }

    // --- Active TWAPs ---

    pub async fn get_active_twaps(&self, sub_addr: &str) -> Result<Vec<UserActiveTwap>> {
        let resp: ApiResponse<Vec<UserActiveTwap>> =
            self.get(&format!("/active-twaps/{}", sub_addr), &[]).await?;
        Ok(resp.data)
    }

    // --- TWAP History ---

    pub async fn get_twap_history(
        &self,
        sub_addr: &str,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserActiveTwap>> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserActiveTwap>> = self
            .get(&format!("/twap-history/{}", sub_addr), &params)
            .await?;
        Ok(resp.data)
    }

    // --- Vaults ---

    pub async fn get_vaults(
        &self,
        page: &PageParams,
        sort: &SortParams,
        search: &SearchTermParams,
    ) -> Result<VaultsResponse> {
        let params = crate::utils::construct_query_params(page, sort, search);
        let resp: ApiResponse<VaultsResponse> = self.get("/vaults", &params).await?;
        Ok(resp.data)
    }

    pub async fn get_user_owned_vaults(
        &self,
        account_addr: &str,
        limit: Option<i32>,
        offset: Option<i32>,
    ) -> Result<PaginatedResponse<UserOwnedVault>> {
        let mut params = vec![];
        if let Some(l) = limit {
            params.push(("limit".to_string(), l.to_string()));
        }
        if let Some(o) = offset {
            params.push(("offset".to_string(), o.to_string()));
        }
        let resp: ApiResponse<PaginatedResponse<UserOwnedVault>> = self
            .get(&format!("/vaults/owned/{}", account_addr), &params)
            .await?;
        Ok(resp.data)
    }

    pub async fn get_user_performances_on_vaults(
        &self,
        account_addr: &str,
    ) -> Result<Vec<UserPerformanceOnVault>> {
        let resp: ApiResponse<Vec<UserPerformanceOnVault>> = self
            .get(&format!("/vaults/performance/{}", account_addr), &[])
            .await?;
        Ok(resp.data)
    }

    // --- Leaderboard ---

    pub async fn get_leaderboard(
        &self,
        page: &PageParams,
        sort: &SortParams,
        search: &SearchTermParams,
    ) -> Result<Leaderboard> {
        let params = crate::utils::construct_query_params(page, sort, search);
        let resp: ApiResponse<Leaderboard> = self.get("/leaderboard", &params).await?;
        Ok(resp.data)
    }

    // --- Order Status ---

    pub async fn get_order_status(
        &self,
        order_id: &str,
        market_address: &str,
        user_address: &str,
    ) -> Result<Option<OrderStatus>> {
        let params = vec![
            ("market_address".to_string(), market_address.to_string()),
            ("user_address".to_string(), user_address.to_string()),
        ];
        let result: std::result::Result<ApiResponse<OrderStatus>, _> =
            self.get(&format!("/orders/{}", order_id), &params).await;
        match result {
            Ok(resp) => Ok(Some(resp.data)),
            Err(DecibelError::Api { status: 404, .. }) => Ok(None),
            Err(e) => Err(e),
        }
    }

    // --- WebSocket Subscriptions ---

    pub fn ws(&self) -> &WebSocketManager {
        &self.ws
    }

    pub async fn subscribe_account_overview<F>(
        &self,
        sub_addr: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(AccountOverviewWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("accountOverview:{}", sub_addr);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<AccountOverviewWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_user_positions<F>(
        &self,
        sub_addr: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(UserPositionsWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("userPositions:{}", sub_addr);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<UserPositionsWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_user_open_orders<F>(
        &self,
        sub_addr: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(UserOpenOrdersWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("userOpenOrders:{}", sub_addr);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<UserOpenOrdersWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_market_depth<F>(
        &self,
        market_name: &str,
        _agg_size: MarketDepthAggregationSize,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(MarketDepth) + Send + Sync + 'static,
    {
        let topic = format!("marketDepth:{}", market_name);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<MarketDepth>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_market_price<F>(
        &self,
        market_name: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(MarketPriceWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("marketPrice:{}", market_name);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<MarketPriceWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_all_market_prices<F>(
        &self,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(AllMarketPricesWsMessage) + Send + Sync + 'static,
    {
        let topic = "allMarketPrices".to_string();
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<AllMarketPricesWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_market_trades<F>(
        &self,
        market_name: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(MarketTradesWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("marketTrades:{}", market_name);
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<MarketTradesWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }

    pub async fn subscribe_candlestick<F>(
        &self,
        market_name: &str,
        interval: CandlestickInterval,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(CandlestickWsMessage) + Send + Sync + 'static,
    {
        let topic = format!("marketCandlestick:{}:{}", market_name, interval.as_str());
        self.ws
            .subscribe(&topic, move |value| {
                if let Ok(msg) = serde_json::from_value::<CandlestickWsMessage>(value) {
                    callback(msg);
                }
            })
            .await
    }
}
