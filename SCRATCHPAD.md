# Scratchpad

## Task: Create TDD test files for Decibel Python SDK (V2 — models, utils, enums)

### Status: COMPLETE

### Files Written/Updated (this session):
1. `decibel-sdk-python/tests/conftest.py` — Expanded with model-instance fixtures (btc_perp_config, btc_market_price, btc_long_position, etc.) and NOW_MS constant
2. `decibel-sdk-python/tests/unit/models/test_market.py` — Already comprehensive (PerpMarketConfig, MarketPrice, MarketDepth, Candlestick computed methods, immutability)
3. `decibel-sdk-python/tests/unit/models/test_account.py` — Already comprehensive (AccountOverview margin/liquidation helpers, UserPosition direction/notional/PnL, UserSubaccount)
4. `decibel-sdk-python/tests/unit/models/test_order.py` — Added UserTradeHistoryItem tests (notional, net_pnl, rebate handling, loss cases)
5. `decibel-sdk-python/tests/unit/models/test_enums.py` — Created: all 9 enums tested (wire values, variant counts, roundtrip, OrderStatusType parse/is_success/is_failure/is_final)
6. `decibel-sdk-python/tests/unit/utils/test_formatting.py` — Created: round_to_valid_price, round_to_valid_order_size, amount_to_chain_units, chain_units_to_amount, to_chain_price, from_chain_price
7. `decibel-sdk-python/tests/unit/utils/test_address.py` — Created: get_market_addr, get_primary_subaccount_addr (determinism, uniqueness, format, regression vectors)
8. `decibel-sdk-python/tests/unit/utils/test_nonce.py` — Created: generate_replay_protection_nonce (type, u64 range, uniqueness, full-range usage)

### Previous session files:
1. `decibel-sdk-python/tests/unit/state/test_position_manager.py` — Updated with multi-subaccount and is_connected tests
2. `decibel-sdk-python/tests/unit/state/test_risk_monitor.py` — Created from scratch
3. `decibel-sdk-python/tests/unit/bulk/test_bulk_order_manager.py` — Created from scratch
4. `decibel-sdk-python/tests/unit/state/test_order_tracker.py` — Updated with status lookup, cancel transition, and duplicate-status tests
5. `decibel-sdk-python/tests/unit/test_errors.py` — Updated with comprehensive is_retryable and retry_after_ms property tests
