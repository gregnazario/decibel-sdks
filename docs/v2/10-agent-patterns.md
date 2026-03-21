# Agentic Trading Patterns

**Parent**: [00-overview.md](./00-overview.md)

---

## Overview

This document provides complete architectures for autonomous trading agents built on the Decibel v2 SDK. Each pattern is a production-ready blueprint — not a tutorial but a specification for how a real bot should work, including the failure modes and edge cases that determine whether a strategy makes or loses money.

---

## Pattern 1: Market Making Agent

A market making bot provides liquidity by continuously quoting bid/ask prices on both sides of the orderbook. It earns the spread on each round-trip (buy on bid, sell on ask) and earns maker rebates. It loses money to adverse selection (informed traders picking off stale quotes) and inventory risk (accumulating one-sided exposure).

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Market Making Agent                          │
│                                                                     │
│  ┌──────────────────┐      ┌─────────────────────────────────────┐ │
│  │ WS Price Stream   │─────→│        Quote Engine                 │ │
│  │ WS Depth Stream   │      │                                     │ │
│  │ WS Fill Stream    │      │  mid_price = compute_mid(book)      │ │
│  └──────────────────┘      │  skew = inventory_skew(position)    │ │
│                             │  spread = base_spread + vol_adjust  │ │
│  ┌──────────────────┐      │  bid = mid - spread/2 - skew        │ │
│  │ Inventory Manager │←────│  ask = mid + spread/2 - skew        │ │
│  │                   │      │  sizes = compute_sizes(risk_limits) │ │
│  │  position_size    │      └──────────────┬──────────────────────┘ │
│  │  entry_vwap       │                     │                        │
│  │  unrealized_pnl   │      ┌──────────────▼──────────────────────┐ │
│  │  realized_pnl     │      │       Bulk Order Submitter          │ │
│  │  funding_accrued  │      │                                     │ │
│  └──────────────────┘      │  place_bulk_order(bid_levels)       │ │
│                             │  place_bulk_order(ask_levels)       │ │
│  ┌──────────────────┐      └──────────────────────────────────────┘ │
│  │ Risk Monitor      │                                              │
│  │                   │  Limits:                                      │
│  │  max_position     │  - max_position: 1.0 BTC                    │
│  │  max_drawdown     │  - max_drawdown: $5,000                     │
│  │  max_spread       │  - max_spread: 50bps (pull quotes beyond)   │
│  │  funding_rate_cap │  - funding_rate_cap: 20bps/hr (bias skew)   │
│  └──────────────────┘                                              │
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ PnL Tracker       │  Tracks: realized, unrealized, fees, gas,   │
│  │                   │          funding costs, net PnL              │
│  └──────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Quote Computation

```python
class QuoteEngine:
    def __init__(self, config: MarketMakerConfig):
        self.base_spread_bps = config.base_spread_bps  # e.g., 3.0 bps
        self.skew_factor = config.skew_factor            # e.g., 0.5 bps per unit
        self.max_position = config.max_position          # e.g., 1.0 BTC
        self.num_levels = config.num_levels              # e.g., 10
        self.level_spacing_bps = config.level_spacing_bps  # e.g., 1.0 bps between levels
        self.level_size_decay = config.level_size_decay    # e.g., 0.8 (each level 80% of previous)

    def compute_quotes(
        self,
        mid_price: float,
        current_position: float,
        volatility_bps: float,
        funding_rate_bps: float,
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        """Compute bid and ask levels.

        Returns (bid_levels, ask_levels) where each level is (price, size).
        """
        # Spread widens with volatility
        vol_adjusted_spread = self.base_spread_bps + volatility_bps * 0.5

        # Inventory skew: if long, widen ask (sell more aggressively), tighten bid
        inventory_ratio = current_position / self.max_position  # -1.0 to 1.0
        skew = self.skew_factor * inventory_ratio * 10  # in bps

        # Funding bias: if paying funding (long + positive rate), skew to reduce position
        if (current_position > 0 and funding_rate_bps > 0) or \
           (current_position < 0 and funding_rate_bps < 0):
            skew += abs(funding_rate_bps) * 0.1

        half_spread = vol_adjusted_spread / 2.0

        bid_levels = []
        ask_levels = []
        base_size = self._compute_base_size(current_position)

        for i in range(self.num_levels):
            offset_bps = half_spread + i * self.level_spacing_bps
            level_size = base_size * (self.level_size_decay ** i)

            bid_price = mid_price * (1 - (offset_bps + skew) / 10_000)
            ask_price = mid_price * (1 + (offset_bps - skew) / 10_000)

            bid_levels.append((bid_price, level_size))
            ask_levels.append((ask_price, level_size))

        return bid_levels, ask_levels

    def _compute_base_size(self, current_position: float) -> float:
        remaining_capacity = self.max_position - abs(current_position)
        return max(0.001, min(0.01, remaining_capacity / self.num_levels))
```

### Inventory Management

```python
class InventoryManager:
    def __init__(self, max_position: float, max_drawdown: float):
        self.max_position = max_position
        self.max_drawdown = max_drawdown
        self.position_size = 0.0
        self.entry_vwap = 0.0
        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.total_funding = 0.0
        self.total_gas_cost = 0.0
        self.high_water_mark = 0.0

    def on_fill(self, side: str, fill_size: float, fill_price: float, fee: float):
        """Update inventory state from a fill event."""
        signed_size = fill_size if side == "buy" else -fill_size
        old_position = self.position_size
        new_position = old_position + signed_size

        if old_position * new_position < 0:
            # Position flipped — realize PnL on the closed portion
            closed_size = min(abs(old_position), abs(signed_size))
            if old_position > 0:
                self.realized_pnl += closed_size * (fill_price - self.entry_vwap)
            else:
                self.realized_pnl += closed_size * (self.entry_vwap - fill_price)
            self.entry_vwap = fill_price
        elif abs(new_position) > abs(old_position):
            # Adding to position — update VWAP
            old_notional = abs(old_position) * self.entry_vwap
            new_notional = fill_size * fill_price
            self.entry_vwap = (old_notional + new_notional) / abs(new_position)
        elif abs(new_position) < abs(old_position):
            # Reducing position — realize PnL
            if old_position > 0:
                self.realized_pnl += fill_size * (fill_price - self.entry_vwap)
            else:
                self.realized_pnl += fill_size * (self.entry_vwap - fill_price)

        self.position_size = new_position
        self.total_fees += fee

    def unrealized_pnl(self, mark_price: float) -> float:
        if self.position_size == 0:
            return 0.0
        if self.position_size > 0:
            return self.position_size * (mark_price - self.entry_vwap)
        return abs(self.position_size) * (self.entry_vwap - mark_price)

    def net_pnl(self, mark_price: float) -> float:
        return (
            self.realized_pnl
            + self.unrealized_pnl(mark_price)
            - self.total_fees
            - self.total_gas_cost
            + self.total_funding  # positive if receiving funding
        )

    @property
    def should_reduce_position(self) -> bool:
        return abs(self.position_size) > self.max_position * 0.8

    @property
    def position_utilization(self) -> float:
        return abs(self.position_size) / self.max_position if self.max_position > 0 else 0.0
```

