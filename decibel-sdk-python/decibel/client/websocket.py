"""WebSocket client for real-time data streaming."""

import asyncio
import json
from typing import Any, Callable

import websockets
from websockets.exceptions import ConnectionClosed

from ..config import DecibelConfig
from ..errors import WebSocketError
from ..models.account import (
    AccountOverview,
    UserFundingHistoryItem,
    UserOpenOrder,
    UserOrderHistoryItem,
    UserPosition,
    UserTradeHistoryItem,
)
from ..models.enums import CandlestickInterval
from ..models.market import Candlestick, MarketDepth, MarketPrice, MarketTrade
from ..models.order import UserActiveTwap


Callback = Callable[[Any], None]


class WebSocketManager:
    """WebSocket connection manager for real-time data streaming.

    Attributes:
        config: SDK configuration
        api_key: Optional API key for authentication
    """

    def __init__(
        self,
        config: DecibelConfig,
        api_key: str | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize WebSocket manager.

        Args:
            config: SDK configuration
            api_key: Optional API key for authenticated connections
            on_error: Optional callback for WebSocket errors
        """
        self._config = config
        self._api_key = api_key
        self._on_error = on_error
        self._ws: Any | None = None
        self._subscriptions: dict[str, list[Callback]] = {}
        self._connected = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._receive_task: asyncio.Task[None] | None = None
        self._should_reconnect = True

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        if self._connected:
            return

        self._should_reconnect = True
        await self._connect_with_retry()

    async def _connect_with_retry(self) -> None:
        """Connect with exponential backoff retry."""
        while self._should_reconnect:
            try:
                # Build WebSocket URL
                url = self._config.trading_ws_url
                if self._api_key:
                    # Add API key as query parameter
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}x-api-key={self._api_key}"

                # Connect
                self._ws = await websockets.connect(url)

                self._connected = True
                self._reconnect_delay = 1.0  # Reset delay on successful connection

                # Resubscribe to all subscriptions
                for topic in list(self._subscriptions.keys()):
                    await self._send_subscribe(topic)

                # Start receive loop
                self._receive_task = asyncio.create_task(self._receive_loop())
                return

            except Exception as e:
                self._connected = False
                if self._on_error:
                    self._on_error(f"WebSocket connection failed: {e}")

                if not self._should_reconnect:
                    raise WebSocketError(f"Failed to connect: {e}", cause=e) from e

                # Exponential backoff
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self._should_reconnect = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._connected = False
        self._subscriptions.clear()

    async def _send_json(self, data: dict[str, Any]) -> None:
        """Send JSON data.

        Args:
            data: Data to send

        Raises:
            WebSocketError: If not connected
        """
        if not self._ws or not self._connected:
            raise WebSocketError("WebSocket not connected")

        try:
            await self._ws.send(json.dumps(data))
        except Exception as e:
            self._connected = False
            raise WebSocketError(f"Failed to send message: {e}", cause=e) from e

    async def _send_subscribe(self, subscription: str) -> None:
        """Send subscribe message.

        Args:
            subscription: Subscription topic
        """
        await self._send_json({"method": "subscribe", "subscription": subscription})

    async def _send_unsubscribe(self, subscription: str) -> None:
        """Send unsubscribe message.

        Args:
            subscription: Subscription topic
        """
        await self._send_json({"method": "unsubscribe", "subscription": subscription})

    async def _receive_loop(self) -> None:
        """Receive and dispatch messages."""
        while self._connected and self._ws:
            try:
                message = await self._ws.recv()
                data = json.loads(message)
                await self._handle_message(data)

            except ConnectionClosed:
                self._connected = False
                if self._should_reconnect:
                    await self._connect_with_retry()
                else:
                    break

            except Exception as e:
                if self._on_error:
                    self._on_error(f"WebSocket receive error: {e}")
                if not self._connected:
                    break

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming message.

        Args:
            data: Message data
        """
        channel = data.get("channel")
        if not channel:
            return

        callbacks = self._subscriptions.get(channel, [])
        message_data = data.get("data")

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message_data)
                else:
                    callback(message_data)
            except Exception as e:
                if self._on_error:
                    self._on_error(f"Callback error for {channel}: {e}")

    async def subscribe_account_overview(
        self, subaccount_addr: str, callback: Callable[[AccountOverview], Any]
    ) -> None:
        """Subscribe to account overview updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"accountOverview:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_positions(
        self, subaccount_addr: str, callback: Callable[[list[UserPosition]], Any]
    ) -> None:
        """Subscribe to user position updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userPositions:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_open_orders(
        self, subaccount_addr: str, callback: Callable[[list[UserOpenOrder]], Any]
    ) -> None:
        """Subscribe to user open orders updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userOpenOrders:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_order_updates(
        self, subaccount_addr: str, callback: Callable[[Any], Any]
    ) -> None:
        """Subscribe to order status updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"orderUpdate:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_order_history(
        self, subaccount_addr: str, callback: Callable[[list[UserOrderHistoryItem]], Any]
    ) -> None:
        """Subscribe to user order history updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userOrderHistory:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_trade_history(
        self, subaccount_addr: str, callback: Callable[[list[UserTradeHistoryItem]], Any]
    ) -> None:
        """Subscribe to user trade history updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userTradeHistory:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_funding_history(
        self, subaccount_addr: str, callback: Callable[[list[UserFundingHistoryItem]], Any]
    ) -> None:
        """Subscribe to user funding history updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userFundingRateHistory:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_market_depth(
        self, market_name: str, agg_size: int, callback: Callable[[MarketDepth], Any]
    ) -> None:
        """Subscribe to market depth updates.

        Args:
            market_name: Market name
            agg_size: Aggregation size
            callback: Callback function for updates
        """
        topic = f"marketDepth:{market_name}"
        # Store with agg_size as part of the key for unsubscribe
        full_topic = f"{topic}:{agg_size}"
        self._subscriptions.setdefault(full_topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(full_topic)

    async def subscribe_market_price(
        self, market_name: str, callback: Callable[[MarketPrice], Any]
    ) -> None:
        """Subscribe to market price updates.

        Args:
            market_name: Market name
            callback: Callback function for updates
        """
        topic = f"marketPrice:{market_name}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_all_market_prices(
        self, callback: Callable[[list[MarketPrice]], Any]
    ) -> None:
        """Subscribe to all market price updates.

        Args:
            callback: Callback function for updates
        """
        topic = "allMarketPrices"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_market_trades(
        self, market_name: str, callback: Callable[[list[MarketTrade]], Any]
    ) -> None:
        """Subscribe to market trades.

        Args:
            market_name: Market name
            callback: Callback function for updates
        """
        topic = f"marketTrades:{market_name}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_candlesticks(
        self, market_name: str, interval: CandlestickInterval, callback: Callable[[Candlestick], Any]
    ) -> None:
        """Subscribe to candlestick updates.

        Args:
            market_name: Market name
            interval: Candlestick interval
            callback: Callback function for updates
        """
        topic = f"marketCandlestick:{market_name}:{interval.value}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def subscribe_user_active_twaps(
        self, subaccount_addr: str, callback: Callable[[list[UserActiveTwap]], Any]
    ) -> None:
        """Subscribe to user active TWAP order updates.

        Args:
            subaccount_addr: Subaccount address
            callback: Callback function for updates
        """
        topic = f"userActiveTwaps:{subaccount_addr}"
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._connected:
            await self._send_subscribe(topic)

    async def unsubscribe(self, subscription: str) -> None:
        """Unsubscribe from a topic.

        Args:
            subscription: Subscription topic to unsubscribe
        """
        if subscription in self._subscriptions:
            del self._subscriptions[subscription]
            if self._connected:
                await self._send_unsubscribe(subscription)

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected.

        Returns:
            True if connected
        """
        return self._connected
