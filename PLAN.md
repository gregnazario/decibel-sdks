# Plan

## Phase 1: Models, Config, and TDD Tests (COMPLETE)
- [x] config.rs — Network, Deployment, DecibelConfig, presets
- [x] models/enums.rs — all enumerations with serde
- [x] models/common.rs — pagination and result types
- [x] models/market.rs — market data models with computed methods
- [x] models/account.rs — account models with computed methods
- [x] tests/integration_models.rs — cross-crate integration tests
- [x] All 181 tests passing

## Phase 2: Future Work (not yet started)
- [ ] client.rs — DecibelClient builder
- [ ] read/ — REST reader methods
- [ ] write/ — order placement, position management
- [ ] ws/ — WebSocket manager, zero-copy parser
- [ ] state/ — PositionStateManager, BulkOrderManager
- [ ] tx/ — transaction building and signing
- [ ] bench/ — criterion benchmarks
