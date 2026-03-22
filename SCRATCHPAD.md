# Scratchpad

## Task: Fix float precision issues in Decibel Python SDK

### Status: COMPLETE

### Changes Made
1. **`decibel/utils/formatting.py`** — Rewrote to use `decimal.Decimal` for all chain unit conversions and tick/lot rounding. Added `_to_decimal()` helper that converts via string to avoid float representation errors.
2. **`decibel/utils/price.py`** — Rewrote `round_to_tick_size` to use `Decimal` arithmetic with `quantize()` for precise rounding.
3. **`decibel/client/write.py`** — Replaced all `int(x * 10**8)` patterns with `amount_to_chain_units(x, decimals=8)`.

### Test Results
All 392 tests pass.
