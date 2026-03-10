"""Background gas price polling manager."""

from __future__ import annotations

import asyncio
import contextlib
import time

import httpx


class GasPriceInfo:
    __slots__ = ("gas_estimate", "timestamp")

    def __init__(self, gas_estimate: int, timestamp: int) -> None:
        self.gas_estimate = gas_estimate
        self.timestamp = timestamp


class GasPriceManager:
    """Polls the Aptos fullnode for gas price estimates on a background task."""

    def __init__(
        self,
        fullnode_url: str,
        multiplier: float = 1.0,
        refresh_interval_ms: int = 10_000,
    ) -> None:
        self._fullnode_url = fullnode_url.rstrip("/")
        self._multiplier = multiplier
        self._refresh_interval = refresh_interval_ms / 1000.0
        self._gas_price: GasPriceInfo | None = None
        self._task: asyncio.Task[None] | None = None
        self._http = httpx.AsyncClient()

    async def get_gas_price(self) -> int | None:
        info = self._gas_price
        return info.gas_estimate if info else None

    async def initialize(self) -> None:
        """Fetch initial gas price and start the background refresh loop."""
        await self._fetch_and_set()
        self._task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(self._refresh_interval)
            await self._fetch_and_set()

    async def _fetch_and_set(self) -> None:
        estimate = await self._fetch_gas_estimate()
        if estimate is not None:
            adjusted = int(estimate * self._multiplier)
            self._gas_price = GasPriceInfo(
                gas_estimate=adjusted,
                timestamp=int(time.time() * 1000),
            )

    async def _fetch_gas_estimate(self) -> int | None:
        try:
            url = f"{self._fullnode_url}/estimate_gas_price"
            resp = await self._http.get(url)
            body = resp.json()
            return body.get("gas_estimate", 100)
        except Exception:
            return None

    async def destroy(self) -> None:
        """Cancel the background polling task and close the HTTP client."""
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        await self._http.aclose()
