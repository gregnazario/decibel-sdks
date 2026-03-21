# Agent-First Design Principles

**Parent**: [00-overview.md](./00-overview.md)

---

## 1. Structured Data Everywhere

Every response, event, and error is a fully-typed object — never raw JSON, never untyped dictionaries. Agents must be able to introspect any value without guessing its shape.

### Requirements

- All REST responses deserialize into typed models before reaching the caller.
- All WebSocket messages are parsed and dispatched as typed events.
- All errors are structured types with machine-readable codes, not string messages alone.
- In Python: every model is a Pydantic `BaseModel` with full JSON Schema export.
- In Rust: every model derives `serde::Serialize` + `serde::Deserialize` with `#[serde(rename_all = "snake_case")]`.

### Schema Discovery

The SDK MUST expose its schema programmatically:

```python
# Python: agents can inspect the full schema at runtime
from decibel.models import MarketPrice
schema = MarketPrice.model_json_schema()
```

```rust
// Rust: schemars for JSON Schema generation
use decibel::models::MarketPrice;
let schema = schemars::schema_for!(MarketPrice);
```

## 2. Self-Documenting API

Agents (and the LLMs driving them) discover capabilities by inspecting the SDK's type signatures, docstrings, and enumerated methods. The SDK MUST be navigable without external documentation.

### Requirements

- Every public function has a docstring describing its purpose, parameters, return type, and possible errors.
- Every enum variant has a doc comment explaining when it applies.
- Client objects expose a `capabilities()` or equivalent method listing available operations.
- Market enumeration is a first-class operation — agents should be able to list all markets, all order types, all WebSocket topics.

### Python Conventions

```python
class DecibelClient:
    """Decibel trading client for AI agents.

    Provides read access to market data and account state via REST and WebSocket,
    and write access for order placement and account management via on-chain transactions.
    """

    def list_capabilities(self) -> list[str]:
        """Return all available operations on this client.

        Useful for agents discovering what actions are possible.
        """
        ...
```

### Rust Conventions

```rust
/// Decibel trading client for AI agents.
///
/// Provides read access to market data and account state via REST and WebSocket,
/// and write access for order placement and account management via on-chain transactions.
pub struct DecibelClient { /* ... */ }

impl DecibelClient {
    /// List all available operations on this client.
    ///
    /// Useful for agents discovering what actions are possible.
    pub fn capabilities(&self) -> Vec<&'static str> { /* ... */ }
}
```

## 3. Predictable, Actionable Errors

Errors must tell the agent what happened, why, and what to do about it. Every error is categorized, coded, and carries enough context for automated retry or escalation decisions.

### Requirements

- Every error type has a `code` field (enum variant or string constant).
- Every error type has a `retryable` field (bool) indicating whether the operation can be retried.
- Every error type has a `retry_after_ms` field (optional) suggesting when to retry.
- Network errors include the HTTP status code and response body.
- Transaction errors include the VM status, transaction hash, and gas consumed.
- Validation errors include the field name and constraint that was violated.

### Error Hierarchy

```
DecibelError
├── ConfigError            — invalid configuration (not retryable)
├── AuthenticationError    — invalid or expired credentials (not retryable)
├── NetworkError           — transport failure (retryable)
│   ├── TimeoutError       — request timed out (retryable)
│   └── ConnectionError    — connection refused/reset (retryable)
├── ApiError               — REST API returned error (depends on status)
│   ├── RateLimitError     — 429 (retryable after backoff)
│   ├── NotFoundError      — 404 (not retryable)
│   └── ServerError        — 5xx (retryable)
├── ValidationError        — input validation failure (not retryable)
├── TransactionError       — on-chain tx failure (depends on reason)
│   ├── SimulationError    — tx simulation failed (retryable with different params)
│   ├── GasError           — insufficient gas or estimation failure (retryable)
│   └── VmError            — Move VM execution error (not retryable)
├── WebSocketError         — WS connection or subscription error (retryable)
└── SerializationError     — JSON parse/encode failure (not retryable)
```

## 4. High Performance by Default

The SDK MUST be fast without requiring the agent to configure anything. Performance optimizations are built-in, not opt-in.

### Requirements

- HTTP connection pooling is always enabled (HTTP/2 where supported).
- WebSocket uses a single shared connection for all subscriptions.
- Gas prices are cached and refreshed in the background.
- Market configurations are cached after first fetch with configurable TTL.
- USDC decimals are cached after first fetch (immutable value).
- Transaction building is synchronous — no network calls during construction.
- Replay protection nonces are generated locally (no sequence number fetch).
- Serialization uses zero-copy or code-generated paths where possible.

