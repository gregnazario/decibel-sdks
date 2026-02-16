package models

import (
	"encoding/json"
	"testing"
)

func TestAccountOverview_FullJSON(t *testing.T) {
	data := `{
		"perp_equity_balance": 10000.0,
		"unrealized_pnl": 500.0,
		"unrealized_funding_cost": -10.5,
		"cross_margin_ratio": 0.15,
		"maintenance_margin": 1000.0,
		"cross_account_leverage_ratio": 5.0,
		"volume": 250000.0,
		"net_deposits": 8000.0,
		"all_time_return": 0.25,
		"pnl_90d": 2000.0,
		"sharpe_ratio": 1.5,
		"max_drawdown": -0.1,
		"weekly_win_rate_12w": 0.6,
		"average_cash_position": 5000.0,
		"average_leverage": 3.0,
		"cross_account_position": 7000.0,
		"total_margin": 2000.0,
		"usdc_cross_withdrawable_balance": 3000.0,
		"usdc_isolated_withdrawable_balance": 1000.0,
		"realized_pnl": 1500.0,
		"liquidation_fees_paid": 50.0,
		"liquidation_losses": 200.0
	}`
	var overview AccountOverview
	if err := json.Unmarshal([]byte(data), &overview); err != nil {
		t.Fatal(err)
	}
	if overview.PerpEquityBalance != 10000.0 {
		t.Errorf("expected 10000, got %f", overview.PerpEquityBalance)
	}
	if overview.CrossAccountLeverageRatio == nil || *overview.CrossAccountLeverageRatio != 5.0 {
		t.Error("expected cross_account_leverage_ratio=5.0")
	}
	if overview.Volume == nil || *overview.Volume != 250000.0 {
		t.Error("expected volume=250000")
	}
}

func TestAccountOverview_NullOptionals(t *testing.T) {
	data := `{
		"perp_equity_balance": 0,
		"unrealized_pnl": 0,
		"unrealized_funding_cost": 0,
		"cross_margin_ratio": 0,
		"maintenance_margin": 0,
		"cross_account_leverage_ratio": null,
		"volume": null,
		"net_deposits": null,
		"all_time_return": null,
		"pnl_90d": null,
		"sharpe_ratio": null,
		"max_drawdown": null,
		"weekly_win_rate_12w": null,
		"average_cash_position": null,
		"average_leverage": null,
		"cross_account_position": 0,
		"total_margin": 0,
		"usdc_cross_withdrawable_balance": 0,
		"usdc_isolated_withdrawable_balance": 0,
		"realized_pnl": null,
		"liquidation_fees_paid": null,
		"liquidation_losses": null
	}`
	var overview AccountOverview
	if err := json.Unmarshal([]byte(data), &overview); err != nil {
		t.Fatal(err)
	}
	if overview.CrossAccountLeverageRatio != nil {
		t.Error("expected nil cross_account_leverage_ratio")
	}
	if overview.Volume != nil {
		t.Error("expected nil volume")
	}
	if overview.SharpeRatio != nil {
		t.Error("expected nil sharpe_ratio")
	}
	if overview.RealizedPnl != nil {
		t.Error("expected nil realized_pnl")
	}
}

func TestUserSubaccount_JSON(t *testing.T) {
	data := `{
		"subaccount_address": "0xsub",
		"primary_account_address": "0xowner",
		"is_primary": true,
		"custom_label": "Main Trading",
		"is_active": true
	}`
	var sub UserSubaccount
	if err := json.Unmarshal([]byte(data), &sub); err != nil {
		t.Fatal(err)
	}
	if sub.SubaccountAddress != "0xsub" {
		t.Errorf("expected 0xsub, got %s", sub.SubaccountAddress)
	}
	if !sub.IsPrimary {
		t.Error("expected is_primary=true")
	}
	if sub.CustomLabel == nil || *sub.CustomLabel != "Main Trading" {
		t.Error("expected custom_label=Main Trading")
	}
}

func TestUserSubaccount_NullLabel(t *testing.T) {
	data := `{
		"subaccount_address": "0xsub",
		"primary_account_address": "0xowner",
		"is_primary": false,
		"custom_label": null
	}`
	var sub UserSubaccount
	if err := json.Unmarshal([]byte(data), &sub); err != nil {
		t.Fatal(err)
	}
	if sub.CustomLabel != nil {
		t.Error("expected nil custom_label")
	}
}

func TestDelegation_JSON(t *testing.T) {
	data := `{
		"delegated_account": "0xdelegate",
		"permission_type": "trading",
		"expiration_time_s": 1700000000
	}`
	var delegation Delegation
	if err := json.Unmarshal([]byte(data), &delegation); err != nil {
		t.Fatal(err)
	}
	if delegation.DelegatedAccount != "0xdelegate" {
		t.Errorf("expected 0xdelegate, got %s", delegation.DelegatedAccount)
	}
	if delegation.ExpirationTimeS == nil || *delegation.ExpirationTimeS != 1700000000 {
		t.Error("expected expiration_time_s=1700000000")
	}
}

func TestDelegation_NullExpiration(t *testing.T) {
	data := `{
		"delegated_account": "0xdelegate",
		"permission_type": "trading",
		"expiration_time_s": null
	}`
	var delegation Delegation
	if err := json.Unmarshal([]byte(data), &delegation); err != nil {
		t.Fatal(err)
	}
	if delegation.ExpirationTimeS != nil {
		t.Error("expected nil expiration_time_s")
	}
}

func TestLeaderboardItem_JSON(t *testing.T) {
	data := `{
		"rank": 1,
		"account": "0x1",
		"account_value": 100000.0,
		"realized_pnl": 5000.0,
		"roi": 0.05,
		"volume": 500000.0
	}`
	var item LeaderboardItem
	if err := json.Unmarshal([]byte(data), &item); err != nil {
		t.Fatal(err)
	}
	if item.Rank != 1 {
		t.Errorf("expected rank=1, got %d", item.Rank)
	}
	if item.ROI != 0.05 {
		t.Errorf("expected roi=0.05, got %f", item.ROI)
	}
}

func TestUserTradeHistoryItem_JSON(t *testing.T) {
	data := `{
		"account": "0xaccount",
		"market": "0xmarket",
		"action": "OpenLong",
		"size": 1.5,
		"price": 45000.0,
		"is_profit": true,
		"realized_pnl_amount": 500.0,
		"is_funding_positive": true,
		"realized_funding_amount": 10.0,
		"is_rebate": false,
		"fee_amount": 5.0,
		"transaction_unix_ms": 1708000000000,
		"transaction_version": 100
	}`
	var trade UserTradeHistoryItem
	if err := json.Unmarshal([]byte(data), &trade); err != nil {
		t.Fatal(err)
	}
	if trade.Action != "OpenLong" {
		t.Errorf("expected OpenLong, got %s", trade.Action)
	}
	if !trade.IsProfit {
		t.Error("expected is_profit=true")
	}
	if trade.RealizedPnlAmount != 500.0 {
		t.Errorf("expected 500.0, got %f", trade.RealizedPnlAmount)
	}
}
