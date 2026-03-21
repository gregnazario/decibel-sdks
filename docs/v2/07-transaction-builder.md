# On-Chain Transaction Builder Specification

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

The transaction builder handles all write operations on the Decibel exchange. It constructs, signs, and submits Aptos Move transactions for order placement, account management, vault operations, and delegation.

For agents, transaction building MUST be synchronous (no network calls during construction) to minimize latency in decision-execution loops.

## Architecture

```
Agent Call (e.g., place_order)
    │
    ├─ 1. Resolve parameters (market name → address, format prices)
    ├─ 2. Build transaction payload (SYNC — no network calls)
    │     ├─ Load ABI (cached)
    │     ├─ Generate replay protection nonce (local random)
    │     ├─ Compute expiration timestamp (local clock + delta)
    │     └─ Construct RawTransaction
    ├─ 3. [Optional] Simulate transaction (async, skippable)
    ├─ 4. Sign transaction (Ed25519, local)
    ├─ 5. Submit transaction (async)
    │     ├─ Mode A: Gas Station (sponsored)
    │     ├─ Mode B: Self-paid (direct to fullnode)
    │     └─ Retry on transient failure
    └─ 6. Wait for confirmation + extract events
```

---

## Latency Breakdown: Build-Sign-Submit Pipeline

Every millisecond between signal detection and order reaching the matching engine is potential slippage. Here is the full latency budget for a single order:

### Python SDK

| Stage | Operation | Latency (P50) | Latency (P99) | Notes |
|---|---|---|---|---|
| 1 | Market name → address lookup | < 1μs | < 5μs | In-memory HashMap |
| 2 | Price rounding to tick_size | < 10μs | < 50μs | Pure arithmetic |
| 3 | Size rounding to lot_size | < 10μs | < 50μs | Pure arithmetic |
| 4 | Chain unit conversion | < 5μs | < 20μs | Multiply by 10^decimals |
| 5 | ABI lookup | < 1μs | < 5μs | Cached in dict |
| 6 | Nonce generation | < 5μs | < 20μs | `secrets.token_bytes(8)` |
| 7 | Payload construction | < 500μs | < 2ms | BCS serialization |
| 8 | RawTransaction assembly | < 200μs | < 1ms | Struct construction |
| **Build subtotal** | | **< 2ms** | **< 5ms** | **Zero network calls** |
| 9 | Ed25519 signing | < 500μs | < 2ms | cryptography lib |
| 10a | Gas Station submission | 50–150ms | 300ms | POST to gas station |
| 10b | Self-paid submission | 30–100ms | 200ms | POST to fullnode |
| 11 | Transaction confirmation | 500ms–2s | 4s | Aptos block time (~1-2s) |
| **Total (signal → confirmed)** | | **~600ms** | **~4s** | Network-dominated |

### Rust SDK

| Stage | Operation | Latency (P50) | Latency (P99) | Notes |
|---|---|---|---|---|
| 1–6 | Parameter resolution + nonce | < 10μs | < 50μs | All in-memory |
| 7–8 | Payload + RawTransaction build | < 100μs | < 500μs | BCS serialization |
| **Build subtotal** | | **< 200μs** | **< 1ms** | **Zero network calls** |
| 9 | Ed25519 signing | < 50μs | < 200μs | ed25519-dalek |
| 10a | Gas Station submission | 30–100ms | 200ms | POST to gas station |
| 10b | Self-paid submission | 20–80ms | 150ms | POST to fullnode |
| 11 | Transaction confirmation | 500ms–2s | 4s | Aptos block time |
| **Total (signal → confirmed)** | | **~550ms** | **~4s** | Network-dominated |

### Key Insight

Build + sign is < 5ms even in Python. The latency is dominated by network submission (50-150ms) and Aptos block confirmation (~1-2s). Optimizing the build path further has diminishing returns — optimizing submission routing and confirmation polling is where latency gains come from.

### Where to Focus Optimization Effort

```
Signal detected ──────────────────────────────────────────── Order confirmed
  │                                                                │
  ├─ Build (< 5ms) ─┤─ Sign (< 2ms) ─┤─ Submit (50-150ms) ─┤─ Confirm (500ms-2s) ─┤
  │   0.5% of total  │  0.2% of total  │   10-20% of total   │   80-90% of total    │
  │                  │                  │                      │                       │
  │  NOT worth       │  NOT worth       │  Worth optimizing:   │  Worth optimizing:    │
  │  optimizing      │  optimizing      │  - Colocate near     │  - Fire-and-forget    │
  │                  │                  │    fullnode           │    for quotes          │
  │                  │                  │  - Self-paid (skip    │  - Optimistic+verify  │
  │                  │                  │    gas station hop)   │    for entries         │
  │                  │                  │  - HTTP/2 persistent  │  - Skip for non-      │
  │                  │                  │    connections         │    critical txns       │
```

### Reducing End-to-End Latency: Practical Techniques

| Technique | Latency Saved | Complexity | Applicable To |
|---|---|---|---|
| Skip simulation (`skip_simulate=True`) | 50–200ms | Low | All order types after initial testing |
| Self-paid instead of gas station | 20–50ms | Low | High-frequency bots |
| HTTP/2 persistent connection to fullnode | 10–30ms per request | Low | All bots |
| Colocate bot near fullnode | 10–50ms RTT reduction | Medium | Latency-sensitive market makers |
| Fire-and-forget submission (skip confirmation) | 500ms–2s | Low | Quote updates, non-critical orders |
| Pre-build transactions (prepare payload before signal) | ~5ms | Medium | Predictable order patterns |
| Parallel bid+ask bulk orders | 50–150ms (half the sequential time) | Low | Market makers |

---

## Orderless Transactions

Decibel uses orderless transactions on Aptos: a random 64-bit replay protection nonce replaces the sequential sequence number. This enables:

- **No sequence number fetch**: No network call to get account state.
- **Parallel submission**: Multiple transactions can be built and submitted simultaneously.
- **Offline construction**: Transactions can be prepared before network is available.

### Replay Protection Nonce Generation

```python
import secrets

def generate_replay_protection_nonce() -> int:
    """Generate a random 64-bit nonce for transaction replay protection."""
    return int.from_bytes(secrets.token_bytes(8), byteorder="big")
```

```rust
use rand::Rng;

pub fn generate_replay_protection_nonce() -> u64 {
    rand::thread_rng().gen::<u64>()
}
```

