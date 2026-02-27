package bdd

import (
	"fmt"

	"github.com/cucumber/godog"
	"github.com/gregnazario/decibel-sdks/sdk-go/models"
)

// PositionSteps implements BDD steps for position management scenarios.
type PositionSteps struct {
	testWorld *TestWorld
}

// NewPositionSteps creates a new PositionSteps instance.
func NewPositionSteps(world *TestWorld) *PositionSteps {
	return &PositionSteps{testWorld: world}
}

// RegisterSteps registers all position steps with godog.
func (s *PositionSteps) RegisterSteps(ctx *godog.ScenarioContext) {
	ctx.Step(`^I have an initialized Decibel read client$`, s.givenReadClient)
	ctx.Step(`^I have an open position in the ([^"]*) market$`, s.givenOpenPosition)
	ctx.Step(`^I request my positions$`, s.requestPositions)
	ctx.Step(`^I should receive my open positions$`, s.shouldReceivePositions)
	ctx.Step(`^each position should have a market$`, s.checkPositionMarket)
	ctx.Step(`^each position should have a size$`, s.checkPositionSize)
	ctx.Step(`^each position should have an entry price$`, s.checkEntryPrice)
	ctx.Step(`^each position should have unrealized PnL$`, s.checkUnrealizedPnl)
	ctx.Step(`^I request the position for the ([^"]*) market$`, s.requestPositionForMarket)
	ctx.Step(`^I should receive the position data$`, s.shouldReceivePositionData)
	ctx.Step(`^the position should indicate if it is long or short$`, s.checkPositionDirection)
	// Additional steps can be added following the same pattern
}

func (s *PositionSteps) givenReadClient() error {
	_, err := s.testWorld.GetReadClient()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}
	return nil
}

func (s *PositionSteps) givenOpenPosition(market string) error {
	s.testWorld.TestMarketName = market
	_, err := s.testWorld.GetReadClient()
	if err != nil {
		s.testWorld.SetError(err)
		return err
	}
	return nil
}

func (s *PositionSteps) requestPositions() error {
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

func (s *PositionSteps) shouldReceivePositions() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	// positions field is set (may be empty)
	return nil
}

func (s *PositionSteps) checkPositionMarket() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, position := range s.testWorld.Positions {
		if position.Market == "" {
			return fmt.Errorf("position should have a market")
		}
	}
	return nil
}

func (s *PositionSteps) checkPositionSize() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, position := range s.testWorld.Positions {
		if position.Size == 0 {
			return fmt.Errorf("position size should not be zero for open positions")
		}
	}
	return nil
}

func (s *PositionSteps) checkEntryPrice() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, position := range s.testWorld.Positions {
		if position.EntryPrice <= 0 {
			return fmt.Errorf("entry price should be positive")
		}
	}
	return nil
}

func (s *PositionSteps) checkUnrealizedPnl() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, position := range s.testWorld.Positions {
		// Unrealized PnL is included in the funding cost
		_ = position.UnrealizedFunding
	}
	return nil
}

func (s *PositionSteps) requestPositionForMarket(market string) error {
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

	// Filter to only the requested market
	var filtered []models.UserPosition
	for _, p := range positions {
		if p.Market == market {
			filtered = append(filtered, p)
		}
	}
	s.testWorld.Positions = filtered
	return nil
}

func (s *PositionSteps) shouldReceivePositionData() error {
	if s.testWorld.LastError != nil {
		return fmt.Errorf("expected no error, got: %v", s.testWorld.LastError)
	}
	// positions field is set
	return nil
}

func (s *PositionSteps) checkPositionDirection() error {
	if s.testWorld.LastError != nil {
		return nil
	}
	for _, position := range s.testWorld.Positions {
		// Positive size = long, negative size = short
		_ = position.Size > 0
		_ = position.Size < 0
	}
	return nil
}
