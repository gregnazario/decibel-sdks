"""Tests for utility functions."""

import pytest

from decibel.utils.address import (
    _bcs_serialize_string,
    _create_object_address,
    _hex_to_bytes,
    _strip_hex_prefix,
    get_market_addr,
    get_primary_subaccount_addr,
    get_vault_share_address,
)
from decibel.utils.crypto import generate_random_replay_protection_nonce
from decibel.utils.price import round_to_tick_size


def test_strip_hex_prefix():
    """Test hex prefix stripping."""
    assert _strip_hex_prefix("0x123") == "123"
    assert _strip_hex_prefix("123") == "123"
    assert _strip_hex_prefix("0XABC") == "0XABC"  # Only lowercase 0x


def test_hex_to_bytes():
    """Test hex to bytes conversion."""
    result = _hex_to_bytes("0x1234")
    assert result == b"\x12\x34"

    result = _hex_to_bytes("1234")
    assert result == b"\x12\x34"

    # Test odd length (should pad with leading zero)
    result = _hex_to_bytes("123")
    assert result == b"\x01\x23"


def test_bcs_serialize_string():
    """Test BCS string serialization."""
    result = _bcs_serialize_string("test")
    # Length (4) + string bytes
    assert len(result) == 1 + 4
    assert result[-4:] == b"test"

    # Test empty string
    result = _bcs_serialize_string("")
    assert len(result) == 1
    assert result[0] == 0


def test_create_object_address():
    """Test object address derivation."""
    source = bytes.fromhex("1234567890abcdef" * 2)  # 16 bytes
    seed = b"test_seed"
    addr = _create_object_address(source, seed)
    assert len(addr) == 32
    assert isinstance(addr, bytes)


def test_get_market_addr():
    """Test market address derivation."""
    market_addr = get_market_addr("BTC-USD", "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234")
    assert market_addr.startswith("0x")
    assert len(market_addr) == 66  # 0x + 64 hex chars


def test_get_primary_subaccount_addr():
    """Test primary subaccount address derivation."""
    sub_addr = get_primary_subaccount_addr(
        "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234",
        "v0.4",
        "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    assert sub_addr.startswith("0x")
    assert len(sub_addr) == 66


def test_get_vault_share_address():
    """Test vault share address derivation."""
    share_addr = get_vault_share_address("0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234")
    assert share_addr.startswith("0x")
    assert len(share_addr) == 66


def test_round_to_tick_size():
    """Test price rounding to tick size."""
    # Round up
    result = round_to_tick_size(45001.7, 0.5, 2, True)
    assert result == 45002.0

    # Round down
    result = round_to_tick_size(45001.7, 0.5, 2, False)
    assert result == 45001.5

    # No rounding needed
    result = round_to_tick_size(45000.0, 0.5, 2, True)
    assert result == 45000.0

    # Zero tick size (should return original)
    result = round_to_tick_size(45001.7, 0.0, 2, True)
    assert result == 45001.7


def test_generate_random_replay_protection_nonce():
    """Test random nonce generation."""
    nonce = generate_random_replay_protection_nonce()
    assert isinstance(nonce, int)
    assert 0 <= nonce < 2**64

    # Test uniqueness (very high probability of being different)
    nonce2 = generate_random_replay_protection_nonce()
    assert nonce != nonce2
