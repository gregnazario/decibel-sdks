"""REST API client for read operations."""

from typing import Any, Callable, Generic, TypeVar

import httpx

from ..config import DecibelConfig
from ..errors import APIError, NetworkError
from ..models.account import (
    AccountOverview,
    Delegation,
    LeaderboardItem,
    PortfolioChartData,
    UserFundingHistoryItem,
    UserFundHistoryItem,
    UserOpenOrder,
    UserOrderHistoryItem,
    UserPosition,
    UserSubaccount,
    UserTradeHistoryItem,
)
from ..models.common import PageParams, PaginatedResponse, SearchTermParams, SortParams
from ..models.enums import CandlestickInterval, VolumeWindow
from ..models.market import (
    Candlestick,
    MarketContext,
    MarketDepth,
    MarketPrice,
    MarketTrade,
    PerpMarketConfig,
)
from ..models.vault import UserOwnedVault, UserPerformanceOnVault, Vault, VaultsResponse
from .websocket import WebSocketManager

T = TypeVar("T")


class ApiResponse(Generic[T]):
    """API response wrapper.

    Attributes:
        data: Response data
        status: HTTP status code
        status_text: HTTP status text
    """

    def __init__(self, data: T, status: int, status_text: str) -> None:
        self.data = data
        self.status = status
        self.status_text = status_text


import typing


