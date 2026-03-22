"""TDD tests for the Decibel error hierarchy with position safety classification.

Trading bots must know whether an error has corrupted their view of positions.
The position_safety field on every error answers: "Can I still trust my local
state, or do I need to re-sync / halt?"

Safety levels:
    SAFE     – No state change occurred; local view is still accurate.
    UNKNOWN  – State *may* have changed; must reconcile before trading.
    STALE    – Local state is outdated (e.g. long WebSocket disconnect).
    CRITICAL – Protective orders may have failed; emergency action required.
"""

import json

import pytest

from decibel.errors import (
    AuthenticationError,
    ConfigError,
    CriticalTradingError,
    DecibelError,
    GasError,
    PositionSafety,
    RateLimitError,
    SimulationError,
    SubmissionError,
    ValidationError,
    VmError,
    WebSocketError,
)

# ---------------------------------------------------------------------------
# Error hierarchy: each error type carries the correct position_safety level
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """Verify that every concrete error type carries the correct position_safety."""

    def test_config_error_is_safe(self):
        """ConfigError is SAFE because misconfiguration cannot change on-chain state.

        A bot that catches a ConfigError knows it never sent a transaction, so
        its position view is still valid.
        """
        err = ConfigError("missing API key")
        assert err.position_safety == PositionSafety.SAFE

    def test_auth_error_is_safe(self):
        """AuthenticationError is SAFE — rejected at the gateway, no state change.

        An expired JWT or wrong API key means the request never reached the
        matching engine, so positions are untouched.
        """
        err = AuthenticationError("token expired")
        assert err.position_safety == PositionSafety.SAFE

    def test_validation_error_is_safe(self):
        """ValidationError is SAFE and carries the offending field/constraint.

        The order was rejected before submission (e.g. size below minimum), so
        no on-chain state changed.  The field and constraint help the bot fix
        the request programmatically.
        """
        err = ValidationError(
            "size too small",
            field="size",
            constraint="min_size=0.001",
        )
        assert err.position_safety == PositionSafety.SAFE
        assert err.field == "size"
        assert err.constraint == "min_size=0.001"

    def test_rate_limit_is_safe(self):
        """RateLimitError is SAFE and includes retry_after_ms.

        The request was throttled before reaching the matching engine.  The bot
        should back off for retry_after_ms and try again.
        """
        err = RateLimitError("too many requests", retry_after_ms=500)
        assert err.position_safety == PositionSafety.SAFE
        assert err.retry_after_ms == 500

    def test_simulation_error_is_safe(self):
        """SimulationError is SAFE — the transaction was only simulated, never submitted.

        Simulation failures (e.g. Move abort) mean the transaction would fail
        on-chain, but since it was never broadcast, state is unchanged.
        """
        err = SimulationError("MOVE_ABORT: insufficient margin")
        assert err.position_safety == PositionSafety.SAFE

    def test_gas_error_is_safe(self):
        """GasError is SAFE — gas estimation or funding failed before submission.

        The transaction was never sent to the mempool.
        """
        err = GasError("insufficient gas balance")
        assert err.position_safety == PositionSafety.SAFE

    def test_submission_error_is_unknown(self):
        """SubmissionError has UNKNOWN safety — the tx may or may not have landed.

        A network timeout during broadcast means the transaction might have
        been included in a block.  The bot must query on-chain state before
        making further decisions.
        """
        err = SubmissionError("broadcast timeout")
        assert err.position_safety == PositionSafety.UNKNOWN

    def test_vm_error_is_unknown(self):
        """VmError is UNKNOWN and includes tx_hash and vm_status.

        The transaction was submitted and executed, but the VM rejected it.
        Partial side-effects (e.g. gas spent, nonce consumed) mean the bot
        must re-check its state.
        """
        err = VmError(
            "execution failed",
            tx_hash="0xabc123",
            vm_status="MOVE_ABORT(0x1::coin, 10)",
        )
        assert err.position_safety == PositionSafety.UNKNOWN
        assert err.tx_hash == "0xabc123"
        assert err.vm_status == "MOVE_ABORT(0x1::coin, 10)"

    def test_ws_error_stale_on_long_disconnect(self):
        """WebSocketError is STALE when the disconnect lasted > 5 seconds.

        A brief blip (< 5s) is treated as transient.  A longer gap means
        the bot may have missed fills or liquidations, so its local state is
        stale and must be re-synced via REST.
        """
        err = WebSocketError("connection lost", disconnect_duration_ms=6000)
        assert err.position_safety == PositionSafety.STALE

    def test_critical_trading_error(self):
        """CriticalTradingError is CRITICAL and reports affected market/order IDs.

        This is the most dangerous class: a protective order (stop-loss,
        take-profit) failed to place or cancel.  The bot has unprotected
        exposure and should take emergency action (e.g. market-close).
        """
        err = CriticalTradingError(
            "stop-loss placement failed",
            affected_market="BTC-USD",
            affected_order_ids=["order-1", "order-2"],
        )
        assert err.position_safety == PositionSafety.CRITICAL
        assert err.affected_market == "BTC-USD"
        assert err.affected_order_ids == ["order-1", "order-2"]


