"""Cryptographic utilities."""

import secrets


def generate_random_replay_protection_nonce() -> int:
    """Generate a cryptographically secure random nonce for replay protection.

    Returns:
        Random 64-bit nonce
    """
    return secrets.randbits(64)
