package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PerpMarketConfig(
    @SerialName("market_addr") val marketAddr: String,
    @SerialName("market_name") val marketName: String,
    @SerialName("sz_decimals") val szDecimals: Int,
    @SerialName("px_decimals") val pxDecimals: Int,
    @SerialName("max_leverage") val maxLeverage: Double,
    @SerialName("min_size") val minSize: Double,
    @SerialName("lot_size") val lotSize: Double,
    @SerialName("tick_size") val tickSize: Double,
    @SerialName("max_open_interest") val maxOpenInterest: Double,
    @SerialName("margin_call_fee_pct") val marginCallFeePct: Double,
    @SerialName("taker_in_next_block") val takerInNextBlock: Boolean
)

@Serializable
data class MarketDepth(
    val market: String,
    val bids: List<MarketOrder>,
    val asks: List<MarketOrder>,
    @SerialName("unix_ms") val unixMs: Long
)

@Serializable
data class MarketOrder(
    val price: Double,
    val size: Double
)

@Serializable
data class MarketPrice(
    val market: String,
    @SerialName("mark_px") val markPx: Double,
    @SerialName("mid_px") val midPx: Double,
    @SerialName("oracle_px") val oraclePx: Double,
    @SerialName("funding_rate_bps") val fundingRateBps: Double,
    @SerialName("is_funding_positive") val isFundingPositive: Boolean,
    @SerialName("open_interest") val openInterest: Double,
    @SerialName("transaction_unix_ms") val transactionUnixMs: Long
)

@Serializable
data class MarketContext(
    val market: String,
    @SerialName("volume_24h") val volume24h: Double,
    @SerialName("open_interest") val openInterest: Double,
    @SerialName("previous_day_price") val previousDayPrice: Double,
    @SerialName("price_change_pct_24h") val priceChangePct24h: Double
)

@Serializable
data class Candlestick(
    @SerialName("T") val closeTimestamp: Long,
    val c: Double,
    val h: Double,
    val i: String,
    val l: Double,
    val o: Double,
    val t: Long,
    val v: Double
)

@Serializable
data class MarketTrade(
    val market: String,
    val price: Double,
    val size: Double,
    @SerialName("is_buy") val isBuy: Boolean,
    @SerialName("unix_ms") val unixMs: Long
)
