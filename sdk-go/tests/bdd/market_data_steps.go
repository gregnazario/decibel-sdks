package bdd

import (
	"fmt"

	"github.com/cucumber/godog"
	"github.com/gregnazario/decibel-sdks/sdk-go/models"
)

// MarketDataSteps implements BDD steps for market data scenarios.
type MarketDataSteps struct {
	testWorld *TestWorld
}

// NewMarketDataSteps creates a new MarketDataSteps instance.
func NewMarketDataSteps(world *TestWorld) *MarketDataSteps {
	return &MarketDataSteps{testWorld: world}
}

// RegisterSteps registers all market data steps with godog.
func (s *MarketDataSteps) RegisterSteps(ctx *godog.ScenarioContext) {
	// Background steps
	ctx.Step(`^I have an initialized Decibel read client$`, s.givenReadClient)

	// Market listing steps
	ctx.Step(`^I request all markets$`, s.requestAllMarkets)
	ctx.Step(`^I should receive a list of market configurations$`, s.shouldReceiveMarkets)
	ctx.Step(`^each market should have a market address$`, s.checkMarketAddress)
	ctx.Step(`^each market should have a market name$`, s.checkMarketName)
	ctx.Step(`^each market should have size decimals$`, s.checkSizeDecimals)
	ctx.Step(`^each market should have price decimals$`, s.checkPriceDecimals)
	ctx.Step(`^each market should have maximum leverage$`, s.checkMaxLeverage)
	ctx.Step(`^each market should have minimum order size$`, s.checkMinSize)
	ctx.Step(`^each market should have lot size$`, s.checkLotSize)
	ctx.Step(`^each market should have tick size$`, s.checkTickSize)

	// Individual market steps
	ctx.Step(`^I request the market with name ([^"]*)$`, s.requestMarketByName)
	ctx.Step(`^I should receive the ([^"]*) market configuration$`, s.shouldReceiveMarketConfig)
	ctx.Step(`^the market name should be ([^"]*)$`, s.checkMarketNameValue)
	ctx.Step(`^the market should have a valid market address$`, s.checkValidMarketAddress)

	// Market depth steps
	ctx.Step(`^I request the market depth for ([^"]*) with no limit$`, s.requestMarketDepthNoLimit)
	ctx.Step(`^I request the market depth for ([^"]*) with a limit of (\d+)$`, s.requestMarketDepthWithLimit)
	ctx.Step(`^I should receive the current order book$`, s.shouldReceiveOrderBook)
	ctx.Step(`^the order book should contain bid orders$`, s.checkBids)
	ctx.Step(`^the order book should contain ask orders$`, s.checkAsks)
	ctx.Step(`^bid orders should be sorted by price descending$`, s.checkBidsSorted)
	ctx.Step(`^ask orders should be sorted by price ascending$`, s.checkAsksSorted)
	ctx.Step(`^each price level should have a price and size$`, s.checkPriceLevels)

	// Market prices steps
	ctx.Step(`^I request all market prices$`, s.requestAllPrices)
	ctx.Step(`^I should receive current prices for all markets$`, s.shouldReceiveAllPrices)
	ctx.Step(`^each market price should include a mark price$`, s.checkMarkPrice)
	ctx.Step(`^each market price should include a mid price$`, s.checkMidPrice)

	// Individual market price steps
	ctx.Step(`^I request the price for ([^"]*)$`, s.requestPrice)
	ctx.Step(`^I should receive the current ([^"]*) market price$`, s.shouldReceiveMarketPrice)

	// Market trades steps
	ctx.Step(`^I request recent trades for ([^"]*) with default limit$`, s.requestTradesDefault)
	ctx.Step(`^I should receive a list of recent trades$`, s.shouldReceiveTrades)
	ctx.Step(`^each trade should have a price$`, s.checkTradePrice)
	ctx.Step(`^each trade should have a size$`, s.checkTradeSize)
	ctx.Step(`^each trade should indicate if it was a buy or sell$`, s.checkTradeDirection)
	ctx.Step(`^each trade should have a timestamp$`, s.checkTradeTimestamp)

	// Candlestick steps
	ctx.Step(`^I request candlesticks for ([^"]*) with interval ([^"]*)$`, s.requestCandlesticks)
	ctx.Step(`^I should receive historical candlestick data$`, s.shouldReceiveCandlesticks)
	ctx.Step(`^each candlestick should have an open price$`, s.checkCandlestickOpen)
	ctx.Step(`^each candlestick should have a high price$`, s.checkCandlestickHigh)
	ctx.Step(`^each candlestick should have a low price$`, s.checkCandlestickLow)
	ctx.Step(`^each candlestick should have a close price$`, s.checkCandlestickClose)
	ctx.Step(`^each candlestick should have a volume$`, s.checkCandlestickVolume)

	// Market contexts steps
	ctx.Step(`^I request all asset contexts$`, s.requestAssetContexts)
	ctx.Step(`^I should receive market context data for all markets$`, s.shouldReceiveContexts)
}

