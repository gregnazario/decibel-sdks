import Foundation

public struct Vault: Codable {
    public let address: String
    public let name: String
    public let description: String?
    public let manager: String
    public let status: String
    public let createdAt: Int64
    public let tvl: Double?
    public let volume: Double?
    public let volume30d: Double?
    public let allTimePnl: Double?
    public let netDeposits: Double?
    public let allTimeReturn: Double?
    public let pastMonthReturn: Double?
    public let sharpeRatio: Double?
    public let maxDrawdown: Double?
    public let weeklyWinRate12w: Double?
    public let profitShare: Double?
    public let pnl90d: Double?
    public let managerCashPct: Double?
    public let averageLeverage: Double?
    public let depositors: Int64?
    public let perpEquity: Double?
    public let vaultType: VaultType?
    public let socialLinks: [String]?

    enum CodingKeys: String, CodingKey {
        case address, name, description, manager, status
        case createdAt = "created_at"
        case tvl, volume
        case volume30d = "volume_30d"
        case allTimePnl = "all_time_pnl"
        case netDeposits = "net_deposits"
        case allTimeReturn = "all_time_return"
        case pastMonthReturn = "past_month_return"
        case sharpeRatio = "sharpe_ratio"
        case maxDrawdown = "max_drawdown"
        case weeklyWinRate12w = "weekly_win_rate_12w"
        case profitShare = "profit_share"
        case pnl90d = "pnl_90d"
        case managerCashPct = "manager_cash_pct"
        case averageLeverage = "average_leverage"
        case depositors
        case perpEquity = "perp_equity"
        case vaultType = "vault_type"
        case socialLinks = "social_links"
    }
}

public struct UserOwnedVault: Codable {
    public let vaultAddress: String
    public let vaultName: String
    public let vaultShareSymbol: String
    public let status: String
    public let ageDays: Int64
    public let numManagers: Int64
    public let tvl: Double?
    public let apr: Double?
    public let managerEquity: Double?
    public let managerStake: Double?

    enum CodingKeys: String, CodingKey {
        case vaultAddress = "vault_address"
        case vaultName = "vault_name"
        case vaultShareSymbol = "vault_share_symbol"
        case status
        case ageDays = "age_days"
        case numManagers = "num_managers"
        case tvl, apr
        case managerEquity = "manager_equity"
        case managerStake = "manager_stake"
    }
}
