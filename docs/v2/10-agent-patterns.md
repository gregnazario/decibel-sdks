# Agent Integration Patterns

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

This document provides reference architectures and patterns for AI agents integrating with Decibel via the v2 SDK. These patterns are designed for autonomous operation — agents that run continuously, make decisions based on market state, and execute trades without human intervention.

---

## Pattern 1: Market Monitoring Agent

A read-only agent that streams market data and produces signals. No private key needed.

### Architecture

```
┌──────────────────────────────────────────┐
│              Market Monitor              │
│                                          │
│  ┌──────────┐    ┌──────────────────┐    │
│  │ WS Price │───→│ Signal Generator │──→ Output (signals, alerts)
│  │  Stream   │    └──────────────────┘    │
│  └──────────┘                            │
│  ┌──────────┐    ┌──────────────────┐    │
│  │ WS Depth │───→│ Liquidity Model  │──→ Output
│  │  Stream   │    └──────────────────┘    │
│  └──────────┘                            │
│  ┌──────────┐    ┌──────────────────┐    │
│  │ REST     │───→│ Context Enricher │──→ Output
│  │ Polling   │    └──────────────────┘    │
│  └──────────┘                            │
└──────────────────────────────────────────┘
```

### Python Implementation

```python
import asyncio
from decibel import DecibelClient, MAINNET_CONFIG
from decibel.models import MarketPrice, MarketDepth

class MarketMonitor:
    def __init__(self, bearer_token: str, markets: list[str]):
        self.client = DecibelClient(config=MAINNET_CONFIG, bearer_token=bearer_token)
        self.markets = markets
        self.latest_prices: dict[str, MarketPrice] = {}

    async def run(self):
        async with self.client:
            unsubs = []
            for market in self.markets:
                unsub = await self.client.subscribe_market_price(
                    market, callback=self._on_price
                )
                unsubs.append(unsub)

            try:
                await asyncio.Event().wait()  # run forever
            finally:
                for unsub in unsubs:
                    await unsub()

    async def _on_price(self, price: MarketPrice):
        self.latest_prices[price.market] = price
        if self._detect_signal(price):
            await self._emit_signal(price)

    def _detect_signal(self, price: MarketPrice) -> bool:
        """Implement signal detection logic."""
        ...

    async def _emit_signal(self, price: MarketPrice):
        """Emit signal to downstream consumers."""
        ...
```

---

## Pattern 2: Execution Agent

An agent that receives signals and executes trades. Requires a private key.

### Architecture

```
┌───────────────────────────────────────────────────┐
│                Execution Agent                     │
│                                                    │
│  Signal ──→ ┌──────────┐    ┌───────────────────┐ │
│  Input      │ Validate  │───→│ Format & Execute  │ │
│             └──────────┘    └───────────────────┘ │
│                                      │             │
│                               ┌──────▼──────┐     │
│                               │  Confirm &   │     │
│                               │  Monitor     │     │
│                               └─────────────┘     │
└───────────────────────────────────────────────────┘
```

### Python Implementation

```python
from decibel import DecibelClient, MAINNET_CONFIG
from decibel.models import PlaceOrderResult, TimeInForce, UserPosition
from decibel.errors import DecibelError, RateLimitError, VmError

class ExecutionAgent:
    def __init__(self, bearer_token: str, private_key: str):
        self.client = DecibelClient(
            config=MAINNET_CONFIG,
            bearer_token=bearer_token,
            private_key=private_key,
        )
        self.positions: dict[str, UserPosition] = {}

    async def execute_signal(self, signal: dict) -> dict:
        """Execute a trading signal and return the result.

        Returns a structured result for the agent's decision log.
        """
        market = signal["market"]
        side = signal["side"]  # "buy" or "sell"
        size = signal["size"]

        market_config = await self.client.get_market(market)
        prices = await self.client.get_price(market)
        current_price = prices[0].mark_px

        # Determine limit price with slippage tolerance
        slippage_bps = signal.get("max_slippage_bps", 10)
        if side == "buy":
            limit_price = current_price * (1 + slippage_bps / 10_000)
        else:
            limit_price = current_price * (1 - slippage_bps / 10_000)

        try:
            result: PlaceOrderResult = await self.client.place_order(
                market_name=market,
                price=limit_price,
                size=size,
                is_buy=(side == "buy"),
                time_in_force=TimeInForce.ImmediateOrCancel,
                is_reduce_only=signal.get("reduce_only", False),
                client_order_id=signal.get("signal_id"),
            )

            return {
                "status": "executed" if result.success else "rejected",
                "order_id": result.order_id,
                "transaction_hash": result.transaction_hash,
                "error": result.error,
            }

        except RateLimitError as e:
            return {"status": "rate_limited", "retry_after_ms": e.retry_after_ms}
        except VmError as e:
            return {"status": "vm_error", "vm_status": e.vm_status}
        except DecibelError as e:
            return {"status": "error", "code": e.code, "retryable": e.retryable}
```

