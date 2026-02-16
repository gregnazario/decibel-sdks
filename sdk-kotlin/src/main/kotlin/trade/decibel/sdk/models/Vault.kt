package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Vault(
    val address: String,
    val name: String,
    val description: String? = null,
    val manager: String,
    val status: String,
    @SerialName("created_at") val createdAt: Long,
    val tvl: Double? = null,
    val volume: Double? = null,
    @SerialName("volume_30d") val volume30d: Double? = null,
    @SerialName("all_time_pnl") val allTimePnl: Double? = null,
    @SerialName("net_deposits") val netDeposits: Double? = null,
    @SerialName("all_time_return") val allTimeReturn: Double? = null,
    @SerialName("past_month_return") val pastMonthReturn: Double? = null,
    @SerialName("sharpe_ratio") val sharpeRatio: Double? = null,
    @SerialName("max_drawdown") val maxDrawdown: Double? = null,
    @SerialName("weekly_win_rate_12w") val weeklyWinRate12w: Double? = null,
    @SerialName("profit_share") val profitShare: Double? = null,
    @SerialName("pnl_90d") val pnl90d: Double? = null,
    @SerialName("manager_cash_pct") val managerCashPct: Double? = null,
    @SerialName("average_leverage") val averageLeverage: Double? = null,
    val depositors: Long? = null,
    @SerialName("perp_equity") val perpEquity: Double? = null,
    @SerialName("vault_type") val vaultType: String? = null,
    @SerialName("social_links") val socialLinks: List<String>? = null
)

@Serializable
data class UserOwnedVault(
    @SerialName("vault_address") val vaultAddress: String,
    @SerialName("vault_name") val vaultName: String,
    @SerialName("vault_share_symbol") val vaultShareSymbol: String,
    val status: String,
    @SerialName("age_days") val ageDays: Long,
    @SerialName("num_managers") val numManagers: Long,
    val tvl: Double? = null,
    val apr: Double? = null,
    @SerialName("manager_equity") val managerEquity: Double? = null,
    @SerialName("manager_stake") val managerStake: Double? = null
)

@Serializable
data class UserOpenOrder(
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
