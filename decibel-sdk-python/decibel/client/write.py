"""Write client for on-chain operations."""

from typing import Any

import httpx

from ..config import DecibelConfig
from ..errors import SigningError, SimulationError, TransactionError
from ..gas.manager import GasPriceManager
from ..models.common import PlaceOrderResult, TwapOrderResult
from ..models.enums import TimeInForce
from ..transaction.builder import AptosTransactionBuilder
from ..transaction.signer import Ed25519Signer
from ..utils.address import get_market_addr
from ..utils.formatting import amount_to_chain_units


class DecibelWriteClient:
    """Client for on-chain operations (requires Ed25519 private key).

    Attributes:
        config: SDK configuration
        signer: Ed25519 signer
        skip_simulate: Skip transaction simulation
        no_fee_payer: Disable gas station/fee payer
    """

    def __init__(
        self,
        config: DecibelConfig,
        private_key: bytes | Ed25519Signer,
        skip_simulate: bool = False,
        no_fee_payer: bool = False,
        gas_price_manager: GasPriceManager | None = None,
    ) -> None:
        """Initialize write client.

        Args:
            config: SDK configuration
            private_key: Ed25519 private key (32 bytes) or Ed25519Signer instance
            skip_simulate: Skip transaction simulation (default: false)
            no_fee_payer: Disable gas station/fee payer (default: false)
            gas_price_manager: Optional custom gas price manager
        """
        config.validate()

        self._config = config
        self._skip_simulate = skip_simulate
        self._no_fee_payer = no_fee_payer

        # Initialize signer
        if isinstance(private_key, Ed25519Signer):
            self._signer = private_key
        else:
            self._signer = Ed25519Signer(private_key)

        # Get sender address from public key
        self._sender = self._derive_address()

        # Initialize transaction builder
        self._builder = AptosTransactionBuilder(config)

        # Initialize gas price manager
        self._gas_manager = gas_price_manager or GasPriceManager(config)

        # Create HTTP client
        self._http = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    def _derive_address(self) -> str:
        """Derive address from public key.

        Returns:
            Address as hex string
        """
        # For Ed25519, the address is derived from the public key
        # This is a simplified version - in production you'd use proper address derivation
        pub_key = self._signer.public_key
        # For now, use the last 32 bytes of SHA3-256 of public key
        import hashlib

        hash_digest = hashlib.sha3_256(pub_key).digest()
        return f"0x{hash_digest.hex()}"

    async def _submit_transaction(
        self, transaction: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit a signed transaction.

        Args:
            transaction: Transaction to submit

        Returns:
            Transaction response

        Raises:
            SigningError: Signing error
            TransactionError: Transaction error
            SimulationError: Simulation error
        """
        # Add sender to transaction
        transaction["sender"] = self._sender

        # Get gas price
        gas_price = await self._gas_manager.get_gas_price()
        transaction["gas_unit_price"] = str(gas_price)

        # Simulate if not skipped
        if not self._skip_simulate:
            simulation_result = await self._simulate_transaction(transaction)
            # Use simulation gas estimate
            if "gas_used" in simulation_result:
                transaction["max_gas_amount"] = str(int(simulation_result["gas_used"]) * 2)

        # Sign transaction
        try:
            # For Aptos, we need to serialize and sign the transaction
            # This is a simplified version - in production you'd use proper BCS serialization
            transaction_bytes = self._serialize_transaction(transaction)
            signature = self._signer.sign(transaction_bytes)
        except Exception as e:
            raise SigningError(f"Failed to sign transaction: {e}", cause=e) from e

        # Submit
        if self._no_fee_payer or not self._config.gas_station_url:
            # Submit directly to node
            tx_payload = {
                "transaction": transaction,
                "signature": {
                    "type": "ed25519_signature",
                    "public_key": self._signer.public_key.hex(),
                    "signature": signature.hex(),
                },
            }
            response = await self._http.post(
                f"{self._config.fullnode_url}/transactions",
                json=tx_payload,
            )
        else:
            # Submit via gas station
            tx_payload = {
                "signature": signature.hex(),
                "transaction": transaction,
            }
            response = await self._http.post(
                f"{self._config.gas_station_url}/transactions",
                json=tx_payload,
            )

        if not response.is_success:
            error_msg = response.text
            raise TransactionError(
                message=f"Transaction failed: {error_msg}",
                vm_status=None,
            )

        return response.json()

    def _serialize_transaction(self, transaction: dict[str, Any]) -> bytes:
        """Serialize transaction for signing.

        Args:
            transaction: Transaction to serialize

        Returns:
            Serialized bytes

        Note:
            This is a simplified implementation. In production, you'd use proper BCS serialization.
        """
        import json

        return json.dumps(transaction, sort_keys=True).encode()

    async def _simulate_transaction(
        self, transaction: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate a transaction.

        Args:
            transaction: Transaction to simulate

        Returns:
            Simulation result

        Raises:
            SimulationError: Simulation error
        """
        try:
            response = await self._http.post(
                f"{self._config.fullnode_url}/transactions/simulate",
                json=transaction,
            )
            response.raise_for_status()
            result = response.json()

            if not result or len(result) == 0:
                raise SimulationError("Empty simulation result")

            simulation = result[0]

            # Check for VM errors
            if "vm_status" in simulation and simulation["vm_status"] != "Executed successfully":
                raise SimulationError(f"Simulation failed: {simulation['vm_status']}")

            return simulation

        except httpx.HTTPError as e:
            raise SimulationError(f"Simulation request failed: {e}", cause=e) from e

    async def close(self) -> None:
        """Close the HTTP client and gas manager."""
        await self._http.aclose()
        await self._gas_manager.stop()

    # --- Account Management ---

    async def create_subaccount(self) -> str:
        """Create a new subaccount.

        Returns:
            Created subaccount address
        """
        tx = self._builder.build_create_subaccount_transaction()
        await self._submit_transaction(tx)
        return self._sender

    async def deposit(self, amount: int, subaccount_addr: str | None = None) -> dict[str, Any]:
        """Deposit collateral to subaccount.

        Args:
            amount: Amount in smallest unit
            subaccount_addr: Optional subaccount address (defaults to primary)

        Returns:
            Transaction response
        """
        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        tx = self._builder.build_deposit_transaction(amount, subaccount_addr)
        return await self._submit_transaction(tx)

    async def withdraw(self, amount: int, subaccount_addr: str | None = None) -> dict[str, Any]:
        """Withdraw collateral from subaccount.

        Args:
            amount: Amount in smallest unit
            subaccount_addr: Optional subaccount address (defaults to primary)

        Returns:
            Transaction response
        """
        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        tx = self._builder.build_withdraw_transaction(amount, subaccount_addr)
        return await self._submit_transaction(tx)

    async def configure_user_settings(
        self,
        market_addr: str,
        subaccount_addr: str,
        is_cross: bool,
        user_leverage: int,
    ) -> dict[str, Any]:
        """Configure user settings for a market.

        Args:
            market_addr: Market address
            subaccount_addr: Subaccount address
            is_cross: Cross margin mode
            user_leverage: Leverage in basis points (1000 = 10x)

        Returns:
            Transaction response
        """
        tx = self._builder.build_configure_user_settings_transaction(
            market_addr, subaccount_addr, is_cross, user_leverage
        )
        return await self._submit_transaction(tx)

    # --- Order Management ---

    async def place_order(
        self,
        market_name: str,
        price: float,
        size: float,
        is_buy: bool,
        time_in_force: TimeInForce,
        is_reduce_only: bool,
        client_order_id: int | None = None,
        subaccount_addr: str | None = None,
        stop_price: float | None = None,
        tick_size: float | None = None,
    ) -> PlaceOrderResult:
        """Place a limit order.

        Args:
            market_name: Market name (e.g., "BTC-USD")
            price: Limit price
            size: Order size
            is_buy: Buy or sell
            time_in_force: Time in force type
            is_reduce_only: Reduce only flag
            client_order_id: Optional client order ID
            subaccount_addr: Optional subaccount address
            stop_price: Optional stop trigger price
            tick_size: Optional tick size for price rounding

        Returns:
            Order placement result
        """
        from ..utils.price import round_to_tick_size

        # Get market address
        market_addr = get_market_addr(market_name, self._config.deployment.perp_engine_global_addr)

        # Get subaccount address
        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        # Round price if tick_size provided
        if tick_size and price > 0:
            price = round_to_tick_size(price, tick_size, 8, not is_buy)

        price_int = amount_to_chain_units(price, decimals=8)
        size_int = amount_to_chain_units(size, decimals=8)

        try:
            tx = self._builder.build_place_order_transaction(
                market_addr=market_addr,
                subaccount_addr=subaccount_addr,
                price=price_int,
                size=size_int,
                is_buy=is_buy,
                time_in_force=time_in_force.value,
                is_reduce_only=is_reduce_only,
                client_order_id=client_order_id,
                stop_price=amount_to_chain_units(stop_price, decimals=8) if stop_price else None,
            )

            result = await self._submit_transaction(tx)

            # Extract order ID from result
            order_id = result.get("order_id")

            return PlaceOrderResult(
                success=True,
                order_id=order_id,
                transaction_hash=result.get("hash"),
            )

        except Exception as e:
            return PlaceOrderResult(
                success=False,
                error=str(e),
            )

    async def cancel_order(
        self,
        order_id: str,
        market_name: str,
        subaccount_addr: str | None = None,
    ) -> dict[str, Any]:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel
            market_name: Market name
            subaccount_addr: Optional subaccount address

        Returns:
            Transaction response
        """
        market_addr = get_market_addr(market_name, self._config.deployment.perp_engine_global_addr)

        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        tx = self._builder.build_cancel_order_transaction(order_id, market_addr, subaccount_addr)
        return await self._submit_transaction(tx)

    async def cancel_client_order(
        self,
        client_order_id: str,
        market_name: str,
        subaccount_addr: str | None = None,
    ) -> dict[str, Any]:
        """Cancel an order by client order ID.

        Args:
            client_order_id: Client order ID
            market_name: Market name
            subaccount_addr: Optional subaccount address

        Returns:
            Transaction response
        """
        market_addr = get_market_addr(market_name, self._config.deployment.perp_engine_global_addr)

        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        tx = self._builder.build_cancel_client_order_transaction(
            client_order_id, market_addr, subaccount_addr
        )
        return await self._submit_transaction(tx)

    # --- TWAP Orders ---

    async def place_twap_order(
        self,
        market_name: str,
        size: float,
        is_buy: bool,
        is_reduce_only: bool,
        twap_frequency_seconds: int,
        twap_duration_seconds: int,
        client_order_id: int | None = None,
        subaccount_addr: str | None = None,
    ) -> TwapOrderResult:
        """Place a TWAP order.

        Args:
            market_name: Market name
            size: Total size
            is_buy: Buy or sell
            is_reduce_only: Reduce only flag
            twap_frequency_seconds: Execution frequency in seconds
            twap_duration_seconds: Total duration in seconds
            client_order_id: Optional client order ID
            subaccount_addr: Optional subaccount address

        Returns:
            TWAP order result
        """
        market_addr = get_market_addr(market_name, self._config.deployment.perp_engine_global_addr)

        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        size_int = amount_to_chain_units(size, decimals=8)

        try:
            tx = self._builder.build_place_twap_order_transaction(
                market_addr=market_addr,
                subaccount_addr=subaccount_addr,
                size=size_int,
                is_buy=is_buy,
                is_reduce_only=is_reduce_only,
                client_order_id=client_order_id,
                twap_frequency_seconds=twap_frequency_seconds,
                twap_duration_seconds=twap_duration_seconds,
            )

            result = await self._submit_transaction(tx)

            return TwapOrderResult(
                success=True,
                order_id=result.get("order_id"),
                transaction_hash=result.get("hash", ""),
            )

        except Exception:
            return TwapOrderResult(
                success=False,
                transaction_hash="",
            )

    async def cancel_twap_order(
        self,
        order_id: str,
        market_addr: str,
        subaccount_addr: str | None = None,
    ) -> dict[str, Any]:
        """Cancel a TWAP order.

        Args:
            order_id: TWAP order ID
            market_addr: Market address
            subaccount_addr: Optional subaccount address

        Returns:
            Transaction response
        """
        if subaccount_addr is None:
            from ..utils.address import get_primary_subaccount_addr

            subaccount_addr = get_primary_subaccount_addr(
                self._sender, self._config.compat_version.value, self._config.deployment.package
            )

        # TWAP orders use the same cancel function as regular orders
        tx = self._builder.build_cancel_order_transaction(order_id, market_addr, subaccount_addr)
        return await self._submit_transaction(tx)

    # --- Delegation ---

    async def delegate_trading(
        self,
        subaccount_addr: str,
        account_to_delegate_to: str,
        expiration_timestamp_secs: int | None = None,
    ) -> dict[str, Any]:
        """Delegate trading to another account.

        Args:
            subaccount_addr: Subaccount address
            account_to_delegate_to: Account to delegate to
            expiration_timestamp_secs: Optional expiration timestamp

        Returns:
            Transaction response
        """
        tx = self._builder.build_delegate_trading_transaction(
            subaccount_addr, account_to_delegate_to, expiration_timestamp_secs
        )
        return await self._submit_transaction(tx)

    async def revoke_delegation(
        self,
        subaccount_addr: str,
        account_to_revoke: str,
    ) -> dict[str, Any]:
        """Revoke trading delegation.

        Args:
            subaccount_addr: Subaccount address
            account_to_revoke: Account to revoke delegation from

        Returns:
            Transaction response
        """
        tx = self._builder.build_revoke_delegation_transaction(subaccount_addr, account_to_revoke)
        return await self._submit_transaction(tx)
