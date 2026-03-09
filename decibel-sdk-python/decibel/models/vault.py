"""Vault-related data models."""

from typing import Any

from pydantic import BaseModel, Field

from .enums import VaultType


class Vault(BaseModel):
    """Trading vault.

    Attributes:
        address: Vault address
        name: Vault name
        description: Vault description
        manager: Manager account address
        status: Vault status
        created_at: Creation timestamp
        tvl: Total value locked
        volume: Trading volume
        volume_30d: 30-day volume
        all_time_pnl: All-time PnL
        net_deposits: Net deposits
        all_time_return: All-time return
        past_month_return: Past month return
        sharpe_ratio: Sharpe ratio
        max_drawdown: Maximum drawdown
        weekly_win_rate_12w: 12-week weekly win rate
        profit_share: Profit share percentage
        pnl_90d: 90-day PnL
        manager_cash_pct: Manager cash percentage
        average_leverage: Average leverage
        depositors: Number of depositors
        perp_equity: Perp equity
        vault_type: Vault type
        social_links: Social media links
    """

    address: str
    name: str
    manager: str
    status: str
    created_at: int
    description: str | None = None
    tvl: float | None = None
    volume: float | None = None
    volume_30d: float | None = None
    all_time_pnl: float | None = None
    net_deposits: float | None = None
    all_time_return: float | None = None
    past_month_return: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    weekly_win_rate_12w: float | None = None
    profit_share: float | None = None
    pnl_90d: float | None = None
    manager_cash_pct: float | None = None
    average_leverage: float | None = None
    depositors: int | None = None
    perp_equity: float | None = None
    vault_type: VaultType | None = None
    social_links: list[str] = Field(default_factory=list)


class VaultsResponse(BaseModel):
    """Response for listing vaults.

    Attributes:
        items: List of vaults
        total_count: Total count
        total_value_locked: Total value locked across all vaults
        total_volume: Total volume across all vaults
    """

    items: list[Vault]
    total_count: int
    total_value_locked: float
    total_volume: float


class UserOwnedVault(BaseModel):
    """Vault owned by a user.

    Attributes:
        vault_address: Vault address
        vault_name: Vault name
        vault_share_symbol: Share token symbol
        status: Status
        age_days: Age in days
        num_managers: Number of managers
        tvl: Total value locked
        apr: Annual percentage rate
        manager_equity: Manager equity
        manager_stake: Manager stake
    """

    vault_address: str
    vault_name: str
    vault_share_symbol: str
    status: str
    age_days: int
    num_managers: int
    tvl: float | None = None
    apr: float | None = None
    manager_equity: float | None = None
    manager_stake: float | None = None


class UserPerformanceOnVault(BaseModel):
    """User's performance on a vault.

    Attributes:
        vault_address: Vault address
        vault_name: Vault name
        shares: Number of shares owned
        share_value: Value per share
        total_value: Total value of shares
        deposited_amount: Total deposited amount
        withdrawn_amount: Total withdrawn amount
        realized_pnl: Realized PnL
        unrealized_pnl: Unrealized PnL
        all_time_return: All-time return
    """

    vault_address: str
    vault_name: str
    shares: int
    share_value: float
    total_value: float
    deposited_amount: float
    withdrawn_amount: float
    realized_pnl: float
    unrealized_pnl: float
    all_time_return: float
