package models

import (
	"encoding/json"
	"testing"
)

func TestUserPosition_FullJSON(t *testing.T) {
	data := `{
		"market": "0xmarket",
		"user": "0xuser",
		"size": 1.5,
		"user_leverage": 10.0,
		"entry_price": 45000.0,
		"is_isolated": false,
		"unrealized_funding": -5.0,
		"estimated_liquidation_price": 40000.0,
		"tp_order_id": "123",
		"tp_trigger_price": 50000.0,
		"tp_limit_price": 49500.0,
		"sl_order_id": "456",
		"sl_trigger_price": 42000.0,
		"sl_limit_price": 42500.0,
		"has_fixed_sized_tpsls": true
	}`
	var pos UserPosition
	if err := json.Unmarshal([]byte(data), &pos); err != nil {
		t.Fatal(err)
	}
	if pos.Size != 1.5 {
		t.Errorf("expected 1.5, got %f", pos.Size)
	}
	if pos.IsIsolated {
		t.Error("expected is_isolated=false")
	}
	if pos.TpOrderID == nil || *pos.TpOrderID != "123" {
		t.Error("expected tp_order_id=123")
	}
	if pos.SlOrderID == nil || *pos.SlOrderID != "456" {
		t.Error("expected sl_order_id=456")
	}
	if !pos.HasFixedSizedTpsls {
		t.Error("expected has_fixed_sized_tpsls=true")
	}
}

func TestUserPosition_NullTpSl(t *testing.T) {
	data := `{
		"market": "0xmarket",
		"user": "0xuser",
		"size": -2.0,
		"user_leverage": 5.0,
		"entry_price": 3000.0,
		"is_isolated": true,
		"unrealized_funding": 0.0,
		"estimated_liquidation_price": 3500.0,
		"tp_order_id": null,
		"tp_trigger_price": null,
		"tp_limit_price": null,
		"sl_order_id": null,
		"sl_trigger_price": null,
		"sl_limit_price": null,
		"has_fixed_sized_tpsls": false
	}`
	var pos UserPosition
	if err := json.Unmarshal([]byte(data), &pos); err != nil {
		t.Fatal(err)
	}
	if pos.Size != -2.0 {
		t.Errorf("expected -2.0 (short), got %f", pos.Size)
	}
	if !pos.IsIsolated {
		t.Error("expected is_isolated=true")
	}
	if pos.TpOrderID != nil {
		t.Error("expected nil tp_order_id")
	}
	if pos.SlOrderID != nil {
		t.Error("expected nil sl_order_id")
	}
}

func TestCrossedPosition_JSON(t *testing.T) {
	data := `{
		"positions": [
			{
				"size": 1.5,
				"sz_decimals": 8,
				"entry_px": 45000.0,
				"max_leverage": 50.0,
				"is_long": true,
				"token_type": "BTC"
			}
		]
	}`
	var crossed CrossedPosition
	if err := json.Unmarshal([]byte(data), &crossed); err != nil {
		t.Fatal(err)
	}
	if len(crossed.Positions) != 1 {
		t.Errorf("expected 1 position, got %d", len(crossed.Positions))
	}
	if !crossed.Positions[0].IsLong {
		t.Error("expected is_long=true")
	}
}
