"""Tests for all Pydantic model serialization/deserialization roundtrips."""

from __future__ import annotations

import json

from decibel_sdk.models import (
    AccountOverview,
    Candlestick,
    CandlestickInterval,
    Delegation,
    Leaderboard,
    LeaderboardItem,
    MarketContext,
    MarketDepth,
    MarketDepthAggregationSize,
    MarketOrder,
    MarketPrice,
    MarketTrade,
    OrderStatus,
    OrderStatusType,
    PageParams,
    PaginatedResponse,
    PerpMarketConfig,
    PlaceOrderResult,
    PortfolioChartData,
    SearchTermParams,
    SortDirection,
    SortParams,
    TimeInForce,
    TwapOrderResult,
    TwapStatus,
    UserActiveTwap,
    UserFundHistoryItem,
    UserNotification,
    UserOpenOrder,
    UserOwnedVault,
    UserPerformanceOnVault,
    UserPosition,
    UserSubaccount,
    Vault,
    VaultDeposit,
    VaultsResponse,
    VaultWithdrawal,
    VolumeWindow,
    WsSubscribeRequest,
)


class TestEnums:
    def test_time_in_force_values(self) -> None:
        assert TimeInForce.GOOD_TILL_CANCELED == 0
        assert TimeInForce.POST_ONLY == 1
        assert TimeInForce.IMMEDIATE_OR_CANCEL == 2

    def test_candlestick_interval_str(self) -> None:
        assert CandlestickInterval.ONE_MINUTE == "1m"
        assert CandlestickInterval.ONE_MONTH == "1mo"
        assert len(CandlestickInterval) == 13

    def test_volume_window_str(self) -> None:
        assert VolumeWindow.SEVEN_DAYS == "7d"
        assert VolumeWindow.NINETY_DAYS == "90d"

    def test_order_status_type(self) -> None:
        assert OrderStatusType.from_str("Acknowledged") == OrderStatusType.ACKNOWLEDGED
        assert OrderStatusType.from_str("Canceled") == OrderStatusType.CANCELLED
        assert OrderStatusType.from_str("Cancelled") == OrderStatusType.CANCELLED
        assert OrderStatusType.from_str("garbage") == OrderStatusType.UNKNOWN

    def test_order_status_type_properties(self) -> None:
        assert OrderStatusType.ACKNOWLEDGED.is_success
        assert OrderStatusType.FILLED.is_success
        assert not OrderStatusType.CANCELLED.is_success
        assert OrderStatusType.CANCELLED.is_failure
        assert OrderStatusType.REJECTED.is_failure
        assert OrderStatusType.FILLED.is_final
        assert not OrderStatusType.UNKNOWN.is_final

    def test_sort_direction(self) -> None:
        assert SortDirection.ASCENDING == "ASC"
        assert SortDirection.DESCENDING == "DESC"

    def test_twap_status(self) -> None:
        assert TwapStatus.ACTIVATED == "Activated"

    def test_market_depth_aggregation_size(self) -> None:
        assert MarketDepthAggregationSize.ONE == 1
        assert MarketDepthAggregationSize.THOUSAND == 1000


class TestPagination:
    def test_page_params_defaults(self) -> None:
        p = PageParams()
        assert p.limit is None
        assert p.offset is None

    def test_page_params_with_values(self) -> None:
        p = PageParams(limit=20, offset=5)
        assert p.limit == 20
        assert p.offset == 5

    def test_paginated_response(self) -> None:
        resp = PaginatedResponse[str](items=["a", "b"], total_count=10)
        assert resp.items == ["a", "b"]
        assert resp.total_count == 10

    def test_sort_params(self) -> None:
        s = SortParams(sort_key="volume", sort_dir=SortDirection.DESCENDING)
        assert s.sort_key == "volume"

    def test_search_term_params(self) -> None:
        s = SearchTermParams(search_term="BTC")
        assert s.search_term == "BTC"


