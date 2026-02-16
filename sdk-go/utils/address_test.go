package utils

import (
	"testing"
)

func TestGetMarketAddr_ReturnsHexString(t *testing.T) {
	addr := GetMarketAddr("BTC-USD", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
	if len(addr) != 66 {
		t.Errorf("expected length 66, got %d", len(addr))
	}
	if addr[:2] != "0x" {
		t.Errorf("expected 0x prefix, got %s", addr[:2])
	}
}

func TestGetMarketAddr_Deterministic(t *testing.T) {
	global := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	addr1 := GetMarketAddr("BTC-USD", global)
	addr2 := GetMarketAddr("BTC-USD", global)
	if addr1 != addr2 {
		t.Errorf("addresses should be equal: %s != %s", addr1, addr2)
	}
}

func TestGetMarketAddr_DifferentMarkets(t *testing.T) {
	global := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	btcAddr := GetMarketAddr("BTC-USD", global)
	ethAddr := GetMarketAddr("ETH-USD", global)
	if btcAddr == ethAddr {
		t.Error("BTC and ETH addresses should differ")
	}
}

func TestGetPrimarySubaccountAddr_ReturnsHexString(t *testing.T) {
	addr := GetPrimarySubaccountAddr(
		"0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
		"v0.4",
		"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
	)
	if len(addr) != 66 {
		t.Errorf("expected length 66, got %d", len(addr))
	}
}

func TestGetPrimarySubaccountAddr_Deterministic(t *testing.T) {
	account := "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
	pkg := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	addr1 := GetPrimarySubaccountAddr(account, "v0.4", pkg)
	addr2 := GetPrimarySubaccountAddr(account, "v0.4", pkg)
	if addr1 != addr2 {
		t.Errorf("addresses should be equal: %s != %s", addr1, addr2)
	}
}

func TestGetVaultShareAddress_ReturnsHexString(t *testing.T) {
	addr := GetVaultShareAddress("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
	if len(addr) != 66 {
		t.Errorf("expected length 66, got %d", len(addr))
	}
}

func TestRoundToTickSize_RoundDown(t *testing.T) {
	tests := []struct {
		price, tickSize, expected float64
	}{
		{45123.45, 0.5, 45123.0},
		{100.0, 10.0, 100.0},
		{105.0, 10.0, 100.0},
	}
	for _, tc := range tests {
		got := RoundToTickSize(tc.price, tc.tickSize, 2, false)
		if got != tc.expected {
			t.Errorf("RoundToTickSize(%f, %f, false) = %f, want %f", tc.price, tc.tickSize, got, tc.expected)
		}
	}
}

func TestRoundToTickSize_RoundUp(t *testing.T) {
	tests := []struct {
		price, tickSize, expected float64
	}{
		{45123.45, 0.5, 45123.5},
		{105.0, 10.0, 110.0},
	}
	for _, tc := range tests {
		got := RoundToTickSize(tc.price, tc.tickSize, 2, true)
		if got != tc.expected {
			t.Errorf("RoundToTickSize(%f, %f, true) = %f, want %f", tc.price, tc.tickSize, got, tc.expected)
		}
	}
}

func TestRoundToTickSize_ZeroTickSize(t *testing.T) {
	got := RoundToTickSize(45123.45, 0.0, 2, false)
	if got != 45123.45 {
		t.Errorf("expected unchanged price, got %f", got)
	}
}

func TestRoundToTickSize_NegativeTickSize(t *testing.T) {
	got := RoundToTickSize(45123.45, -1.0, 2, false)
	if got != 45123.45 {
		t.Errorf("expected unchanged price, got %f", got)
	}
}

func TestGenerateRandomReplayProtectionNonce_Unique(t *testing.T) {
	n1 := GenerateRandomReplayProtectionNonce()
	n2 := GenerateRandomReplayProtectionNonce()
	if n1 == n2 {
		t.Error("nonces should be unique")
	}
}

func TestExtractOrderIDFromEvents_Found(t *testing.T) {
	events := []map[string]interface{}{
		{
			"type": "0x1::market_types::OrderEvent",
			"data": map[string]interface{}{
				"user":     "0xsubaccount",
				"order_id": "12345",
			},
		},
	}
	id := ExtractOrderIDFromEvents(events, "0xsubaccount")
	if id == nil {
		t.Fatal("expected non-nil order ID")
	}
	if *id != "12345" {
		t.Errorf("expected 12345, got %s", *id)
	}
}

func TestExtractOrderIDFromEvents_WrongUser(t *testing.T) {
	events := []map[string]interface{}{
		{
			"type": "0x1::market_types::OrderEvent",
			"data": map[string]interface{}{
				"user":     "0xother",
				"order_id": "12345",
			},
		},
	}
	id := ExtractOrderIDFromEvents(events, "0xsubaccount")
	if id != nil {
		t.Error("expected nil for wrong user")
	}
}

func TestExtractOrderIDFromEvents_Empty(t *testing.T) {
	id := ExtractOrderIDFromEvents(nil, "0xsubaccount")
	if id != nil {
		t.Error("expected nil for empty events")
	}
}

func TestExtractOrderIDFromEvents_WrongEventType(t *testing.T) {
	events := []map[string]interface{}{
		{
			"type": "0x1::other::SomeEvent",
			"data": map[string]interface{}{
				"user":     "0xsubaccount",
				"order_id": "12345",
			},
		},
	}
	id := ExtractOrderIDFromEvents(events, "0xsubaccount")
	if id != nil {
		t.Error("expected nil for wrong event type")
	}
}

func TestBcsSerializeString(t *testing.T) {
	result := bcsSerializeString("BTC-USD")
	if result[0] != 7 {
		t.Errorf("expected length byte 7, got %d", result[0])
	}
	if string(result[1:]) != "BTC-USD" {
		t.Errorf("expected BTC-USD, got %s", string(result[1:]))
	}
}

func TestHexToBytes(t *testing.T) {
	bytes := hexToBytes("0xabcd")
	if len(bytes) != 2 {
		t.Errorf("expected 2 bytes, got %d", len(bytes))
	}
	if bytes[0] != 0xab || bytes[1] != 0xcd {
		t.Errorf("expected [0xab, 0xcd], got %v", bytes)
	}
}

func TestHexToBytes_WithoutPrefix(t *testing.T) {
	bytes := hexToBytes("abcd")
	if len(bytes) != 2 {
		t.Errorf("expected 2 bytes, got %d", len(bytes))
	}
}
