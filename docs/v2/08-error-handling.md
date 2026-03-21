# Error Handling and Observability

**Parent**: [00-overview.md](./00-overview.md)

---

## Design Principles

1. **Every error is typed** — no generic "something went wrong" exceptions.
2. **Every error is actionable** — includes `retryable`, `retry_after_ms`, and context for automated recovery.
3. **Every error is serializable** — can be logged as structured JSON for agent telemetry.
4. **Errors compose** — the hierarchy allows catch-all handling or specific matching.

---

## Error Hierarchy

```
DecibelError
│
├── ConfigError
│   Fields: message
│   Retryable: NO
│   Description: Invalid SDK configuration. Fix config and reinitialize.
│
├── AuthenticationError
│   Fields: message
│   Retryable: NO
│   Description: Invalid or expired bearer token / API key.
│
├── NetworkError
│   ├── TimeoutError
│   │   Fields: url, timeout_ms
│   │   Retryable: YES
│   │   Description: HTTP request timed out.
│   │
│   └── ConnectionError
│       Fields: url, reason
│       Retryable: YES
│       Description: TCP connection refused or reset.
│
├── ApiError
│   Fields: status, status_text, message, url
│   Retryable: depends on status
│   │
│   ├── RateLimitError (status=429)
│   │   Fields: retry_after_ms
│   │   Retryable: YES
│   │   Description: Rate limited. Wait retry_after_ms before retrying.
│   │
│   ├── NotFoundError (status=404)
│   │   Retryable: NO
│   │   Description: Resource not found.
│   │
│   └── ServerError (status=5xx)
│       Retryable: YES
│       Description: Server-side failure. Safe to retry.
│
├── ValidationError
│   Fields: field, constraint, value
│   Retryable: NO
│   Description: Input validation failure. Fix the input.
│
├── TransactionError
│   Fields: transaction_hash, vm_status, gas_used, message
│   │
│   ├── SimulationError
│   │   Fields: vm_status, message
│   │   Retryable: MAYBE (different params may succeed)
│   │   Description: Transaction simulation failed.
│   │
│   ├── GasError
│   │   Fields: estimated, available, message
│   │   Retryable: YES (with higher gas)
│   │   Description: Insufficient gas or estimation failure.
│   │
│   └── VmError
│       Fields: transaction_hash, vm_status, abort_code
│       Retryable: NO
│       Description: Move VM execution error (e.g., insufficient balance, invalid order).
│
├── WebSocketError
│   Fields: message, topic
│   Retryable: YES
│   Description: WebSocket connection or subscription failure.
│
└── SerializationError
    Fields: message, raw_data
    Retryable: NO
    Description: JSON parse/encode failure. Indicates a bug or protocol change.
```

---

## Python Implementation

