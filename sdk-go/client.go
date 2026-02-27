package decibel

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"time"

	"github.com/gregnazario/decibel-sdks/sdk-go/models"
)

// DecibelReadClient provides read-only access to the Decibel API.
type DecibelReadClient struct {
	config     *DecibelConfig
	httpClient *http.Client
	apiKey     string
}

// NewDecibelReadClient creates a new read-only client.
func NewDecibelReadClient(config *DecibelConfig, apiKey string) (*DecibelReadClient, error) {
	if err := config.Validate(); err != nil {
		return nil, fmt.Errorf("invalid config: %w", err)
	}

	return &DecibelReadClient{
		config: config,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		apiKey: apiKey,
	}, nil
}

// doGet performs an HTTP GET request and returns the response body.
func (c *DecibelReadClient) doGet(endpoint string) ([]byte, error) {
	url := c.config.TradingHTTPURL + endpoint

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.apiKey != "" {
		req.Header.Set("x-api-key", c.apiKey)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, &APIError{
			Status:  resp.StatusCode,
			Message: string(body),
		}
	}

	return body, nil
}

// GetAllMarkets retrieves all market configurations.
func (c *DecibelReadClient) GetAllMarkets() ([]models.PerpMarketConfig, error) {
	body, err := c.doGet("/markets")
	if err != nil {
		return nil, err
	}

	var markets []models.PerpMarketConfig
	if err := json.Unmarshal(body, &markets); err != nil {
		return nil, fmt.Errorf("failed to parse markets: %w", err)
	}

	return markets, nil
}

// GetMarketByName retrieves a specific market by name.
func (c *DecibelReadClient) GetMarketByName(name string) (*models.PerpMarketConfig, error) {
	body, err := c.doGet("/markets/" + name)
	if err != nil {
		return nil, err
	}

	var market models.PerpMarketConfig
	if err := json.Unmarshal(body, &market); err != nil {
		return nil, fmt.Errorf("failed to parse market: %w", err)
	}

	return &market, nil
}

