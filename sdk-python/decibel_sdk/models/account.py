"""Account, subaccount, delegation, and analytics models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AccountOverview(BaseModel):
    perp_equity_balance: float
    unrealized_pnl: float
    unrealized_funding_cost: float
    cross_margin_ratio: float
    maintenance_margin: float
    cross_account_leverage_ratio: float | None = None
    volume: float | None = None
    net_deposits: float | None = None
    all_time_return: float | None = None
    pnl_90d: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    weekly_win_rate_12w: float | None = None
    average_cash_position: float | None = None
    average_leverage: float | None = None
    cross_account_position: float
    total_margin: float
    usdc_cross_withdrawable_balance: float
    usdc_isolated_withdrawable_balance: float
    realized_pnl: float | None = None
    liquidation_fees_paid: float | None = None
    liquidation_losses: float | None = None


class UserSubaccount(BaseModel):
    subaccount_address: str
    primary_account_address: str
    is_primary: bool
    custom_label: str | None = None
    is_active: bool | None = None


class Delegation(BaseModel):
    delegated_account: str
    permission_type: str
    expiration_time_s: int | None = None


class UserFundHistoryItem(BaseModel):
    amount: float
    is_deposit: bool
    transaction_unix_ms: int
    transaction_version: int


class UserFundingHistoryItem(BaseModel):
    market: str
    funding_rate_bps: float
    is_funding_positive: bool
    funding_amount: float
    position_size: float
    transaction_unix_ms: int
    transaction_version: int


class LeaderboardItem(BaseModel):
    rank: int
    account: str
    account_value: float
    realized_pnl: float
    roi: float
    volume: float


class Leaderboard(BaseModel):
    items: list[LeaderboardItem]
    total_count: int


class PortfolioChartData(BaseModel):
    timestamp: int
    value: float


class UserNotification(BaseModel):
    id: str
    notification_type: str = Field(alias="type")
    message: str
    timestamp: int
    read: bool

    model_config = {"populate_by_name": True}


class UserTradeHistoryItem(BaseModel):
    account: str
    market: str
    action: str
    size: float
    price: float
    is_profit: bool
    realized_pnl_amount: float
    is_funding_positive: bool
    realized_funding_amount: float
    is_rebate: bool
    fee_amount: float
    transaction_unix_ms: int
    transaction_version: int
