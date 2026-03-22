# Error Handling for Trading Bots

**Parent**: [00-overview.md](./00-overview.md)

---

## Design Principles

1. **Every error classifies position safety** — can the bot still trust its local view of positions and orders?
2. **Every error is actionable** — the bot knows whether to retry, re-sync, cancel all, or halt.
3. **Every error serializes to JSON** — structured output for agent logging, telemetry, and LLM consumption.
4. **Critical errors escalate immediately** — cancel failures and stop-loss failures never wait for retry loops.

---

## Position Safety Classification

Every error the SDK produces carries a `position_safety` field. This is the single most important field for a trading bot — it answers: "Is my view of the world still correct?"

### Safety Levels

| Level | Meaning | Bot Action |
|---|---|---|
| `SAFE` | The bot's local state (positions, orders, balances) is still accurate. The failed operation had no side effects. | Retry or skip the operation. No state re-sync needed. |
| `UNKNOWN` | The operation may or may not have executed. The bot cannot know without checking. | **Must** query REST to reconcile state before taking further action. |
| `STALE` | The bot's local state is definitely out of date. Something happened (fill, cancel, liquidation) that the bot missed. | Halt new orders. Fetch all positions and open orders from REST. Rebuild local state. |
| `CRITICAL` | A protective order (stop-loss, TP/SL) may not be in place, or the bot cannot confirm its risk exposure. | **Emergency procedure**: cancel all orders, evaluate positions, potentially close everything. |

### Which Errors Produce Which Safety Level

