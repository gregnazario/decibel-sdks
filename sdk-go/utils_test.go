package decibel

import (
	"testing"

	"github.com/gregnazario/decibel-sdks/sdk-go/utils"
	"github.com/stretchr/testify/assert"
)

func TestGetMarketAddr_ReturnsHexString(t *testing.T) {
	addr := utils.GetMarketAddr("BTC-USD", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
	assert.True(t, len(addr) > 0)
	assert.Equal(t, "0x", addr[:2])
	assert.Equal(t, 66, len(addr))
}

func TestGetMarketAddr_Deterministic(t *testing.T) {
	global := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	addr1 := utils.GetMarketAddr("BTC-USD", global)
	addr2 := utils.GetMarketAddr("BTC-USD", global)
	assert.Equal(t, addr1, addr2)
}

func TestGetMarketAddr_DifferentMarkets(t *testing.T) {
	global := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	btcAddr := utils.GetMarketAddr("BTC-USD", global)
	ethAddr := utils.GetMarketAddr("ETH-USD", global)
	assert.NotEqual(t, btcAddr, ethAddr)
}

func TestGetPrimarySubaccountAddr_ReturnsHexString(t *testing.T) {
	addr := utils.GetPrimarySubaccountAddr(
		"0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
		"v0.4",
		"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
	)
	assert.True(t, len(addr) > 0)
	assert.Equal(t, "0x", addr[:2])
}

func TestGetPrimarySubaccountAddr_Deterministic(t *testing.T) {
	account := "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
	pkg := "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
	addr1 := utils.GetPrimarySubaccountAddr(account, "v0.4", pkg)
	addr2 := utils.GetPrimarySubaccountAddr(account, "v0.4", pkg)
	assert.Equal(t, addr1, addr2)
}

func TestGetVaultShareAddress_ReturnsHexString(t *testing.T) {
	addr := utils.GetVaultShareAddress("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
	assert.Equal(t, "0x", addr[:2])
	assert.Equal(t, 66, len(addr))
}

func TestRoundToTickSize_RoundDown(t *testing.T) {
	assert.Equal(t, 45123.0, utils.RoundToTickSize(45123.45, 0.5, 2, false))
	assert.Equal(t, 100.0, utils.RoundToTickSize(100.0, 10.0, 0, false))
	assert.Equal(t, 100.0, utils.RoundToTickSize(105.0, 10.0, 0, false))
}

func TestRoundToTickSize_RoundUp(t *testing.T) {
	assert.Equal(t, 45123.5, utils.RoundToTickSize(45123.45, 0.5, 2, true))
	assert.Equal(t, 110.0, utils.RoundToTickSize(105.0, 10.0, 0, true))
}

func TestRoundToTickSize_ZeroTickSize(t *testing.T) {
	assert.Equal(t, 45123.45, utils.RoundToTickSize(45123.45, 0.0, 2, false))
}

func TestGenerateNonce_Unique(t *testing.T) {
	n1 := utils.GenerateRandomReplayProtectionNonce()
	n2 := utils.GenerateRandomReplayProtectionNonce()
	assert.NotEqual(t, n1, n2)
}

func TestExtractOrderID_Found(t *testing.T) {
	events := []map[string]interface{}{
		{
			"type": "0x1::market_types::OrderEvent",
			"data": map[string]interface{}{
				"user":     "0xsubaccount",
				"order_id": "12345",
			},
		},
	}
	id := utils.ExtractOrderIDFromEvents(events, "0xsubaccount")
	assert.NotNil(t, id)
	assert.Equal(t, "12345", *id)
}

func TestExtractOrderID_NotFound(t *testing.T) {
	events := []map[string]interface{}{
		{
			"type": "0x1::market_types::OrderEvent",
			"data": map[string]interface{}{
				"user":     "0xother",
				"order_id": "12345",
			},
		},
	}
	id := utils.ExtractOrderIDFromEvents(events, "0xsubaccount")
	assert.Nil(t, id)
}

func TestExtractOrderID_EmptyEvents(t *testing.T) {
	id := utils.ExtractOrderIDFromEvents(nil, "0xsubaccount")
	assert.Nil(t, id)
}
