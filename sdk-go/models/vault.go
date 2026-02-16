package models

// Vault represents a trading vault.
type Vault struct {
	Address          string    `json:"address"`
	Name             string    `json:"name"`
	Description      *string   `json:"description"`
	Manager          string    `json:"manager"`
	Status           string    `json:"status"`
	CreatedAt        int64     `json:"created_at"`
	TVL              *float64  `json:"tvl"`
	Volume           *float64  `json:"volume"`
	Volume30d        *float64  `json:"volume_30d"`
	AllTimePnl       *float64  `json:"all_time_pnl"`
	NetDeposits      *float64  `json:"net_deposits"`
	AllTimeReturn    *float64  `json:"all_time_return"`
	PastMonthReturn  *float64  `json:"past_month_return"`
	SharpeRatio      *float64  `json:"sharpe_ratio"`
	MaxDrawdown      *float64  `json:"max_drawdown"`
	WeeklyWinRate    *float64  `json:"weekly_win_rate_12w"`
	ProfitShare      *float64  `json:"profit_share"`
	Pnl90d           *float64  `json:"pnl_90d"`
	ManagerCashPct   *float64  `json:"manager_cash_pct"`
	AverageLeverage  *float64  `json:"average_leverage"`
	Depositors       *int64    `json:"depositors"`
	PerpEquity       *float64  `json:"perp_equity"`
	VaultType        *string   `json:"vault_type"`
	SocialLinks      []string  `json:"social_links"`
}

// VaultsResponse is the response for listing vaults.
type VaultsResponse struct {
	Items            []Vault `json:"items"`
	TotalCount       int64   `json:"total_count"`
	TotalValueLocked float64 `json:"total_value_locked"`
	TotalVolume      float64 `json:"total_volume"`
}

// UserOwnedVault represents a vault owned by a user.
type UserOwnedVault struct {
	VaultAddress     string   `json:"vault_address"`
	VaultName        string   `json:"vault_name"`
	VaultShareSymbol string   `json:"vault_share_symbol"`
	Status           string   `json:"status"`
	AgeDays          int64    `json:"age_days"`
	NumManagers      int64    `json:"num_managers"`
	TVL              *float64 `json:"tvl"`
	APR              *float64 `json:"apr"`
	ManagerEquity    *float64 `json:"manager_equity"`
	ManagerStake     *float64 `json:"manager_stake"`
}
