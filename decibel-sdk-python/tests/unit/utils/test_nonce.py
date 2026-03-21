"""TDD tests for nonce generation utilities.

Replay-protection nonces must be unique 64-bit integers.  A
duplicate nonce would cause the Aptos VM to reject the transaction
(replay attack guard), so correctness here directly affects trade
execution reliability.

The function under test is expected at ``decibel.utils.nonce``.
If that module does not yet exist, these tests will fail with an
ImportError — which is the intended TDD starting state.
"""

from __future__ import annotations

import pytest

from decibel.utils.nonce import generate_replay_protection_nonce


# ===================================================================
# generate_replay_protection_nonce
# ===================================================================


class TestGenerateReplayProtectionNonce:
    """Contract tests for nonce generation.

    A nonce must be:
    1. A Python int
    2. In the u64 range [0, 2^64)
    3. Cryptographically random (each call returns a different value)
    """

    def test_returns_int(self) -> None:
        """Nonce must be a plain Python int for BCS serialisation.

        The transaction builder packs the nonce as a u64; passing a
        float or string would raise at serialisation time.
        """
        nonce = generate_replay_protection_nonce()
        assert isinstance(nonce, int)

    def test_fits_u64_range(self) -> None:
        """Nonce must be in [0, 2^64).

        The Aptos VM treats the nonce as an unsigned 64-bit integer;
        values outside this range would overflow or be rejected.
        """
        nonce = generate_replay_protection_nonce()
        assert 0 <= nonce < 2**64

    def test_consecutive_calls_differ(self) -> None:
        """Two consecutive calls must return different values.

        While collisions are theoretically possible in a 64-bit space,
        they are astronomically unlikely with a CSPRNG and indicate a
        broken implementation if observed.
        """
        a = generate_replay_protection_nonce()
        b = generate_replay_protection_nonce()
        assert a != b

    def test_many_calls_all_unique(self) -> None:
        """100 generated nonces should all be unique.

        Batch uniqueness gives higher confidence than a single pair
        comparison that the underlying entropy source is functional.
        """
        nonces = {generate_replay_protection_nonce() for _ in range(100)}
        assert len(nonces) == 100

    def test_nonce_positive_or_zero(self) -> None:
        """Nonce must be non-negative.

        Negative values are invalid in the unsigned on-chain
        representation.
        """
        for _ in range(50):
            assert generate_replay_protection_nonce() >= 0

    def test_nonce_not_always_small(self) -> None:
        """At least one of 50 nonces should exceed 2^32.

        Ensures the generator uses the full 64-bit range rather than
        only the lower 32 bits.  The probability of all 50 being
        below 2^32 is (2^32 / 2^64)^50 ≈ 0 — effectively impossible.
        """
        nonces = [generate_replay_protection_nonce() for _ in range(50)]
        assert any(n > 2**32 for n in nonces)