### Fill Handling with Bulk Orders

```python
class MarketMaker:
    async def run(self):
        async with self.client:
            await self._subscribe_all()
            try:
                await asyncio.Event().wait()
            finally:
                await self._cancel_all_quotes()

    async def _subscribe_all(self):
        await self.client.subscribe_market_price(
            self.market, callback=self._on_price_update
        )
        await self.client.subscribe_depth(
            self.market, aggregation_level=1, callback=self._on_depth
        )
        await self.client.subscribe_bulk_order_fills(
            self.subaccount, callback=self._on_bulk_fill
        )
        await self.client.subscribe_order_updates(
            self.subaccount, callback=self._on_order_update
        )
        await self.client.subscribe_positions(
            self.subaccount, callback=self._on_position_update
        )

    async def _on_price_update(self, price: MarketPrice):
        """Non-blocking: queue a requote instead of trading in the callback."""
        self._latest_price = price
        asyncio.create_task(self._maybe_requote())

    async def _maybe_requote(self):
        if self._requote_lock.locked():
            return  # already requoting
        async with self._requote_lock:
            bid_levels, ask_levels = self.quote_engine.compute_quotes(
                mid_price=self._latest_price.mark_px,
                current_position=self.inventory.position_size,
                volatility_bps=self._estimate_volatility(),
                funding_rate_bps=self._latest_price.funding_rate_bps,
            )

            # Submit both sides in parallel using bulk orders
            await asyncio.gather(
                self.client.place_bulk_order(
                    market_name=self.market,
                    levels=bid_levels,
                    is_buy=True,
                    subaccount_addr=self.subaccount,
                ),
                self.client.place_bulk_order(
                    market_name=self.market,
                    levels=ask_levels,
                    is_buy=False,
                    subaccount_addr=self.subaccount,
                ),
            )

    async def _on_bulk_fill(self, update: BulkOrderFillsUpdate):
        """Process bulk order fills and update inventory."""
        for fill in update.fills:
            self.inventory.on_fill(
                side="buy" if fill.is_buy else "sell",
                fill_size=fill.size,
                fill_price=fill.price,
                fee=fill.fee,
            )

        # If inventory is approaching limits, requote with tighter skew
        if self.inventory.should_reduce_position:
            asyncio.create_task(self._maybe_requote())
```

---

## Pattern 2: Funding Rate Arbitrage Agent

Funding rate arbitrage exploits the funding payments between long and short positions. When the funding rate is positive, shorts receive funding from longs. When negative, longs receive from shorts. The strategy holds a position that receives funding while hedging directional risk either on another venue or by accepting the exposure with tight stop-losses.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Funding Rate Arbitrage Agent                       │
│                                                                     │
│  ┌──────────────────┐     ┌──────────────────────────────────────┐ │
│  │ WS Price Stream   │────→│       Funding Rate Monitor           │ │
│  │ (all markets)     │     │                                      │ │
│  └──────────────────┘     │  For each market:                    │ │
│                            │    funding_rate_bps/hr               │ │
│                            │    annualized = rate × 8760          │ │
│                            │    net_of_fees = annualized - fees   │ │
│                            │    score = net_of_fees / volatility  │ │
│                            └─────────────┬────────────────────────┘ │
│                                          │                          │
│                             ┌────────────▼────────────────────────┐ │
│                             │      Entry/Exit Decision Engine     │ │
│                             │                                      │ │
│                             │  ENTER when:                        │ │
│                             │    - net_annualized > 30%           │ │
│                             │    - rate has been stable > 1hr     │ │
│                             │    - spread cost < 2hr funding      │ │
│                             │                                      │ │
│                             │  EXIT when:                         │ │
│                             │    - net_annualized < 5%            │ │
│                             │    - rate flipped sign              │ │
│                             │    - position PnL < -max_loss       │ │
│                             └─────────────┬──────────────────────┘ │
│                                           │                         │
│                             ┌─────────────▼──────────────────────┐ │
│                             │      Position Manager               │ │
│                             │                                      │ │
│                             │  - Track funding accrual per hour   │ │
│                             │  - Set stop-loss at entry ± X%      │ │
│                             │  - Monitor liquidation distance     │ │
│                             └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class FundingRateArbitrage:
    def __init__(
        self,
        client: DecibelClient,
        subaccount: str,
        markets: list[str],
        min_annualized_rate: float = 0.30,  # 30% annualized minimum to enter
        exit_annualized_rate: float = 0.05,  # 5% annualized — exit threshold
        max_position_usd: float = 50_000,
        max_loss_per_trade_usd: float = 500,
    ):
        self.client = client
        self.subaccount = subaccount
        self.markets = markets
        self.min_annualized = min_annualized_rate
        self.exit_annualized = exit_annualized_rate
        self.max_position_usd = max_position_usd
        self.max_loss_usd = max_loss_per_trade_usd
        self.active_positions: dict[str, FundingPosition] = {}
        self.rate_history: dict[str, list[tuple[int, float]]] = {}

    async def run(self):
        async with self.client:
            # Subscribe to all market prices for funding rate monitoring
            for market in self.markets:
                await self.client.subscribe_market_price(
                    market, callback=self._on_price
                )
            await self.client.subscribe_positions(
                self.subaccount, callback=self._on_position_update
            )

            # Main evaluation loop
            while True:
                await self._evaluate_opportunities()
                await self._monitor_active_positions()
                await asyncio.sleep(60)

    async def _on_price(self, price: MarketPrice):
        market = price.market
        if market not in self.rate_history:
            self.rate_history[market] = []
        self.rate_history[market].append((price.timestamp_ms, price.funding_rate_bps))
        # Keep last 24h of history
        cutoff = price.timestamp_ms - 86_400_000
        self.rate_history[market] = [
            (ts, r) for ts, r in self.rate_history[market] if ts > cutoff
        ]

    async def _evaluate_opportunities(self):
        for market in self.markets:
            if market in self.active_positions:
                continue

            history = self.rate_history.get(market, [])
            if len(history) < 60:  # need at least 1 hour of data
                continue

            current_rate = history[-1][1]
            avg_rate_1h = sum(r for _, r in history[-60:]) / 60

            # Annualize: rate is bps/hr, so × 8760 hours/year
            annualized = abs(avg_rate_1h) * 8760 / 10_000  # as a fraction

            # Entry cost: taker fee to enter + taker fee to exit
            entry_cost_bps = 3.4 * 2  # worst case taker fee both ways
            # Hours of funding to recoup entry cost
            hours_to_breakeven = entry_cost_bps / abs(avg_rate_1h) if avg_rate_1h != 0 else float('inf')

            # Rate stability: standard deviation over last hour
            rates_1h = [r for _, r in history[-60:]]
            rate_std = (sum((r - avg_rate_1h) ** 2 for r in rates_1h) / len(rates_1h)) ** 0.5

            if (annualized > self.min_annualized
                and hours_to_breakeven < 6
                and rate_std < abs(avg_rate_1h) * 0.5):  # rate is stable

                await self._enter_funding_trade(market, current_rate)

    async def _enter_funding_trade(self, market: str, funding_rate_bps: float):
        """Enter a position to collect funding."""
        prices = await self.client.get_price(market)
        mark = prices[0].mark_px

        # If funding rate is positive: shorts receive → go short
        # If funding rate is negative: longs receive → go long
        is_buy = funding_rate_bps < 0
        position_size = self.max_position_usd / mark

        # Use IOC with slippage tolerance
        limit_price = mark * (1.001 if is_buy else 0.999)

        result = await self.client.place_order(
            market_name=market,
            price=limit_price,
            size=position_size,
            is_buy=is_buy,
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=False,
            client_order_id=f"funding-{market}-{int(time.time())}",
        )

        if result.success:
            # Set stop-loss to cap downside
            sl_distance = self.max_loss_usd / (position_size * mark) * mark
            sl_price = (mark - sl_distance) if is_buy else (mark + sl_distance)

            await self.client.place_tp_sl(
                market_addr=result.market_addr,
                sl_trigger_price=sl_price,
                sl_limit_price=sl_price * (0.995 if is_buy else 1.005),
                subaccount_addr=self.subaccount,
            )

            self.active_positions[market] = FundingPosition(
                market=market,
                entry_price=mark,
                size=position_size if is_buy else -position_size,
                entry_time=time.time(),
                funding_collected=0.0,
                entry_funding_rate=funding_rate_bps,
            )

    async def _monitor_active_positions(self):
        """Check if any active positions should be closed."""
        for market, pos in list(self.active_positions.items()):
            history = self.rate_history.get(market, [])
            if not history:
                continue

            current_rate = history[-1][1]
            annualized = abs(current_rate) * 8760 / 10_000

            should_exit = False
            reason = ""

            # Rate dropped below exit threshold
            if annualized < self.exit_annualized:
                should_exit = True
                reason = f"rate dropped to {annualized:.1%} annualized"

            # Rate flipped sign (we're now paying instead of receiving)
            if (pos.size > 0 and current_rate > 0) or (pos.size < 0 and current_rate < 0):
                should_exit = True
                reason = f"rate flipped — now paying funding"

            # Position has been held long enough to capture meaningful funding
            hours_held = (time.time() - pos.entry_time) / 3600
            if hours_held > 168:  # 1 week max hold
                should_exit = True
                reason = "max hold time reached"

            if should_exit:
                await self._close_position(market, reason)

    async def _close_position(self, market: str, reason: str):
        pos = self.active_positions.pop(market, None)
        if not pos:
            return

        prices = await self.client.get_price(market)
        mark = prices[0].mark_px
        is_buy = pos.size < 0  # close by taking opposite side

        await self.client.place_order(
            market_name=market,
            price=mark * (1.001 if is_buy else 0.999),
            size=abs(pos.size),
            is_buy=is_buy,
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=True,
            client_order_id=f"funding-exit-{market}-{int(time.time())}",
        )


