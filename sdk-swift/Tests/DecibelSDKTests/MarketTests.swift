import XCTest
@testable import DecibelSDK

final class MarketTests: XCTestCase {
    let decoder = JSONDecoder()

    func testMarketPrice_Deserialization() throws {
        let json = """
        {
            "market": "ETH-USD",
            "mark_px": 3000.5,
            "mid_px": 3000.0,
            "oracle_px": 3001.0,
            "funding_rate_bps": 0.0123,
            "is_funding_positive": true,
            "open_interest": 500000.0,
            "transaction_unix_ms": 1708000000000
        }
        """.data(using: .utf8)!

        let price = try decoder.decode(MarketPrice.self, from: json)
        XCTAssertEqual(price.market, "ETH-USD")
        XCTAssertEqual(price.markPx, 3000.5)
        XCTAssertEqual(price.midPx, 3000.0)
        XCTAssertEqual(price.oraclePx, 3001.0)
        XCTAssertTrue(price.isFundingPositive)
    }

    func testMarketContext_Deserialization() throws {
        let json = """
        {
            "market": "SOL-USD",
            "volume_24h": 5000000.0,
            "open_interest": 200000.0,
            "previous_day_price": 100.0,
            "price_change_pct_24h": 5.5
        }
        """.data(using: .utf8)!

        let ctx = try decoder.decode(MarketContext.self, from: json)
        XCTAssertEqual(ctx.market, "SOL-USD")
        XCTAssertEqual(ctx.volume24h, 5000000.0)
        XCTAssertEqual(ctx.priceChangePct24h, 5.5)
    }

    func testCandlestick_Deserialization() throws {
        let json = """
        {
            "T": 1708000060000,
            "c": 45200.0,
            "h": 45300.0,
            "i": "1m",
            "l": 45100.0,
            "o": 45150.0,
            "t": 1708000000000,
            "v": 125.5
        }
        """.data(using: .utf8)!

        let candle = try decoder.decode(Candlestick.self, from: json)
        XCTAssertEqual(candle.open, 45150.0)
        XCTAssertEqual(candle.high, 45300.0)
        XCTAssertEqual(candle.low, 45100.0)
        XCTAssertEqual(candle.close, 45200.0)
        XCTAssertEqual(candle.volume, 125.5)
        XCTAssertEqual(candle.interval, "1m")
    }

    func testMarketTrade_Buy() throws {
        let json = """
        {"market": "BTC-USD", "price": 45123.0, "size": 0.5, "is_buy": true, "unix_ms": 1708000000000}
        """.data(using: .utf8)!

        let trade = try decoder.decode(MarketTrade.self, from: json)
        XCTAssertEqual(trade.market, "BTC-USD")
        XCTAssertTrue(trade.isBuy)
        XCTAssertEqual(trade.price, 45123.0)
    }

    func testMarketTrade_Sell() throws {
        let json = """
        {"market": "ETH-USD", "price": 3000.0, "size": 2.0, "is_buy": false, "unix_ms": 0}
        """.data(using: .utf8)!

        let trade = try decoder.decode(MarketTrade.self, from: json)
        XCTAssertFalse(trade.isBuy)
    }

    func testMarketOrder_Deserialization() throws {
        let json = """
        {"price": 45100.0, "size": 2.5}
        """.data(using: .utf8)!

        let order = try decoder.decode(MarketOrder.self, from: json)
        XCTAssertEqual(order.price, 45100.0)
        XCTAssertEqual(order.size, 2.5)
    }

    func testPaginatedResponse_Deserialization() throws {
        let json = """
        {
            "items": [{"rank": 1, "account": "0x1", "account_value": 100.0, "realized_pnl": 50.0, "roi": 0.5, "volume": 1000.0}],
            "total_count": 42
        }
        """.data(using: .utf8)!

        let resp = try decoder.decode(PaginatedResponse<LeaderboardItem>.self, from: json)
        XCTAssertEqual(resp.items.count, 1)
        XCTAssertEqual(resp.totalCount, 42)
    }

    func testVolumeWindow_Values() {
        XCTAssertEqual(VolumeWindow.sevenDays.rawValue, "7d")
        XCTAssertEqual(VolumeWindow.fourteenDays.rawValue, "14d")
        XCTAssertEqual(VolumeWindow.thirtyDays.rawValue, "30d")
        XCTAssertEqual(VolumeWindow.ninetyDays.rawValue, "90d")
    }

    func testSortDirection_Values() {
        XCTAssertEqual(SortDirection.ascending.rawValue, "ASC")
        XCTAssertEqual(SortDirection.descending.rawValue, "DESC")
    }

    func testTwapStatus_Values() {
        XCTAssertEqual(TwapStatus.activated.rawValue, "Activated")
        XCTAssertEqual(TwapStatus.finished.rawValue, "Finished")
        XCTAssertEqual(TwapStatus.cancelled.rawValue, "Cancelled")
    }

    func testPageParams_Default() {
        let params = PageParams()
        XCTAssertNil(params.limit)
        XCTAssertNil(params.offset)
    }

    func testPageParams_WithValues() {
        let params = PageParams(limit: 10, offset: 20)
        XCTAssertEqual(params.limit, 10)
        XCTAssertEqual(params.offset, 20)
    }
}
