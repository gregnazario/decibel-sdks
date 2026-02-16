# Decibel Cross-Platform SDK - Scratchpad

## Current Status: Phase 2 - Writing BDD Tests

## Completed
- [x] Explored workspace and existing codebase
- [x] Downloaded and analyzed TypeScript SDK (`@decibeltrade/sdk` v0.3.1)
- [x] Fetched and analyzed Decibel documentation sitemap
- [x] Created comprehensive specification document (`docs/specification.md`) - 5 iterations
- [x] Created implementation plan (`PLAN.md`)

## In Progress
- [ ] Writing BDD test suites for Rust SDK
- [ ] Writing BDD test suites for Swift SDK
- [ ] Writing BDD test suites for Kotlin SDK
- [ ] Writing BDD test suites for Go SDK

## Pending
- [ ] Build Rust SDK
- [ ] Build Swift SDK
- [ ] Build Kotlin SDK
- [ ] Build Go SDK

## Key Reference Info
- TypeScript SDK: `@decibeltrade/sdk` v0.3.1
- Aptos TS SDK: `@aptos-labs/ts-sdk` ^5.2.1
- Decibel Docs: https://docs.decibel.trade/
- Platform: Fully on-chain perpetuals exchange on Aptos
- Compat Version: v0.4

## Architecture Notes
- Read client: REST + WebSocket, no private key needed
- Write client: On-chain Aptos transactions, Ed25519 keypair required
- Gas station: Sponsored transactions via gas station URL + API key
- Subaccount system: Primary subaccount derived from owner address
- Market addresses: Derived from market name + perp engine global address
