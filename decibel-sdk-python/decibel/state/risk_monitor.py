"""Risk monitoring layer on top of PositionStateManager."""

from __future__ import annotations

from dataclasses import dataclass

from decibel.models.account import UserPosition
from decibel.state.position_manager import PositionStateManager


@dataclass
class LiquidationEstimate:
    """Proximity of a position to its liquidation price."""

    market: str
    liquidation_price: float
    current_price: float
    distance_pct: float
    distance_usd: float


class RiskMonitor:
    """Answers real-time risk questions using the shared state manager."""

    def __init__(self, state: PositionStateManager) -> None:
        self._state = state

    def liquidation_distance(
        self, market: str, subaccount: str
    ) -> LiquidationEstimate | None:
        pos = self._state.position(market, subaccount)
        if pos is None:
            return None
        px = self._state.price(market)
        if px is None:
            return None

        mark = px.mark_px
        liq = pos.estimated_liquidation_price
        distance_pct = abs(mark - liq) / mark * 100 if mark else 0.0
        distance_usd = abs(mark - liq) * abs(pos.size)

        return LiquidationEstimate(
            market=market,
            liquidation_price=liq,
            current_price=mark,
            distance_pct=distance_pct,
            distance_usd=distance_usd,
        )

    def min_liquidation_distance(
        self, subaccount: str
    ) -> LiquidationEstimate | None:
        positions = self._state.positions(subaccount)
        closest: LiquidationEstimate | None = None
        for market in positions:
            est = self.liquidation_distance(market, subaccount)
            if est is None:
                continue
            if closest is None or est.distance_pct < closest.distance_pct:
                closest = est
        return closest

    def margin_warning(
        self,
        subaccount: str,
        warn_threshold: float = 0.80,
        critical_threshold: float = 0.90,
    ) -> str | None:
        ov = self._state.overview(subaccount)
        if ov is None:
            return None
        usage = self._state.margin_usage_pct(subaccount)
        if usage >= critical_threshold:
            return "critical"
        if usage >= warn_threshold:
            return "warn"
        return "ok"

    def funding_accrual_rate(
        self, market: str, subaccount: str
    ) -> float | None:
        pos = self._state.position(market, subaccount)
        if pos is None:
            return None
        px = self._state.price(market)
        if px is None:
            return None
        return abs(pos.size) * px.mark_px * px.funding_rate_bps / 10_000

    def total_funding_accrual_rate(self, subaccount: str) -> float:
        positions = self._state.positions(subaccount)
        total = 0.0
        for market in positions:
            rate = self.funding_accrual_rate(market, subaccount)
            if rate is not None:
                total += rate
        return total

    def positions_without_tp_sl(self, subaccount: str) -> list[UserPosition]:
        positions = self._state.positions(subaccount)
        return [
            pos for pos in positions.values()
            if not pos.tp_order_id and not pos.sl_order_id
        ]

    def unprotected_exposure_usd(self, subaccount: str) -> float:
        unprotected = self.positions_without_tp_sl(subaccount)
        total = 0.0
        for pos in unprotected:
            px = self._state.price(pos.market)
            mark = px.mark_px if px else pos.entry_price
            total += abs(pos.size * mark)
        return total

    def risk_summary(self, subaccount: str) -> dict:
        min_liq = self.min_liquidation_distance(subaccount)
        return {
            "margin_warning": self.margin_warning(subaccount),
            "gross_exposure_usd": self._state.gross_exposure(subaccount),
            "net_exposure_usd": self._state.net_exposure(subaccount),
            "total_funding_accrual_rate": self.total_funding_accrual_rate(subaccount),
            "unprotected_exposure_usd": self.unprotected_exposure_usd(subaccount),
            "min_liquidation_distance_pct": min_liq.distance_pct if min_liq else None,
        }
