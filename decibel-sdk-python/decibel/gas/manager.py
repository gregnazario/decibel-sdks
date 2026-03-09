"""Gas price manager for fetching gas prices from gas station."""

import asyncio
from typing import Any

import httpx

from ..config import DecibelConfig
from ..errors import GasEstimationError, NetworkError


class GasPriceManager:
    """Manages gas prices with periodic refresh from gas station.

    Attributes:
        config: SDK configuration
        refresh_interval: Refresh interval in seconds
        multiplier: Gas price multiplier
    """

    def __init__(
        self,
        config: DecibelConfig,
        refresh_interval: float = 5.0,
        multiplier: float = 1.0,
    ) -> None:
        """Initialize gas price manager.

        Args:
            config: SDK configuration
            refresh_interval: Refresh interval in seconds
            multiplier: Gas price multiplier (e.g., 1.1 for 10% extra)
        """
        self._config = config
        self._refresh_interval = refresh_interval
        self._multiplier = multiplier
        self._gas_price: int | None = None
        self._lock = asyncio.Lock()
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start background gas price refresh."""
        if self._running:
            return

        self._running = True
        # Fetch initial gas price
        await self._fetch_gas_price()
        # Start background refresh task
        self._task = asyncio.create_task(self._refresh_loop())

    async def stop(self) -> None:
        """Stop background gas price refresh."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _refresh_loop(self) -> None:
        """Background refresh loop."""
        while self._running:
            try:
                await asyncio.sleep(self._refresh_interval)
                if self._running:
                    await self._fetch_gas_price()
            except asyncio.CancelledError:
                break
            except Exception:
                # Don't crash the loop on fetch errors
                pass

    async def _fetch_gas_price(self) -> None:
        """Fetch gas price from gas station.

        Raises:
            NetworkError: Network error
            GasEstimationError: Gas estimation error
        """
        if not self._config.gas_station_url:
            # Use default gas price if no gas station
            async with self._lock:
                self._gas_price = 100
            return

        url = f"{self._config.gas_station_url}/gas_price"
        headers = {}
        if self._config.gas_station_api_key:
            headers["x-api-key"] = self._config.gas_station_api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                # Parse gas price (assuming format: {"gas_price": "123"} or similar)
                gas_price_str = data.get("gas_price", "100")
                async with self._lock:
                    self._gas_price = int(int(gas_price_str) * self._multiplier)

        except httpx.HTTPError as e:
            raise NetworkError(f"Failed to fetch gas price: {e}", cause=e) from e
        except (ValueError, KeyError) as e:
            raise GasEstimationError(f"Failed to parse gas price response: {e}", cause=e) from e

    async def get_gas_price(self) -> int:
        """Get current gas price.

        Returns:
            Gas price in gas units
        """
        if not self._running:
            # Auto-start if not running
            await self.start()

        async with self._lock:
            if self._gas_price is None:
                # Fetch if not yet fetched
                await self._fetch_gas_price()
            return self._gas_price or 100

    @property
    def is_running(self) -> bool:
        """Check if manager is running.

        Returns:
            True if running
        """
        return self._running