class DecibelReadClient:
    """REST API client for reading market data and account information.

    Attributes:
        config: SDK configuration
        ws: WebSocket manager for real-time data
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        config: DecibelConfig,
        api_key: str | None = None,
        on_ws_error: Callable[[str], None] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize read client.

        Args:
            config: SDK configuration
            api_key: Optional API key for authenticated requests
            on_ws_error: Optional callback for WebSocket errors
            timeout: HTTP request timeout in seconds
        """
        config.validate()
        self._config = config
        self._api_key = api_key
        self._timeout = timeout

        # Create HTTP client with connection pooling
        self._http = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

        # Create WebSocket manager
        self.ws = WebSocketManager(config, api_key, on_ws_error)

    def _api_url(self, path: str) -> str:
        """Build full API URL.

        Args:
            path: API path

        Returns:
            Full URL
        """
        return f"{self._config.trading_http_url}/api/v1{path}"

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> ApiResponse[Any]:
        """Make GET request.

        Args:
            path: API path
            params: Query parameters

        Returns:
            API response

        Raises:
            NetworkError: Network error
            APIError: API error
        """
        url = self._api_url(path)
        headers = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        try:
            response = await self._http.get(url, params=params, headers=headers)
        except httpx.HTTPError as e:
            raise NetworkError(f"HTTP request failed: {e}", cause=e) from e

        status = response.status_code
        status_text = response.reason_phrase or ""

        if not response.is_success:
            try:
                message = response.text
            except Exception:
                message = "Unknown error"
            raise APIError(status, status_text, message)

        try:
            data = response.json()
        except Exception as e:
            raise NetworkError(f"Failed to parse JSON: {e}", cause=e) from e

        return ApiResponse(data, status, status_text)

    async def close(self) -> None:
        """Close the HTTP client and WebSocket connection."""
        await self._http.aclose()
        await self.ws.disconnect()

    # --- Markets ---

    async def get_all_markets(self) -> list[PerpMarketConfig]:
        """Get all markets.

        Returns:
            List of market configurations
        """
        resp = await self._get("/markets")
        return [PerpMarketConfig(**m) for m in resp.data]

    async def get_market_by_name(self, name: str) -> PerpMarketConfig:
        """Get market by name.

        Args:
            name: Market name (e.g., "BTC-USD")

        Returns:
            Market configuration
        """
        resp = await self._get(f"/markets/{name}")
        return PerpMarketConfig(**resp.data)

    async def get_all_market_contexts(self) -> list[MarketContext]:
        """Get all market contexts.

        Returns:
            List of market contexts
        """
        resp = await self._get("/asset-contexts")
        return [MarketContext(**c) for c in resp.data]

    # --- Market Depth ---

    async def get_market_depth(self, market_name: str, limit: int = 100) -> MarketDepth:
        """Get market depth (order book).

        Args:
            market_name: Market name
            limit: Number of levels to return

        Returns:
            Market depth
        """
        resp = await self._get(f"/depth/{market_name}", {"limit": limit})
        return MarketDepth(**resp.data)

    # --- Market Prices ---

    async def get_all_market_prices(self) -> list[MarketPrice]:
        """Get all market prices.

        Returns:
            List of market prices
        """
        resp = await self._get("/prices")
        return [MarketPrice(**p) for p in resp.data]

    async def get_market_price(self, market_name: str) -> list[MarketPrice]:
        """Get market price by name.

        Args:
            market_name: Market name

        Returns:
            List of market prices (typically one)
        """
        resp = await self._get(f"/prices/{market_name}")
        return [MarketPrice(**p) for p in resp.data]

    # --- Market Trades ---

    async def get_market_trades(self, market_name: str, limit: int = 100) -> list[MarketTrade]:
        """Get recent market trades.

        Args:
            market_name: Market name
            limit: Number of trades to return

        Returns:
            List of trades
        """
        resp = await self._get(f"/trades/{market_name}", {"limit": limit})
        return [MarketTrade(**t) for t in resp.data]

    # --- Candlesticks ---

    async def get_candlesticks(
        self,
        market_name: str,
        interval: CandlestickInterval,
        start_time: int,
        end_time: int,
    ) -> list[Candlestick]:
        """Get OHLCV candlesticks.

        Args:
            market_name: Market name
            interval: Candlestick interval
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds

        Returns:
            List of candlesticks
        """
        params = {
            "interval": interval.value,
            "startTime": start_time,
            "endTime": end_time,
        }
        resp = await self._get(f"/candlesticks/{market_name}", params)
        return [Candlestick(**c) for c in resp.data]

    # --- Account Overview ---

    async def get_account_overview(
        self,
        subaccount_addr: str,
        volume_window: VolumeWindow | None = None,
        include_performance: bool = False,
    ) -> AccountOverview:
        """Get account overview.

        Args:
            subaccount_addr: Subaccount address
            volume_window: Volume calculation window
            include_performance: Whether to include performance metrics

        Returns:
            Account overview
        """
        params: dict[str, Any] = {"include_performance": include_performance}
        if volume_window:
            params["volume_window"] = volume_window.value
        resp = await self._get(f"/account/{subaccount_addr}", params)
        return AccountOverview(**resp.data)

    # --- User Positions ---

    async def get_positions(
        self,
        subaccount_addr: str,
        market_addr: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[UserPosition]:
        """Get user positions.

        Args:
            subaccount_addr: Subaccount address
            market_addr: Optional market address filter
            include_deleted: Whether to include deleted positions
            limit: Maximum number of positions to return

        Returns:
            List of positions
        """
        params: dict[str, Any] = {"include_deleted": include_deleted, "limit": limit}
        if market_addr:
            params["market_addr"] = market_addr
        resp = await self._get(f"/positions/{subaccount_addr}", params)
        return [UserPosition(**p) for p in resp.data]

    # --- User Open Orders ---

    async def get_open_orders(self, subaccount_addr: str) -> list[UserOpenOrder]:
        """Get user open orders.

        Args:
            subaccount_addr: Subaccount address

        Returns:
            List of open orders
        """
        resp = await self._get(f"/open-orders/{subaccount_addr}")
        return [UserOpenOrder(**o) for o in resp.data]

    # --- User Order History ---

    async def get_order_history(
        self,
        subaccount_addr: str,
        market_addr: str | None = None,
        page_params: PageParams | None = None,
    ) -> PaginatedResponse[UserOrderHistoryItem]:
        """Get user order history.

        Args:
            subaccount_addr: Subaccount address
            market_addr: Optional market address filter
            page_params: Optional pagination parameters

        Returns:
            Paginated order history
        """
        params: dict[str, Any] = {}
        if market_addr:
            params["market_addr"] = market_addr
        if page_params:
            if page_params.limit is not None:
                params["limit"] = page_params.limit
            if page_params.offset is not None:
                params["offset"] = page_params.offset
        resp = await self._get(f"/order-history/{subaccount_addr}", params)
        return PaginatedResponse[UserOrderHistoryItem](
            items=[UserOrderHistoryItem(**o) for o in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    # --- User Trade History ---

    async def get_trade_history(
        self,
        subaccount_addr: str,
        page_params: PageParams | None = None,
    ) -> PaginatedResponse[UserTradeHistoryItem]:
        """Get user trade history.

        Args:
            subaccount_addr: Subaccount address
            page_params: Optional pagination parameters

        Returns:
            Paginated trade history
        """
        params: dict[str, Any] = {}
        if page_params:
            if page_params.limit is not None:
                params["limit"] = page_params.limit
            if page_params.offset is not None:
                params["offset"] = page_params.offset
        resp = await self._get(f"/trade-history/{subaccount_addr}", params)
        return PaginatedResponse[UserTradeHistoryItem](
            items=[UserTradeHistoryItem(**t) for t in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    # --- User Funding History ---

    async def get_funding_history(
        self,
        subaccount_addr: str,
        market_addr: str | None = None,
        page_params: PageParams | None = None,
    ) -> PaginatedResponse[UserFundingHistoryItem]:
        """Get user funding history.

        Args:
            subaccount_addr: Subaccount address
            market_addr: Optional market address filter
            page_params: Optional pagination parameters

        Returns:
            Paginated funding history
        """
        params: dict[str, Any] = {}
        if market_addr:
            params["market_addr"] = market_addr
        if page_params:
            if page_params.limit is not None:
                params["limit"] = page_params.limit
            if page_params.offset is not None:
                params["offset"] = page_params.offset
        resp = await self._get(f"/funding-history/{subaccount_addr}", params)
        return PaginatedResponse[UserFundingHistoryItem](
            items=[UserFundingHistoryItem(**f) for f in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    # --- User Fund History ---

    async def get_fund_history(
        self,
        subaccount_addr: str,
        page_params: PageParams | None = None,
    ) -> PaginatedResponse[UserFundHistoryItem]:
        """Get user deposit/withdrawal history.

        Args:
            subaccount_addr: Subaccount address
            page_params: Optional pagination parameters

        Returns:
            Paginated fund history
        """
        params: dict[str, Any] = {}
        if page_params:
            if page_params.limit is not None:
                params["limit"] = page_params.limit
            if page_params.offset is not None:
                params["offset"] = page_params.offset
        resp = await self._get(f"/fund-history/{subaccount_addr}", params)
        return PaginatedResponse[UserFundHistoryItem](
            items=[UserFundHistoryItem(**f) for f in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    # --- User Subaccounts ---

    async def get_subaccounts(self, owner_addr: str) -> list[UserSubaccount]:
        """Get user subaccounts.

        Args:
            owner_addr: Owner account address

        Returns:
            List of subaccounts
        """
        resp = await self._get(f"/subaccounts/{owner_addr}")
        return [UserSubaccount(**s) for s in resp.data]

    # --- Delegations ---

    async def get_delegations(self, subaccount_addr: str) -> list[Delegation]:
        """Get delegations for a subaccount.

        Args:
            subaccount_addr: Subaccount address

        Returns:
            List of delegations
        """
        resp = await self._get(f"/delegations/{subaccount_addr}")
        return [Delegation(**d) for d in resp.data]

    # --- Vaults ---

    async def get_vaults(
        self,
        filters: dict[str, Any] | None = None,
    ) -> VaultsResponse:
        """Get vaults with optional filters.

        Args:
            filters: Optional filters (page_params, sort_params, search_term)

        Returns:
            Vaults response
        """
        params: dict[str, Any] = {}
        if filters:
            page_params = filters.get("page_params")
            sort_params = filters.get("sort_params")
            search_params = filters.get("search_params")

            if page_params and isinstance(page_params, PageParams):
                if page_params.limit is not None:
                    params["limit"] = page_params.limit
                if page_params.offset is not None:
                    params["offset"] = page_params.offset
            if sort_params and isinstance(sort_params, SortParams):
                if sort_params.sort_key:
                    params["sort_key"] = sort_params.sort_key
                if sort_params.sort_dir:
                    params["sort_dir"] = sort_params.sort_dir.value
            if search_params and isinstance(search_params, SearchTermParams):
                if search_params.search_term:
                    params["search_term"] = search_params.search_term

        resp = await self._get("/vaults", params)
        return VaultsResponse(
            items=[Vault(**v) for v in resp.data["items"]],
            total_count=resp.data["total_count"],
            total_value_locked=resp.data["total_value_locked"],
            total_volume=resp.data["total_volume"],
        )

    async def get_user_owned_vaults(
        self, account_addr: str, page_params: PageParams | None = None
    ) -> PaginatedResponse[UserOwnedVault]:
        """Get vaults owned by a user.

        Args:
            account_addr: Account address
            page_params: Optional pagination parameters

        Returns:
            Paginated user-owned vaults
        """
        params: dict[str, Any] = {}
        if page_params:
            if page_params.limit is not None:
                params["limit"] = page_params.limit
            if page_params.offset is not None:
                params["offset"] = page_params.offset
        resp = await self._get(f"/vaults/owned/{account_addr}", params)
        return PaginatedResponse[UserOwnedVault](
            items=[UserOwnedVault(**v) for v in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    async def get_vault_performance(self, account_addr: str) -> list[UserPerformanceOnVault]:
        """Get user performance on vaults.

        Args:
            account_addr: Account address

        Returns:
            List of vault performances
        """
        resp = await self._get(f"/vaults/performance/{account_addr}")
        return [UserPerformanceOnVault(**p) for p in resp.data]

    # --- Analytics ---

    async def get_leaderboard(
        self, filters: dict[str, Any] | None = None
    ) -> PaginatedResponse[LeaderboardItem]:
        """Get leaderboard.

        Args:
            filters: Optional filters (page_params, sort_params, search_term)

        Returns:
            Paginated leaderboard
        """
        params: dict[str, Any] = {}
        if filters:
            page_params = filters.get("page_params")
            sort_params = filters.get("sort_params")
            search_params = filters.get("search_params")

            if page_params and isinstance(page_params, PageParams):
                if page_params.limit is not None:
                    params["limit"] = page_params.limit
                if page_params.offset is not None:
                    params["offset"] = page_params.offset
            if sort_params and isinstance(sort_params, SortParams):
                if sort_params.sort_key:
                    params["sort_key"] = sort_params.sort_key
                if sort_params.sort_dir:
                    params["sort_dir"] = sort_params.sort_dir.value
            if search_params and isinstance(search_params, SearchTermParams):
                if search_params.search_term:
                    params["search_term"] = search_params.search_term

        resp = await self._get("/leaderboard", params)
        return PaginatedResponse[LeaderboardItem](
            items=[LeaderboardItem(**i) for i in resp.data["items"]],
            total_count=resp.data["total_count"],
        )

    async def get_portfolio_chart(self, subaccount_addr: str, interval: str = "1d") -> list[PortfolioChartData]:
        """Get portfolio chart data.

        Args:
            subaccount_addr: Subaccount address
            interval: Data interval

        Returns:
            List of portfolio chart data points
        """
        resp = await self._get(f"/portfolio-chart/{subaccount_addr}", {"interval": interval})
        return [PortfolioChartData(**d) for d in resp.data]
