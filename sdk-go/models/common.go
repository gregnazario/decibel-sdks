package models

// TimeInForce represents order time-in-force types.
type TimeInForce uint8

const (
	GoodTillCanceled   TimeInForce = 0
	PostOnly           TimeInForce = 1
	ImmediateOrCancel  TimeInForce = 2
)

// CandlestickInterval represents OHLC candlestick intervals.
type CandlestickInterval string

const (
	IntervalOneMinute      CandlestickInterval = "1m"
	IntervalFiveMinutes    CandlestickInterval = "5m"
	IntervalFifteenMinutes CandlestickInterval = "15m"
	IntervalThirtyMinutes  CandlestickInterval = "30m"
	IntervalOneHour        CandlestickInterval = "1h"
	IntervalTwoHours       CandlestickInterval = "2h"
	IntervalFourHours      CandlestickInterval = "4h"
	IntervalEightHours     CandlestickInterval = "8h"
	IntervalTwelveHours    CandlestickInterval = "12h"
	IntervalOneDay         CandlestickInterval = "1d"
	IntervalThreeDays      CandlestickInterval = "3d"
	IntervalOneWeek        CandlestickInterval = "1w"
	IntervalOneMonth       CandlestickInterval = "1mo"
)

// VolumeWindow represents time windows for volume calculation.
type VolumeWindow string

const (
	VolumeWindow7D  VolumeWindow = "7d"
	VolumeWindow14D VolumeWindow = "14d"
	VolumeWindow30D VolumeWindow = "30d"
	VolumeWindow90D VolumeWindow = "90d"
)

// OrderStatusType represents the status of an order.
type OrderStatusType string

const (
	OrderStatusAcknowledged OrderStatusType = "Acknowledged"
	OrderStatusFilled       OrderStatusType = "Filled"
	OrderStatusCancelled    OrderStatusType = "Cancelled"
	OrderStatusRejected     OrderStatusType = "Rejected"
	OrderStatusUnknown      OrderStatusType = "Unknown"
)

// ParseOrderStatusType converts a string to an OrderStatusType.
func ParseOrderStatusType(s string) OrderStatusType {
	switch s {
	case "Acknowledged":
		return OrderStatusAcknowledged
	case "Filled":
		return OrderStatusFilled
	case "Cancelled", "Canceled":
		return OrderStatusCancelled
	case "Rejected":
		return OrderStatusRejected
	default:
		return OrderStatusUnknown
	}
}

// IsSuccess returns true if the order status indicates success.
func (s OrderStatusType) IsSuccess() bool {
	return s == OrderStatusAcknowledged || s == OrderStatusFilled
}

// IsFailure returns true if the order status indicates failure.
func (s OrderStatusType) IsFailure() bool {
	return s == OrderStatusCancelled || s == OrderStatusRejected
}

// IsFinal returns true if the order status is terminal.
func (s OrderStatusType) IsFinal() bool {
	return s.IsSuccess() || s.IsFailure()
}

// SortDirection for pagination.
type SortDirection string

const (
	SortAscending  SortDirection = "ASC"
	SortDescending SortDirection = "DESC"
)

// TwapStatus for TWAP orders.
type TwapStatus string

const (
	TwapActivated TwapStatus = "Activated"
	TwapFinished  TwapStatus = "Finished"
	TwapCancelled TwapStatus = "Cancelled"
)

// TradeAction types.
type TradeAction string

const (
	TradeOpenLong  TradeAction = "OpenLong"
	TradeCloseLong TradeAction = "CloseLong"
	TradeOpenShort TradeAction = "OpenShort"
	TradeCloseShort TradeAction = "CloseShort"
	TradeNet       TradeAction = "Net"
)

// VaultType represents the type of vault.
type VaultType string

const (
	VaultTypeUser     VaultType = "user"
	VaultTypeProtocol VaultType = "protocol"
)

// MarketDepthAggregationSize defines valid aggregation sizes.
type MarketDepthAggregationSize int

const (
	AggSize1    MarketDepthAggregationSize = 1
	AggSize2    MarketDepthAggregationSize = 2
	AggSize5    MarketDepthAggregationSize = 5
	AggSize10   MarketDepthAggregationSize = 10
	AggSize100  MarketDepthAggregationSize = 100
	AggSize1000 MarketDepthAggregationSize = 1000
)

// AllAggregationSizes returns all valid aggregation sizes.
func AllAggregationSizes() []MarketDepthAggregationSize {
	return []MarketDepthAggregationSize{AggSize1, AggSize2, AggSize5, AggSize10, AggSize100, AggSize1000}
}

// PageParams for pagination.
type PageParams struct {
	Limit  *int `json:"limit,omitempty"`
	Offset *int `json:"offset,omitempty"`
}

// PaginatedResponse is a generic paginated response.
type PaginatedResponse[T any] struct {
	Items      []T   `json:"items"`
	TotalCount int64 `json:"total_count"`
}

// SortParams for sorting.
type SortParams struct {
	SortKey *string        `json:"sort_key,omitempty"`
	SortDir *SortDirection `json:"sort_dir,omitempty"`
}

// SearchTermParams for searching.
type SearchTermParams struct {
	SearchTerm *string `json:"search_term,omitempty"`
}

// PlaceOrderResult contains the result of placing an order.
type PlaceOrderResult struct {
	Success         bool    `json:"success"`
	OrderID         *string `json:"order_id,omitempty"`
	TransactionHash *string `json:"transaction_hash,omitempty"`
	Error           *string `json:"error,omitempty"`
}

// TwapOrderResult contains the result of placing a TWAP order.
type TwapOrderResult struct {
	Success         bool    `json:"success"`
	OrderID         *string `json:"order_id,omitempty"`
	TransactionHash string  `json:"transaction_hash"`
}
