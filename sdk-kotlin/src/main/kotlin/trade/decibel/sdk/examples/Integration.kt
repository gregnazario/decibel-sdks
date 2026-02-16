/**
 * Integration example: list markets, check balance, place a trade, check balance again.
 *
 * Usage:
 *   export DECIBEL_PRIVATE_KEY="0x..."
 *   export DECIBEL_ACCOUNT_ADDRESS="0x..."
 *   export APTOS_NODE_API_KEY="..."          # optional
 *   ./gradlew run --args="integration"
 *
 * Or run this main function directly from your IDE.
 */
package trade.decibel.sdk.examples

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.delay
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

// ── Inline models (mirrors DecibelSDK types) ────────────────────────────

@Serializable
data class MarketInfo(
    @SerialName("market_addr") val marketAddr: String,
    @SerialName("market_name") val marketName: String,
    @SerialName("max_leverage") val maxLeverage: Double,
    @SerialName("tick_size") val tickSize: Double,
    @SerialName("lot_size") val lotSize: Double,
    @SerialName("min_size") val minSize: Double,
)

@Serializable
data class PriceInfo(
    val market: String,
    @SerialName("mark_px") val markPx: Double,
    @SerialName("mid_px") val midPx: Double,
    @SerialName("oracle_px") val oraclePx: Double,
    @SerialName("funding_rate_bps") val fundingRateBps: Double,
)

@Serializable
data class BookLevel(val price: Double, val size: Double)

@Serializable
data class DepthInfo(
    val market: String,
    val bids: List<BookLevel>,
    val asks: List<BookLevel>,
)

@Serializable
data class AccountInfo(
    @SerialName("perp_equity_balance") val perpEquityBalance: Double,
    @SerialName("total_margin") val totalMargin: Double,
    @SerialName("unrealized_pnl") val unrealizedPnl: Double,
    @SerialName("usdc_cross_withdrawable_balance") val withdrawable: Double,
)

@Serializable
data class OrderInfo(
    @SerialName("order_id") val orderId: String,
    val market: String,
    val price: Double,
    @SerialName("remaining_size") val remainingSize: Double,
    @SerialName("is_buy") val isBuy: Boolean,
)

// ── Main ────────────────────────────────────────────────────────────────

suspend fun main() {
    val baseURL = "https://api.testnet.decibel.trade/api/v1"
    val apiKey = System.getenv("APTOS_NODE_API_KEY") ?: ""
    val privateKey = System.getenv("DECIBEL_PRIVATE_KEY") ?: ""
    val accountAddr = System.getenv("DECIBEL_ACCOUNT_ADDRESS")
        ?: "0x0000000000000000000000000000000000000000000000000000000000000001"

    val json = Json { ignoreUnknownKeys = true }
    val client = HttpClient(CIO) {
        install(ContentNegotiation) { json(json) }
    }

    fun HttpRequestBuilder.auth() {
        if (apiKey.isNotEmpty()) header("x-api-key", apiKey)
    }

    try {
        // ── 1. List all available markets ───────────────────────────────
        println("=== Available Markets ===")
        val markets: List<MarketInfo> = client.get("$baseURL/markets") { auth() }.body()
        for (m in markets) {
            println("  %-12s  max_lev: %5.0fx  tick: %-8s  lot: %s".format(
                m.marketName, m.maxLeverage, m.tickSize, m.lotSize))
        }
        println("Total markets: ${markets.size}\n")

        if (markets.isEmpty()) {
            println("No markets found. Exiting.")
            return
        }

        val market = markets.first()

        // ── 2. Fetch current price ──────────────────────────────────────
        val prices: List<PriceInfo> = client.get("$baseURL/prices/${market.marketName}") { auth() }.body()
        prices.firstOrNull()?.let { p ->
            println("=== ${market.marketName} Prices ===")
            println("  mark: ${p.markPx}  mid: ${p.midPx}  oracle: ${p.oraclePx}  funding: ${p.fundingRateBps} bps\n")
        }

        // ── 3. Fetch order book depth ───────────────────────────────────
        val depth: DepthInfo = client.get("$baseURL/depth/${market.marketName}?limit=5") { auth() }.body()
        println("=== ${market.marketName} Order Book (top 5) ===")
        println("  Bids:")
        for (b in depth.bids) println("    ${b.size} @ ${b.price}")
        println("  Asks:")
        for (a in depth.asks) println("    ${a.size} @ ${a.price}")
        println()

        // ── 4. Check balance BEFORE trade ───────────────────────────────
        val subaccount = accountAddr
        try {
            val before: AccountInfo = client.get("$baseURL/account/$subaccount") { auth() }.body()
            println("=== Balance BEFORE Trade ===")
            println("  equity:       ${before.perpEquityBalance}")
            println("  margin:       ${before.totalMargin}")
            println("  unrealised:   ${before.unrealizedPnl}")
            println("  withdrawable: ${before.withdrawable}\n")
        } catch (e: Exception) {
            println("  (Could not fetch account overview: ${e.message})\n")
        }

        // ── 5. Place a trade (conceptual) ───────────────────────────────
        println("=== Placing Order (conceptual) ===")
        println("  market: ${market.marketName}  side: BUY  price: <10% below mid>  size: ${market.minSize}  tif: GTC")
        if (privateKey.isEmpty()) {
            println("  (Skipped — set DECIBEL_PRIVATE_KEY to submit on-chain)")
        } else {
            println("  → Would build + sign + submit Aptos transaction here.")
        }
        println()

        // ── 6. Check balance AFTER trade ────────────────────────────────
        delay(500)
        try {
            val after: AccountInfo = client.get("$baseURL/account/$subaccount") { auth() }.body()
            println("=== Balance AFTER Trade ===")
            println("  equity:       ${after.perpEquityBalance}")
            println("  margin:       ${after.totalMargin}")
            println("  unrealised:   ${after.unrealizedPnl}")
            println("  withdrawable: ${after.withdrawable}\n")
        } catch (_: Exception) { }

        // ── 7. Show open orders ─────────────────────────────────────────
        try {
            val orders: List<OrderInfo> = client.get("$baseURL/open-orders/$subaccount") { auth() }.body()
            println("=== Open Orders (${orders.size}) ===")
            for (o in orders) {
                val side = if (o.isBuy) "BUY" else "SELL"
                println("  ${o.orderId} $side ${o.market} @ ${o.price} (remaining: ${o.remainingSize})")
            }
        } catch (_: Exception) { }

        println("\nDone.")
    } finally {
        client.close()
    }
}
