use crate::config::DecibelConfig;
use crate::error::{DecibelError, Result};
use crate::gas::GasPriceManager;
use crate::models::*;

/// Arguments for placing an order
#[derive(Debug, Clone)]
pub struct PlaceOrderArgs {
    pub market_name: String,
    pub price: f64,
    pub size: f64,
    pub is_buy: bool,
    pub time_in_force: TimeInForce,
    pub is_reduce_only: bool,
    pub client_order_id: Option<String>,
    pub stop_price: Option<f64>,
    pub tp_trigger_price: Option<f64>,
    pub tp_limit_price: Option<f64>,
    pub sl_trigger_price: Option<f64>,
    pub sl_limit_price: Option<f64>,
    pub builder_addr: Option<String>,
    pub builder_fee: Option<u64>,
    pub subaccount_addr: Option<String>,
    pub tick_size: Option<f64>,
}

/// Arguments for canceling an order
#[derive(Debug, Clone)]
pub struct CancelOrderArgs {
    pub order_id: String,
    pub market_name: Option<String>,
    pub market_addr: Option<String>,
    pub subaccount_addr: Option<String>,
}

/// Arguments for placing a TWAP order
#[derive(Debug, Clone)]
pub struct PlaceTwapOrderArgs {
    pub market_name: String,
    pub size: f64,
    pub is_buy: bool,
    pub is_reduce_only: bool,
    pub client_order_id: Option<String>,
    pub twap_frequency_seconds: u64,
    pub twap_duration_seconds: u64,
    pub builder_address: Option<String>,
    pub builder_fees: Option<u64>,
    pub subaccount_addr: Option<String>,
}

/// Arguments for placing TP/SL orders on a position
#[derive(Debug, Clone)]
pub struct PlaceTpSlArgs {
    pub market_addr: String,
    pub tp_trigger_price: Option<f64>,
    pub tp_limit_price: Option<f64>,
    pub tp_size: Option<f64>,
    pub sl_trigger_price: Option<f64>,
    pub sl_limit_price: Option<f64>,
    pub sl_size: Option<f64>,
    pub subaccount_addr: Option<String>,
    pub tick_size: Option<f64>,
}

/// Arguments for configuring user settings for a market
#[derive(Debug, Clone)]
pub struct ConfigureMarketSettingsArgs {
    pub market_addr: String,
    pub subaccount_addr: String,
    pub is_cross: bool,
    pub user_leverage: u64,
}

/// Arguments for delegation
#[derive(Debug, Clone)]
pub struct DelegateTradingArgs {
    pub subaccount_addr: String,
    pub account_to_delegate_to: String,
    pub expiration_timestamp_secs: Option<u64>,
}

/// Transaction response from on-chain operations
#[derive(Debug, Clone)]
pub struct TransactionResponse {
    pub hash: String,
    pub success: bool,
    pub vm_status: Option<String>,
    pub events: Vec<serde_json::Value>,
}

pub struct DecibelWriteClient {
    config: DecibelConfig,
    http: reqwest::Client,
    private_key: Vec<u8>,
    account_address: String,
    skip_simulate: bool,
    no_fee_payer: bool,
    _gas_price_manager: Option<GasPriceManager>,
    time_delta_ms: i64,
}

impl DecibelWriteClient {
    pub fn new(
        config: DecibelConfig,
        private_key_hex: &str,
        account_address: &str,
        skip_simulate: bool,
        no_fee_payer: bool,
        node_api_key: Option<String>,
        gas_price_manager: Option<GasPriceManager>,
        time_delta_ms: Option<i64>,
    ) -> Result<Self> {
        config.validate()?;

        let private_key = hex::decode(
            private_key_hex
                .strip_prefix("0x")
                .unwrap_or(private_key_hex),
        )
        .map_err(|e| DecibelError::Config(format!("Invalid private key hex: {}", e)))?;

        let mut client_builder = reqwest::Client::builder().pool_max_idle_per_host(10);
        if let Some(ref key) = node_api_key {
            let mut headers = reqwest::header::HeaderMap::new();
            headers.insert("x-api-key", key.parse().unwrap());
            client_builder = client_builder.default_headers(headers);
        }

        let http = client_builder
            .build()
            .map_err(|e| DecibelError::Network(e))?;

        Ok(Self {
            config,
            http,
            private_key,
            account_address: account_address.to_string(),
            skip_simulate,
            no_fee_payer,
            _gas_price_manager: gas_price_manager,
            time_delta_ms: time_delta_ms.unwrap_or(0),
        })
    }

