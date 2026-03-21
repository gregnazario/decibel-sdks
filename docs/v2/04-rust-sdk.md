# Rust SDK Specification

**Parent**: [00-overview.md](./00-overview.md)  
**Language**: Rust 2021 Edition  
**Crate**: `decibel-sdk`  
**MSRV**: 1.75+

---

## Philosophy

The Rust SDK is for latency-critical agents: market makers, HFT bots, co-located strategies, and infrastructure. It prioritizes:

1. **Zero-cost abstractions** — no runtime overhead for type safety.
2. **Send + Sync everywhere** — all public types are safe for concurrent use across tokio tasks.
3. **Compile-time guarantees** — invalid states are unrepresentable where possible.
4. **Minimal allocations** — hot paths (WebSocket message parsing, order building) minimize heap allocation.

---

## Crate Structure

```
src/
├── lib.rs                   # Crate root, re-exports
├── config.rs                # DecibelConfig, Deployment, presets
├── client.rs                # DecibelClient (unified entry point)
├── models/
│   ├── mod.rs               # Re-exports all models
│   ├── market.rs            # PerpMarketConfig, MarketPrice, MarketContext, etc.
│   ├── account.rs           # AccountOverview, UserPosition, UserSubaccount
│   ├── order.rs             # UserOpenOrder, OrderStatus, PlaceOrderResult, etc.
│   ├── trade.rs             # UserTradeHistoryItem, UserFundingHistoryItem, etc.
│   ├── vault.rs             # Vault, UserOwnedVault
│   ├── analytics.rs         # LeaderboardItem, PortfolioChartPoint
│   ├── twap.rs              # UserActiveTwap
│   ├── ws.rs                # WebSocket message wrapper types
│   ├── pagination.rs        # PageParams, SortParams, PaginatedResponse<T>
│   └── enums.rs             # All enumerations
├── read/
│   ├── mod.rs
│   ├── client.rs            # DecibelReadClient
│   ├── markets.rs           # Market data reader methods
│   ├── account.rs           # Account data reader methods
│   ├── history.rs           # Historical data reader methods
│   ├── vaults.rs            # Vault reader methods
│   └── analytics.rs         # Leaderboard, portfolio reader methods
├── write/
│   ├── mod.rs
│   ├── client.rs            # DecibelWriteClient
│   ├── orders.rs            # Order placement and cancellation
│   ├── positions.rs         # TP/SL management
│   ├── accounts.rs          # Subaccount management, delegation
│   ├── vaults.rs            # Vault operations
│   └── bulk.rs              # Bulk order operations
├── ws/
│   ├── mod.rs
│   ├── manager.rs           # WebSocketManager
│   └── topics.rs            # Topic string builders and parsing
├── tx/
│   ├── mod.rs
│   ├── builder.rs           # TransactionBuilder (sync build)
│   ├── signer.rs            # Ed25519 transaction signing
│   └── gas.rs               # GasPriceManager
├── utils/
│   ├── mod.rs
│   ├── address.rs           # Address derivation (market, subaccount, vault share)
│   ├── formatting.rs        # Price/size formatting and rounding
│   └── nonce.rs             # Replay protection nonce generation
└── error.rs                 # Error types via thiserror
```

---

## Entry Point: DecibelClient

```rust
use decibel_sdk::{DecibelClient, DecibelConfig, MAINNET_CONFIG};

// Read-only agent
let client = DecibelClient::builder()
    .config(MAINNET_CONFIG)
    .bearer_token("your-bearer-token")
    .build()
    .await?;

// Full agent (read + write)
let client = DecibelClient::builder()
    .config(MAINNET_CONFIG)
    .bearer_token("your-bearer-token")
    .private_key("0x...")
    .build()
    .await?;
```

### Builder Parameters

| Method | Type | Required | Description |
|---|---|---|---|
| `.config()` | `DecibelConfig` | YES | SDK configuration |
| `.bearer_token()` | `&str` | YES | Bearer token for REST/WS auth |
| `.private_key()` | `&str` | NO | Ed25519 private key hex |
| `.node_api_key()` | `&str` | NO | Aptos node API key |
| `.skip_simulate()` | `bool` | NO | Skip tx simulation (default: `false`) |
| `.no_fee_payer()` | `bool` | NO | Disable gas station (default: `false`) |
| `.gas_refresh_interval()` | `Duration` | NO | Gas price refresh (default: 5s) |
| `.time_delta_ms()` | `i64` | NO | Clock drift compensation |
| `.request_timeout()` | `Duration` | NO | HTTP timeout (default: 30s) |

