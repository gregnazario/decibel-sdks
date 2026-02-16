/// Integration example: list markets, check balance, place a trade, check balance again.
///
/// This file demonstrates the read-only flow using DecibelSDK types.
/// On-chain transaction submission (placing orders) requires Aptos SDK
/// integration which is platform-specific.
///
/// Usage:
///   swift run Integration
///   (or copy into an Xcode project that depends on DecibelSDK)

import Foundation
#if canImport(DecibelSDK)
import DecibelSDK
#endif

// MARK: - Minimal HTTP helper (self-contained example)

let baseURL = "https://api.testnet.decibel.trade/api/v1"

func fetchJSON<T: Decodable>(_ path: String, as type: T.Type) async throws -> T {
    guard let url = URL(string: baseURL + path) else {
        throw URLError(.badURL)
    }
    var request = URLRequest(url: url)
    if let key = ProcessInfo.processInfo.environment["APTOS_NODE_API_KEY"] {
        request.setValue(key, forHTTPHeaderField: "x-api-key")
    }
    let (data, response) = try await URLSession.shared.data(for: request)
    if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
        let body = String(data: data, encoding: .utf8) ?? ""
        throw NSError(domain: "API", code: http.statusCode,
                      userInfo: [NSLocalizedDescriptionKey: body])
    }
    return try JSONDecoder().decode(T.self, from: data)
}

// MARK: - Inline models (mirrors DecibelSDK types)

struct MarketInfo: Codable {
    let market_addr: String
    let market_name: String
    let max_leverage: Double
    let tick_size: Double
    let lot_size: Double
    let min_size: Double
}

struct PriceInfo: Codable {
    let market: String
    let mark_px: Double
    let mid_px: Double
    let oracle_px: Double
    let funding_rate_bps: Double
}

struct BookLevel: Codable {
    let price: Double
    let size: Double
}

struct DepthInfo: Codable {
    let market: String
    let bids: [BookLevel]
    let asks: [BookLevel]
}

struct AccountInfo: Codable {
    let perp_equity_balance: Double
    let total_margin: Double
    let unrealized_pnl: Double
    let usdc_cross_withdrawable_balance: Double
}

struct OrderInfo: Codable {
    let order_id: String
    let market: String
    let price: Double
    let remaining_size: Double
    let is_buy: Bool
}

// MARK: - Main

@main
struct IntegrationExample {
    static func main() async {
        let accountAddr = ProcessInfo.processInfo.environment["DECIBEL_ACCOUNT_ADDRESS"]
            ?? "0x0000000000000000000000000000000000000000000000000000000000000001"

        do {
            // ── 1. List all available markets ───────────────────────────
            print("=== Available Markets ===")
            let markets: [MarketInfo] = try await fetchJSON("/markets", as: [MarketInfo].self)
            for m in markets {
                print("  \(m.market_name)  max_lev: \(m.max_leverage)x  tick: \(m.tick_size)  lot: \(m.lot_size)")
            }
            print("Total markets: \(markets.count)\n")

            guard let market = markets.first else {
                print("No markets found. Exiting.")
                return
            }

            // ── 2. Fetch current price ──────────────────────────────────
            let prices: [PriceInfo] = try await fetchJSON("/prices/\(market.market_name)", as: [PriceInfo].self)
            if let p = prices.first {
                print("=== \(market.market_name) Prices ===")
                print("  mark: \(p.mark_px)  mid: \(p.mid_px)  oracle: \(p.oracle_px)  funding: \(p.funding_rate_bps) bps\n")
            }

            // ── 3. Fetch order book depth ───────────────────────────────
            let depth: DepthInfo = try await fetchJSON("/depth/\(market.market_name)?limit=5", as: DepthInfo.self)
            print("=== \(market.market_name) Order Book (top 5) ===")
            print("  Bids:")
            for b in depth.bids { print("    \(b.size) @ \(b.price)") }
            print("  Asks:")
            for a in depth.asks { print("    \(a.size) @ \(a.price)") }
            print()

            // ── 4. Check balance BEFORE trade ───────────────────────────
            let subaccount = accountAddr
            if let overview: AccountInfo = try? await fetchJSON("/account/\(subaccount)", as: AccountInfo.self) {
                print("=== Balance BEFORE Trade ===")
                print("  equity:       \(overview.perp_equity_balance)")
                print("  margin:       \(overview.total_margin)")
                print("  unrealised:   \(overview.unrealized_pnl)")
                print("  withdrawable: \(overview.usdc_cross_withdrawable_balance)\n")
            } else {
                print("  (Could not fetch account overview)\n")
            }

            // ── 5. Place a trade (conceptual) ───────────────────────────
            print("=== Placing Order (conceptual) ===")
            print("  market: \(market.market_name)  side: BUY  price: <10% below mid>  size: \(market.min_size)  tif: GTC")
            if ProcessInfo.processInfo.environment["DECIBEL_PRIVATE_KEY"] == nil {
                print("  (Skipped — set DECIBEL_PRIVATE_KEY to submit on-chain)")
            } else {
                print("  → Would build + sign + submit Aptos transaction here.")
            }
            print()

            // ── 6. Check balance AFTER trade ────────────────────────────
            try await Task.sleep(nanoseconds: 500_000_000)
            if let overview: AccountInfo = try? await fetchJSON("/account/\(subaccount)", as: AccountInfo.self) {
                print("=== Balance AFTER Trade ===")
                print("  equity:       \(overview.perp_equity_balance)")
                print("  margin:       \(overview.total_margin)")
                print("  unrealised:   \(overview.unrealized_pnl)")
                print("  withdrawable: \(overview.usdc_cross_withdrawable_balance)\n")
            }

            // ── 7. Show open orders ─────────────────────────────────────
            if let orders: [OrderInfo] = try? await fetchJSON("/open-orders/\(subaccount)", as: [OrderInfo].self) {
                print("=== Open Orders (\(orders.count)) ===")
                for o in orders {
                    let side = o.is_buy ? "BUY" : "SELL"
                    print("  \(o.order_id) \(side) \(o.market) @ \(o.price) (remaining: \(o.remaining_size))")
                }
            }

            print("\nDone.")

        } catch {
            print("Error: \(error)")
        }
    }
}