# ---------------------------------------------------------------------------
# Position safety classification: structural guarantees
# ---------------------------------------------------------------------------


class TestPositionSafetyClassification:
    """Structural tests that ensure the classification system is sound."""

    def test_all_errors_have_position_safety(self):
        """Every concrete error subclass exposes a position_safety attribute.

        This prevents a new error type from being added without a safety
        classification, which would leave the bot unsure how to react.
        """
        error_instances = [
            ConfigError("x"),
            AuthenticationError("x"),
            ValidationError("x"),
            RateLimitError("x", retry_after_ms=0),
            SimulationError("x"),
            GasError("x"),
            SubmissionError("x"),
            VmError("x"),
            WebSocketError("x", disconnect_duration_ms=6000),
            CriticalTradingError("x", affected_market="M", affected_order_ids=[]),
        ]
        for err in error_instances:
            assert hasattr(err, "position_safety"), (
                f"{type(err).__name__} missing position_safety"
            )
            assert isinstance(err.position_safety, PositionSafety)

    def test_safe_errors_not_retryable_by_default(self):
        """SAFE does not imply retryable — these are orthogonal concepts.

        A ConfigError is SAFE but should not be retried (the config won't
        magically fix itself).  Conversely, a RateLimitError is SAFE *and*
        retryable.
        """
        err = ConfigError("bad config")
        assert err.position_safety == PositionSafety.SAFE
        assert not err.is_retryable

    def test_retryable_field_independent_of_safety(self):
        """is_retryable and position_safety are independent axes.

        A RateLimitError is (SAFE, retryable).  A SubmissionError is
        (UNKNOWN, retryable).  A ConfigError is (SAFE, not retryable).
        """
        rate_limit = RateLimitError("slow down", retry_after_ms=100)
        assert rate_limit.position_safety == PositionSafety.SAFE
        assert rate_limit.is_retryable

        submission = SubmissionError("timeout")
        assert submission.position_safety == PositionSafety.UNKNOWN
        assert submission.is_retryable

        config = ConfigError("bad")
        assert config.position_safety == PositionSafety.SAFE
        assert not config.is_retryable


# ---------------------------------------------------------------------------
# Serialization: errors must be machine-readable for logging pipelines
# ---------------------------------------------------------------------------


class TestErrorSerialization:
    """Errors must serialize cleanly for structured logging and alerting."""

    def test_error_to_dict(self):
        """to_dict() includes code, message, and position_safety.

        Structured logging systems ingest error dicts.  Every error must
        produce a dict with at least these three fields so that dashboards
        can filter by safety level.
        """
        err = ConfigError("missing key")
        d = err.to_dict()
        assert "code" in d
        assert "message" in d
        assert "position_safety" in d
        assert d["message"] == "missing key"

    def test_error_to_json(self):
        """to_json() produces valid JSON that round-trips.

        Errors are often serialized into log lines or sent over WebSocket
        for monitoring.  Invalid JSON would break downstream parsers.
        """
        err = ValidationError("bad field", field="price", constraint="positive")
        raw = err.to_json()
        parsed = json.loads(raw)
        assert parsed["message"] == "bad field"
        assert "position_safety" in parsed

    def test_error_str_human_readable(self):
        """__str__() returns a readable message suitable for LLM consumption.

        When an LLM agent catches an error and needs to decide what to do,
        __str__() should give it enough context in plain English.
        """
        err = VmError(
            "execution failed",
            tx_hash="0xabc",
            vm_status="MOVE_ABORT",
        )
        s = str(err)
        assert "execution failed" in s
        assert len(s) < 500


# ---------------------------------------------------------------------------
# Error recovery helpers
# ---------------------------------------------------------------------------


