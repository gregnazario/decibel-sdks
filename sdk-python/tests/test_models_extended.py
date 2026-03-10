"""Extended model tests: edge cases, nullable fields, enum variants."""

from __future__ import annotations

from decibel_sdk.models import (
    AccountOverview,
    CandlestickInterval,
    CrossedPosition,
    MarketDepthAggregationSize,
    OrderEvent,
    PerpPosition,
    TimeInForce,
    TradeAction,
    TwapEvent,
    UserFundingHistoryItem,
    UserPosition,
    UserTradeHistoryItem,
    VaultType,
    VolumeWindow,
)
from decibel_sdk.models.ws import (
    AccountOverviewWsMessage,
    AllMarketPricesWsMessage,
    CandlestickWsMessage,
    MarketDepthWsMessage,
    MarketPriceWsMessage,
    MarketTradesWsMessage,
    UserActiveTwapsWsMessage,
    UserFundingHistoryWsMessage,
    UserOpenOrdersWsMessage,
    UserOrderHistoryWsMessage,
    UserPositionsWsMessage,
    UserTradeHistoryWsMessage,
    WsMessage,
)


class TestEnumEdgeCases:
    def test_all_candlestick_intervals(self) -> None:
        expected = [
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1mo",
        ]
        assert [i.value for i in CandlestickInterval] == expected

    def test_all_volume_windows(self) -> None:
        expected = ["7d", "14d", "30d", "90d"]
        assert [w.value for w in VolumeWindow] == expected

    def test_time_in_force_int_values(self) -> None:
        assert int(TimeInForce.GOOD_TILL_CANCELED) == 0
        assert int(TimeInForce.POST_ONLY) == 1
        assert int(TimeInForce.IMMEDIATE_OR_CANCEL) == 2

    def test_trade_action_variants(self) -> None:
        assert TradeAction.OPEN_LONG == "OpenLong"
        assert TradeAction.NET == "Net"

    def test_vault_type(self) -> None:
        assert VaultType.USER == "user"
        assert VaultType.PROTOCOL == "protocol"

    def test_market_depth_aggregation_all(self) -> None:
        expected = [1, 2, 5, 10, 100, 1000]
        assert [int(s) for s in MarketDepthAggregationSize] == expected


class TestPositionNullableFields:
    def test_position_with_tp_sl(self) -> None:
        data = {
            "market": "0xm",
            "user": "0xu",
            "size": 1.0,
            "user_leverage": 10.0,
            "entry_price": 50000.0,
            "is_isolated": False,
            "unrealized_funding": 0.0,
            "estimated_liquidation_price": 40000.0,
            "tp_order_id": "tp1",
            "tp_trigger_price": 55000.0,
            "tp_limit_price": 54900.0,
            "sl_order_id": "sl1",
            "sl_trigger_price": 45000.0,
            "sl_limit_price": 45100.0,
            "has_fixed_sized_tpsls": True,
        }
        p = UserPosition.model_validate(data)
        assert p.tp_order_id == "tp1"
        assert p.sl_trigger_price == 45000.0


class TestPerpPositionAndCrossed:
    def test_perp_position(self) -> None:
        pp = PerpPosition(
            size=1.5,
            sz_decimals=4,
            entry_px=50000.0,
            max_leverage=50.0,
            is_long=True,
            token_type="BTC",
        )
        assert pp.is_long

    def test_crossed_position(self) -> None:
        cp = CrossedPosition(
            positions=[
                PerpPosition(
                    size=1.0,
                    sz_decimals=4,
                    entry_px=50000.0,
                    max_leverage=50.0,
                    is_long=True,
                    token_type="BTC",
                ),
            ]
        )
        assert len(cp.positions) == 1


class TestOrderEvents:
    def test_order_event(self) -> None:
        oe = OrderEvent(
            client_order_id="cid",
            details="filled",
            is_bid=True,
            is_taker=False,
            market="0xm",
            metadata_bytes="0x",
            order_id="oid",
            orig_size="1.0",
            parent="0xp",
            price="50000",
            remaining_size="0.0",
            size_delta="1.0",
            status="Filled",
            time_in_force=0,
            trigger_condition=None,
            user="0xu",
        )
        assert oe.is_bid

    def test_twap_event(self) -> None:
        te = TwapEvent(
            account="0xa",
            duration_s="3600",
            frequency_s="60",
            is_buy=True,
            is_reduce_only=False,
            market="0xm",
            order_id="tid",
            orig_size="10.0",
            remain_size="5.0",
            start_time_s="1700000000",
            status="Activated",
            client_order_id="cid",
        )
        assert te.duration_s == "3600"


