"""Tests for utility functions with cross-SDK test vectors from Rust."""

from __future__ import annotations

from decibel_sdk.models.common import PageParams, SearchTermParams, SortDirection, SortParams
from decibel_sdk.utils.address import (
    bcs_serialize_string,
    create_object_address,
    get_market_addr,
    get_primary_subaccount_addr,
    get_vault_share_address,
    hex_to_bytes,
)
from decibel_sdk.utils.events import extract_order_id_from_events
from decibel_sdk.utils.nonce import generate_random_replay_protection_nonce
from decibel_sdk.utils.price import round_to_tick_size
from decibel_sdk.utils.query import construct_query_params


class TestBcsSerializeString:
    def test_btc_usd(self) -> None:
        result = bcs_serialize_string("BTC-USD")
        assert result[0] == 7  # length
        assert result[1:] == b"BTC-USD"

    def test_empty_string(self) -> None:
        result = bcs_serialize_string("")
        assert result == b"\x00"

    def test_long_string_uleb128(self) -> None:
        # String with length > 127 needs 2-byte ULEB128
        s = "x" * 128
        result = bcs_serialize_string(s)
        # ULEB128 of 128: 0x80, 0x01
        assert result[0] == 0x80
        assert result[1] == 0x01
        assert result[2:] == b"x" * 128


class TestHexToBytes:
    def test_with_prefix(self) -> None:
        assert hex_to_bytes("0xabcd") == bytes([0xAB, 0xCD])

    def test_without_prefix(self) -> None:
        assert hex_to_bytes("abcd") == bytes([0xAB, 0xCD])

    def test_odd_length(self) -> None:
        # Odd-length hex gets left-padded with 0
        assert hex_to_bytes("0xabc") == bytes([0x0A, 0xBC])

    def test_empty(self) -> None:
        assert hex_to_bytes("0x") == b""


class TestCreateObjectAddress:
    def test_deterministic(self) -> None:
        source = bytes(32)
        seed = b"test"
        result1 = create_object_address(source, seed)
        result2 = create_object_address(source, seed)
        assert result1 == result2
        assert len(result1) == 32

    def test_different_seeds_produce_different_addresses(self) -> None:
        source = bytes(32)
        addr1 = create_object_address(source, b"seed1")
        addr2 = create_object_address(source, b"seed2")
        assert addr1 != addr2

    def test_short_source_is_padded(self) -> None:
        short = bytes([0x01])
        full = bytes(31) + bytes([0x01])
        # Both should produce the same address since short gets right-justified
        addr_short = create_object_address(short, b"seed")
        addr_full = create_object_address(full, b"seed")
        assert addr_short == addr_full


class TestGetMarketAddr:
    def test_returns_hex_string(self) -> None:
        addr = get_market_addr("BTC-USD", "0x" + "ab" * 32)
        assert addr.startswith("0x")
        assert len(addr) == 66  # 0x + 64 hex chars

    def test_deterministic(self) -> None:
        perp_global = "0x" + "ab" * 32
        addr1 = get_market_addr("BTC-USD", perp_global)
        addr2 = get_market_addr("BTC-USD", perp_global)
        assert addr1 == addr2

    def test_different_markets_different_addrs(self) -> None:
        perp_global = "0x" + "ab" * 32
        btc = get_market_addr("BTC-USD", perp_global)
        eth = get_market_addr("ETH-USD", perp_global)
        assert btc != eth


class TestGetPrimarySubaccountAddr:
    def test_returns_hex_string(self) -> None:
        addr = get_primary_subaccount_addr(
            "0x" + "01" * 32,
            "v0.4",
            "0x" + "02" * 32,
        )
        assert addr.startswith("0x")
        assert len(addr) == 66

    def test_deterministic(self) -> None:
        a1 = get_primary_subaccount_addr("0x01", "v0.4", "0xpkg")
        a2 = get_primary_subaccount_addr("0x01", "v0.4", "0xpkg")
        assert a1 == a2


