# Conversation Log

## Task: Fix 15 PR Review Comments for Decibel Python SDK

### Request
Fix all 15 PR review comments across docs, models, state management, error handling, CI, and utilities.

### Approach
1. Read all source files and test files to understand current behavior
2. Analyzed test expectations to determine correct implementation for ambiguous cases
3. Applied targeted fixes to each file
4. Updated test assertions where implementation semantics changed (margin_usage_pct, mm_fraction)
5. Ran full test suite — 392/392 passed
6. Committed and pushed to branch

### Key Decisions
- **Item 1 (table syntax)**: Tables were already correctly formatted. The `||` appearance in file reads was the line-number separator adjacent to table pipes.
- **Item 5 (mm_fraction)**: Updated both implementation (remove `/100`) and fixture (`margin_call_fee_pct=0.005`) to be consistent.
- **Item 8 (margin_usage_pct)**: Changed to 0.0–1.0 scale, also updated `margin_warning` thresholds from 80/90 to 0.80/0.90 and test assertion from 20.0 to 0.20.
- **Item 9 (funding_accrual_rate)**: Tests expect absolute (unsigned) values. Current implementation already matches. No change made.