// GetMarketDepth retrieves the order book for a market.
func (c *DecibelReadClient) GetMarketDepth(marketName string, limit *int) (*models.MarketDepth, error) {
	endpoint := "/market_depth/" + marketName
	if limit != nil {
		endpoint += "?limit=" + strconv.Itoa(*limit)
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var depth models.MarketDepth
	if err := json.Unmarshal(body, &depth); err != nil {
		return nil, fmt.Errorf("failed to parse market depth: %w", err)
	}

	return &depth, nil
}

// GetAllMarketPrices retrieves prices for all markets.
func (c *DecibelReadClient) GetAllMarketPrices() ([]models.MarketPrice, error) {
	body, err := c.doGet("/market_prices")
	if err != nil {
		return nil, err
	}

	var prices []models.MarketPrice
	if err := json.Unmarshal(body, &prices); err != nil {
		return nil, fmt.Errorf("failed to parse market prices: %w", err)
	}

	return prices, nil
}

// GetMarketPriceByName retrieves the price for a specific market.
func (c *DecibelReadClient) GetMarketPriceByName(name string) ([]models.MarketPrice, error) {
	body, err := c.doGet("/market_prices/" + name)
	if err != nil {
		return nil, err
	}

	var prices []models.MarketPrice
	if err := json.Unmarshal(body, &prices); err != nil {
		return nil, fmt.Errorf("failed to parse market price: %w", err)
	}

	return prices, nil
}

// GetMarketTrades retrieves recent trades for a market.
func (c *DecibelReadClient) GetMarketTrades(marketName string, limit *int) ([]models.MarketTrade, error) {
	endpoint := "/market_trades/" + marketName
	if limit != nil {
		endpoint += "?limit=" + strconv.Itoa(*limit)
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var trades []models.MarketTrade
	if err := json.Unmarshal(body, &trades); err != nil {
		return nil, fmt.Errorf("failed to parse market trades: %w", err)
	}

	return trades, nil
}

// GetCandlesticks retrieves historical candlestick data.
func (c *DecibelReadClient) GetCandlesticks(marketName, interval string, startTime, endTime *int64) ([]models.Candlestick, error) {
	endpoint := "/candlesticks/" + marketName + "/" + interval
	queryParams := ""
	if startTime != nil {
		queryParams += "&start_time=" + strconv.FormatInt(*startTime, 10)
	}
	if endTime != nil {
		queryParams += "&end_time=" + strconv.FormatInt(*endTime, 10)
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:] // Remove leading &
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var candlesticks []models.Candlestick
	if err := json.Unmarshal(body, &candlesticks); err != nil {
		return nil, fmt.Errorf("failed to parse candlesticks: %w", err)
	}

	return candlesticks, nil
}

// GetAllMarketContexts retrieves context data for all markets.
func (c *DecibelReadClient) GetAllMarketContexts() ([]models.MarketContext, error) {
	body, err := c.doGet("/market_contexts")
	if err != nil {
		return nil, err
	}

	var contexts []models.MarketContext
	if err := json.Unmarshal(body, &contexts); err != nil {
		return nil, fmt.Errorf("failed to parse market contexts: %w", err)
	}

	return contexts, nil
}

// GetAccountOverview retrieves the account overview for a subaccount.
func (c *DecibelReadClient) GetAccountOverview(subaccountAddr string) (*models.AccountOverview, error) {
	body, err := c.doGet("/account_overview/" + subaccountAddr)
	if err != nil {
		return nil, err
	}

	var overview models.AccountOverview
	if err := json.Unmarshal(body, &overview); err != nil {
		return nil, fmt.Errorf("failed to parse account overview: %w", err)
	}

	return &overview, nil
}

// GetUserPositions retrieves all positions for a subaccount.
func (c *DecibelReadClient) GetUserPositions(subaccountAddr string) ([]models.UserPosition, error) {
	body, err := c.doGet("/positions/" + subaccountAddr)
	if err != nil {
		return nil, err
	}

	var positions []models.UserPosition
	if err := json.Unmarshal(body, &positions); err != nil {
		return nil, fmt.Errorf("failed to parse positions: %w", err)
	}

	return positions, nil
}

// GetUserOpenOrders retrieves all open orders for a subaccount.
func (c *DecibelReadClient) GetUserOpenOrders(subaccountAddr string) ([]models.UserOpenOrder, error) {
	body, err := c.doGet("/open_orders/" + subaccountAddr)
	if err != nil {
		return nil, err
	}

	var orders []models.UserOpenOrder
	if err := json.Unmarshal(body, &orders); err != nil {
		return nil, fmt.Errorf("failed to parse open orders: %w", err)
	}

	return orders, nil
}

// GetUserOrderHistory retrieves the order history for a subaccount.
func (c *DecibelReadClient) GetUserOrderHistory(subaccountAddr string, limit, offset *int, marketName *string) ([]models.UserOrderHistoryItem, error) {
	endpoint := "/order_history/" + subaccountAddr
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if marketName != nil {
		queryParams += "&market=" + *marketName
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var history []models.UserOrderHistoryItem
	if err := json.Unmarshal(body, &history); err != nil {
		return nil, fmt.Errorf("failed to parse order history: %w", err)
	}

	return history, nil
}

// GetUserTradeHistory retrieves the trade history for a subaccount.
func (c *DecibelReadClient) GetUserTradeHistory(subaccountAddr string, limit, offset *int, marketName *string) ([]models.UserTradeHistoryItem, error) {
	endpoint := "/trade_history/" + subaccountAddr
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if marketName != nil {
		queryParams += "&market=" + *marketName
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var history []models.UserTradeHistoryItem
	if err := json.Unmarshal(body, &history); err != nil {
		return nil, fmt.Errorf("failed to parse trade history: %w", err)
	}

	return history, nil
}

// GetUserFundingHistory retrieves the funding payment history for a subaccount.
func (c *DecibelReadClient) GetUserFundingHistory(subaccountAddr string, limit, offset *int, marketName *string) ([]models.UserFundingHistoryItem, error) {
	endpoint := "/funding_history/" + subaccountAddr
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if marketName != nil {
		queryParams += "&market=" + *marketName
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var history []models.UserFundingHistoryItem
	if err := json.Unmarshal(body, &history); err != nil {
		return nil, fmt.Errorf("failed to parse funding history: %w", err)
	}

	return history, nil
}

// GetUserFundHistory retrieves the deposit/withdrawal history for a subaccount.
func (c *DecibelReadClient) GetUserFundHistory(subaccountAddr string, limit, offset *int) ([]models.UserFundHistoryItem, error) {
	endpoint := "/fund_history/" + subaccountAddr
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var history []models.UserFundHistoryItem
	if err := json.Unmarshal(body, &history); err != nil {
		return nil, fmt.Errorf("failed to parse fund history: %w", err)
	}

	return history, nil
}

// GetUserSubaccounts retrieves all subaccounts for an owner address.
func (c *DecibelReadClient) GetUserSubaccounts(ownerAddr string) ([]models.UserSubaccount, error) {
	body, err := c.doGet("/subaccounts/" + ownerAddr)
	if err != nil {
		return nil, err
	}

	var subaccounts []models.UserSubaccount
	if err := json.Unmarshal(body, &subaccounts); err != nil {
		return nil, fmt.Errorf("failed to parse subaccounts: %w", err)
	}

	return subaccounts, nil
}

// GetDelegations retrieves all delegations for a subaccount.
func (c *DecibelReadClient) GetDelegations(subaccountAddr string) ([]models.Delegation, error) {
	body, err := c.doGet("/delegations/" + subaccountAddr)
	if err != nil {
		return nil, err
	}

	var delegations []models.Delegation
	if err := json.Unmarshal(body, &delegations); err != nil {
		return nil, fmt.Errorf("failed to parse delegations: %w", err)
	}

	return delegations, nil
}

// GetActiveTwaps retrieves all active TWAP orders for a subaccount.
func (c *DecibelReadClient) GetActiveTwaps(subaccountAddr string) ([]models.UserActiveTwap, error) {
	body, err := c.doGet("/active_twaps/" + subaccountAddr)
	if err != nil {
		return nil, err
	}

	var twaps []models.UserActiveTwap
	if err := json.Unmarshal(body, &twaps); err != nil {
		return nil, fmt.Errorf("failed to parse active TWAPs: %w", err)
	}

	return twaps, nil
}

// GetTwapHistory retrieves the TWAP order history for a subaccount.
func (c *DecibelReadClient) GetTwapHistory(subaccountAddr string, limit, offset *int) ([]models.UserTwapHistoryItem, error) {
	endpoint := "/twap_history/" + subaccountAddr
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var history []models.UserTwapHistoryItem
	if err := json.Unmarshal(body, &history); err != nil {
		return nil, fmt.Errorf("failed to parse TWAP history: %w", err)
	}

	return history, nil
}

// GetVaults retrieves all vaults.
func (c *DecibelReadClient) GetVaults(limit, offset *int) ([]models.Vault, error) {
	endpoint := "/vaults"
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var vaults []models.Vault
	if err := json.Unmarshal(body, &vaults); err != nil {
		return nil, fmt.Errorf("failed to parse vaults: %w", err)
	}

	return vaults, nil
}

// GetUserOwnedVaults retrieves vaults owned by a user.
func (c *DecibelReadClient) GetUserOwnedVaults(ownerAddr string) ([]models.Vault, error) {
	body, err := c.doGet("/vaults/owner/" + ownerAddr)
	if err != nil {
		return nil, err
	}

	var vaults []models.Vault
	if err := json.Unmarshal(body, &vaults); err != nil {
		return nil, fmt.Errorf("failed to parse user vaults: %w", err)
	}

	return vaults, nil
}

// GetUserPerformancesOnVaults retrieves performance metrics for vaults the user has interacted with.
func (c *DecibelReadClient) GetUserPerformancesOnVaults(userAddr string) ([]models.VaultPerformance, error) {
	body, err := c.doGet("/vaults/performance/" + userAddr)
	if err != nil {
		return nil, err
	}

	var performances []models.VaultPerformance
	if err := json.Unmarshal(body, &performances); err != nil {
		return nil, fmt.Errorf("failed to parse vault performances: %w", err)
	}

	return performances, nil
}

// GetLeaderboard retrieves the leaderboard.
func (c *DecibelReadClient) GetLeaderboard(limit, offset *int) ([]models.LeaderboardEntry, error) {
	endpoint := "/leaderboard"
	queryParams := ""
	if limit != nil {
		queryParams += "&limit=" + strconv.Itoa(*limit)
	}
	if offset != nil {
		queryParams += "&offset=" + strconv.Itoa(*offset)
	}
	if queryParams != "" {
		endpoint += "?" + queryParams[1:]
	}

	body, err := c.doGet(endpoint)
	if err != nil {
		return nil, err
	}

	var leaderboard []models.LeaderboardEntry
	if err := json.Unmarshal(body, &leaderboard); err != nil {
		return nil, fmt.Errorf("failed to parse leaderboard: %w", err)
	}

	return leaderboard, nil
}
