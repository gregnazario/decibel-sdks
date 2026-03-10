"""Exception hierarchy and API response wrapper for the Decibel SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class DecibelError(Exception):
    """Base exception for all Decibel SDK errors."""


class ConfigError(DecibelError):
    """Invalid configuration."""


class NetworkError(DecibelError):
    """HTTP/WS connection failure."""


class ApiError(DecibelError):
    """REST API returned a non-2xx status."""

    def __init__(self, status: int, status_text: str, message: str) -> None:
        self.status = status
        self.status_text = status_text
        self.message = message
        super().__init__(f"API error (status {status}): {message}")


class ValidationError(DecibelError):
    """Response schema validation failure."""


class TransactionError(DecibelError):
    """On-chain transaction failure."""

    def __init__(
        self,
        message: str,
        transaction_hash: str | None = None,
        vm_status: str | None = None,
    ) -> None:
        self.transaction_hash = transaction_hash
        self.vm_status = vm_status
        super().__init__(message)


class SimulationError(DecibelError):
    """Transaction simulation failure."""


class SigningError(DecibelError):
    """Transaction signing failure."""


class GasEstimationError(DecibelError):
    """Gas estimation failure."""


class WebSocketError(DecibelError):
    """WebSocket error."""


class SerializationError(DecibelError):
    """JSON serialization failure."""


class TimeoutError(DecibelError):  # noqa: A001
    """Request/transaction timeout."""


@dataclass
class ApiResponse(Generic[T]):
    """Wrapper for API responses carrying typed data plus HTTP status info."""

    data: T
    status: int
    status_text: str