    pub fn account_address(&self) -> &str {
        &self.account_address
    }

    pub fn get_primary_subaccount_addr(&self) -> String {
        crate::utils::get_primary_subaccount_addr(
            &self.account_address,
            "v0.4",
            &self.config.deployment.package,
        )
    }

    fn resolve_subaccount(&self, subaccount_addr: Option<&str>) -> String {
        subaccount_addr
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.get_primary_subaccount_addr())
    }

    fn get_market_addr(&self, market_name: &str) -> String {
        crate::utils::get_market_addr(
            market_name,
            &self.config.deployment.perp_engine_global,
        )
    }

    /// Build a transaction payload for a Move entry function call
    fn build_payload(
        &self,
        function: &str,
        type_args: Vec<String>,
        args: Vec<serde_json::Value>,
    ) -> serde_json::Value {
        serde_json::json!({
            "function": function,
            "type_arguments": type_args,
            "arguments": args
        })
    }

    /// Submit a transaction (placeholder - actual implementation needs Aptos SDK)
    async fn submit_transaction(
        &self,
        _payload: serde_json::Value,
    ) -> Result<TransactionResponse> {
        // In a real implementation, this would:
        // 1. Build the transaction using Aptos SDK
        // 2. Simulate if !skip_simulate
        // 3. Sign with Ed25519 private key
        // 4. Submit via fee payer or directly
        // 5. Wait for confirmation
        Err(DecibelError::Transaction {
            transaction_hash: None,
            vm_status: None,
            message: "Transaction submission requires Aptos SDK integration".into(),
        })
    }

    // --- Account Management ---

    pub async fn create_subaccount(&self) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::create_new_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![],
        );
        self.submit_transaction(payload).await
    }

    pub async fn deposit(
        &self,
        amount: u64,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::deposit_to_subaccount_at",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(self.config.deployment.usdc),
                serde_json::json!(amount),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn withdraw(
        &self,
        amount: u64,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::withdraw_from_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(self.config.deployment.usdc),
                serde_json::json!(amount),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn configure_user_settings_for_market(
        &self,
        args: ConfigureMarketSettingsArgs,
    ) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::configure_user_settings_for_market",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(args.subaccount_addr),
                serde_json::json!(args.market_addr),
                serde_json::json!(args.is_cross),
                serde_json::json!(args.user_leverage),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- Order Management ---

    pub async fn place_order(&self, args: PlaceOrderArgs) -> Result<PlaceOrderResult> {
        let market_addr = self.get_market_addr(&args.market_name);
        let sub = self.resolve_subaccount(args.subaccount_addr.as_deref());

        let mut price = args.price;
        if let Some(tick_size) = args.tick_size {
            price = crate::utils::round_to_tick_size(price, tick_size, 0, args.is_buy);
        }

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts_entry::place_order_to_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(market_addr),
                serde_json::json!(price),
                serde_json::json!(args.size),
                serde_json::json!(args.is_buy),
                serde_json::json!(args.time_in_force.as_u8()),
                serde_json::json!(args.is_reduce_only),
                serde_json::json!(args.client_order_id),
                serde_json::json!(args.stop_price),
                serde_json::json!(args.tp_trigger_price),
                serde_json::json!(args.tp_limit_price),
                serde_json::json!(args.sl_trigger_price),
                serde_json::json!(args.sl_limit_price),
                serde_json::json!(args.builder_addr),
                serde_json::json!(args.builder_fee),
            ],
        );

        match self.submit_transaction(payload).await {
            Ok(tx) => {
                let order_id =
                    crate::utils::extract_order_id_from_events(&tx.events, &sub);
                Ok(PlaceOrderResult::success(order_id, tx.hash))
            }
            Err(e) => Ok(PlaceOrderResult::failure(e.to_string())),
        }
    }

    pub async fn cancel_order(&self, args: CancelOrderArgs) -> Result<TransactionResponse> {
        let market_addr = if let Some(ref addr) = args.market_addr {
            addr.clone()
        } else if let Some(ref name) = args.market_name {
            self.get_market_addr(name)
        } else {
            return Err(DecibelError::Validation(
                "Either market_name or market_addr must be provided".into(),
            ));
        };

        let sub = self.resolve_subaccount(args.subaccount_addr.as_deref());

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::cancel_order_to_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(args.order_id),
                serde_json::json!(market_addr),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn cancel_client_order(
        &self,
        client_order_id: &str,
        market_name: &str,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let market_addr = self.get_market_addr(market_name);
        let sub = self.resolve_subaccount(subaccount_addr);

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::cancel_client_order_to_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(client_order_id),
                serde_json::json!(market_addr),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- TWAP Orders ---

    pub async fn place_twap_order(&self, args: PlaceTwapOrderArgs) -> Result<TwapOrderResult> {
        let market_addr = self.get_market_addr(&args.market_name);
        let sub = self.resolve_subaccount(args.subaccount_addr.as_deref());

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::place_twap_order_to_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(market_addr),
                serde_json::json!(args.size),
                serde_json::json!(args.is_buy),
                serde_json::json!(args.is_reduce_only),
                serde_json::json!(args.twap_frequency_seconds),
                serde_json::json!(args.twap_duration_seconds),
            ],
        );

        match self.submit_transaction(payload).await {
            Ok(tx) => Ok(TwapOrderResult {
                success: true,
                order_id: None,
                transaction_hash: tx.hash,
            }),
            Err(e) => Err(e),
        }
    }

    pub async fn cancel_twap_order(
        &self,
        order_id: &str,
        market_addr: &str,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::cancel_twap_order_to_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(order_id),
                serde_json::json!(market_addr),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- Position Management ---

    pub async fn place_tp_sl_order_for_position(
        &self,
        args: PlaceTpSlArgs,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(args.subaccount_addr.as_deref());

        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::place_tp_sl_order_for_position",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(args.market_addr),
                serde_json::json!(args.tp_trigger_price),
                serde_json::json!(args.tp_limit_price),
                serde_json::json!(args.tp_size),
                serde_json::json!(args.sl_trigger_price),
                serde_json::json!(args.sl_limit_price),
                serde_json::json!(args.sl_size),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- Delegation ---

    pub async fn delegate_trading_to(
        &self,
        args: DelegateTradingArgs,
    ) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::delegate_trading_to_for_subaccount",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(args.subaccount_addr),
                serde_json::json!(args.account_to_delegate_to),
                serde_json::json!(args.expiration_timestamp_secs),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn revoke_delegation(
        &self,
        subaccount_addr: Option<&str>,
        account_to_revoke: &str,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::revoke_delegation",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(account_to_revoke),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- Builder Fee ---

    pub async fn approve_max_builder_fee(
        &self,
        builder_addr: &str,
        max_fee: u64,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::approve_max_builder_fee",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(builder_addr),
                serde_json::json!(max_fee),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn revoke_max_builder_fee(
        &self,
        builder_addr: &str,
        subaccount_addr: Option<&str>,
    ) -> Result<TransactionResponse> {
        let sub = self.resolve_subaccount(subaccount_addr);
        let payload = self.build_payload(
            &format!(
                "{}::dex_accounts::revoke_max_builder_fee",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(sub),
                serde_json::json!(builder_addr),
            ],
        );
        self.submit_transaction(payload).await
    }

    // --- Vault Operations ---

    pub async fn create_vault(&self, args: CreateVaultArgs) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::vaults::create_and_fund_vault",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(args.contribution_asset_type.unwrap_or_default()),
                serde_json::json!(args.vault_name),
                serde_json::json!(args.vault_share_symbol),
                serde_json::json!(args.vault_share_icon_uri.unwrap_or_default()),
                serde_json::json!(args.vault_share_project_uri.unwrap_or_default()),
                serde_json::json!(args.fee_bps),
                serde_json::json!(args.fee_interval_s),
                serde_json::json!(args.contribution_lockup_duration_s),
                serde_json::json!(args.initial_funding),
                serde_json::json!(args.accepts_contributions),
                serde_json::json!(args.delegate_to_creator),
                serde_json::json!(args.vault_description),
                serde_json::json!(args.vault_social_links),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn activate_vault(&self, vault_address: &str) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::vaults::activate_vault",
                self.config.deployment.package
            ),
            vec![],
            vec![serde_json::json!(vault_address)],
        );
        self.submit_transaction(payload).await
    }

    pub async fn deposit_to_vault(
        &self,
        vault_address: &str,
        amount: u64,
    ) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::vaults::contribute_to_vault",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(vault_address),
                serde_json::json!(amount),
            ],
        );
        self.submit_transaction(payload).await
    }

    pub async fn withdraw_from_vault(
        &self,
        vault_address: &str,
        shares: u64,
    ) -> Result<TransactionResponse> {
        let payload = self.build_payload(
            &format!(
                "{}::vaults::redeem_from_vault",
                self.config.deployment.package
            ),
            vec![],
            vec![
                serde_json::json!(vault_address),
                serde_json::json!(shares),
            ],
        );
        self.submit_transaction(payload).await
    }
}
