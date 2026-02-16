import Foundation

public enum TimeInForce: UInt8, Codable {
    case goodTillCanceled = 0
    case postOnly = 1
    case immediateOrCancel = 2
}

public enum CandlestickInterval: String, Codable {
    case oneMinute = "1m"
    case fiveMinutes = "5m"
    case fifteenMinutes = "15m"
    case thirtyMinutes = "30m"
    case oneHour = "1h"
    case twoHours = "2h"
    case fourHours = "4h"
    case eightHours = "8h"
    case twelveHours = "12h"
    case oneDay = "1d"
    case threeDays = "3d"
    case oneWeek = "1w"
    case oneMonth = "1mo"
}

public enum VolumeWindow: String, Codable {
    case sevenDays = "7d"
    case fourteenDays = "14d"
    case thirtyDays = "30d"
    case ninetyDays = "90d"
}

public enum OrderStatusType: String {
    case acknowledged = "Acknowledged"
    case filled = "Filled"
    case cancelled = "Cancelled"
    case rejected = "Rejected"
    case unknown = "Unknown"

    public init(from string: String) {
        switch string {
        case "Acknowledged": self = .acknowledged
        case "Filled": self = .filled
        case "Cancelled", "Canceled": self = .cancelled
        case "Rejected": self = .rejected
        default: self = .unknown
        }
    }

    public var isSuccess: Bool {
        self == .acknowledged || self == .filled
    }

    public var isFailure: Bool {
        self == .cancelled || self == .rejected
    }

    public var isFinal: Bool {
        isSuccess || isFailure
    }
}

public enum SortDirection: String, Codable {
    case ascending = "ASC"
    case descending = "DESC"
}

public enum TwapStatus: String, Codable {
    case activated = "Activated"
    case finished = "Finished"
    case cancelled = "Cancelled"
}

public enum VaultType: String, Codable {
    case user
    case `protocol`
}

public enum MarketDepthAggregationSize: Int {
    case one = 1
    case two = 2
    case five = 5
    case ten = 10
    case hundred = 100
    case thousand = 1000

    public static var all: [MarketDepthAggregationSize] {
        [.one, .two, .five, .ten, .hundred, .thousand]
    }
}

public struct PageParams {
    public var limit: Int?
    public var offset: Int?

    public init(limit: Int? = nil, offset: Int? = nil) {
        self.limit = limit
        self.offset = offset
    }
}

public struct PaginatedResponse<T: Codable>: Codable {
    public let items: [T]
    public let totalCount: Int64

    enum CodingKeys: String, CodingKey {
        case items
        case totalCount = "total_count"
    }
}

public struct PlaceOrderResult {
    public let success: Bool
    public let orderID: String?
    public let transactionHash: String?
    public let error: String?

    public static func success(orderID: String?, transactionHash: String) -> PlaceOrderResult {
        PlaceOrderResult(success: true, orderID: orderID, transactionHash: transactionHash, error: nil)
    }

    public static func failure(error: String) -> PlaceOrderResult {
        PlaceOrderResult(success: false, orderID: nil, transactionHash: nil, error: error)
    }
}
