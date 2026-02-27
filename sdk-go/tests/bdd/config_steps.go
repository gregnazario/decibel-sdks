package bdd

import (
	"fmt"

	"github.com/cucumber/godog"
	decibel "github.com/gregnazario/decibel-sdks/sdk-go"
)

// ConfigSteps implements BDD steps for SDK configuration scenarios.
type ConfigSteps struct {
	testWorld *TestWorld
}

// NewConfigSteps creates a new ConfigSteps instance.
func NewConfigSteps(world *TestWorld) *ConfigSteps {
	return &ConfigSteps{testWorld: world}
}

// RegisterSteps registers all configuration steps with godog.
func (s *ConfigSteps) RegisterSteps(ctx *godog.ScenarioContext) {
	ctx.Step(`^I have an uninitialized Decibel configuration$`, s.iHaveAnUninitializedConfig)
	ctx.Step(`^I create a read client using the ([^"]*) preset configuration$`, s.iCreateReadClientWithPreset)
	ctx.Step(`^I create a read client with custom endpoints$`, s.iCreateReadClientWithCustomEndpoints)
	ctx.Step(`^the client should be configured for the ([^"]*) environment$`, s.clientShouldBeConfiguredFor)
	ctx.Step(`^the client should have a valid HTTP client$`, s.clientShouldHaveValidHTTPClient)
	ctx.Step(`^the client should use the ([^"]*) API endpoint$`, s.clientShouldUseAPIEndpoint)
	ctx.Step(`^the client should have chain ID set to (\d+)$`, s.clientShouldHaveChainID)
	ctx.Step(`^the client should have the correct deployment addresses$`, s.clientShouldHaveDeploymentAddresses)
	ctx.Step(`^I request a configuration named ([^"]*)$`, s.iRequestConfigNamed)
	ctx.Step(`^I should receive the ([^"]*) configuration$`, s.iShouldReceiveConfig)
	ctx.Step(`^the configuration should be valid$`, s.configShouldBeValid)
}

func (s *ConfigSteps) iHaveAnUninitializedConfig() error {
	s.testWorld.Config = nil
	s.testWorld.LastError = nil
	return nil
}

func (s *ConfigSteps) iCreateReadClientWithPreset(preset string) error {
	switch preset {
	case "mainnet":
		cfg := decibel.MainnetConfig()
		s.testWorld.Config = &cfg
	case "testnet":
		cfg := decibel.TestnetConfig()
		s.testWorld.Config = &cfg
	case "local":
		cfg := decibel.LocalConfig()
		s.testWorld.Config = &cfg
	default:
		return fmt.Errorf("unknown preset: %s", preset)
	}

	client, err := decibel.NewDecibelReadClient(s.testWorld.Config, s.testWorld.APIKey)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.ReadClient = client
	return nil
}

func (s *ConfigSteps) iCreateReadClientWithCustomEndpoints() error {
	customPkg := "0xcustom"
	cfg := decibel.DecibelConfig{
		Network:        decibel.NetworkCustom,
		FullnodeURL:    "https://custom.fullnode.com/v1",
		TradingHTTPURL: "https://custom.api.com",
		TradingWsURL:   "wss://custom.api.com/ws",
		Deployment: decibel.Deployment{
			Package: customPkg,
		},
		ChainID:       uint8Ptr(1),
		CompatVersion: decibel.CompatVersionV04,
	}

	if err := cfg.Validate(); err != nil {
		s.testWorld.SetError(err)
		return err
	}

	client, err := decibel.NewDecibelReadClient(&cfg, s.testWorld.APIKey)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.Config = &cfg
	s.testWorld.ReadClient = client
	return nil
}

func (s *ConfigSteps) clientShouldBeConfiguredFor(env string) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.ReadClient == nil {
		return fmt.Errorf("read client should not be nil")
	}

	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	var expectedNetwork decibel.Network
	switch env {
	case "mainnet":
		expectedNetwork = decibel.NetworkMainnet
	case "testnet":
		expectedNetwork = decibel.NetworkTestnet
	case "local":
		expectedNetwork = decibel.NetworkLocal
	default:
		return fmt.Errorf("unknown environment: %s", env)
	}

	if s.testWorld.Config.Network != expectedNetwork {
		return fmt.Errorf("expected network %s, got %s", expectedNetwork, s.testWorld.Config.Network)
	}

	return nil
}

func (s *ConfigSteps) clientShouldHaveValidHTTPClient() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.ReadClient == nil {
		return fmt.Errorf("read client should not be nil")
	}

	return nil
}

func (s *ConfigSteps) clientShouldUseAPIEndpoint(endpoint string) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	var expectedURL string
	switch endpoint {
	case "mainnet API":
		expectedURL = "https://api.decibel.trade"
	case "testnet API":
		expectedURL = "https://api.testnet.decibel.trade"
	case "local API":
		expectedURL = "http://localhost:3000"
	default:
		return fmt.Errorf("unknown endpoint: %s", endpoint)
	}

	if s.testWorld.Config.TradingHTTPURL != expectedURL {
		return fmt.Errorf("expected URL %s, got %s", expectedURL, s.testWorld.Config.TradingHTTPURL)
	}

	return nil
}

func (s *ConfigSteps) clientShouldHaveChainID(expectedChainID int) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	if s.testWorld.Config.ChainID == nil {
		return fmt.Errorf("chain ID should not be nil")
	}

	if int(*s.testWorld.Config.ChainID) != expectedChainID {
		return fmt.Errorf("expected chain ID %d, got %d", expectedChainID, *s.testWorld.Config.ChainID)
	}

	return nil
}

func (s *ConfigSteps) clientShouldHaveDeploymentAddresses() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	if s.testWorld.Config.Deployment.Package == "" {
		return fmt.Errorf("deployment package should not be empty")
	}

	return nil
}

func (s *ConfigSteps) iRequestConfigNamed(name string) error {
	config, ok := decibel.NamedConfig(name)
	if !ok {
		s.testWorld.SetError(fmt.Errorf("configuration not found: %s", name))
		return s.testWorld.LastError
	}

	s.testWorld.Config = config
	return nil
}

func (s *ConfigSteps) iShouldReceiveConfig(name string) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}

	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	var expectedNetwork decibel.Network
	switch name {
	case "mainnet":
		expectedNetwork = decibel.NetworkMainnet
	case "testnet":
		expectedNetwork = decibel.NetworkTestnet
	case "local":
		expectedNetwork = decibel.NetworkLocal
	default:
		return fmt.Errorf("unknown config name: %s", name)
	}

	if s.testWorld.Config.Network != expectedNetwork {
		return fmt.Errorf("expected network %s, got %s", expectedNetwork, s.testWorld.Config.Network)
	}

	return nil
}

func (s *ConfigSteps) configShouldBeValid() error {
	if s.testWorld.Config == nil {
		return fmt.Errorf("config should not be nil")
	}

	if err := s.testWorld.Config.Validate(); err != nil {
		return fmt.Errorf("config should be valid: %v", err)
	}

	return nil
}

// Helper function
func uint8Ptr(v uint8) *uint8 {
	return &v
}
