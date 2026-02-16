package models

import (
	"encoding/json"
	"testing"
)

func TestUserOpenOrder_JSON(t *testing.T) {
	data := `{
		"market": "0xmarket",
		"order_id": "12345",
		"client_order_id": "my-order-1",
		"price": 45000.0,
		"orig_size": 1.0,
		"remaining_size": 0.5,
		"is_buy": true,
		"time_in_force": "GoodTillCanceled",
		"is_reduce_only": false,
		"status": "Acknowledged",
		"transaction_unix_ms": 1708000000000,
		"transaction_version": 100
	}`
	var order UserOpenOrder
	if err := json.Unmarshal([]byte(data), &order); err != nil {
		t.Fatal(err)
	}
	if order.OrderID != "12345" {
		t.Errorf("expected 12345, got %s", order.OrderID)
	}
	if order.ClientOrderID == nil || *order.ClientOrderID != "my-order-1" {
		t.Error("expected client_order_id=my-order-1")
	}
	if !order.IsBuy {
		t.Error("expected is_buy=true")
	}
	if order.RemainingSize != 0.5 {
		t.Errorf("expected remaining_size=0.5, got %f", order.RemainingSize)
	}
	if order.Status != "Acknowledged" {
		t.Errorf("expected Acknowledged, got %s", order.Status)
	}
}

func TestUserOpenOrder_NullClientOrderID(t *testing.T) {
	data := `{
		"market": "0xmarket",
		"order_id": "12345",
		"client_order_id": null,
		"price": 45000.0,
		"orig_size": 1.0,
		"remaining_size": 1.0,
		"is_buy": false,
		"time_in_force": "PostOnly",
		"is_reduce_only": true,
		"status": "Acknowledged",
		"transaction_unix_ms": 0,
		"transaction_version": 0
	}`
	var order UserOpenOrder
	if err := json.Unmarshal([]byte(data), &order); err != nil {
		t.Fatal(err)
	}
	if order.ClientOrderID != nil {
		t.Error("expected nil client_order_id")
	}
	if order.IsBuy {
		t.Error("expected is_buy=false")
	}
	if !order.IsReduceOnly {
		t.Error("expected is_reduce_only=true")
	}
}

func TestOrderStatus_JSON(t *testing.T) {
	data := `{
		"parent": "0xparent",
		"market": "0xmarket",
		"order_id": "12345",
		"status": "Filled",
		"orig_size": 1.0,
		"remaining_size": 0.0,
		"size_delta": 1.0,
		"price": 45000.0,
		"is_buy": true,
		"details": "fully filled",
		"transaction_version": 200,
		"unix_ms": 1708000000000
	}`
	var status OrderStatus
	if err := json.Unmarshal([]byte(data), &status); err != nil {
		t.Fatal(err)
	}
	if status.Status != "Filled" {
		t.Errorf("expected Filled, got %s", status.Status)
	}
	if status.RemainingSize != 0.0 {
		t.Errorf("expected 0, got %f", status.RemainingSize)
	}
	if status.SizeDelta != 1.0 {
		t.Errorf("expected 1.0, got %f", status.SizeDelta)
	}
}

func TestUserActiveTwap_JSON(t *testing.T) {
	data := `{
		"market": "0xmarket",
		"is_buy": true,
		"order_id": "twap-1",
		"client_order_id": "my-twap",
		"is_reduce_only": false,
		"start_unix_ms": 1708000000000,
		"frequency_s": 60,
		"duration_s": 3600,
		"orig_size": 10.0,
		"remaining_size": 5.0,
		"status": "Activated",
		"transaction_unix_ms": 1708000000000,
		"transaction_version": 100
	}`
	var twap UserActiveTwap
	if err := json.Unmarshal([]byte(data), &twap); err != nil {
		t.Fatal(err)
	}
	if twap.OrderID != "twap-1" {
		t.Errorf("expected twap-1, got %s", twap.OrderID)
	}
	if twap.FrequencyS != 60 {
		t.Errorf("expected 60, got %d", twap.FrequencyS)
	}
	if twap.DurationS != 3600 {
		t.Errorf("expected 3600, got %d", twap.DurationS)
	}
	if twap.RemainingSize != 5.0 {
		t.Errorf("expected 5.0, got %f", twap.RemainingSize)
	}
}
