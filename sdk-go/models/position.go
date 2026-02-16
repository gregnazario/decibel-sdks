package models

// UserPosition represents a user's position in a market.
type UserPosition struct {
	Market                  string   `json:"market"`
	User                    string   `json:"user"`
	Size                    float64  `json:"size"`
	UserLeverage            float64  `json:"user_leverage"`
	EntryPrice              float64  `json:"entry_price"`
	IsIsolated              bool     `json:"is_isolated"`
	UnrealizedFunding       float64  `json:"unrealized_funding"`
	EstimatedLiquidationPx  float64  `json:"estimated_liquidation_price"`
	TpOrderID               *string  `json:"tp_order_id"`
	TpTriggerPrice          *float64 `json:"tp_trigger_price"`
	TpLimitPrice            *float64 `json:"tp_limit_price"`
	SlOrderID               *string  `json:"sl_order_id"`
	SlTriggerPrice          *float64 `json:"sl_trigger_price"`
	SlLimitPrice            *float64 `json:"sl_limit_price"`
	HasFixedSizedTpsls      bool     `json:"has_fixed_sized_tpsls"`
}

// PerpPosition represents a crossed position component.
type PerpPosition struct {
	Size        float64 `json:"size"`
	SzDecimals  int32   `json:"sz_decimals"`
	EntryPx     float64 `json:"entry_px"`
	MaxLeverage float64 `json:"max_leverage"`
	IsLong      bool    `json:"is_long"`
	TokenType   string  `json:"token_type"`
}

// CrossedPosition contains all crossed positions.
type CrossedPosition struct {
	Positions []PerpPosition `json:"positions"`
}
