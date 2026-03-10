"""Tests for the error hierarchy and ApiResponse."""

from __future__ import annotations

from decibel_sdk.errors import (
    ApiError,
    ApiResponse,
    ConfigError,
    DecibelError,
    GasEstimationError,
    NetworkError,
    SerializationError,
    SigningError,
    SimulationError,
    TransactionError,
    ValidationError,
    WebSocketError,
)


class TestErrorHierarchy:
    def test_all_subclass_decibel_error(self) -> None:
        subclasses = [
            ConfigError,
            NetworkError,
            ApiError,
            ValidationError,
            TransactionError,
            SimulationError,
            SigningError,
            GasEstimationError,
            WebSocketError,
            SerializationError,
        ]
        for cls in subclasses:
            assert issubclass(cls, DecibelError)

    def test_config_error_message(self) -> None:
        err = ConfigError("bad config")
        assert str(err) == "bad config"
        assert isinstance(err, DecibelError)

    def test_api_error_fields(self) -> None:
        err = ApiError(status=404, status_text="Not Found", message="resource missing")
        assert err.status == 404
        assert err.status_text == "Not Found"
        assert err.message == "resource missing"
        assert "404" in str(err)

    def test_transaction_error_fields(self) -> None:
        err = TransactionError(
            message="vm error",
            transaction_hash="0xabc",
            vm_status="ABORTED",
        )
        assert err.transaction_hash == "0xabc"
        assert err.vm_status == "ABORTED"
        assert "vm error" in str(err)

    def test_transaction_error_optional_fields(self) -> None:
        err = TransactionError(message="failed")
        assert err.transaction_hash is None
        assert err.vm_status is None


class TestApiResponse:
    def test_generic_response(self) -> None:
        resp = ApiResponse(data={"key": "value"}, status=200, status_text="OK")
        assert resp.data == {"key": "value"}
        assert resp.status == 200
        assert resp.status_text == "OK"

    def test_typed_response(self) -> None:
        resp: ApiResponse[list[int]] = ApiResponse(data=[1, 2, 3], status=200, status_text="OK")
        assert resp.data == [1, 2, 3]