class TestMarketModels:
    def test_perp_market_config_roundtrip(self) -> None:
        data = {
            "market_addr": "0xabc",
            "market_name": "BTC-USD",
            "sz_decimals": 4,
            "px_decimals": 2,
            "max_leverage": 50.0,
            "min_size": 0.001,
            "lot_size": 0.001,
            "tick_size": 0.5,
            "max_open_interest": 1000000.0,
            "margin_call_fee_pct": 0.5,
            "taker_in_next_block": True,
        }
        m = PerpMarketConfig.model_validate(data)
        assert m.market_name == "BTC-USD"
        assert m.model_dump() == data

    def test_market_depth(self) -> None:
        data = {
            "market": "BTC-USD",
            "bids": [{"price": 50000.0, "size": 1.5}],
            "asks": [{"price": 50001.0, "size": 2.0}],
            "unix_ms": 1700000000000,
        }
        depth = MarketDepth.model_validate(data)
        assert len(depth.bids) == 1
        assert depth.bids[0].price == 50000.0

    def test_market_price(self) -> None:
        data = {
            "market": "ETH-USD",
            "mark_px": 3000.5,
            "mid_px": 3000.0,
            "oracle_px": 3001.0,
            "funding_rate_bps": 0.01,
            "is_funding_positive": True,
            "open_interest": 500000.0,
            "transaction_unix_ms": 1700000000000,
        }
        p = MarketPrice.model_validate(data)
        assert p.mark_px == 3000.5

    def test_market_context(self) -> None:
        mc = MarketContext(
            market="BTC-USD",
            volume_24h=1e9,
            open_interest=5e8,
            previous_day_price=49000.0,
            price_change_pct_24h=2.5,
        )
        assert mc.volume_24h == 1e9

    def test_candlestick_alias(self) -> None:
        data = {
            "T": 1700000000,
            "c": 50000.0,
            "h": 51000.0,
            "i": "1h",
            "l": 49000.0,
            "o": 49500.0,
            "t": 1699996400,
            "v": 1000.0,
        }
        c = Candlestick.model_validate(data)
        assert c.close_timestamp == 1700000000
        dumped = c.model_dump(by_alias=True)
        assert "T" in dumped

    def test_market_trade(self) -> None:
        mt = MarketTrade(
            market="SOL-USD", price=100.0, size=10.0, is_buy=True, unix_ms=1700000000000
        )
        assert mt.is_buy is True


class TestAccountModels:
    def test_account_overview_minimal(self) -> None:
        data = {
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": -50.0,
            "unrealized_funding_cost": 0.5,
            "cross_margin_ratio": 0.1,
            "maintenance_margin": 500.0,
            "cross_account_position": 5000.0,
            "total_margin": 2000.0,
            "usdc_cross_withdrawable_balance": 8000.0,
            "usdc_isolated_withdrawable_balance": 1000.0,
        }
        ao = AccountOverview.model_validate(data)
        assert ao.cross_account_leverage_ratio is None
        assert ao.perp_equity_balance == 10000.0

    def test_account_overview_full(self) -> None:
        data = {
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": -50.0,
            "unrealized_funding_cost": 0.5,
            "cross_margin_ratio": 0.1,
            "maintenance_margin": 500.0,
            "cross_account_leverage_ratio": 5.0,
            "volume": 1000000.0,
            "net_deposits": 5000.0,
            "all_time_return": 0.15,
            "pnl_90d": 2000.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.1,
            "weekly_win_rate_12w": 0.6,
            "average_cash_position": 3000.0,
            "average_leverage": 3.0,
            "cross_account_position": 5000.0,
            "total_margin": 2000.0,
            "usdc_cross_withdrawable_balance": 8000.0,
            "usdc_isolated_withdrawable_balance": 1000.0,
            "realized_pnl": 1500.0,
            "liquidation_fees_paid": 10.0,
            "liquidation_losses": 0.0,
        }
        ao = AccountOverview.model_validate(data)
        assert ao.cross_account_leverage_ratio == 5.0
        assert ao.sharpe_ratio == 1.5

    def test_user_subaccount(self) -> None:
        s = UserSubaccount(
            subaccount_address="0xsub",
            primary_account_address="0xmain",
            is_primary=True,
        )
        assert s.custom_label is None
        assert s.is_active is None

    def test_delegation(self) -> None:
        d = Delegation(
            delegated_account="0xdel",
            permission_type="trading",
            expiration_time_s=1700000000,
        )
        assert d.expiration_time_s == 1700000000

    def test_user_fund_history_item(self) -> None:
        item = UserFundHistoryItem(
            amount=100.0, is_deposit=True, transaction_unix_ms=1700000000000, transaction_version=1
        )
        assert item.is_deposit

    def test_leaderboard(self) -> None:
        lb = Leaderboard(
            items=[
                LeaderboardItem(
                    rank=1,
                    account="0xabc",
                    account_value=100000.0,
                    realized_pnl=5000.0,
                    roi=0.05,
                    volume=1000000.0,
                )
            ],
            total_count=100,
        )
        assert lb.items[0].rank == 1

    def test_portfolio_chart_data(self) -> None:
        p = PortfolioChartData(timestamp=1700000000, value=10000.0)
        assert p.value == 10000.0

    def test_user_notification_alias(self) -> None:
        data = {
            "id": "n1",
            "type": "liquidation",
            "message": "Position liquidated",
            "timestamp": 1700000000,
            "read": False,
        }
        n = UserNotification.model_validate(data)
        assert n.notification_type == "liquidation"


