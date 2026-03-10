"""Tests for WebSocket manager and subscription patterns."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from decibel_sdk.client.ws import Subscription, WebSocketManager, WsReadyState
from decibel_sdk.config import DecibelConfig, Deployment, Network
from decibel_sdk.errors import WebSocketError
from decibel_sdk.models.market import MarketPrice


@pytest.fixture
def config() -> DecibelConfig:
    return DecibelConfig(
        network=Network.TESTNET,
        trading_http_url="https://test.example.com",
        trading_ws_url="wss://test.example.com/ws",
        fullnode_url="https://fullnode.example.com/v1",
        deployment=Deployment(
            package="0xabc123",
            usdc="0xusdc",
            testc="0xtestc",
            perp_engine_global="0xperp",
        ),
    )


class FakeWsConnection:
    """Simulates a websockets ClientConnection for testing."""

    def __init__(self) -> None:
        self._incoming: asyncio.Queue[str] = asyncio.Queue()
        self._sent: list[str] = []
        self._closed = False

    async def send(self, msg: str) -> None:
        self._sent.append(msg)

    async def close(self) -> None:
        self._closed = True
        # Push sentinel to unblock the async iterator
        await self._incoming.put(None)  # type: ignore[arg-type]

    def __aiter__(self) -> FakeWsConnection:
        return self

    async def __anext__(self) -> str:
        item = await self._incoming.get()
        if item is None:
            raise StopAsyncIteration
        return item

    async def push(self, data: dict) -> None:
        """Test helper: push a JSON message as if it came from the server."""
        await self._incoming.put(json.dumps(data))


class TestWsReadyState:
    def test_enum_values(self) -> None:
        assert WsReadyState.CONNECTING.value == "Connecting"
        assert WsReadyState.OPEN.value == "Open"
        assert WsReadyState.CLOSING.value == "Closing"
        assert WsReadyState.CLOSED.value == "Closed"


class TestSubscription:
    async def test_iterate_messages(self) -> None:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        sub: Subscription[str] = Subscription(queue)

        await queue.put("hello")
        await queue.put("world")
        await queue.put(None)  # sentinel to stop

        results = []
        async for msg in sub:
            results.append(msg)

        assert results == ["hello", "world"]

    async def test_stop_on_none(self) -> None:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        sub: Subscription[str] = Subscription(queue)

        await queue.put(None)
        results = []
        async for msg in sub:
            results.append(msg)
        assert results == []

    async def test_aclose(self) -> None:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        sub: Subscription[str] = Subscription(queue)

        await sub.aclose()
        with pytest.raises(StopAsyncIteration):
            await sub.__anext__()

    async def test_closed_after_none(self) -> None:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        sub: Subscription[str] = Subscription(queue)

        await queue.put(None)
        with pytest.raises(StopAsyncIteration):
            await sub.__anext__()
        # subsequent call also raises
        with pytest.raises(StopAsyncIteration):
            await sub.__anext__()


class TestWebSocketManager:
    async def test_initial_state(self, config: DecibelConfig) -> None:
        mgr = WebSocketManager(config)
        assert mgr.ready_state == WsReadyState.CLOSED

    async def test_connect_sets_open(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)
            await mgr.connect()
            assert mgr.ready_state == WsReadyState.OPEN
            await mgr.close()

    async def test_connect_with_api_key(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()
        connect_mock = AsyncMock(return_value=fake_ws)

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            connect_mock,
        ):
            mgr = WebSocketManager(config, api_key="test-key")
            await mgr.connect()
            # Verify the URL includes the API key
            call_url = connect_mock.call_args[0][0]
            assert "x-api-key=test-key" in call_url
            assert call_url.startswith("wss://test.example.com/ws?")
            await mgr.close()

    async def test_connect_failure_raises_websocket_error(self, config: DecibelConfig) -> None:
        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError("refused"),
        ):
            mgr = WebSocketManager(config)
            with pytest.raises(WebSocketError, match="refused"):
                await mgr.connect()
            assert mgr.ready_state == WsReadyState.CLOSED

    async def test_connect_idempotent(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()
        connect_mock = AsyncMock(return_value=fake_ws)

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            connect_mock,
        ):
            mgr = WebSocketManager(config)
            await mgr.connect()
            await mgr.connect()  # second call should be no-op
            assert connect_mock.call_count == 1
            await mgr.close()

    async def test_subscribe_sends_subscribe_message(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice):
                # Give the event loop a chance to process
                await asyncio.sleep(0.01)

                # Check that a subscribe message was sent
                assert len(fake_ws._sent) >= 1
                sub_msg = json.loads(fake_ws._sent[0])
                assert sub_msg["method"] == "subscribe"
                assert sub_msg["subscription"] == "marketPrice:BTC-USD"

            # After exiting, an unsubscribe should be sent
            await asyncio.sleep(0.01)
            unsub_msgs = [json.loads(m) for m in fake_ws._sent if "unsubscribe" in m]
            assert len(unsub_msgs) == 1
            assert unsub_msgs[0]["subscription"] == "marketPrice:BTC-USD"

            await mgr.close()

    async def test_subscribe_receives_typed_messages(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice) as sub:
                # Simulate server pushing a message
                await fake_ws.push(
                    {
                        "channel": "marketPrice:BTC-USD",
                        "data": {
                            "market": "BTC-USD",
                            "mark_px": 45000.5,
                            "mid_px": 44999.5,
                            "oracle_px": 44999.0,
                            "funding_rate_bps": 0.5,
                            "is_funding_positive": True,
                            "open_interest": 500.0,
                            "transaction_unix_ms": 1700000000000,
                        },
                    }
                )

                # Allow time for deserialization
                await asyncio.sleep(0.05)

                msg = await asyncio.wait_for(sub.__anext__(), timeout=1.0)
                assert isinstance(msg, MarketPrice)
                assert msg.market == "BTC-USD"
                assert msg.mark_px == 45000.5

            await mgr.close()

    async def test_subscribe_filters_by_channel(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            market_data = {
                "market": "BTC-USD",
                "mark_px": 45000.0,
                "mid_px": 44999.5,
                "oracle_px": 44999.0,
                "funding_rate_bps": 0.5,
                "is_funding_positive": True,
                "open_interest": 500.0,
                "transaction_unix_ms": 1700000000000,
            }

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice) as sub:
                # Push a message for a different channel — should not be delivered
                await fake_ws.push(
                    {
                        "channel": "marketPrice:ETH-USD",
                        "data": {**market_data, "market": "ETH-USD"},
                    }
                )

                # Push a message for the subscribed channel
                await fake_ws.push(
                    {
                        "channel": "marketPrice:BTC-USD",
                        "data": market_data,
                    }
                )

                await asyncio.sleep(0.05)

                msg = await asyncio.wait_for(sub.__anext__(), timeout=1.0)
                assert msg.market == "BTC-USD"

            await mgr.close()

    async def test_multiple_subscribers_same_topic(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            market_data = {
                "market": "BTC-USD",
                "mark_px": 45000.0,
                "mid_px": 44999.5,
                "oracle_px": 44999.0,
                "funding_rate_bps": 0.5,
                "is_funding_positive": True,
                "open_interest": 500.0,
                "transaction_unix_ms": 1700000000000,
            }

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice) as sub1:
                async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice) as sub2:
                    # Only one subscribe message should have been sent
                    sub_msgs = [m for m in fake_ws._sent if '"subscribe"' in m and "BTC-USD" in m]
                    assert len(sub_msgs) == 1

                    await fake_ws.push(
                        {
                            "channel": "marketPrice:BTC-USD",
                            "data": market_data,
                        }
                    )

                    await asyncio.sleep(0.05)

                    msg1 = await asyncio.wait_for(sub1.__anext__(), timeout=1.0)
                    msg2 = await asyncio.wait_for(sub2.__anext__(), timeout=1.0)
                    assert msg1.market == "BTC-USD"
                    assert msg2.market == "BTC-USD"

                # sub2 exited but sub1 still active — no unsubscribe yet
                unsub_msgs = [m for m in fake_ws._sent if '"unsubscribe"' in m]
                assert len(unsub_msgs) == 0

            # Now sub1 also exited — unsubscribe should be sent
            await asyncio.sleep(0.01)
            unsub_msgs = [m for m in fake_ws._sent if '"unsubscribe"' in m]
            assert len(unsub_msgs) == 1

            await mgr.close()

    async def test_close_signals_all_queues(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice):
                await mgr.close()
                assert mgr.ready_state == WsReadyState.CLOSED

    async def test_reset_sends_unsub_then_sub(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)
            await mgr.connect()

            await mgr.reset("marketPrice:BTC-USD")

            assert len(fake_ws._sent) == 2
            unsub = json.loads(fake_ws._sent[0])
            resub = json.loads(fake_ws._sent[1])
            assert unsub["method"] == "unsubscribe"
            assert unsub["subscription"] == "marketPrice:BTC-USD"
            assert resub["method"] == "subscribe"
            assert resub["subscription"] == "marketPrice:BTC-USD"

            await mgr.close()

    async def test_send_when_not_connected_raises(self, config: DecibelConfig) -> None:
        mgr = WebSocketManager(config)
        with pytest.raises(WebSocketError, match="Not connected"):
            await mgr._send("hello")

    async def test_malformed_json_ignored(self, config: DecibelConfig) -> None:
        fake_ws = FakeWsConnection()

        with patch(
            "decibel_sdk.client.ws.websockets.asyncio.client.connect",
            new_callable=AsyncMock,
            return_value=fake_ws,
        ):
            mgr = WebSocketManager(config)

            market_data = {
                "market": "BTC-USD",
                "mark_px": 45000.0,
                "mid_px": 44999.5,
                "oracle_px": 44999.0,
                "funding_rate_bps": 0.5,
                "is_funding_positive": True,
                "open_interest": 500.0,
                "transaction_unix_ms": 1700000000000,
            }

            async with mgr.subscribe("marketPrice:BTC-USD", MarketPrice) as sub:
                # Push malformed JSON — should be silently ignored
                await fake_ws._incoming.put("not valid json{{{")

                # Push a valid message after
                await fake_ws.push(
                    {
                        "channel": "marketPrice:BTC-USD",
                        "data": market_data,
                    }
                )

                await asyncio.sleep(0.05)

                msg = await asyncio.wait_for(sub.__anext__(), timeout=1.0)
                assert msg.market == "BTC-USD"

            await mgr.close()
