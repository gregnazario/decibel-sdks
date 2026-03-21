"""TDD tests for trade history data models.

These tests define the API contract for UserTradeHistoryItem,
UserFundingHistoryItem, and UserFundHistoryItem.  Computed properties
(net_pnl, notional) are specified here before implementation.
"""

from __future__ import annotations

import pytest

from decibel.models.account import (
    UserFundHistoryItem,
    UserFundingHistoryItem,
    UserTradeHistoryItem,
)
from decibel.models.enums import TradeAction
from tests.conftest import NOW_MS

BTC_MARKET_ADDR = "0xabc123"
PRIMARY_ADDR = "0xsub1"


# ===================================================================
# UserTradeHistoryItem
# ===================================================================


class TestUserTradeHistoryItem:
    """Contract tests for the trade history item model.

    Every trade event is recorded with PnL, funding, and fee breakdowns.
    Computed helpers (net_pnl, notional) aggregate these for display.
    """

    def test_user_trade_history_roundtrip(
        self, user_trade_history_item: UserTradeHistoryItem
    ) -> None:
        """Serialise → deserialise must preserve every field.

        Trade history is the audit trail for PnL reports; lossless
        serialization is critical.
        """
        data = user_trade_history_item.model_dump()
        restored = UserTradeHistoryItem(**data)
        assert restored == user_trade_history_item

    def test_user_trade_history_json_roundtrip(
        self, user_trade_history_item: UserTradeHistoryItem
    ) -> None:
        """JSON wire-format roundtrip."""
        json_str = user_trade_history_item.model_dump_json()
        restored = UserTradeHistoryItem.model_validate_json(json_str)
        assert restored == user_trade_history_item

    def test_user_trade_history_net_pnl(
        self, user_trade_history_item: UserTradeHistoryItem
    ) -> None:
        """net_pnl = realized_pnl_amount + realized_funding_amount - fee_amount.

        Gives the all-in profit or loss for a single trade event.
        $1,000 + $5.0 - $24.0 = $981.0.
        """
        assert user_trade_history_item.net_pnl == pytest.approx(981.0)

    def test_user_trade_history_net_pnl_loss(self) -> None:
        """net_pnl for a losing trade is negative."""
        trade = UserTradeHistoryItem(
            account=PRIMARY_ADDR,
            market=BTC_MARKET_ADDR,
            action=TradeAction.CLOSE_LONG,
            size=0.5,
            price=93_000.0,
            is_profit=False,
            realized_pnl_amount=-500.0,
            is_funding_positive=False,
            realized_funding_amount=-2.0,
            is_rebate=False,
            fee_amount=23.25,
            transaction_unix_ms=NOW_MS,
            transaction_version=1_000_011,
        )
        assert trade.net_pnl == pytest.approx(-525.25)

    def test_user_trade_history_notional(
        self, user_trade_history_item: UserTradeHistoryItem
    ) -> None:
        """notional = size * price.

        0.5 * $96,000 = $48,000.
        """
        assert user_trade_history_item.notional == pytest.approx(48_000.0)

    def test_user_trade_history_action_enum(
        self, user_trade_history_item: UserTradeHistoryItem
    ) -> None:
        """action field is a TradeAction enum (not a raw string).

        Typed enums prevent string-typo bugs in strategy logic.
        """
        assert isinstance(user_trade_history_item.action, TradeAction)
        assert user_trade_history_item.action == TradeAction.CLOSE_LONG

    def test_user_trade_history_rebate(self) -> None:
        """When is_rebate is True, fee_amount represents a maker rebate.

        Rebates reduce effective cost — net_pnl should add the fee.
        pnl=200, funding=0, fee=5 (rebate) → net_pnl = 200 + 0 + 5 = 205.
        """
        trade = UserTradeHistoryItem(
            account=PRIMARY_ADDR,
            market=BTC_MARKET_ADDR,
            action=TradeAction.CLOSE_SHORT,
            size=1.0,
            price=95_000.0,
            is_profit=True,
            realized_pnl_amount=200.0,
            is_funding_positive=True,
            realized_funding_amount=0.0,
            is_rebate=True,
            fee_amount=5.0,
            transaction_unix_ms=NOW_MS,
            transaction_version=1_000_012,
        )
        assert trade.net_pnl == pytest.approx(205.0)


# ===================================================================
# UserFundingHistoryItem
# ===================================================================


class TestUserFundingHistoryItem:
    """Contract tests for the funding payment model."""

    def test_user_funding_history_roundtrip(
        self, user_funding_history_item: UserFundingHistoryItem
    ) -> None:
        """Serialise → deserialise preserves all fields."""
        data = user_funding_history_item.model_dump()
        restored = UserFundingHistoryItem(**data)
        assert restored == user_funding_history_item

    def test_user_funding_history_json_roundtrip(
        self, user_funding_history_item: UserFundingHistoryItem
    ) -> None:
        """JSON roundtrip."""
        json_str = user_funding_history_item.model_dump_json()
        restored = UserFundingHistoryItem.model_validate_json(json_str)
        assert restored == user_funding_history_item

    def test_user_funding_history_fields(
        self, user_funding_history_item: UserFundingHistoryItem
    ) -> None:
        """Spot-check key fields match fixture data."""
        assert user_funding_history_item.funding_rate_bps == pytest.approx(0.75)
        assert user_funding_history_item.is_funding_positive is True
        assert user_funding_history_item.funding_amount == pytest.approx(12.50)
        assert user_funding_history_item.position_size == pytest.approx(0.5)


# ===================================================================
# UserFundHistoryItem
# ===================================================================


class TestUserFundHistoryItem:
    """Contract tests for deposit/withdrawal history items."""

    def test_user_fund_history_deposit_roundtrip(
        self, user_fund_history_deposit: UserFundHistoryItem
    ) -> None:
        """Serialise → deserialise preserves deposit event."""
        data = user_fund_history_deposit.model_dump()
        restored = UserFundHistoryItem(**data)
        assert restored == user_fund_history_deposit

    def test_user_fund_history_withdrawal_roundtrip(
        self, user_fund_history_withdrawal: UserFundHistoryItem
    ) -> None:
        """Serialise → deserialise preserves withdrawal event."""
        data = user_fund_history_withdrawal.model_dump()
        restored = UserFundHistoryItem(**data)
        assert restored == user_fund_history_withdrawal

    def test_user_fund_history_json_roundtrip(
        self, user_fund_history_deposit: UserFundHistoryItem
    ) -> None:
        """JSON roundtrip."""
        json_str = user_fund_history_deposit.model_dump_json()
        restored = UserFundHistoryItem.model_validate_json(json_str)
        assert restored == user_fund_history_deposit

    def test_user_fund_history_deposit_flag(
        self, user_fund_history_deposit: UserFundHistoryItem
    ) -> None:
        """is_deposit is True for deposits."""
        assert user_fund_history_deposit.is_deposit is True

    def test_user_fund_history_withdrawal_flag(
        self, user_fund_history_withdrawal: UserFundHistoryItem
    ) -> None:
        """is_deposit is False for withdrawals."""
        assert user_fund_history_withdrawal.is_deposit is False
