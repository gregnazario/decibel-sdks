package models

import (
	"encoding/json"
	"testing"
)

func TestVault_JSON(t *testing.T) {
	data := `{
		"address": "0xvault",
		"name": "Alpha Vault",
		"description": "A great vault",
		"manager": "0xmanager",
		"status": "Active",
		"created_at": 1700000000000,
		"tvl": 500000.0,
		"volume": 1000000.0,
		"volume_30d": null,
		"all_time_pnl": 50000.0,
		"net_deposits": 400000.0,
		"all_time_return": 0.125,
		"past_month_return": 0.03,
		"sharpe_ratio": 2.1,
		"max_drawdown": -0.05,
		"weekly_win_rate_12w": 0.75,
		"profit_share": 0.2,
		"pnl_90d": 30000.0,
		"manager_cash_pct": 0.1,
		"average_leverage": 2.0,
		"depositors": 42,
		"perp_equity": 450000.0,
		"vault_type": "user",
		"social_links": ["https://twitter.com/vault"]
	}`
	var vault Vault
	if err := json.Unmarshal([]byte(data), &vault); err != nil {
		t.Fatal(err)
	}
	if vault.Name != "Alpha Vault" {
		t.Errorf("expected Alpha Vault, got %s", vault.Name)
	}
	if vault.VaultType == nil || *vault.VaultType != "user" {
		t.Error("expected vault_type=user")
	}
	if vault.Depositors == nil || *vault.Depositors != 42 {
		t.Error("expected depositors=42")
	}
	if vault.Volume30d != nil {
		t.Error("expected nil volume_30d")
	}
}

func TestVaultsResponse_JSON(t *testing.T) {
	data := `{
		"items": [],
		"total_count": 0,
		"total_value_locked": 1000000.0,
		"total_volume": 5000000.0
	}`
	var resp VaultsResponse
	if err := json.Unmarshal([]byte(data), &resp); err != nil {
		t.Fatal(err)
	}
	if resp.TotalValueLocked != 1000000.0 {
		t.Errorf("expected 1000000, got %f", resp.TotalValueLocked)
	}
	if resp.TotalVolume != 5000000.0 {
		t.Errorf("expected 5000000, got %f", resp.TotalVolume)
	}
}

func TestUserOwnedVault_JSON(t *testing.T) {
	data := `{
		"vault_address": "0xvault",
		"vault_name": "My Vault",
		"vault_share_symbol": "MYVLT",
		"status": "Active",
		"age_days": 30,
		"num_managers": 2,
		"tvl": 100000.0,
		"apr": 0.15,
		"manager_equity": 50000.0,
		"manager_stake": 0.5
	}`
	var vault UserOwnedVault
	if err := json.Unmarshal([]byte(data), &vault); err != nil {
		t.Fatal(err)
	}
	if vault.VaultName != "My Vault" {
		t.Errorf("expected My Vault, got %s", vault.VaultName)
	}
	if vault.AgeDays != 30 {
		t.Errorf("expected 30, got %d", vault.AgeDays)
	}
}