### Agent Discovery

```rust
// Agents can discover capabilities
let caps: Vec<&str> = client.capabilities();
// Returns: ["get_markets", "get_prices", "get_positions", "place_order", ...]

// JSON Schema export via schemars
use schemars::schema_for;
use decibel_sdk::models::MarketPrice;
let schema = schema_for!(MarketPrice);
println!("{}", serde_json::to_string_pretty(&schema)?);
```

---

## Configuration

```rust
use decibel_sdk::config::{DecibelConfig, Deployment, Network};

// Use a preset
let config = decibel_sdk::MAINNET_CONFIG;

// Or build custom
let config = DecibelConfig {
    network: Network::Mainnet,
    fullnode_url: "https://fullnode.mainnet.aptoslabs.com".into(),
    trading_http_url: "https://api.mainnet.aptoslabs.com/decibel".into(),
    trading_ws_url: "wss://api.mainnet.aptoslabs.com/decibel/ws".into(),
    deployment: Deployment {
        package: "0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06".into(),
        usdc: "0x...".into(),
        testc: "0x...".into(),
        perp_engine_global: "0x...".into(),
    },
    compat_version: "v0.4".into(),
    gas_station_url: None,
    gas_station_api_key: None,
    chain_id: None,
};
```

### Config Types

```rust
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct DecibelConfig {
    pub network: Network,
    pub fullnode_url: String,
    pub trading_http_url: String,
    pub trading_ws_url: String,
    pub deployment: Deployment,
    pub compat_version: String,
    pub gas_station_url: Option<String>,
    pub gas_station_api_key: Option<String>,
    pub chain_id: Option<u8>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum Network {
    Mainnet,
    Testnet,
    Devnet,
    Custom,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Deployment {
    pub package: String,
    pub usdc: String,
    pub testc: String,
    pub perp_engine_global: String,
}
```

---

## Read Operations

All read operations are async and return `Result<T, DecibelError>`.

### Market Data

```rust
use decibel_sdk::models::*;

// List all markets
let markets: Vec<PerpMarketConfig> = client.get_markets().await?;

// Get a specific market
let btc: PerpMarketConfig = client.get_market("BTC-USD").await?;

// Current prices
let prices: Vec<MarketPrice> = client.get_prices().await?;
let btc_price: Vec<MarketPrice> = client.get_price("BTC-USD").await?;

// Orderbook depth
let depth: MarketDepth = client.get_depth("BTC-USD", Some(20)).await?;

// Recent trades
let trades: Vec<MarketTrade> = client.get_trades("BTC-USD", Some(50)).await?;

// Candlesticks
let candles: Vec<Candlestick> = client.get_candlesticks(
    "BTC-USD",
    CandlestickInterval::OneHour,
    1710000000000,
    1710086400000,
).await?;

// Asset contexts
let contexts: Vec<MarketContext> = client.get_asset_contexts().await?;
```

### Account Data

```rust
// Account overview
let overview: AccountOverview = client.get_account_overview(
    "0x...",
    Some(VolumeWindow::ThirtyDays),
    Some(true), // include_performance
).await?;

// Positions
let positions: Vec<UserPosition> = client.get_positions("0x...", None).await?;

// Open orders
let orders: Vec<UserOpenOrder> = client.get_open_orders("0x...").await?;

// Subaccounts
let subs: Vec<UserSubaccount> = client.get_subaccounts("0x...").await?;
```

### History (Paginated)

