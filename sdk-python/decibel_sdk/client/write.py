"""Write client for transaction building, signing, and submission."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

import httpx

from decibel_sdk.config import DecibelConfig
from decibel_sdk.errors import (
    ConfigError,
    TransactionError,
    ValidationError,
)
from decibel_sdk.gas.manager import GasPriceManager
from decibel_sdk.models.common import PlaceOrderResult, TimeInForce, TwapOrderResult
from decibel_sdk.transaction.builder import TransactionPayload
from decibel_sdk.utils.address import get_market_addr, get_primary_subaccount_addr
from decibel_sdk.utils.events import extract_order_id_from_events
from decibel_sdk.utils.price import round_to_tick_size

# --- Arg dataclasses ---


@dataclass
class PlaceOrderArgs:
    market_name: str
    price: float
    size: float
    is_buy: bool
    time_in_force: TimeInForce
    is_reduce_only: bool = False
    client_order_id: str | None = None
    stop_price: float | None = None
    tp_trigger_price: float | None = None
    tp_limit_price: float | None = None
    sl_trigger_price: float | None = None
    sl_limit_price: float | None = None
    builder_addr: str | None = None
    builder_fee: int | None = None
    subaccount_addr: str | None = None
    tick_size: float | None = None


@dataclass
class CancelOrderArgs:
    order_id: str
    market_name: str | None = None
    market_addr: str | None = None
    subaccount_addr: str | None = None


@dataclass
class PlaceTwapOrderArgs:
    market_name: str
    size: float
    is_buy: bool
    twap_frequency_seconds: int
    twap_duration_seconds: int
    is_reduce_only: bool = False
    client_order_id: str | None = None
    builder_address: str | None = None
    builder_fees: int | None = None
    subaccount_addr: str | None = None


@dataclass
class PlaceTpSlArgs:
    market_addr: str
    tp_trigger_price: float | None = None
    tp_limit_price: float | None = None
    tp_size: float | None = None
    sl_trigger_price: float | None = None
    sl_limit_price: float | None = None
    sl_size: float | None = None
    subaccount_addr: str | None = None
    tick_size: float | None = None


@dataclass
class ConfigureMarketSettingsArgs:
    market_addr: str
    subaccount_addr: str
    is_cross: bool
    user_leverage: int


@dataclass
class DelegateTradingArgs:
    subaccount_addr: str
    account_to_delegate_to: str
    expiration_timestamp_secs: int | None = None


# --- Transaction Response ---


@dataclass
class TransactionResponse:
    hash: str
    success: bool
    vm_status: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


# --- Write Client ---


class DecibelWriteClient:
    """Async client for building and submitting Decibel transactions."""

    def __init__(
        self,
        config: DecibelConfig,
        private_key_hex: str,
        account_address: str,
        skip_simulate: bool = False,
        no_fee_payer: bool = False,
        node_api_key: str | None = None,
        gas_price_manager: GasPriceManager | None = None,
        time_delta_ms: int = 0,
    ) -> None:
        config.model_dump()  # triggers validation

        key_hex = private_key_hex.removeprefix("0x")
        try:
            self._private_key = bytes.fromhex(key_hex)
        except ValueError as exc:
            raise ConfigError(f"Invalid private key hex: {exc}") from exc

        self._config = config
        self._account_address = account_address
        self._skip_simulate = skip_simulate
        self._no_fee_payer = no_fee_payer
        self._gas_price_manager = gas_price_manager
        self._time_delta_ms = time_delta_ms

        headers: dict[str, str] = {}
        if node_api_key:
            headers["x-api-key"] = node_api_key
        self._http = httpx.AsyncClient(http2=True, headers=headers)

    async def __aenter__(self) -> DecibelWriteClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    @property
    def account_address(self) -> str:
        return self._account_address

    def get_primary_subaccount_addr(self) -> str:
        return get_primary_subaccount_addr(
            self._account_address,
            self._config.compat_version.value if self._config.compat_version else "v0.4",
            self._config.deployment.package,
        )

    def _resolve_subaccount(self, subaccount_addr: str | None) -> str:
        return subaccount_addr or self.get_primary_subaccount_addr()

    def _get_market_addr(self, market_name: str) -> str:
        return get_market_addr(
            market_name,
            self._config.deployment.perp_engine_global,
        )

    def _build_payload(
        self,
        function: str,
        type_args: list[str] | None = None,
        args: list[Any] | None = None,
    ) -> TransactionPayload:
        return TransactionPayload(
            function=function,
            type_arguments=type_args or [],
            arguments=args or [],
        )

    async def _submit_transaction(self, payload: TransactionPayload) -> TransactionResponse:
        # In a real implementation, this would:
        # 1. Build the transaction using Aptos BCS serialization
        # 2. Simulate if not skip_simulate
        # 3. Sign with Ed25519 private key (self._private_key)
        # 4. Submit via fee payer or directly
        # 5. Wait for confirmation
        raise TransactionError(
            message="Transaction submission requires Aptos SDK integration",
        )

    # --- Account Management ---

    async def create_subaccount(self) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::create_new_subaccount",
        )
        return await self._submit_transaction(payload)

    async def deposit(self, amount: int, subaccount_addr: str | None = None) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::deposit_to_subaccount_at",
            args=[sub, self._config.deployment.usdc, amount],
        )
        return await self._submit_transaction(payload)

    async def withdraw(
        self, amount: int, subaccount_addr: str | None = None
    ) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::withdraw_from_subaccount",
            args=[sub, self._config.deployment.usdc, amount],
        )
        return await self._submit_transaction(payload)

    async def configure_user_settings_for_market(
        self, args: ConfigureMarketSettingsArgs
    ) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::configure_user_settings_for_market",
            args=[
                args.subaccount_addr,
                args.market_addr,
                args.is_cross,
                args.user_leverage,
            ],
        )
        return await self._submit_transaction(payload)

    # --- Order Management ---

    async def place_order(self, args: PlaceOrderArgs) -> PlaceOrderResult:
        market_addr = self._get_market_addr(args.market_name)
        sub = self._resolve_subaccount(args.subaccount_addr)

        price = args.price
        if args.tick_size is not None:
            price = round_to_tick_size(price, args.tick_size, 0, args.is_buy)

        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts_entry::place_order_to_subaccount",
            args=[
                sub,
                market_addr,
                price,
                args.size,
                args.is_buy,
                int(args.time_in_force),
                args.is_reduce_only,
                args.client_order_id,
                args.stop_price,
                args.tp_trigger_price,
                args.tp_limit_price,
                args.sl_trigger_price,
                args.sl_limit_price,
                args.builder_addr,
                args.builder_fee,
            ],
        )

        try:
            tx = await self._submit_transaction(payload)
            order_id = extract_order_id_from_events(tx.events, sub)
            return PlaceOrderResult(success=True, order_id=order_id, transaction_hash=tx.hash)
        except TransactionError as e:
            return PlaceOrderResult(success=False, error_message=str(e), transaction_hash=None)

    async def cancel_order(self, args: CancelOrderArgs) -> TransactionResponse:
        if args.market_addr:
            market_addr = args.market_addr
        elif args.market_name:
            market_addr = self._get_market_addr(args.market_name)
        else:
            raise ValidationError("Either market_name or market_addr must be provided")

        sub = self._resolve_subaccount(args.subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::cancel_order_to_subaccount",
            args=[sub, args.order_id, market_addr],
        )
        return await self._submit_transaction(payload)

    async def cancel_client_order(
        self,
        client_order_id: str,
        market_name: str,
        subaccount_addr: str | None = None,
    ) -> TransactionResponse:
        market_addr = self._get_market_addr(market_name)
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::cancel_client_order_to_subaccount",
            args=[sub, client_order_id, market_addr],
        )
        return await self._submit_transaction(payload)

    # --- TWAP Orders ---

    async def place_twap_order(self, args: PlaceTwapOrderArgs) -> TwapOrderResult:
        market_addr = self._get_market_addr(args.market_name)
        sub = self._resolve_subaccount(args.subaccount_addr)

        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::place_twap_order_to_subaccount",
            args=[
                sub,
                market_addr,
                args.size,
                args.is_buy,
                args.is_reduce_only,
                args.twap_frequency_seconds,
                args.twap_duration_seconds,
            ],
        )

        try:
            tx = await self._submit_transaction(payload)
            return TwapOrderResult(success=True, order_id=None, transaction_hash=tx.hash)
        except TransactionError:
            raise

    async def cancel_twap_order(
        self,
        order_id: str,
        market_addr: str,
        subaccount_addr: str | None = None,
    ) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::cancel_twap_order_to_subaccount",
            args=[sub, order_id, market_addr],
        )
        return await self._submit_transaction(payload)

    # --- Position Management ---

    async def place_tp_sl_order_for_position(self, args: PlaceTpSlArgs) -> TransactionResponse:
        sub = self._resolve_subaccount(args.subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::place_tp_sl_order_for_position",
            args=[
                sub,
                args.market_addr,
                args.tp_trigger_price,
                args.tp_limit_price,
                args.tp_size,
                args.sl_trigger_price,
                args.sl_limit_price,
                args.sl_size,
            ],
        )
        return await self._submit_transaction(payload)

    # --- Delegation ---

    async def delegate_trading_to(self, args: DelegateTradingArgs) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::delegate_trading_to_for_subaccount",
            args=[
                args.subaccount_addr,
                args.account_to_delegate_to,
                args.expiration_timestamp_secs,
            ],
        )
        return await self._submit_transaction(payload)

    async def revoke_delegation(
        self,
        account_to_revoke: str,
        subaccount_addr: str | None = None,
    ) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::revoke_delegation",
            args=[sub, account_to_revoke],
        )
        return await self._submit_transaction(payload)

    # --- Builder Fee ---

    async def approve_max_builder_fee(
        self,
        builder_addr: str,
        max_fee: int,
        subaccount_addr: str | None = None,
    ) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::approve_max_builder_fee",
            args=[sub, builder_addr, max_fee],
        )
        return await self._submit_transaction(payload)

    async def revoke_max_builder_fee(
        self,
        builder_addr: str,
        subaccount_addr: str | None = None,
    ) -> TransactionResponse:
        sub = self._resolve_subaccount(subaccount_addr)
        payload = self._build_payload(
            f"{self._config.deployment.package}::dex_accounts::revoke_max_builder_fee",
            args=[sub, builder_addr],
        )
        return await self._submit_transaction(payload)

    # --- Vault Operations ---

    async def create_vault(
        self,
        vault_name: str,
        vault_share_symbol: str,
        fee_bps: int,
        fee_interval_s: int,
        contribution_lockup_duration_s: int,
        initial_funding: int,
        accepts_contributions: bool,
        delegate_to_creator: bool,
        vault_description: str = "",
        vault_social_links: list[str] | None = None,
        contribution_asset_type: str = "",
        vault_share_icon_uri: str = "",
        vault_share_project_uri: str = "",
    ) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::vaults::create_and_fund_vault",
            args=[
                contribution_asset_type,
                vault_name,
                vault_share_symbol,
                vault_share_icon_uri,
                vault_share_project_uri,
                fee_bps,
                fee_interval_s,
                contribution_lockup_duration_s,
                initial_funding,
                accepts_contributions,
                delegate_to_creator,
                vault_description,
                vault_social_links or [],
            ],
        )
        return await self._submit_transaction(payload)

    async def activate_vault(self, vault_address: str) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::vaults::activate_vault",
            args=[vault_address],
        )
        return await self._submit_transaction(payload)

    async def deposit_to_vault(self, vault_address: str, amount: int) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::vaults::contribute_to_vault",
            args=[vault_address, amount],
        )
        return await self._submit_transaction(payload)

    async def withdraw_from_vault(self, vault_address: str, shares: int) -> TransactionResponse:
        payload = self._build_payload(
            f"{self._config.deployment.package}::vaults::redeem_from_vault",
            args=[vault_address, shares],
        )
        return await self._submit_transaction(payload)
