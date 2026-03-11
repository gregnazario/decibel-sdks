import Foundation
@testable import DecibelSDK

/// TestWorld maintains state across BDD test scenarios.
class TestWorld {
    // Configuration
    var config: DecibelConfig?
    var apiKey: String? = ProcessInfo.processInfo.environment["DECIBEL_API_KEY"]

    // Clients
    var readClient: DecibelReadClient?

    // Error state
    var lastError: Error?

    // Market data
    var markets: [PerpMarketConfig] = []
    var marketDepth: MarketDepth?
    var marketPrices: [MarketPrice] = []
    var candlesticks: [Candlestick] = []
    var marketContexts: [MarketContext] = []
    var marketTrades: [MarketTrade] = []

    // Account data
    var accountOverview: AccountOverview?
    var positions: [UserPosition] = []
    var openOrders: [UserOpenOrder] = []
    var orderHistory: [UserOrderHistoryItem] = []
    var tradeHistory: [UserTradeHistoryItem] = []
    var fundingHistory: [UserFundingHistoryItem] = []
    var fundHistory: [UserFundHistoryItem] = []
    var subaccounts: [UserSubaccount] = []
    var delegations: [Delegation] = []

    // TWAP data
    var activeTwaps: [UserActiveTwap] = []
    var twapHistory: [UserTwapHistoryItem] = []

    // Vault data
    var vaults: [Vault] = []
    var userVaults: [Vault] = []
    var vaultPerformances: [VaultPerformance] = []

    // Leaderboard
    var leaderboard: [LeaderboardEntry] = []

    // Test data
    var testMarketName: String = ""
    var testSubaccountAddr: String = ""

    /// Resets the test world state.
    func clear() {
        config = nil
        readClient = nil
        lastError = nil
        markets.removeAll()
        marketDepth = nil
        marketPrices.removeAll()
        candlesticks.removeAll()
        marketContexts.removeAll()
        marketTrades.removeAll()
        accountOverview = nil
        positions.removeAll()
        openOrders.removeAll()
        orderHistory.removeAll()
        tradeHistory.removeAll()
        fundingHistory.removeAll()
        fundHistory.removeAll()
        subaccounts.removeAll()
        delegations.removeAll()
        activeTwaps.removeAll()
        twapHistory.removeAll()
        vaults.removeAll()
        userVaults.removeAll()
        vaultPerformances.removeAll()
        leaderboard.removeAll()
        testMarketName = ""
        testSubaccountAddr = ""
    }

    /// Returns true if there was an error.
    func hasError() -> Bool {
        return lastError != nil
    }

    /// Returns the read client, initializing if necessary.
    func getReadClient() -> DecibelReadClient {
        if readClient == nil {
            if config == nil {
                config = .testnet
            }
            readClient = DecibelReadClient(config: config!, apiKey: apiKey)
        }
        return readClient!
    }
}
