package decibel

import (
	"encoding/json"
	"testing"

	"github.com/gregnazario/decibel-sdks/sdk-go/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestPerpMarketConfig_Deserialization(t *testing.T) {
	data := `{
		"market_addr": "0xabc123",
		"market_name": "BTC-USD",
		"sz_decimals": 8,
		"px_decimals": 2,
		"max_leverage": 50.0,
		"min_size": 0.001,
		"lot_size": 0.001,
		"tick_size": 0.1,
		"max_open_interest": 1000000.0,
		"margin_call_fee_pct": 0.5,
		"taker_in_next_block": false
	}`

	var config models.PerpMarketConfig
	err := json.Unmarshal([]byte(data), &config)
	require.NoError(t, err)
	assert.Equal(t, "BTC-USD", config.MarketName)
	assert.Equal(t, int32(8), config.SzDecimals)
	assert.False(t, config.TakerInNextBlock)
}

func TestMarketDepth_Deserialization(t *testing.T) {
	data := `{
		"market": "BTC-USD",
		"bids": [{"price": 45100.0, "size": 2.5}],
		"asks": [{"price": 45150.0, "size": 3.0}],
		"unix_ms": 1708000000000
	}`

	var depth models.MarketDepth
	err := json.Unmarshal([]byte(data), &depth)
	require.NoError(t, err)
	assert.Equal(t, "BTC-USD", depth.Market)
	assert.Len(t, depth.Bids, 1)
	assert.Len(t, depth.Asks, 1)
	assert.Equal(t, 45100.0, depth.Bids[0].Price)
}

func TestMarketPrice_Deserialization(t *testing.T) {
	data := `{
		"market": "ETH-USD",
		"mark_px": 3000.5,
		"mid_px": 3000.0,
		"oracle_px": 3001.0,
		"funding_rate_bps": 0.0123,
		"is_funding_positive": true,
		"open_interest": 500000.0,
		"transaction_unix_ms": 1708000000000
	}`

	var price models.MarketPrice
	err := json.Unmarshal([]byte(data), &price)
	require.NoError(t, err)
	assert.Equal(t, "ETH-USD", price.Market)
	assert.True(t, price.IsFundingPositive)
}

func TestAccountOverview_WithNulls(t *testing.T) {
	data := `{
		"perp_equity_balance": 10000.0,
		"unrealized_pnl": 0.0,
		"unrealized_funding_cost": 0.0,
		"cross_margin_ratio": 0.0,
		"maintenance_margin": 0.0,
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
		"cross_account_position": 0.0,
		"total_margin": 0.0,
		"usdc_cross_withdrawable_balance": 0.0,
		"usdc_isolated_withdrawable_balance": 0.0,
		"realized_pnl": null,
		"liquidation_fees_paid": null,
		"liquidation_losses": null
	}`

	var overview models.AccountOverview
	err := json.Unmarshal([]byte(data), &overview)
	require.NoError(t, err)
	assert.Equal(t, 10000.0, overview.PerpEquityBalance)
	assert.Nil(t, overview.Volume)
	assert.Nil(t, overview.SharpeRatio)
}

func TestUserPosition_Deserialization(t *testing.T) {
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
		"sl_order_id": null,
		"sl_trigger_price": null,
		"sl_limit_price": null,
		"has_fixed_sized_tpsls": true
	}`

	var pos models.UserPosition
	err := json.Unmarshal([]byte(data), &pos)
	require.NoError(t, err)
	assert.Equal(t, 1.5, pos.Size)
	assert.NotNil(t, pos.TpOrderID)
	assert.Nil(t, pos.SlOrderID)
}

func TestOrderStatusType_Success(t *testing.T) {
	assert.True(t, models.OrderStatusAcknowledged.IsSuccess())
	assert.True(t, models.OrderStatusFilled.IsSuccess())
	assert.False(t, models.OrderStatusCancelled.IsSuccess())
}

func TestOrderStatusType_Failure(t *testing.T) {
	assert.True(t, models.OrderStatusCancelled.IsFailure())
	assert.True(t, models.OrderStatusRejected.IsFailure())
	assert.False(t, models.OrderStatusAcknowledged.IsFailure())
}

func TestOrderStatusType_Final(t *testing.T) {
	assert.True(t, models.OrderStatusFilled.IsFinal())
	assert.True(t, models.OrderStatusCancelled.IsFinal())
	assert.False(t, models.OrderStatusUnknown.IsFinal())
}

func TestParseOrderStatusType(t *testing.T) {
	assert.Equal(t, models.OrderStatusAcknowledged, models.ParseOrderStatusType("Acknowledged"))
	assert.Equal(t, models.OrderStatusCancelled, models.ParseOrderStatusType("Cancelled"))
	assert.Equal(t, models.OrderStatusCancelled, models.ParseOrderStatusType("Canceled"))
	assert.Equal(t, models.OrderStatusUnknown, models.ParseOrderStatusType("garbage"))
}

func TestTimeInForce_Values(t *testing.T) {
	assert.Equal(t, models.TimeInForce(0), models.GoodTillCanceled)
	assert.Equal(t, models.TimeInForce(1), models.PostOnly)
	assert.Equal(t, models.TimeInForce(2), models.ImmediateOrCancel)
}

func TestPlaceOrderResult_Success(t *testing.T) {
	orderID := "123"
	txHash := "0xhash"
	result := models.PlaceOrderResult{
		Success:         true,
		OrderID:         &orderID,
		TransactionHash: &txHash,
	}
	assert.True(t, result.Success)
	assert.Equal(t, "123", *result.OrderID)
}

func TestAggregationSizes(t *testing.T) {
	sizes := models.AllAggregationSizes()
	assert.Len(t, sizes, 6)
}
