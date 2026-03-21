# Design Principles: What Bots and Agents Actually Need

**Parent**: [00-overview.md](./00-overview.md)

---

This document is not a list of software engineering virtues. It is a specification of the concrete problems trading bots and agentic systems encounter on Decibel, and the design decisions the SDK makes to address them.

---

## 1. The Bot Knows Its Position at All Times

The single most critical thing a trading bot needs is accurate, real-time knowledge of its own state: what positions it holds, what orders are resting, how much margin is available, how close it is to liquidation.

### The Problem

REST polling introduces latency. Between polls, the bot's state is stale. A fill can happen, funding accrues, a stop triggers, a liquidation starts — and the bot doesn't know.

### The SDK Solution

The SDK maintains a **local position state manager** synced in real-time via WebSocket:

- `account_positions:{addr}` stream keeps positions current
- `account_overview:{addr}` stream keeps margin/equity current
- `order_updates:{addr}` stream delivers fill and cancel events
- `user_trades:{addr}` stream delivers execution details

The local state manager provides derived fields that are not in the raw API:

| Computed Field | Formula | Why It Matters |
|---|---|---|
| `unrealized_pnl_usd` | `(mark_price - entry_price) × size` | Real-time P&L tracking |
| `margin_usage_pct` | `total_margin / perp_equity_balance` | How leveraged you are |
| `liquidation_distance_pct` | `(mark_price - liq_price) / mark_price` | How close to liquidation |
| `funding_accrual_rate` | `funding_rate_bps × position_notional / 10000` | Cost per second of holding |
| `net_exposure_usd` | `Σ(size × mark_price)` across all markets | Directional risk |
| `total_notional_usd` | `Σ(|size| × mark_price)` across all markets | Gross exposure |

The bot reads local state synchronously. The WebSocket updates it asynchronously. The bot never has to choose between "fast" and "accurate."

### What This Means for the SDK

- The SDK MUST maintain a `PositionStateManager` that aggregates WebSocket streams into a coherent local view.
- The state manager MUST re-sync from REST on WebSocket reconnection.
- The state manager MUST expose computed risk metrics (not just raw fields).
- The state manager MUST be thread-safe (Rust: `Send + Sync`, Python: accessible from any async task).

---

## 2. Every Order Has a Lifecycle the Bot Can Track

A bot places an order and needs to know: was it accepted? Is it resting? Has it been partially filled? Was it rejected? Did the transaction fail? This must work without polling.

### The Problem

On-chain order placement is a multi-step process:
1. Build transaction
2. Sign transaction
3. Submit transaction
4. Wait for transaction to be included in a block
5. Parse events from the transaction to extract order ID
6. Monitor order status via WebSocket or REST

Between steps 3 and 6, the bot is blind. If the WebSocket disconnects, order status is lost.

### The SDK Solution

The SDK provides **end-to-end order lifecycle tracking**:

1. `place_order()` returns a `PlaceOrderResult` with `order_id` and `transaction_hash`.
2. The `client_order_id` parameter allows the bot to correlate orders across restarts.
3. The `order_updates:{addr}` WebSocket stream delivers real-time status changes.
4. The `get_order_status()` REST call provides point-in-time verification.
5. On reconnect, the SDK re-fetches open orders to restore the local view.

### What This Means for the SDK

- `place_order()` MUST extract the order ID from transaction events before returning.
- `client_order_id` MUST be a first-class parameter, not an afterthought.
- The SDK MUST provide a way to list all orders placed in the current session.
- The SDK MUST warn (not error) if a `client_order_id` has been seen before in the same session.

---

## 3. Bulk Orders Are Not a Convenience — They're the Core Market Making Primitive

Market makers don't place individual orders. They quote entire bid/ask ladders and replace them atomically when the market moves. Decibel's bulk order API is the most important feature for market makers.

### How Bulk Orders Work on Decibel

- One bulk order set per market per subaccount.
- Each `place_bulk_orders` call atomically replaces all previous bulk orders in that market.
- No cancel step needed — the replace is atomic.
- Post-only execution: all bulk orders are maker orders.
- Sequence numbers must be monotonically increasing (stale updates are rejected).
- Maximum 30 levels per side per call.
- Partial failures don't revert — a price level that crosses is skipped, the rest are placed.
- Bulk orders and regular orders are tracked separately.

### The SDK Solution

The SDK provides a **BulkOrderManager** per market:

- Tracks the current sequence number locally (monotonically incrementing).
- Provides `quote(bids, asks)` that atomically replaces the entire quote set.
- Tracks fills via `bulk_order_fills:{addr}` WebSocket stream.
- Provides `cancel_all()` (submit empty arrays) to clear all bulk orders.
- Exposes fill history for P&L tracking.

### What This Means for the SDK

- The `BulkOrderManager` MUST manage sequence numbers automatically — the bot never has to think about this.
- The SDK MUST reject or warn if bulk order arrays exceed 30 levels per side.
- The SDK MUST handle partial placement failures (log which levels were skipped).
- Fill tracking MUST associate fills with the specific bulk order that generated them.

