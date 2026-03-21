# Conversation Log

## Task: Add computed properties to Decibel SDK Pydantic models

**Request**: Add computed properties to existing Pydantic models in market.py, account.py, and common.py without changing existing fields.

**Actions taken**:
- Read all three files to understand current structure
- Added computed properties to PerpMarketConfig (min_size_decimal, lot_size_decimal, tick_size_decimal, mm_fraction) + model_config
- Added computed properties to MarketDepth (best_bid, best_ask, spread, mid_price, bid_depth_at, ask_depth_at, imbalance)
- Added computed properties to MarketPrice (funding_rate_hourly, funding_direction, __str__)
- Added computed properties to Candlestick (is_bullish, body_pct, range_pct)
- Added computed properties to AccountOverview (margin_usage_pct, liquidation_buffer_usd, liquidation_buffer_pct, is_liquidation_warning, total_withdrawable)
- Added computed properties to UserPosition (is_long, is_short, is_flat, direction, notional, unrealized_pnl, unrealized_pnl_pct, total_unrealized_pnl, liquidation_distance_pct, has_tp, has_sl, has_protection)
- Added computed properties to UserOpenOrder (filled_size, fill_pct, side, notional, age_ms)
- Added computed properties to UserTradeHistoryItem (net_pnl, notional)
- Added TransactionResult class to common.py
- Exported TransactionResult from models __init__.py
