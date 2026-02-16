package decibel

import "errors"

// Network represents the Aptos network type.
type Network string

const (
	NetworkMainnet Network = "mainnet"
	NetworkTestnet Network = "testnet"
	NetworkDevnet  Network = "devnet"
	NetworkLocal   Network = "local"
	NetworkCustom  Network = "custom"
)

// CompatVersion represents the SDK compatibility version.
type CompatVersion string

const (
	CompatVersionV04 CompatVersion = "v0.4"
)

// Deployment contains smart contract deployment addresses.
type Deployment struct {
	Package          string `json:"package"`
	USDC             string `json:"usdc"`
	TestC            string `json:"testc"`
	PerpEngineGlobal string `json:"perp_engine_global"`
}

// DecibelConfig holds the SDK configuration.
type DecibelConfig struct {
	Network          Network       `json:"network"`
	FullnodeURL      string        `json:"fullnode_url"`
	TradingHTTPURL   string        `json:"trading_http_url"`
	TradingWsURL     string        `json:"trading_ws_url"`
	GasStationURL    string        `json:"gas_station_url,omitempty"`
	GasStationAPIKey string        `json:"gas_station_api_key,omitempty"`
	Deployment       Deployment    `json:"deployment"`
	ChainID          *uint8        `json:"chain_id,omitempty"`
	CompatVersion    CompatVersion `json:"compat_version"`
}

// Validate checks that required configuration fields are set.
func (c *DecibelConfig) Validate() error {
	if c.FullnodeURL == "" {
		return errors.New("config: fullnode_url must not be empty")
	}
	if c.TradingHTTPURL == "" {
		return errors.New("config: trading_http_url must not be empty")
	}
	if c.TradingWsURL == "" {
		return errors.New("config: trading_ws_url must not be empty")
	}
	if c.Deployment.Package == "" {
		return errors.New("config: deployment.package must not be empty")
	}
	return nil
}

// Preset configurations

func uint8Ptr(v uint8) *uint8 { return &v }

// MainnetConfig returns the production mainnet configuration.
func MainnetConfig() DecibelConfig {
	return DecibelConfig{
		Network:        NetworkMainnet,
		FullnodeURL:    "https://fullnode.mainnet.aptoslabs.com/v1",
		TradingHTTPURL: "https://api.decibel.trade",
		TradingWsURL:   "wss://api.decibel.trade/ws",
		GasStationURL:  "https://api.netna.aptoslabs.com/gs/v1",
		Deployment: Deployment{
			Package: "0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d",
			USDC:    "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b",
		},
		ChainID:       uint8Ptr(1),
		CompatVersion: CompatVersionV04,
	}
}

// TestnetConfig returns the testnet configuration.
func TestnetConfig() DecibelConfig {
	return DecibelConfig{
		Network:        NetworkTestnet,
		FullnodeURL:    "https://fullnode.testnet.aptoslabs.com/v1",
		TradingHTTPURL: "https://api.testnet.decibel.trade",
		TradingWsURL:   "wss://api.testnet.decibel.trade/ws",
		GasStationURL:  "https://api.testnet.aptoslabs.com/gs/v1",
		Deployment:     Deployment{},
		ChainID:        uint8Ptr(2),
		CompatVersion:  CompatVersionV04,
	}
}

// LocalConfig returns the local development configuration.
func LocalConfig() DecibelConfig {
	return DecibelConfig{
		Network:        NetworkLocal,
		FullnodeURL:    "http://localhost:8080/v1",
		TradingHTTPURL: "http://localhost:3000",
		TradingWsURL:   "ws://localhost:3000/ws",
		GasStationURL:  "http://localhost:8081",
		Deployment:     Deployment{},
		ChainID:        uint8Ptr(4),
		CompatVersion:  CompatVersionV04,
	}
}

// NamedConfig returns a configuration by name.
func NamedConfig(name string) (*DecibelConfig, bool) {
	switch name {
	case "mainnet":
		c := MainnetConfig()
		return &c, true
	case "testnet":
		c := TestnetConfig()
		return &c, true
	case "local":
		c := LocalConfig()
		return &c, true
	default:
		return nil, false
	}
}
