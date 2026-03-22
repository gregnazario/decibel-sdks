"""Utility modules for the Decibel SDK."""

from decibel.utils.address import (
    get_market_addr,
    get_primary_subaccount_addr,
    get_vault_share_address,
)
from decibel.utils.formatting import (
    amount_to_chain_units,
    chain_units_to_amount,
    from_chain_price,
    from_chain_size,
    round_to_valid_order_size,
    round_to_valid_price,
    to_chain_price,
    to_chain_size,
)
from decibel.utils.nonce import generate_replay_protection_nonce
from decibel.utils.price import round_to_tick_size

# Backward-compatible alias for the v1 name
generate_random_replay_protection_nonce = generate_replay_protection_nonce

__all__ = [
    "get_market_addr",
    "get_primary_subaccount_addr",
    "get_vault_share_address",
    "round_to_tick_size",
    "generate_replay_protection_nonce",
    "generate_random_replay_protection_nonce",
    "amount_to_chain_units",
    "chain_units_to_amount",
    "round_to_valid_price",
    "round_to_valid_order_size",
    "to_chain_price",
    "from_chain_price",
    "to_chain_size",
    "from_chain_size",
]
