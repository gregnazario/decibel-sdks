package decibel

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMainnetConfig_AllFieldsPopulated(t *testing.T) {
	config := MainnetConfig()
	assert.Equal(t, NetworkMainnet, config.Network)
	assert.NotEmpty(t, config.FullnodeURL)
	assert.NotEmpty(t, config.TradingHTTPURL)
	assert.NotEmpty(t, config.TradingWsURL)
	assert.NotEmpty(t, config.Deployment.Package)
	assert.Equal(t, CompatVersionV04, config.CompatVersion)
	assert.Equal(t, uint8(1), *config.ChainID)
}

func TestTestnetConfig_NetworkIsTestnet(t *testing.T) {
	config := TestnetConfig()
	assert.Equal(t, NetworkTestnet, config.Network)
	assert.Equal(t, uint8(2), *config.ChainID)
}

func TestLocalConfig_UsesLocalhost(t *testing.T) {
	config := LocalConfig()
	assert.Equal(t, NetworkLocal, config.Network)
	assert.Contains(t, config.FullnodeURL, "localhost")
	assert.Contains(t, config.TradingHTTPURL, "localhost")
	assert.Contains(t, config.TradingWsURL, "localhost")
}

func TestValidConfig_ValidateSucceeds(t *testing.T) {
	config := MainnetConfig()
	err := config.Validate()
	assert.NoError(t, err)
}

func TestEmptyFullnodeURL_ValidateFails(t *testing.T) {
	config := MainnetConfig()
	config.FullnodeURL = ""
	err := config.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "fullnode_url")
}

func TestEmptyTradingHTTPURL_ValidateFails(t *testing.T) {
	config := MainnetConfig()
	config.TradingHTTPURL = ""
	assert.Error(t, config.Validate())
}

func TestEmptyTradingWsURL_ValidateFails(t *testing.T) {
	config := MainnetConfig()
	config.TradingWsURL = ""
	assert.Error(t, config.Validate())
}

func TestEmptyPackage_ValidateFails(t *testing.T) {
	config := MainnetConfig()
	config.Deployment.Package = ""
	assert.Error(t, config.Validate())
}

func TestNamedConfig_Mainnet(t *testing.T) {
	config, ok := NamedConfig("mainnet")
	assert.True(t, ok)
	assert.Equal(t, NetworkMainnet, config.Network)
}

func TestNamedConfig_Unknown(t *testing.T) {
	_, ok := NamedConfig("nonexistent")
	assert.False(t, ok)
}

func TestConfig_SerializationRoundtrip(t *testing.T) {
	config := MainnetConfig()
	data, err := json.Marshal(config)
	require.NoError(t, err)

	var deserialized DecibelConfig
	err = json.Unmarshal(data, &deserialized)
	require.NoError(t, err)

	assert.Equal(t, config.Network, deserialized.Network)
	assert.Equal(t, config.FullnodeURL, deserialized.FullnodeURL)
}
