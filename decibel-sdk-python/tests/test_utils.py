"""Tests for utility functions."""


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
    """Test object address derivation produces 32 bytes and is deterministic."""
    source = bytes.fromhex("1234567890abcdef" * 4)  # 32 bytes
    seed = b"test_seed"
    addr = _create_object_address(source, seed)
    assert len(addr) == 32, "Aptos object addresses are 32 bytes"
    assert isinstance(addr, bytes)
    # Deterministic
    addr2 = _create_object_address(source, seed)
    assert addr == addr2, "Same inputs must produce same address"
    # Different seed produces different address
    addr3 = _create_object_address(source, b"other_seed")
    assert addr != addr3, "Different seeds must produce different addresses"


def test_get_market_addr():
    """Test market address derivation is deterministic and distinct per market."""
    perp_global = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234"
    btc_addr = get_market_addr("BTC-USD", perp_global)
    assert btc_addr.startswith("0x")
    assert len(btc_addr) == 66
    assert btc_addr != "0x" + "00" * 32, "Must not derive to zero address"
    # Deterministic
    btc_addr2 = get_market_addr("BTC-USD", perp_global)
    assert btc_addr == btc_addr2, "Same inputs must produce same address"
    # Different market produces different address
    eth_addr = get_market_addr("ETH-USD", perp_global)
    assert btc_addr != eth_addr, "BTC-USD and ETH-USD must have different addresses"


def test_get_primary_subaccount_addr():
    """Test subaccount derivation is deterministic and varies by account."""
    account = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234"
    package = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    sub_addr = get_primary_subaccount_addr(account, "v0.4", package)
    assert sub_addr.startswith("0x")
    assert len(sub_addr) == 66
    assert sub_addr != "0x" + "00" * 32, "Must not derive to zero address"
    assert sub_addr != account, "Subaccount must differ from the owner account"
    # Deterministic
    sub_addr2 = get_primary_subaccount_addr(account, "v0.4", package)
    assert sub_addr == sub_addr2, "Same inputs must produce same address"
    # Different account produces different subaccount
    other_account = "0x" + "ff" * 32
    other_sub = get_primary_subaccount_addr(other_account, "v0.4", package)
    assert sub_addr != other_sub, "Different accounts must have different subaccounts"


def test_get_vault_share_address():
    """Test vault share address derivation is deterministic and distinct."""
    vault = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef1234"
    share_addr = get_vault_share_address(vault)
    assert share_addr.startswith("0x")
    assert len(share_addr) == 66
    assert share_addr != "0x" + "00" * 32, "Must not derive to zero address"
    assert share_addr != vault, "Share address must differ from vault address"
    # Deterministic
    share_addr2 = get_vault_share_address(vault)
    assert share_addr == share_addr2, "Same input must produce same address"
    # Different vault produces different share address
    other_vault = "0x" + "ab" * 32
    other_share = get_vault_share_address(other_vault)
    assert share_addr != other_share, "Different vaults must have different share addresses"


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