```rust
use decibel_sdk::models::pagination::*;

// Trade history
let trades: PaginatedResponse<UserTradeHistoryItem> = client.get_trade_history(
    "0x...",
    PageParams { limit: 50, offset: 0 },
).await?;

// Order history with sort
let orders: PaginatedResponse<UserOrderHistoryItem> = client.get_order_history(
    "0x...",
    None, // market_addr filter
    PageParams { limit: 20, offset: 0 },
    Some(SortParams {
        sort_key: Some("transaction_unix_ms".into()),
        sort_dir: Some(SortDirection::Descending),
    }),
).await?;

// Funding history
let funding: PaginatedResponse<UserFundingHistoryItem> = client.get_funding_history(
    "0x...",
    None, // market_addr filter
    PageParams { limit: 100, offset: 0 },
).await?;
```

---

## Write Operations

Write operations require a private key and return `Result<TransactionResult, DecibelError>`.

### Account Management

```rust
// Create subaccount
let result: TransactionResult = client.create_subaccount().await?;

// Deposit USDC
let result = client.deposit(1_000_000, Some("0x...")).await?;

// Withdraw USDC
let result = client.withdraw(500_000, Some("0x...")).await?;

// Configure market settings
let result = client.configure_market_settings(
    "0x...", // market_addr
    "0x...", // subaccount_addr
    true,    // is_cross
    10_000,  // user_leverage (basis points)
).await?;
```

### Order Management

```rust
use decibel_sdk::models::enums::TimeInForce;

// Place order
let result: PlaceOrderResult = client.place_order(PlaceOrderParams {
    market_name: "BTC-USD".into(),
    price: 45_000.0,
    size: 0.25,
    is_buy: true,
    time_in_force: TimeInForce::GoodTillCanceled,
    is_reduce_only: false,
    client_order_id: Some("agent-001".into()),
    ..Default::default()
}).await?;

if result.success {
    println!("Order placed: {:?}", result.order_id);
}

// Cancel order
let result = client.cancel_order(CancelOrderParams {
    order_id: result.order_id.unwrap(),
    market_name: Some("BTC-USD".into()),
    ..Default::default()
}).await?;

// Cancel by client order ID
let result = client.cancel_client_order(
    "agent-001",
    "BTC-USD",
    None, // subaccount
    None, // account_override
).await?;
```

### Parameter Structs with Builder Pattern

```rust
/// Parameters for placing an order.
///
/// Required fields: market_name, price, size, is_buy, time_in_force, is_reduce_only.
/// All other fields have sensible defaults.
#[derive(Debug, Clone, Default, Serialize, JsonSchema)]
pub struct PlaceOrderParams {
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

#[derive(Debug, Clone, Default, Serialize, JsonSchema)]
pub struct CancelOrderParams {
    pub order_id: String,
    pub market_name: Option<String>,
    pub market_addr: Option<String>,
    pub subaccount_addr: Option<String>,
}
```

### TWAP Orders

```rust
let result = client.place_twap_order(PlaceTwapParams {
    market_name: "BTC-USD".into(),
    size: 2.0,
    is_buy: true,
    is_reduce_only: false,
    twap_frequency_seconds: 30,
    twap_duration_seconds: 15 * 60,
    client_order_id: Some("twap-001".into()),
    ..Default::default()
}).await?;

let result = client.cancel_twap_order("order_id", "0x...market_addr", None, None).await?;
```

### Position Management (TP/SL)

```rust
let result = client.place_tp_sl(TpSlParams {
    market_addr: "0x...".into(),
    tp_trigger_price: Some(47_000.0),
    tp_limit_price: Some(46_950.0),
    sl_trigger_price: Some(43_000.0),
    sl_limit_price: Some(43_050.0),
    ..Default::default()
}).await?;

let result = client.update_tp_order(UpdateTpParams {
    market_addr: "0x...".into(),
    prev_order_id: "...".into(),
    tp_trigger_price: Some(48_000.0),
    tp_limit_price: Some(47_950.0),
    ..Default::default()
}).await?;
```

### Delegation and Builder Fees

```rust
let result = client.delegate_trading(
    "0x...",      // subaccount_addr
    "0x...",      // delegate_to
    None,         // expiration
).await?;

let result = client.approve_builder_fee(
    "0x...",      // builder_addr
    100,          // max_fee_bps
    None,         // subaccount
).await?;
```

### Vault Operations

