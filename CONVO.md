# Conversation Log

## 2026-03-22: Fix float precision issues in Decibel Python SDK

**Request:** Rewrite formatting.py and price.py to use `decimal.Decimal` for all chain unit conversions, and fix write.py to use `amount_to_chain_units` instead of raw `int(x * 10**8)`.

**Actions taken:**
1. Read all relevant source files and test file.
2. Rewrote `formatting.py` with Decimal-based arithmetic for `amount_to_chain_units`, `round_to_valid_price`, `round_to_valid_order_size`, and related helpers.
3. Rewrote `price.py` with Decimal-based `round_to_tick_size`.
4. Fixed `write.py` — replaced 3 instances of `int(x * 10**8)` with `amount_to_chain_units(x, decimals=8)`.
5. Ran full test suite: 392/392 passed.
6. Committed and pushed to `cursor/v2-sdk-agent-specifications-7958`.