```python
from dataclasses import dataclass


class DecibelError(Exception):
    """Base class for all Decibel SDK errors."""

    code: str
    message: str
    retryable: bool = False
    retry_after_ms: int | None = None

    def __init__(self, code: str, message: str, retryable: bool = False, retry_after_ms: int | None = None):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.retry_after_ms = retry_after_ms
        super().__init__(f"[{code}] {message}")

    def to_dict(self) -> dict:
        """Serialize error for structured logging."""
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "retry_after_ms": self.retry_after_ms,
            "type": type(self).__name__,
        }


class ConfigError(DecibelError):
    def __init__(self, message: str):
        super().__init__("CONFIG_ERROR", message, retryable=False)


class AuthenticationError(DecibelError):
    def __init__(self, message: str = "Invalid or expired credentials"):
        super().__init__("AUTH_ERROR", message, retryable=False)


class NetworkError(DecibelError):
    url: str

    def __init__(self, code: str, message: str, url: str):
        self.url = url
        super().__init__(code, message, retryable=True, retry_after_ms=1000)


class TimeoutError(NetworkError):
    timeout_ms: int

    def __init__(self, url: str, timeout_ms: int):
        self.timeout_ms = timeout_ms
        super().__init__("TIMEOUT", f"Request to {url} timed out after {timeout_ms}ms", url)


class ConnectionError(NetworkError):
    def __init__(self, url: str, reason: str):
        super().__init__("CONNECTION_ERROR", f"Connection to {url} failed: {reason}", url)


class ApiError(DecibelError):
    status: int
    status_text: str
    url: str

    def __init__(self, status: int, status_text: str, message: str, url: str):
        self.status = status
        self.status_text = status_text
        self.url = url
        retryable = status >= 500
        super().__init__(
            f"API_ERROR_{status}",
            f"{status} {status_text}: {message}",
            retryable=retryable,
        )


class RateLimitError(ApiError):
    def __init__(self, url: str, retry_after_ms: int = 1000):
        super().__init__(429, "Too Many Requests", "Rate limited", url)
        self.retryable = True
        self.retry_after_ms = retry_after_ms


class NotFoundError(ApiError):
    def __init__(self, url: str, message: str = "Resource not found"):
        super().__init__(404, "Not Found", message, url)


class ServerError(ApiError):
    def __init__(self, status: int, url: str, message: str):
        super().__init__(status, "Server Error", message, url)
        self.retryable = True
        self.retry_after_ms = 1000


class ValidationError(DecibelError):
    field: str
    constraint: str
    value: object

    def __init__(self, field: str, constraint: str, value: object = None):
        self.field = field
        self.constraint = constraint
        self.value = value
        super().__init__(
            "VALIDATION_ERROR",
            f"Invalid value for '{field}': {constraint}",
            retryable=False,
        )


class TransactionError(DecibelError):
    transaction_hash: str | None
    vm_status: str | None
    gas_used: int | None

    def __init__(
        self,
        code: str,
        message: str,
        transaction_hash: str | None = None,
        vm_status: str | None = None,
        gas_used: int | None = None,
        retryable: bool = False,
    ):
        self.transaction_hash = transaction_hash
        self.vm_status = vm_status
        self.gas_used = gas_used
        super().__init__(code, message, retryable=retryable)


class SimulationError(TransactionError):
    def __init__(self, vm_status: str, message: str):
        super().__init__(
            "SIMULATION_ERROR", message, vm_status=vm_status, retryable=True
        )


class GasError(TransactionError):
    def __init__(self, message: str):
        super().__init__("GAS_ERROR", message, retryable=True, retry_after_ms=2000)


class VmError(TransactionError):
    abort_code: int | None

    def __init__(
        self,
        transaction_hash: str,
        vm_status: str,
        abort_code: int | None = None,
    ):
        self.abort_code = abort_code
        super().__init__(
            "VM_ERROR",
            f"Move VM error: {vm_status}",
            transaction_hash=transaction_hash,
            vm_status=vm_status,
            retryable=False,
        )


class WebSocketError(DecibelError):
    topic: str | None

    def __init__(self, message: str, topic: str | None = None):
        self.topic = topic
        super().__init__("WS_ERROR", message, retryable=True, retry_after_ms=1000)


class SerializationError(DecibelError):
    raw_data: str | None

    def __init__(self, message: str, raw_data: str | None = None):
        self.raw_data = raw_data
        super().__init__("SERIALIZATION_ERROR", message, retryable=False)
```

---

## Rust Implementation

See [04-rust-sdk.md](./04-rust-sdk.md) for the full `DecibelError` enum with `thiserror` derive.

Key methods on `DecibelError`:

```rust
impl DecibelError {
    /// Whether this error is safe to retry.
    pub fn is_retryable(&self) -> bool;

    /// Suggested retry delay in milliseconds, if applicable.
    pub fn retry_after_ms(&self) -> Option<u64>;

    /// Machine-readable error code string.
    pub fn code(&self) -> &'static str;

    /// Serialize to JSON for structured logging.
    pub fn to_json(&self) -> serde_json::Value;
}
```

---

## Agent Error Recovery Patterns

### Automatic Retry with Backoff

```python
import asyncio

async def retry_with_backoff(
    fn,
    max_retries: int = 3,
    base_delay_ms: int = 1000,
):
    """Retry a function with exponential backoff on retryable errors."""
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except DecibelError as e:
            if not e.retryable or attempt == max_retries:
                raise
            delay_ms = e.retry_after_ms or (base_delay_ms * (2 ** attempt))
            await asyncio.sleep(delay_ms / 1000)
    raise RuntimeError("Unreachable")
```

