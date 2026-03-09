"""Address derivation utilities."""

import hashlib


def get_market_addr(market_name: str, perp_engine_global_addr: str) -> str:
    """Derive a market object address from the market name and perp engine global address.

    Args:
        market_name: Market name (e.g., "BTC-USD")
        perp_engine_global_addr: Perp engine global object address

    Returns:
        Derived market address
    """
    addr_bytes = _hex_to_bytes(perp_engine_global_addr)
    seed = _bcs_serialize_string(market_name)
    object_addr = _create_object_address(addr_bytes, seed)
    return f"0x{object_addr.hex()}"


def get_primary_subaccount_addr(
    account_addr: str, compat_version: str, package_addr: str
) -> str:
    """Derive the primary subaccount address for an account.

    Args:
        account_addr: Account address
        compat_version: SDK compatibility version
        package_addr: Package address

    Returns:
        Derived primary subaccount address
    """
    addr_bytes = _hex_to_bytes(account_addr)
    seed = f"{_strip_hex_prefix(package_addr)}::dex_accounts::primary_account"
    object_addr = _create_object_address(addr_bytes, seed.encode())
    return f"0x{object_addr.hex()}"


def get_vault_share_address(vault_address: str) -> str:
    """Derive a vault share token address.

    Args:
        vault_address: Vault address

    Returns:
        Derived vault share token address
    """
    addr_bytes = _hex_to_bytes(vault_address)
    object_addr = _create_object_address(addr_bytes, b"vault_share")
    return f"0x{object_addr.hex()}"


def _create_object_address(source: bytes, seed: bytes) -> bytes:
    """Compute SHA3-256(source || seed || 0xFE).

    Args:
        source: Source address bytes
        seed: Seed bytes

    Returns:
        Derived address bytes
    """
    padded_source = bytearray(32)
    src_len = min(len(source), 32)
    padded_source[32 - src_len :] = source[:src_len]

    hasher = hashlib.sha3_256()
    hasher.update(bytes(padded_source))
    hasher.update(seed)
    hasher.update(b"\xFE")

    return hasher.digest()


def _bcs_serialize_string(s: str) -> bytes:
    """Serialize a string with ULEB128 length prefix (BCS format).

    Args:
        s: String to serialize

    Returns:
        Serialized bytes
    """
    bytes_val = s.encode()
    result = bytearray()
    length = len(bytes_val)

    while True:
        b = length & 0x7F
        length >>= 7
        if length > 0:
            b |= 0x80
        result.append(b)
        if length == 0:
            break

    result.extend(bytes_val)
    return bytes(result)


def _hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hex string (with optional 0x prefix) to bytes.

    Args:
        hex_str: Hex string

    Returns:
        Bytes

    Raises:
        ValueError: If hex string is invalid
    """
    stripped = _strip_hex_prefix(hex_str)
    if len(stripped) % 2 != 0:
        stripped = "0" + stripped
    return bytes.fromhex(stripped)


def _strip_hex_prefix(s: str) -> str:
    """Strip 0x prefix from a hex string.

    Args:
        s: Hex string

    Returns:
        String without 0x prefix
    """
    return s.removeprefix("0x")
