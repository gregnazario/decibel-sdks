"""Replay protection nonce generation."""

from __future__ import annotations

import secrets


def generate_replay_protection_nonce() -> int:
    """Generate a random 64-bit nonce for transaction replay protection.

    Returns a cryptographically random integer in the u64 range [0, 2^64).
    """
    return int.from_bytes(secrets.token_bytes(8), byteorder="big")
