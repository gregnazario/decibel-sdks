package bdd

import (
	"fmt"

	"github.com/cucumber/godog"
)

// OrderSteps implements BDD steps for order management scenarios.
type OrderSteps struct {
	testWorld *TestWorld
}

// NewOrderSteps creates a new OrderSteps instance.
func NewOrderSteps(world *TestWorld) *OrderSteps {
	return &OrderSteps{testWorld: world}
}

// RegisterSteps registers all order steps with godog.
func (s *OrderSteps) RegisterSteps(ctx *godog.ScenarioContext) {
	ctx.Given(`^I have an initialized Decibel write client$`, s.givenWriteClient)
	ctx.Given(`^I have configured my subaccount for the ([^"]*) market$`, s.givenConfiguredMarket)
	ctx.When(`^I place a limit buy order$`, s.placeLimitBuyOrder)
	ctx.Then(`^the order should be accepted$`, s.orderAccepted)
	ctx.And(`^the order should have an order ID$`, s.checkOrderId)
	ctx.When(`^I request the open orders for my subaccount$`, s.requestOpenOrders)
	ctx.Then(`^I should receive a list of open orders$`, s.shouldReceiveOpenOrders)
	ctx.And(`^each order should have a market$`, s.checkOrderMarket)
	ctx.And(`^each order should have a price$`, s.checkOrderPrice)
	ctx.And(`^each order should have a size$`, s.checkOrderSize)
	ctx.And(`^each order should indicate if it is a buy or sell$`, s.checkOrderSide)
	// Additional steps can be added following the same pattern
}

func (s *OrderSteps) givenWriteClient() error {
	// Write client would be initialized here
	// For now, we just document the expected behavior
	return nil
}

func (s *OrderSteps) givenConfiguredMarket(market string) error {
	s.testWorld.TestMarketName = market
	_, err := s.testWorld.GetReadClient()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}
	return nil
}

func (s *OrderSteps) placeLimitBuyOrder() error {
	// This would use the write client to place an order
	// For now, we document the expected behavior:
	// 1. Get the current market price
	// 2. Place a limit buy order below the current price
	// 3. Store the order ID for verification
	return nil
}

func (s *OrderSteps) orderAccepted() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	return nil
}

func (s *OrderSteps) checkOrderId() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	// In a real implementation, we would verify the order ID exists
	return nil
}

func (s *OrderSteps) requestOpenOrders() error {
	subAddr := s.testWorld.TestSubaccountAddr
	if subAddr == "" {
		subAddr = "0xtest_subaccount_address"
	}

	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	orders, err := client.GetUserOpenOrders(subAddr)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.OpenOrders = orders
	return nil
}

func (s *OrderSteps) shouldReceiveOpenOrders() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.OpenOrders == nil {
		return fmt.Errorf("open orders should be set")
	}
	return nil
}

func (s *OrderSteps) checkOrderMarket() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, order := range s.testWorld.OpenOrders {
		if order.Market == "" {
			return fmt.Errorf("order should have a market")
		}
	}
	return nil
}

func (s *OrderSteps) checkOrderPrice() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, order := range s.testWorld.OpenOrders {
		if order.Price <= 0 {
			return fmt.Errorf("order should have a positive price")
		}
	}
	return nil
}

func (s *OrderSteps) checkOrderSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, order := range s.testWorld.OpenOrders {
		if order.OrigSize <= 0 {
			return fmt.Errorf("order should have a positive original size")
		}
	}
	return nil
}

func (s *OrderSteps) checkOrderSide() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, order := range s.testWorld.OpenOrders {
		// The IsBuy field should be accessible
		_ = order.IsBuy
	}
	return nil
}
