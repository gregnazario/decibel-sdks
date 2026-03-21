# Decibel V2 SDK Specification

**Version**: 2.0.0  
**Date**: 2026-03-21  
**Target Languages**: Python, Rust  
**Paradigm**: Agent-First  
**Reference**: [docs.decibel.trade](https://docs.decibel.trade) and `@decibeltrade/sdk` v0.3.1 (TypeScript)

---

## What Is This

This specification defines two SDKs — one in Python, one in Rust — for the Decibel on-chain perpetual futures exchange on Aptos. Unlike the v1 specification which targeted human developers building interactive UIs, v2 is designed **for AI agents first**: autonomous programs that read market state, make decisions, and execute trades without human intervention in the loop.

## Why Agent-First

AI agents are the fastest-growing consumer of trading APIs. They differ from human developers in critical ways:

| Concern | Human Developer | AI Agent |
|---|---|---|
| **Discovery** | Reads docs, browses examples | Inspects schemas, enumerates capabilities |
| **Error recovery** | Reads stack traces, debugs | Needs structured errors with retry hints |
| **Data format** | Flexible — can parse anything | Needs strongly-typed, self-describing data |
| **Performance** | Tolerates latency in UI | Microseconds matter in decision loops |
| **Composition** | Writes bespoke glue code | Chains atomic operations programmatically |
| **Observability** | Checks logs manually | Needs machine-readable metrics and traces |

The v2 SDK is built around these realities.

## Target Languages

### Python

Python is the primary language for AI/ML agents, trading bots, and data pipelines. The v2 Python SDK uses:

- **Pydantic v2** for all data models (JSON Schema generation, validation, serialization)
- **asyncio + httpx** for async HTTP
- **websockets** for real-time streaming
- Type annotations everywhere for agent introspection
- `__repr__` and `__str__` on all types for LLM-friendly output

### Rust

Rust is the primary language for high-frequency trading, co-located strategies, and infrastructure. The v2 Rust SDK uses:

- **serde** with derive macros for zero-cost serialization
- **tokio** async runtime
- **reqwest** for HTTP with connection pooling
- **tokio-tungstenite** for WebSocket
- Full `Send + Sync` guarantees for concurrent agents
- `thiserror` for structured error hierarchies

## Document Index

| Document | Description |
|---|---|
| [01-design-principles.md](./01-design-principles.md) | Agent-first design principles and patterns |
| [02-structured-data-models.md](./02-structured-data-models.md) | All data types, enums, and schemas |
| [03-python-sdk.md](./03-python-sdk.md) | Python SDK specification and idioms |
| [04-rust-sdk.md](./04-rust-sdk.md) | Rust SDK specification and idioms |
| [05-rest-api.md](./05-rest-api.md) | REST API client specification |
| [06-websocket-api.md](./06-websocket-api.md) | WebSocket streaming specification |
| [07-transaction-builder.md](./07-transaction-builder.md) | On-chain transaction builder specification |
| [08-error-handling.md](./08-error-handling.md) | Error taxonomy, recovery, and observability |
| [09-performance.md](./09-performance.md) | Performance requirements and benchmarks |
| [10-agent-patterns.md](./10-agent-patterns.md) | Agent integration patterns and examples |

## Platform Summary

Decibel is a fully on-chain perpetual futures exchange on Aptos:

- **Order book**: Central Limit Order Book (CLOB) matching engine
- **Margin**: Cross and isolated margin modes
- **Collateral**: Multi-collateral, primarily USDC
- **Accounts**: Subaccount system for position isolation
- **Vaults**: Pooled capital management with performance fees
- **Orders**: Limit, IOC, post-only, TWAP, bulk, TP/SL
- **Delegation**: Automated trading via delegated accounts
- **Builder fees**: Revenue share for frontend/bot integrators

### API Surface

| Layer | Transport | Purpose |
|---|---|---|
| REST API | HTTPS GET | Read market data, account state, history |
| WebSocket | WSS | Real-time streaming of prices, positions, orders |
| On-Chain | Aptos transactions | Write operations — place orders, manage accounts |

### Network Endpoints

| Network | REST Base URL | WebSocket URL |
|---|---|---|
| Mainnet | `https://api.mainnet.aptoslabs.com/decibel` | `wss://api.mainnet.aptoslabs.com/decibel/ws` |
| Testnet | `https://api.testnet.aptoslabs.com/decibel` | `wss://api.testnet.aptoslabs.com/decibel/ws` |

### Authentication

- **REST/WebSocket**: Bearer token via `Authorization: Bearer <KEY>` header (REST) or `Sec-Websocket-Protocol: decibel, <KEY>` (WebSocket)
- **On-Chain**: Ed25519 private key for transaction signing
- **Node API**: Aptos fullnode API key for higher rate limits

## Versioning

The v2 SDK targets compatibility version `v0.4` of the Decibel protocol. The SDK version follows semver independently from the protocol version.
