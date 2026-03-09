"""Exception classes for the Decibel SDK."""

from typing import Any


class DecibelError(Exception):
    """Base error class for all SDK errors."""

    def __init__(
        self,
        message: str,
        kind: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Human-readable error message
            kind: Error category/type
            cause: Underlying exception that caused this error
        """
        super().__init__(message)
        self.kind = kind
        self.cause = cause
        self.message = message

    def __str__(self) -> str:
        """Return error string representation."""
        if self.cause:
            return f"{self.kind} error: {self.message}: {self.cause}"
        return f"{self.kind} error: {self.message}"

    def __repr__(self) -> str:
        """Return error representation."""
        return f"{self.__class__.__name__}(kind={self.kind!r}, message={self.message!r}, cause={self.cause!r})"


class ConfigError(DecibelError):
    """Configuration-related errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="config", cause=cause)


class NetworkError(DecibelError):
    """Network/HTTP connection errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="network", cause=cause)


class APIError(DecibelError):
    """REST API returned non-2xx status.

    Attributes:
        status: HTTP status code
        status_text: HTTP status text
        message: Error message from server
    """

    def __init__(
        self,
        status: int,
        status_text: str,
        message: str,
    ) -> None:
        self.status = status
        self.status_text = status_text
        super().__init__(message, kind="api")
        self.message = message

    def __str__(self) -> str:
        """Return error string representation."""
        return f"API error (status {self.status} {self.status_text}): {self.message}"


class ValidationError(DecibelError):
    """Response schema validation failure."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="validation", cause=cause)


class TransactionError(DecibelError):
    """On-chain transaction failure.

    Attributes:
        transaction_hash: Transaction hash (if submitted)
        vm_status: Move VM error status
        message: Human-readable error message
    """

    def __init__(
        self,
        message: str,
        transaction_hash: str | None = None,
        vm_status: str | None = None,
    ) -> None:
        self.transaction_hash = transaction_hash
        self.vm_status = vm_status
        super().__init__(message, kind="transaction")
        self.message = message

    def __str__(self) -> str:
        """Return error string representation."""
        parts = [f"transaction error: {self.message}"]
        if self.transaction_hash:
            parts.append(f"hash: {self.transaction_hash}")
        if self.vm_status:
            parts.append(f"vm_status: {self.vm_status}")
        return ", ".join(parts)


class SimulationError(DecibelError):
    """Transaction simulation failure."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="simulation", cause=cause)


class SigningError(DecibelError):
    """Transaction signing failure."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="signing", cause=cause)


class GasEstimationError(DecibelError):
    """Gas estimation failure."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="gas_estimation", cause=cause)


class WebSocketError(DecibelError):
    """WebSocket connection/subscription error."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="websocket", cause=cause)


class SerializationError(DecibelError):
    """JSON serialization/deserialization error."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="serialization", cause=cause)


class TimeoutError(DecibelError):
    """Request/transaction timeout."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, kind="timeout", cause=cause)