### Expiration Timestamp

```python
import time

def generate_expiration_timestamp(ttl_seconds: int = 600) -> int:
    """Generate transaction expiration timestamp.

    Args:
        ttl_seconds: Time-to-live in seconds (default: 10 minutes).
    """
    return int(time.time()) + ttl_seconds
```

```rust
pub fn generate_expiration_timestamp(ttl_seconds: u64) -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs()
        + ttl_seconds
}
```

---

## Clock Drift Handling: `time_delta_ms`

Transaction expiration timestamps are compared against the Aptos chain's clock, not the bot's local clock. If the bot's clock drifts relative to the chain, transactions can expire prematurely (clock ahead) or linger in the mempool longer than expected (clock behind).

### Why Clock Drift Matters

| Drift Direction | Effect | Symptom |
|---|---|---|
| Bot clock **ahead** by 5s | Expiration timestamp is 5s in the "future" from chain's perspective | Transactions appear to have a shorter TTL than configured. A 600s TTL actually becomes ~595s. Usually harmless. |
| Bot clock **behind** by 5s | Expiration timestamp is 5s in the "past" from chain's perspective | Transactions appear to have a longer TTL. Usually harmless. |
| Bot clock **ahead** by 60s+ | Severe: chain may reject transactions as "already expired" if TTL is short | `TRANSACTION_EXPIRED` VM errors on submission |
| Bot clock **behind** by 60s+ | Transactions linger in mempool much longer than expected | Stale orders executing minutes after being "cancelled" by the bot |

For a market maker with a 60-second TTL, even 10 seconds of clock drift causes problems. For a directional bot with a 10-minute TTL, 10 seconds is irrelevant.

### Computing `time_delta_ms`

The `time_delta_ms` value represents the offset between the bot's local clock and the Aptos chain's clock: `chain_time - local_time`. A positive value means the chain is ahead of the bot.

```python
class ClockDriftManager:
    def __init__(self, fullnode_url: str, refresh_interval_s: float = 60.0):
        self._fullnode_url = fullnode_url
        self._refresh_interval = refresh_interval_s
        self._time_delta_ms: int = 0
        self._samples: collections.deque = collections.deque(maxlen=10)
        self._task: asyncio.Task | None = None

    async def start(self):
        await self._measure()
        self._task = asyncio.create_task(self._refresh_loop())

    async def _measure(self):
        """Measure clock drift by comparing local time with ledger timestamp."""
        local_before_ms = int(time.time() * 1000)
        ledger_info = await self._http.get(f"{self._fullnode_url}/v1/")
        local_after_ms = int(time.time() * 1000)
        rtt_ms = local_after_ms - local_before_ms
        local_midpoint_ms = local_before_ms + rtt_ms // 2
        chain_time_ms = int(ledger_info["ledger_timestamp"]) // 1000  # μs → ms
        delta = chain_time_ms - local_midpoint_ms
        self._samples.append(delta)
        self._time_delta_ms = int(statistics.median(self._samples))

    async def _refresh_loop(self):
        while True:
            await asyncio.sleep(self._refresh_interval)
            try:
                await self._measure()
            except Exception as e:
                logger.warning(f"Clock drift measurement failed: {e}")

    @property
    def time_delta_ms(self) -> int:
        return self._time_delta_ms
```

```rust
pub struct ClockDriftManager {
    time_delta_ms: AtomicI64,
    samples: Mutex<VecDeque<i64>>,
    fullnode_url: String,
}

impl ClockDriftManager {
    pub fn time_delta_ms(&self) -> i64 {
        self.time_delta_ms.load(Ordering::Relaxed)
    }

    pub async fn measure(&self) -> Result<(), DecibelError> {
        let before = SystemTime::now().duration_since(UNIX_EPOCH)?.as_millis() as i64;
        let ledger = self.client.get_ledger_info().await?;
        let after = SystemTime::now().duration_since(UNIX_EPOCH)?.as_millis() as i64;
        let rtt = after - before;
        let local_midpoint = before + rtt / 2;
        let chain_time_ms = (ledger.ledger_timestamp / 1000) as i64; // μs → ms
        let delta = chain_time_ms - local_midpoint;
        let mut samples = self.samples.lock().unwrap();
        samples.push_back(delta);
        if samples.len() > 10 { samples.pop_front(); }
        let mut sorted: Vec<_> = samples.iter().copied().collect();
        sorted.sort();
        let median = sorted[sorted.len() / 2];
        self.time_delta_ms.store(median, Ordering::Relaxed);
        Ok(())
    }
}
```

### Applying `time_delta_ms` to Transaction Building

The `build_transaction_sync` function accepts `time_delta_ms` and adjusts the expiration timestamp:

```python
expiration = int(time.time()) + ttl_seconds
if time_delta_ms:
    expiration += time_delta_ms // 1000
```

This shifts the expiration forward (if bot clock is behind) or backward (if bot clock is ahead) to align with chain time.

### Recommended TTL by Order Type

| Order Type | Recommended TTL | Why |
|---|---|---|
| Market maker quotes | 60s | Quotes are replaced frequently; short TTL prevents stale quotes from executing after a crash |
| IOC / aggressive orders | 60s | Should execute immediately; expiration is just a safety net |
| GTC limit orders | 600s (10min) | Need time to rest in the book; resubmit before expiry if still wanted |
| TWAP slices | 120s | Individual slices are time-bounded |
| Emergency closes | 30s | Must execute now or not at all — if it doesn't land in 30s, something is wrong |
| Deposits / withdrawals | 600s | No urgency, but don't want them lingering forever |

### Clock Drift Alerting

| Drift Magnitude | Severity | Action |
|---|---|---|
| < 1s | Normal | No action needed |
| 1–5s | Warning | Log, continue operating |
| 5–30s | Elevated | Increase TTL on all transactions, alert operator |
| > 30s | Critical | Halt trading, alert operator, investigate NTP sync |

---

## Parallel Transaction Submission

Orderless nonces are the key enabler for parallel order placement. Unlike sequential nonce systems (Ethereum), where transaction N+1 cannot be mined until transaction N is confirmed, Decibel's random nonces allow truly independent transactions.

### Use Cases for Parallel Submission

