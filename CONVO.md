# Conversation Log

## 2026-03-21 (session 2): TDD Test Files — Models, Enums, Utils

**Request:** Create 7 TDD test files for the Decibel Python SDK covering models (market, account, order, enums) and utilities (formatting, address, nonce).

**Actions Taken:**
- Reviewed all source models (market.py, account.py, order.py, common.py, enums.py), utilities (price.py, address.py, crypto.py), and existing test files
- Updated conftest.py with model-instance fixtures used by the TDD tests (btc_perp_config, btc_market_price, btc_long_position, eth_short_position, flat_position, account_overview, zero_equity_account, btc_open_order, order_status_filled, place_order_success/failure, btc_trade_history_item, etc.)
- test_market.py and test_account.py already existed with comprehensive TDD tests matching the spec — kept as-is
- Added UserTradeHistoryItem tests (notional, net_pnl, rebate, loss) to test_order.py
- Created test_enums.py covering all 9 enum types with wire values, roundtrips, variant counts, and OrderStatusType helper methods
- Created test_formatting.py for TDD of `decibel.utils.formatting` (module does not yet exist)
- Created test_address.py testing get_market_addr and get_primary_subaccount_addr determinism and format
- Created test_nonce.py testing generate_replay_protection_nonce from `decibel.utils.nonce` (module does not yet exist)

**Key Decisions:**
- TDD imports: test_formatting.py imports from `decibel.utils.formatting` and test_nonce.py imports from `decibel.utils.nonce` — these modules will be created during implementation
- Fixtures use realistic BTC ~$95k / ETH ~$3.5k data for meaningful numeric assertions
- All computed method tests include docstrings explaining trading bot relevance

## 2026-03-21 (session 1): TDD Test Files for Decibel Python SDK

**Request:** Create 5 TDD test files for the Decibel Python SDK, written before implementation.

**Actions Taken:**
- Reviewed existing codebase: models, errors, conftest fixtures, existing test stubs
- Found 3 of 5 test files already existed with good coverage; added missing test cases
- Created 2 new test files from scratch (risk_monitor, bulk_order_manager)
- All files pass Python syntax validation

**Key Decisions:**
- Used existing model types (UserPosition, AccountOverview, MarketPrice, etc.) from `decibel.models`
- Test imports reference modules that don't exist yet (TDD approach): `decibel.state.position_manager`, `decibel.state.risk_monitor`, `decibel.state.order_tracker`, `decibel.bulk.order_manager`
- Error tests import new error types (PositionSafety, RiskMonitor, etc.) that need to be implemented