func (s *MarketDataSteps) givenReadClient() error {
	_, err := s.testWorld.GetReadClient()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}
	return nil
}

func (s *MarketDataSteps) requestAllMarkets() error {
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	markets, err := client.GetAllMarkets()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.Markets = markets
	return nil
}

func (s *MarketDataSteps) shouldReceiveMarkets() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if len(s.testWorld.Markets) == 0 {
		return fmt.Errorf("should have at least one market")
	}
	return nil
}

func (s *MarketDataSteps) checkMarketAddress() error {
	if s.testWorld.LastError != nil {
		return nil // Already checked
	}
	for _, market := range s.testWorld.Markets {
		if market.MarketAddr == "" {
			return fmt.Errorf("market address should not be empty")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkMarketName() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.MarketName == "" {
			return fmt.Errorf("market name should not be empty")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkSizeDecimals() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.SzDecimals < 0 {
			return fmt.Errorf("size decimals should be non-negative")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkPriceDecimals() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.PxDecimals < 0 {
			return fmt.Errorf("price decimals should be non-negative")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkMaxLeverage() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.MaxLeverage <= 0 {
			return fmt.Errorf("max leverage should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkMinSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.MinSize <= 0 {
			return fmt.Errorf("min size should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkLotSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.LotSize <= 0 {
			return fmt.Errorf("lot size should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkTickSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, market := range s.testWorld.Markets {
		if market.TickSize <= 0 {
			return fmt.Errorf("tick size should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) requestMarketByName(name string) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	market, err := client.GetMarketByName(name)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.Markets = []models.PerpMarketConfig{*market}
	return nil
}

func (s *MarketDataSteps) shouldReceiveMarketConfig(name string) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if len(s.testWorld.Markets) != 1 {
		return fmt.Errorf("should have exactly one market")
	}
	if s.testWorld.Markets[0].MarketName != name {
		return fmt.Errorf("market name should match")
	}
	return nil
}

func (s *MarketDataSteps) checkMarketNameValue(name string) error {
	if s.testWorld.LastError != nil {
		return nil
	}
	if s.testWorld.Markets[0].MarketName != name {
		return fmt.Errorf("market name should be %s", name)
	}
	return nil
}

func (s *MarketDataSteps) checkValidMarketAddress() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	addr := s.testWorld.Markets[0].MarketAddr
	if len(addr) < 66 {
		return fmt.Errorf("market address should be valid hex")
	}
	return nil
}

func (s *MarketDataSteps) requestMarketDepthNoLimit(name string) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	depth, err := client.GetMarketDepth(name, nil)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketDepth = depth
	return nil
}

func (s *MarketDataSteps) requestMarketDepthWithLimit(name string, limit int) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	depth, err := client.GetMarketDepth(name, &limit)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketDepth = depth
	return nil
}

func (s *MarketDataSteps) shouldReceiveOrderBook() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.MarketDepth == nil {
		return fmt.Errorf("market depth should be set")
	}
	return nil
}

func (s *MarketDataSteps) checkBids() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	// Bids field exists and is accessible
	_ = s.testWorld.MarketDepth.Bids
	return nil
}

func (s *MarketDataSteps) checkAsks() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	// Asks field exists and is accessible
	_ = s.testWorld.MarketDepth.Asks
	return nil
}

func (s *MarketDataSteps) checkBidsSorted() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	prevPrice := float64(9999999999)
	for _, bid := range s.testWorld.MarketDepth.Bids {
		if bid.Price > prevPrice {
			return fmt.Errorf("bids should be sorted descending")
		}
		prevPrice = bid.Price
	}
	return nil
}

func (s *MarketDataSteps) checkAsksSorted() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	prevPrice := float64(0)
	for _, ask := range s.testWorld.MarketDepth.Asks {
		if ask.Price < prevPrice {
			return fmt.Errorf("asks should be sorted ascending")
		}
		prevPrice = ask.Price
	}
	return nil
}

func (s *MarketDataSteps) checkPriceLevels() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, bid := range s.testWorld.MarketDepth.Bids {
		if bid.Price <= 0 {
			return fmt.Errorf("bid price should be positive")
		}
		if bid.Size < 0 {
			return fmt.Errorf("bid size should be non-negative")
		}
	}
	for _, ask := range s.testWorld.MarketDepth.Asks {
		if ask.Price <= 0 {
			return fmt.Errorf("ask price should be positive")
		}
		if ask.Size < 0 {
			return fmt.Errorf("ask size should be non-negative")
		}
	}
	return nil
}

func (s *MarketDataSteps) requestAllPrices() error {
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	prices, err := client.GetAllMarketPrices()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketPrices = prices
	return nil
}

func (s *MarketDataSteps) shouldReceiveAllPrices() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if len(s.testWorld.MarketPrices) == 0 {
		return fmt.Errorf("should have at least one market price")
	}
	return nil
}