@dataclass
class FundingPosition:
    market: str
    entry_price: float
    size: float
    entry_time: float
    funding_collected: float
    entry_funding_rate: float
```

### Funding Cost Accounting

Decibel's continuous funding accrues every oracle update (~1 second). Over a 24h period at 10bps/hr:

```
Hourly cost:    10 bps × position_notional = 0.10% per hour
Daily cost:     24 × 0.10% = 2.4% per day
Annual cost:    8,760 × 0.10% = 876% annualized

On a $50,000 position at 10bps/hr:
  Hourly: $50 per hour
  Daily:  $1,200 per day
```

Bots **must** track funding accrual. Use `GET /funding_rate_history` for historical reconciliation and the `accrued_funding` field on position updates for real-time tracking.

---

## Pattern 3: Multi-Leg Strategy Agent

A multi-leg agent manages simultaneous positions across multiple markets. Examples include spread trading (long one asset, short a correlated one), basis trading (long spot + short perp), and statistical arbitrage across related assets.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Multi-Leg Strategy Agent                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Spread Monitor                             │   │
│  │                                                               │   │
│  │  z_score = (spread - mean) / std_dev                         │   │
│  │  spread = price_A / price_B - hedge_ratio                    │   │
│  │                                                               │   │
│  │  Signal:                                                      │   │
│  │    z > +2.0 → spread too wide → short A, long B              │   │
│  │    z < -2.0 → spread too tight → long A, short B             │   │
│  │    |z| < 0.5 → mean reversion complete → close both          │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │                   Execution Engine                            │   │
│  │                                                               │   │
│  │  Atomic entry: place both legs simultaneously via gather()   │   │
│  │  If one leg fails: immediately unwind the other              │   │
│  │  Delta hedge: rebalance when net delta exceeds threshold     │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │                   Delta Hedger                                │   │
│  │                                                               │   │
│  │  net_delta = sum(position_i × beta_i) for all legs           │   │
│  │  if |net_delta| > threshold: hedge with market order          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class MultiLegStrategy:
    def __init__(
        self,
        client: DecibelClient,
        subaccount: str,
        leg_a: str,  # e.g., "BTC-USD"
        leg_b: str,  # e.g., "ETH-USD"
        hedge_ratio: float,  # e.g., 14.0 (1 BTC ≈ 14 ETH in notional)
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        lookback_periods: int = 200,
        max_notional_per_leg: float = 25_000,
        max_net_delta_usd: float = 2_000,
    ):
        self.client = client
        self.subaccount = subaccount
        self.leg_a = leg_a
        self.leg_b = leg_b
        self.hedge_ratio = hedge_ratio
        self.z_entry = z_score_entry
        self.z_exit = z_score_exit
        self.lookback = lookback_periods
        self.max_notional = max_notional_per_leg
        self.max_net_delta = max_net_delta_usd

        self.spread_history: list[float] = []
        self.prices: dict[str, float] = {}
        self.positions: dict[str, float] = {}  # market → signed size
        self.is_in_trade = False
        self.trade_direction: str | None = None  # "long_spread" or "short_spread"

    async def run(self):
        async with self.client:
            await self.client.subscribe_market_price(self.leg_a, callback=self._on_price)
            await self.client.subscribe_market_price(self.leg_b, callback=self._on_price)
            await self.client.subscribe_positions(
                self.subaccount, callback=self._on_position_update
            )

            while True:
                await asyncio.sleep(1)  # evaluate every second
                if len(self.prices) == 2:
                    await self._evaluate()

    async def _on_price(self, price: MarketPrice):
        self.prices[price.market] = price.mark_px

        if len(self.prices) == 2:
            spread = self.prices[self.leg_a] / self.prices[self.leg_b] - self.hedge_ratio
            self.spread_history.append(spread)
            if len(self.spread_history) > self.lookback * 2:
                self.spread_history = self.spread_history[-self.lookback * 2:]

    async def _evaluate(self):
        if len(self.spread_history) < self.lookback:
            return

        recent = self.spread_history[-self.lookback:]
        mean = sum(recent) / len(recent)
        std = (sum((x - mean) ** 2 for x in recent) / len(recent)) ** 0.5
        if std == 0:
            return

        current_spread = self.spread_history[-1]
        z_score = (current_spread - mean) / std

        if not self.is_in_trade:
            if z_score > self.z_entry:
                await self._enter_spread_trade("short_spread", z_score)
            elif z_score < -self.z_entry:
                await self._enter_spread_trade("long_spread", z_score)
        else:
            if abs(z_score) < self.z_exit:
                await self._exit_spread_trade(z_score)

            # Check delta and hedge if needed
            await self._check_delta_hedge()

    async def _enter_spread_trade(self, direction: str, z_score: float):
        price_a = self.prices[self.leg_a]
        price_b = self.prices[self.leg_b]
        size_a = self.max_notional / price_a
        size_b = self.max_notional / price_b

        if direction == "short_spread":
            # Spread too wide: short A, long B
            a_side, b_side = False, True
        else:
            # Spread too narrow: long A, short B
            a_side, b_side = True, False

        # Execute both legs simultaneously
        result_a, result_b = await asyncio.gather(
            self.client.place_order(
                market_name=self.leg_a,
                price=price_a * (1.001 if a_side else 0.999),
                size=size_a,
                is_buy=a_side,
                time_in_force=TimeInForce.ImmediateOrCancel,
                client_order_id=f"spread-{direction}-A-{int(time.time())}",
            ),
            self.client.place_order(
                market_name=self.leg_b,
                price=price_b * (1.001 if b_side else 0.999),
                size=size_b,
                is_buy=b_side,
                time_in_force=TimeInForce.ImmediateOrCancel,
                client_order_id=f"spread-{direction}-B-{int(time.time())}",
            ),
            return_exceptions=True,
        )

        a_ok = not isinstance(result_a, Exception) and result_a.success
        b_ok = not isinstance(result_b, Exception) and result_b.success

        if a_ok and b_ok:
            self.is_in_trade = True
            self.trade_direction = direction
        elif a_ok and not b_ok:
            # Unwind leg A immediately
            await self.client.place_order(
                market_name=self.leg_a,
                price=price_a * (0.999 if a_side else 1.001),
                size=size_a,
                is_buy=not a_side,
                time_in_force=TimeInForce.ImmediateOrCancel,
                is_reduce_only=True,
            )
        elif b_ok and not a_ok:
            await self.client.place_order(
                market_name=self.leg_b,
                price=price_b * (0.999 if b_side else 1.001),
                size=size_b,
                is_buy=not b_side,
                time_in_force=TimeInForce.ImmediateOrCancel,
                is_reduce_only=True,
            )

    async def _check_delta_hedge(self):
        """Ensure net dollar delta stays within bounds."""
        pos_a = self.positions.get(self.leg_a, 0.0)
        pos_b = self.positions.get(self.leg_b, 0.0)
        price_a = self.prices.get(self.leg_a, 0.0)
        price_b = self.prices.get(self.leg_b, 0.0)

        delta_a = pos_a * price_a
        delta_b = pos_b * price_b
        net_delta = delta_a + delta_b

        if abs(net_delta) > self.max_net_delta:
            # Hedge by adjusting the smaller leg
            hedge_notional = net_delta  # positive = too long, sell to hedge
            hedge_market = self.leg_b  # hedge on the more liquid leg
            hedge_price = price_b
            hedge_size = abs(hedge_notional) / hedge_price
            hedge_is_buy = hedge_notional < 0

            await self.client.place_order(
                market_name=hedge_market,
                price=hedge_price * (1.001 if hedge_is_buy else 0.999),
                size=hedge_size,
                is_buy=hedge_is_buy,
                time_in_force=TimeInForce.ImmediateOrCancel,
                client_order_id=f"delta-hedge-{int(time.time())}",
            )

    async def _exit_spread_trade(self, z_score: float):
        """Close both legs of the spread."""
        tasks = []
        for market in [self.leg_a, self.leg_b]:
            pos = self.positions.get(market, 0.0)
            if pos == 0:
                continue
            price = self.prices.get(market, 0.0)
            is_buy = pos < 0  # close by taking opposite side
            tasks.append(
                self.client.place_order(
                    market_name=market,
                    price=price * (1.001 if is_buy else 0.999),
                    size=abs(pos),
                    is_buy=is_buy,
                    time_in_force=TimeInForce.ImmediateOrCancel,
                    is_reduce_only=True,
                    client_order_id=f"spread-exit-{market}-{int(time.time())}",
                )
            )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.is_in_trade = False
        self.trade_direction = None

    async def _on_position_update(self, update):
        for position in update.positions:
            self.positions[position.market] = position.size
```