class TestErrorRecoveryHelpers:
    """Helper methods that let bots make automated recovery decisions."""

    def test_all_errors_have_is_retryable(self):
        """Every error type exposes an is_retryable property.

        An automated trading bot loops over caught exceptions and must be able
        to call is_retryable on any DecibelError subclass without AttributeError.
        """
        errors = [
            ConfigError("x"),
            AuthenticationError("x"),
            ValidationError("x"),
            RateLimitError("x", retry_after_ms=0),
            SimulationError("x"),
            GasError("x"),
            SubmissionError("x"),
            VmError("x"),
            WebSocketError("x", disconnect_duration_ms=0),
            CriticalTradingError("x", affected_market="M", affected_order_ids=[]),
        ]
        for err in errors:
            assert hasattr(err, "is_retryable"), (
                f"{type(err).__name__} missing is_retryable"
            )
            assert isinstance(err.is_retryable, bool)

    def test_all_errors_have_retry_after_ms(self):
        """Every error type exposes a retry_after_ms property.

        Even errors that are not retryable should have retry_after_ms (typically 0
        or None) so the bot can use a uniform retry loop pattern:
            if err.is_retryable:
                await asyncio.sleep(err.retry_after_ms / 1000)
        """
        errors = [
            ConfigError("x"),
            AuthenticationError("x"),
            ValidationError("x"),
            RateLimitError("x", retry_after_ms=500),
            SimulationError("x"),
            GasError("x"),
            SubmissionError("x"),
            VmError("x"),
            WebSocketError("x", disconnect_duration_ms=0),
            CriticalTradingError("x", affected_market="M", affected_order_ids=[]),
        ]
        for err in errors:
            assert hasattr(err, "retry_after_ms"), (
                f"{type(err).__name__} missing retry_after_ms"
            )

    def test_is_retryable(self):
        """is_retryable is True for transient failures that may succeed on retry.

        Network errors, rate limits, and gas errors are all transient — the
        bot should wait and try again.
        """
        assert RateLimitError("x", retry_after_ms=100).is_retryable
        assert GasError("x").is_retryable
        assert SubmissionError("x").is_retryable

    def test_retry_after_ms(self):
        """retry_after_ms tells the bot exactly how long to wait.

        For rate limit errors, the server specifies the cooldown.  The bot
        should sleep for this duration before retrying.
        """
        err = RateLimitError("throttled", retry_after_ms=1500)
        assert err.retry_after_ms == 1500

    def test_is_critical(self):
        """is_critical is True only for CriticalTradingError.

        Critical errors mean protective orders have failed.  The bot must
        take emergency action (e.g. close all positions via market orders).
        """
        assert CriticalTradingError(
            "SL failed", affected_market="BTC-USD", affected_order_ids=[]
        ).is_critical
        assert not ConfigError("x").is_critical
        assert not SubmissionError("x").is_critical

    def test_needs_resync(self):
        """needs_resync is True when local state may be stale or corrupted.

        UNKNOWN and STALE errors both require the bot to re-fetch state
        from REST before making new trading decisions.
        """
        assert SubmissionError("timeout").needs_resync
        assert VmError("fail").needs_resync
        assert WebSocketError("lost", disconnect_duration_ms=6000).needs_resync
        assert not ConfigError("x").needs_resync
        assert not RateLimitError("x", retry_after_ms=0).needs_resync


# ---------------------------------------------------------------------------
# Inheritance: all errors share a common base for broad except clauses
# ---------------------------------------------------------------------------


class TestInheritance:
    """The error hierarchy must be catchable at the base level."""

    def test_all_errors_inherit_decibel_error(self):
        """Every SDK error is a DecibelError so bots can use a single except clause.

        Trading loops typically have an outer `except DecibelError` to catch
        any SDK-level failure and log it before deciding on recovery.
        """
        errors = [
            ConfigError("x"),
            AuthenticationError("x"),
            ValidationError("x"),
            RateLimitError("x", retry_after_ms=0),
            SimulationError("x"),
            GasError("x"),
            SubmissionError("x"),
            VmError("x"),
            WebSocketError("x", disconnect_duration_ms=0),
            CriticalTradingError("x", affected_market="M", affected_order_ids=[]),
        ]
        for err in errors:
            assert isinstance(err, DecibelError), (
                f"{type(err).__name__} does not inherit DecibelError"
            )

    def test_catch_base_class(self):
        """except DecibelError catches all SDK error subtypes.

        This is the canonical pattern for trading bot error handling:
            try:
                await client.place_order(...)
            except DecibelError as e:
                if e.is_critical:
                    emergency_close()
                elif e.needs_resync:
                    await resync_state()
        """
        with pytest.raises(DecibelError):
            raise ConfigError("test")

        with pytest.raises(DecibelError):
            raise CriticalTradingError(
                "test", affected_market="M", affected_order_ids=[]
            )

        with pytest.raises(DecibelError):
            raise VmError("test", tx_hash="0x1", vm_status="ABORT")
