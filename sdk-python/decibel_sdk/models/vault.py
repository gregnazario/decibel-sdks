"""Vault models and operation argument types."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

from decibel_sdk.models.common import VaultType


class Vault(BaseModel):
    address: str
    name: str
    description: str | None = None
    manager: str
    status: str
    created_at: int
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
    social_links: list[str] | None = None


class VaultsResponse(BaseModel):
    items: list[Vault]
    total_count: int
    total_value_locked: float
    total_volume: float


class UserOwnedVault(BaseModel):
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


class VaultDeposit(BaseModel):
    amount_usdc: float
    shares_received: float
    timestamp_ms: int
    unlock_timestamp_ms: int | None = None


class VaultWithdrawal(BaseModel):
    amount_usdc: float | None = None
    shares_redeemed: float
    timestamp_ms: int
    status: str


class UserPerformanceOnVault(BaseModel):
    vault: Vault
    account_address: str
    total_deposited: float | None = None
    total_withdrawn: float | None = None
    current_num_shares: float | None = None
    current_value_of_shares: float | None = None
    share_price: float | None = None
    all_time_earned: float | None = None
    all_time_return: float | None = None
    volume: float | None = None
    weekly_win_rate_12w: float | None = None
    deposits: list[VaultDeposit] | None = None
    withdrawals: list[VaultWithdrawal] | None = None
    locked_amount: float | None = None
    unrealized_pnl: float | None = None


# --- Vault Operation Args ---


@dataclass
class CreateVaultArgs:
    vault_name: str
    vault_description: str
    vault_social_links: list[str] = field(default_factory=list)
    vault_share_symbol: str = ""
    vault_share_icon_uri: str | None = None
    vault_share_project_uri: str | None = None
    fee_bps: int = 0
    fee_interval_s: int = 0
    contribution_lockup_duration_s: int = 0
    initial_funding: int = 0
    accepts_contributions: bool = True
    delegate_to_creator: bool = True
    contribution_asset_type: str | None = None
    subaccount_addr: str | None = None


@dataclass
class ActivateVaultArgs:
    vault_address: str
    additional_funding: int | None = None


@dataclass
class DepositToVaultArgs:
    vault_address: str
    amount: int


@dataclass
class WithdrawFromVaultArgs:
    vault_address: str
    shares: int
