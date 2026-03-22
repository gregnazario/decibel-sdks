"""Exception classes for the Decibel SDK with position-safety classification.

Every error carries a ``position_safety`` level that tells a trading bot
whether its local view of positions can still be trusted:

* **SAFE** -- no state change occurred; local view is accurate.
* **UNKNOWN** -- state *may* have changed; must reconcile before trading.
* **STALE** -- local state is outdated (e.g. long WebSocket disconnect).
* **CRITICAL** -- protective orders may have failed; emergency action required.
"""

from __future__ import annotations

import enum
import json
from typing import Any

# ---------------------------------------------------------------------------
# Position safety enum
# ---------------------------------------------------------------------------

class PositionSafety(enum.Enum):
    SAFE = "safe"
    UNKNOWN = "unknown"
    STALE = "stale"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Base error
# ---------------------------------------------------------------------------

class DecibelError(Exception):
    """Base error class for all SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        position_safety: PositionSafety = PositionSafety.SAFE,
        code: str | None = None,
        is_retryable: bool = False,
        retry_after_ms: int = 0,
        kind: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.position_safety = position_safety
        self.code = code or kind or type(self).__name__
        self.is_retryable = is_retryable
        self.retry_after_ms = retry_after_ms
        self.kind = kind or self.code
        self.cause = cause

    # -- recovery helpers --------------------------------------------------

    @property
    def is_critical(self) -> bool:
        return self.position_safety == PositionSafety.CRITICAL

    @property
    def needs_resync(self) -> bool:
        return self.position_safety in (PositionSafety.UNKNOWN, PositionSafety.STALE)

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "position_safety": self.position_safety.value,
            "is_retryable": self.is_retryable,
            "retry_after_ms": self.retry_after_ms,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(message={self.message!r}, "
            f"position_safety={self.position_safety!r})"
        )


# ---------------------------------------------------------------------------
# SAFE errors -- no on-chain state change
# ---------------------------------------------------------------------------

class ConfigError(DecibelError):
    """Configuration-related errors."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            kind="config",
            cause=cause,
        )


class AuthenticationError(DecibelError):
    """Authentication / authorisation failure."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            kind="authentication",
            cause=cause,
        )


class ValidationError(DecibelError):
    """Request or parameter validation failure."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        constraint: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            kind="validation",
            cause=cause,
        )
        self.field = field
        self.constraint = constraint


class RateLimitError(DecibelError):
    """Request was throttled by the server."""

    def __init__(self, message: str, *, retry_after_ms: int = 0) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            is_retryable=True,
            retry_after_ms=retry_after_ms,
            kind="rate_limit",
        )


class SimulationError(DecibelError):
    """Transaction simulation failure (tx was never submitted)."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            kind="simulation",
            cause=cause,
        )


class GasError(DecibelError):
    """Gas estimation or funding failure (tx was never submitted)."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            is_retryable=True,
            kind="gas",
            cause=cause,
        )


# ---------------------------------------------------------------------------
# UNKNOWN safety -- state may have changed
# ---------------------------------------------------------------------------

class SubmissionError(DecibelError):
    """Transaction broadcast may or may not have landed on-chain."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.UNKNOWN,
            is_retryable=True,
            kind="submission",
            cause=cause,
        )


class VmError(DecibelError):
    """Transaction executed but the Move VM rejected it."""

    def __init__(
        self,
        message: str,
        *,
        tx_hash: str | None = None,
        vm_status: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.UNKNOWN,
            kind="vm",
            cause=cause,
        )
        self.tx_hash = tx_hash
        self.vm_status = vm_status


# ---------------------------------------------------------------------------
# STALE / dynamic safety
# ---------------------------------------------------------------------------

class WebSocketError(DecibelError):
    """WebSocket connection or subscription error.

    Safety depends on how long the connection was down: >5 s is STALE,
    otherwise SAFE.
    """

    _STALE_THRESHOLD_MS = 5000

    def __init__(
        self,
        message: str,
        *,
        disconnect_duration_ms: int = 0,
        cause: Exception | None = None,
    ) -> None:
        safety = (
            PositionSafety.STALE
            if disconnect_duration_ms > self._STALE_THRESHOLD_MS
            else PositionSafety.SAFE
        )
        super().__init__(
            message,
            position_safety=safety,
            is_retryable=True,
            kind="websocket",
            cause=cause,
        )
        self.disconnect_duration_ms = disconnect_duration_ms


# ---------------------------------------------------------------------------
# CRITICAL safety
# ---------------------------------------------------------------------------

class CriticalTradingError(DecibelError):
    """A protective order (stop-loss / take-profit) failed."""

    def __init__(
        self,
        message: str,
        *,
        affected_market: str,
        affected_order_ids: list[str],
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.CRITICAL,
            kind="critical_trading",
            cause=cause,
        )
        self.affected_market = affected_market
        self.affected_order_ids = affected_order_ids


# ---------------------------------------------------------------------------
# Legacy / general errors (preserved for backward compatibility)
# ---------------------------------------------------------------------------

class NetworkError(DecibelError):
    """Network / HTTP connection errors."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.UNKNOWN,
            is_retryable=True,
            kind="network",
            cause=cause,
        )


class APIError(DecibelError):
    """REST API returned non-2xx status."""

    def __init__(
        self,
        status: int,
        status_text: str,
        message: str,
    ) -> None:
        super().__init__(message, kind="api")
        self.status = status
        self.status_text = status_text

    def __str__(self) -> str:
        return f"API error (status {self.status} {self.status_text}): {self.message}"


class TransactionError(DecibelError):
    """On-chain transaction failure."""

    def __init__(
        self,
        message: str,
        *,
        transaction_hash: str | None = None,
        vm_status: str | None = None,
    ) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.UNKNOWN,
            kind="transaction",
        )
        self.transaction_hash = transaction_hash
        self.vm_status = vm_status


class SigningError(DecibelError):
    """Transaction signing failure."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message, kind="signing", cause=cause)


class GasEstimationError(DecibelError):
    """Gas estimation failure."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.SAFE,
            is_retryable=True,
            kind="gas_estimation",
            cause=cause,
        )


class SerializationError(DecibelError):
    """JSON serialization / deserialization error."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message, kind="serialization", cause=cause)


class TimeoutError(DecibelError):
    """Request / transaction timeout."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            position_safety=PositionSafety.UNKNOWN,
            is_retryable=True,
            kind="timeout",
            cause=cause,
        )