---

## 4. Funding Is a Cost That Accrues Every Second

Unlike exchanges with 8-hour funding periods, Decibel uses continuous funding that accrues every oracle update (~1 second). A bot holding a position for 5 minutes pays or receives funding proportional to those 5 minutes. This has major implications.

### Why This Matters for Bots

- **Position sizing**: The cost of holding a position includes continuous funding, not a periodic settlement.
- **Strategy evaluation**: Backtests must account for per-second funding, not per-period.
- **Liquidation risk**: Funding accrues into unrealized PnL and affects the liquidation threshold even if price doesn't move.
- **Arbitrage**: Continuous funding eliminates the manipulation windows that exist on periodic-funding exchanges.

### The SDK Solution

- `UserPosition` includes `unrealized_funding` as a real-time field.
- `AccountOverview` includes `unrealized_funding_cost` in the equity calculation.
- The position state manager computes `funding_accrual_rate` (funding cost per second at current rate).
- Market price streams include `funding_rate_bps` and `is_funding_positive`.

### What This Means for the SDK

- The SDK MUST NOT hide or round funding values — they're financially material.
- The SDK MUST provide helpers to estimate funding cost over a time horizon.
- The SDK SHOULD expose the cumulative funding index if available from the API.

---

## 5. Margin, Leverage, and Liquidation Are Not Abstractions — They're Constraints

A bot operates within margin constraints. Every order it considers must be checked against available margin. Every position change affects the margin ratio. Getting too close to liquidation means forced closure.

### Key Formulas the SDK Must Expose

```
Account Equity = Total Collateral + Unrealized PnL
Unrealized PnL = Mark-to-Market PnL + Unrealized Funding Cost
Mark-to-Market PnL = (Mark Price - Entry Price) × Position Size

IM Requirement = Σ(Position Notional × IM Fraction)
MM Requirement = Σ(Position Notional × MM Fraction)
IM Fraction = 1 / User-Selected Leverage
MM Fraction = 1 / (Max Market Leverage × 2)

Tradeable Balance = Account Equity - max(IM Requirement, PnL Haircut Requirement)
Withdrawable Balance = Collateral Value - IM Requirement - Unrealized Loss
```

### The SDK Solution

The `AccountOverview` and computed state provide:

- `margin_ratio`: current `Account Equity / MM Requirement` — below 1.0 means liquidation.
- `available_margin`: how much notional the bot can add before hitting IM limit.
- `liquidation_buffer`: dollars or percent between current equity and MM requirement.
- Per-market IM/MM based on market config and position size.

### What This Means for the SDK

- The SDK MUST compute margin ratios locally, not just relay the API value.
- The SDK MUST provide `can_place_order(market, size, leverage)` as a pre-check.
- The SDK MUST provide liquidation warning thresholds (configurable, e.g., 150%, 120%, 105% of MM).
- The SDK MUST NOT allow the bot to accidentally exceed its margin without explicit override.

---

## 6. Fees Are Part of the Strategy, Not an Afterthought

Maker/taker fees, builder fees, and gas costs determine whether a strategy is profitable. The SDK must make fees visible and predictable.

### Fee Structure

| Tier | 30D Volume | Taker | Maker |
|---|---|---|---|
| 0 | < $10M | 3.40 bps | 1.10 bps |
| 1 | > $10M | 3.00 bps | 0.90 bps |
| 2 | > $50M | 2.50 bps | 0.60 bps |
| 3 | > $200M | 2.20 bps | 0.30 bps |
| 4 | > $1B | 2.10 bps | 0.00 bps |
| 5 | > $4B | 1.90 bps | 0.00 bps |
| 6 | > $15B | 1.80 bps | 0.00 bps |

Additionally:
- **Builder fees**: Optional, set per-order in basis points, paid to the builder address.
- **Gas costs**: APT for on-chain transaction execution (~0.001-0.01 APT per tx).
- **Funding**: Continuous cost/income based on position direction and funding rate.

### The SDK Solution

- Fee schedule is accessible via `client.fee_schedule` or similar.
- `estimate_order_cost(market, size, price, side, time_in_force)` returns estimated total cost including fees.
- Order results include actual fee paid.
- Trade history includes `fee_amount` and `is_rebate` per trade.
- Gas costs are tracked per transaction.

### What This Means for the SDK

- The SDK MUST expose the fee schedule as a typed data structure.
- The SDK MUST provide fee estimation before order placement.
- The SDK SHOULD track cumulative fees paid in a session for P&L reporting.

---

## 7. The SDK Builds Transactions as Fast as Possible

On-chain execution adds latency that doesn't exist on centralized exchanges. Every millisecond of SDK overhead is additive to the inherent blockchain latency. The SDK must minimize its contribution.

### Latency Budget for a Trading Decision