---

## Pattern 4: LLM-Powered Trading Agent

An LLM-powered trading agent uses a language model as its decision engine. The SDK provides tools (functions) that the LLM can call, and the agent loop feeds market context to the LLM at each step.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LLM Trading Agent                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   Context Builder                             │   │
│  │                                                               │   │
│  │  Assembles a structured snapshot for the LLM:                │   │
│  │    - Current positions (market, size, PnL, liq distance)     │   │
│  │    - Open orders (market, price, size, age)                  │   │
│  │    - Account overview (equity, margin usage, fee tier)       │   │
│  │    - Recent price action (last 5 candle closes)              │   │
│  │    - Funding rates (current + 24h average)                   │   │
│  │    - Recent trades (last 5 fills with PnL)                   │   │
│  │    - Risk metrics (max drawdown, Sharpe, exposure %)         │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │                   LLM Decision Engine                         │   │
│  │                                                               │   │
│  │  System prompt: trading rules, risk limits, strategy goals   │   │
│  │  User message: structured context snapshot                    │   │
│  │  Available tools: SDK functions as tool definitions           │   │
│  │                                                               │   │
│  │  LLM outputs: tool calls (place_order, cancel, etc.)         │   │
│  │             or "no action" with reasoning                     │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │                   Tool Executor                               │   │
│  │                                                               │   │
│  │  Validates LLM tool calls against risk limits before exec    │   │
│  │  Executes validated calls against the SDK                     │   │
│  │  Returns structured results to the LLM for reflection        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### What Context to Provide

