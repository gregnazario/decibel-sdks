"""REST read client for all Decibel API endpoints."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import TypeVar

import httpx
from pydantic import TypeAdapter

from decibel_sdk.client.ws import Subscription, WebSocketManager
from decibel_sdk.config import DecibelConfig
from decibel_sdk.errors import ApiError, ApiResponse, NetworkError
from decibel_sdk.models.account import (
    AccountOverview,
    Delegation,
    Leaderboard,
    UserFundHistoryItem,
    UserFundingHistoryItem,
    UserSubaccount,
    UserTradeHistoryItem,
)
from decibel_sdk.models.common import (
    CandlestickInterval,
    MarketDepthAggregationSize,
    PageParams,
    PaginatedResponse,
    SearchTermParams,
    SortParams,
    VolumeWindow,
)
from decibel_sdk.models.market import (
    Candlestick,
    MarketContext,
    MarketDepth,
    MarketPrice,
    MarketTrade,
    PerpMarketConfig,
)
from decibel_sdk.models.order import (
    OrderStatus,
    UserActiveTwap,
    UserOpenOrder,
    UserOrderHistoryItem,
)
from decibel_sdk.models.position import UserPosition
from decibel_sdk.models.vault import (
    UserOwnedVault,
    UserPerformanceOnVault,
    VaultsResponse,
)
from decibel_sdk.models.ws import (
    AccountOverviewWsMessage,
    AllMarketPricesWsMessage,
    CandlestickWsMessage,
    MarketDepthWsMessage,
    MarketPriceWsMessage,
    MarketTradesWsMessage,
    UserActiveTwapsWsMessage,
    UserOpenOrdersWsMessage,
    UserPositionsWsMessage,
)
from decibel_sdk.utils.query import construct_query_params

T = TypeVar("T")


class DecibelReadClient:
    """Async REST client for reading data from the Decibel API."""

    def __init__(
        self,
        config: DecibelConfig,
        api_key: str | None = None,
    ) -> None:
        config.model_dump()  # triggers validation
        self._config = config
        self._api_key = api_key
        self._http = httpx.AsyncClient(http2=True)
        self._ws = WebSocketManager(config, api_key=api_key)

    async def __aenter__(self) -> DecibelReadClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @property
    def ws(self) -> WebSocketManager:
        return self._ws

    async def close(self) -> None:
        await self._ws.close()
        await self._http.aclose()

    def _api_url(self, path: str) -> str:
        return f"{self._config.trading_http_url}/api/v1{path}"

    async def _get(
        self,
        path: str,
        response_type: type[T],
        params: list[tuple[str, str]] | None = None,
    ) -> ApiResponse[T]:
        url = self._api_url(path)
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        try:
            response = await self._http.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc)) from exc

        status = response.status_code
        status_text = str(status)

        if status >= 400:
            body = response.text
            raise ApiError(status=status, status_text=status_text, message=body)

        adapter = TypeAdapter(response_type)
        data = adapter.validate_json(response.content)

        return ApiResponse(data=data, status=status, status_text=status_text)

    # --- Markets ---

    async def get_all_markets(self) -> list[PerpMarketConfig]:
        resp = await self._get("/markets", list[PerpMarketConfig])
        return resp.data

    async def get_market_by_name(self, name: str) -> PerpMarketConfig:
        resp = await self._get(f"/markets/{name}", PerpMarketConfig)
        return resp.data

    # --- Market Contexts ---

    async def get_all_market_contexts(self) -> list[MarketContext]:
        resp = await self._get("/asset-contexts", list[MarketContext])
        return resp.data

    # --- Market Depth ---

    async def get_market_depth(self, market_name: str, limit: int | None = None) -> MarketDepth:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        resp = await self._get(f"/depth/{market_name}", MarketDepth, params)
        return resp.data

    # --- Market Prices ---

    async def get_all_market_prices(self) -> list[MarketPrice]:
        resp = await self._get("/prices", list[MarketPrice])
        return resp.data

    async def get_market_price_by_name(self, market_name: str) -> list[MarketPrice]:
        resp = await self._get(f"/prices/{market_name}", list[MarketPrice])
        return resp.data

    # --- Market Trades ---

    async def get_market_trades(
        self, market_name: str, limit: int | None = None
    ) -> list[MarketTrade]:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        resp = await self._get(f"/trades/{market_name}", list[MarketTrade], params)
        return resp.data

    # --- Candlesticks ---

    async def get_candlesticks(
        self,
        market_name: str,
        interval: CandlestickInterval,
        start_time: int,
        end_time: int,
    ) -> list[Candlestick]:
        params = [
            ("interval", interval.value),
            ("startTime", str(start_time)),
            ("endTime", str(end_time)),
        ]
        resp = await self._get(f"/candlesticks/{market_name}", list[Candlestick], params)
        return resp.data

    # --- Account Overview ---

    async def get_account_overview(
        self,
        sub_addr: str,
        volume_window: VolumeWindow | None = None,
        include_performance: bool | None = None,
    ) -> AccountOverview:
        params: list[tuple[str, str]] = []
        if volume_window is not None:
            params.append(("volume_window", volume_window.value))
        if include_performance is not None:
            params.append(("include_performance", str(include_performance).lower()))
        resp = await self._get(f"/account/{sub_addr}", AccountOverview, params)
        return resp.data

    # --- User Positions ---

    async def get_user_positions(
        self,
        sub_addr: str,
        market_addr: str | None = None,
        include_deleted: bool | None = None,
        limit: int | None = None,
    ) -> list[UserPosition]:
        params: list[tuple[str, str]] = []
        if market_addr is not None:
            params.append(("market_addr", market_addr))
        if include_deleted is not None:
            params.append(("include_deleted", str(include_deleted).lower()))
        if limit is not None:
            params.append(("limit", str(limit)))
        resp = await self._get(f"/positions/{sub_addr}", list[UserPosition], params)
        return resp.data

    # --- User Open Orders ---

    async def get_user_open_orders(self, sub_addr: str) -> list[UserOpenOrder]:
        resp = await self._get(f"/open-orders/{sub_addr}", list[UserOpenOrder])
        return resp.data

    # --- User Order History ---

    async def get_user_order_history(
        self,
        sub_addr: str,
        market_addr: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserOrderHistoryItem]:
        params: list[tuple[str, str]] = []
        if market_addr is not None:
            params.append(("market_addr", market_addr))
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/order-history/{sub_addr}",
            PaginatedResponse[UserOrderHistoryItem],
            params,
        )
        return resp.data

    # --- User Trade History ---

    async def get_user_trade_history(
        self,
        sub_addr: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserTradeHistoryItem]:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/trade-history/{sub_addr}",
            PaginatedResponse[UserTradeHistoryItem],
            params,
        )
        return resp.data

    # --- User Funding History ---

    async def get_user_funding_history(
        self,
        sub_addr: str,
        market_addr: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserFundingHistoryItem]:
        params: list[tuple[str, str]] = []
        if market_addr is not None:
            params.append(("market_addr", market_addr))
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/funding-history/{sub_addr}",
            PaginatedResponse[UserFundingHistoryItem],
            params,
        )
        return resp.data

    # --- User Fund History ---

    async def get_user_fund_history(
        self,
        sub_addr: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserFundHistoryItem]:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/fund-history/{sub_addr}",
            PaginatedResponse[UserFundHistoryItem],
            params,
        )
        return resp.data

    # --- Subaccounts ---

    async def get_user_subaccounts(self, owner_addr: str) -> list[UserSubaccount]:
        resp = await self._get(f"/subaccounts/{owner_addr}", list[UserSubaccount])
        return resp.data

    # --- Delegations ---

    async def get_delegations(self, sub_addr: str) -> list[Delegation]:
        resp = await self._get(f"/delegations/{sub_addr}", list[Delegation])
        return resp.data

    # --- Active TWAPs ---

    async def get_active_twaps(self, sub_addr: str) -> list[UserActiveTwap]:
        resp = await self._get(f"/active-twaps/{sub_addr}", list[UserActiveTwap])
        return resp.data

    # --- TWAP History ---

    async def get_twap_history(
        self,
        sub_addr: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserActiveTwap]:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/twap-history/{sub_addr}",
            PaginatedResponse[UserActiveTwap],
            params,
        )
        return resp.data

    # --- Vaults ---

    async def get_vaults(
        self,
        page: PageParams | None = None,
        sort: SortParams | None = None,
        search: SearchTermParams | None = None,
    ) -> VaultsResponse:
        params = construct_query_params(
            page or PageParams(),
            sort or SortParams(),
            search or SearchTermParams(),
        )
        resp = await self._get("/vaults", VaultsResponse, params or None)
        return resp.data

    async def get_user_owned_vaults(
        self,
        account_addr: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[UserOwnedVault]:
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        resp = await self._get(
            f"/vaults/owned/{account_addr}",
            PaginatedResponse[UserOwnedVault],
            params,
        )
        return resp.data

    async def get_user_performances_on_vaults(
        self, account_addr: str
    ) -> list[UserPerformanceOnVault]:
        resp = await self._get(
            f"/vaults/performance/{account_addr}",
            list[UserPerformanceOnVault],
        )
        return resp.data

    # --- Leaderboard ---

    async def get_leaderboard(
        self,
        page: PageParams | None = None,
        sort: SortParams | None = None,
        search: SearchTermParams | None = None,
    ) -> Leaderboard:
        params = construct_query_params(
            page or PageParams(),
            sort or SortParams(),
            search or SearchTermParams(),
        )
        resp = await self._get("/leaderboard", Leaderboard, params or None)
        return resp.data

    # --- Order Status ---

    async def get_order_status(
        self,
        order_id: str,
        market_address: str,
        user_address: str,
    ) -> OrderStatus | None:
        params = [
            ("market_address", market_address),
            ("user_address", user_address),
        ]
        try:
            resp = await self._get(f"/orders/{order_id}", OrderStatus, params)
            return resp.data
        except ApiError as e:
            if e.status == 404:
                return None
            raise

    # --- WebSocket Subscriptions ---

    def subscribe_account_overview(
        self, sub_addr: str
    ) -> AbstractAsyncContextManager[Subscription[AccountOverviewWsMessage]]:
        topic = f"accountOverview:{sub_addr}"
        return self._ws.subscribe(topic, AccountOverviewWsMessage)

    def subscribe_user_positions(
        self, sub_addr: str
    ) -> AbstractAsyncContextManager[Subscription[UserPositionsWsMessage]]:
        topic = f"userPositions:{sub_addr}"
        return self._ws.subscribe(topic, UserPositionsWsMessage)

    def subscribe_user_open_orders(
        self, sub_addr: str
    ) -> AbstractAsyncContextManager[Subscription[UserOpenOrdersWsMessage]]:
        topic = f"userOpenOrders:{sub_addr}"
        return self._ws.subscribe(topic, UserOpenOrdersWsMessage)

    def subscribe_market_depth(
        self, market_name: str, agg_size: MarketDepthAggregationSize
    ) -> AbstractAsyncContextManager[Subscription[MarketDepthWsMessage]]:
        topic = f"marketDepth:{market_name}"
        return self._ws.subscribe(topic, MarketDepthWsMessage)

    def subscribe_market_price(
        self, market_name: str
    ) -> AbstractAsyncContextManager[Subscription[MarketPriceWsMessage]]:
        topic = f"marketPrice:{market_name}"
        return self._ws.subscribe(topic, MarketPriceWsMessage)

    def subscribe_all_market_prices(
        self,
    ) -> AbstractAsyncContextManager[Subscription[AllMarketPricesWsMessage]]:
        return self._ws.subscribe("allMarketPrices", AllMarketPricesWsMessage)

    def subscribe_market_trades(
        self, market_name: str
    ) -> AbstractAsyncContextManager[Subscription[MarketTradesWsMessage]]:
        topic = f"marketTrades:{market_name}"
        return self._ws.subscribe(topic, MarketTradesWsMessage)

    def subscribe_candlestick(
        self, market_name: str, interval: CandlestickInterval
    ) -> AbstractAsyncContextManager[Subscription[CandlestickWsMessage]]:
        topic = f"marketCandlestick:{market_name}:{interval.value}"
        return self._ws.subscribe(topic, CandlestickWsMessage)

    def subscribe_user_active_twaps(
        self, sub_addr: str
    ) -> AbstractAsyncContextManager[Subscription[UserActiveTwapsWsMessage]]:
        topic = f"userActiveTwaps:{sub_addr}"
        return self._ws.subscribe(topic, UserActiveTwapsWsMessage)
