# SCRATCHPAD

## Status: Complete

## V2 Specification — Second Pass (Trading Bot & Agent Deep Dive)

### What Changed

Rewrote all 11 docs + added Go SDK spec (12 total, 11,700+ lines). Major changes:

1. **Design principles**: Replaced generic SW principles with concrete trading problems
   - Position state management with computed risk fields
   - Bulk order management as core market making primitive
   - Continuous funding impact awareness
   - Margin/leverage/liquidation as hard constraints
   - Fee schedule awareness for strategy profitability
   - Transaction latency budgets with realistic numbers
   - Reconnection without state loss protocol
   - Errors with position safety classification

2. **Data models**: Added computed methods on all major models
   - MarketDepth: spread, imbalance, depth_at
   - UserPosition: unrealized_pnl, liquidation_distance_pct, has_protection
   - AccountOverview: margin_usage_pct, liquidation_buffer, is_liquidation_warning
   - Added BulkOrderSet and BulkOrderFill models

3. **Python SDK**: Rewrote around PositionStateManager, BulkOrderManager, order lifecycle tracking, risk monitoring, reconnection strategy, real bot patterns

4. **Rust SDK**: Rewrote with zero-allocation hot paths, lock-free patterns, PositionSafety enum on errors, cache-line-aligned position state, real market making example, criterion benchmarks

5. **Go SDK**: New spec for future infrastructure use (API gateways, orchestrators, monitoring)

6. **REST API**: Added rate limit strategy, request prioritization by bot type, state reconciliation protocol

7. **WebSocket**: Added orderbook management (full snapshot model), state synchronization, topic priority by bot type, latency measurement, multi-subaccount subscription management

8. **Transaction builder**: Added clock drift handling, bulk order specifics (sequence numbers, partial failures), gas station vs self-paid comparison, parallel submission patterns, ABI versioning

9. **Error handling**: Rewrote around position safety classification (SAFE/UNKNOWN/STALE/CRITICAL), critical error classes, emergency procedures, trading-specific recovery scenarios

10. **Performance**: Rewrote with end-to-end latency budget, hot path identification, Rust memory layout, gas cost analysis, real-world benchmark specifications

11. **Agent patterns**: 5 production-ready patterns: market making (with quote engine, inventory skew, PnL tracker), funding rate arbitrage, multi-leg strategy, LLM-powered agent, risk watchdog; plus anti-patterns section