class TestOrderModels:
    def test_user_open_order(self) -> None:
        data = {
            "market": "0xmarket",
            "order_id": "123",
            "price": 50000.0,
            "orig_size": 1.0,
            "remaining_size": 0.5,
            "is_buy": True,
            "time_in_force": "GoodTillCanceled",
            "is_reduce_only": False,
            "status": "Acknowledged",
            "transaction_unix_ms": 1700000000000,
            "transaction_version": 42,
        }
        o = UserOpenOrder.model_validate(data)
        assert o.client_order_id is None
        assert o.remaining_size == 0.5

    def test_order_status(self) -> None:
        os_data = {
            "parent": "0xparent",
            "market": "0xmarket",
            "order_id": "456",
            "status": "Filled",
            "orig_size": 1.0,
            "remaining_size": 0.0,
            "size_delta": 1.0,
            "price": 50000.0,
            "is_buy": True,
            "details": "fully filled",
            "transaction_version": 100,
            "unix_ms": 1700000000000,
        }
        o = OrderStatus.model_validate(os_data)
        assert o.status == "Filled"

    def test_user_active_twap(self) -> None:
        data = {
            "market": "0xmarket",
            "is_buy": True,
            "order_id": "twap1",
            "client_order_id": "client1",
            "is_reduce_only": False,
            "start_unix_ms": 1700000000000,
            "frequency_s": 60,
            "duration_s": 3600,
            "orig_size": 10.0,
            "remaining_size": 5.0,
            "status": "Activated",
            "transaction_unix_ms": 1700000000000,
            "transaction_version": 50,
        }
        t = UserActiveTwap.model_validate(data)
        assert t.frequency_s == 60


class TestPositionModels:
    def test_user_position(self) -> None:
        data = {
            "market": "0xmarket",
            "user": "0xuser",
            "size": 2.5,
            "user_leverage": 10.0,
            "entry_price": 48000.0,
            "is_isolated": False,
            "unrealized_funding": -5.0,
            "estimated_liquidation_price": 42000.0,
            "has_fixed_sized_tpsls": False,
        }
        p = UserPosition.model_validate(data)
        assert p.tp_order_id is None
        assert p.size == 2.5


class TestVaultModels:
    def test_vault_minimal(self) -> None:
        v = Vault(
            address="0xvault",
            name="Alpha Vault",
            manager="0xmanager",
            status="active",
            created_at=1700000000,
        )
        assert v.tvl is None
        assert v.social_links is None

    def test_vaults_response(self) -> None:
        resp = VaultsResponse(
            items=[],
            total_count=0,
            total_value_locked=0.0,
            total_volume=0.0,
        )
        assert resp.total_count == 0

    def test_user_owned_vault(self) -> None:
        uov = UserOwnedVault(
            vault_address="0xv",
            vault_name="My Vault",
            vault_share_symbol="MVLT",
            status="active",
            age_days=30,
            num_managers=1,
        )
        assert uov.apr is None

    def test_vault_deposit(self) -> None:
        vd = VaultDeposit(amount_usdc=1000.0, shares_received=100.0, timestamp_ms=1700000000000)
        assert vd.unlock_timestamp_ms is None

    def test_vault_withdrawal(self) -> None:
        vw = VaultWithdrawal(shares_redeemed=50.0, timestamp_ms=1700000000000, status="completed")
        assert vw.amount_usdc is None

    def test_user_performance_on_vault(self) -> None:
        vault = Vault(address="0xv", name="V", manager="0xm", status="active", created_at=0)
        perf = UserPerformanceOnVault(vault=vault, account_address="0xacc")
        assert perf.total_deposited is None


class TestPlaceOrderResult:
    def test_success(self) -> None:
        r = PlaceOrderResult.make_success("order123", "0xtxhash")
        assert r.success is True
        assert r.order_id == "order123"
        assert r.error is None

    def test_failure(self) -> None:
        r = PlaceOrderResult.make_failure("insufficient margin")
        assert r.success is False
        assert r.error == "insufficient margin"
        assert r.order_id is None


class TestTwapOrderResult:
    def test_create(self) -> None:
        r = TwapOrderResult(success=True, order_id="twap1", transaction_hash="0xabc")
        assert r.success


class TestWsSubscribeRequest:
    def test_subscribe(self) -> None:
        req = WsSubscribeRequest.subscribe("marketPrice:BTC-USD")
        assert req.method == "subscribe"
        assert req.subscription == "marketPrice:BTC-USD"
        payload = json.loads(req.model_dump_json())
        assert payload["method"] == "subscribe"

    def test_unsubscribe(self) -> None:
        req = WsSubscribeRequest.unsubscribe("marketPrice:BTC-USD")
        assert req.method == "unsubscribe"


class TestModelSerialization:
    def test_market_price_json_roundtrip(self) -> None:
        data = {
            "market": "BTC-USD",
            "mark_px": 50000.0,
            "mid_px": 49999.0,
            "oracle_px": 50001.0,
            "funding_rate_bps": 0.01,
            "is_funding_positive": True,
            "open_interest": 1000000.0,
            "transaction_unix_ms": 1700000000000,
        }
        m = MarketPrice.model_validate(data)
        json_str = m.model_dump_json()
        m2 = MarketPrice.model_validate_json(json_str)
        assert m == m2

    def test_paginated_response_json_roundtrip(self) -> None:
        data = {"items": [{"price": 100.0, "size": 1.0}], "total_count": 1}
        resp = PaginatedResponse[MarketOrder].model_validate(data)
        assert resp.items[0].price == 100.0
