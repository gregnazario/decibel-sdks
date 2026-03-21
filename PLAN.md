# Plan

## V2 SDK Specification — Agent-First Design

### Phase 1: Specification (COMPLETE)
- [x] Analyze docs.decibel.trade API surface
- [x] Document agent-first design principles
- [x] Define all data models with schemas
- [x] Specify Python SDK (Pydantic v2, async, idiomatic)
- [x] Specify Rust SDK (serde, tokio, idiomatic)
- [x] Specify REST API client with full endpoint catalog
- [x] Specify WebSocket streaming with topics and lifecycle
- [x] Specify transaction builder (sync build, signing, submission)
- [x] Define error taxonomy with recovery patterns
- [x] Set performance targets and benchmarks
- [x] Document agent integration patterns

### Phase 2: Implementation (NEXT)
- [ ] Implement Python SDK based on v2 specification
- [ ] Implement Rust SDK based on v2 specification
- [ ] Write unit tests for all data models
- [ ] Write integration tests against testnet
- [ ] Write benchmarks for serialization, formatting, and tx building
- [ ] Set up CI for both SDKs

### Phase 3: Validation
- [ ] Run agent scenario tests
- [ ] Measure performance against targets
- [ ] Validate LLM tool integration
- [ ] Documentation review
