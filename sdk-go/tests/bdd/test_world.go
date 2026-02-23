package bdd

import (
	"os"

	decibel "github.com/gregnazario/decibel-sdks/sdk-go"
	"github.com/gregnazario/decibel-sdks/sdk-go/models"
)

// TestWorld maintains state across BDD scenario steps.
type TestWorld struct {
	// Configuration
	Config *decibel.DecibelConfig
	APIKey string

	// Clients
	ReadClient  *decibel.DecibelReadClient
	WriteClient *decibel.DecibelWriteClient

	// Error state
	LastError error

	// Market data
	Markets        []models.PerpMarketConfig
	MarketDepth    *models.MarketDepth
	MarketPrices   []models.MarketPrice
	Candlesticks   []models.Candlestick
	MarketContexts []models.MarketContext
	MarketTrades   []models.MarketTrade

	// Account data
	AccountOverview *models.AccountOverview
	Positions       []models.UserPosition
	OpenOrders      []models.UserOpenOrder
	OrderHistory    []models.UserOrderHistoryItem
	TradeHistory    []models.UserTradeHistoryItem
	FundingHistory  []models.UserFundingHistoryItem
	FundHistory     []models.UserFundHistoryItem
	Subaccounts     []models.UserSubaccount
	Delegations     []models.Delegation

	// TWAP data
	ActiveTwaps   []models.UserActiveTwap
	TwapHistory   []models.UserTwapHistoryItem

	// Vault data
	Vaults            []models.Vault
	UserVaults        []models.Vault
	VaultPerformances []models.VaultPerformance

	// Leaderboard
	Leaderboard []models.LeaderboardEntry

	// Test data
	TestMarketName     string
	TestSubaccountAddr string
}

// NewTestWorld creates a new TestWorld instance.
func NewTestWorld() *TestWorld {
	return &TestWorld{
		APIKey: os.Getenv("DECIBEL_API_KEY"),
	}
}

// Clear resets the test world state.
func (w *TestWorld) Clear() {
	w.Config = nil
	w.ReadClient = nil
	w.WriteClient = nil
	w.LastError = nil
	w.Markets = nil
	w.MarketDepth = nil
	w.MarketPrices = nil
	w.Candlesticks = nil
	w.MarketContexts = nil
	w.MarketTrades = nil
	w.AccountOverview = nil
	w.Positions = nil
	w.OpenOrders = nil
	w.OrderHistory = nil
	w.TradeHistory = nil
	w.FundingHistory = nil
	w.FundHistory = nil
	w.Subaccounts = nil
	w.Delegations = nil
	w.ActiveTwaps = nil
	w.TwapHistory = nil
	w.Vaults = nil
	w.UserVaults = nil
	w.VaultPerformances = nil
	w.Leaderboard = nil
	w.TestMarketName = ""
	w.TestSubaccountAddr = ""
}

// HasError returns true if there was an error.
func (w *TestWorld) HasError() bool {
	return w.LastError != nil
}

// SetError sets the last error.
func (w *TestWorld) SetError(err error) {
	w.LastError = err
}

// GetReadClient returns the read client, initializing if necessary.
func (w *TestWorld) GetReadClient() (*decibel.DecibelReadClient, error) {
	if w.ReadClient == nil {
		if w.Config == nil {
			w.Config = decibel.TestnetConfig()
		}
		client, err := decibel.NewDecibelReadClient(w.Config, w.APIKey)
		if err != nil {
			w.SetError(err)
			return nil, err
		}
		w.ReadClient = client
	}
	return w.ReadClient, nil
}
