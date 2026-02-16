use serde::{Deserialize, Serialize};

use super::common::VaultType;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Vault {
    pub address: String,
    pub name: String,
    pub description: Option<String>,
    pub manager: String,
    pub status: String,
    pub created_at: i64,
    pub tvl: Option<f64>,
    pub volume: Option<f64>,
    pub volume_30d: Option<f64>,
    pub all_time_pnl: Option<f64>,
    pub net_deposits: Option<f64>,
    pub all_time_return: Option<f64>,
    pub past_month_return: Option<f64>,
    pub sharpe_ratio: Option<f64>,
    pub max_drawdown: Option<f64>,
    pub weekly_win_rate_12w: Option<f64>,
    pub profit_share: Option<f64>,
    pub pnl_90d: Option<f64>,
    pub manager_cash_pct: Option<f64>,
    pub average_leverage: Option<f64>,
    pub depositors: Option<i64>,
    pub perp_equity: Option<f64>,
    pub vault_type: Option<VaultType>,
    pub social_links: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultsResponse {
    pub items: Vec<Vault>,
    pub total_count: i64,
    pub total_value_locked: f64,
    pub total_volume: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserOwnedVault {
    pub vault_address: String,
    pub vault_name: String,
    pub vault_share_symbol: String,
    pub status: String,
    pub age_days: i64,
    pub num_managers: i64,
    pub tvl: Option<f64>,
    pub apr: Option<f64>,
    pub manager_equity: Option<f64>,
    pub manager_stake: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultDeposit {
    pub amount_usdc: f64,
    pub shares_received: f64,
    pub timestamp_ms: i64,
    pub unlock_timestamp_ms: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultWithdrawal {
    pub amount_usdc: Option<f64>,
    pub shares_redeemed: f64,
    pub timestamp_ms: i64,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPerformanceOnVault {
    pub vault: Vault,
    pub account_address: String,
    pub total_deposited: Option<f64>,
    pub total_withdrawn: Option<f64>,
    pub current_num_shares: Option<f64>,
    pub current_value_of_shares: Option<f64>,
    pub share_price: Option<f64>,
    pub all_time_earned: Option<f64>,
    pub all_time_return: Option<f64>,
    pub volume: Option<f64>,
    pub weekly_win_rate_12w: Option<f64>,
    pub deposits: Option<Vec<VaultDeposit>>,
    pub withdrawals: Option<Vec<VaultWithdrawal>>,
    pub locked_amount: Option<f64>,
    pub unrealized_pnl: Option<f64>,
}

// --- Vault Operation Args ---

#[derive(Debug, Clone)]
pub struct CreateVaultArgs {
    pub vault_name: String,
    pub vault_description: String,
    pub vault_social_links: Vec<String>,
    pub vault_share_symbol: String,
    pub vault_share_icon_uri: Option<String>,
    pub vault_share_project_uri: Option<String>,
    pub fee_bps: u64,
    pub fee_interval_s: u64,
    pub contribution_lockup_duration_s: u64,
    pub initial_funding: u64,
    pub accepts_contributions: bool,
    pub delegate_to_creator: bool,
    pub contribution_asset_type: Option<String>,
    pub subaccount_addr: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ActivateVaultArgs {
    pub vault_address: String,
    pub additional_funding: Option<u64>,
}

#[derive(Debug, Clone)]
pub struct DepositToVaultArgs {
    pub vault_address: String,
    pub amount: u64,
}

#[derive(Debug, Clone)]
pub struct WithdrawFromVaultArgs {
    pub vault_address: String,
    pub shares: u64,
}
