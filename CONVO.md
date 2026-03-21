# Conversation Log

## 2026-03-21: TDD Test Files for Decibel Python SDK

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
