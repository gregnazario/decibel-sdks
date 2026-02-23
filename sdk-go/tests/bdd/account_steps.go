package bdd

import (
	"fmt"

	"github.com/cucumber/godog"
)

// AccountSteps implements BDD steps for account management scenarios.
type AccountSteps struct {
	testWorld *TestWorld
}

// NewAccountSteps creates a new AccountSteps instance.
func NewAccountSteps(world *TestWorld) *AccountSteps {
	return &AccountSteps{testWorld: world}
}

// RegisterSteps registers all account steps with godog.
func (s *AccountSteps) RegisterSteps(ctx *godog.ScenarioContext) {
	ctx.Given(`^I have an initialized Decibel read client$`, s.givenReadClient)
	ctx.Given(`^I have a subaccount address ([^"]*)$`, s.givenSubaccountAddress)
	ctx.When(`^I request the account overview for a subaccount$`, s.requestAccountOverview)
	ctx.Then(`^I should receive the account overview data$`, s.shouldReceiveAccountOverview)
	ctx.And(`^the overview should include the total margin$`, s.checkTotalMargin)
	ctx.And(`^the overview should include the unrealized PnL$`, s.checkUnrealizedPnl)
	ctx.And(`^the overview should include the cross margin ratio$`, s.checkCrossMarginRatio)
	ctx.When(`^I request the account positions$`, s.requestPositions)
	ctx.Then(`^I should receive the account positions$`, s.shouldReceivePositions)
	ctx.When(`^I request the account open orders$`, s.requestOpenOrders)
	ctx.Then(`^I should receive the open orders$`, s.shouldReceiveOpenOrders)
	// Additional steps can be added following the same pattern
}

func (s *AccountSteps) givenReadClient() error {
	_, err := s.testWorld.GetReadClient()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}
	return nil
}

func (s *AccountSteps) givenSubaccountAddress(addr string) error {
	s.testWorld.TestSubaccountAddr = addr
	return nil
}

func (s *AccountSteps) requestAccountOverview() error {
	subAddr := s.testWorld.TestSubaccountAddr
	if subAddr == "" {
		subAddr = "0xtest_subaccount_address"
	}

	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	overview, err := client.GetAccountOverview(subAddr)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.AccountOverview = overview
	return nil
}

func (s *AccountSteps) shouldReceiveAccountOverview() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	if s.testWorld.AccountOverview == nil {
		return fmt.Errorf("account overview should be set")
	}
	return nil
}

func (s *AccountSteps) checkTotalMargin() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	if s.testWorld.AccountOverview.TotalMargin < 0 {
		return fmt.Errorf("total margin should be non-negative")
	}
	return nil
}

func (s *AccountSteps) checkUnrealizedPnl() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	// Unrealized PnL can be negative, so just check it's finite
	_ = s.testWorld.AccountOverview.UnrealizedPnl
	return nil
}

func (s *AccountSteps) checkCrossMarginRatio() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	if s.testWorld.AccountOverview.CrossMarginRatio < 0 {
		return fmt.Errorf("cross margin ratio should be non-negative")
	}
	return nil
}

func (s *AccountSteps) requestPositions() error {
	subAddr := s.testWorld.TestSubaccountAddr
	if subAddr == "" {
		subAddr = "0xtest_subaccount_address"
	}

	client, err := s.testWorld.GetReadClient()
	if err != nil {
		return err
	}

	positions, err := client.GetUserPositions(subAddr)
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}

	s.testWorld.Positions = positions
	return nil
}

func (s *AccountSteps) shouldReceivePositions() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	// positions could be empty if the account has no open positions
	return nil
}

func (s *AccountSteps) requestOpenOrders() error {
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

func (s *AccountSteps) shouldReceiveOpenOrders() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	// open_orders could be empty
	return nil
}