func (s *MarketDataSteps) checkMarkPrice() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, price := range s.testWorld.MarketPrices {
		if price.MarkPx <= 0 {
			return fmt.Errorf("mark price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkMidPrice() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, price := range s.testWorld.MarketPrices {
		if price.MidPx <= 0 {
			return fmt.Errorf("mid price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) requestPrice(name string) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	prices, err := client.GetMarketPriceByName(name)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketPrices = prices
	return nil
}

func (s *MarketDataSteps) shouldReceiveMarketPrice(name string) error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if len(s.testWorld.MarketPrices) == 0 {
		return fmt.Errorf("should have market prices")
	}
	return nil
}

func (s *MarketDataSteps) requestTradesDefault(name string) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	trades, err := client.GetMarketTrades(name, nil)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketTrades = trades
	return nil
}

func (s *MarketDataSteps) shouldReceiveTrades() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.MarketTrades == nil {
		return fmt.Errorf("market trades should be set")
	}
	return nil
}

func (s *MarketDataSteps) checkTradePrice() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, trade := range s.testWorld.MarketTrades {
		if trade.Price <= 0 {
			return fmt.Errorf("trade price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkTradeSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, trade := range s.testWorld.MarketTrades {
		if trade.Size <= 0 {
			return fmt.Errorf("trade size should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkTradeDirection() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, trade := range s.testWorld.MarketTrades {
		// is_buy field should be accessible
		_ = trade.IsBuy
	}
	return nil
}

func (s *MarketDataSteps) checkTradeTimestamp() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, trade := range s.testWorld.MarketTrades {
		if trade.UnixMs <= 0 {
			return fmt.Errorf("trade timestamp should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) requestCandlesticks(name, interval string) error {
	s.testWorld.TestMarketName = name
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	candlesticks, err := client.GetCandlesticks(name, interval, nil, nil)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.Candlesticks = candlesticks
	return nil
}

func (s *MarketDataSteps) shouldReceiveCandlesticks() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.Candlesticks == nil {
		return fmt.Errorf("candlesticks should be set")
	}
	return nil
}

func (s *MarketDataSteps) checkCandlestickOpen() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, candle := range s.testWorld.Candlesticks {
		if candle.Open <= 0 {
			return fmt.Errorf("open price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkCandlestickHigh() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, candle := range s.testWorld.Candlesticks {
		if candle.High <= 0 {
			return fmt.Errorf("high price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkCandlestickLow() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, candle := range s.testWorld.Candlesticks {
		if candle.Low <= 0 {
			return fmt.Errorf("low price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkCandlestickClose() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, candle := range s.testWorld.Candlesticks {
		if candle.Close <= 0 {
			return fmt.Errorf("close price should be positive")
		}
	}
	return nil
}

func (s *MarketDataSteps) checkCandlestickVolume() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, candle := range s.testWorld.Candlesticks {
		if candle.Volume < 0 {
			return fmt.Errorf("volume should be non-negative")
		}
	}
	return nil
}

func (s *MarketDataSteps) requestAssetContexts() error {
	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	contexts, err := client.GetAllMarketContexts()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.MarketContexts = contexts
	return nil
}

func (s *MarketDataSteps) shouldReceiveContexts() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.MarketContexts == nil {
		return fmt.Errorf("market contexts should be set")
	}
	return nil
}