```
Signal detected (0ms)
  → Compute decision (varies, bot-dependent)
  → SDK: build transaction (MUST be <1ms Rust, <5ms Python)
  → SDK: sign transaction (MUST be <500μs Rust, <2ms Python)
  → Network: submit to fullnode (~50-200ms)
  → Chain: transaction included in block (~500ms-2s)
  → SDK: parse confirmation events (~100μs Rust, <1ms Python)
Total SDK overhead: <2ms Rust, <8ms Python (excluding network)
```

### What This Means for the SDK

- Transaction building MUST be synchronous with pre-cached ABI, chain ID, and gas price.
- ABI definitions MUST be bundled (not fetched at runtime).
- Replay protection nonces MUST be generated locally (random, not sequence-number-based).
- Market name → address resolution MUST be cached.
- Gas prices MUST be refreshed in the background, never blocking a build.
- Signing MUST use the Ed25519 key already in memory (no key loading per tx).

---

## 8. Reconnection Must Not Lose State

WebSocket disconnections are not exceptional — they happen every hour (server session timeout) and on network hiccups. The bot must survive reconnection without losing track of positions, orders, or fills.

### The SDK Solution

On WebSocket reconnection:
1. Re-authenticate with the same bearer token.
2. Re-subscribe to all active topics.
3. Fetch current state from REST to fill the gap:
   - `GET /account_positions` to refresh position state
   - `GET /open_orders` to refresh order state
   - `GET /account_overviews` to refresh equity/margin
4. Emit a `reconnected` event so the bot can perform its own re-sync logic.
5. Resume WebSocket streaming.

### What This Means for the SDK

- The SDK MUST track all active subscriptions and restore them on reconnect.
- The SDK MUST perform REST re-sync after reconnect before resuming callbacks.
- The SDK MUST emit lifecycle events (connected, disconnected, reconnecting, reconnected).
- The SDK MUST NOT deliver stale WebSocket data that arrived before the REST re-sync.

---

## 9. Errors Must Indicate What to Do, Not Just What Happened

A bot encountering an error needs to decide: retry? abort? wait? escalate? The error must carry enough information for automated decision-making.

### Error Decision Tree

```
Error occurred
  ├─ Is it retryable?
  │   ├─ YES: How long to wait? (retry_after_ms)
  │   │   ├─ Network/timeout: exponential backoff
  │   │   ├─ Rate limit: server-specified delay
  │   │   ├─ Gas error: retry with higher gas
  │   │   └─ 5xx server error: brief delay
  │   └─ NO: What happened?
  │       ├─ Validation error: fix input (field + constraint provided)
  │       ├─ VM error: transaction is invalid (abort_code provided)
  │       ├─ Auth error: credentials are wrong (stop all operations)
  │       └─ Config error: SDK misconfigured (stop all operations)
  └─ Does it affect position safety?
      ├─ YES (e.g., cancel failed, stop-loss failed):
      │   → SDK flags as CRITICAL, bot should take emergency action
      └─ NO (e.g., read failed, non-critical write):
          → Normal retry/abort logic
```

### What This Means for the SDK

- Every error MUST have `retryable: bool` and `retry_after_ms: Option<u64>`.
- Errors that affect position safety MUST be flagged as `critical: bool`.
- Cancel/stop-loss/liquidation-avoidance failures MUST be distinguishable from ordinary errors.
- The SDK MUST provide `is_retryable()`, `retry_after_ms()`, and `is_critical()` methods.

---

## 10. Structured Data with Computed Fields, Not Raw JSON

Raw API responses are not what a bot needs. A bot needs computed risk metrics, derived state, and validated types. The SDK transforms raw data into actionable intelligence.

### What This Means for the SDK

- All models are strongly typed — never raw dictionaries or `serde_json::Value`.
- Models include computed fields where the computation is non-trivial.
- Python: Pydantic v2 models with `model_computed_fields` or `@computed_field`.
- Rust: Methods on model types that compute derived values.
- JSON Schema export for LLM agent tool integration.

---

## 11. Multi-Subaccount Is Not Optional

Serious bots use multiple subaccounts to isolate strategies, manage risk independently, and avoid cross-contamination of P&L.

### The SDK Solution

- All read/write operations take `subaccount_addr` as a parameter.
- The position state manager supports multiple subaccounts simultaneously.
- WebSocket subscriptions can be per-subaccount.
- The SDK resolves the primary subaccount address from the owner address automatically.
- The SDK supports delegation: a single API wallet signing for multiple subaccounts.

---

## 12. Go and Rust for Performance, Python for Intelligence

The language choice is not about preference — it's about what each layer of a trading system needs:

| Layer | Language | Why |
|---|---|---|
| Signal generation, ML inference, strategy logic | Python | NumPy/PyTorch/pandas ecosystem, fast iteration |
| Execution engine, market making loop, orderbook management | Rust | Zero-cost abstractions, deterministic latency, no GC pauses |
| API gateway, aggregation services, monitoring | Go (future) | High concurrency, fast compilation, simple deployment |

The SDK MUST be idiomatic in each language — not a mechanical translation. A Rust market maker looks different from a Python ML agent, and the SDK should reflect that.
