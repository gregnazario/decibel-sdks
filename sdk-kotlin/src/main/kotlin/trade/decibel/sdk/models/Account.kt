package trade.decibel.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class AccountOverview(
    @SerialName("perp_equity_balance") val perpEquityBalance: Double,
    @SerialName("unrealized_pnl") val unrealizedPnl: Double,
    @SerialName("unrealized_funding_cost") val unrealizedFundingCost: Double,
    @SerialName("cross_margin_ratio") val crossMarginRatio: Double,
    @SerialName("maintenance_margin") val maintenanceMargin: Double,
    @SerialName("cross_account_leverage_ratio") val crossAccountLeverageRatio: Double? = null,
    val volume: Double? = null,
    @SerialName("net_deposits") val netDeposits: Double? = null,
    @SerialName("all_time_return") val allTimeReturn: Double? = null,
    @SerialName("pnl_90d") val pnl90d: Double? = null,
    @SerialName("sharpe_ratio") val sharpeRatio: Double? = null,
    @SerialName("max_drawdown") val maxDrawdown: Double? = null,
    @SerialName("weekly_win_rate_12w") val weeklyWinRate12w: Double? = null,
    @SerialName("average_cash_position") val averageCashPosition: Double? = null,
    @SerialName("average_leverage") val averageLeverage: Double? = null,
    @SerialName("cross_account_position") val crossAccountPosition: Double,
    @SerialName("total_margin") val totalMargin: Double,
    @SerialName("usdc_cross_withdrawable_balance") val usdcCrossWithdrawableBalance: Double,
    @SerialName("usdc_isolated_withdrawable_balance") val usdcIsolatedWithdrawableBalance: Double,
    @SerialName("realized_pnl") val realizedPnl: Double? = null,
    @SerialName("liquidation_fees_paid") val liquidationFeesPaid: Double? = null,
    @SerialName("liquidation_losses") val liquidationLosses: Double? = null
)

@Serializable
data class UserSubaccount(
    @SerialName("subaccount_address") val subaccountAddress: String,
    @SerialName("primary_account_address") val primaryAccountAddress: String,
    @SerialName("is_primary") val isPrimary: Boolean,
    @SerialName("custom_label") val customLabel: String? = null,
    @SerialName("is_active") val isActive: Boolean? = null
)

@Serializable
data class Delegation(
    @SerialName("delegated_account") val delegatedAccount: String,
    @SerialName("permission_type") val permissionType: String,
    @SerialName("expiration_time_s") val expirationTimeS: Long? = null
)

@Serializable
data class LeaderboardItem(
    val rank: Long,
    val account: String,
    @SerialName("account_value") val accountValue: Double,
    @SerialName("realized_pnl") val realizedPnl: Double,
    val roi: Double,
    val volume: Double
)