| Error Scenario | Safety Level | Reasoning |
|---|---|---|
| Order placement fails with `ValidationError` | `SAFE` | Nothing was sent to chain. Local state unchanged. |
| Order placement fails with `SimulationError` | `SAFE` | Transaction never submitted. |
| Order placement gets `RateLimitError` | `SAFE` | Request never reached the matching engine. |
| Order placement times out (no tx hash) | `SAFE` | SDK didn't get a hash, so nothing was submitted. |
| Order submission succeeds but confirmation times out | `UNKNOWN` | Transaction is in mempool — it might execute or expire. |
| Cancel order fails with network error | `UNKNOWN` | The cancel may have reached the chain or not. The order might still be live, or might have filled while the cancel was in flight. |
| Cancel order returns `VmError` (order not found) | `UNKNOWN` | The order was already filled or cancelled. Bot's local state may be wrong about this order. |
| WebSocket disconnects for > 5 seconds | `STALE` | Fills, cancels, and liquidations could have happened during the gap. |
| REST position fetch returns different state than local | `STALE` | Local state diverged. Something was missed. |
| Stop-loss placement fails | `CRITICAL` | The position is unprotected. |
| TP/SL cancel fails (wanted to update, couldn't remove old) | `CRITICAL` | Stale protective orders may fire at wrong prices. |
| Cancel-all fails for any order in the batch | `CRITICAL` | Bot wanted to flatten but couldn't. Residual exposure exists. |

---

## Error Hierarchy

```
DecibelError
│
├── ConfigError                    position_safety: SAFE
│   Fields: message
│   Description: Invalid SDK configuration.
│
├── AuthenticationError            position_safety: SAFE
│   Fields: message
│   Description: Invalid or expired credentials.
│
├── NetworkError                   position_safety: varies
│   ├── TimeoutError               position_safety: SAFE (if pre-submit), UNKNOWN (if post-submit)
│   │   Fields: url, timeout_ms, phase (pre_submit | post_submit)
│   │
│   └── ConnectionError            position_safety: SAFE (if pre-submit), UNKNOWN (if post-submit)
│       Fields: url, reason, phase
│
├── ApiError                       position_safety: SAFE
│   Fields: status, status_text, message, url
│   │
│   ├── RateLimitError (429)       position_safety: SAFE
│   │   Fields: retry_after_ms
│   │
│   └── ServerError (5xx)          position_safety: SAFE (read), UNKNOWN (write)
│       Fields: retry_after_ms
│
├── ValidationError                position_safety: SAFE
│   Fields: field, constraint, value
│
├── TransactionError               position_safety: varies
│   │
│   ├── SimulationError            position_safety: SAFE
│   │   Fields: vm_status, message
│   │
│   ├── GasError                   position_safety: SAFE
│   │   Fields: estimated, available
│   │
│   ├── SubmissionError            position_safety: UNKNOWN
│   │   Fields: tx_hash (if available), message
│   │
│   └── VmError                    position_safety: UNKNOWN
│       Fields: transaction_hash, vm_status, abort_code
│
├── WebSocketError                 position_safety: STALE (if disconnected > 5s)
│   Fields: message, topic, disconnect_duration_ms
│
└── CriticalTradingError           position_safety: CRITICAL
    Fields: failed_operation, affected_market, affected_order_ids, message
    Description: A protective order operation failed.
```

---

## Structured Error Output

Every error serializes to JSON with a consistent schema. This is the format agents log, LLMs consume, and telemetry pipelines ingest.

### Schema

```json
{
  "error_type": "CancelFailure",
  "code": "VM_ERROR",
  "message": "Order 0xabc123 not found — may have filled",
  "position_safety": "UNKNOWN",
  "timestamp_ms": 1710000000000,
  "context": {
    "market": "BTC-USD",
    "order_id": "0xabc123",
    "client_order_id": "mm-btc-bid-001",
    "operation": "cancel_order",
    "tx_hash": "0xdef456"
  },
  "recovery": {
    "action": "reconcile_order_state",
    "steps": [
      "GET /orders?order_id=0xabc123 to check if filled or cancelled",
      "GET /account_positions to update position state",
      "If filled: update local inventory tracking",
      "If cancelled: safe to proceed"
    ]
  }
}
```

### Python Implementation

```python
import time
import json
from dataclasses import dataclass, field, asdict
from enum import StrEnum


class PositionSafety(StrEnum):
    SAFE = "SAFE"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    CRITICAL = "CRITICAL"


class DecibelError(Exception):
    code: str
    message: str
    position_safety: PositionSafety
    context: dict
    recovery: dict | None

    def __init__(
        self,
        code: str,
        message: str,
        position_safety: PositionSafety = PositionSafety.SAFE,
        context: dict | None = None,
        recovery: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.position_safety = position_safety
        self.context = context or {}
        self.recovery = recovery
        super().__init__(f"[{code}] {message}")

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "error_type": type(self).__name__,
            "code": self.code,
            "message": self.message,
            "position_safety": self.position_safety.value,
            "timestamp_ms": int(time.time() * 1000),
            "context": self.context,
            "recovery": self.recovery,
        }

    @property
    def requires_state_sync(self) -> bool:
        return self.position_safety in (PositionSafety.UNKNOWN, PositionSafety.STALE, PositionSafety.CRITICAL)

    @property
    def requires_emergency_action(self) -> bool:
        return self.position_safety == PositionSafety.CRITICAL
```

### Rust Implementation

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PositionSafety {
    Safe,
    Unknown,
    Stale,
    Critical,
}

impl DecibelError {
    pub fn position_safety(&self) -> PositionSafety { /* match on variant */ }
    pub fn requires_state_sync(&self) -> bool {
        matches!(self.position_safety(), PositionSafety::Unknown | PositionSafety::Stale | PositionSafety::Critical)
    }
    pub fn requires_emergency_action(&self) -> bool {
        self.position_safety() == PositionSafety::Critical
    }
    pub fn to_json(&self) -> serde_json::Value { /* structured serialization */ }
}
```

---

## Critical Errors: When the Bot's Safety Net Is Gone

These are the errors that must bypass all retry logic and trigger immediate escalation. A "critical" error means the bot's protective orders may not be in place — the position is potentially unprotected.

### Cancel Failure

The bot tried to cancel an order and the cancel failed. The order might still be live and could fill at any moment.

```python
class CancelFailure(CriticalTradingError):
    """A cancel request failed. The target order's state is unknown."""

    def __init__(self, order_id: str, market: str, reason: str, tx_hash: str | None = None):
        super().__init__(
            code="CANCEL_FAILURE",
            message=f"Failed to cancel order {order_id} on {market}: {reason}",
            position_safety=PositionSafety.UNKNOWN,
            context={
                "market": market,
                "order_id": order_id,
                "operation": "cancel_order",
                "tx_hash": tx_hash,
            },
            recovery={
                "action": "reconcile_then_retry",
                "steps": [
                    f"GET /orders?order_id={order_id} to determine current state",
                    "If still open: retry cancel with higher gas",
                    "If filled: update position tracking with the fill",
                    "If not found: order was already cancelled or expired",
                ],
            },
        )
```

**Why this is critical**: If the order was a resting limit that the bot wanted to pull (because the market moved), and the cancel fails, that order can fill at a now-unfavorable price. If it was a leg of a spread, the bot has one-sided exposure.

### Stop-Loss Placement Failure

The bot opened a position and immediately tried to place a stop-loss. The SL placement failed.

```python
class StopLossPlacementFailure(CriticalTradingError):
    """Stop-loss order failed to place. Position is unprotected."""

    def __init__(self, market: str, position_size: float, intended_sl_price: float, reason: str):
        super().__init__(
            code="SL_PLACEMENT_FAILURE",
            message=f"Stop-loss failed for {position_size} {market} at {intended_sl_price}: {reason}",
            position_safety=PositionSafety.CRITICAL,
            context={
                "market": market,
                "position_size": position_size,
                "intended_sl_price": intended_sl_price,
                "operation": "place_tp_sl",
            },
            recovery={
                "action": "emergency_protect_position",
                "steps": [
                    "Retry SL placement immediately with higher gas (3x multiplier)",
                    "If retry fails: place a reduce-only IOC order at market price to close",
                    "If IOC fails: escalate — human intervention required",
                ],
            },
        )
```

**Why this is critical**: An unprotected position can move against the bot without any circuit breaker. A gap move during an unprotected window can cause catastrophic loss.

### TP/SL Update Failure

The bot tried to move its stop-loss (e.g., trailing stop) and the update failed. The old SL is still in place, but at the wrong price.

```python
class TpSlUpdateFailure(CriticalTradingError):
    """TP/SL update failed. Old protective order is at stale price."""

    def __init__(self, market: str, old_price: float, intended_price: float, reason: str):
        super().__init__(
            code="TPSL_UPDATE_FAILURE",
            message=f"TP/SL update failed on {market}: wanted {intended_price}, stuck at {old_price}",
            position_safety=PositionSafety.CRITICAL,
            context={
                "market": market,
                "old_trigger_price": old_price,
                "intended_trigger_price": intended_price,
                "operation": "update_tp_sl",
            },
            recovery={
                "action": "verify_and_retry",
                "steps": [
                    "GET /open_orders to confirm which TP/SL is currently active",
                    "Retry the update with higher gas",
                    "If stuck: cancel old TP/SL and place new one (two transactions)",
                    "If cancel also fails: close position manually",
                ],
            },
        )
```

### Cancel-All Partial Failure

During emergency flatten, some cancels succeeded and some failed. The bot has partial residual exposure.

```python
class CancelAllPartialFailure(CriticalTradingError):
    """Some orders failed to cancel during a cancel-all operation."""

    def __init__(self, succeeded: list[str], failed: list[tuple[str, str]], market: str | None = None):
        super().__init__(
            code="CANCEL_ALL_PARTIAL",
            message=f"Cancel-all: {len(succeeded)} succeeded, {len(failed)} failed",
            position_safety=PositionSafety.CRITICAL,
            context={
                "market": market,
                "cancelled_order_ids": succeeded,
                "failed_cancels": [{"order_id": oid, "reason": r} for oid, r in failed],
                "operation": "cancel_all",
            },
            recovery={
                "action": "retry_failed_cancels",
                "steps": [
                    "Retry each failed cancel individually with maximum gas",
                    "For any that still fail: GET /orders to check if they filled",
                    "Update position tracking for any fills discovered",
                    "If orders are stuck open: place counter-orders to neutralize exposure",
                ],
            },
        )
```

---

## Trading-Specific Error Recovery

### Scenario 1: Order Placement Fails Mid-Strategy

The bot is executing a multi-leg strategy (e.g., buy BTC-USD + sell ETH-USD) and the first leg succeeds but the second fails.

```python
async def execute_spread_entry(client, long_params, short_params):
    long_result = None
    short_result = None

    try:
        long_result, short_result = await asyncio.gather(
            client.place_order(**long_params),
            client.place_order(**short_params),
            return_exceptions=True,
        )
    except Exception as e:
        pass

    long_ok = long_result and not isinstance(long_result, Exception) and long_result.success
    short_ok = short_result and not isinstance(short_result, Exception) and short_result.success

    if long_ok and short_ok:
        return {"status": "both_legs_filled", "long": long_result, "short": short_result}

    if long_ok and not short_ok:
        # One leg is on. Decide: unwind the long, or retry the short.
        error = short_result if isinstance(short_result, Exception) else None

        if error and isinstance(error, (RateLimitError, GasError)):
            # Transient — retry the short leg
            short_result = await client.place_order(**short_params)
            if short_result.success:
                return {"status": "both_legs_filled_after_retry"}

        # Short leg won't go through — unwind the long
        await client.place_order(
            market_name=long_params["market_name"],
            price=0,
            size=long_params["size"],
            is_buy=False,
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=True,
            client_order_id=f"unwind-{long_params.get('client_order_id', '')}",
        )
        return {"status": "unwound", "reason": str(error)}

    if not long_ok and short_ok:
        # Mirror of above — unwind the short
        await client.place_order(
            market_name=short_params["market_name"],
            price=0,
            size=short_params["size"],
            is_buy=True,
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=True,
        )
        return {"status": "unwound", "reason": str(long_result)}

    return {"status": "both_failed", "long_error": str(long_result), "short_error": str(short_result)}
```

**Key principle**: Never leave a partial spread on. If one leg fails, immediately unwind the other. Use `is_reduce_only=True` and IOC to guarantee the unwind doesn't increase exposure.

### Scenario 2: Cancel Fails for an Order That Might Have Filled

The bot sends a cancel, and the cancel transaction returns a VM error saying the order doesn't exist. This means either: (a) it was already cancelled, or (b) it filled while the cancel was in flight.

```python
async def safe_cancel_with_reconciliation(client, order_id: str, market: str, subaccount: str):
    try:
        result = await client.cancel_order(
            order_id=order_id,
            market_name=market,
        )
        return {"status": "cancelled", "result": result}

    except VmError as e:
        if "order not found" in e.vm_status.lower() or "ORDER_NOT_FOUND" in str(e.abort_code):
            # Order is gone. Was it filled or cancelled?
            order_status = await client.get_order_status(
                order_id=order_id,
                market_name=market,
                user_address=subaccount,
            )

            if order_status.status == "filled":
                return {
                    "status": "already_filled",
                    "fill_price": order_status.average_fill_price,
                    "fill_size": order_status.filled_size,
                    "position_safety": "STALE",  # local position state needs update
                }
            elif order_status.status == "cancelled":
                return {"status": "already_cancelled", "position_safety": "SAFE"}
            else:
                return {"status": "unknown", "position_safety": "UNKNOWN"}

        raise  # unexpected VM error — propagate

    except NetworkError:
        # Cancel might have reached chain or not.
        # Must check order state before proceeding.
        return {"status": "cancel_uncertain", "position_safety": "UNKNOWN"}
```

**Key principle**: After any failed cancel, always query the order's current state. Never assume the order is still live — it might have filled, and the bot needs to account for that fill in its position tracking.

### Scenario 3: WebSocket Disconnects Mid-Fill

The bot submitted an IOC order, then the WebSocket dropped before the `order_updates` callback fired. The bot doesn't know if the order filled.

```python
async def handle_ws_disconnect_during_pending_order(
    client, pending_orders: list[dict], subaccount: str
):
    """Called when WS reconnects after a disconnect with orders in flight."""

    # Step 1: Get authoritative position state from REST
    current_positions = await client.get_positions(account=subaccount)
    current_orders = await client.get_open_orders(account=subaccount)

    # Step 2: Reconcile each pending order
    reconciled = []
    for pending in pending_orders:
        order_id = pending.get("order_id")
        tx_hash = pending.get("tx_hash")

        if order_id:
            order_status = await client.get_order_status(
                order_id=order_id,
                market_name=pending["market"],
                user_address=subaccount,
            )
            reconciled.append({
                "order_id": order_id,
                "expected_side": pending["side"],
                "actual_status": order_status.status,
                "filled_size": order_status.filled_size,
                "fill_price": order_status.average_fill_price,
            })
        elif tx_hash:
            # Order ID not yet known — check tx outcome
            try:
                tx_result = await client.get_transaction(tx_hash)
                if tx_result.success:
                    events = extract_order_events(tx_result)
                    reconciled.append({
                        "tx_hash": tx_hash,
                        "events": events,
                        "status": "confirmed",
                    })
                else:
                    reconciled.append({"tx_hash": tx_hash, "status": "failed_on_chain"})
            except NotFoundError:
                reconciled.append({"tx_hash": tx_hash, "status": "not_found_expired"})

    # Step 3: Rebuild local state from REST truth
    return {
        "positions": current_positions,
        "open_orders": current_orders,
        "reconciled_pending": reconciled,
        "action": "replace_local_state",
    }
```

**Key principle**: After any WS disconnect, treat all pending orders as `UNKNOWN`. Use REST to rebuild ground truth. Never resume trading until local state matches REST state.

---

## Emergency Procedures

### Procedure 1: Cancel All Orders

**When to trigger**:
- Margin ratio drops below the bot's risk threshold (e.g., < 15% available margin)
- WebSocket disconnect lasts > 30 seconds
- Multiple consecutive order failures (> 3 failures in 10 seconds)
- Any `CRITICAL` position safety error
- Price moves more than the bot's max tolerable gap since last confirmed state

```python
async def emergency_cancel_all(client, subaccount: str) -> dict:
    """Cancel every open order across all markets. Returns reconciliation report."""
    open_orders = await client.get_open_orders(account=subaccount)

    if not open_orders:
        return {"status": "no_orders", "cancelled": 0}

    results = await asyncio.gather(
        *[
            client.cancel_order(
                order_id=order.order_id,
                market_name=order.market,
            )
            for order in open_orders
        ],
        return_exceptions=True,
    )

    succeeded = []
    failed = []
    for order, result in zip(open_orders, results):
        if isinstance(result, Exception):
            failed.append((order.order_id, str(result)))
        else:
            succeeded.append(order.order_id)

    if failed:
        raise CancelAllPartialFailure(succeeded=succeeded, failed=failed)

    return {"status": "all_cancelled", "cancelled": len(succeeded)}
```

### Procedure 2: Close All Positions

**When to trigger**:
- Bot's maximum drawdown threshold is breached
- System detects a flash crash (> 5% move in < 1 minute)
- Unrecoverable state inconsistency after multiple reconciliation failures
- External kill switch triggered

```python
async def emergency_close_all_positions(client, subaccount: str) -> dict:
    """Close every open position with aggressive IOC orders."""

    # Step 1: Cancel all orders first to free margin and prevent new fills
    await emergency_cancel_all(client, subaccount)

    # Step 2: Get fresh position state
    positions = await client.get_positions(account=subaccount)
    open_positions = [p for p in positions if p.size != 0]

    if not open_positions:
        return {"status": "no_positions", "closed": 0}

    # Step 3: Close each position with IOC at aggressive price
    close_tasks = []
    for pos in open_positions:
        prices = await client.get_price(pos.market)
        mark = prices[0].mark_px

        # Use 1% slippage tolerance for emergency close
        if pos.size > 0:
            # Long position — sell to close at 1% below mark
            close_price = mark * 0.99
        else:
            # Short position — buy to close at 1% above mark
            close_price = mark * 1.01

        close_tasks.append(
            client.place_order(
                market_name=pos.market,
                price=close_price,
                size=abs(pos.size),
                is_buy=(pos.size < 0),
                time_in_force=TimeInForce.ImmediateOrCancel,
                is_reduce_only=True,
                client_order_id=f"emergency-close-{pos.market}-{int(time.time())}",
            )
        )

    results = await asyncio.gather(*close_tasks, return_exceptions=True)

    closed = []
    failed = []
    for pos, result in zip(open_positions, results):
        if isinstance(result, Exception):
            failed.append({"market": pos.market, "size": pos.size, "error": str(result)})
        else:
            closed.append({"market": pos.market, "size": pos.size, "tx_hash": result.transaction_hash})

    return {"status": "closed", "closed": closed, "failed": failed}
```

### Procedure 3: Halt Trading

**When to trigger**:
- Emergency close fails (positions couldn't be closed)
- Authentication error (credentials revoked or expired)
- Repeated `CRITICAL` errors (> 2 in 1 minute)
- Gas balance critically low (can't afford protective orders)

```python
class TradingHalt(Exception):
    """Raised to signal the bot's main loop must stop."""

    def __init__(self, reason: str, state_snapshot: dict):
        self.reason = reason
        self.state_snapshot = state_snapshot
        super().__init__(f"TRADING HALTED: {reason}")


async def halt_trading(client, subaccount: str, reason: str):
    """Attempt final cleanup then halt."""

    # Best-effort: cancel all and close all
    try:
        cancel_report = await emergency_cancel_all(client, subaccount)
    except CancelAllPartialFailure as e:
        cancel_report = e.to_dict()

    try:
        close_report = await emergency_close_all_positions(client, subaccount)
    except Exception as e:
        close_report = {"error": str(e)}

    # Capture final state for post-mortem
    final_state = {}
    try:
        final_state = {
            "positions": [p.__dict__ for p in await client.get_positions(account=subaccount)],
            "open_orders": [o.__dict__ for o in await client.get_open_orders(account=subaccount)],
            "overview": (await client.get_account_overview(account=subaccount)).__dict__,
        }
    except Exception:
        final_state = {"error": "Could not fetch final state"}

    raise TradingHalt(
        reason=reason,
        state_snapshot={
            "cancel_report": cancel_report,
            "close_report": close_report,
            "final_state": final_state,
            "timestamp_ms": int(time.time() * 1000),
        },
    )
```

---

## Emergency Decision Tree

```
Error occurs
│
├── position_safety == SAFE
│   └── Log and continue. Retry if the operation was important.
│
├── position_safety == UNKNOWN
│   ├── Was it a cancel failure?
│   │   ├── YES → Query order state via REST
│   │   │   ├── Order filled → Update position tracking, log unexpected fill
│   │   │   ├── Order cancelled → Safe, continue
│   │   │   └── Order still open → Retry cancel with higher gas
│   │   └── NO (submission timeout) → Check tx hash if available
│   │       ├── Tx confirmed → Extract events, update state
│   │       ├── Tx not found → Assume expired, safe to retry
│   │       └── Tx pending → Wait up to 10s, then treat as expired
│   └── After reconciliation: if state matches expectations → resume
│       Otherwise → escalate to STALE
│
├── position_safety == STALE
│   ├── Pause new order submissions
│   ├── Fetch all state from REST:
│   │   ├── GET /account_positions
│   │   ├── GET /open_orders
│   │   └── GET /account_overviews
│   ├── Replace local state with REST truth
│   ├── Verify risk limits still satisfied
│   │   ├── YES → Resume trading
│   │   └── NO → Escalate to CRITICAL
│   └── Log the stale event with duration estimate
│
└── position_safety == CRITICAL
    ├── Immediately: emergency_cancel_all()
    ├── Evaluate: are positions within risk tolerance?
    │   ├── YES → Place fresh protective orders (SL at safe levels)
    │   │   ├── SL placement succeeds → Resume with heightened monitoring
    │   │   └── SL placement fails → emergency_close_all_positions()
    │   └── NO → emergency_close_all_positions()
    │       ├── Close succeeds → halt_trading() with reason
    │       └── Close fails → halt_trading() — REQUIRES HUMAN INTERVENTION
    └── Always: emit CRITICAL alert to external monitoring
```

---

## Error-to-Action Mapping for Common Bot Operations

### Placing an Order

| Error | Position Safety | Action |
|---|---|---|
| `ValidationError` (invalid price/size) | `SAFE` | Fix parameters (round to tick/lot), retry |
| `SimulationError` (insufficient margin) | `SAFE` | Reduce size or close other positions first |
| `GasError` (insufficient gas) | `SAFE` | Top up gas balance, retry with higher gas price |
| `RateLimitError` | `SAFE` | Wait `retry_after_ms`, retry |
| `NetworkError` (pre-submit) | `SAFE` | Retry immediately |
| `SubmissionError` (tx hash obtained but confirmation failed) | `UNKNOWN` | Poll tx hash via REST; treat result accordingly |
| `VmError` (abort_code) | `UNKNOWN` | Check abort code table; common: insufficient balance, market paused |

### Cancelling an Order

| Error | Position Safety | Action |
|---|---|---|
| `VmError` (order not found) | `UNKNOWN` | Order filled or already cancelled — query order status |
| `NetworkError` | `UNKNOWN` | Cancel might have landed — query order status |
| `RateLimitError` | `SAFE` | Wait and retry — order is still resting |
| `GasError` | `SAFE` | Retry with higher gas — urgent if the order is protective |

### Placing Stop-Loss / Take-Profit

| Error | Position Safety | Action |
|---|---|---|
| Any error | `CRITICAL` | Retry immediately with maximum gas. If retry fails, close the position. |

### WebSocket Reconnection

| Condition | Position Safety | Action |
|---|---|---|
| Disconnect < 2s | `SAFE` | Likely no missed events. Resume after re-subscribe. |
| Disconnect 2–30s | `STALE` | Fetch REST snapshots for positions and open orders. |
| Disconnect > 30s | `STALE` | Full state re-sync. Cancel all resting orders. Rebuild from REST. |

---

## Observability: Structured Event Log

All SDK operations emit structured events. The format is consistent so bots can pipe these directly into monitoring systems.

### Event Types

| Event Type | Emitted When | Key Fields |
|---|---|---|
| `order_submitted` | Order transaction sent | `market`, `side`, `size`, `price`, `client_order_id`, `tx_hash` |
| `order_confirmed` | Transaction confirmed | `order_id`, `tx_hash`, `vm_status`, `gas_used`, `fill_events` |
| `order_failed` | Transaction failed or VM error | `error_code`, `position_safety`, `recovery_action` |
| `cancel_submitted` | Cancel transaction sent | `order_id`, `market`, `tx_hash` |
| `cancel_confirmed` | Cancel confirmed | `order_id`, `tx_hash` |
| `cancel_failed` | Cancel failed | `order_id`, `error_code`, `position_safety` |
| `ws_disconnected` | WebSocket connection lost | `duration_estimate_ms`, `active_subscriptions` |
| `ws_reconnected` | WebSocket re-established | `gap_duration_ms`, `state_freshness` |
| `state_sync` | REST state fetched for reconciliation | `trigger`, `positions_changed`, `orders_changed` |
| `emergency_cancel_all` | Emergency cancel triggered | `reason`, `order_count`, `succeeded`, `failed` |
| `emergency_close_all` | Emergency close triggered | `reason`, `position_count`, `closed`, `failed` |
| `trading_halted` | Bot stopped trading | `reason`, `final_state_snapshot` |

### Event Hook

```python
client = DecibelClient(
    config=MAINNET_CONFIG,
    bearer_token="...",
    private_key="0x...",
    on_event=my_event_handler,
)

async def my_event_handler(event: dict) -> None:
    safety = event.get("position_safety")
    if safety == "CRITICAL":
        await send_pagerduty_alert(event)
    elif safety in ("UNKNOWN", "STALE"):
        await send_slack_warning(event)

    # Always log for telemetry
    structured_logger.info(json.dumps(event))
```