```rust
let result = client.create_vault(CreateVaultParams {
    vault_name: "Agent Alpha".into(),
    vault_description: "AI-managed momentum strategy".into(),
    vault_social_links: vec![],
    vault_share_symbol: "ALPHA".into(),
    fee_bps: 1000,
    fee_interval_s: 604800,
    contribution_lockup_duration_s: 86400,
    initial_funding: 10_000_000,
    accepts_contributions: true,
    delegate_to_creator: true,
    ..Default::default()
}).await?;

let result = client.activate_vault("0x...vault").await?;
let result = client.deposit_to_vault("0x...vault", 5_000_000).await?;
let result = client.withdraw_from_vault("0x...vault", 1_000).await?;
```

---

## WebSocket Subscriptions

### Callback-Based

```rust
use decibel_sdk::models::MarketPrice;

// Subscribe to market price
let unsub = client.subscribe_market_price("BTC-USD", |price: MarketPrice| {
    println!("BTC: {}", price.mark_px);
}).await?;

// Subscribe to all market prices
let unsub = client.subscribe_all_market_prices(|update| {
    for price in &update.prices {
        println!("{}: {}", price.market, price.mark_px);
    }
}).await?;

// Subscribe to positions
let unsub = client.subscribe_positions("0x...", |update| {
    for pos in &update.positions {
        println!("{}: size={}", pos.market, pos.size);
    }
}).await?;

// Unsubscribe
unsub.unsubscribe().await?;
```

### Channel-Based (tokio::sync)

For agents that prefer pulling from a channel:

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel::<MarketPrice>(100);

let unsub = client.subscribe_market_price("BTC-USD", move |price| {
    let _ = tx.try_send(price);
}).await?;

// Agent loop
while let Some(price) = rx.recv().await {
    if price.mark_px > threshold {
        client.place_order(...).await?;
        break;
    }
}

unsub.unsubscribe().await?;
```

### Stream-Based (futures::Stream)

```rust
use futures::StreamExt;

let mut stream = client.stream_market_price("BTC-USD").await?;

while let Some(price) = stream.next().await {
    let price = price?;
    // Process price update
}
```

---

## Error Handling

All errors use `thiserror` derive and the `DecibelError` enum. See [08-error-handling.md](./08-error-handling.md) for the full taxonomy.

```rust
use decibel_sdk::error::DecibelError;

match client.place_order(params).await {
    Ok(result) if result.success => {
        println!("Order placed: {:?}", result.order_id);
    }
    Ok(result) => {
        eprintln!("Order rejected: {:?}", result.error);
    }
    Err(DecibelError::RateLimit { retry_after_ms }) => {
        tokio::time::sleep(Duration::from_millis(retry_after_ms)).await;
        // retry...
    }
    Err(DecibelError::Transaction { hash, vm_status, .. }) => {
        eprintln!("TX {} failed: {}", hash, vm_status);
    }
    Err(e) if e.is_retryable() => {
        // Generic retry logic
        tokio::time::sleep(Duration::from_secs(1)).await;
        // retry...
    }
    Err(e) => {
        eprintln!("Unrecoverable error: {}", e);
    }
}
```

---

## Observability

The SDK uses the `tracing` crate for structured logging.

```rust
use tracing_subscriber;

// Enable tracing
tracing_subscriber::fmt()
    .with_max_level(tracing::Level::DEBUG)
    .with_target(true)
    .init();

// The SDK emits spans and events:
// decibel::http  — HTTP request/response
// decibel::ws    — WebSocket messages
// decibel::tx    — Transaction build/sign/submit
// decibel::gas   — Gas price updates
```

---

## Price/Size Formatting Utilities

```rust
use decibel_sdk::utils::formatting::*;

let market = client.get_market("BTC-USD").await?;

// Round price to valid tick size
let price = round_to_valid_price(45_123.456, &market);

// Round size to valid lot size (enforces min_size)
let size = round_to_valid_order_size(0.1234, &market);

// Convert to/from chain units
let chain_price = amount_to_chain_units(price, market.px_decimals);
let chain_size = amount_to_chain_units(size, market.sz_decimals);

let decimal_price = chain_units_to_amount(chain_price, market.px_decimals);
```

---

## Model Patterns

### Serde Derive Pattern

```rust
use serde::{Serialize, Deserialize};
use schemars::JsonSchema;

