# REST API Client Specification

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

The REST API client handles all HTTP communication with the Decibel trading API. It is the backbone of read operations and provides the foundation for market data queries, account state inspection, and historical data retrieval.

## Base URL

All endpoints are under `{config.trading_http_url}/api/v1/`.

| Network | Base URL |
|---|---|
| Mainnet | `https://api.mainnet.aptoslabs.com/decibel/api/v1/` |
| Testnet | `https://api.testnet.aptoslabs.com/decibel/api/v1/` |

## Authentication

Every request MUST include:

| Header | Value | Required |
|---|---|---|
| `Authorization` | `Bearer <token>` | YES |
| `Origin` | Application origin URL | YES |

## HTTP Client Requirements

| Requirement | Description |
|---|---|
| **Connection pooling** | MUST reuse TCP connections. HTTP/2 preferred. |
| **Timeouts** | Default 30s per request, configurable. |
| **Retries** | Automatic retry on 5xx and network errors with exponential backoff. |
| **Compression** | MUST accept `gzip` responses. |
| **Content type** | All requests send/receive `application/json`. |

### Python Implementation

```python
import httpx

class HttpClient:
    def __init__(self, base_url: str, bearer_token: str, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Origin": "https://app.decibel.trade",
                "Accept-Encoding": "gzip",
            },
            timeout=timeout,
            http2=True,
        )
```

### Rust Implementation

```rust
use reqwest::Client;

pub struct HttpClient {
    client: Client,
    base_url: String,
}

impl HttpClient {
    pub fn new(base_url: &str, bearer_token: &str, timeout: Duration) -> Self {
        let client = Client::builder()
            .default_headers({
                let mut h = reqwest::header::HeaderMap::new();
                h.insert("Authorization", format!("Bearer {}", bearer_token).parse().unwrap());
                h.insert("Origin", "https://app.decibel.trade".parse().unwrap());
                h
            })
            .timeout(timeout)
            .pool_max_idle_per_host(10)
            .gzip(true)
            .build()
            .unwrap();
        Self { client, base_url: base_url.to_string() }
    }
}
```

## Generic Request Methods

The HTTP client MUST expose typed generic methods. The return type is always deserialized before reaching the caller.

### Method Signatures

```
async get<T>(path, query_params?) -> Result<T, DecibelError>
async post<T>(path, body) -> Result<T, DecibelError>
async patch<T>(path, body) -> Result<T, DecibelError>
```

### Error Mapping

| HTTP Status | SDK Error |
|---|---|
| 200-299 | Success — deserialize body to `T` |
| 400 | `ValidationError` |
| 401 | `AuthenticationError` |
| 404 | `ApiError::NotFound` |
| 429 | `RateLimitError` (parse `Retry-After` header) |
| 500-599 | `ApiError::Server` (retryable) |
| Timeout | `TimeoutError` (retryable) |
| Connection refused | `ConnectionError` (retryable) |

---

## Endpoint Catalog

### Market Data Endpoints

#### GET /markets

List all available perpetual futures markets.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters |

**Response**: `Vec<PerpMarketConfig>`

**Agent Usage**: Fetch once at startup, cache with TTL. Use to resolve market names to addresses and to get formatting parameters (tick_size, lot_size, etc.).

---

#### GET /markets/{name}

Get a specific market by name.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | path | YES | Market name (e.g., `"BTC-USD"`) |

**Response**: `PerpMarketConfig`

---

#### GET /prices

Get current prices for all markets.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `market` | query | NO | Filter by market name or `"all"` |

**Response**: `Vec<MarketPrice>`

---

#### GET /prices/{marketName}

Get price for a specific market.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |

**Response**: `Vec<MarketPrice>`

---

#### GET /depth/{marketName}

Get orderbook depth snapshot.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `limit` | query | NO | Number of levels per side |

**Response**: `MarketDepth`

---

#### GET /trades/{marketName}

Get recent market trades.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `limit` | query | NO | Number of trades |

**Response**: `Vec<MarketTrade>`

---

#### GET /candlesticks/{marketName}

Get OHLCV candlestick data.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketName` | path | YES | Market name |
| `interval` | query | YES | Candle interval (`1m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `1d`, `1w`, `1mo`) |
| `startTime` | query | YES | Start timestamp (Unix ms) |
| `endTime` | query | YES | End timestamp (Unix ms) |

**Response**: `Vec<Candlestick>`

**Limits**: Maximum 1000 candles per request. Missing intervals are interpolated using last known close price.

---

#### GET /asset-contexts

Get extended market context with 24h statistics.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters |

**Response**: `Vec<MarketContext>`

---

### Account Endpoints

#### GET /account_overviews

Get account overview including equity, margin, and performance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |
| `volume_window` | query | NO | Volume window (`7d`, `14d`, `30d`, `90d`) |
| `include_performance` | query | NO | Include performance metrics (`true`/`false`) |

**Response**: `AccountOverview`

---

#### GET /account_positions

Get open positions for an account.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |
| `market` | query | NO | Filter by market address |
| `limit` | query | NO | Number of positions |