| Scenario | Parallel Txns | Example |
|---|---|---|
| Multi-market entry | 2–10 | Buy BTC-USD, ETH-USD, SOL-USD simultaneously |
| Bracket order | 2–3 | Place order + set TP + set SL |
| Quote replacement | 2 | Cancel old quote + place new quote (or use bulk orders) |
| Emergency exit | N | Close all positions across all markets simultaneously |

### Python: Parallel Order Placement

```python
import asyncio

async def enter_positions(client, signals: list[dict]):
    """Place orders for multiple markets in parallel."""
    tasks = []
    for signal in signals:
        task = client.place_order(
            market_name=signal["market"],
            price=signal["price"],
            size=signal["size"],
            is_buy=signal["is_buy"],
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=False,
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for signal, result in zip(signals, results):
        if isinstance(result, Exception):
            logger.error(f"Order failed for {signal['market']}: {result}")
        else:
            logger.info(f"Order placed for {signal['market']}: {result.order_id}")
    return results
```

### Rust: Parallel Order Placement

```rust
let (btc, eth, sol) = tokio::join!(
    client.place_order(PlaceOrderParams {
        market_name: "BTC-USD".into(),
        price: 68000.0,
        size: 0.1,
        is_buy: true,
        time_in_force: TimeInForce::ImmediateOrCancel,
        ..Default::default()
    }),
    client.place_order(PlaceOrderParams {
        market_name: "ETH-USD".into(),
        price: 3400.0,
        size: 1.5,
        is_buy: true,
        time_in_force: TimeInForce::ImmediateOrCancel,
        ..Default::default()
    }),
    client.place_order(PlaceOrderParams {
        market_name: "SOL-USD".into(),
        price: 145.0,
        size: 20.0,
        is_buy: true,
        time_in_force: TimeInForce::ImmediateOrCancel,
        ..Default::default()
    }),
);
```

### Throughput Ceiling

Parallel submission is bounded by:
1. **Gas Station rate limit**: The gas station API may have its own rate limit (typically 10-50 tx/sec per account).
2. **Aptos mempool**: The fullnode accepts transactions faster than they can be included in blocks.
3. **Block time**: Aptos produces blocks every ~1-2 seconds. Each block includes many transactions, but confirmation latency is still 1-2s regardless of how fast you submit.

For a market maker sending 10 quote updates/second (5 markets × 2 sides), parallel submission is essential — sequential submission would take 10 × 100ms = 1s, leaving quotes stale before the last one submits. With parallel submission, all 10 go out in ~100ms.

### Practical Parallel Patterns

**Pattern 1: Multi-market quote refresh.** Update all markets simultaneously:

```python
async def refresh_all_quotes(self, markets: list[str], quotes: dict[str, QuoteLevels]):
    """Refresh bid and ask quotes for all markets in parallel."""
    tasks = []
    for market in markets:
        levels = quotes[market]
        tasks.append(self._client.place_bulk_order(
            market_name=market, is_buy=True, levels=levels.bids,
        ))
        tasks.append(self._client.place_bulk_order(
            market_name=market, is_buy=False, levels=levels.asks,
        ))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            market = markets[i // 2]
            side = "bid" if i % 2 == 0 else "ask"
            logger.error(f"Quote refresh failed: {market} {side}: {result}")
```

**Pattern 2: Emergency close all positions.** Close every position across every market simultaneously:

```python
async def emergency_close_all(self, positions: list[Position]):
    """Close all positions with aggressive IOC orders in parallel."""
    tasks = []
    for pos in positions:
        tasks.append(self._client.place_order(
            market_name=pos.market_name,
            price=0 if pos.size > 0 else float('inf'),  # market-like IOC
            size=abs(pos.size),
            is_buy=pos.size < 0,  # buy to close short, sell to close long
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=True,
        ))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    closed = sum(1 for r in results if not isinstance(r, Exception))
    failed = sum(1 for r in results if isinstance(r, Exception))
    logger.critical(f"Emergency close: {closed} succeeded, {failed} failed")
```

**Pattern 3: Nonce independence verification.** Each parallel transaction uses its own random nonce. There is no need to coordinate between them:

```python
# These three transactions have independent nonces and can be submitted
# to different fullnodes or the same fullnode without conflict.
tx1 = build_transaction_sync(sender, "place_order_to_subaccount", ...)  # nonce: 0xA3F2...
tx2 = build_transaction_sync(sender, "place_order_to_subaccount", ...)  # nonce: 0x7B1C...
tx3 = build_transaction_sync(sender, "cancel_order_to_subaccount", ...) # nonce: 0xE9D4...
# All three can be signed and submitted simultaneously
```

---

## Transaction Building (Synchronous)

The core transaction builder takes pre-resolved parameters and constructs a `RawTransaction` with zero network calls.

### Inputs

| Input | Source | Network Required |
|---|---|---|
| Sender address | Private key derivation | NO |
| Function name | Hardcoded per operation | NO |
| Type arguments | Hardcoded per operation | NO |
| Function arguments | Agent-provided, formatted | NO |
| ABI | Cached from initial fetch | NO (after first call) |
| Chain ID | Cached from config or initial fetch | NO (after first call) |
| Gas unit price | Cached from GasPriceManager | NO (refreshed in background) |
| Max gas amount | Config default or simulation result | NO |
| Replay nonce | Local random generation | NO |
| Expiration | Local clock computation | NO |

### Build Flow

```python
def build_transaction_sync(
    sender: str,
    function: str,
    function_arguments: list,
    type_arguments: list,
    abi: dict,
    chain_id: int,
    gas_unit_price: int,
    max_gas_amount: int = 100_000,
    ttl_seconds: int = 600,
    time_delta_ms: int = 0,
) -> RawTransaction:
    """Build an Aptos transaction synchronously.

    No network calls are made during this function.
    All parameters must be pre-resolved.
    """
    nonce = generate_replay_protection_nonce()
    expiration = generate_expiration_timestamp(ttl_seconds)
    if time_delta_ms:
        expiration += time_delta_ms // 1000

    payload = build_entry_function_payload(function, type_arguments, function_arguments, abi)

    return RawTransaction(
        sender=sender,
        sequence_number=0xDEADBEEF,  # unused with replay nonce
        payload=embed_replay_nonce(payload, nonce),
        max_gas_amount=max_gas_amount,
        gas_unit_price=gas_unit_price,
        expiration_timestamp_secs=expiration,
        chain_id=chain_id,
    )
```

---

## ABI Bundling Strategy

