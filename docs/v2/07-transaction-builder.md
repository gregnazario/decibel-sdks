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

    # Construct entry function payload from ABI
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
    account_override=session_key,  # signs with session key instead of primary
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
    skip_simulate=True,  # skip simulation for faster submission
)
```

---

## Gas Price Management

The `GasPriceManager` runs in the background, periodically fetching and caching gas price estimates.

### Behavior

| Feature | Specification |
|---|---|
| **Refresh interval** | Configurable (default: 5 seconds) |
| **Multiplier** | Configurable (default: 1.5x) |
| **Lazy start** | Only starts fetching when first gas price is requested |
| **Thread safety** | Safe for concurrent reads from multiple tasks |
| **Fallback** | If fetch fails, use last known good value |
| **Cleanup** | `destroy()` / `Drop` stops the background task |

### Interface

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

## ABI Caching

The SDK caches ABI definitions for all known entry functions. ABIs are loaded once (from bundled data or a single network fetch) and used for all subsequent transaction builds.

### Bundled ABIs

The SDK SHOULD bundle ABI definitions for all standard Decibel entry functions. This eliminates the need for any network call during transaction construction, even on the first build.

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
