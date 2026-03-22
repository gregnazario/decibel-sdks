# Go SDK Specification (Future)

**Parent**: [00-overview.md](./00-overview.md)  
**Language**: Go 1.22+  
**Module**: `github.com/decibel-trade/decibel-sdk-go`  
**Status**: Planned — lower priority than Python and Rust

---

## Role in the Ecosystem

Go fills the gap between Python (flexibility, ML ecosystem) and Rust (raw performance):

| Use Case | Why Go |
|---|---|
| API gateway / aggregation service | Goroutine-per-connection scales to thousands of concurrent users |
| Multi-strategy orchestrator | Clean concurrency via channels; no async/await complexity |
| Monitoring / alerting service | Simple deployment (single binary), low memory |
| Backtesting infrastructure | Fast enough for historical simulation, easy to parallelize |
| Microservice trading architecture | gRPC/HTTP service mesh integration; quick compile-deploy cycle |

Go is **not** the choice for the innermost market making loop (use Rust) or ML inference (use Python). It's the choice for the surrounding infrastructure.

---

## Package Structure

```
decibel/
├── config.go                # DecibelConfig, Deployment, presets
├── client.go                # DecibelClient (unified entry point)
├── errors.go                # Error types
├── models/
│   ├── market.go            # PerpMarketConfig, MarketPrice, MarketDepth, etc.
│   ├── account.go           # AccountOverview, UserPosition, UserSubaccount
│   ├── order.go             # UserOpenOrder, OrderStatus, PlaceOrderResult
│   ├── trade.go             # UserTradeHistoryItem, UserFundingHistoryItem
│   ├── vault.go             # Vault, UserOwnedVault
│   ├── analytics.go         # LeaderboardItem, PortfolioChartPoint
│   ├── twap.go              # UserActiveTwap
│   ├── bulk.go              # BulkOrderSet, BulkOrderFill
│   ├── ws.go                # WebSocket message types
│   ├── pagination.go        # PageParams, SortParams, PaginatedResponse
│   └── enums.go             # All enumerations
├── read/
│   ├── client.go            # ReadClient
│   ├── markets.go           # Market data methods
│   ├── account.go           # Account data methods
│   ├── history.go           # History methods
│   └── vaults.go            # Vault methods
├── write/
│   ├── client.go            # WriteClient
│   ├── orders.go            # Order placement/cancellation
│   ├── positions.go         # TP/SL management
│   ├── accounts.go          # Subaccount management
│   └── vaults.go            # Vault operations
├── ws/
│   ├── manager.go           # WebSocketManager
│   └── topics.go            # Topic builders
├── state/
│   ├── positions.go         # PositionStateManager
│   ├── bulk.go              # BulkOrderManager
│   └── risk.go              # Risk computations
├── tx/
│   ├── builder.go           # Transaction builder (sync)
│   ├── signer.go            # Ed25519 signing
│   └── gas.go               # GasPriceManager
└── utils/
    ├── address.go           # Address derivation
    ├── formatting.go        # Price/size formatting
    └── nonce.go             # Replay nonce generation
```

---

## Go Idioms

### Functional Options for Configuration

```go
type ClientOption func(*clientConfig)

func WithBearerToken(token string) ClientOption {
    return func(c *clientConfig) { c.bearerToken = token }
}

func WithPrivateKey(key string) ClientOption {
    return func(c *clientConfig) { c.privateKey = key }
}

func WithNodeAPIKey(key string) ClientOption {
    return func(c *clientConfig) { c.nodeAPIKey = key }
}

func WithSkipSimulate(skip bool) ClientOption {
    return func(c *clientConfig) { c.skipSimulate = skip }
}

func WithGasRefreshInterval(d time.Duration) ClientOption {
    return func(c *clientConfig) { c.gasRefreshInterval = d }
}

func WithRequestTimeout(d time.Duration) ClientOption {
    return func(c *clientConfig) { c.requestTimeout = d }
}

func NewClient(config DecibelConfig, opts ...ClientOption) (*DecibelClient, error) {
    // Apply options...
}
```

### Context for Cancellation and Timeouts

Every method takes `context.Context` as the first parameter:

```go
func (c *DecibelClient) GetMarkets(ctx context.Context) ([]PerpMarketConfig, error)
func (c *DecibelClient) PlaceOrder(ctx context.Context, params PlaceOrderParams) (*PlaceOrderResult, error)
func (c *DecibelClient) GetPositions(ctx context.Context, subAddr string) ([]UserPosition, error)
```

### Channel-Based WebSocket Subscriptions

Go naturally uses channels for streaming data:

```go
// Subscribe returns a channel that receives updates and a cancel function
priceCh, cancel, err := client.SubscribeMarketPrice(ctx, "BTC-USD")
if err != nil {
    return err
}
defer cancel()

for price := range priceCh {
    if price.MarkPx > threshold {
        _, err := client.PlaceOrder(ctx, PlaceOrderParams{
            MarketName: "BTC-USD",
            Price:      price.MarkPx * 0.999,
            Size:       0.1,
            IsBuy:      true,
            TimeInForce: GoodTillCanceled,
        })
        if err != nil {
            log.Printf("order failed: %v", err)
        }
    }
}
```

### Error Handling with `(T, error)`

```go
result, err := client.PlaceOrder(ctx, params)
if err != nil {
    var rateLimitErr *RateLimitError
    if errors.As(err, &rateLimitErr) {
        time.Sleep(time.Duration(rateLimitErr.RetryAfterMs) * time.Millisecond)
        result, err = client.PlaceOrder(ctx, params)
    }

    var txErr *TransactionError
    if errors.As(err, &txErr) {
        if txErr.IsCritical() {
            // Position safety issue — emergency action needed
            emergencyCloseAll(ctx, client)
        }
    }
    return fmt.Errorf("place order: %w", err)
}
```

### Interfaces for Testing

```go
type MarketReader interface {
    GetMarkets(ctx context.Context) ([]PerpMarketConfig, error)
    GetPrices(ctx context.Context) ([]MarketPrice, error)
    GetDepth(ctx context.Context, market string, limit int) (*MarketDepth, error)
}

type OrderWriter interface {
    PlaceOrder(ctx context.Context, params PlaceOrderParams) (*PlaceOrderResult, error)
    CancelOrder(ctx context.Context, params CancelOrderParams) (*TransactionResult, error)
}

// DecibelClient implements both
var _ MarketReader = (*DecibelClient)(nil)
var _ OrderWriter = (*DecibelClient)(nil)
```

---

## PositionStateManager (Go)

```go
type PositionStateManager struct {
    mu        sync.RWMutex
    positions map[string]UserPosition // market_addr -> position
    overview  *AccountOverview
    orders    map[string]UserOpenOrder // order_id -> order
}

// Snapshot returns a consistent point-in-time view of all state.
func (m *PositionStateManager) Snapshot() StateSnapshot {
    m.mu.RLock()
    defer m.mu.RUnlock()
    // Deep copy all state
    ...
}

// NetExposure returns net directional exposure in USD across all positions.
func (m *PositionStateManager) NetExposure(prices map[string]float64) float64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    var net float64
    for _, pos := range m.positions {
        if px, ok := prices[pos.Market]; ok {
            net += pos.Size * px
        }
    }
    return net
}

// MarginUsagePct returns percentage of equity used as margin.
func (m *PositionStateManager) MarginUsagePct() float64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    if m.overview == nil || m.overview.PerpEquityBalance == 0 {
        return 0
    }
    return m.overview.TotalMargin / m.overview.PerpEquityBalance * 100
}
```

---

## BulkOrderManager (Go)

```go
type BulkOrderManager struct {
    client   *DecibelClient
    market   string
    subAddr  string
    seqNum   atomic.Uint64
    fills    []BulkOrderFill
    fillsMu  sync.RWMutex
}

// SetQuotes atomically replaces all bulk orders for this market.
func (m *BulkOrderManager) SetQuotes(
    ctx context.Context,
    bids []PriceSize,
    asks []PriceSize,
) (*TransactionResult, error) {
    seq := m.seqNum.Add(1)
    // Convert to chain units, build tx, submit
    ...
}

// CancelAll removes all bulk orders by submitting empty arrays.
func (m *BulkOrderManager) CancelAll(ctx context.Context) (*TransactionResult, error) {
    return m.SetQuotes(ctx, nil, nil)
}

// Fills returns all fills since last reset.
func (m *BulkOrderManager) Fills() []BulkOrderFill {
    m.fillsMu.RLock()
    defer m.fillsMu.RUnlock()
    return slices.Clone(m.fills)
}
```