The SDK MUST ship all known Decibel entry function ABIs as static data bundled into the package. This eliminates runtime ABI fetching entirely.

### Why Bundling Matters

| Without bundling | With bundling |
|---|---|
| First `place_order` call: fetch ABI from fullnode (~200ms) | First `place_order` call: read from memory (< 1μs) |
| ABI fetch can fail (network error) | No network dependency |
| Must cache + handle cache invalidation | Static data, never stale |
| Cold start penalty for every new function | All functions available immediately |

### Bundled ABI Set

The SDK bundles ABIs for every Decibel entry function:

| Module | Functions | Count |
|---|---|---|
| `dex_accounts_entry` | `place_order_to_subaccount` | 1 |
| `dex_accounts` | `cancel_order_to_subaccount`, `cancel_client_order_to_subaccount`, `create_new_subaccount`, `deposit_to_subaccount_at`, `withdraw_from_subaccount`, `configure_user_settings_for_market`, `place_twap_order_to_subaccount`, `cancel_twap_order_to_subaccount`, `place_bulk_order`, `cancel_bulk_order`, `place_tp_sl_order_for_position`, `update_tp_order_for_position`, `update_sl_order_for_position`, `cancel_tp_sl_order_for_position`, `delegate_trading_to_for_subaccount`, `revoke_delegation`, `approve_max_builder_fee`, `revoke_max_builder_fee` | 18 |
| `vaults` | `create_and_fund_vault`, `activate_vault`, `contribute_to_vault`, `redeem_from_vault`, `delegate_dex_actions_to` | 5 |

### Python: Bundled ABIs

```python
import json
from importlib import resources

_BUNDLED_ABIS: dict[str, dict] = {}

def _load_bundled_abis():
    global _BUNDLED_ABIS
    abi_data = resources.read_text("decibel.data", "abis.json")
    _BUNDLED_ABIS = json.loads(abi_data)

def get_abi(function_name: str) -> dict:
    if not _BUNDLED_ABIS:
        _load_bundled_abis()
    abi = _BUNDLED_ABIS.get(function_name)
    if abi is None:
        raise ConfigError(f"No ABI found for function: {function_name}")
    return abi
```

### Rust: Bundled ABIs

```rust
use once_cell::sync::Lazy;
use std::collections::HashMap;

static BUNDLED_ABIS: Lazy<HashMap<&str, AbiDefinition>> = Lazy::new(|| {
    let json = include_str!("../data/abis.json");
    serde_json::from_str(json).expect("bundled ABIs must be valid JSON")
});

pub fn get_abi(function_name: &str) -> Result<&AbiDefinition, DecibelError> {
    BUNDLED_ABIS.get(function_name)
        .ok_or_else(|| DecibelError::Config(format!("No ABI for: {}", function_name)))
}
```

### ABI Format

```json
{
  "name": "place_order_to_subaccount",
  "visibility": "friend",
  "is_entry": true,
  "is_view": false,
  "generic_type_params": [],
  "params": ["&signer", "address", "address", "u64", "u64", "bool", "u8", "bool", "0x1::option::Option<u128>", "0x1::option::Option<u64>", "0x1::option::Option<u64>", "0x1::option::Option<u64>", "0x1::option::Option<u64>", "0x1::option::Option<u64>", "0x1::option::Option<address>", "0x1::option::Option<u64>"],
  "return": []
}
```

### ABI Versioning Strategy

Decibel contracts may be upgraded, adding new parameters to existing entry functions or adding new entry functions. The SDK must handle this gracefully.

**Versioning approach**: The bundled `abis.json` file includes a version field and a mapping from SDK version to supported contract version:

```json
{
  "abi_version": "2.1.0",
  "min_contract_version": "2.0.0",
  "max_contract_version": "2.1.0",
  "functions": {
    "place_order_to_subaccount": { ... },
    "place_bulk_order": { ... }
  }
}
```

**On contract upgrade**: When Decibel upgrades the on-chain contract, the new ABI may add optional parameters to existing functions. The SDK handles this by:

1. **Additive parameters**: New optional parameters are appended to the end of the parameter list. Old SDK versions that don't send them still work — the chain fills in defaults.
2. **New functions**: New entry functions can only be called by SDK versions that bundle the new ABI. Calling an unknown function produces a `ConfigError` at build time, not a runtime error.
3. **Breaking changes**: If a parameter type changes (rare), the old ABI is incompatible. The SDK should compare its bundled version against the on-chain version and warn if mismatched.

**Runtime ABI version check** (optional, for defense-in-depth):

```python
async def check_abi_compatibility(self) -> bool:
    """Verify that bundled ABIs are compatible with the deployed contract."""
    try:
        on_chain_module = await self._fullnode.get_account_module(
            self._package_addr, "dex_accounts"
        )
        on_chain_functions = {f["name"] for f in on_chain_module["abi"]["exposed_functions"]}
        bundled_functions = set(_BUNDLED_ABIS.keys())
        missing = bundled_functions - on_chain_functions
        if missing:
            logger.error(f"Bundled ABIs reference functions not on chain: {missing}")
            return False
        return True
    except Exception as e:
        logger.warning(f"ABI compatibility check failed: {e}")
        return True  # assume compatible on failure
```

**SDK update cadence**: The SDK should be updated within 24 hours of any Decibel contract upgrade that adds new functions. Minor parameter additions (new optional parameters with defaults) do not require an SDK update.

---

## Transaction Signing

All transactions are signed with Ed25519.

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def sign_transaction(raw_tx: RawTransaction, private_key: Ed25519PrivateKey) -> SignedTransaction:
    """Sign a raw transaction with an Ed25519 private key."""
    signing_message = raw_tx.signing_message()
    signature = private_key.sign(signing_message)
    return SignedTransaction(raw_tx, signature)
```

```rust
use ed25519_dalek::{SigningKey, Signer};