class TestAccountOverviewAllNullable:
    def test_all_optional_fields_none(self) -> None:
        data = {
            "perp_equity_balance": 0.0,
            "unrealized_pnl": 0.0,
            "unrealized_funding_cost": 0.0,
            "cross_margin_ratio": 0.0,
            "maintenance_margin": 0.0,
            "cross_account_position": 0.0,
            "total_margin": 0.0,
            "usdc_cross_withdrawable_balance": 0.0,
            "usdc_isolated_withdrawable_balance": 0.0,
        }
        ao = AccountOverview.model_validate(data)
        assert ao.cross_account_leverage_ratio is None
        assert ao.volume is None
        assert ao.realized_pnl is None
        assert ao.liquidation_losses is None


class TestWsMessageWrappers:
    def test_account_overview_ws(self) -> None:
        data = {
            "account_overview": {
                "perp_equity_balance": 100.0,
                "unrealized_pnl": 0.0,
                "unrealized_funding_cost": 0.0,
                "cross_margin_ratio": 0.0,
                "maintenance_margin": 0.0,
                "cross_account_position": 0.0,
                "total_margin": 0.0,
                "usdc_cross_withdrawable_balance": 0.0,
                "usdc_isolated_withdrawable_balance": 0.0,
            }
        }
        msg = AccountOverviewWsMessage.model_validate(data)
        assert msg.account_overview.perp_equity_balance == 100.0

    def test_user_positions_ws(self) -> None:
        msg = UserPositionsWsMessage(positions=[])
        assert msg.positions == []

    def test_user_open_orders_ws(self) -> None:
        msg = UserOpenOrdersWsMessage(orders=[])
        assert msg.orders == []

    def test_user_order_history_ws(self) -> None:
        msg = UserOrderHistoryWsMessage(orders=[])
        assert msg.orders == []

    def test_user_trade_history_ws(self) -> None:
        msg = UserTradeHistoryWsMessage(trades=[])
        assert msg.trades == []

    def test_user_funding_history_ws(self) -> None:
        msg = UserFundingHistoryWsMessage(funding=[])
        assert msg.funding == []

    def test_market_price_ws_flattened(self) -> None:
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
        msg = MarketPriceWsMessage.model_validate(data)
        assert msg.mark_px == 50000.0

    def test_all_market_prices_ws(self) -> None:
        msg = AllMarketPricesWsMessage(prices=[])
        assert msg.prices == []

    def test_market_trades_ws(self) -> None:
        msg = MarketTradesWsMessage(trades=[])
        assert msg.trades == []

    def test_candlestick_ws(self) -> None:
        candle_data = {
            "T": 1700000000,
            "c": 50000.0,
            "h": 51000.0,
            "i": "1h",
            "l": 49000.0,
            "o": 49500.0,
            "t": 1699996400,
            "v": 1000.0,
        }
        msg = CandlestickWsMessage(candle=candle_data)  # type: ignore[arg-type]
        assert msg.candle.close_timestamp == 1700000000

    def test_market_depth_ws_flattened(self) -> None:
        data = {
            "market": "BTC-USD",
            "bids": [{"price": 50000.0, "size": 1.0}],
            "asks": [{"price": 50001.0, "size": 1.0}],
            "unix_ms": 1700000000000,
        }
        msg = MarketDepthWsMessage.model_validate(data)
        assert msg.market == "BTC-USD"

    def test_user_active_twaps_ws(self) -> None:
        msg = UserActiveTwapsWsMessage(twaps=[])
        assert msg.twaps == []

    def test_ws_message_generic(self) -> None:
        data = {"channel": "test", "data": {"key": "value"}}
        msg = WsMessage[dict[str, str]].model_validate(data)
        assert msg.channel == "test"
        assert msg.data["key"] == "value"


class TestTradeHistoryItem:
    def test_full_trade(self) -> None:
        item = UserTradeHistoryItem(
            account="0xa",
            market="BTC-USD",
            action="OpenLong",
            size=1.0,
            price=50000.0,
            is_profit=True,
            realized_pnl_amount=100.0,
            is_funding_positive=True,
            realized_funding_amount=5.0,
            is_rebate=False,
            fee_amount=10.0,
            transaction_unix_ms=1700000000000,
            transaction_version=1,
        )
        assert item.action == "OpenLong"


class TestFundingHistoryItem:
    def test_funding_item(self) -> None:
        item = UserFundingHistoryItem(
            market="0xm",
            funding_rate_bps=0.01,
            is_funding_positive=True,
            funding_amount=5.0,
            position_size=10.0,
            transaction_unix_ms=1700000000000,
            transaction_version=1,
        )
        assert item.funding_rate_bps == 0.01
