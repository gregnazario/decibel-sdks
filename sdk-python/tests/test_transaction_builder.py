"""Tests for the transaction builder."""

from __future__ import annotations

from decibel_sdk.transaction.builder import TransactionPayload


class TestTransactionPayload:
    def test_basic_payload(self) -> None:
        payload = TransactionPayload(
            function="0xpkg::module::function",
            type_arguments=["0x1::aptos_coin::AptosCoin"],
            arguments=["arg1", 42],
        )
        assert payload.function == "0xpkg::module::function"
        assert len(payload.type_arguments) == 1
        assert len(payload.arguments) == 2

    def test_to_dict(self) -> None:
        payload = TransactionPayload(
            function="0xpkg::dex::place_order",
            arguments=["0xsub", "0xmarket", 50000.0],
        )
        d = payload.to_dict()
        assert d["function"] == "0xpkg::dex::place_order"
        assert d["type_arguments"] == []
        assert d["arguments"] == ["0xsub", "0xmarket", 50000.0]

    def test_defaults(self) -> None:
        payload = TransactionPayload(function="0xpkg::mod::fn")
        assert payload.type_arguments == []
        assert payload.arguments == []