pub fn sign_transaction(raw_tx: &RawTransaction, key: &SigningKey) -> SignedTransaction {
    let signing_message = raw_tx.signing_message();
    let signature = key.sign(&signing_message);
    SignedTransaction::new(raw_tx.clone(), signature)
}
```

### Account Override

Write operations accept an optional `account_override` parameter for signing with a different key (e.g., session keys, delegated accounts):

```python
result = await client.place_order(
    market_name="BTC-USD",
    price=45000.0,
    size=0.25,
    is_buy=True,
    time_in_force=TimeInForce.GoodTillCanceled,
    is_reduce_only=False,
    account_override=session_key,
)
```

---

## Transaction Submission

### Mode 1: Gas Station (Sponsored Transactions)

When `gas_station_url` and `gas_station_api_key` are configured:

1. Build transaction with fee payer placeholder (`AccountAddress::ZERO`).
2. Sign the transaction (sender signature only).
3. POST to gas station API, which signs as fee payer and submits.

```
POST {gas_station_url}/transactions
Headers:
  Authorization: Bearer {gas_station_api_key}
Body: {
  "signature": "<sender_signature_bytes_hex>",
  "transaction": "<raw_transaction_bytes_hex>"
}
```

### Mode 2: Self-Paid

When `no_fee_payer` is `true` or gas station is not configured:

1. Build transaction without fee payer.
2. Sign the transaction.
3. Submit directly to Aptos fullnode via `POST /v1/transactions`.

### Submission Retry

| Failure Type | Retry |
|---|---|
| Network error | Retry up to 3 times with exponential backoff |
| Gas estimation failure | Retry with higher gas price |
| 429 rate limit | Retry after `Retry-After` delay |
| VM error | Do NOT retry (transaction is invalid) |

---

## Transaction Confirmation Monitoring

After submission, the bot needs to efficiently determine whether the transaction was included in a block and what the outcome was.

### Polling Strategy

```python
async def wait_for_confirmation(
    client: HttpClient,
    tx_hash: str,
    timeout_ms: int = 10_000,
    poll_interval_ms: int = 500,
) -> TransactionResult:
    """Poll fullnode for transaction confirmation.

    Uses exponential backoff: 200ms, 400ms, 800ms, then 1s steady-state.
    """
    start = time.monotonic()
    interval = 0.2  # start at 200ms

    while (time.monotonic() - start) * 1000 < timeout_ms:
        try:
            result = await client.get(f"/v1/transactions/by_hash/{tx_hash}")
            if result.get("type") == "user_transaction":
                success = result.get("success", False)
                return TransactionResult(
                    hash=tx_hash,
                    success=success,
                    vm_status=result.get("vm_status"),
                    gas_used=int(result.get("gas_used", 0)),
                    events=result.get("events", []),
                    version=int(result.get("version", 0)),
                )
        except NotFoundError:
            pass  # transaction not yet indexed

        await asyncio.sleep(interval)
        interval = min(interval * 2, 1.0)

    raise TimeoutError(f"Transaction {tx_hash} not confirmed within {timeout_ms}ms")
```

### Event Extraction

Transaction events contain the actual outcome — order ID, fill price, fill size, etc. The SDK parses these from the confirmed transaction:

```python
def extract_order_events(tx_result: TransactionResult) -> list[OrderEvent]:
    events = []
    for event in tx_result.events:
        if "OrderPlaced" in event["type"]:
            events.append(OrderEvent(
                event_type="placed",
                order_id=event["data"]["order_id"],
                market=event["data"]["market"],
                price=int(event["data"]["price"]),
                size=int(event["data"]["size"]),
                side="buy" if event["data"]["is_buy"] else "sell",
            ))
        elif "OrderFilled" in event["type"]:
            events.append(OrderEvent(
                event_type="filled",
                order_id=event["data"]["order_id"],
                fill_price=int(event["data"]["fill_price"]),
                fill_size=int(event["data"]["fill_size"]),
                fee=int(event["data"]["fee"]),
            ))
    return events
```

### Fire-and-Forget vs Wait-for-Confirm

Bots can choose their confirmation strategy:

| Strategy | Use Case | Latency | Risk |
|---|---|---|---|
| **Fire-and-forget** | High-frequency quoting where stale quotes are worse than unconfirmed ones | ~100ms | May not know if order landed |
| **Wait-for-confirm** | Directional trades where position tracking must be accurate | ~1-3s | Higher latency, but guaranteed state awareness |
| **Optimistic + verify** | Submit, assume success, verify asynchronously via WS `order_updates` | ~100ms submit + async verify | Best of both worlds for most bots |

```python
# Fire-and-forget
tx_hash = await client.submit_transaction(signed_tx)

# Wait-for-confirm
result = await client.place_order(market_name="BTC-USD", ...)

# Optimistic + verify
tx_hash = await client.submit_transaction(signed_tx)
# ... continue processing ...
# Later, when order_updates WS callback fires:
async def on_order_update(update: OrderUpdate):
    if update.client_order_id == my_order_id:
        confirmed = True
```

---

## Transaction Simulation

When `skip_simulate` is `false` (default), the SDK simulates before submitting:

1. Build transaction with estimated gas.
2. Submit to `/v1/transactions/simulate` endpoint.
3. Parse simulation result for gas estimate and potential errors.
4. If simulation succeeds, rebuild with actual gas estimate (with multiplier).
5. If simulation fails, return `SimulationError` with the VM error.

Agents can skip simulation for lower latency:

```python
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="...",
    private_key="0x...",
    skip_simulate=True,
)
```

---

## Gas Optimization: Strategy and Submission Mode Selection

Gas costs on Aptos are low compared to EVM chains, but for a market maker sending 100+ transactions per minute, they accumulate. The gas strategy has two dimensions: (1) gas station vs self-paid submission, and (2) gas price multiplier selection.

### Gas Station vs Self-Paid: When to Use Each

| Factor | Gas Station (Sponsored) | Self-Paid (Direct) |
|---|---|---|
| **Setup** | Requires `gas_station_url` + `gas_station_api_key` | Requires APT in the signing account |
| **Latency** | ~50–150ms (extra hop to gas station API) | ~30–100ms (direct to fullnode) |
| **Cost to bot** | Free (sponsor pays) | Bot pays gas in APT |
| **Rate limits** | Gas station may enforce its own rate limits (typically 10–50 tx/s) | Fullnode mempool limits (~50–100 tx/s per account) |
| **Reliability** | Additional point of failure (gas station downtime) | Direct dependency on fullnode only |
| **Account management** | No APT balance needed | Must maintain APT balance |

**Recommendation by bot type:**

| Bot Type | Recommended Mode | Reasoning |
|---|---|---|
| Market maker (high frequency) | **Self-paid** | Lower latency matters. Gas cost per quote update is tiny. Avoid gas station rate limits. |
| Market maker (getting started) | **Gas station** | Simpler setup. Switch to self-paid once volume justifies it. |
| Directional bot | **Gas station** | Low frequency, latency is less critical, simplifies APT balance management. |
| Risk monitor (cancel-only) | **Gas station** | Rare transactions, simplicity wins. |
| TWAP agent | **Gas station** | Moderate frequency, latency tolerance is high (slices are minutes apart). |

### Fallback Between Modes

The SDK should support automatic fallback: if gas station submission fails (timeout, 5xx, rate limit), fall back to self-paid for that transaction:

```python
async def submit_with_fallback(
    self,
    signed_tx: SignedTransaction,
    prefer_gas_station: bool = True,
) -> str:
    if prefer_gas_station and self._gas_station_available:
        try:
            return await self._submit_via_gas_station(signed_tx)
        except (TimeoutError, GasStationError) as e:
            logger.warning(f"Gas station failed ({e}), falling back to self-paid")
    return await self._submit_direct(signed_tx)
