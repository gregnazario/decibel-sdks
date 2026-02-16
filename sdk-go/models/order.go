package models

// UserOpenOrder represents an active open order.
type UserOpenOrder struct {
	Market             string  `json:"market"`
	OrderID            string  `json:"order_id"`
	ClientOrderID      *string `json:"client_order_id"`
	Price              float64 `json:"price"`
	OrigSize           float64 `json:"orig_size"`
	RemainingSize      float64 `json:"remaining_size"`
	IsBuy              bool    `json:"is_buy"`
	TimeInForce        string  `json:"time_in_force"`
	IsReduceOnly       bool    `json:"is_reduce_only"`
	Status             string  `json:"status"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}

// UserOrderHistoryItem represents an order in history.
type UserOrderHistoryItem struct {
	Market             string  `json:"market"`
	OrderID            string  `json:"order_id"`
	ClientOrderID      *string `json:"client_order_id"`
	Price              float64 `json:"price"`
	OrigSize           float64 `json:"orig_size"`
	RemainingSize      float64 `json:"remaining_size"`
	IsBuy              bool    `json:"is_buy"`
	TimeInForce        string  `json:"time_in_force"`
	IsReduceOnly       bool    `json:"is_reduce_only"`
	Status             string  `json:"status"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}

// OrderStatus represents the status of an order.
type OrderStatus struct {
	Parent             string  `json:"parent"`
	Market             string  `json:"market"`
	OrderID            string  `json:"order_id"`
	Status             string  `json:"status"`
	OrigSize           float64 `json:"orig_size"`
	RemainingSize      float64 `json:"remaining_size"`
	SizeDelta          float64 `json:"size_delta"`
	Price              float64 `json:"price"`
	IsBuy              bool    `json:"is_buy"`
	Details            string  `json:"details"`
	TransactionVersion int64   `json:"transaction_version"`
	UnixMs             int64   `json:"unix_ms"`
}

// UserActiveTwap represents an active TWAP order.
type UserActiveTwap struct {
	Market             string  `json:"market"`
	IsBuy              bool    `json:"is_buy"`
	OrderID            string  `json:"order_id"`
	ClientOrderID      string  `json:"client_order_id"`
	IsReduceOnly       bool    `json:"is_reduce_only"`
	StartUnixMs        int64   `json:"start_unix_ms"`
	FrequencyS         int64   `json:"frequency_s"`
	DurationS          int64   `json:"duration_s"`
	OrigSize           float64 `json:"orig_size"`
	RemainingSize      float64 `json:"remaining_size"`
	Status             string  `json:"status"`
	TransactionUnixMs  int64   `json:"transaction_unix_ms"`
	TransactionVersion int64   `json:"transaction_version"`
}
