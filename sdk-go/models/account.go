package models

// AccountOverview contains comprehensive account information.
type AccountOverview struct {
	PerpEquityBalance              float64  `json:"perp_equity_balance"`
	UnrealizedPnl                  float64  `json:"unrealized_pnl"`
	UnrealizedFundingCost          float64  `json:"unrealized_funding_cost"`
	CrossMarginRatio               float64  `json:"cross_margin_ratio"`
	MaintenanceMargin              float64  `json:"maintenance_margin"`
	CrossAccountLeverageRatio      *float64 `json:"cross_account_leverage_ratio"`
	Volume                         *float64 `json:"volume"`
	NetDeposits                    *float64 `json:"net_deposits"`
	AllTimeReturn                  *float64 `json:"all_time_return"`
	Pnl90d                         *float64 `json:"pnl_90d"`
	SharpeRatio                    *float64 `json:"sharpe_ratio"`
	MaxDrawdown                    *float64 `json:"max_drawdown"`
	WeeklyWinRate12w               *float64 `json:"weekly_win_rate_12w"`
	AverageCashPosition            *float64 `json:"average_cash_position"`
	AverageLeverage                *float64 `json:"average_leverage"`
	CrossAccountPosition           float64  `json:"cross_account_position"`
	TotalMargin                    float64  `json:"total_margin"`
	UsdcCrossWithdrawableBalance   float64  `json:"usdc_cross_withdrawable_balance"`
	UsdcIsolatedWithdrawableBalance float64 `json:"usdc_isolated_withdrawable_balance"`
	RealizedPnl                    *float64 `json:"realized_pnl"`
	LiquidationFeesPaid            *float64 `json:"liquidation_fees_paid"`
	LiquidationLosses              *float64 `json:"liquidation_losses"`
}

// UserSubaccount represents a user's subaccount.
type UserSubaccount struct {
	SubaccountAddress     string  `json:"subaccount_address"`
	PrimaryAccountAddress string  `json:"primary_account_address"`
	IsPrimary             bool    `json:"is_primary"`
	CustomLabel           *string `json:"custom_label"`
	IsActive              *bool   `json:"is_active,omitempty"`
}

// Delegation represents a trading delegation.
type Delegation struct {
	DelegatedAccount string `json:"delegated_account"`
	PermissionType   string `json:"permission_type"`
	ExpirationTimeS  *int64 `json:"expiration_time_s"`
}

// UserFundHistoryItem represents a deposit/withdrawal.
type UserFundHistoryItem struct {
	Amount             float64 `json:"amount"`
	IsDeposit          bool    `json:"is_deposit"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}

// UserFundingHistoryItem represents a funding payment.
type UserFundingHistoryItem struct {
	Market             string  `json:"market"`
	FundingRateBps     float64 `json:"funding_rate_bps"`
	IsFundingPositive  bool    `json:"is_funding_positive"`
	FundingAmount      float64 `json:"funding_amount"`
	PositionSize       float64 `json:"position_size"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}

// LeaderboardItem represents a single leaderboard entry.
type LeaderboardItem struct {
	Rank         int64   `json:"rank"`
	Account      string  `json:"account"`
	AccountValue float64 `json:"account_value"`
	RealizedPnl  float64 `json:"realized_pnl"`
	ROI          float64 `json:"roi"`
	Volume       float64 `json:"volume"`
}

// Leaderboard represents the full leaderboard response.
type Leaderboard struct {
	Items      []LeaderboardItem `json:"items"`
	TotalCount int64             `json:"total_count"`
}

// UserTradeHistoryItem represents a trade in user history.
type UserTradeHistoryItem struct {
	Account               string  `json:"account"`
	Market                string  `json:"market"`
	Action                string  `json:"action"`
	Size                  float64 `json:"size"`
	Price                 float64 `json:"price"`
	IsProfit              bool    `json:"is_profit"`
	RealizedPnlAmount     float64 `json:"realized_pnl_amount"`
	IsFundingPositive     bool    `json:"is_funding_positive"`
	RealizedFundingAmount float64 `json:"realized_funding_amount"`
	IsRebate              bool    `json:"is_rebate"`
	FeeAmount             float64 `json:"fee_amount"`
	TransactionUnixMs     int64   `json:"transaction_unix_ms"`
	TransactionVersion    int64   `json:"transaction_version"`
}

// LeaderboardEntry represents a single entry in the leaderboard.
type LeaderboardEntry struct {
	Rank         int64   `json:"rank"`
	Account      string  `json:"account"`
	AccountValue float64 `json:"account_value"`
	RealizedPnl  float64 `json:"realized_pnl"`
	ROI          float64 `json:"roi"`
	Volume       float64 `json:"volume"`
}

// VaultPerformance represents performance metrics for a vault.
type VaultPerformance struct {
	VaultAddress        string  `json:"vault_address"`
	VaultName           string  `json:"vault_name"`
	UserDeposits        float64 `json:"user_deposits"`
	UserShares          float64 `json:"user_shares"`
	UserPnl             float64 `json:"user_pnl"`
	UserReturnValue     float64 `json:"user_return_value"`
}

// UserTwapHistoryItem represents a TWAP order in history.
type UserTwapHistoryItem struct {
	Market             string  `json:"market"`
	IsBuy              bool    `json:"is_buy"`
	OrderID            string  `json:"order_id"`
	ClientOrderID      string  `json:"client_order_id"`
	IsReduceOnly       bool    `json:"is_reduce_only"`
	StartUnixMs        int64   `json:"start_unix_ms"`
	FrequencyS         int64   `json:"frequency_s"`
	DurationS          int64   `json:"duration_s"`
	OrigSize           float64 `json:"orig_size"`
	ExecutedSize       float64 `json:"executed_size"`
	Status             string  `json:"status"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}
