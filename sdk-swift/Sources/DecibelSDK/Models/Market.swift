import Foundation

public struct PerpMarketConfig: Codable {
    public let marketAddr: String
    public let marketName: String
    public let szDecimals: Int32
    public let pxDecimals: Int32
    public let maxLeverage: Double
    public let minSize: Double
    public let lotSize: Double
    public let tickSize: Double
    public let maxOpenInterest: Double
    public let marginCallFeePct: Double
    public let takerInNextBlock: Bool

    enum CodingKeys: String, CodingKey {
        case marketAddr = "market_addr"
        case marketName = "market_name"
        case szDecimals = "sz_decimals"
        case pxDecimals = "px_decimals"
        case maxLeverage = "max_leverage"
        case minSize = "min_size"
        case lotSize = "lot_size"
        case tickSize = "tick_size"
        case maxOpenInterest = "max_open_interest"
        case marginCallFeePct = "margin_call_fee_pct"
        case takerInNextBlock = "taker_in_next_block"
    }
}

public struct MarketDepth: Codable {
    public let market: String
    public let bids: [MarketOrder]
    public let asks: [MarketOrder]
    public let unixMs: Int64

    enum CodingKeys: String, CodingKey {
        case market, bids, asks
        case unixMs = "unix_ms"
    }
}

public struct MarketOrder: Codable {
    public let price: Double
    public let size: Double
}

public struct MarketPrice: Codable {
    public let market: String
    public let markPx: Double
    public let midPx: Double
    public let oraclePx: Double
    public let fundingRateBps: Double
    public let isFundingPositive: Bool
    public let openInterest: Double
    public let transactionUnixMs: Int64

    enum CodingKeys: String, CodingKey {
        case market
        case markPx = "mark_px"
        case midPx = "mid_px"
        case oraclePx = "oracle_px"
        case fundingRateBps = "funding_rate_bps"
        case isFundingPositive = "is_funding_positive"
        case openInterest = "open_interest"
        case transactionUnixMs = "transaction_unix_ms"
    }
}

public struct MarketContext: Codable {
    public let market: String
    public let volume24h: Double
    public let openInterest: Double
    public let previousDayPrice: Double
    public let priceChangePct24h: Double

    enum CodingKeys: String, CodingKey {
        case market
        case volume24h = "volume_24h"
        case openInterest = "open_interest"
        case previousDayPrice = "previous_day_price"
        case priceChangePct24h = "price_change_pct_24h"
    }
}

public struct Candlestick: Codable {
    public let closeTimestamp: Int64
    public let close: Double
    public let high: Double
    public let interval: String
    public let low: Double
    public let open: Double
    public let openTimestamp: Int64
    public let volume: Double

    enum CodingKeys: String, CodingKey {
        case closeTimestamp = "T"
        case close = "c"
        case high = "h"
        case interval = "i"
        case low = "l"
        case open = "o"
        case openTimestamp = "t"
        case volume = "v"
    }
}

public struct MarketTrade: Codable {
    public let market: String
    public let price: Double
    public let size: Double
    public let isBuy: Bool
    public let unixMs: Int64

    enum CodingKeys: String, CodingKey {
        case market, price, size
        case isBuy = "is_buy"
        case unixMs = "unix_ms"
    }
}
