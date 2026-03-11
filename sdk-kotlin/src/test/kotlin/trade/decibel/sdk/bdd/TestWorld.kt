package trade.decibel.sdk.bdd

import trade.decibel.sdk.client.DecibelReadClient
import trade.decibel.sdk.config.DecibelConfig
import trade.decibel.sdk.models.*

/**
 * TestWorld maintains state across BDD scenario steps.
 */
class TestWorld {
    // Configuration
    var config: DecibelConfig? = null
    var apiKey: String? = System.getenv("DECIBEL_API_KEY")

    // Clients
    var readClient: DecibelReadClient? = null

    // Error state
    var lastError: Throwable? = null

    // Market data
    var markets: List<PerpMarketConfig>? = null
    var marketDepth: MarketDepth? = null
    var marketPrices: List<MarketPrice>? = null
    var candlesticks: List<Candlestick>? = null
    var marketContexts: List<MarketContext>? = null
    var marketTrades: List<MarketTrade>? = null

    // Account data
    var accountOverview: AccountOverview? = null
    var positions: List<UserPosition>? = null
    var openOrders: List<UserOpenOrder>? = null
    var orderHistory: List<UserOrderHistoryItem>? = null
    var tradeHistory: List<UserTradeHistoryItem>? = null
    var fundingHistory: List<UserFundingHistoryItem>? = null
    var fundHistory: List<UserFundHistoryItem>? = null
    var subaccounts: List<UserSubaccount>? = null
    var delegations: List<Delegation>? = null

    // TWAP data
    var activeTwaps: List<UserActiveTwap>? = null
    var twapHistory: List<UserTwapHistoryItem>? = null

    // Vault data
    var vaults: List<Vault>? = null
    var userVaults: List<Vault>? = null
    var vaultPerformances: List<VaultPerformance>? = null

    // Leaderboard
    var leaderboard: List<LeaderboardEntry>? = null

    // Test data
    var testMarketName: String = ""
    var testSubaccountAddr: String = ""

    /**
     * Resets the test world state.
     */
    fun clear() {
        config = null
        readClient = null
        lastError = null
        markets = null
        marketDepth = null
        marketPrices = null
        candlesticks = null
        marketContexts = null
        marketTrades = null
        accountOverview = null
        positions = null
        openOrders = null
        orderHistory = null
        tradeHistory = null
        fundingHistory = null
        fundHistory = null
        subaccounts = null
        delegations = null
        activeTwaps = null
        twapHistory = null
        vaults = null
        userVaults = null
        vaultPerformances = null
        leaderboard = null
        testMarketName = ""
        testSubaccountAddr = ""
    }

    /**
     * Returns true if there was an error.
     */
    fun hasError(): Boolean = lastError != null

    /**
     * Returns the read client, initializing if necessary.
     */
    fun getOrCreateReadClient(): DecibelReadClient {
        if (readClient == null) {
            if (config == null) {
                config = DecibelConfig.TESTNET
            }
            readClient = DecibelReadClient(config!!, apiKey)
        }
        return readClient!!
    }
}
