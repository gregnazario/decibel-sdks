"""Tests for write client: arg validation, payload construction, subaccount resolution."""

from __future__ import annotations

import pytest

from decibel_sdk.client.write import (
    CancelOrderArgs,
    ConfigureMarketSettingsArgs,
    DecibelWriteClient,
    DelegateTradingArgs,
    PlaceOrderArgs,
    PlaceTpSlArgs,
    PlaceTwapOrderArgs,
    TransactionResponse,
)
from decibel_sdk.config import DecibelConfig, Deployment, Network
from decibel_sdk.errors import ConfigError, TransactionError, ValidationError
from decibel_sdk.models.common import TimeInForce


@pytest.fixture
def config() -> DecibelConfig:
    return DecibelConfig(
        network=Network.TESTNET,
        trading_http_url="https://api.testnet.decibel.trade",
        trading_ws_url="wss://api.testnet.decibel.trade/ws",
        fullnode_url="https://fullnode.testnet.aptoslabs.com/v1",
        deployment=Deployment(
            package="0x" + "aa" * 32,
            usdc="0x" + "bb" * 32,
            testc="0x" + "cc" * 32,
            perp_engine_global="0x" + "dd" * 32,
        ),
    )


@pytest.fixture
def private_key() -> str:
    return "0x" + "ab" * 32


@pytest.fixture
def account_addr() -> str:
    return "0x" + "11" * 32


