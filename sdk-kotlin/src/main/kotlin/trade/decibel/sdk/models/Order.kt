package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserOrderHistoryItem(
    val market: String,
    @SerialName("order_id") val orderId: String,
    @SerialName("client_order_id") val clientOrderId: String? = null,
    val price: Double,
    @SerialName("orig_size") val origSize: Double,
    @SerialName("remaining_size") val remainingSize: Double,
    @SerialName("is_buy") val isBuy: Boolean,
    @SerialName("time_in_force") val timeInForce: String,
    @SerialName("is_reduce_only") val isReduceOnly: Boolean,
    val status: String,
    @SerialName("transaction_unix_ms") val transactionUnixMs: Long,
    @SerialName("transaction_version") val transactionVersion: Long
)

@Serializable
data class UserActiveTwap(
    val market: String,
    @SerialName("is_buy") val isBuy: Boolean,
    @SerialName("order_id") val orderId: String,
    @SerialName("client_order_id") val clientOrderId: String,
    @SerialName("is_reduce_only") val isReduceOnly: Boolean,
    @SerialName("start_unix_ms") val startUnixMs: Long,
    @SerialName("frequency_s") val frequencyS: Long,
    @SerialName("duration_s") val durationS: Long,
    @SerialName("orig_size") val origSize: Double,
    @SerialName("remaining_size") val remainingSize: Double,
    val status: String,
    @SerialName("transaction_unix_ms") val transactionUnixMs: Long,
    @SerialName("transaction_version") val transactionVersion: Long
)
