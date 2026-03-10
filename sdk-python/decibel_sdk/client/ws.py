"""WebSocket manager with AsyncIterator-based subscriptions."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum
from typing import Generic, TypeVar

import websockets
import websockets.asyncio.client
from pydantic import TypeAdapter

from decibel_sdk.config import DecibelConfig
from decibel_sdk.errors import WebSocketError
from decibel_sdk.models.ws import WsSubscribeRequest

T = TypeVar("T")

logger = logging.getLogger(__name__)


class WsReadyState(str, Enum):
    CONNECTING = "Connecting"
    OPEN = "Open"
    CLOSING = "Closing"
    CLOSED = "Closed"


class Subscription(Generic[T]):
    """AsyncIterator-backed subscription for WebSocket messages.

    Usage::

        async with manager.subscribe("topic", MessageType) as sub:
            async for msg in sub:
                print(msg)
    """

    def __init__(self, queue: asyncio.Queue[T | None]) -> None:
        self._queue = queue
        self._closed = False

    def __aiter__(self) -> Subscription[T]:
        return self

    async def __anext__(self) -> T:
        if self._closed:
            raise StopAsyncIteration
        item = await self._queue.get()
        if item is None:
            self._closed = True
            raise StopAsyncIteration
        return item

    async def aclose(self) -> None:
        self._closed = True


class WebSocketManager:
    """Single-connection, multiplexed WebSocket manager."""

    def __init__(
        self,
        config: DecibelConfig,
        api_key: str | None = None,
    ) -> None:
        self._config = config
        self._api_key = api_key
        self._state = WsReadyState.CLOSED
        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._subscriptions: dict[str, list[asyncio.Queue[object]]] = {}
        self._read_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    @property
    def ready_state(self) -> WsReadyState:
        return self._state

    async def connect(self) -> None:
        async with self._lock:
            if self._state in (WsReadyState.OPEN, WsReadyState.CONNECTING):
                return
            self._state = WsReadyState.CONNECTING

        ws_url = self._config.trading_ws_url
        if self._api_key:
            sep = "&" if "?" in ws_url else "?"
            ws_url = f"{ws_url}{sep}x-api-key={self._api_key}"

        try:
            self._ws = await websockets.asyncio.client.connect(ws_url)
        except Exception as exc:
            self._state = WsReadyState.CLOSED
            raise WebSocketError(str(exc)) from exc

        self._state = WsReadyState.OPEN
        self._read_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                channel = msg.get("channel")
                data = msg.get("data", msg)
                if channel and channel in self._subscriptions:
                    for queue in self._subscriptions[channel]:
                        with contextlib.suppress(asyncio.QueueFull):
                            queue.put_nowait(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as exc:
            logger.debug("WS read loop error: %s", exc)
        finally:
            self._state = WsReadyState.CLOSED

    @asynccontextmanager
    async def subscribe(self, topic: str, message_type: type[T]) -> AsyncIterator[Subscription[T]]:
        """Subscribe to a topic and yield an async iterator of typed messages.

        Usage::

            async with ws.subscribe("marketPrice:BTC-USD", MarketPriceWsMessage) as sub:
                async for msg in sub:
                    print(msg.mark_px)
        """
        await self.connect()

        adapter = TypeAdapter(message_type)
        raw_queue: asyncio.Queue[object] = asyncio.Queue(maxsize=256)
        typed_queue: asyncio.Queue[T | None] = asyncio.Queue(maxsize=256)

        is_new = topic not in self._subscriptions or not self._subscriptions[topic]
        self._subscriptions.setdefault(topic, []).append(raw_queue)

        if is_new:
            await self._send(WsSubscribeRequest.subscribe(topic).model_dump_json())

        # Background task to deserialize messages
        async def _deserialize() -> None:
            while True:
                raw = await raw_queue.get()
                if raw is None:
                    await typed_queue.put(None)
                    break
                try:
                    if isinstance(raw, dict):
                        parsed = adapter.validate_python(raw)
                    else:
                        parsed = adapter.validate_json(json.dumps(raw))
                    await typed_queue.put(parsed)
                except Exception:
                    pass

        deser_task = asyncio.create_task(_deserialize())

        try:
            yield Subscription(typed_queue)
        finally:
            # Clean up
            await raw_queue.put(None)
            deser_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await deser_task

            if topic in self._subscriptions:
                queues = self._subscriptions[topic]
                if raw_queue in queues:
                    queues.remove(raw_queue)
                if not queues:
                    del self._subscriptions[topic]
                    with contextlib.suppress(Exception):
                        await self._send(WsSubscribeRequest.unsubscribe(topic).model_dump_json())

    async def _send(self, msg: str) -> None:
        if self._ws is None:
            raise WebSocketError("Not connected")
        await self._ws.send(msg)

    async def reset(self, topic: str) -> None:
        await self._send(WsSubscribeRequest.unsubscribe(topic).model_dump_json())
        await self._send(WsSubscribeRequest.subscribe(topic).model_dump_json())

    async def close(self) -> None:
        self._state = WsReadyState.CLOSING

        # Signal all queues to stop
        for queues in self._subscriptions.values():
            for q in queues:
                with contextlib.suppress(asyncio.QueueFull):
                    q.put_nowait(None)
        self._subscriptions.clear()

        if self._ws is not None:
            await self._ws.close()
            self._ws = None

        if self._read_task is not None:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        self._state = WsReadyState.CLOSED
