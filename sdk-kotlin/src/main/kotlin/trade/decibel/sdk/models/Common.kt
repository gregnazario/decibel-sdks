package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

enum class TimeInForce(val value: UByte) {
    GOOD_TILL_CANCELED(0u),
    POST_ONLY(1u),
    IMMEDIATE_OR_CANCEL(2u);

    companion object {
        fun fromValue(value: UByte): TimeInForce? =
            entries.find { it.value == value }
    }
}

@Serializable
enum class CandlestickInterval(val value: String) {
    @SerialName("1m") ONE_MINUTE("1m"),
    @SerialName("5m") FIVE_MINUTES("5m"),
    @SerialName("15m") FIFTEEN_MINUTES("15m"),
    @SerialName("30m") THIRTY_MINUTES("30m"),
    @SerialName("1h") ONE_HOUR("1h"),
    @SerialName("2h") TWO_HOURS("2h"),
    @SerialName("4h") FOUR_HOURS("4h"),
    @SerialName("8h") EIGHT_HOURS("8h"),
    @SerialName("12h") TWELVE_HOURS("12h"),
    @SerialName("1d") ONE_DAY("1d"),
    @SerialName("3d") THREE_DAYS("3d"),
    @SerialName("1w") ONE_WEEK("1w"),
    @SerialName("1mo") ONE_MONTH("1mo")
}

@Serializable
enum class VolumeWindow(val value: String) {
    @SerialName("7d") SEVEN_DAYS("7d"),
    @SerialName("14d") FOURTEEN_DAYS("14d"),
    @SerialName("30d") THIRTY_DAYS("30d"),
    @SerialName("90d") NINETY_DAYS("90d")
}

enum class OrderStatusType(val value: String) {
    ACKNOWLEDGED("Acknowledged"),
    FILLED("Filled"),
    CANCELLED("Cancelled"),
    REJECTED("Rejected"),
    UNKNOWN("Unknown");

    val isSuccess: Boolean get() = this == ACKNOWLEDGED || this == FILLED
    val isFailure: Boolean get() = this == CANCELLED || this == REJECTED
    val isFinal: Boolean get() = isSuccess || isFailure

    companion object {
        fun fromString(s: String): OrderStatusType = when (s) {
            "Acknowledged" -> ACKNOWLEDGED
            "Filled" -> FILLED
            "Cancelled", "Canceled" -> CANCELLED
            "Rejected" -> REJECTED
            else -> UNKNOWN
        }
    }
}

@Serializable
enum class SortDirection {
    @SerialName("ASC") ASCENDING,
    @SerialName("DESC") DESCENDING
}

@Serializable
enum class TwapStatus {
    @SerialName("Activated") ACTIVATED,
    @SerialName("Finished") FINISHED,
    @SerialName("Cancelled") CANCELLED
}

@Serializable
enum class VaultType {
    @SerialName("user") USER,
    @SerialName("protocol") PROTOCOL
}

enum class MarketDepthAggregationSize(val value: Int) {
    ONE(1), TWO(2), FIVE(5), TEN(10), HUNDRED(100), THOUSAND(1000);

    companion object {
        val all = entries.toList()
    }
}

data class PageParams(
    val limit: Int? = null,
    val offset: Int? = null
)

@Serializable
data class PaginatedResponse<T>(
    val items: List<T>,
    @SerialName("total_count") val totalCount: Long
)

data class SortParams(
    val sortKey: String? = null,
    val sortDir: SortDirection? = null
)

data class SearchTermParams(
    val searchTerm: String? = null
)

data class PlaceOrderResult(
    val success: Boolean,
    val orderId: String? = null,
    val transactionHash: String? = null,
    val error: String? = null
) {
    companion object {
        fun success(orderId: String?, transactionHash: String) =
            PlaceOrderResult(success = true, orderId = orderId, transactionHash = transactionHash)

        fun failure(error: String) =
            PlaceOrderResult(success = false, error = error)
    }
}