The context window is the LLM's entire view of the trading world. Too little context and it makes uninformed decisions. Too much and it gets confused or hits token limits.

```python
async def build_trading_context(
    client: DecibelClient,
    subaccount: str,
    active_markets: list[str],
) -> dict:
    """Build a structured context snapshot for the LLM."""

    positions = await client.get_positions(account=subaccount)
    open_orders = await client.get_open_orders(account=subaccount)
    overview = await client.get_account_overview(account=subaccount)

    prices = {}
    for market in active_markets:
        price_data = await client.get_price(market)
        if price_data:
            prices[market] = {
                "mark_price": price_data[0].mark_px,
                "index_price": price_data[0].index_px,
                "best_bid": price_data[0].best_bid,
                "best_ask": price_data[0].best_ask,
                "funding_rate_bps_per_hr": price_data[0].funding_rate_bps,
                "funding_annualized_pct": price_data[0].funding_rate_bps * 8760 / 100,
            }

    return {
        "account": {
            "equity_usd": overview.account_equity,
            "available_margin_usd": overview.available_margin,
            "margin_usage_pct": overview.cross_margin_usage * 100,
            "fee_tier": overview.fee_tier,
            "unrealized_pnl": overview.unrealized_pnl,
        },
        "positions": [
            {
                "market": p.market,
                "side": "long" if p.size > 0 else "short",
                "size": abs(p.size),
                "entry_price": p.entry_price,
                "mark_price": prices.get(p.market, {}).get("mark_price"),
                "unrealized_pnl": p.unrealized_pnl,
                "liquidation_price": p.liquidation_price,
                "margin_used": p.margin_used,
                "accrued_funding": p.accrued_funding,
            }
            for p in positions if p.size != 0
        ],
        "open_orders": [
            {
                "market": o.market,
                "side": o.side,
                "price": o.price,
                "size": o.size,
                "order_type": o.order_type,
                "client_order_id": o.client_order_id,
            }
            for o in open_orders
        ],
        "market_data": prices,
        "risk_summary": {
            "total_exposure_usd": sum(
                abs(p.size) * prices.get(p.market, {}).get("mark_price", 0)
                for p in positions if p.size != 0
            ),
            "position_count": sum(1 for p in positions if p.size != 0),
            "order_count": len(open_orders),
        },
    }
```

### What Tools to Expose

Keep the tool set minimal. An LLM with 50 tools performs worse than one with 8 well-defined tools.

```python
TRADING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "place_limit_order",
            "description": "Place a limit order. Use IOC for immediate execution, GTC for resting orders, PostOnly for maker-only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "market": {"type": "string", "description": "Market name, e.g. 'BTC-USD'"},
                    "side": {"type": "string", "enum": ["buy", "sell"]},
                    "price": {"type": "number", "description": "Limit price in USD"},
                    "size": {"type": "number", "description": "Order size in base asset units"},
                    "time_in_force": {"type": "string", "enum": ["IOC", "GTC", "PostOnly"]},
                    "reduce_only": {"type": "boolean", "description": "If true, can only reduce existing position"},
                },
                "required": ["market", "side", "price", "size", "time_in_force"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "Cancel a specific open order by its client_order_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_order_id": {"type": "string"},
                },
                "required": ["client_order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_all_orders",
            "description": "Cancel all open orders. Use when you want to reset all resting orders.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_position",
            "description": "Close an entire position in a market using an IOC order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "market": {"type": "string", "description": "Market to close position in"},
                },
                "required": ["market"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_stop_loss",
            "description": "Set a stop-loss on an existing position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "market": {"type": "string"},
                    "trigger_price": {"type": "number", "description": "Price at which the SL triggers"},
                },
                "required": ["market", "trigger_price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orderbook",
            "description": "Get current orderbook depth for a market. Returns top 10 bids and asks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "market": {"type": "string"},
                },
                "required": ["market"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_candles",
            "description": "Get recent OHLCV candles for technical analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "market": {"type": "string"},
                    "interval": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"]},
                    "count": {"type": "integer", "description": "Number of candles (max 200)"},
                },
                "required": ["market", "interval", "count"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "no_action",
            "description": "Explicitly choose to take no action this cycle. Provide reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                },
                "required": ["reasoning"],
            },
        },
    },
]
```

### Decision Loop Architecture