class TestGetVaultShareAddress:
    def test_returns_hex_string(self) -> None:
        addr = get_vault_share_address("0x" + "ff" * 32)
        assert addr.startswith("0x")
        assert len(addr) == 66

    def test_deterministic(self) -> None:
        a1 = get_vault_share_address("0x" + "aa" * 32)
        a2 = get_vault_share_address("0x" + "aa" * 32)
        assert a1 == a2


class TestRoundToTickSize:
    def test_round_down(self) -> None:
        assert round_to_tick_size(45123.45, 0.5, 2, False) == 45123.0

    def test_round_up(self) -> None:
        assert round_to_tick_size(45123.45, 0.5, 2, True) == 45123.5

    def test_exact_boundary(self) -> None:
        assert round_to_tick_size(100.0, 10.0, 0, False) == 100.0

    def test_round_down_larger_tick(self) -> None:
        assert round_to_tick_size(105.0, 10.0, 0, False) == 100.0

    def test_round_up_larger_tick(self) -> None:
        assert round_to_tick_size(105.0, 10.0, 0, True) == 110.0

    def test_zero_tick_size_returns_price(self) -> None:
        assert round_to_tick_size(123.45, 0.0, 2, False) == 123.45

    def test_negative_tick_size_returns_price(self) -> None:
        assert round_to_tick_size(123.45, -1.0, 2, False) == 123.45


class TestGenerateNonce:
    def test_returns_int(self) -> None:
        n = generate_random_replay_protection_nonce()
        assert isinstance(n, int)
        assert 0 <= n < 2**64

    def test_randomness(self) -> None:
        n1 = generate_random_replay_protection_nonce()
        n2 = generate_random_replay_protection_nonce()
        # Extremely unlikely to collide
        assert n1 != n2


class TestExtractOrderIdFromEvents:
    def test_extracts_from_matching_event(self) -> None:
        events = [
            {
                "type": "0xpkg::market_types::OrderEvent",
                "data": {
                    "user": "0xsub",
                    "order_id": "order123",
                },
            }
        ]
        assert extract_order_id_from_events(events, "0xsub") == "order123"

    def test_returns_none_for_wrong_user(self) -> None:
        events = [
            {
                "type": "0xpkg::market_types::OrderEvent",
                "data": {
                    "user": "0xother",
                    "order_id": "order123",
                },
            }
        ]
        assert extract_order_id_from_events(events, "0xsub") is None

    def test_returns_none_for_wrong_event_type(self) -> None:
        events = [
            {
                "type": "0xpkg::other::Event",
                "data": {
                    "user": "0xsub",
                    "order_id": "order123",
                },
            }
        ]
        assert extract_order_id_from_events(events, "0xsub") is None

    def test_returns_none_for_empty_events(self) -> None:
        assert extract_order_id_from_events([], "0xsub") is None

    def test_finds_first_matching(self) -> None:
        events = [
            {
                "type": "0xpkg::market_types::OrderEvent",
                "data": {"user": "0xother", "order_id": "wrong"},
            },
            {
                "type": "0xpkg::market_types::OrderEvent",
                "data": {"user": "0xsub", "order_id": "correct"},
            },
        ]
        assert extract_order_id_from_events(events, "0xsub") == "correct"


class TestConstructQueryParams:
    def test_all_params(self) -> None:
        page = PageParams(limit=10, offset=5)
        sort = SortParams(sort_key="volume", sort_dir=SortDirection.DESCENDING)
        search = SearchTermParams(search_term="BTC")
        params = construct_query_params(page, sort, search)
        assert ("limit", "10") in params
        assert ("offset", "5") in params
        assert ("sort_key", "volume") in params
        assert ("sort_dir", "DESC") in params
        assert ("search_term", "BTC") in params

    def test_empty_params(self) -> None:
        params = construct_query_params(PageParams(), SortParams(), SearchTermParams())
        assert params == []

    def test_partial_params(self) -> None:
        params = construct_query_params(
            PageParams(limit=20),
            SortParams(),
            SearchTermParams(),
        )
        assert params == [("limit", "20")]
