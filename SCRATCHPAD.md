# Scratchpad

## Task: Add computed properties to Pydantic models in Decibel SDK

### Status: Complete

### Changes Made
1. **market.py** - Added computed properties to `PerpMarketConfig`, `MarketDepth`, `MarketPrice`, and `Candlestick`. Added `model_config = ConfigDict(populate_by_name=True)` to `PerpMarketConfig`. Added `ConfigDict` to pydantic import.
2. **account.py** - Added computed properties to `AccountOverview`, `UserPosition`, `UserOpenOrder`, and `UserTradeHistoryItem`.
3. **common.py** - Added `TransactionResult` class.
4. **__init__.py** - Exported `TransactionResult` from models package.
