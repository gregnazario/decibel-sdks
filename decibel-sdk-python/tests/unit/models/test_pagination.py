"""TDD tests for pagination and sorting models.

PageParams, SortParams, and PaginatedResponse are used on every list
endpoint.  These tests lock down default values and generic-type
behaviour so consumers can rely on consistent pagination semantics.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from decibel.models.common import PageParams, PaginatedResponse, SortParams
from decibel.models.enums import SortDirection
from decibel.models.market import MarketPrice

from tests.conftest import NOW_MS


# ===================================================================
# PageParams
# ===================================================================


class TestPageParams:
    """Contract tests for pagination parameters."""

    def test_page_params_defaults(self) -> None:
        """Default PageParams: limit=10, offset=0.

        Callers that omit pagination should get the first 10 items.
        """
        params = PageParams()
        assert params.limit == 10
        assert params.offset == 0

    def test_page_params_custom(self) -> None:
        """Custom limit and offset are preserved."""
        params = PageParams(limit=50, offset=200)
        assert params.limit == 50
        assert params.offset == 200

    def test_page_params_roundtrip(self, custom_page_params: PageParams) -> None:
        """Serialise → deserialise roundtrip."""
        data = custom_page_params.model_dump()
        restored = PageParams(**data)
        assert restored == custom_page_params

    def test_page_params_json_roundtrip(self, custom_page_params: PageParams) -> None:
        """JSON roundtrip."""
        json_str = custom_page_params.model_dump_json()
        restored = PageParams.model_validate_json(json_str)
        assert restored == custom_page_params

    def test_page_params_limit_min(self) -> None:
        """limit must be >= 1."""
        with pytest.raises(ValidationError):
            PageParams(limit=0)

    def test_page_params_limit_max(self) -> None:
        """limit must be <= 1000."""
        with pytest.raises(ValidationError):
            PageParams(limit=1001)

    def test_page_params_offset_non_negative(self) -> None:
        """offset must be >= 0."""
        with pytest.raises(ValidationError):
            PageParams(offset=-1)

    def test_page_params_none_limit(self) -> None:
        """limit=None is allowed (field is Optional)."""
        params = PageParams(limit=None)
        assert params.limit is None


# ===================================================================
# SortParams
# ===================================================================


class TestSortParams:
    """Contract tests for sorting parameters."""

    def test_sort_params_defaults(self) -> None:
        """Default SortParams: both fields are None (server decides)."""
        params = SortParams()
        assert params.sort_key is None
        assert params.sort_dir is None

    def test_sort_params_custom(self) -> None:
        """Custom sort key and direction."""
        params = SortParams(
            sort_key="transaction_unix_ms",
            sort_dir=SortDirection.DESCENDING,
        )
        assert params.sort_key == "transaction_unix_ms"
        assert params.sort_dir == SortDirection.DESCENDING

    def test_sort_params_roundtrip(self, desc_sort_params: SortParams) -> None:
        """Serialise → deserialise roundtrip."""
        data = desc_sort_params.model_dump()
        restored = SortParams(**data)
        assert restored == desc_sort_params

    def test_sort_params_json_roundtrip(self, desc_sort_params: SortParams) -> None:
        """JSON roundtrip."""
        json_str = desc_sort_params.model_dump_json()
        restored = SortParams.model_validate_json(json_str)
        assert restored == desc_sort_params

    def test_sort_params_ascending(self) -> None:
        """Ascending sort direction."""
        params = SortParams(sort_key="price", sort_dir=SortDirection.ASCENDING)
        assert params.sort_dir == SortDirection.ASCENDING


# ===================================================================
# PaginatedResponse
# ===================================================================


class TestPaginatedResponse:
    """Contract tests for the generic paginated response.

    PaginatedResponse[T] wraps a list of items with a total count,
    enabling offset-based pagination on any list endpoint.
    """

    def test_paginated_response_int_items(self) -> None:
        """PaginatedResponse with int items."""
        resp = PaginatedResponse[int](items=[1, 2, 3], total_count=100)
        assert resp.items == [1, 2, 3]
        assert resp.total_count == 100

    def test_paginated_response_str_items(self) -> None:
        """PaginatedResponse with string items."""
        resp = PaginatedResponse[str](items=["a", "b"], total_count=50)
        assert len(resp.items) == 2
        assert resp.total_count == 50

    def test_paginated_response_model_items(self) -> None:
        """PaginatedResponse wrapping Pydantic models (MarketPrice).

        This is the real-world usage: paginated lists of typed models.
        """
        prices = [
            MarketPrice(
                market="BTC-USD",
                mark_px=95_000.0,
                mid_px=95_000.5,
                oracle_px=95_010.0,
                funding_rate_bps=0.75,
                is_funding_positive=True,
                open_interest=120.5,
                transaction_unix_ms=NOW_MS,
            ),
            MarketPrice(
                market="ETH-USD",
                mark_px=3_500.0,
                mid_px=3_500.25,
                oracle_px=3_501.0,
                funding_rate_bps=-0.30,
                is_funding_positive=False,
                open_interest=2_500.0,
                transaction_unix_ms=NOW_MS,
            ),
        ]
        resp = PaginatedResponse[MarketPrice](items=prices, total_count=2)
        assert len(resp.items) == 2
        assert resp.items[0].market == "BTC-USD"
        assert resp.items[1].market == "ETH-USD"
        assert resp.total_count == 2

    def test_paginated_response_empty(self) -> None:
        """PaginatedResponse with no items."""
        resp = PaginatedResponse[int](items=[], total_count=0)
        assert resp.items == []
        assert resp.total_count == 0

    def test_paginated_response_roundtrip_ints(self) -> None:
        """Serialise → deserialise roundtrip with int items."""
        resp = PaginatedResponse[int](items=[10, 20], total_count=2)
        data = resp.model_dump()
        restored = PaginatedResponse[int](**data)
        assert restored.items == [10, 20]
        assert restored.total_count == 2

    def test_paginated_response_json_roundtrip_ints(self) -> None:
        """JSON roundtrip with int items."""
        resp = PaginatedResponse[int](items=[10, 20], total_count=2)
        json_str = resp.model_dump_json()
        restored = PaginatedResponse[int].model_validate_json(json_str)
        assert restored.items == [10, 20]
        assert restored.total_count == 2

    def test_paginated_response_total_count_mismatch(self) -> None:
        """total_count may differ from len(items) (represents total across pages).

        This is by design for offset-based pagination: the server returns
        a page of items but total_count reflects all matching records.
        """
        resp = PaginatedResponse[int](items=[1, 2, 3], total_count=500)
        assert len(resp.items) == 3
        assert resp.total_count == 500