**Response**: `Vec<UserPosition>`

---

#### GET /open_orders

Get currently open orders.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |

**Response**: `Vec<UserOpenOrder>`

---

#### GET /subaccounts

Get all subaccounts for an owner.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `owner` | query | YES | Owner address |

**Response**: `Vec<UserSubaccount>`

---

#### GET /delegations

Get active delegations for a subaccount.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | query | YES | Subaccount address |

**Response**: `Vec<Delegation>`

---

### History Endpoints (Paginated)

All history endpoints support the following common query parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | query | NO | `10` | Items per page (max 200) |
| `offset` | query | NO | `0` | Pagination offset |
| `sort_by` | query | NO | `transaction_unix_ms` | Sort key |
| `sort_dir` | query | NO | `DESC` | Sort direction |

#### GET /order_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `order_type` | query | NO |
| `status` | query | NO |
| `side` | query | NO |
| `is_reduce_only` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserOrderHistoryItem>`

---

#### GET /trade_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `order_id` | query | NO |
| `side` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserTradeHistoryItem>`

---

#### GET /funding_rate_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `side` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserFundingHistoryItem>`

---

#### GET /account_fund_history

| Additional Params | Type | Required |
|---|---|---|
| `account` | query | YES |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserFundHistoryItem>`

---

### TWAP Endpoints

#### GET /active_twaps

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |

**Response**: `Vec<UserActiveTwap>`

---

#### GET /twap_history

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `limit` | query | NO |
| `offset` | query | NO |
| `start_time` | query | NO |
| `end_time` | query | NO |

**Response**: `PaginatedResponse<UserActiveTwap>`

---

### Bulk Order Endpoints

#### GET /bulk_orders

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |

**Response**: Bulk orders response

---

#### GET /bulk_order_status

| Parameter | Type | Required |
|---|---|---|
| `sequence_number` | query | YES |

**Response**: Bulk order status

---

#### GET /bulk_order_fills

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `market` | query | NO |
| `sequence_number` | query | NO |

**Response**: Bulk order fills

---

### Vault Endpoints

#### GET /vaults

| Parameter | Type | Required | Description |
|---|---|---|---|
| `limit` | query | NO | Page size |
| `offset` | query | NO | Offset |
| `sort_key` | query | NO | Sort field |
| `sort_dir` | query | NO | Sort direction |
| `search` | query | NO | Search term |
| `vault_type` | query | NO | `"user"` or `"protocol"` |
| `vault_address` | query | NO | Exact vault address |
| `status` | query | NO | Vault status filter |

**Response**: `PaginatedResponse<Vault>`

---

#### GET /account_owned_vaults

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `limit` | query | NO |
| `offset` | query | NO |

**Response**: `PaginatedResponse<UserOwnedVault>`

---

#### GET /account_vault_performance

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |

**Response**: Vault performance data

---

### Analytics Endpoints

#### GET /leaderboard

| Parameter | Type | Required |
|---|---|---|
| `limit` | query | NO |
| `offset` | query | NO |
| `sort_key` | query | NO |
| `sort_dir` | query | NO |
| `search_term` | query | NO |

**Response**: `PaginatedResponse<LeaderboardItem>`

---

#### GET /portfolio_chart

| Parameter | Type | Required |
|---|---|---|
| `account` | query | YES |
| `interval` | query | NO |

**Response**: `Vec<PortfolioChartPoint>`

---

### Order Status Endpoint

#### GET /orders

| Parameter | Type | Required | Description |
|---|---|---|---|
| `order_id` | query | YES | Order ID |
| `market_address` | query | YES | Market address |
| `user_address` | query | YES | User address |

**Response**: `OrderStatus`

---

## Caching Strategy

The SDK MUST implement these caching behaviors:

| Data | Cache Strategy | TTL | Invalidation |
|---|---|---|---|
| Market configs | Cache after first fetch | 5 minutes | Manual refresh or TTL expiry |
| USDC decimals | Cache forever | ∞ | Immutable value |
| Prices | No cache (real-time) | — | Use WebSocket for streaming |
| Positions | No cache | — | Use WebSocket for streaming |
| Orders | No cache | — | Use WebSocket for streaming |

## Rate Limiting

The SDK MUST handle rate limiting gracefully:

1. Detect `429` responses.
2. Parse `Retry-After` header if present.
3. Return `RateLimitError` with `retry_after_ms`.
4. Optionally implement automatic retry with backoff (configurable).

## Query Parameter Construction

The SDK provides a utility to build query strings from typed parameters:

```python
def build_query_params(
    page: PageParams | None = None,
    sort: SortParams | None = None,
    search: str | None = None,
    **kwargs: Any,
) -> dict[str, str]:
    """Build URL query parameters from typed inputs.

    Omits None values. Converts enums to their wire values.
    """
    ...
```

```rust
fn build_query_params(
    page: Option<&PageParams>,
    sort: Option<&SortParams>,
    search: Option<&str>,
    extra: &[(&str, &str)],
) -> Vec<(String, String)> {
    // Omits None values. Converts enums to wire values.
    ...
}
```
