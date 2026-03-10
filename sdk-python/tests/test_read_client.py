"""Tests for the REST read client with pytest-httpx mocked responses."""

from __future__ import annotations

import pytest

from decibel_sdk.client.read import DecibelReadClient
from decibel_sdk.config import DecibelConfig, Deployment, Network
from decibel_sdk.errors import ApiError
from decibel_sdk.models.common import CandlestickInterval

BASE = "https://api.testnet.decibel.trade/api/v1"


@pytest.fixture
def config() -> DecibelConfig:
    return DecibelConfig(
        network=Network.TESTNET,
        fullnode_url="https://fullnode.testnet.aptoslabs.com/v1",
        trading_http_url="https://api.testnet.decibel.trade",
        trading_ws_url="wss://api.testnet.decibel.trade/ws",
        deployment=Deployment(package="0xpkg", usdc="", testc="", perp_engine_global=""),
    )


@pytest.fixture
async def client(config: DecibelConfig) -> DecibelReadClient:
    c = DecibelReadClient(config)
    yield c  # type: ignore[misc]
    await c.close()


class TestGetAllMarkets:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/markets",
            json=[
                {
                    "market_addr": "0xm1",
                    "market_name": "BTC-USD",
                    "sz_decimals": 4,
                    "px_decimals": 2,
                    "max_leverage": 50.0,
                    "min_size": 0.001,
                    "lot_size": 0.001,
                    "tick_size": 0.5,
                    "max_open_interest": 1e6,
                    "margin_call_fee_pct": 0.5,
                    "taker_in_next_block": True,
                }
            ],
        )

        markets = await client.get_all_markets()
        assert len(markets) == 1
        assert markets[0].market_name == "BTC-USD"


class TestGetMarketByName:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/markets/ETH-USD",
            json={
                "market_addr": "0xm2",
                "market_name": "ETH-USD",
                "sz_decimals": 3,
                "px_decimals": 2,
                "max_leverage": 20.0,
                "min_size": 0.01,
                "lot_size": 0.01,
                "tick_size": 0.1,
                "max_open_interest": 5e5,
                "margin_call_fee_pct": 0.5,
                "taker_in_next_block": False,
            },
        )

        market = await client.get_market_by_name("ETH-USD")
        assert market.market_name == "ETH-USD"
        assert market.max_leverage == 20.0


class TestGetMarketDepth:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/depth/BTC-USD",
            json={
                "market": "BTC-USD",
                "bids": [{"price": 50000.0, "size": 1.0}],
                "asks": [{"price": 50001.0, "size": 2.0}],
                "unix_ms": 1700000000000,
            },
        )

        depth = await client.get_market_depth("BTC-USD")
        assert depth.market == "BTC-USD"
        assert len(depth.bids) == 1


class TestGetMarketPrices:
    async def test_get_all(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/prices",
            json=[
                {
                    "market": "BTC-USD",
                    "mark_px": 50000.0,
                    "mid_px": 49999.0,
                    "oracle_px": 50001.0,
                    "funding_rate_bps": 0.01,
                    "is_funding_positive": True,
                    "open_interest": 1e6,
                    "transaction_unix_ms": 1700000000000,
                }
            ],
        )

        prices = await client.get_all_market_prices()
        assert len(prices) == 1
        assert prices[0].mark_px == 50000.0


class TestGetCandlesticks:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/candlesticks/BTC-USD?interval=1h&startTime=0&endTime=1700000000",
            json=[
                {
                    "T": 1700000000,
                    "c": 50000.0,
                    "h": 51000.0,
                    "i": "1h",
                    "l": 49000.0,
                    "o": 49500.0,
                    "t": 1699996400,
                    "v": 1000.0,
                }
            ],
        )

        candles = await client.get_candlesticks(
            "BTC-USD", CandlestickInterval.ONE_HOUR, 0, 1700000000
        )
        assert len(candles) == 1
        assert candles[0].close_timestamp == 1700000000


class TestGetAccountOverview:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/account/0xsub",
            json={
                "perp_equity_balance": 10000.0,
                "unrealized_pnl": 0.0,
                "unrealized_funding_cost": 0.0,
                "cross_margin_ratio": 0.1,
                "maintenance_margin": 500.0,
                "cross_account_position": 5000.0,
                "total_margin": 2000.0,
                "usdc_cross_withdrawable_balance": 8000.0,
                "usdc_isolated_withdrawable_balance": 1000.0,
            },
        )

        ao = await client.get_account_overview("0xsub")
        assert ao.perp_equity_balance == 10000.0


class TestGetUserPositions:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/positions/0xsub",
            json=[
                {
                    "market": "0xm",
                    "user": "0xsub",
                    "size": 1.0,
                    "user_leverage": 10.0,
                    "entry_price": 50000.0,
                    "is_isolated": False,
                    "unrealized_funding": 0.0,
                    "estimated_liquidation_price": 40000.0,
                    "has_fixed_sized_tpsls": False,
                }
            ],
        )

        positions = await client.get_user_positions("0xsub")
        assert len(positions) == 1
        assert positions[0].size == 1.0


class TestGetUserOpenOrders:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/open-orders/0xsub",
            json=[
                {
                    "market": "0xm",
                    "order_id": "o1",
                    "price": 50000.0,
                    "orig_size": 1.0,
                    "remaining_size": 1.0,
                    "is_buy": True,
                    "time_in_force": "GoodTillCanceled",
                    "is_reduce_only": False,
                    "status": "Acknowledged",
                    "transaction_unix_ms": 1700000000000,
                    "transaction_version": 1,
                }
            ],
        )

        orders = await client.get_user_open_orders("0xsub")
        assert len(orders) == 1
        assert orders[0].order_id == "o1"