/// Real-time price snapshot for a perpetual futures market.
///
/// Received from REST GET /api/v1/prices or WebSocket market_price:{addr} topic.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub struct MarketPrice {
    /// Market name or address
    pub market: String,
    /// Mark price for margin calculations
    pub mark_px: f64,
    /// Mid price (average of best bid/ask)
    pub mid_px: f64,
    /// Oracle price from external feed
    pub oracle_px: f64,
    /// Funding rate in basis points
    pub funding_rate_bps: f64,
    /// True if longs pay shorts
    pub is_funding_positive: bool,
    /// Total open interest
    pub open_interest: f64,
    /// Timestamp of last update (Unix ms)
    pub transaction_unix_ms: i64,
}

impl std::fmt::Display for MarketPrice {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "MarketPrice({}: mark={}, oracle={}, funding={}bps)",
            self.market, self.mark_px, self.oracle_px, self.funding_rate_bps
        )
    }
}
```

### Enum Pattern

```rust
/// Controls how long an order remains active on the orderbook.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[repr(u8)]
pub enum TimeInForce {
    /// Remains on book until filled or canceled
    GoodTillCanceled = 0,
    /// Rejected if it would immediately match (maker only)
    PostOnly = 1,
    /// Fill what's available immediately, cancel the rest
    ImmediateOrCancel = 2,
}

impl Default for TimeInForce {
    fn default() -> Self {
        Self::GoodTillCanceled
    }
}

/// Time interval for candlestick/OHLCV data.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub enum CandlestickInterval {
    #[serde(rename = "1m")]
    OneMinute,
    #[serde(rename = "5m")]
    FiveMinutes,
    #[serde(rename = "15m")]
    FifteenMinutes,
    #[serde(rename = "30m")]
    ThirtyMinutes,
    #[serde(rename = "1h")]
    OneHour,
    #[serde(rename = "2h")]
    TwoHours,
    #[serde(rename = "4h")]
    FourHours,
    #[serde(rename = "8h")]
    EightHours,
    #[serde(rename = "12h")]
    TwelveHours,
    #[serde(rename = "1d")]
    OneDay,
    #[serde(rename = "3d")]
    ThreeDays,
    #[serde(rename = "1w")]
    OneWeek,
    #[serde(rename = "1mo")]
    OneMonth,
}
```

### Error Pattern

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DecibelError {
    #[error("configuration error: {message}")]
    Config { message: String },

    #[error("authentication error: {message}")]
    Authentication { message: String },

    #[error("network error: {source}")]
    Network {
        #[source]
        source: reqwest::Error,
        retryable: bool,
    },

    #[error("rate limited, retry after {retry_after_ms}ms")]
    RateLimit { retry_after_ms: u64 },

    #[error("API error {status}: {message}")]
    Api {
        status: u16,
        message: String,
        retryable: bool,
    },

    #[error("transaction error: {vm_status}")]
    Transaction {
        hash: String,
        vm_status: String,
        gas_used: Option<u64>,
    },

    #[error("validation error on field '{field}': {constraint}")]
    Validation { field: String, constraint: String },

    #[error("WebSocket error: {message}")]
    WebSocket { message: String, retryable: bool },

    #[error("serialization error: {source}")]
    Serialization {
        #[source]
        source: serde_json::Error,
    },
}

impl DecibelError {
    /// Whether this error is safe to retry.
    pub fn is_retryable(&self) -> bool {
        match self {
            Self::Network { retryable, .. } => *retryable,
            Self::RateLimit { .. } => true,
            Self::Api { retryable, .. } => *retryable,
            Self::WebSocket { retryable, .. } => *retryable,
            _ => false,
        }
    }

    /// Suggested retry delay in milliseconds, if applicable.
    pub fn retry_after_ms(&self) -> Option<u64> {
        match self {
            Self::RateLimit { retry_after_ms } => Some(*retry_after_ms),
            Self::Network { .. } => Some(1000),
            Self::WebSocket { .. } => Some(1000),
            _ => None,
        }
    }
}
```

---

## Dependencies