```python
class LLMTradingAgent:
    def __init__(
        self,
        client: DecibelClient,
        llm_client,  # OpenAI / Anthropic client
        subaccount: str,
        markets: list[str],
        system_prompt: str,
        decision_interval_s: int = 60,
        max_tool_calls_per_cycle: int = 5,
    ):
        self.client = client
        self.llm = llm_client
        self.subaccount = subaccount
        self.markets = markets
        self.system_prompt = system_prompt
        self.interval = decision_interval_s
        self.max_calls = max_tool_calls_per_cycle
        self.decision_log: list[dict] = []

    async def run(self):
        async with self.client:
            while True:
                try:
                    await self._decision_cycle()
                except Exception as e:
                    structured_log = {
                        "event": "decision_cycle_error",
                        "error": str(e),
                        "timestamp_ms": int(time.time() * 1000),
                    }
                    logger.error(json.dumps(structured_log))

                await asyncio.sleep(self.interval)

    async def _decision_cycle(self):
        # 1. Build context
        context = await build_trading_context(self.client, self.subaccount, self.markets)

        # 2. Ask LLM for decision
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2)},
        ]

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TRADING_TOOLS,
            tool_choice="auto",
        )

        # 3. Execute tool calls with risk validation
        tool_calls_executed = 0
        for tool_call in response.choices[0].message.tool_calls or []:
            if tool_calls_executed >= self.max_calls:
                break

            args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name

            # Risk gate: validate before execution
            validation = self._validate_tool_call(tool_name, args, context)
            if not validation["allowed"]:
                self.decision_log.append({
                    "action": "blocked",
                    "tool": tool_name,
                    "args": args,
                    "reason": validation["reason"],
                })
                continue

            result = await self._execute_tool(tool_name, args)
            self.decision_log.append({
                "action": "executed",
                "tool": tool_name,
                "args": args,
                "result": result,
                "timestamp_ms": int(time.time() * 1000),
            })
            tool_calls_executed += 1

    def _validate_tool_call(self, tool_name: str, args: dict, context: dict) -> dict:
        """Pre-execution risk validation. The LLM cannot bypass these limits."""

        if tool_name == "place_limit_order":
            # Check position limits
            market = args["market"]
            size = args["size"]
            price = args.get("price", 0)
            notional = size * price

            current_exposure = context["risk_summary"]["total_exposure_usd"]
            if current_exposure + notional > context["account"]["equity_usd"] * 3:
                return {"allowed": False, "reason": "Would exceed 3x leverage limit"}

            if notional > context["account"]["equity_usd"] * 0.5:
                return {"allowed": False, "reason": "Single order > 50% of equity"}

        if tool_name in ("place_limit_order", "close_position"):
            if context["account"]["margin_usage_pct"] > 80:
                reduce_only = args.get("reduce_only", False)
                if not reduce_only and tool_name == "place_limit_order":
                    return {"allowed": False, "reason": "Margin usage > 80%, only reduce-only allowed"}

        return {"allowed": True, "reason": ""}

    async def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a validated tool call against the SDK."""
        TIF_MAP = {"IOC": TimeInForce.ImmediateOrCancel, "GTC": TimeInForce.GoodTillCanceled, "PostOnly": TimeInForce.PostOnly}

        try:
            if tool_name == "place_limit_order":
                result = await self.client.place_order(
                    market_name=args["market"],
                    price=args["price"],
                    size=args["size"],
                    is_buy=(args["side"] == "buy"),
                    time_in_force=TIF_MAP[args["time_in_force"]],
                    is_reduce_only=args.get("reduce_only", False),
                    client_order_id=f"llm-{int(time.time())}",
                )
                return {"success": result.success, "order_id": result.order_id}

            elif tool_name == "cancel_order":
                result = await self.client.cancel_client_order(
                    client_order_id=args["client_order_id"],
                )
                return {"success": True}

            elif tool_name == "cancel_all_orders":
                orders = await self.client.get_open_orders(account=self.subaccount)
                for order in orders:
                    await self.client.cancel_order(order_id=order.order_id, market_name=order.market)
                return {"cancelled": len(orders)}

            elif tool_name == "close_position":
                positions = await self.client.get_positions(account=self.subaccount)
                pos = next((p for p in positions if p.market == args["market"] and p.size != 0), None)
                if not pos:
                    return {"success": False, "reason": "No position in this market"}
                prices = await self.client.get_price(args["market"])
                mark = prices[0].mark_px
                result = await self.client.place_order(
                    market_name=args["market"],
                    price=mark * (1.002 if pos.size < 0 else 0.998),
                    size=abs(pos.size),
                    is_buy=(pos.size < 0),
                    time_in_force=TimeInForce.ImmediateOrCancel,
                    is_reduce_only=True,
                )
                return {"success": result.success}

            elif tool_name == "set_stop_loss":
                return await self._set_stop_loss(args["market"], args["trigger_price"])

            elif tool_name == "get_orderbook":
                depth = await self.client.get_depth(args["market"], limit=10)
                return {
                    "bids": [(l.price, l.size) for l in depth.bids[:10]],
                    "asks": [(l.price, l.size) for l in depth.asks[:10]],
                }

            elif tool_name == "get_recent_candles":
                now = int(time.time() * 1000)
                interval_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}
                count = min(args.get("count", 50), 200)
                start = now - interval_ms[args["interval"]] * count
                candles = await self.client.get_candlesticks(args["market"], args["interval"], start, now)
                return [{"o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume} for c in candles[-count:]]

            elif tool_name == "no_action":
                return {"action": "none", "reasoning": args["reasoning"]}

        except DecibelError as e:
            return {"success": False, "error": e.to_dict()}
```

### System Prompt Design

```python
SYSTEM_PROMPT = """You are an autonomous trading agent managing a perpetual futures portfolio on Decibel.

RULES (non-negotiable):
1. Never risk more than 2% of equity on a single trade.
2. Always set a stop-loss within 3% of entry on any new position.
3. Maximum 3 simultaneous positions.
4. Maximum 3x total leverage.
5. Do not trade if margin usage > 70%.
6. Account for funding costs: a position paying 10bps/hr costs 2.4%/day.

STRATEGY:
- You are a momentum/mean-reversion hybrid.
- Enter on strong trends (large moves with volume), exit on mean reversion signals.
- Prefer PostOnly orders for entries (saves fees) and IOC for exits (guarantees fill).
- Size positions based on conviction: low conviction = 0.5% of equity, high = 2%.

OUTPUT:
- Use the provided tools to take actions.
- If no action is appropriate, call no_action with your reasoning.
- Think about risk/reward before every trade.
"""
```

---

## Pattern 5: Risk Watchdog

A standalone service that monitors all subaccounts and takes emergency action when risk thresholds are breached. This runs independently from the trading bots — it's the safety net that catches what the bots miss.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Risk Watchdog                                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Subaccount Monitor (per account)                 │   │
│  │                                                               │   │
│  │  WS: account_overview    → equity, margin ratio              │   │
│  │  WS: account_positions   → position sizes, PnL               │   │
│  │  WS: order_updates       → fill/cancel events                │   │
│  │  WS: all_market_prices   → mark prices for all markets       │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │              Risk Evaluation Engine                            │   │
│  │                                                               │   │
│  │  Rules (evaluated every tick):                                │   │
│  │    1. margin_usage > 85%     → CANCEL all non-reduce-only    │   │
│  │    2. margin_usage > 95%     → CLOSE all positions            │   │
│  │    3. single_position_pnl    → CLOSE if loss > $X            │   │
│  │       < -max_loss_per_pos                                     │   │
│  │    4. total_pnl < -daily_    → HALT all trading               │   │
│  │       loss_limit                                              │   │
│  │    5. WS disconnect > 60s    → CANCEL all, PAUSE trading     │   │
│  │    6. position_size >        → CANCEL new orders for market   │   │
│  │       max_allowed                                             │   │
│  │    7. no_stop_loss_on_pos    → PLACE emergency SL             │   │
│  │       for > 30s                                               │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐   │
│  │              Action Executor                                  │   │
│  │                                                               │   │
│  │  - Cancel orders (with verification)                          │   │
│  │  - Close positions (with aggressive pricing)                  │   │
│  │  - Place emergency stop-losses                                │   │
│  │  - Emit alerts (Slack, PagerDuty, email)                     │   │
│  │  - Log all actions with full context                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
@dataclass
class RiskLimits:
    max_margin_usage_pct: float = 85.0
    critical_margin_usage_pct: float = 95.0
    max_loss_per_position_usd: float = 5_000
    daily_loss_limit_usd: float = 20_000
    max_position_size: dict[str, float] = None  # market → max size
    max_total_exposure_usd: float = 500_000
    require_stop_loss_within_s: int = 30
    ws_disconnect_cancel_threshold_s: int = 60