```rust
pub async fn retry_with_backoff<F, Fut, T>(
    f: F,
    max_retries: usize,
    base_delay: Duration,
) -> Result<T, DecibelError>
where
    F: Fn() -> Fut,
    Fut: Future<Output = Result<T, DecibelError>>,
{
    for attempt in 0..=max_retries {
        match f().await {
            Ok(v) => return Ok(v),
            Err(e) if e.is_retryable() && attempt < max_retries => {
                let delay = e.retry_after_ms()
                    .map(Duration::from_millis)
                    .unwrap_or(base_delay * 2u32.pow(attempt as u32));
                tokio::time::sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
    unreachable!()
}
```

### Error Classification for Agent Decision-Making

```python
async def execute_with_classification(client, params):
    """Execute an order and classify the outcome for agent decision-making."""
    try:
        result = await client.place_order(**params)
        return {"action": "success", "order_id": result.order_id}
    except RateLimitError as e:
        return {"action": "wait", "delay_ms": e.retry_after_ms}
    except ValidationError as e:
        return {"action": "fix_params", "field": e.field, "constraint": e.constraint}
    except GasError:
        return {"action": "retry_with_higher_gas"}
    except VmError as e:
        return {"action": "abort", "reason": e.vm_status}
    except NetworkError:
        return {"action": "retry"}
```

---

## Observability

### Structured Logging

All SDK operations emit structured log events. The SDK uses:
- **Python**: `logging` stdlib with the `decibel` logger name.
- **Rust**: `tracing` crate with `decibel` as the target.

### Log Levels

| Level | What is logged |
|---|---|
| `ERROR` | All errors, failed transactions, connection failures |
| `WARN` | Rate limiting, reconnection attempts, deprecated API usage |
| `INFO` | Transaction submissions, subscription starts/stops |
| `DEBUG` | HTTP requests/responses (method, URL, status, latency) |
| `TRACE` | WebSocket messages, raw JSON payloads, deserialization details |

### Structured Event Format

Every log event includes:

```json
{
  "timestamp": 1710000000000,
  "level": "DEBUG",
  "target": "decibel::http",
  "message": "GET /api/v1/prices",
  "fields": {
    "url": "https://api.mainnet.aptoslabs.com/decibel/api/v1/prices",
    "status": 200,
    "latency_ms": 42,
    "response_bytes": 1234
  }
}
```

### Event Hook

For custom telemetry (e.g., sending metrics to Datadog, forwarding to an LLM for analysis):

```python
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="...",
    on_event=my_telemetry_handler,
)

async def my_telemetry_handler(event: dict) -> None:
    """Handle SDK events for custom observability."""
    match event["type"]:
        case "http_request":
            metrics.histogram("decibel.http.latency", event["latency_ms"])
        case "tx_submitted":
            metrics.increment("decibel.tx.submitted")
        case "ws_message":
            metrics.increment("decibel.ws.messages")
        case "error":
            metrics.increment("decibel.errors", tags=[f"code:{event['code']}"])
```

### Event Types

| Event Type | Emitted When | Key Fields |
|---|---|---|
| `http_request` | HTTP request completed | `method`, `url`, `status`, `latency_ms` |
| `http_error` | HTTP request failed | `method`, `url`, `error`, `retryable` |
| `ws_connected` | WebSocket connected | `url` |
| `ws_disconnected` | WebSocket disconnected | `url`, `reason` |
| `ws_message` | WebSocket message received | `topic`, `payload_bytes` |
| `ws_subscribe` | Topic subscribed | `topic` |
| `ws_unsubscribe` | Topic unsubscribed | `topic` |
| `tx_built` | Transaction built | `function`, `gas_price` |
| `tx_signed` | Transaction signed | `hash` |
| `tx_submitted` | Transaction submitted | `hash`, `mode` (gas_station/self_paid) |
| `tx_confirmed` | Transaction confirmed | `hash`, `gas_used`, `vm_status` |
| `tx_failed` | Transaction failed | `hash`, `vm_status`, `error` |
| `error` | Any error occurred | `code`, `message`, `retryable` |
| `gas_price_updated` | Gas price refreshed | `old_price`, `new_price` |
| `cache_hit` | Cache hit | `key`, `ttl_remaining_ms` |
| `cache_miss` | Cache miss | `key` |
