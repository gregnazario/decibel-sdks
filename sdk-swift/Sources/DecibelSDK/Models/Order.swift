import Foundation

public struct UserOpenOrder: Codable {
    public let market: String
    public let orderID: String
    public let clientOrderID: String?
    public let price: Double
    public let origSize: Double
    public let remainingSize: Double
    public let isBuy: Bool
    public let timeInForce: String
    public let isReduceOnly: Bool
    public let status: String
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case market
        case orderID = "order_id"
        case clientOrderID = "client_order_id"
        case price
        case origSize = "orig_size"
        case remainingSize = "remaining_size"
        case isBuy = "is_buy"
        case timeInForce = "time_in_force"
        case isReduceOnly = "is_reduce_only"
        case status
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}

public struct OrderStatus: Codable {
    public let parent: String
    public let market: String
    public let orderID: String
    public let status: String
    public let origSize: Double
    public let remainingSize: Double
    public let sizeDelta: Double
    public let price: Double
    public let isBuy: Bool
    public let details: String
    public let transactionVersion: Int64
    public let unixMs: Int64

    enum CodingKeys: String, CodingKey {
        case parent, market
        case orderID = "order_id"
        case status
        case origSize = "orig_size"
        case remainingSize = "remaining_size"
        case sizeDelta = "size_delta"
        case price
        case isBuy = "is_buy"
        case details
        case transactionVersion = "transaction_version"
        case unixMs = "unix_ms"
    }
}

public struct UserActiveTwap: Codable {
    public let market: String
    public let isBuy: Bool
    public let orderID: String
    public let clientOrderID: String
    public let isReduceOnly: Bool
    public let startUnixMs: Int64
    public let frequencyS: Int64
    public let durationS: Int64
    public let origSize: Double
    public let remainingSize: Double
    public let status: String
    public let transactionUnixMs: Int64
    public let transactionVersion: Int64

    enum CodingKeys: String, CodingKey {
        case market
        case isBuy = "is_buy"
        case orderID = "order_id"
        case clientOrderID = "client_order_id"
        case isReduceOnly = "is_reduce_only"
        case startUnixMs = "start_unix_ms"
        case frequencyS = "frequency_s"
        case durationS = "duration_s"
        case origSize = "orig_size"
        case remainingSize = "remaining_size"
        case status
        case transactionUnixMs = "transaction_unix_ms"
        case transactionVersion = "transaction_version"
    }
}
