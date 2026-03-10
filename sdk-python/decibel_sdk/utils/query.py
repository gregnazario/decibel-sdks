"""Query parameter construction utilities."""

from __future__ import annotations

from decibel_sdk.models.common import PageParams, SearchTermParams, SortParams


def construct_query_params(
    page: PageParams,
    sort: SortParams,
    search: SearchTermParams,
) -> list[tuple[str, str]]:
    """Build URL query parameters from pagination, sort, and search params."""
    params: list[tuple[str, str]] = []

    if page.limit is not None:
        params.append(("limit", str(page.limit)))
    if page.offset is not None:
        params.append(("offset", str(page.offset)))
    if sort.sort_key is not None:
        params.append(("sort_key", sort.sort_key))
    if sort.sort_dir is not None:
        params.append(("sort_dir", sort.sort_dir.value))
    if search.search_term is not None:
        params.append(("search_term", search.search_term))

    return params