class RiskWatchdog:
    def __init__(
        self,
        client: DecibelClient,
        subaccounts: list[str],
        limits: RiskLimits,
        alert_callback: Callable | None = None,
    ):
        self.client = client
        self.subaccounts = subaccounts
        self.limits = limits
        self.alert = alert_callback or self._default_alert
        self.state: dict[str, SubaccountState] = {}
        self.daily_pnl_start: dict[str, float] = {}
        self.action_log: list[dict] = []
        self.positions_without_sl: dict[str, float] = {}  # key → timestamp when first seen

    async def run(self):
        async with self.client:
            for account in self.subaccounts:
                self.state[account] = SubaccountState()

                await self.client.subscribe_account_overview(
                    account, callback=lambda o, a=account: self._on_overview(a, o)
                )
                await self.client.subscribe_positions(
                    account, callback=lambda p, a=account: self._on_positions(a, p)
                )
                await self.client.subscribe_order_updates(
                    account, callback=lambda u, a=account: self._on_order_update(a, u)
                )

            await self.client.subscribe_all_market_prices(
                callback=self._on_all_prices
            )

            # Periodic deep check using REST (cross-validates WS state)
            while True:
                await self._periodic_deep_check()
                await asyncio.sleep(30)

    async def _on_overview(self, account: str, overview: AccountOverview):
        self.state[account].overview = overview
        margin_pct = overview.cross_margin_usage * 100

        if margin_pct > self.limits.critical_margin_usage_pct:
            await self._action_close_all(account, f"CRITICAL margin at {margin_pct:.1f}%")
        elif margin_pct > self.limits.max_margin_usage_pct:
            await self._action_cancel_non_reduce_only(account, f"Margin at {margin_pct:.1f}%")

    async def _on_positions(self, account: str, update):
        self.state[account].positions = {p.market: p for p in update.positions}

        for pos in update.positions:
            if pos.size == 0:
                continue

            # Check per-position loss limit
            if pos.unrealized_pnl < -self.limits.max_loss_per_position_usd:
                await self._action_close_position(
                    account, pos.market,
                    f"Position loss ${abs(pos.unrealized_pnl):.0f} exceeds limit ${self.limits.max_loss_per_position_usd}"
                )

            # Check position size limits
            max_size = (self.limits.max_position_size or {}).get(pos.market)
            if max_size and abs(pos.size) > max_size:
                await self.alert({
                    "level": "WARNING",
                    "account": account,
                    "market": pos.market,
                    "message": f"Position size {abs(pos.size)} exceeds limit {max_size}",
                })

            # Track positions without stop-losses
            pos_key = f"{account}:{pos.market}"
            has_sl = pos.sl_order_id is not None if hasattr(pos, 'sl_order_id') else False
            if not has_sl:
                if pos_key not in self.positions_without_sl:
                    self.positions_without_sl[pos_key] = time.time()
                elif time.time() - self.positions_without_sl[pos_key] > self.limits.require_stop_loss_within_s:
                    await self._action_emergency_stop_loss(account, pos)
                    self.positions_without_sl.pop(pos_key, None)
            else:
                self.positions_without_sl.pop(pos_key, None)

        # Check daily PnL
        daily_key = f"{account}:{time.strftime('%Y-%m-%d')}"
        if daily_key not in self.daily_pnl_start:
            self.daily_pnl_start[daily_key] = sum(
                p.unrealized_pnl for p in update.positions
            )
        current_pnl = sum(p.unrealized_pnl for p in update.positions)
        daily_pnl = current_pnl - self.daily_pnl_start.get(daily_key, current_pnl)

        if daily_pnl < -self.limits.daily_loss_limit_usd:
            await self._action_halt_trading(
                account, f"Daily loss ${abs(daily_pnl):.0f} exceeds limit ${self.limits.daily_loss_limit_usd}"
            )

    async def _action_cancel_non_reduce_only(self, account: str, reason: str):
        """Cancel all orders that could increase exposure."""
        self._log_action("cancel_non_reduce_only", account, reason)
        await self.alert({"level": "WARNING", "account": account, "action": "cancel_non_reduce_only", "reason": reason})

        orders = await self.client.get_open_orders(account=account)
        tasks = []
        for order in orders:
            if not order.is_reduce_only:
                tasks.append(
                    self.client.cancel_order(order_id=order.order_id, market_name=order.market)
                )
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _action_close_all(self, account: str, reason: str):
        """Emergency: close all positions."""
        self._log_action("close_all", account, reason)
        await self.alert({"level": "CRITICAL", "account": account, "action": "close_all", "reason": reason})

        # Cancel all orders first
        orders = await self.client.get_open_orders(account=account)
        cancel_tasks = [
            self.client.cancel_order(order_id=o.order_id, market_name=o.market) for o in orders
        ]
        await asyncio.gather(*cancel_tasks, return_exceptions=True)

        # Close all positions
        positions = await self.client.get_positions(account=account)
        close_tasks = []
        for pos in positions:
            if pos.size == 0:
                continue
            prices = await self.client.get_price(pos.market)
            mark = prices[0].mark_px
            close_tasks.append(
                self.client.place_order(
                    market_name=pos.market,
                    price=mark * (1.01 if pos.size < 0 else 0.99),
                    size=abs(pos.size),
                    is_buy=(pos.size < 0),
                    time_in_force=TimeInForce.ImmediateOrCancel,
                    is_reduce_only=True,
                )
            )
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

    async def _action_close_position(self, account: str, market: str, reason: str):
        self._log_action("close_position", account, reason, market=market)
        await self.alert({"level": "WARNING", "account": account, "market": market, "action": "close_position", "reason": reason})

        pos = self.state[account].positions.get(market)
        if not pos or pos.size == 0:
            return

        prices = await self.client.get_price(market)
        mark = prices[0].mark_px
        await self.client.place_order(
            market_name=market,
            price=mark * (1.01 if pos.size < 0 else 0.99),
            size=abs(pos.size),
            is_buy=(pos.size < 0),
            time_in_force=TimeInForce.ImmediateOrCancel,
            is_reduce_only=True,
        )

    async def _action_emergency_stop_loss(self, account: str, pos):
        """Place an emergency SL on an unprotected position."""
        self._log_action("emergency_sl", account, f"Position in {pos.market} unprotected for > {self.limits.require_stop_loss_within_s}s")
        await self.alert({"level": "WARNING", "account": account, "market": pos.market, "action": "emergency_sl"})

        prices = await self.client.get_price(pos.market)
        mark = prices[0].mark_px
        # 3% stop loss from current mark
        if pos.size > 0:
            sl_trigger = mark * 0.97
        else:
            sl_trigger = mark * 1.03

        await self.client.place_tp_sl(
            market_addr=pos.market,
            sl_trigger_price=sl_trigger,
            sl_limit_price=sl_trigger * (0.995 if pos.size > 0 else 1.005),
            subaccount_addr=account,
        )

    async def _action_halt_trading(self, account: str, reason: str):
        self._log_action("halt_trading", account, reason)
        await self.alert({"level": "CRITICAL", "account": account, "action": "halt_trading", "reason": reason})
        await self._action_close_all(account, reason)

    async def _periodic_deep_check(self):
        """REST-based cross-validation of WS state."""
        for account in self.subaccounts:
            try:
                rest_positions = await self.client.get_positions(account=account)
                ws_positions = self.state[account].positions

                for pos in rest_positions:
                    ws_pos = ws_positions.get(pos.market)
                    if ws_pos and abs(ws_pos.size - pos.size) > 0.0001:
                        await self.alert({
                            "level": "WARNING",
                            "account": account,
                            "market": pos.market,
                            "message": f"State mismatch: WS says {ws_pos.size}, REST says {pos.size}",
                            "action": "state_resync",
                        })
                        self.state[account].positions[pos.market] = pos
            except Exception as e:
                await self.alert({"level": "ERROR", "account": account, "message": f"Deep check failed: {e}"})

    def _log_action(self, action: str, account: str, reason: str, **kwargs):
        entry = {
            "timestamp_ms": int(time.time() * 1000),
            "action": action,
            "account": account,
            "reason": reason,
            **kwargs,
        }
        self.action_log.append(entry)
        logger.warning(json.dumps(entry))

    async def _default_alert(self, payload: dict):
        logger.critical(json.dumps(payload))


