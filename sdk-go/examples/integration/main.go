// Integration example: list markets, check balance, place a trade, check balance again.
//
// Usage:
//
//	export DECIBEL_PRIVATE_KEY="0x..."
//	export DECIBEL_ACCOUNT_ADDRESS="0x..."
//	export APTOS_NODE_API_KEY="..."          # optional
//	go run ./examples/integration
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// Minimal inline client so the example is self-contained.
// In production, use the decibel package directly.

var (
	baseURL = "https://api.testnet.decibel.trade/api/v1"
	apiKey  = os.Getenv("APTOS_NODE_API_KEY")
)

func get(path string, out interface{}) error {
	req, _ := http.NewRequest("GET", baseURL+path, nil)
	if apiKey != "" {
		req.Header.Set("x-api-key", apiKey)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API %d: %s", resp.StatusCode, body)
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

type Market struct {
	MarketAddr  string  `json:"market_addr"`
	MarketName  string  `json:"market_name"`
	MaxLeverage float64 `json:"max_leverage"`
	TickSize    float64 `json:"tick_size"`
	LotSize     float64 `json:"lot_size"`
	MinSize     float64 `json:"min_size"`
}

type Price struct {
	Market   string  `json:"market"`
	MarkPx   float64 `json:"mark_px"`
	MidPx    float64 `json:"mid_px"`
	OraclePx float64 `json:"oracle_px"`
}

type BookLevel struct {
	Price float64 `json:"price"`
	Size  float64 `json:"size"`
}

type Depth struct {
	Market string      `json:"market"`
	Bids   []BookLevel `json:"bids"`
	Asks   []BookLevel `json:"asks"`
}

type AccountOverview struct {
	PerpEquityBalance float64  `json:"perp_equity_balance"`
	TotalMargin       float64  `json:"total_margin"`
	UnrealizedPnl     float64  `json:"unrealized_pnl"`
	Withdrawable      float64  `json:"usdc_cross_withdrawable_balance"`
	Volume            *float64 `json:"volume"`
}

type OpenOrder struct {
	OrderID       string  `json:"order_id"`
	Market        string  `json:"market"`
	Price         float64 `json:"price"`
	RemainingSize float64 `json:"remaining_size"`
	IsBuy         bool    `json:"is_buy"`
}

func main() {
	privateKey := os.Getenv("DECIBEL_PRIVATE_KEY")
	accountAddr := os.Getenv("DECIBEL_ACCOUNT_ADDRESS")
	_ = privateKey // used by the write path (on-chain tx, omitted here for brevity)

	if accountAddr == "" {
		fmt.Println("Set DECIBEL_ACCOUNT_ADDRESS (and optionally DECIBEL_PRIVATE_KEY) env vars.")
		fmt.Println("This example will still run the read-only steps.")
		accountAddr = "0x0000000000000000000000000000000000000000000000000000000000000001"
	}

	// ── 1. List all available markets ───────────────────────────────────
	fmt.Println("=== Available Markets ===")
	var markets []Market
	if err := get("/markets", &markets); err != nil {
		fmt.Printf("  Error fetching markets: %v\n", err)
		fmt.Println("  (Is the testnet API reachable?)")
		os.Exit(1)
	}
	for _, m := range markets {
		fmt.Printf("  %-12s  max_lev: %5.0fx  tick: %-8g  lot: %g\n",
			m.MarketName, m.MaxLeverage, m.TickSize, m.LotSize)
	}
	fmt.Printf("Total markets: %d\n\n", len(markets))

	if len(markets) == 0 {
		fmt.Println("No markets found. Exiting.")
		return
	}

	name := markets[0].MarketName

	// ── 2. Fetch current price ──────────────────────────────────────────
	var prices []Price
	if err := get("/prices/"+name, &prices); err == nil && len(prices) > 0 {
		p := prices[0]
		fmt.Printf("=== %s Prices ===\n  mark: %.2f  mid: %.2f  oracle: %.2f\n\n",
			name, p.MarkPx, p.MidPx, p.OraclePx)
	}

	// ── 3. Fetch order book depth ───────────────────────────────────────
	var depth Depth
	if err := get(fmt.Sprintf("/depth/%s?limit=5", name), &depth); err == nil {
		fmt.Printf("=== %s Order Book (top 5) ===\n", name)
		fmt.Println("  Bids:")
		for _, b := range depth.Bids {
			fmt.Printf("    %.4f @ %.2f\n", b.Size, b.Price)
		}
		fmt.Println("  Asks:")
		for _, a := range depth.Asks {
			fmt.Printf("    %.4f @ %.2f\n", a.Size, a.Price)
		}
		fmt.Println()
	}

	// ── 4. Check balance BEFORE trade ───────────────────────────────────
	// NOTE: subaccount address derivation requires on-chain SDK;
	// here we show the API call pattern.
	subaccount := accountAddr // In practice, derive the primary subaccount address
	var overview AccountOverview
	if err := get("/account/"+subaccount, &overview); err == nil {
		fmt.Println("=== Balance BEFORE Trade ===")
		fmt.Printf("  equity:       %.2f\n", overview.PerpEquityBalance)
		fmt.Printf("  margin:       %.2f\n", overview.TotalMargin)
		fmt.Printf("  unrealised:   %.2f\n", overview.UnrealizedPnl)
		fmt.Printf("  withdrawable: %.2f\n\n", overview.Withdrawable)
	} else {
		fmt.Printf("  (Could not fetch account overview: %v)\n\n", err)
	}

	// ── 5. Place a trade ────────────────────────────────────────────────
	// Placing an on-chain order requires building and signing an Aptos
	// transaction. The full flow is:
	//
	//   1. Build the Move entry-function payload
	//   2. Simulate to estimate gas (optional)
	//   3. Sign with Ed25519 private key
	//   4. Submit via gas station or directly
	//   5. Wait for confirmation
	//
	// This is shown conceptually below. The actual implementation lives
	// in the decibel.DecibelWriteClient (not yet wired to Aptos in the
	// Go SDK — use the Rust or TypeScript SDK for a full example).
	fmt.Println("=== Placing Order (conceptual) ===")
	fmt.Printf("  market: %s  side: BUY  price: <10%% below mid>  size: %g  tif: GTC\n",
		name, markets[0].MinSize)
	if privateKey == "" {
		fmt.Println("  (Skipped — set DECIBEL_PRIVATE_KEY to submit on-chain)")
	} else {
		fmt.Println("  → Would build + sign + submit Aptos transaction here.")
		fmt.Println("  → See sdk-rust/examples/integration.rs for the full flow.")
	}
	fmt.Println()

	// ── 6. Check balance AFTER trade ────────────────────────────────────
	// In a real flow, sleep briefly then re-query.
	time.Sleep(500 * time.Millisecond)
	if err := get("/account/"+subaccount, &overview); err == nil {
		fmt.Println("=== Balance AFTER Trade ===")
		fmt.Printf("  equity:       %.2f\n", overview.PerpEquityBalance)
		fmt.Printf("  margin:       %.2f\n", overview.TotalMargin)
		fmt.Printf("  unrealised:   %.2f\n", overview.UnrealizedPnl)
		fmt.Printf("  withdrawable: %.2f\n\n", overview.Withdrawable)
	}

	// ── 7. Show open orders ─────────────────────────────────────────────
	var openOrders []OpenOrder
	if err := get("/open-orders/"+subaccount, &openOrders); err == nil {
		fmt.Printf("=== Open Orders (%d) ===\n", len(openOrders))
		for _, o := range openOrders {
			side := "SELL"
			if o.IsBuy {
				side = "BUY"
			}
			fmt.Printf("  %s %s %s @ %.2f (remaining: %.4f)\n",
				o.OrderID, side, o.Market, o.Price, o.RemainingSize)
		}
	}

	fmt.Println("\nDone.")
}
