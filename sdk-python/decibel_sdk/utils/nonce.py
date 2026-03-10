"""Replay protection nonce generation."""

from __future__ import annotations

import secrets


def generate_random_replay_protection_nonce() -> int:
    """Generate a random 64-bit nonce for replay protection."""
    return secrets.randbits(64)
