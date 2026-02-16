package models

import (
	"encoding/json"
	"testing"
)

func TestTimeInForce_Values(t *testing.T) {
	if GoodTillCanceled != 0 {
		t.Errorf("GoodTillCanceled should be 0, got %d", GoodTillCanceled)
	}
	if PostOnly != 1 {
		t.Errorf("PostOnly should be 1, got %d", PostOnly)
	}
	if ImmediateOrCancel != 2 {
		t.Errorf("ImmediateOrCancel should be 2, got %d", ImmediateOrCancel)
	}
}

func TestParseOrderStatusType(t *testing.T) {
	tests := []struct {
		input    string
		expected OrderStatusType
	}{
		{"Acknowledged", OrderStatusAcknowledged},
		{"Filled", OrderStatusFilled},
		{"Cancelled", OrderStatusCancelled},
		{"Canceled", OrderStatusCancelled},
		{"Rejected", OrderStatusRejected},
		{"garbage", OrderStatusUnknown},
		{"", OrderStatusUnknown},
	}
	for _, tc := range tests {
		got := ParseOrderStatusType(tc.input)
		if got != tc.expected {
			t.Errorf("ParseOrderStatusType(%q) = %q, want %q", tc.input, got, tc.expected)
		}
	}
}

func TestOrderStatusType_IsSuccess(t *testing.T) {
	if !OrderStatusAcknowledged.IsSuccess() {
		t.Error("Acknowledged should be success")
	}
	if !OrderStatusFilled.IsSuccess() {
		t.Error("Filled should be success")
	}
	if OrderStatusCancelled.IsSuccess() {
		t.Error("Cancelled should not be success")
	}
	if OrderStatusRejected.IsSuccess() {
		t.Error("Rejected should not be success")
	}
	if OrderStatusUnknown.IsSuccess() {
		t.Error("Unknown should not be success")
	}
}

func TestOrderStatusType_IsFailure(t *testing.T) {
	if !OrderStatusCancelled.IsFailure() {
		t.Error("Cancelled should be failure")
	}
	if !OrderStatusRejected.IsFailure() {
		t.Error("Rejected should be failure")
	}
	if OrderStatusAcknowledged.IsFailure() {
		t.Error("Acknowledged should not be failure")
	}
}

func TestOrderStatusType_IsFinal(t *testing.T) {
	if !OrderStatusFilled.IsFinal() {
		t.Error("Filled should be final")
	}
	if !OrderStatusCancelled.IsFinal() {
		t.Error("Cancelled should be final")
	}
	if OrderStatusUnknown.IsFinal() {
		t.Error("Unknown should not be final")
	}
}

func TestAllAggregationSizes(t *testing.T) {
	sizes := AllAggregationSizes()
	if len(sizes) != 6 {
		t.Errorf("expected 6 aggregation sizes, got %d", len(sizes))
	}
	expected := []MarketDepthAggregationSize{1, 2, 5, 10, 100, 1000}
	for i, s := range sizes {
		if s != expected[i] {
			t.Errorf("sizes[%d] = %d, want %d", i, s, expected[i])
		}
	}
}

func TestPlaceOrderResult_JSON(t *testing.T) {
	orderID := "123"
	txHash := "0xhash"
	result := PlaceOrderResult{
		Success:         true,
		OrderID:         &orderID,
		TransactionHash: &txHash,
	}
	data, err := json.Marshal(result)
	if err != nil {
		t.Fatal(err)
	}
	var decoded PlaceOrderResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatal(err)
	}
	if !decoded.Success {
		t.Error("expected success=true")
	}
	if *decoded.OrderID != "123" {
		t.Errorf("expected order_id=123, got %s", *decoded.OrderID)
	}
}

func TestPlaceOrderResult_FailureNilFields(t *testing.T) {
	errMsg := "Insufficient balance"
	result := PlaceOrderResult{
		Success: false,
		Error:   &errMsg,
	}
	if result.Success {
		t.Error("expected success=false")
	}
	if result.OrderID != nil {
		t.Error("expected nil order_id")
	}
	if result.TransactionHash != nil {
		t.Error("expected nil transaction_hash")
	}
	if *result.Error != "Insufficient balance" {
		t.Errorf("expected error message, got %s", *result.Error)
	}
}

func TestPaginatedResponse_JSON(t *testing.T) {
	data := `{"items":[{"rank":1,"account":"0x1","account_value":100.0,"realized_pnl":50.0,"roi":0.5,"volume":1000.0}],"total_count":42}`
	var resp PaginatedResponse[LeaderboardItem]
	if err := json.Unmarshal([]byte(data), &resp); err != nil {
		t.Fatal(err)
	}
	if len(resp.Items) != 1 {
		t.Errorf("expected 1 item, got %d", len(resp.Items))
	}
	if resp.TotalCount != 42 {
		t.Errorf("expected total_count=42, got %d", resp.TotalCount)
	}
}

func TestCandlestickInterval_String(t *testing.T) {
	if IntervalOneMinute != "1m" {
		t.Errorf("expected 1m, got %s", IntervalOneMinute)
	}
	if IntervalOneHour != "1h" {
		t.Errorf("expected 1h, got %s", IntervalOneHour)
	}
	if IntervalOneDay != "1d" {
		t.Errorf("expected 1d, got %s", IntervalOneDay)
	}
	if IntervalOneMonth != "1mo" {
		t.Errorf("expected 1mo, got %s", IntervalOneMonth)
	}
}

func TestVolumeWindow_String(t *testing.T) {
	if VolumeWindow7D != "7d" {
		t.Errorf("expected 7d, got %s", VolumeWindow7D)
	}
	if VolumeWindow30D != "30d" {
		t.Errorf("expected 30d, got %s", VolumeWindow30D)
	}
}