@dataclass
class SubaccountState:
    overview: AccountOverview | None = None
    positions: dict = None

    def __post_init__(self):
        if self.positions is None:
            self.positions = {}
```

---

## Anti-Patterns

### 1. Polling Instead of Subscribing

**Bad**: Polling the REST API for price updates in a loop. This wastes rate limit budget, always sees stale data, and can never react faster than the poll interval.

```python
# DON'T: 1 req/sec per market, always 1 second behind
while True:
    prices = await client.get_prices()
    for p in prices:
        process(p)
    await asyncio.sleep(1)
```

**Good**: Subscribe to the WebSocket for real-time prices. Use REST only as a fallback when WS is stale.

```python
# DO: instant updates, zero rate limit cost
await client.subscribe_market_price("BTC-USD", callback=process)
```

**Impact**: A market maker polling at 1s intervals is quoting on data that's 0.5–1s old on average. In a volatile market moving 10bps/sec, that's 5–10bps of adverse selection per quote.

### 2. Not Tracking Fills

**Bad**: Placing orders and not tracking whether they fill. The bot has no idea what its actual position is.

```python
# DON'T: fire and forget
await client.place_order(market_name="BTC-USD", ...)
# ... bot continues without knowing if it filled
```

**Good**: Track every fill via WS `order_updates` and `user_trades`. Maintain local position state.

```python
# DO: track every fill
await client.subscribe_order_updates(subaccount, callback=on_order_update)
await client.subscribe_user_trades(subaccount, callback=on_fill)

async def on_fill(trade: UserTradesUpdate):
    for fill in trade.trades:
        inventory.on_fill(fill.side, fill.size, fill.price, fill.fee)
```

**Impact**: Without fill tracking, the bot doesn't know its inventory. It can accumulate dangerous one-sided exposure without realizing it.

### 3. Ignoring Funding Costs

**Bad**: Holding positions for hours or days without accounting for continuous funding.

```python
# DON'T: open position and forget about funding
await client.place_order(market_name="BTC-USD", ...)
# ... hold for 24 hours at +15bps/hr funding rate
# Hidden cost: 15 × 24 = 360bps = 3.6% of position notional
```

**Good**: Track funding rate and include it in PnL calculations.

```python
# DO: factor funding into hold/close decisions
if position.accrued_funding < -daily_funding_budget:
    await close_position(market)
```

**Impact**: A bot holding a long position while paying 15bps/hr funding is losing $3,600/day on a $100k position. Many strategies that look profitable on paper are funding-negative in practice.

### 4. Not Using client_order_id

**Bad**: Placing orders without a `client_order_id`, then struggling to correlate results with intentions.

```python
# DON'T: no way to match this order to the signal that triggered it
await client.place_order(market_name="BTC-USD", price=68000, size=0.1, ...)
```

**Good**: Assign a unique `client_order_id` to every order. Use it for idempotency (don't double-place on retry), correlation (match fills to signals), and cancellation (cancel by client ID without needing the on-chain order ID).

```python
# DO: every order has a traceable ID
signal_id = f"momentum-btc-{signal.timestamp}"
await client.place_order(
    market_name="BTC-USD",
    price=68000,
    size=0.1,
    client_order_id=signal_id,
    ...
)

# Later: cancel by client ID
await client.cancel_client_order(client_order_id=signal_id)
```

**Impact**: Without `client_order_id`, the bot can't safely retry failed orders (might double-place), can't correlate fills to strategy signals for attribution, and can't cancel orders without tracking the on-chain order ID from the placement result.

### 5. Blocking the WebSocket Callback

**Bad**: Running heavy computation or making network calls inside the WS callback. This blocks the WS read loop, causing message buffering and eventual drops.

```python
# DON'T: blocks the entire WS read pipeline
async def on_price(price: MarketPrice):
    features = run_ml_model(price)        # 50ms of CPU work
    await client.place_order(...)          # 100ms of network I/O
    await update_database(features)        # 20ms of I/O
```

**Good**: The WS callback should do the absolute minimum: store the update and dispatch work to a separate task.

```python
# DO: callback is instant, work happens in background
async def on_price(price: MarketPrice):
    latest_prices[price.market] = price
    asyncio.create_task(process_price(price))

async def process_price(price: MarketPrice):
    features = run_ml_model(price)
    await client.place_order(...)
```

**Impact**: A callback that takes 50ms blocks the WS read loop. At 1,000 messages/sec, this means 50 messages are buffered (or dropped) per slow callback. Over time, the bot falls behind and trades on increasingly stale data.

### 6. Not Reconciling State After Reconnection

**Bad**: Reconnecting the WebSocket and immediately resuming trading without checking what happened during the gap.

```python
# DON'T: resume as if nothing happened
async def on_reconnect():
    logger.info("Reconnected!")
    # ... immediately start placing orders on stale state
```

**Good**: After any WS reconnect, treat local state as STALE and re-sync from REST before trading.

```python
# DO: rebuild state from REST truth
async def on_reconnect():
    positions = await client.get_positions(account=subaccount)
    open_orders = await client.get_open_orders(account=subaccount)
    local_state.replace_all(positions, open_orders)
    await verify_risk_limits(local_state)
    logger.info("State re-synced, resuming trading")
```

**Impact**: During a 10-second disconnect, the bot might have had orders fill, positions liquidated, or funding accrue. Trading on stale state can lead to duplicate positions, exceeded risk limits, or missed fills.
