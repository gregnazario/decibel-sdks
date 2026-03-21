# Conversation Log

## 2026-03-21

### Task: Build V2 SDK Specification Docs

**Request**: Build a new set of specification docs under `docs/v2/` defining an SDK built for AI agents first, including structured data, documentation, and high performance. Use docs.decibel.trade as reference. Target Python and Rust SDKs. Should be idiomatic but agent-first.

**Approach**:
1. Fetched full API documentation from docs.decibel.trade (llms.txt, REST overview, WebSocket overview, on-chain reference, authentication, connection management, contract reference, optimized building, formatting, TypeScript SDK read/write)
2. Analyzed existing v1 specification and repo structure (5 SDK implementations across Python, Rust, Go, Swift, Kotlin)
3. Designed v2 specification with agent-first paradigm: structured data everywhere, self-documenting API, predictable errors, high performance by default
4. Created 11 specification documents covering: overview, design principles, data models, Python SDK, Rust SDK, REST API, WebSocket API, transaction builder, error handling, performance, and agent patterns

**Key Differences from V1**:
- Agent-first design principles instead of developer-first
- Unified `DecibelClient` entry point (v1 had separate ReadClient/WriteClient)
- Schema discovery built-in (JSON Schema export for models)
- Structured errors with `retryable`, `retry_after_ms`, and machine-readable codes
- Async iterator / stream alternatives for WebSocket (beyond callbacks)
- LLM tool integration patterns
- Performance benchmarks with concrete targets
- Updated to latest API surface (v2 WS topics like `depth:{addr}`, `market_price:{addr}`, bearer token auth)
