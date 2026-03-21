"""Aptos transaction builder for Decibel smart contract calls."""

from typing import Any

from ..config import DecibelConfig
from ..utils.crypto import generate_random_replay_protection_nonce


class AptosTransactionBuilder:
    """Builder for constructing Aptos transactions.

    Attributes:
        config: SDK configuration
    """

    def __init__(self, config: DecibelConfig) -> None:
        """Initialize transaction builder.

        Args:
            config: SDK configuration
        """
        self._config = config
        self._chain_id = config.chain_id or 1

    def build_transaction(
        self,
        function: str,
        type_arguments: list[str],
        function_arguments: list[Any],
        max_gas_amount: int | None = None,
        gas_unit_price: int | None = None,
    ) -> dict[str, Any]:
        """Build an Aptos transaction payload.

        Args:
            function: Fully qualified Move function name (e.g., "0x...::module::function")
            type_arguments: Move type arguments (typically empty)
            function_arguments: Move function arguments
            max_gas_amount: Maximum gas amount (optional)
            gas_unit_price: Gas unit price (optional)

        Returns:
            Transaction payload dictionary
        """
        # Generate expiration timestamp (30 seconds from now)
        from datetime import datetime, timedelta

        expiration_secs = int((datetime.now() + timedelta(seconds=30)).timestamp())

        payload = {
            "function": function,
            "type_arguments": type_arguments,
            "arguments": self._encode_arguments(function_arguments),
        }

        transaction = {
            "sender": "",  # Will be set by signer
            "payload": payload,
            "max_gas_amount": str(max_gas_amount or 100000),
            "gas_unit_price": str(gas_unit_price or 100),
            "expiration_timestamp_secs": expiration_secs,
            "chain_id": self._chain_id,
        }

        return transaction

    def _encode_arguments(self, arguments: list[Any]) -> list[Any]:
        """Encode function arguments for Move ABI.

        Args:
            arguments: Raw arguments

        Returns:
            Encoded arguments
        """
        encoded = []
        for arg in arguments:
            if isinstance(arg, str):
                # String argument - check if it's an address
                if arg.startswith("0x"):
                    encoded.append(arg)
                else:
                    # Regular string
                    encoded.append(arg)
            elif isinstance(arg, bool):
                encoded.append(arg)
            elif isinstance(arg, int):
                encoded.append(str(arg))
            elif isinstance(arg, float):
                # For floats, we need to handle them as strings with proper decimal places
                encoded.append(str(arg))
            elif isinstance(arg, list):
                # Vector/list argument
                encoded.append(arg)
            elif arg is None:
                encoded.append("")
            else:
                encoded.append(arg)

        return encoded

    # --- Account Management ---

    def build_create_subaccount_transaction(self) -> dict[str, Any]:
        """Build transaction to create a new subaccount.

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::create_new_subaccount"

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[],
        )

    def build_deposit_transaction(
        self, amount: int, subaccount_addr: str
    ) -> dict[str, Any]:
        """Build transaction to deposit collateral to subaccount.

        Args:
            amount: Amount in smallest unit
            subaccount_addr: Subaccount address

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        usdc = self._config.deployment.usdc
        function = f"{package}::dex_accounts::deposit_to_subaccount_at"

        return self.build_transaction(
            function=function,
            type_arguments=[usdc],
            function_arguments=[subaccount_addr, amount],
        )

    def build_withdraw_transaction(
        self, amount: int, subaccount_addr: str
    ) -> dict[str, Any]:
        """Build transaction to withdraw collateral from subaccount.

        Args:
            amount: Amount in smallest unit
            subaccount_addr: Subaccount address

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        usdc = self._config.deployment.usdc
        function = f"{package}::dex_accounts::withdraw_from_subaccount"

        return self.build_transaction(
            function=function,
            type_arguments=[usdc],
            function_arguments=[subaccount_addr, amount],
        )

    def build_configure_user_settings_transaction(
        self,
        market_addr: str,
        subaccount_addr: str,
        is_cross: bool,
        user_leverage: int,
    ) -> dict[str, Any]:
        """Build transaction to configure user settings.

        Args:
            market_addr: Market address
            subaccount_addr: Subaccount address
            is_cross: Cross margin mode
            user_leverage: Leverage in basis points (1000 = 10x)

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::configure_user_settings_for_market"

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[market_addr, subaccount_addr, is_cross, user_leverage],
        )

    # --- Order Management ---

    def build_place_order_transaction(
        self,
        market_addr: str,
        subaccount_addr: str,
        price: int,
        size: int,
        is_buy: bool,
        time_in_force: int,
        is_reduce_only: bool,
        client_order_id: int | None = None,
        stop_price: int | None = None,
        nonce: int | None = None,
    ) -> dict[str, Any]:
        """Build transaction to place an order.

        Args:
            market_addr: Market address
            subaccount_addr: Subaccount address
            price: Limit price in smallest unit
            size: Order size in smallest unit
            is_buy: Buy or sell
            time_in_force: Time in force (0=GTC, 1=PostOnly, 2=IOC)
            is_reduce_only: Reduce only flag
            client_order_id: Optional client order ID
            stop_price: Optional stop trigger price
            nonce: Replay protection nonce

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts_entry::place_order_to_subaccount"

        if client_order_id is None:
            client_order_id = generate_random_replay_protection_nonce()
        if nonce is None:
            nonce = generate_random_replay_protection_nonce()

        # Build order params
        order_params = [
            price,  # limit_price
            size,  # size
            is_buy,  # is_buy
            client_order_id,  # client_order_id
            time_in_force,  # time_in_force
            nonce,  # nonce
            is_reduce_only,  # is_reduce_only
            stop_price or 0,  # stop_price (0 if not set)
            "",  # tp_trigger_price (empty string)
            "",  # tp_limit_price (empty string)
            "",  # sl_trigger_price (empty string)
            "",  # sl_limit_price (empty string)
            [],  # tp_size (empty vector)
            [],  # sl_size (empty vector)
            "",  # builder_address (empty string)
            0,  # builder_fee_bps (0 if not set)
        ]

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[market_addr, subaccount_addr] + order_params,
        )

    def build_cancel_order_transaction(
        self,
        order_id: str,
        market_addr: str,
        subaccount_addr: str,
    ) -> dict[str, Any]:
        """Build transaction to cancel an order.

        Args:
            order_id: Order ID
            market_addr: Market address
            subaccount_addr: Subaccount address

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::cancel_order_to_subaccount"

        # Parse order_id as integer
        try:
            order_id_int = int(order_id)
        except ValueError:
            # If order_id is a hex string or other format, we might need to handle differently
            order_id_int = 0

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[subaccount_addr, order_id_int, market_addr],
        )

    def build_cancel_client_order_transaction(
        self,
        client_order_id: str,
        market_addr: str,
        subaccount_addr: str,
    ) -> dict[str, Any]:
        """Build transaction to cancel order by client order ID.

        Args:
            client_order_id: Client order ID
            market_addr: Market address
            subaccount_addr: Subaccount address

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::cancel_client_order_to_subaccount"

        # Parse client_order_id as integer
        try:
            client_order_id_int = int(client_order_id)
        except ValueError:
            client_order_id_int = 0

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[subaccount_addr, client_order_id_int, market_addr],
        )

    # --- TWAP Orders ---

    def build_place_twap_order_transaction(
        self,
        market_addr: str,
        subaccount_addr: str,
        size: int,
        is_buy: bool,
        is_reduce_only: bool,
        client_order_id: int | None = None,
        twap_frequency_seconds: int = 60,
        twap_duration_seconds: int = 3600,
    ) -> dict[str, Any]:
        """Build transaction to place a TWAP order.

        Args:
            market_addr: Market address
            subaccount_addr: Subaccount address
            size: Total size in smallest unit
            is_buy: Buy or sell
            is_reduce_only: Reduce only flag
            client_order_id: Optional client order ID
            twap_frequency_seconds: Execution frequency in seconds
            twap_duration_seconds: Total duration in seconds

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::place_twap_order_to_subaccount"

        if client_order_id is None:
            client_order_id = generate_random_replay_protection_nonce()

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[
                market_addr,
                subaccount_addr,
                size,
                is_buy,
                is_reduce_only,
                client_order_id,
                twap_frequency_seconds,
                twap_duration_seconds,
            ],
        )

    # --- Delegation ---

    def build_delegate_trading_transaction(
        self,
        subaccount_addr: str,
        account_to_delegate_to: str,
        expiration_timestamp_secs: int | None = None,
    ) -> dict[str, Any]:
        """Build transaction to delegate trading.

        Args:
            subaccount_addr: Subaccount address
            account_to_delegate_to: Account to delegate to
            expiration_timestamp_secs: Optional expiration timestamp

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::delegate_trading_to_for_subaccount"

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[subaccount_addr, account_to_delegate_to, expiration_timestamp_secs or 0],
        )

    def build_revoke_delegation_transaction(
        self,
        subaccount_addr: str,
        account_to_revoke: str,
    ) -> dict[str, Any]:
        """Build transaction to revoke delegation.

        Args:
            subaccount_addr: Subaccount address
            account_to_revoke: Account to revoke delegation from

        Returns:
            Transaction payload
        """
        package = self._config.deployment.package
        function = f"{package}::dex_accounts::revoke_delegation"

        return self.build_transaction(
            function=function,
            type_arguments=[],
            function_arguments=[subaccount_addr, account_to_revoke],
        )