```toml
[package]
name = "decibel-sdk"
version = "2.0.0"
edition = "2021"
rust-version = "1.75"

[dependencies]
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
tokio-tungstenite = { version = "0.24", features = ["rustls-tls-native-roots"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
ed25519-dalek = { version = "2", features = ["rand_core"] }
bcs = "0.1"
thiserror = "2"
tracing = "0.1"
schemars = { version = "0.8", features = ["derive"] }
futures = "0.3"
url = "2"
rand = "0.8"
sha3 = "0.10"
hex = "0.4"

[dev-dependencies]
tokio = { version = "1", features = ["test-util", "macros"] }
tracing-subscriber = "0.3"
wiremock = "0.6"
pretty_assertions = "1"
proptest = "1"
criterion = "0.5"

[[bench]]
name = "serialization"
harness = false
```

---

## Testing

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn market_price_roundtrip() {
        let json = r#"{
            "market": "BTC-USD",
            "mark_px": 45000.0,
            "mid_px": 44999.5,
            "oracle_px": 45001.0,
            "funding_rate_bps": 0.01,
            "is_funding_positive": true,
            "open_interest": 1500000.0,
            "transaction_unix_ms": 1710000000000
        }"#;

        let price: MarketPrice = serde_json::from_str(json).unwrap();
        assert_eq!(price.market, "BTC-USD");
        assert_eq!(price.mark_px, 45000.0);

        let roundtrip = serde_json::to_string(&price).unwrap();
        let price2: MarketPrice = serde_json::from_str(&roundtrip).unwrap();
        assert_eq!(price, price2);
    }

    #[test]
    fn schema_export() {
        let schema = schemars::schema_for!(MarketPrice);
        let json = serde_json::to_string_pretty(&schema).unwrap();
        assert!(json.contains("mark_px"));
        assert!(json.contains("oracle_px"));
    }
}
```

### Integration Tests

```rust
#[tokio::test]
#[ignore] // requires testnet access
async fn test_place_and_cancel_order() {
    let client = DecibelClient::builder()
        .config(TESTNET_CONFIG)
        .bearer_token(&std::env::var("DECIBEL_BEARER_TOKEN").unwrap())
        .private_key(&std::env::var("DECIBEL_PRIVATE_KEY").unwrap())
        .build()
        .await
        .unwrap();

    let result = client.place_order(PlaceOrderParams {
        market_name: "BTC-USD".into(),
        price: 10.0,
        size: 1.0,
        is_buy: true,
        time_in_force: TimeInForce::GoodTillCanceled,
        is_reduce_only: false,
        client_order_id: Some("rust-test-001".into()),
        ..Default::default()
    }).await.unwrap();

    assert!(result.success);
    assert!(result.order_id.is_some());

    let cancel = client.cancel_order(CancelOrderParams {
        order_id: result.order_id.unwrap(),
        market_name: Some("BTC-USD".into()),
        ..Default::default()
    }).await.unwrap();

    assert!(cancel.success);
}
```

### Benchmarks

```rust
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_market_price_deser(c: &mut Criterion) {
    let json = r#"{"market":"BTC-USD","mark_px":45000.0,"mid_px":44999.5,"oracle_px":45001.0,"funding_rate_bps":0.01,"is_funding_positive":true,"open_interest":1500000.0,"transaction_unix_ms":1710000000000}"#;

    c.bench_function("MarketPrice deserialize", |b| {
        b.iter(|| {
            let _: MarketPrice = serde_json::from_str(json).unwrap();
        })
    });
}

criterion_group!(benches, bench_market_price_deser);
criterion_main!(benches);
```

---

## Thread Safety

All public types in the Rust SDK implement `Send + Sync`:

```rust
// The client is safe to share across tokio tasks
let client = Arc::new(client);

let client_clone = client.clone();
tokio::spawn(async move {
    let prices = client_clone.get_prices().await.unwrap();
    // ...
});

let client_clone = client.clone();
tokio::spawn(async move {
    let result = client_clone.place_order(params).await.unwrap();
    // ...
});
```

Internal mutable state (caches, WebSocket subscriptions) uses `Arc<RwLock<>>` for reads and `Arc<Mutex<>>` for writes that require exclusive access.
