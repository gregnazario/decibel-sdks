# Scratchpad

## Current Task
Create Rust v2 SDK models, config, and TDD tests at `/workspace/sdk-rust-v2/`.

## Status: COMPLETE
- All files created and compiling
- 169 unit tests + 12 integration tests passing (181 total)

## Files Created/Modified
1. `sdk-rust-v2/Cargo.toml` — added `serde_repr` dependency
2. `sdk-rust-v2/src/lib.rs` — re-exports config, error, models, utils
3. `sdk-rust-v2/src/config.rs` — Network enum (Mainnet/Testnet/Devnet/Custom), Deployment, DecibelConfig, presets
4. `sdk-rust-v2/src/models/mod.rs` — re-exports enums, common, market, account
5. `sdk-rust-v2/src/models/enums.rs` — TimeInForce, CandlestickInterval, VolumeWindow, OrderStatusType, SortDirection, TwapStatus, TradeAction, VaultType, DepthAggregationLevel
6. `sdk-rust-v2/src/models/common.rs` — PageParams, SortParams, PaginatedResponse<T>, PlaceOrderResult, TransactionResult
7. `sdk-rust-v2/src/models/market.rs` — PerpMarketConfig, MarketOrder, MarketDepth, MarketPrice, MarketContext, Candlestick, MarketTrade
8. `sdk-rust-v2/src/models/account.rs` — AccountOverview, UserPosition, UserOpenOrder, UserTradeHistoryItem, UserSubaccount, UserFundingHistoryItem, UserFundHistoryItem, Delegation
9. `sdk-rust-v2/tests/integration_models.rs` — cross-crate integration tests