```

### Gas Price Multiplier Tuning

The `GasPriceManager` runs in the background, periodically fetching and caching gas price estimates. Bots must balance between paying too much for gas (waste) and paying too little (transactions stuck in mempool).

| Multiplier | Effect | Use Case |
|---|---|---|
| 1.0x | Exact estimated gas price | Low-priority transactions, cost-sensitive |
| 1.5x (default) | 50% above estimate | Standard operation — good balance |
| 2.0x | Double estimate | High-urgency orders (emergency close, liquidation avoidance) |
| 3.0x+ | Aggressive overpay | "I need this in the next block no matter what" |

### Dynamic Gas Strategy

```python
class GasStrategy:
    def __init__(self, base_multiplier: float = 1.5):
        self._base = base_multiplier
        self._urgency_multiplier = 1.0

    def set_urgency(self, urgency: str):
        match urgency:
            case "low":
                self._urgency_multiplier = 0.8
            case "normal":
                self._urgency_multiplier = 1.0
            case "high":
                self._urgency_multiplier = 1.5
            case "critical":
                self._urgency_multiplier = 2.5

    @property
    def effective_multiplier(self) -> float:
        return self._base * self._urgency_multiplier
```

### Bot-Specific Gas Considerations

| Scenario | Recommended Multiplier | Reasoning |
|---|---|---|
| Market making quote updates | 1.5x | Quotes are replaced frequently; a stuck one gets replaced by the next update |
| Directional entry (IOC) | 2.0x | Signal is time-sensitive; delay means slippage |
| Position close (risk event) | 3.0x | Capital preservation trumps gas cost |
| TWAP slice | 1.2x | Individual slices are small; TWAP naturally absorbs delay |
| Deposit/withdraw | 1.0x | No urgency, save gas |

### Gas Cost Budgeting for Market Makers

On Aptos, gas prices are typically 100–150 octas (1 APT = 10^8 octas). A market maker sending 10 bulk order updates per second across 5 markets:

```
Transactions per second: 10
Average gas per tx: ~20,000 gas units
Gas price: 150 octas/unit
Cost per second: 10 × 20,000 × 150 = 30,000,000 octas = 0.3 APT/s
Cost per hour: 1,080 APT/hr
Cost per day: ~25,920 APT/day
```

At $10/APT, that's ~$260K/day. In practice, market makers send far fewer than 10 tx/s (bulk orders bundle 30 levels into 1 tx), so actual costs are 10–100x lower. Use the gas station if available to eliminate this cost entirely.

### GasPriceManager Interface

| Feature | Specification |
|---|---|
| **Refresh interval** | Configurable (default: 5 seconds) |
| **Multiplier** | Configurable (default: 1.5x) |
| **Lazy start** | Only starts fetching when first gas price is requested |
| **Thread safety** | Safe for concurrent reads from multiple tasks |
| **Fallback** | If fetch fails, use last known good value |
| **Cleanup** | `destroy()` / `Drop` stops the background task |

```python
class GasPriceManager:
    def __init__(
        self,
        fullnode_url: str,
        refresh_interval_s: float = 5.0,
        multiplier: float = 1.5,
    ): ...

    async def get_gas_price(self) -> int:
        """Get the current gas price estimate with multiplier applied."""
        ...

    async def destroy(self) -> None:
        """Stop the background refresh task."""
        ...
```

```rust
pub struct GasPriceManager { /* ... */ }