---

## Concurrency Patterns

### Goroutine-Per-Strategy

```go
func main() {
    client, _ := decibel.NewClient(decibel.MainnetConfig,
        decibel.WithBearerToken(os.Getenv("BEARER_TOKEN")),
        decibel.WithPrivateKey(os.Getenv("PRIVATE_KEY")),
    )
    defer client.Close()

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    g, ctx := errgroup.WithContext(ctx)

    // Strategy 1: BTC market making on subaccount A
    g.Go(func() error {
        return runMarketMaker(ctx, client, "BTC-USD", subAccountA)
    })

    // Strategy 2: ETH momentum on subaccount B
    g.Go(func() error {
        return runMomentumBot(ctx, client, "ETH-USD", subAccountB)
    })

    // Risk monitor across all subaccounts
    g.Go(func() error {
        return runRiskMonitor(ctx, client, []string{subAccountA, subAccountB})
    })

    if err := g.Wait(); err != nil {
        log.Fatal(err)
    }
}
```

### Select for Multi-Stream Processing

```go
func runMarketMaker(ctx context.Context, client *DecibelClient, market, subAddr string) error {
    priceCh, cancelPrice, _ := client.SubscribeMarketPrice(ctx, market)
    defer cancelPrice()

    fillCh, cancelFills, _ := client.SubscribeBulkOrderFills(ctx, subAddr)
    defer cancelFills()

    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()

    bulk := client.BulkOrderManager(market, subAddr)

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()

        case price := <-priceCh:
            // Update fair value, recompute quotes
            bids, asks := computeQuotes(price)
            bulk.SetQuotes(ctx, bids, asks)

        case fill := <-fillCh:
            // Update inventory, adjust skew
            updateInventory(fill)

        case <-ticker.C:
            // Periodic risk check
            if marginTooLow(client) {
                bulk.CancelAll(ctx)
            }
        }
    }
}
```

---

## Dependencies

```go
module github.com/decibel-trade/decibel-sdk-go

go 1.22

require (
    golang.org/x/crypto v0.28.0     // Ed25519 signing
    nhooyr.io/websocket v1.8.11      // WebSocket client
    github.com/stretchr/testify v1.9 // Testing
    golang.org/x/sync v0.8.0         // errgroup
)
```

Key decisions:
- **No `gorilla/websocket`** — `nhooyr.io/websocket` is more actively maintained and supports `context.Context` natively.
- **stdlib `net/http`** for REST — no need for external HTTP client in Go.
- **stdlib `encoding/json`** — fast enough for most use cases; `github.com/bytedance/sonic` available as optional high-performance alternative.
- **`golang.org/x/crypto`** for Ed25519 — standard library extension.

---

## Testing

```go
func TestPlaceAndCancelOrder(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test")
    }

    client, err := decibel.NewClient(decibel.TestnetConfig,
        decibel.WithBearerToken(os.Getenv("BEARER_TOKEN")),
        decibel.WithPrivateKey(os.Getenv("PRIVATE_KEY")),
    )
    require.NoError(t, err)
    defer client.Close()

    ctx := context.Background()

    result, err := client.PlaceOrder(ctx, decibel.PlaceOrderParams{
        MarketName:  "BTC-USD",
        Price:       10.0,
        Size:        1.0,
        IsBuy:       true,
        TimeInForce: decibel.GoodTillCanceled,
    })
    require.NoError(t, err)
    assert.True(t, result.Success)
    assert.NotEmpty(t, result.OrderID)

    cancel, err := client.CancelOrder(ctx, decibel.CancelOrderParams{
        OrderID:    result.OrderID,
        MarketName: "BTC-USD",
    })
    require.NoError(t, err)
    assert.True(t, cancel.Success)
}
```

---

## What's NOT in the Go SDK

The Go SDK is scoped to infrastructure use cases. It deliberately excludes:

- **ML/data science integrations** — use the Python SDK for NumPy/pandas/PyTorch.
- **Sub-microsecond optimization** — use the Rust SDK for HFT hot paths.
- **GUI/interactive tooling** — use the TypeScript SDK for web interfaces.

The Go SDK focuses on: correctness, clean concurrency, simple deployment, and infrastructure-grade reliability.
