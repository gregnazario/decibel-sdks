"""Tests for data models."""

import pytest
from pydantic import ValidationError

from decibel.models.account import AccountOverview, UserPosition
from decibel.models.common import PageParams, PaginatedResponse, PlaceOrderResult
from decibel.models.enums import (
    CandlestickInterval,
    MarketDepthAggregationSize,
    OrderStatusType,
    SortDirection,
    TimeInForce,
    TwapStatus,
    VaultType,
    VolumeWindow,
)
from decibel.models.market import MarketDepth, MarketOrder, MarketPrice, PerpMarketConfig


def test_perp_market_config_model():
    """Test PerpMarketConfig model."""
    data = {
        "market_addr": "0x123",
        "market_name": "BTC-USD",
        "sz_decimals": 8,
        "px_decimals": 8,
        "max_leverage": 10.0,
        "min_size": 0.001,
        "lot_size": 0.001,
        "tick_size": 0.01,
        "max_open_interest": 1000000.0,
        "margin_call_fee_pct": 0.005,
        "taker_in_next_block": True,
    }
    market = PerpMarketConfig(**data)
    assert market.market_name == "BTC-USD"
    assert market.max_leverage == 10.0


def test_market_price_model():
    """Test MarketPrice model."""
    data = {
        "market": "BTC-USD",
        "mark_px": 45000.0,
        "mid_px": 45000.5,
        "oracle_px": 45001.0,
        "funding_rate_bps": 0.01,
        "is_funding_positive": True,
        "open_interest": 1000.0,
        "transaction_unix_ms": 1708000000000,
    }
    price = MarketPrice(**data)
    assert price.market == "BTC-USD"
    assert price.mark_px == 45000.0


def test_market_depth_model():
    """Test MarketDepth model."""
    data = {
        "market": "BTC-USD",
        "bids": [{"price": 44999.0, "size": 1.5}, {"price": 44998.0, "size": 2.0}],
        "asks": [{"price": 45001.0, "size": 1.0}, {"price": 45002.0, "size": 3.0}],
        "unix_ms": 1708000000000,
    }
    depth = MarketDepth(**data)
    assert len(depth.bids) == 2
    assert depth.bids[0].price == 44999.0


def test_account_overview_model():
    """Test AccountOverview model."""
    data = {
        "perp_equity_balance": 10000.0,
        "unrealized_pnl": 500.0,
        "unrealized_funding_cost": 10.0,
        "cross_margin_ratio": 0.5,
        "maintenance_margin": 100.0,
        "cross_account_position": 5000.0,
        "total_margin": 2000.0,
        "usdc_cross_withdrawable_balance": 8000.0,
        "usdc_isolated_withdrawable_balance": 0.0,
    }
    overview = AccountOverview(**data)
    assert overview.perp_equity_balance == 10000.0
    assert overview.unrealized_pnl == 500.0


def test_user_position_model():
    """Test UserPosition model."""
    data = {
        "market": "0x123",
        "user": "0x456",
        "size": 1.5,
        "user_leverage": 5.0,
        "entry_price": 44000.0,
        "is_isolated": False,
        "unrealized_funding": 5.0,
        "estimated_liquidation_price": 40000.0,
        "has_fixed_sized_tpsls": False,
    }
    position = UserPosition(**data)
    assert position.size == 1.5
    assert position.is_isolated is False


def test_page_params_model():
    """Test PageParams model."""
    params = PageParams(limit=10, offset=0)
    assert params.limit == 10
    assert params.offset == 0

    # Test default values
    params_default = PageParams()
    assert params_default.limit == 10
    assert params_default.offset == 0


def test_paginated_response_model():
    """Test PaginatedResponse model."""
    data = {"items": [1, 2, 3], "total_count": 3}
    response = PaginatedResponse[int](**data)
    assert len(response.items) == 3
    assert response.total_count == 3


def test_place_order_result_model():
    """Test PlaceOrderResult model."""
    success_data = {"success": True, "order_id": "12345", "transaction_hash": "0xabc"}
    result = PlaceOrderResult(**success_data)
    assert result.success is True
    assert result.order_id == "12345"

    failure_data = {"success": False, "error": "Insufficient balance"}
    result = PlaceOrderResult(**failure_data)
    assert result.success is False
    assert result.error == "Insufficient balance"


def test_enum_values():
    """Test enum values."""
    assert TimeInForce.GOOD_TILL_CANCELED.value == 0
    assert TimeInForce.POST_ONLY.value == 1
    assert TimeInForce.IMMEDIATE_OR_CANCEL.value == 2

    assert CandlestickInterval.ONE_MINUTE.value == "1m"
    assert CandlestickInterval.ONE_HOUR.value == "1h"

    assert OrderStatusType.ACKNOWLEDGED.value == "Acknowledged"
    assert OrderStatusType.FILLED.value == "Filled"


def test_order_status_type_methods():
    """Test OrderStatusType helper methods."""
    assert OrderStatusType.ACKNOWLEDGED.is_success() is True
    assert OrderStatusType.FILLED.is_success() is True
    assert OrderStatusType.CANCELLED.is_failure() is True
    assert OrderStatusType.REJECTED.is_failure() is True
    assert OrderStatusType.ACKNOWLEDGED.is_final() is True


def test_order_status_type_parse():
    """Test OrderStatusType parsing."""
    assert OrderStatusType.parse("Acknowledged") == OrderStatusType.ACKNOWLEDGED
    assert OrderStatusType.parse("Filled") == OrderStatusType.FILLED
    assert OrderStatusType.parse("Cancelled") == OrderStatusType.CANCELLED
    assert OrderStatusType.parse("Canceled") == OrderStatusType.CANCELLED
    assert OrderStatusType.parse("Rejected") == OrderStatusType.REJECTED
    assert OrderStatusType.parse("Unknown") == OrderStatusType.UNKNOWN


def test_market_depth_aggregation_sizes():
    """Test MarketDepthAggregationSize."""
    sizes = MarketDepthAggregationSize.all_sizes()
    assert MarketDepthAggregationSize.SIZE_1 in sizes
    assert MarketDepthAggregationSize.SIZE_100 in sizes