### Benchmarks (targets)

| Operation | Python Target | Rust Target |
|---|---|---|
| REST GET (cached connection) | < 50ms | < 10ms |
| WebSocket message parse | < 1ms | < 100μs |
| Transaction build (sync) | < 5ms | < 500μs |
| Transaction sign | < 2ms | < 200μs |
| JSON deserialize (MarketPrice) | < 500μs | < 50μs |

## 5. Composable Operations

Agents build strategies by chaining atomic operations. The SDK MUST provide small, focused functions that compose cleanly.

### Requirements

- Every write operation returns a result with the transaction hash and any extracted data (order ID, subaccount address, etc.).
- Read operations accept explicit parameters — no ambient state or side effects.
- Pagination is handled via explicit `PageParams` — never hidden cursors.
- Subscriptions return an unsubscribe handle — the agent controls the lifecycle.
- Batch operations are available where the protocol supports them (bulk orders).

### Composition Example

```python
# Agent workflow: check position, adjust TP/SL, rebalance
position = await client.get_positions(subaccount)
for pos in position:
    if pos.unrealized_pnl > threshold:
        await client.update_tp_order(
            market_addr=pos.market,
            prev_order_id=pos.tp_order_id,
            tp_trigger_price=pos.entry_price * 1.05,
        )
```

## 6. Observable and Traceable

Agents need to monitor their own behavior. The SDK provides hooks for logging, metrics, and tracing without requiring external instrumentation.

### Requirements

- All HTTP requests log method, URL, status, and latency at DEBUG level.
- All WebSocket messages log topic and payload size at TRACE level.
- All transactions log hash, gas used, and VM status at INFO level.
- All errors log the full error context at ERROR level.
- A configurable `on_event` callback receives structured events for custom telemetry.
- Python: uses `logging` stdlib. Rust: uses `tracing` crate.

## 7. Safe Defaults, Explicit Overrides

The SDK ships with sensible defaults for every parameter but allows agents to override anything. No hidden magic.

### Requirements

- Default timeout: 30 seconds for REST, 60 seconds for transaction confirmation.
- Default gas multiplier: 1.5x estimated gas price.
- Default transaction expiry: 600 seconds (10 minutes).
- Default WebSocket reconnect: exponential backoff starting at 1 second, max 30 seconds.
- Default max subscriptions per connection: 100 (server limit).
- All defaults are documented in the config struct and overridable at construction time.

## 8. Idempotent Where Possible

Agents may retry operations. The SDK MUST make retries safe where the protocol allows.

### Requirements

- `client_order_id` is exposed as a first-class parameter for order idempotency.
- Read operations are naturally idempotent.
- The SDK warns (does not error) when re-subscribing to an already-active WebSocket topic.
- Transaction replay protection is built-in via random nonces.
- Deposit/withdraw operations are idempotent at the transaction level (unique nonce per tx).

## 9. Minimal Dependencies

The SDK MUST not pull in the world. Every dependency must justify its presence.

### Python Dependencies

| Package | Purpose | Justification |
|---|---|---|
| `httpx` | HTTP client | Async, HTTP/2, connection pooling |
| `websockets` | WebSocket client | Lightweight, async |
| `pydantic` | Data models | Validation, JSON Schema, serialization |
| `cryptography` | Ed25519 signing | Transaction signing |
| `aptos-sdk` | Aptos transaction building | BCS serialization, address derivation |

### Rust Dependencies

| Crate | Purpose | Justification |
|---|---|---|
| `tokio` | Async runtime | Industry standard for async Rust |
| `reqwest` | HTTP client | Connection pooling, TLS |
| `tokio-tungstenite` | WebSocket | Tokio-native WebSocket |
| `serde` / `serde_json` | Serialization | Zero-cost derive macros |
| `ed25519-dalek` | Signing | Pure-Rust Ed25519 |
| `bcs` | BCS serialization | Aptos binary format |
| `thiserror` | Error types | Ergonomic error enums |
| `tracing` | Observability | Structured logging |
| `schemars` | JSON Schema | Schema export for agent discovery |

## 10. Test-Driven Contract

Every SDK feature is specified with test cases. The specification defines the expected behavior; implementations must pass these tests.

### Test Categories

| Category | Description |
|---|---|
| **Unit** | Individual function behavior (serialization, address derivation, price rounding) |
| **Integration** | Full client workflows against testnet (place order → check status → cancel) |
| **Property** | Fuzz-tested invariants (round-trip serialization, price rounding monotonicity) |
| **Agent Scenario** | Multi-step agent workflows (monitoring → decision → execution → verification) |