class TestGetUserOrderHistory:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/order-history/0xsub",
            json={
                "items": [
                    {
                        "market": "0xm",
                        "order_id": "o2",
                        "price": 50000.0,
                        "orig_size": 1.0,
                        "remaining_size": 0.0,
                        "is_buy": True,
                        "time_in_force": "GoodTillCanceled",
                        "is_reduce_only": False,
                        "status": "Filled",
                        "transaction_unix_ms": 1700000000000,
                        "transaction_version": 2,
                    }
                ],
                "total_count": 1,
            },
        )

        resp = await client.get_user_order_history("0xsub")
        assert resp.total_count == 1
        assert resp.items[0].order_id == "o2"


class TestGetUserTradeHistory:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/trade-history/0xsub",
            json={
                "items": [
                    {
                        "account": "0xa",
                        "market": "BTC-USD",
                        "action": "OpenLong",
                        "size": 1.0,
                        "price": 50000.0,
                        "is_profit": True,
                        "realized_pnl_amount": 100.0,
                        "is_funding_positive": True,
                        "realized_funding_amount": 5.0,
                        "is_rebate": False,
                        "fee_amount": 10.0,
                        "transaction_unix_ms": 1700000000000,
                        "transaction_version": 1,
                    }
                ],
                "total_count": 1,
            },
        )

        resp = await client.get_user_trade_history("0xsub")
        assert resp.total_count == 1


class TestGetSubaccounts:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/subaccounts/0xowner",
            json=[
                {
                    "subaccount_address": "0xsub",
                    "primary_account_address": "0xowner",
                    "is_primary": True,
                }
            ],
        )

        subs = await client.get_user_subaccounts("0xowner")
        assert len(subs) == 1
        assert subs[0].is_primary


class TestGetDelegations:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/delegations/0xsub",
            json=[
                {
                    "delegated_account": "0xdel",
                    "permission_type": "trading",
                }
            ],
        )

        delegations = await client.get_delegations("0xsub")
        assert len(delegations) == 1


class TestGetActiveTwaps:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/active-twaps/0xsub",
            json=[
                {
                    "market": "0xm",
                    "is_buy": True,
                    "order_id": "t1",
                    "client_order_id": "c1",
                    "is_reduce_only": False,
                    "start_unix_ms": 1700000000000,
                    "frequency_s": 60,
                    "duration_s": 3600,
                    "orig_size": 10.0,
                    "remaining_size": 5.0,
                    "status": "Activated",
                    "transaction_unix_ms": 1700000000000,
                    "transaction_version": 1,
                }
            ],
        )

        twaps = await client.get_active_twaps("0xsub")
        assert len(twaps) == 1
        assert twaps[0].order_id == "t1"


class TestGetVaults:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/vaults",
            json={
                "items": [
                    {
                        "address": "0xv",
                        "name": "Alpha",
                        "manager": "0xm",
                        "status": "active",
                        "created_at": 1700000000,
                    }
                ],
                "total_count": 1,
                "total_value_locked": 1e6,
                "total_volume": 5e6,
            },
        )

        resp = await client.get_vaults()
        assert resp.total_count == 1
        assert resp.items[0].name == "Alpha"


class TestGetLeaderboard:
    async def test_success(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/leaderboard",
            json={
                "items": [
                    {
                        "rank": 1,
                        "account": "0xa",
                        "account_value": 100000.0,
                        "realized_pnl": 5000.0,
                        "roi": 0.05,
                        "volume": 1e6,
                    }
                ],
                "total_count": 100,
            },
        )

        lb = await client.get_leaderboard()
        assert lb.total_count == 100
        assert lb.items[0].rank == 1


class TestGetOrderStatus:
    async def test_found(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/orders/o1?market_address=0xm&user_address=0xu",
            json={
                "parent": "0xp",
                "market": "0xm",
                "order_id": "o1",
                "status": "Filled",
                "orig_size": 1.0,
                "remaining_size": 0.0,
                "size_delta": 1.0,
                "price": 50000.0,
                "is_buy": True,
                "details": "filled",
                "transaction_version": 100,
                "unix_ms": 1700000000000,
            },
        )

        status = await client.get_order_status("o1", "0xm", "0xu")
        assert status is not None
        assert status.status == "Filled"

    async def test_not_found(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/orders/o999?market_address=0xm&user_address=0xu",
            status_code=404,
            json={"error": "not found"},
        )

        status = await client.get_order_status("o999", "0xm", "0xu")
        assert status is None


class TestApiError:
    async def test_500_raises(self, client: DecibelReadClient, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(
            url=f"{BASE}/markets",
            status_code=500,
            text="Internal Server Error",
        )

        with pytest.raises(ApiError) as exc_info:
            await client.get_all_markets()
        assert exc_info.value.status == 500


class TestApiKeyHeader:
    async def test_api_key_sent(self, config: DecibelConfig, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(url=f"{BASE}/markets", json=[])

        client = DecibelReadClient(config, api_key="test-key")
        await client.get_all_markets()
        await client.close()

        request = mock.get_request()
        assert request is not None
        assert request.headers["x-api-key"] == "test-key"


class TestContextManager:
    async def test_async_with(self, config: DecibelConfig, httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
        from pytest_httpx import HTTPXMock

        mock: HTTPXMock = httpx_mock  # type: ignore[assignment]
        mock.add_response(url=f"{BASE}/markets", json=[])

        async with DecibelReadClient(config) as client:
            markets = await client.get_all_markets()
            assert markets == []
