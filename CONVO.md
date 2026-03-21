# Conversation Log

## 2026-03-21

### Task 1: Build V2 SDK Specification Docs (Initial)

Created 11 specification documents under `docs/v2/` for agent-first SDK design targeting Python and Rust. Used docs.decibel.trade as reference.

### Task 2: Deep Rewrite for Trading Bot and Agentic Trading

**Request**: Think deeply about what trading bots and agentic trading actually need. Improve or not improve things based on real requirements. Plan Go and Rust SDKs for performance.

**Analysis performed**:
- Fetched detailed API docs: order placement params, bulk order mechanics (atomic replace, sequence numbers, 30-level limit, PostOnly only), TWAP, fee schedule (tiered maker/taker, builder fees), funding (continuous ~1s accrual, CFI-based), margin (cross/isolated, IM/MM formulas, tradeable/withdrawable balance), liquidation (two-stage: market disposition + backstop vault)
- Identified gaps in v1 spec: no position state management, no bulk order manager, no computed risk fields, no fee awareness, no reconnection protocol, no position safety classification on errors

**What was improved (worth the complexity)**:
- Position state management (bots need real-time local state, not REST polling)
- Bulk order management (market makers need atomic quote replacement, not individual order placement)
- Computed risk fields (margin_usage_pct, liquidation_distance_pct, funding_accrual_rate)
- Position safety classification on errors (SAFE/UNKNOWN/STALE/CRITICAL)
- Fee schedule exposure and fee estimation
- Reconnection with REST re-sync protocol
- End-to-end latency budgets with realistic numbers
- Gas cost analysis for production bot budgeting

**What was not improved (not worth the complexity)**:
- Orderbook delta application — Decibel sends full snapshots, not deltas, so there's no need for complex delta management. Simple replacement is correct.
- Complex caching strategies — most data bots need should come via WebSocket, not cached REST. Only market config and USDC decimals deserve caching.
- Multi-connection WebSocket — server enforces single connection per client. No reason to fight this.
- Synchronous Python wrapper — async is the right model for I/O-heavy bot code. Sync wrappers hide bugs.

**Languages**:
- Python: AI/ML agents, strategy prototyping, medium-frequency trading
- Rust: HFT, market making, co-located infrastructure
- Go (future): API gateways, orchestrators, monitoring services

### Task 3: Create TDD/BDD Test Files for Python SDK

**Request**: Write 7 test files defining the API contract for all major model types before implementation.

**Approach**: Read all existing model source files (market.py, account.py, order.py, enums.py, common.py, config.py) to understand current fields and structure. Wrote TDD tests that:
- Test existing serialization roundtrips (dict and JSON)
- Define computed properties not yet implemented (funding_rate_hourly, unrealized_pnl, margin_usage_pct, etc.)
- Use realistic BTC ~$95k / ETH ~$3.5k trading data
- Cover edge cases (empty orderbook, zero equity, zero-size position)
- Pin enum wire values to prevent silent API breakage

**Files created**: conftest.py, test_market.py, test_account.py, test_order.py, test_enums.py, test_trade.py, test_pagination.py

### Task 4: Create BDD Feature Files (Gherkin)

**Request**: Write 7 BDD feature files in Gherkin format describing high-level trading bot behaviors.

**Approach**: Read all existing SDK source — models (order.py, account.py, market.py, enums.py, common.py), errors.py, client (websocket.py, read.py, write.py), existing TDD tests (test_position_manager.py, test_order_tracker.py, test_errors.py), and config.py — to ground scenarios in actual SDK APIs and field names.

**Files created** (under `tests/bdd/features/`):
1. `position_state.feature` — 9 scenarios covering WS bootstrap, live updates, sync reads, flat positions, multi-subaccount, net/gross exposure, mark price, depth
2. `order_lifecycle.feature` — 7 scenarios covering placement, WS updates, partial/full fill, cancel, client_order_id lookup
3. `bulk_orders.feature` — 8 scenarios covering two-sided quotes, atomic replace, sequence numbers, fill tracking, cancel_all, max levels, one-sided
4. `risk_monitoring.feature` — 8 scenarios covering liquidation distance, margin warnings, funding accrual, unprotected positions, risk summary, auto-reactions
5. `reconnection.feature` — 7 scenarios covering auto-reconnect, subscription restore, REST re-sync, gap_detected, trading pause, full recovery, multiple disconnections
6. `error_safety.feature` — 7 scenarios covering SAFE/UNKNOWN/STALE/CRITICAL classification with concrete error types
7. `price_formatting.feature` — 6 scenarios covering human↔chain conversion, rounding, clamping, raw mode, round-trip fidelity