---

## Pattern 3: Position Management Agent

An agent that monitors open positions and manages TP/SL orders, rebalancing, and risk limits.

### Python Implementation

```python
import asyncio
from decibel import DecibelClient, MAINNET_CONFIG
from decibel.models import UserPosition, AccountOverview

class PositionManager:
    def __init__(self, bearer_token: str, private_key: str, subaccount: str):
        self.client = DecibelClient(
            config=MAINNET_CONFIG,
            bearer_token=bearer_token,
            private_key=private_key,
        )
        self.subaccount = subaccount
        self.max_drawdown_pct = 5.0
        self.tp_pct = 3.0
        self.sl_pct = 2.0

    async def run(self):
        async with self.client:
            unsub_positions = await self.client.subscribe_positions(
                self.subaccount, callback=self._on_positions
            )
            unsub_overview = await self.client.subscribe_account_overview(
                self.subaccount, callback=self._on_overview
            )

            try:
                await asyncio.Event().wait()
            finally:
                await unsub_positions()
                await unsub_overview()

    async def _on_positions(self, update):
        for position in update.positions:
            await self._manage_position(position)

    async def _on_overview(self, overview: AccountOverview):
        if overview.cross_margin_ratio < 0.1:
            await self._emergency_reduce_positions()

    async def _manage_position(self, position: UserPosition):
        if position.size == 0:
            return

        # Set TP/SL if not already set
        if position.tp_order_id is None:
            tp_price = position.entry_price * (
                1 + self.tp_pct / 100 if position.size > 0
                else 1 - self.tp_pct / 100
            )
            sl_price = position.entry_price * (
                1 - self.sl_pct / 100 if position.size > 0
                else 1 + self.sl_pct / 100
            )

            await self.client.place_tp_sl(
                market_addr=position.market,
                tp_trigger_price=tp_price,
                tp_limit_price=tp_price,
                sl_trigger_price=sl_price,
                sl_limit_price=sl_price,
                subaccount_addr=self.subaccount,
            )

    async def _emergency_reduce_positions(self):
        """Close all positions when margin is dangerously low."""
        positions = await self.client.get_positions(self.subaccount)
        for pos in positions:
            if pos.size != 0:
                await self.client.place_order(
                    market_name=pos.market,
                    price=0,  # market order via IOC at aggressive price
                    size=abs(pos.size),
                    is_buy=(pos.size < 0),  # buy to close short, sell to close long
                    time_in_force=TimeInForce.ImmediateOrCancel,
                    is_reduce_only=True,
                )
```

---

## Pattern 4: Market Making Agent

An agent that provides liquidity by quoting bid/ask prices on both sides of the orderbook.

### Rust Implementation

