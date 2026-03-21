"""TDD tests for account data models.

These tests define the API contract for AccountOverview, UserPosition, and
UserSubaccount.  Computed properties (margin_usage_pct, liquidation_buffer,
notional, PnL helpers, etc.) are specified here first; the implementation
follows.  Realistic BTC ~$95k / ETH ~$3.5k data is used throughout.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from decibel.models.account import (
    AccountOverview,
    UserPosition,
    UserSubaccount,
)


# ===================================================================
# AccountOverview
# ===================================================================


class TestAccountOverview:
    """Contract tests for the account overview model.

    The AccountOverview is the primary health-check object for risk systems;
    every computed helper must behave correctly at boundary values.
    """

    def test_account_overview_roundtrip(self, account_overview: AccountOverview) -> None:
        """Serialise → deserialise must preserve every field.

        Account snapshots are cached by risk monitors; a lossy roundtrip
        would silently mis-report margin health.
        """
        data = account_overview.model_dump()
        restored = AccountOverview(**data)
        assert restored == account_overview

    def test_account_overview_json_roundtrip(self, account_overview: AccountOverview) -> None:
        """JSON export → re-import roundtrip for REST wire format."""
        json_str = account_overview.model_dump_json()
        restored = AccountOverview.model_validate_json(json_str)
        assert restored == account_overview

    def test_account_overview_margin_usage_pct(self, account_overview: AccountOverview) -> None:
        """margin_usage_pct = total_margin / perp_equity_balance.

        Tells a bot what fraction of its equity is locked as margin.
        With $12,500 margin on $50,000 equity → 25%.
        """
        assert account_overview.margin_usage_pct == pytest.approx(0.25)

    def test_account_overview_liquidation_buffer_usd(self, account_overview: AccountOverview) -> None:
        """liquidation_buffer_usd = perp_equity_balance - maintenance_margin.

        Remaining equity cushion before forced liquidation.
        $50,000 - $2,500 = $47,500.
        """
        assert account_overview.liquidation_buffer_usd == pytest.approx(47_500.0)

    def test_account_overview_liquidation_buffer_pct(self, account_overview: AccountOverview) -> None:
        """liquidation_buffer_pct = liquidation_buffer_usd / perp_equity_balance.

        Fraction of equity remaining before liquidation.
        $47,500 / $50,000 = 0.95.
        """
        assert account_overview.liquidation_buffer_pct == pytest.approx(0.95)

    def test_account_overview_is_liquidation_warning_false(self, account_overview: AccountOverview) -> None:
        """is_liquidation_warning is False when buffer > 10%.

        Bots use this flag to trigger emergency de-risking.
        """
        assert account_overview.is_liquidation_warning is False

    def test_account_overview_is_liquidation_warning_true(self) -> None:
        """is_liquidation_warning is True when buffer <= 10%.

        Simulates an account near liquidation.
        """
        overview = AccountOverview(
            perp_equity_balance=1_000.0,
            unrealized_pnl=-800.0,
            unrealized_funding_cost=0.0,
            cross_margin_ratio=0.95,
            maintenance_margin=950.0,
            cross_account_position=10_000.0,
            total_margin=950.0,
            usdc_cross_withdrawable_balance=50.0,
            usdc_isolated_withdrawable_balance=0.0,
        )
        assert overview.is_liquidation_warning is True

    def test_account_overview_total_withdrawable(self, account_overview: AccountOverview) -> None:
        """total_withdrawable = cross_withdrawable + isolated_withdrawable.

        Single number for display to end users.
        """
        expected = 37_500.0 + 0.0
        assert account_overview.total_withdrawable == pytest.approx(expected)

    # -- edge cases --

    def test_account_overview_zero_equity_margin_usage(self, zero_equity_account: AccountOverview) -> None:
        """margin_usage_pct must not raise on zero equity.

        Division by zero must return 0.0 (or inf-safe equivalent).
        """
        assert zero_equity_account.margin_usage_pct == pytest.approx(0.0)

    def test_account_overview_zero_equity_liquidation_buffer_usd(self, zero_equity_account: AccountOverview) -> None:
        """liquidation_buffer_usd on zero equity returns 0.0."""
        assert zero_equity_account.liquidation_buffer_usd == pytest.approx(0.0)

    def test_account_overview_zero_equity_liquidation_buffer_pct(self, zero_equity_account: AccountOverview) -> None:
        """liquidation_buffer_pct on zero equity returns 0.0."""
        assert zero_equity_account.liquidation_buffer_pct == pytest.approx(0.0)

    def test_account_overview_zero_maintenance_margin(self) -> None:
        """Account with zero maintenance_margin: buffer equals full equity."""
        overview = AccountOverview(
            perp_equity_balance=10_000.0,
            unrealized_pnl=0.0,
            unrealized_funding_cost=0.0,
            cross_margin_ratio=0.0,
            maintenance_margin=0.0,
            cross_account_position=0.0,
            total_margin=0.0,
            usdc_cross_withdrawable_balance=10_000.0,
            usdc_isolated_withdrawable_balance=0.0,
        )
        assert overview.liquidation_buffer_usd == pytest.approx(10_000.0)
        assert overview.liquidation_buffer_pct == pytest.approx(1.0)


# ===================================================================
# UserPosition
# ===================================================================


class TestUserPosition:
    """Contract tests for the user position model.

    Positions are the core primitive for PnL accounting; every direction /
    notional / protection helper must agree with exchange semantics.
    """

    def test_user_position_roundtrip(self, btc_long_position: UserPosition) -> None:
        """Serialise → deserialise must preserve every field."""
        data = btc_long_position.model_dump()
        restored = UserPosition(**data)
        assert restored == btc_long_position

    def test_user_position_json_roundtrip(self, btc_long_position: UserPosition) -> None:
        """JSON wire-format roundtrip."""
        json_str = btc_long_position.model_dump_json()
        restored = UserPosition.model_validate_json(json_str)
        assert restored == btc_long_position

    # -- direction helpers --

    def test_user_position_is_long(self, btc_long_position: UserPosition) -> None:
        """is_long returns True when size > 0."""
        assert btc_long_position.is_long is True

    def test_user_position_is_short(self, eth_short_position: UserPosition) -> None:
        """is_short returns True when size < 0."""
        assert eth_short_position.is_short is True

    def test_user_position_is_flat(self, flat_position: UserPosition) -> None:
        """is_flat returns True when size == 0."""
        assert flat_position.is_flat is True

    def test_user_position_direction_long(self, btc_long_position: UserPosition) -> None:
        """direction returns 'long' for positive size."""
        assert btc_long_position.direction == "long"

    def test_user_position_direction_short(self, eth_short_position: UserPosition) -> None:
        """direction returns 'short' for negative size."""
        assert eth_short_position.direction == "short"

    def test_user_position_direction_flat(self, flat_position: UserPosition) -> None:
        """direction returns 'flat' for zero size."""
        assert flat_position.direction == "flat"

    # -- notional --

    def test_user_position_notional_long(self, btc_long_position: UserPosition) -> None:
        """notional = abs(size) * entry_price.

        0.5 BTC * $94,000 = $47,000.
        """
        assert btc_long_position.notional == pytest.approx(47_000.0)

    def test_user_position_notional_short(self, eth_short_position: UserPosition) -> None:
        """notional uses abs(size) so it's always positive.

        5.0 ETH * $3,600 = $18,000.
        """
        assert eth_short_position.notional == pytest.approx(18_000.0)

    # -- unrealized PnL --

    def test_user_position_unrealized_pnl_long(self, btc_long_position: UserPosition) -> None:
        """unrealized_pnl(mark_px) for a long = (mark - entry) * size.

        With mark=$95,000, entry=$94,000, size=0.5 → $500.
        """
        pnl = btc_long_position.unrealized_pnl(mark_px=95_000.0)
        assert pnl == pytest.approx(500.0)

    def test_user_position_unrealized_pnl_short(self, eth_short_position: UserPosition) -> None:
        """unrealized_pnl(mark_px) for a short = (entry - mark) * abs(size).

        With mark=$3,500, entry=$3,600, size=-5.0 → (3600-3500)*5 = $500.
        """
        pnl = eth_short_position.unrealized_pnl(mark_px=3_500.0)
        assert pnl == pytest.approx(500.0)

    def test_user_position_unrealized_pnl_pct(self, btc_long_position: UserPosition) -> None:
        """unrealized_pnl_pct(mark_px) = unrealized_pnl / notional.

        $500 / $47,000 ≈ 1.064%.
        """
        pct = btc_long_position.unrealized_pnl_pct(mark_px=95_000.0)
        assert pct == pytest.approx(500.0 / 47_000.0, rel=1e-4)

    def test_user_position_total_unrealized_pnl(self, btc_long_position: UserPosition) -> None:
        """total_unrealized_pnl(mark_px) = unrealized_pnl + unrealized_funding.

        Includes funding drag for a complete picture.
        $500 + (-$3.2) = $496.8.
        """
        total = btc_long_position.total_unrealized_pnl(mark_px=95_000.0)
        assert total == pytest.approx(496.8)

    # -- liquidation distance --

    def test_user_position_liquidation_distance_pct_long(self, btc_long_position: UserPosition) -> None:
        """liquidation_distance_pct(mark_px) for a long.

        Distance from current mark to estimated liquidation price as a
        fraction of mark.  ($95,000 - $85,000) / $95,000 ≈ 10.53%.
        """
        dist = btc_long_position.liquidation_distance_pct(mark_px=95_000.0)
        assert dist == pytest.approx((95_000.0 - 85_000.0) / 95_000.0, rel=1e-4)

    def test_user_position_liquidation_distance_pct_short(self, eth_short_position: UserPosition) -> None:
        """liquidation_distance_pct(mark_px) for a short.

        ($4,200 - $3,500) / $3,500 ≈ 20%.
        """
        dist = eth_short_position.liquidation_distance_pct(mark_px=3_500.0)
        assert dist == pytest.approx((4_200.0 - 3_500.0) / 3_500.0, rel=1e-4)

    # -- TP / SL protection helpers --

    def test_user_position_has_tp(self, btc_long_position: UserPosition) -> None:
        """has_tp returns True when tp_order_id is set."""
        assert btc_long_position.has_tp is True

    def test_user_position_has_tp_false(self, eth_short_position: UserPosition) -> None:
        """has_tp returns False when tp_order_id is None."""
        assert eth_short_position.has_tp is False

    def test_user_position_has_sl(self, btc_long_position: UserPosition) -> None:
        """has_sl returns True when sl_order_id is set."""
        assert btc_long_position.has_sl is True

    def test_user_position_has_sl_false(self, eth_short_position: UserPosition) -> None:
        """has_sl returns False when sl_order_id is None."""
        assert eth_short_position.has_sl is False

    def test_user_position_has_protection(self, btc_long_position: UserPosition) -> None:
        """has_protection returns True when either TP or SL is set."""
        assert btc_long_position.has_protection is True

    def test_user_position_no_protection(self, eth_short_position: UserPosition) -> None:
        """has_protection returns False when neither TP nor SL is set."""
        assert eth_short_position.has_protection is False

    # -- negative size for shorts --

    def test_user_position_negative_size(self, eth_short_position: UserPosition) -> None:
        """Short positions are represented with negative size.

        The exchange convention is size < 0 for shorts.
        """
        assert eth_short_position.size < 0
        assert eth_short_position.size == pytest.approx(-5.0)


# ===================================================================
# UserSubaccount
# ===================================================================


class TestUserSubaccount:
    """Contract tests for the subaccount model."""

    def test_user_subaccount_roundtrip(self, user_subaccount: UserSubaccount) -> None:
        """Serialise → deserialise preserves all fields."""
        data = user_subaccount.model_dump()
        restored = UserSubaccount(**data)
        assert restored == user_subaccount

    def test_user_subaccount_json_roundtrip(self, user_subaccount: UserSubaccount) -> None:
        """JSON roundtrip."""
        json_str = user_subaccount.model_dump_json()
        restored = UserSubaccount.model_validate_json(json_str)
        assert restored == user_subaccount

    def test_user_subaccount_optional_fields(self) -> None:
        """Subaccount can be created with only required fields."""
        sub = UserSubaccount(
            subaccount_address="0xsub",
            primary_account_address="0xprimary",
            is_primary=False,
        )
        assert sub.custom_label is None
        assert sub.is_active is None