class TestWriteClientInit:
    def test_basic_init(self, config: DecibelConfig, private_key: str, account_addr: str) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        assert client.account_address == account_addr

    def test_init_strips_0x_prefix(self, config: DecibelConfig, account_addr: str) -> None:
        key_no_prefix = "ab" * 32
        key_with_prefix = "0x" + key_no_prefix

        c1 = DecibelWriteClient(config, key_no_prefix, account_addr)
        c2 = DecibelWriteClient(config, key_with_prefix, account_addr)
        assert c1._private_key == c2._private_key

    def test_invalid_hex_raises_config_error(
        self, config: DecibelConfig, account_addr: str
    ) -> None:
        with pytest.raises(ConfigError, match="Invalid private key hex"):
            DecibelWriteClient(config, "not_hex!", account_addr)

    def test_skip_simulate_and_no_fee_payer(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(
            config,
            private_key,
            account_addr,
            skip_simulate=True,
            no_fee_payer=True,
        )
        assert client._skip_simulate is True
        assert client._no_fee_payer is True


class TestSubaccountResolution:
    def test_get_primary_subaccount(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        sub = client.get_primary_subaccount_addr()
        # Should return a hex string (64 hex chars with 0x prefix)
        assert sub.startswith("0x")
        assert len(sub) == 66  # 0x + 64 hex chars

    def test_resolve_uses_explicit_addr(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        explicit = "0x" + "ff" * 32
        assert client._resolve_subaccount(explicit) == explicit

    def test_resolve_uses_primary_when_none(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        resolved = client._resolve_subaccount(None)
        assert resolved == client.get_primary_subaccount_addr()


class TestPayloadConstruction:
    def test_build_payload(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        payload = client._build_payload(
            "0xabc::module::function",
            type_args=["0x1::coin::CoinStore"],
            args=["arg1", 42],
        )
        assert payload.function == "0xabc::module::function"
        assert payload.type_arguments == ["0x1::coin::CoinStore"]
        assert payload.arguments == ["arg1", 42]

    def test_build_payload_defaults(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        payload = client._build_payload("0xabc::module::function")
        assert payload.type_arguments == []
        assert payload.arguments == []


class TestPlaceOrderArgs:
    def test_defaults(self) -> None:
        args = PlaceOrderArgs(
            market_name="BTC-USD",
            price=45000.0,
            size=1.0,
            is_buy=True,
            time_in_force=TimeInForce.GOOD_TILL_CANCELED,
        )
        assert args.is_reduce_only is False
        assert args.client_order_id is None
        assert args.stop_price is None
        assert args.tick_size is None
        assert args.builder_addr is None

    def test_all_fields(self) -> None:
        args = PlaceOrderArgs(
            market_name="ETH-USD",
            price=3000.0,
            size=10.0,
            is_buy=False,
            time_in_force=TimeInForce.POST_ONLY,
            is_reduce_only=True,
            client_order_id="my-order-1",
            stop_price=2900.0,
            tp_trigger_price=3100.0,
            tp_limit_price=3090.0,
            sl_trigger_price=2800.0,
            sl_limit_price=2810.0,
            builder_addr="0xbuilder",
            builder_fee=100,
            subaccount_addr="0xsub",
            tick_size=0.5,
        )
        assert args.market_name == "ETH-USD"
        assert args.time_in_force == TimeInForce.POST_ONLY


class TestCancelOrderArgs:
    def test_with_market_name(self) -> None:
        args = CancelOrderArgs(order_id="123", market_name="BTC-USD")
        assert args.market_addr is None

    def test_with_market_addr(self) -> None:
        args = CancelOrderArgs(order_id="123", market_addr="0xmarket")
        assert args.market_name is None

    def test_validation_requires_market(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        args = CancelOrderArgs(order_id="123")
        with pytest.raises(ValidationError, match="market_name or market_addr"):
            # cancel_order will also raise TransactionError from submit,
            # but ValidationError should come first
            import asyncio

            asyncio.get_event_loop().run_until_complete(client.cancel_order(args))


class TestPlaceTwapOrderArgs:
    def test_defaults(self) -> None:
        args = PlaceTwapOrderArgs(
            market_name="BTC-USD",
            size=1.0,
            is_buy=True,
            twap_frequency_seconds=60,
            twap_duration_seconds=3600,
        )
        assert args.is_reduce_only is False
        assert args.client_order_id is None
        assert args.subaccount_addr is None


class TestPlaceTpSlArgs:
    def test_partial_tp_sl(self) -> None:
        args = PlaceTpSlArgs(
            market_addr="0xmarket",
            tp_trigger_price=50000.0,
            tp_limit_price=49900.0,
        )
        assert args.sl_trigger_price is None
        assert args.sl_size is None


class TestConfigureMarketSettingsArgs:
    def test_fields(self) -> None:
        args = ConfigureMarketSettingsArgs(
            market_addr="0xmarket",
            subaccount_addr="0xsub",
            is_cross=True,
            user_leverage=10,
        )
        assert args.is_cross is True
        assert args.user_leverage == 10


class TestDelegateTradingArgs:
    def test_optional_expiration(self) -> None:
        args = DelegateTradingArgs(
            subaccount_addr="0xsub",
            account_to_delegate_to="0xdelegate",
        )
        assert args.expiration_timestamp_secs is None


class TestTransactionResponse:
    def test_basic(self) -> None:
        resp = TransactionResponse(hash="0xabc", success=True)
        assert resp.hash == "0xabc"
        assert resp.success is True
        assert resp.vm_status is None
        assert resp.events == []

    def test_with_events(self) -> None:
        resp = TransactionResponse(
            hash="0xdef",
            success=False,
            vm_status="MOVE_ABORT",
            events=[{"type": "order_placed", "data": {}}],
        )
        assert resp.vm_status == "MOVE_ABORT"
        assert len(resp.events) == 1


class TestWriteOperations:
    """Test that write operations build correct payloads.

    Since _submit_transaction raises TransactionError (not yet implemented),
    we verify payloads by monkey-patching _submit_transaction.
    """

    async def test_create_subaccount_payload(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.create_subaccount()
        assert len(captured) == 1
        assert "create_new_subaccount" in captured[0].function
        assert captured[0].arguments == []

    async def test_deposit_payload(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.deposit(1000)
        assert len(captured) == 1
        assert "deposit_to_subaccount_at" in captured[0].function
        # args: [subaccount_addr, usdc_addr, amount]
        assert captured[0].arguments[1] == "0x" + "bb" * 32
        assert captured[0].arguments[2] == 1000

    async def test_withdraw_payload(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.withdraw(500, subaccount_addr="0xexplicit_sub")
        assert "withdraw_from_subaccount" in captured[0].function
        assert captured[0].arguments[0] == "0xexplicit_sub"
        assert captured[0].arguments[2] == 500

    async def test_place_order_payload(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True, events=[])

        client._submit_transaction = capture  # type: ignore[assignment]

        result = await client.place_order(
            PlaceOrderArgs(
                market_name="BTC-USD",
                price=45000.0,
                size=1.0,
                is_buy=True,
                time_in_force=TimeInForce.GOOD_TILL_CANCELED,
            )
        )
        assert "place_order_to_subaccount" in captured[0].function
        assert result.success is True
        assert result.transaction_hash == "0xtest"

    async def test_place_order_with_tick_size(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True, events=[])

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.place_order(
            PlaceOrderArgs(
                market_name="BTC-USD",
                price=45123.45,
                size=1.0,
                is_buy=False,
                time_in_force=TimeInForce.GOOD_TILL_CANCELED,
                tick_size=0.5,
            )
        )
        # Price should be rounded down for sell (is_buy=False)
        rounded_price = captured[0].arguments[2]
        assert rounded_price == 45123.0

    async def test_cancel_order_with_market_name(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.cancel_order(CancelOrderArgs(order_id="order-123", market_name="BTC-USD"))
        assert "cancel_order_to_subaccount" in captured[0].function
        assert captured[0].arguments[1] == "order-123"

    async def test_cancel_order_with_market_addr(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.cancel_order(
            CancelOrderArgs(order_id="order-456", market_addr="0xdirect_market")
        )
        assert captured[0].arguments[2] == "0xdirect_market"

    async def test_cancel_order_no_market_raises(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        with pytest.raises(ValidationError, match="market_name or market_addr"):
            await client.cancel_order(CancelOrderArgs(order_id="123"))

    async def test_cancel_client_order(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtest", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.cancel_client_order("client-1", "ETH-USD")
        assert "cancel_client_order_to_subaccount" in captured[0].function
        assert captured[0].arguments[1] == "client-1"

    async def test_place_twap_order(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xtwap", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        result = await client.place_twap_order(
            PlaceTwapOrderArgs(
                market_name="BTC-USD",
                size=5.0,
                is_buy=True,
                twap_frequency_seconds=60,
                twap_duration_seconds=3600,
            )
        )
        assert "place_twap_order_to_subaccount" in captured[0].function
        assert result.success is True
        assert result.transaction_hash == "0xtwap"

    async def test_delegate_trading(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xdel", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.delegate_trading_to(
            DelegateTradingArgs(
                subaccount_addr="0xsub",
                account_to_delegate_to="0xdelegate",
                expiration_timestamp_secs=9999999,
            )
        )
        assert "delegate_trading_to_for_subaccount" in captured[0].function
        assert captured[0].arguments[0] == "0xsub"
        assert captured[0].arguments[1] == "0xdelegate"
        assert captured[0].arguments[2] == 9999999

    async def test_vault_operations(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xvault", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.activate_vault("0xvault_addr")
        assert "activate_vault" in captured[0].function
        assert captured[0].arguments == ["0xvault_addr"]

    async def test_deposit_to_vault(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xdep", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.deposit_to_vault("0xvault", 5000)
        assert "contribute_to_vault" in captured[0].function
        assert captured[0].arguments == ["0xvault", 5000]

    async def test_withdraw_from_vault(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        captured: list = []

        async def capture(payload):
            captured.append(payload)
            return TransactionResponse(hash="0xwd", success=True)

        client._submit_transaction = capture  # type: ignore[assignment]

        await client.withdraw_from_vault("0xvault", 100)
        assert "redeem_from_vault" in captured[0].function
        assert captured[0].arguments == ["0xvault", 100]

    async def test_submit_not_implemented_raises(
        self, config: DecibelConfig, private_key: str, account_addr: str
    ) -> None:
        client = DecibelWriteClient(config, private_key, account_addr)
        with pytest.raises(TransactionError, match="requires Aptos SDK"):
            await client.create_subaccount()
