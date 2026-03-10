"""Tests for the gas price manager with mocked HTTP."""

from __future__ import annotations

import asyncio

import pytest

from decibel_sdk.gas.manager import GasPriceManager


@pytest.fixture
def gas_url() -> str:
    return "https://fullnode.testnet.aptoslabs.com/v1"


class TestGasPriceManager:
    async def test_initial_price_none(self, gas_url: str) -> None:
        mgr = GasPriceManager(gas_url)
        assert await mgr.get_gas_price() is None
        await mgr.destroy()

    async def test_initialize_fetches_price(
        self,
        gas_url: str,
        httpx_mock: pytest.fixture,  # type: ignore[type-arg]
    ) -> None:
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 150},
        )

        mgr = GasPriceManager(gas_url, multiplier=1.0, refresh_interval_ms=60_000)
        await mgr.initialize()

        price = await mgr.get_gas_price()
        assert price == 150

        await mgr.destroy()

    async def test_multiplier_applied(
        self,
        gas_url: str,
        httpx_mock: pytest.fixture,  # type: ignore[type-arg]
    ) -> None:
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 100},
        )

        mgr = GasPriceManager(gas_url, multiplier=1.5, refresh_interval_ms=60_000)
        await mgr.initialize()

        price = await mgr.get_gas_price()
        assert price == 150

        await mgr.destroy()

    @pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
    async def test_refresh_updates_price(
        self,
        gas_url: str,
        httpx_mock: pytest.fixture,  # type: ignore[type-arg]
    ) -> None:
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        # First fetch during initialize
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 100},
        )
        # Second fetch during poll
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 200},
        )

        mgr = GasPriceManager(gas_url, multiplier=1.0, refresh_interval_ms=50)
        await mgr.initialize()
        assert await mgr.get_gas_price() == 100

        # Wait for the poll to fire
        await asyncio.sleep(0.15)
        assert await mgr.get_gas_price() == 200

        await mgr.destroy()

    async def test_destroy_cancels_task(
        self,
        gas_url: str,
        httpx_mock: pytest.fixture,  # type: ignore[type-arg]
    ) -> None:
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 100},
        )

        mgr = GasPriceManager(gas_url, refresh_interval_ms=60_000)
        await mgr.initialize()
        assert mgr._task is not None

        await mgr.destroy()
        assert mgr._task is None

    @pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
    async def test_fetch_failure_keeps_old_price(
        self,
        gas_url: str,
        httpx_mock: pytest.fixture,  # type: ignore[type-arg]
    ) -> None:
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        # Successful first fetch
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            json={"gas_estimate": 100},
        )
        # Failed second fetch
        mock.add_response(
            url=f"{gas_url}/estimate_gas_price",
            status_code=500,
        )

        mgr = GasPriceManager(gas_url, multiplier=1.0, refresh_interval_ms=50)
        await mgr.initialize()
        assert await mgr.get_gas_price() == 100

        await asyncio.sleep(0.15)
        # Should still have the old price since the fetch failed
        assert await mgr.get_gas_price() == 100

        await mgr.destroy()
