# Decibel V2 SDK Specification

**Version**: 2.0.0  
**Date**: 2026-03-21  
**Target Languages**: Python, Rust, Go (future)  
**Paradigm**: Trading Bot & Agentic Trading First  
**Reference**: [docs.decibel.trade](https://docs.decibel.trade) and `@decibeltrade/sdk` v0.3.1 (TypeScript)

---

## What Is This

This specification defines SDKs for the Decibel on-chain perpetual futures exchange on Aptos. The primary consumers are **trading bots** and **AI agents** — autonomous programs that monitor markets, manage risk, and execute trades without human involvement.

The specification covers three languages in priority order:

1. **Python** — for AI/ML agents, strategy prototyping, data pipelines, and medium-frequency trading
2. **Rust** — for latency-critical market making, HFT, co-located infrastructure, and production trading systems
3. **Go** — (future) for high-concurrency server infrastructure, API gateways, and microservice-based trading architectures

## Who This Is For

This SDK is **not** designed for humans clicking buttons in a UI. It is designed for:

- **Market making bots** that atomically quote bid/ask spreads using bulk orders, manage inventory, and react to fills in sub-second loops
- **Directional trading agents** (AI or algorithmic) that consume price feeds, compute signals, and execute via TWAP or limit orders
- **Risk management systems** that monitor positions, margin ratios, funding accrual, and liquidation proximity — triggering protective actions automatically
- **Vault management agents** that allocate capital across strategies, rebalance positions, and report performance
- **Arbitrage systems** that detect and act on cross-venue price dislocations
- **Infrastructure** that aggregates market data, provides execution routing, or wraps Decibel for higher-level trading platforms

## What Matters for Bots

The v2 SDK is shaped by the realities of what bots need:

| Concern | Why It Matters | How v2 Addresses It |
|---|---|---|
| **Order lifecycle tracking** | Bots must know exactly what happened to every order — placed, filled, partially filled, rejected, cancelled | Every write returns structured results with tx hash and order ID; WebSocket streams order updates; client_order_id for correlation |
| **Position state awareness** | Bots must always know their current exposure, margin usage, and liquidation distance | Local position state manager synced via WebSocket; computed fields for margin ratio, liq distance |
| **Bulk order management** | Market makers need to atomically replace all quotes in a single tx | First-class bulk order API with sequence number management and fill tracking |
| **Funding rate impact** | Continuous funding accrues every second and affects equity/liquidation | SDK computes funding impact on unrealized PnL; models expose accrued funding fields |
| **Fee awareness** | Maker/taker fees affect strategy profitability | Fee schedule exposed; order results include fee amounts; builder fee support |
| **Transaction latency** | Every millisecond between signal and execution is money | Synchronous tx build, pre-cached ABI/gas/chain-id, parallel submission via orderless nonces |
| **Reconnection without state loss** | Network drops cannot cause missed fills or orphaned orders | WS auto-reconnect with subscription restore; position state re-sync on reconnect |
| **Idempotent order placement** | Retry logic must not double-place orders | client_order_id as natural idempotency key; cancel-by-client-id |
| **Gas management** | On-chain execution means gas costs matter at scale | Background gas price manager, gas station for sponsored tx, gas estimation with multiplier |
| **Multi-subaccount isolation** | Run multiple strategies with isolated margin/risk | First-class subaccount management; per-subaccount state tracking |

## Document Index

| Document | Description |
|---|---|
| [01-design-principles.md](./01-design-principles.md) | What bots and agents actually need, and the design decisions that follow |
| [02-structured-data-models.md](./02-structured-data-models.md) | All data types, enums, computed fields, and derived state |
| [03-python-sdk.md](./03-python-sdk.md) | Python SDK specification — strategy prototyping and AI agents |
| [04-rust-sdk.md](./04-rust-sdk.md) | Rust SDK specification — high-performance production trading |
| [05-rest-api.md](./05-rest-api.md) | REST API client with rate limit strategy and caching |
| [06-websocket-api.md](./06-websocket-api.md) | WebSocket streaming, orderbook management, state synchronization |
| [07-transaction-builder.md](./07-transaction-builder.md) | On-chain transaction builder — latency optimization deep dive |
| [08-error-handling.md](./08-error-handling.md) | Trading-specific error recovery and position safety |
| [09-performance.md](./09-performance.md) | Performance requirements, real trading benchmarks |
| [10-agent-patterns.md](./10-agent-patterns.md) | Real agentic trading workflows and architecture patterns |
| [11-go-sdk.md](./11-go-sdk.md) | Go SDK specification — future high-concurrency server infrastructure |

## Platform Summary

Decibel is a fully on-chain perpetual futures exchange on Aptos:

- **Order book**: Central Limit Order Book (CLOB) with price-time priority, deterministic matching
- **Matching**: Executed via Aptos Block-STM — matching and settlement in one atomic transaction
- **Margin**: Cross-margin (shared collateral) and isolated margin modes
- **Mark price**: `median(P_oracle, P_mid, P_basis)` where `P_basis = P_oracle × EMA_150s(P_mid / P_oracle)`
- **Funding**: Continuous — accrues every oracle update (~1 second), not periodic
- **Collateral**: USDC (6 decimals); multi-collateral support
- **Liquidation**: Two-stage (market disposition → backstop vault), fully on-chain
- **Fees**: Tiered maker/taker (0 maker at $1B+ volume); builder fee system for integrators
- **Accounts**: Owner → API Wallet → Subaccount (Trading Account) hierarchy; delegation system
- **Vaults**: On-chain pooled capital with fungible share tokens and interval performance fees
- **Orders**: Limit (GTC/PostOnly/IOC), TWAP, bulk orders (atomic replace), stop orders, TP/SL

### API Surface

| Layer | Transport | Purpose |
|---|---|---|
| REST API | HTTPS GET | Read market data, account state, history |
| WebSocket | WSS | Real-time streaming of prices, depth, positions, orders, fills |
| On-Chain | Aptos transactions | Write operations — place/cancel orders, deposits, delegations, vaults |

### Network Endpoints

| Network | REST Base URL | WebSocket URL |
|---|---|---|
| Mainnet | `https://api.mainnet.aptoslabs.com/decibel` | `wss://api.mainnet.aptoslabs.com/decibel/ws` |
| Testnet | `https://api.testnet.aptoslabs.com/decibel` | `wss://api.testnet.aptoslabs.com/decibel/ws` |

### Authentication

| Method | When Used | How |
|---|---|---|
| Bearer token | REST and WebSocket | `Authorization: Bearer <KEY>` (REST), `Sec-Websocket-Protocol: decibel, <KEY>` (WS) |
| Node API key | Aptos fullnode calls | Higher rate limits for tx submission and view calls |
| Ed25519 private key | On-chain transactions | Signs raw transaction bytes |

### Contract Addresses

| Network | Package Address |
|---|---|
| Mainnet | `0x50ead22afd6ffd9769e3b3d6e0e64a2a350d68e8b102c4e72e33d0b8cfdfdb06` |
| Testnet | `0x952535c3049e52f195f26798c2f1340d7dd5100edbe0f464e520a974d16fbe9f` |

## What Changed from V1

| Area | V1 | V2 |
|---|---|---|
| **Target audience** | Human developers building UIs | Trading bots and AI agents |
| **Languages** | Rust, Swift, Kotlin, Go | Python, Rust, Go (future) |
| **Client model** | Separate ReadClient + WriteClient | Unified client with state management |
| **Position tracking** | Fetch-only | Local state synced via WebSocket with computed risk fields |
| **Bulk orders** | Basic support | First-class with sequence management, fill tracking |
| **Error handling** | Type hierarchy | Structured errors with retry hints and position safety flags |
| **Funding** | Raw fields | Computed impact on PnL and liquidation distance |
| **Fee model** | Not specified | Fee schedule, builder fees, fee estimation |
| **Orderbook** | Snapshot only | Managed local full-depth orderbook from snapshots (no incremental deltas) |
| **Testing** | Unit + integration | Unit + integration + property + agent scenario + backtest |