```rust
use decibel_sdk::*;
use std::sync::Arc;
use tokio::sync::RwLock;

struct MarketMaker {
    client: Arc<DecibelClient>,
    market: String,
    spread_bps: f64,
    size: f64,
    active_orders: Arc<RwLock<Vec<String>>>,
}

impl MarketMaker {
    async fn run(&self) -> Result<(), DecibelError> {
        let orders = self.active_orders.clone();
        let client = self.client.clone();
        let market = self.market.clone();
        let spread = self.spread_bps;
        let size = self.size;

        self.client.subscribe_market_price(&self.market, move |price| {
            let orders = orders.clone();
            let client = client.clone();
            let market = market.clone();

            tokio::spawn(async move {
                // Cancel existing orders
                let current = orders.read().await;
                for oid in current.iter() {
                    let _ = client.cancel_order(CancelOrderParams {
                        order_id: oid.clone(),
                        market_name: Some(market.clone()),
                        ..Default::default()
                    }).await;
                }
                drop(current);

                // Quote new bid/ask
                let bid_price = price.mid_px * (1.0 - spread / 10_000.0);
                let ask_price = price.mid_px * (1.0 + spread / 10_000.0);

                let (bid_result, ask_result) = tokio::join!(
                    client.place_order(PlaceOrderParams {
                        market_name: market.clone(),
                        price: bid_price,
                        size,
                        is_buy: true,
                        time_in_force: TimeInForce::PostOnly,
                        is_reduce_only: false,
                        ..Default::default()
                    }),
                    client.place_order(PlaceOrderParams {
                        market_name: market.clone(),
                        price: ask_price,
                        size,
                        is_buy: false,
                        time_in_force: TimeInForce::PostOnly,
                        is_reduce_only: false,
                        ..Default::default()
                    }),
                );

                let mut new_orders = Vec::new();
                if let Ok(r) = bid_result {
                    if let Some(id) = r.order_id { new_orders.push(id); }
                }
                if let Ok(r) = ask_result {
                    if let Some(id) = r.order_id { new_orders.push(id); }
                }

                *orders.write().await = new_orders;
            });
        }).await?;

        tokio::signal::ctrl_c().await.unwrap();
        Ok(())
    }
}
```

---

## Pattern 5: Vault Management Agent

An agent that manages a vault — monitoring depositor flows, rebalancing positions, and reporting performance.

### Python Implementation

```python
class VaultManager:
    def __init__(self, bearer_token: str, private_key: str, vault_address: str):
        self.client = DecibelClient(
            config=MAINNET_CONFIG,
            bearer_token=bearer_token,
            private_key=private_key,
        )
        self.vault_address = vault_address

    async def create_and_activate_vault(self):
        """Create a new vault and activate it."""
        result = await self.client.create_vault(
            vault_name="AI Alpha Vault",
            vault_description="Autonomous momentum-following strategy",
            vault_social_links=[],
            vault_share_symbol="AIALPHA",
            fee_bps=1000,
            fee_interval_s=604800,
            contribution_lockup_duration_s=86400,
            initial_funding=10_000_000,
            accepts_contributions=True,
            delegate_to_creator=True,
        )
        if result.success:
            await self.client.activate_vault(self.vault_address)
        return result

    async def get_vault_health(self) -> dict:
        """Report vault health metrics for agent decision-making."""
        vaults = await self.client.get_vaults()
        vault = next(
            (v for v in vaults.items if v.address == self.vault_address),
            None,
        )
        if not vault:
            return {"status": "not_found"}

        return {
            "status": "healthy",
            "tvl": vault.tvl,
            "depositors": vault.depositors,
            "all_time_return": vault.all_time_return,
            "max_drawdown": vault.max_drawdown,
            "sharpe_ratio": vault.sharpe_ratio,
        }
```

---

## Pattern 6: Multi-Market Scanner

An agent that scans all markets for opportunities using batch operations.

### Python Implementation

```python
class MarketScanner:
    def __init__(self, bearer_token: str):
        self.client = DecibelClient(config=MAINNET_CONFIG, bearer_token=bearer_token)

    async def scan(self) -> list[dict]:
        """Scan all markets and return opportunities."""
        markets = await self.client.get_markets()
        contexts = await self.client.get_asset_contexts()
        prices = await self.client.get_prices()

        context_map = {c.market: c for c in contexts}
        price_map = {p.market: p for p in prices}

        opportunities = []
        for market in markets:
            ctx = context_map.get(market.market_name)
            px = price_map.get(market.market_name)
            if not ctx or not px:
                continue

            score = self._score_market(market, ctx, px)
            if score > 0:
                opportunities.append({
                    "market": market.market_name,
                    "score": score,
                    "price": px.mark_px,
                    "volume_24h": ctx.volume_24h,
                    "funding_rate": px.funding_rate_bps,
                    "open_interest": px.open_interest,
                    "price_change_24h": ctx.price_change_pct_24h,
                })

        return sorted(opportunities, key=lambda x: x["score"], reverse=True)

    def _score_market(self, market, ctx, price) -> float:
        """Score a market for trading opportunity."""
        ...
```