impl GasPriceManager {
    pub fn new(fullnode_url: &str, refresh_interval: Duration, multiplier: f64) -> Self;
    pub async fn get_gas_price(&self) -> Result<u64, DecibelError>;
    pub async fn destroy(self);
}
```

---

## Smart Contract Entry Points

All Move function calls follow the pattern: `{package}::{module}::{function}`.

### Account Management

| Operation | Function | Module |
|---|---|---|
| Create subaccount | `create_new_subaccount` | `dex_accounts` |
| Deposit | `deposit_to_subaccount_at` | `dex_accounts` |
| Withdraw | `withdraw_from_subaccount` | `dex_accounts` |
| Configure settings | `configure_user_settings_for_market` | `dex_accounts` |

### Order Management

| Operation | Function | Module |
|---|---|---|
| Place order | `place_order_to_subaccount` | `dex_accounts_entry` |
| Cancel order | `cancel_order_to_subaccount` | `dex_accounts` |
| Cancel client order | `cancel_client_order_to_subaccount` | `dex_accounts` |
| Place TWAP | `place_twap_order_to_subaccount` | `dex_accounts` |
| Cancel TWAP | `cancel_twap_order_to_subaccount` | `dex_accounts` |
| Place bulk order | `place_bulk_order` | `dex_accounts` |
| Cancel bulk order | `cancel_bulk_order` | `dex_accounts` |

### Position Management

| Operation | Function | Module |
|---|---|---|
| Place TP/SL | `place_tp_sl_order_for_position` | `dex_accounts` |
| Update TP | `update_tp_order_for_position` | `dex_accounts` |
| Update SL | `update_sl_order_for_position` | `dex_accounts` |
| Cancel TP/SL | `cancel_tp_sl_order_for_position` | `dex_accounts` |

### Delegation

| Operation | Function | Module |
|---|---|---|
| Delegate trading | `delegate_trading_to_for_subaccount` | `dex_accounts` |
| Revoke delegation | `revoke_delegation` | `dex_accounts` |

### Builder Fees

| Operation | Function | Module |
|---|---|---|
| Approve fee | `approve_max_builder_fee` | `dex_accounts` |
| Revoke fee | `revoke_max_builder_fee` | `dex_accounts` |

### Vault Operations

| Operation | Function | Module |
|---|---|---|
| Create vault | `create_and_fund_vault` | `vaults` |
| Activate vault | `activate_vault` | `vaults` |
| Contribute | `contribute_to_vault` | `vaults` |
| Redeem | `redeem_from_vault` | `vaults` |
| Delegate actions | `delegate_dex_actions_to` | `vaults` |

---

## Bulk Order Transactions: Market Maker Specifics

The `place_bulk_order` entry function is the primary tool for market makers on Decibel. It atomically replaces all quotes on one side of a market with up to 30 new price levels. Understanding its mechanics is critical for building a performant quoting engine.

### How Bulk Orders Work

A bulk order is an **atomic replacement**: when the chain processes a `place_bulk_order` transaction, it:

1. Cancels ALL existing orders from the sending subaccount on the specified side (bid or ask) for the specified market.
2. Places up to 30 new orders at the specified prices and sizes.
3. Returns a `sequence_number` that uniquely identifies this bulk order set.

This atomic cancel-and-replace means the market maker never has a moment where old quotes are cancelled but new quotes haven't been placed — there's no "naked" period.

### Sequence Number Management

Each bulk order submission returns a `sequence_number`. This is NOT the Aptos transaction sequence number (Decibel uses orderless/replay-nonce transactions). Instead, it's a Decibel-specific counter that identifies the bulk order set.

```python
class BulkOrderTracker:
    def __init__(self):
        self._last_sequence: dict[str, dict[str, int]] = {}  # market -> side -> seq

    def record_submission(self, market: str, side: str, sequence_number: int):
        if market not in self._last_sequence:
            self._last_sequence[market] = {}
        self._last_sequence[market][side] = sequence_number

    def is_stale_update(self, market: str, side: str, sequence_number: int) -> bool:
        """Check if a WS bulk_orders update is for an older sequence than expected."""
        expected = self._last_sequence.get(market, {}).get(side, 0)
        return sequence_number < expected

    def last_sequence(self, market: str, side: str) -> int | None:
        return self._last_sequence.get(market, {}).get(side)
```

### Bulk Order Constraints

| Constraint | Value | Consequence of Violation |
|---|---|---|
| Max levels per side | 30 | Transaction rejected if > 30 levels provided |
| Min levels per side | 1 | Must provide at least 1 level |
| Price ordering | Must be valid tick-aligned prices | Each level rounded to tick_size independently |
| Size per level | Must meet lot_size and min_size | Each level validated independently |
| PostOnly enforcement | All levels are PostOnly | Any level that would cross the spread is rejected (not filled) |
| One side per transaction | Bid OR ask, not both | To update both sides, submit two parallel transactions |

### Updating Both Sides Simultaneously

Since each `place_bulk_order` call handles one side, updating both bid and ask quotes requires two transactions. Thanks to orderless nonces, these can be submitted in parallel:

```python
async def update_quotes(
    self,
    market: str,
    bid_levels: list[tuple[float, float]],
    ask_levels: list[tuple[float, float]],
):
    """Submit bid and ask bulk orders in parallel."""
    bid_task = self._client.place_bulk_order(
        market_name=market,
        is_buy=True,
        levels=bid_levels,
    )
    ask_task = self._client.place_bulk_order(
        market_name=market,
        is_buy=False,
        levels=ask_levels,
    )
    bid_result, ask_result = await asyncio.gather(
        bid_task, ask_task, return_exceptions=True
    )
    if isinstance(bid_result, Exception):
        logger.error(f"Bid bulk order failed: {bid_result}")
    else:
        self._tracker.record_submission(market, "bid", bid_result.sequence_number)
    if isinstance(ask_result, Exception):
        logger.error(f"Ask bulk order failed: {ask_result}")
    else:
        self._tracker.record_submission(market, "ask", ask_result.sequence_number)
```

### Partial Failure Handling

A bulk order transaction can have **partial rejection**: the transaction itself succeeds (included in a block), but individual levels within the bulk order are rejected. Common causes:

| Rejection Reason | Affected Levels | What Happened |
|---|---|---|
| PostOnly violation | Levels that crossed the spread | The price moved between build and execution; those levels would have been filled as taker |
| Invalid price | Specific levels with bad tick alignment | Should not happen if SDK formats correctly |
| Invalid size | Specific levels below min_size | Should not happen if SDK validates |

The WS `bulk_order_rejections:{accountAddr}` topic reports which levels were rejected. The remaining levels are active.

```python
async def on_bulk_order_rejection(self, rejection: BulkOrderRejectionsUpdate):
    for level in rejection.rejected_levels:
        logger.warning(
            f"Bulk order level rejected: seq={rejection.sequence_number} "
            f"price={level.price} size={level.size} reason={level.reason}"
        )
    total = rejection.total_levels
    rejected = len(rejection.rejected_levels)
    accepted = total - rejected
    if accepted == 0:
        logger.error(
            f"All {total} levels rejected for seq={rejection.sequence_number}. "
            f"Spread may have moved. Will re-quote on next tick."
        )
