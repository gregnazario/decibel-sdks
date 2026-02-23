package trade.decibel.sdk.client

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import trade.decibel.sdk.config.DecibelConfig
import trade.decibel.sdk.models.*

/**
 * DecibelReadClient provides read-only access to the Decibel API.
 */
class DecibelReadClient(
    private val config: DecibelConfig,
    private val apiKey: String? = null
) {
    private val client = HttpClient {
        expectSuccess = false
    }

    /**
     * Retrieves all market configurations.
     */
    suspend fun getAllMarkets(): List<PerpMarketConfig> {
        return client.get("${config.tradingHttpUrl}/markets") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves a specific market by name.
     */
    suspend fun getMarketByName(name: String): PerpMarketConfig {
        return client.get("${config.tradingHttpUrl}/markets/$name") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the order book for a market.
     */
    suspend fun getMarketDepth(marketName: String, limit: Int? = null): MarketDepth {
        return client.get("${config.tradingHttpUrl}/market_depth/$marketName") {
            setApiKey()
            limit?.let { parameter("limit", it) }
        }.body()
    }

    /**
     * Retrieves prices for all markets.
     */
    suspend fun getAllMarketPrices(): List<MarketPrice> {
        return client.get("${config.tradingHttpUrl}/market_prices") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the price for a specific market.
     */
    suspend fun getMarketPriceByName(name: String): List<MarketPrice> {
        return client.get("${config.tradingHttpUrl}/market_prices/$name") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves recent trades for a market.
     */
    suspend fun getMarketTrades(marketName: String, limit: Int? = null): List<MarketTrade> {
        return client.get("${config.tradingHttpUrl}/market_trades/$marketName") {
            setApiKey()
            limit?.let { parameter("limit", it) }
        }.body()
    }

    /**
     * Retrieves historical candlestick data.
     */
    suspend fun getCandlesticks(
        marketName: String,
        interval: String,
        startTime: Long? = null,
        endTime: Long? = null
    ): List<Candlestick> {
        return client.get("${config.tradingHttpUrl}/candlesticks/$marketName/$interval") {
            setApiKey()
            startTime?.let { parameter("start_time", it) }
            endTime?.let { parameter("end_time", it) }
        }.body()
    }

    /**
     * Retrieves context data for all markets.
     */
    suspend fun getAllMarketContexts(): List<MarketContext> {
        return client.get("${config.tradingHttpUrl}/market_contexts") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the account overview for a subaccount.
     */
    suspend fun getAccountOverview(subaccountAddr: String): AccountOverview {
        return client.get("${config.tradingHttpUrl}/account_overview/$subaccountAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves all positions for a subaccount.
     */
    suspend fun getUserPositions(subaccountAddr: String): List<UserPosition> {
        return client.get("${config.tradingHttpUrl}/positions/$subaccountAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves all open orders for a subaccount.
     */
    suspend fun getUserOpenOrders(subaccountAddr: String): List<UserOpenOrder> {
        return client.get("${config.tradingHttpUrl}/open_orders/$subaccountAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the order history for a subaccount.
     */
    suspend fun getUserOrderHistory(
        subaccountAddr: String,
        limit: Int? = null,
        offset: Int? = null,
        marketName: String? = null
    ): List<UserOrderHistoryItem> {
        return client.get("${config.tradingHttpUrl}/order_history/$subaccountAddr") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
            marketName?.let { parameter("market", it) }
        }.body()
    }

    /**
     * Retrieves the trade history for a subaccount.
     */
    suspend fun getUserTradeHistory(
        subaccountAddr: String,
        limit: Int? = null,
        offset: Int? = null,
        marketName: String? = null
    ): List<UserTradeHistoryItem> {
        return client.get("${config.tradingHttpUrl}/trade_history/$subaccountAddr") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
            marketName?.let { parameter("market", it) }
        }.body()
    }

    /**
     * Retrieves the funding payment history for a subaccount.
     */
    suspend fun getUserFundingHistory(
        subaccountAddr: String,
        limit: Int? = null,
        offset: Int? = null,
        marketName: String? = null
    ): List<UserFundingHistoryItem> {
        return client.get("${config.tradingHttpUrl}/funding_history/$subaccountAddr") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
            marketName?.let { parameter("market", it) }
        }.body()
    }

    /**
     * Retrieves the deposit/withdrawal history for a subaccount.
     */
    suspend fun getUserFundHistory(
        subaccountAddr: String,
        limit: Int? = null,
        offset: Int? = null
    ): List<UserFundHistoryItem> {
        return client.get("${config.tradingHttpUrl}/fund_history/$subaccountAddr") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
        }.body()
    }

    /**
     * Retrieves all subaccounts for an owner address.
     */
    suspend fun getUserSubaccounts(ownerAddr: String): List<UserSubaccount> {
        return client.get("${config.tradingHttpUrl}/subaccounts/$ownerAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves all delegations for a subaccount.
     */
    suspend fun getDelegations(subaccountAddr: String): List<Delegation> {
        return client.get("${config.tradingHttpUrl}/delegations/$subaccountAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves all active TWAP orders for a subaccount.
     */
    suspend fun getActiveTwaps(subaccountAddr: String): List<UserActiveTwap> {
        return client.get("${config.tradingHttpUrl}/active_twaps/$subaccountAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the TWAP order history for a subaccount.
     */
    suspend fun getTwapHistory(
        subaccountAddr: String,
        limit: Int? = null,
        offset: Int? = null
    ): List<UserTwapHistoryItem> {
        return client.get("${config.tradingHttpUrl}/twap_history/$subaccountAddr") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
        }.body()
    }

    /**
     * Retrieves all vaults.
     */
    suspend fun getVaults(limit: Int? = null, offset: Int? = null): List<Vault> {
        return client.get("${config.tradingHttpUrl}/vaults") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
        }.body()
    }

    /**
     * Retrieves vaults owned by a user.
     */
    suspend fun getUserOwnedVaults(ownerAddr: String): List<Vault> {
        return client.get("${config.tradingHttpUrl}/vaults/owner/$ownerAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves performance metrics for vaults the user has interacted with.
     */
    suspend fun getUserPerformancesOnVaults(userAddr: String): List<VaultPerformance> {
        return client.get("${config.tradingHttpUrl}/vaults/performance/$userAddr") {
            setApiKey()
        }.body()
    }

    /**
     * Retrieves the leaderboard.
     */
    suspend fun getLeaderboard(limit: Int? = null, offset: Int? = null): List<LeaderboardEntry> {
        return client.get("${config.tradingHttpUrl}/leaderboard") {
            setApiKey()
            limit?.let { parameter("limit", it) }
            offset?.let { parameter("offset", it) }
        }.body()
    }

    /**
     * Closes the HTTP client.
     */
    fun close() {
        client.close()
    }

    private fun HttpRequestBuilder.setApiKey() {
        apiKey?.let { header("x-api-key", it) }
        header(HttpHeaders.ContentType, ContentType.Application.Json)
    }
}