---

## Pattern 7: LLM Tool Integration

The SDK is designed to be used as tools by LLM-based agents. Each method has clear inputs and outputs that map to tool definitions.

### Tool Definition Format (OpenAI-style)

```python
def get_sdk_tools() -> list[dict]:
    """Generate tool definitions from the SDK for LLM agent integration."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_market_price",
                "description": "Get the current price of a market",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market": {
                            "type": "string",
                            "description": "Market name, e.g., 'BTC-USD'",
                        }
                    },
                    "required": ["market"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "place_order",
                "description": "Place a trading order on the exchange",
                "parameters": MarketPrice.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_positions",
                "description": "Get all open positions for a subaccount",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subaccount_addr": {
                            "type": "string",
                            "description": "Subaccount address",
                        }
                    },
                    "required": ["subaccount_addr"],
                },
            },
        },
    ]
```

### LLM Agent Loop

```python
async def llm_agent_loop(client: DecibelClient, llm):
    """Main loop for an LLM-powered trading agent."""
    tools = get_sdk_tools()

    while True:
        # Gather context
        positions = await client.get_positions(subaccount)
        prices = await client.get_prices()
        overview = await client.get_account_overview(subaccount)

        context = {
            "positions": [p.model_dump() for p in positions],
            "prices": [p.model_dump() for p in prices],
            "overview": overview.model_dump(),
        }

        # Ask LLM for decision
        decision = await llm.chat(
            messages=[
                {"role": "system", "content": "You are a trading agent..."},
                {"role": "user", "content": f"Current state: {context}"},
            ],
            tools=tools,
        )

        # Execute tool calls
        for tool_call in decision.tool_calls:
            result = await execute_tool(client, tool_call)
            # Feed result back to LLM for next decision

        await asyncio.sleep(60)
```

---

## Anti-Patterns

### 1. Polling Instead of Subscribing

**Bad**: Polling REST API every second for price updates.

```python
# DON'T DO THIS
while True:
    prices = await client.get_prices()
    process(prices)
    await asyncio.sleep(1)
```

**Good**: Subscribe to WebSocket for real-time updates.

```python
# DO THIS
await client.subscribe_market_price("BTC-USD", callback=process)
```

### 2. Ignoring Error Categories

**Bad**: Catching all errors the same way.

```python
# DON'T DO THIS
try:
    await client.place_order(...)
except Exception:
    retry()
```

**Good**: Handle errors by category.

```python
# DO THIS
try:
    await client.place_order(...)
except RateLimitError as e:
    await asyncio.sleep(e.retry_after_ms / 1000)
    await client.place_order(...)
except VmError:
    log_and_escalate()
except NetworkError:
    retry_with_backoff()
```

### 3. Not Caching Market Config

**Bad**: Fetching market config for every order.

```python
# DON'T DO THIS
for signal in signals:
    market = await client.get_market(signal.market)  # repeated fetch
    await client.place_order(market_name=signal.market, ...)
```

**Good**: The SDK caches internally — just use `place_order` with human-readable values.

```python
# DO THIS — SDK handles market config lookup and caching
for signal in signals:
    await client.place_order(
        market_name=signal.market,
        price=signal.price,
        size=signal.size,
        ...
    )
```

### 4. Blocking the WebSocket Callback

**Bad**: Doing heavy computation in the WebSocket callback.

```python
# DON'T DO THIS
async def on_price(price: MarketPrice):
    result = expensive_ml_inference(price)  # blocks the WS read loop
    await client.place_order(...)
```

**Good**: Offload to a separate task.

```python
# DO THIS
async def on_price(price: MarketPrice):
    asyncio.create_task(process_price(price))

async def process_price(price: MarketPrice):
    result = expensive_ml_inference(price)
    await client.place_order(...)
```