```

### Bulk Order vs Individual Orders: When to Use Each

| Scenario | Use Bulk Orders | Use Individual Orders |
|---|---|---|
| Market making (quoting both sides) | YES — atomic replacement prevents partial exposure | NO |
| Replacing a single resting order | NO — overkill, cancels all orders on that side | YES — cancel + place |
| Placing a single aggressive (IOC) order | NO — bulk orders are PostOnly | YES |
| Emergency cancel-all | YES — submit empty bulk order (0 levels cancels all on that side) | Alternative: individual cancel per order |
| Quoting 1–3 levels | Either works | YES — simpler, less gas |
| Quoting 10–30 levels | YES — one transaction instead of 10–30 | NO — too many transactions |

### Bulk Order Gas Costs

Bulk orders consume more gas than individual orders because they process multiple levels atomically:

| Levels | Approximate Gas | Notes |
|---|---|---|
| 1–5 levels | ~5,000–15,000 gas units | Comparable to 2–3 individual orders |
| 6–15 levels | ~15,000–40,000 gas units | More efficient than individual orders |
| 16–30 levels | ~40,000–80,000 gas units | Gas cost is sub-linear — 30 levels costs less than 30 individual orders |

Use the `max_gas_amount` parameter conservatively for bulk orders. The default of 100,000 is sufficient for any bulk order.

---

## Place Order Argument Formatting: Worked Examples

The `place_order_to_subaccount` function takes chain-unit integers, not human-readable floats. Here is the complete conversion process with real market parameters.

### BTC-USD Market Parameters

From `GET /markets` response for BTC-USD:

```json
{
  "market_name": "BTC-USD",
  "px_decimals": 9,
  "sz_decimals": 9,
  "tick_size": 100000,
  "lot_size": 1000,
  "min_size": 1000000
}
```

### Example: Buy 0.05 BTC at $68,250.50

**Step 1: Round price to tick_size**

```
human_price = 68250.50
denormalized = 68250.50 × 10^9 = 68_250_500_000_000
tick_size = 100_000
rounded = round(68_250_500_000_000 / 100_000) × 100_000 = 68_250_500_000_000
re-normalized = 68_250_500_000_000 / 10^9 = 68250.50  ← valid tick
chain_price = 68_250_500_000_000  (u64)
```

**Step 2: Round size to lot_size, enforce min_size**

```
human_size = 0.05
denormalized = 0.05 × 10^9 = 50_000_000
lot_size = 1000
rounded = round(50_000_000 / 1000) × 1000 = 50_000_000
min_size = 1_000_000
50_000_000 >= 1_000_000 ✓
chain_size = 50_000_000  (u64)
```

**Step 3: Build function arguments**

```python
args = [
    subaccount_addr,         # address: subaccount
    market_addr,             # address: market object address
    68_250_500_000_000,      # u64: price in chain units
    50_000_000,              # u64: size in chain units
    True,                    # bool: is_buy
    2,                       # u8: time_in_force (IOC = 2)
    False,                   # bool: is_reduce_only
    None,                    # Option<u128>: client_order_id
    None,                    # Option<u64>: trigger_price
    None,                    # Option<u64>: stop_limit_price
    None,                    # Option<u64>: take_profit_trigger_price
    None,                    # Option<u64>: stop_loss_trigger_price
    None,                    # Option<u64>: good_till_timestamp
    None,                    # Option<address>: builder_fee_recipient
    None,                    # Option<u64>: builder_fee_bps
]
```

### ETH-USD Market Parameters

```json
{
  "market_name": "ETH-USD",
  "px_decimals": 9,
  "sz_decimals": 9,
  "tick_size": 10000,
  "lot_size": 10000,
  "min_size": 10000000
}
```

### Example: Sell 1.5 ETH at $3,401.25

```
chain_price = round(3401.25 × 10^9 / 10_000) × 10_000 = 3_401_250_000_000
chain_size = round(1.5 × 10^9 / 10_000) × 10_000 = 1_500_000_000
min_size check: 1_500_000_000 >= 10_000_000 ✓

args = [subaccount_addr, market_addr, 3_401_250_000_000, 1_500_000_000, False, 0, False, ...]
```

### Edge Case: Price Between Ticks

If a bot computes a price of $68,250.33 for BTC-USD:

```
denormalized = 68_250_330_000_000
rounded = round(68_250_330_000_000 / 100_000) × 100_000 = 68_250_300_000_000
re-normalized = 68250.30  ← rounded DOWN to nearest tick

The SDK does this automatically when the agent passes price=68250.33 to place_order().
```

### Edge Case: Size Below Minimum

If a bot tries to place an order for 0.0005 BTC (chain units: 500_000):

```
500_000 < min_size (1_000_000)
SDK rounds UP to min_size: chain_size = 1_000_000
re-normalized = 0.001 BTC

If even min_size is too large for the strategy, the SDK raises ValidationError.
```

---

## Address Derivation Utilities

### Get Market Address

Derives the on-chain market object address from a market name:

```python
def get_market_addr(market_name: str, perp_engine_global: str) -> str:
    """Derive market address from market name.

    Uses Aptos create_object_address with BCS-serialized market name.
    """
    serializer = Serializer()
    serializer.str(market_name)
    seed = serializer.output()
    return create_object_address(perp_engine_global, seed)
```

### Get Primary Subaccount Address

Derives the primary subaccount address for an account:

```python
def get_primary_subaccount_addr(
    account_addr: str,
    compat_version: str,
    package_addr: str,
) -> str:
    """Derive the primary subaccount address."""
    ...
```

### Get Vault Share Address

```python
def get_vault_share_address(vault_address: str) -> str:
    """Derive the vault share token address."""
    ...
```

---

## Price and Size Formatting

The SDK MUST convert human-readable prices and sizes to chain units before passing them to the transaction builder. See [02-structured-data-models.md](./02-structured-data-models.md) for `PerpMarketConfig` field definitions.

### Conversion Functions

```python
def amount_to_chain_units(amount: float, decimals: int) -> int:
    """Convert a decimal amount to integer chain units.

    Example: amount_to_chain_units(5.67, 9) = 5670000000
    """
    return int(amount * (10 ** decimals))

def chain_units_to_amount(chain_units: int, decimals: int) -> float:
    """Convert integer chain units back to a decimal amount."""
    return chain_units / (10 ** decimals)

def round_to_valid_price(price: float, market: PerpMarketConfig) -> float:
    """Round a price to the nearest valid tick size for a market."""
    if price == 0:
        return 0.0
    denormalized = price * (10 ** market.px_decimals)
    rounded = round(denormalized / market.tick_size) * market.tick_size
    return round(rounded) / (10 ** market.px_decimals)

def round_to_valid_order_size(size: float, market: PerpMarketConfig) -> float:
    """Round an order size to the nearest valid lot size, enforcing min_size."""
    if size == 0:
        return 0.0
    normalized_min = market.min_size / (10 ** market.sz_decimals)
    if size < normalized_min:
        return normalized_min
    denormalized = size * (10 ** market.sz_decimals)
    rounded = round(denormalized / market.lot_size) * market.lot_size
    return round(rounded) / (10 ** market.sz_decimals)
```

### Agent Convenience

The `place_order` method accepts human-readable prices and sizes by default. The SDK:

1. Fetches market config (cached after first call).
2. Rounds price to valid tick size.
3. Rounds size to valid lot size (enforcing min_size).
4. Converts to chain units.
5. Builds and submits the transaction.

Agents that need raw control can pass `raw=True` to skip automatic formatting.
