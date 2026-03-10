"""Address derivation utilities for Aptos object addresses."""

from __future__ import annotations

import hashlib


def create_object_address(source: bytes, seed: bytes) -> bytes:
    """Aptos ``create_object_address``: SHA3-256(source_32 || seed || 0xFE)."""
    padded = source.rjust(32, b"\x00")[:32]
    h = hashlib.sha3_256()
    h.update(padded)
    h.update(seed)
    h.update(b"\xfe")
    return h.digest()


def bcs_serialize_string(s: str) -> bytes:
    """BCS-serialize a string: ULEB128 length prefix + UTF-8 bytes."""
    data = s.encode("utf-8")
    length = len(data)
    result = bytearray()
    while True:
        byte = length & 0x7F
        length >>= 7
        if length > 0:
            byte |= 0x80
        result.append(byte)
        if length == 0:
            break
    result.extend(data)
    return bytes(result)


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hex string (with optional ``0x`` prefix) to bytes."""
    stripped = _strip_hex_prefix(hex_str)
    if len(stripped) % 2 != 0:
        stripped = "0" + stripped
    return bytes.fromhex(stripped)


def _strip_hex_prefix(s: str) -> str:
    return s[2:] if s.startswith("0x") else s


def get_market_addr(name: str, perp_engine_global_addr: str) -> str:
    """Derive a market object address from market name and perp engine global address."""
    addr_bytes = hex_to_bytes(perp_engine_global_addr)
    seed = bcs_serialize_string(name)
    obj_addr = create_object_address(addr_bytes, seed)
    return "0x" + obj_addr.hex()


def get_primary_subaccount_addr(
    account_addr: str,
    _compat_version: str,
    package_addr: str,
) -> str:
    """Derive the primary subaccount address for an account."""
    addr_bytes = hex_to_bytes(account_addr)
    seed = f"{_strip_hex_prefix(package_addr)}::dex_accounts::primary_account"
    obj_addr = create_object_address(addr_bytes, seed.encode("utf-8"))
    return "0x" + obj_addr.hex()


def get_vault_share_address(vault_address: str) -> str:
    """Derive a vault share token address from the vault address."""
    addr_bytes = hex_to_bytes(vault_address)
    obj_addr = create_object_address(addr_bytes, b"vault_share")
    return "0x" + obj_addr.hex()
