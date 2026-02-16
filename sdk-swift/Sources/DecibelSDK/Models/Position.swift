import Foundation

public struct UserPosition: Codable {
    public let market: String
    public let user: String
    public let size: Double
    public let userLeverage: Double
    public let entryPrice: Double
    public let isIsolated: Bool
    public let unrealizedFunding: Double
    public let estimatedLiquidationPrice: Double
    public let tpOrderID: String?
    public let tpTriggerPrice: Double?
    public let tpLimitPrice: Double?
    public let slOrderID: String?
    public let slTriggerPrice: Double?
    public let slLimitPrice: Double?
    public let hasFixedSizedTpsls: Bool

    enum CodingKeys: String, CodingKey {
        case market, user, size
        case userLeverage = "user_leverage"
        case entryPrice = "entry_price"
        case isIsolated = "is_isolated"
        case unrealizedFunding = "unrealized_funding"
        case estimatedLiquidationPrice = "estimated_liquidation_price"
        case tpOrderID = "tp_order_id"
        case tpTriggerPrice = "tp_trigger_price"
        case tpLimitPrice = "tp_limit_price"
        case slOrderID = "sl_order_id"
        case slTriggerPrice = "sl_trigger_price"
        case slLimitPrice = "sl_limit_price"
        case hasFixedSizedTpsls = "has_fixed_sized_tpsls"
    }
}
