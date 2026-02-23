package bdd

import (
	"context"
	"flag"
	"fmt"
	"os"
	"testing"

	"github.com/cucumber/godog"
	"github.com/cucumber/godog/colors"
)

var opt = godog.Options{
	Output: colors.Colored(os.Stdout),
	Format: "pretty",
}

func init() {
	godog.BindFlags("godog.", flag.CommandLine, &opt)
}

func TestFeatures(t *testing.T) {
	o := opt
	if godog.TestSuite{
		Name:                "bdd",
		ScenarioInitializer:  InitializeScenario,
		Options:             &o,
	}.Run() != 0 {
		t.Fatal("failed to run feature suite")
	}
}

// InitializeScenario sets up the scenario context.
func InitializeScenario(ctx *godog.ScenarioContext) {
	world := NewTestWorld()

	// Register step definitions
	configSteps := NewConfigSteps(world)
	configSteps.RegisterSteps(ctx)

	marketDataSteps := NewMarketDataSteps(world)
	marketDataSteps.RegisterSteps(ctx)

	accountSteps := NewAccountSteps(world)
	accountSteps.RegisterSteps(ctx)

	orderSteps := NewOrderSteps(world)
	orderSteps.RegisterSteps(ctx)

	positionSteps := NewPositionSteps(world)
	positionSteps.RegisterSteps(ctx)

	// Clear world before each scenario
	ctx.Before(func(ctx context.Context, sc *godog.Scenario) (context.Context, error) {
		world.Clear()
		return ctx, nil
	})

	// Print scenario name for debugging
	ctx.Before(func(ctx context.Context, sc *godog.Scenario) (context.Context, error) {
		fmt.Printf("\n=== Running Scenario: %s ===\n", sc.Name)
		return ctx, nil
	})
}
