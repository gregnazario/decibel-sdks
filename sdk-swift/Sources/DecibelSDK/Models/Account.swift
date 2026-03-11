import Foundation

public struct AccountOverview: Codable {
    public let perpEquityBalance: Double
    public let unrealizedPnl: Double
    public let unrealizedFundingCost: Double
    public let crossMarginRatio: Double
    public let maintenanceMargin: Double
    public let crossAccountLeverageRatio: Double?
    public let volume: Double?
    public let netDeposits: Double?
    public let allTimeReturn: Double?
    public let pnl90d: Double?
    public let sharpeRatio: Double?
    public let maxDrawdown: Double?
    public let weeklyWinRate12w: Double?
    public let averageCashPosition: Double?
    public let averageLeverage: Double?
    public let crossAccountPosition: Double
    public let totalMargin: Double
    public let usdcCrossWithdrawableBalance: Double
    public let usdcIsolatedWithdrawableBalance: Double
    public let realizedPnl: Double?
    public let liquidationFeesPaid: Double?
    public let liquidationLosses: Double?

    enum CodingKeys: String, CodingKey {
        case perpEquityBalance = "perp_equity_balance"
        case unrealizedPnl = "unrealized_pnl"
        case unrealizedFundingCost = "unrealized_funding_cost"
        case crossMarginRatio = "cross_margin_ratio"
        case maintenanceMargin = "maintenance_margin"
        case crossAccountLeverageRatio = "cross_account_leverage_ratio"
        case volume
        case netDeposits = "net_deposits"
        case allTimeReturn = "all_time_return"
        case pnl90d = "pnl_90d"
        case sharpeRatio = "sharpe_ratio"
        case maxDrawdown = "max_drawdown"
        case weeklyWinRate12w = "weekly_win_rate_12w"
        case averageCashPosition = "average_cash_position"
        case averageLeverage = "average_leverage"
        case crossAccountPosition = "cross_account_position"
        case totalMargin = "total_margin"
        case usdcCrossWithdrawableBalance = "usdc_cross_withdrawable_balance"
        case usdcIsolatedWithdrawableBalance = "usdc_isolated_withdrawable_balance"
        case realizedPnl = "realized_pnl"
        case liquidationFeesPaid = "liquidation_fees_paid"
        case liquidationLosses = "liquidation_losses"
    }
}

public struct UserSubaccount: Codable {
    public let subaccountAddress: String
    public let primaryAccountAddress: String
    public let isPrimary: Bool
    public let customLabel: String?
    public let isActive: Bool?

    enum CodingKeys: String, CodingKey {
        case subaccountAddress = "subaccount_address"
        case primaryAccountAddress = "primary_account_address"
        case isPrimary = "is_primary"
        case customLabel = "custom_label"
        case isActive = "is_active"
    }
}

public struct Delegation: Codable {
    public let delegatedAccount: String
    public let permissionType: String
    public let expirationTimeS: Int64?

    enum CodingKeys: String, CodingKey {
        case delegatedAccount = "delegated_account"
        case permissionType = "permission_type"
        case expirationTimeS = "expiration_time_s"
    }
}

public struct LeaderboardItem: Codable {
    public let rank: Int64
    public let account: String
    public let accountValue: Double
    public let realizedPnl: Double
    public let roi: Double
    public let volume: Double

    enum CodingKeys: String, CodingKey {
        case rank, account
        case accountValue = "account_value"
        case realizedPnl = "realized_pnl"
        case roi, volume
    }
}

public typealias LeaderboardEntry = LeaderboardItem

public struct UserFundHistoryItem: Codable {
    public let amount: Double
    public let isDeposit: Bool
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case amount
        case isDeposit = "is_deposit"
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}

public struct UserFundingHistoryItem: Codable {
    public let market: String
    public let fundingRateBps: Double
    public let isFundingPositive: Bool
    public let fundingAmount: Double
    public let positionSize: Double
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case market
        case fundingRateBps = "funding_rate_bps"
        case isFundingPositive = "is_funding_positive"
        case fundingAmount = "funding_amount"
        case positionSize = "position_size"
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}

public struct UserTradeHistoryItem: Codable {
    public let account: String
    public let market: String
    public let action: String
    public let size: Double
    public let price: Double
    public let isProfit: Bool
    public let realizedPnlAmount: Double
    public let isFundingPositive: Bool
    public let realizedFundingAmount: Double
    public let isRebate: Bool
    public let feeAmount: Double
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case account, market, action, size, price
        case isProfit = "is_profit"
        case realizedPnlAmount = "realized_pnl_amount"
        case isFundingPositive = "is_funding_positive"
        case realizedFundingAmount = "realized_funding_amount"
        case isRebate = "is_rebate"
        case feeAmount = "fee_amount"
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}

public struct VaultPerformance: Codable {
    public let vaultAddress: String
    public let vaultName: String
    public let userDeposits: Double
    public let userShares: Double
    public let userPnl: Double
    public let userReturnValue: Double

    enum CodingKeys: String, CodingKey {
        case vaultAddress = "vault_address"
        case vaultName = "vault_name"
        case userDeposits = "user_deposits"
        case userShares = "user_shares"
        case userPnl = "user_pnl"
        case userReturnValue = "user_return_value"
    }
}

public struct UserTwapHistoryItem: Codable {
    public let market: String
    public let isBuy: Bool
    public let orderId: String
    public let clientOrderId: String
    public let isReduceOnly: Bool
    public let startUnixMs: Int64
    public let frequencyS: Int64
    public let durationS: Int64
    public let origSize: Double
    public let executedSize: Double
    public let status: String
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case market
        case isBuy = "is_buy"
        case orderId = "order_id"
        case clientOrderId = "client_order_id"
        case isReduceOnly = "is_reduce_only"
        case startUnixMs = "start_unix_ms"
        case frequencyS = "frequency_s"
        case durationS = "duration_s"
        case origSize = "orig_size"
        case executedSize = "executed_size"
        case status
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}
