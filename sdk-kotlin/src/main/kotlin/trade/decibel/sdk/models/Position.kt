package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserPosition(
    val market: String,
    val user: String,
    val size: Double,
    @SerialName("user_leverage") val userLeverage: Double,
    @SerialName("entry_price") val entryPrice: Double,
    @SerialName("is_isolated") val isIsolated: Boolean,
    @SerialName("unrealized_funding") val unrealizedFunding: Double,
    @SerialName("estimated_liquidation_price") val estimatedLiquidationPrice: Double,
    @SerialName("tp_order_id") val tpOrderId: String? = null,
    @SerialName("tp_trigger_price") val tpTriggerPrice: Double? = null,
    @SerialName("tp_limit_price") val tpLimitPrice: Double? = null,
    @SerialName("sl_order_id") val slOrderId: String? = null,
    @SerialName("sl_trigger_price") val slTriggerPrice: Double? = null,
    @SerialName("sl_limit_price") val slLimitPrice: Double? = null,
    @SerialName("has_fixed_sized_tpsls") val hasFixedSizedTpsls: Boolean
)
