import XCTest
@testable import DecibelSDK

final class ModelTests: XCTestCase {
    let decoder = JSONDecoder()

    func testMarketConfig_Deserialization() throws {
        let json = """
        {
            "market_addr": "0xabc123",
            "market_name": "BTC-USD",
            "sz_decimals": 8,
            "px_decimals": 2,
            "max_leverage": 50.0,
            "min_size": 0.001,
            "lot_size": 0.001,
            "tick_size": 0.1,
            "max_open_interest": 1000000.0,
            "margin_call_fee_pct": 0.5,
            "taker_in_next_block": false
        }
        """.data(using: .utf8)!

        let config = try decoder.decode(PerpMarketConfig.self, from: json)
        XCTAssertEqual(config.marketName, "BTC-USD")
        XCTAssertEqual(config.szDecimals, 8)
        XCTAssertFalse(config.takerInNextBlock)
    }

    func testMarketDepth_Deserialization() throws {
        let json = """
        {
            "market": "BTC-USD",
            "bids": [{"price": 45100.0, "size": 2.5}],
            "asks": [{"price": 45150.0, "size": 3.0}],
            "unix_ms": 1708000000000
        }
        """.data(using: .utf8)!

        let depth = try decoder.decode(MarketDepth.self, from: json)
        XCTAssertEqual(depth.market, "BTC-USD")
        XCTAssertEqual(depth.bids.count, 1)
        XCTAssertEqual(depth.bids[0].price, 45100.0)
    }

    func testAccountOverview_WithNulls() throws {
        let json = """
        {
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": 0.0,
            "unrealized_funding_cost": 0.0,
            "cross_margin_ratio": 0.0,
            "maintenance_margin": 0.0,
            "cross_account_leverage_ratio": null,
            "volume": null,
            "net_deposits": null,
            "all_time_return": null,
            "pnl_90d": null,
            "sharpe_ratio": null,
            "max_drawdown": null,
            "weekly_win_rate_12w": null,
            "average_cash_position": null,
            "average_leverage": null,
            "cross_account_position": 0.0,
            "total_margin": 0.0,
            "usdc_cross_withdrawable_balance": 0.0,
            "usdc_isolated_withdrawable_balance": 0.0,
            "realized_pnl": null,
            "liquidation_fees_paid": null,
            "liquidation_losses": null
        }
        """.data(using: .utf8)!

        let overview = try decoder.decode(AccountOverview.self, from: json)
        XCTAssertEqual(overview.perpEquityBalance, 10000.0)
        XCTAssertNil(overview.volume)
        XCTAssertNil(overview.sharpeRatio)
    }

    func testTimeInForce_Values() {
        XCTAssertEqual(TimeInForce.goodTillCanceled.rawValue, 0)
        XCTAssertEqual(TimeInForce.postOnly.rawValue, 1)
        XCTAssertEqual(TimeInForce.immediateOrCancel.rawValue, 2)
    }

    func testOrderStatusType_Success() {
        XCTAssertTrue(OrderStatusType.acknowledged.isSuccess)
        XCTAssertTrue(OrderStatusType.filled.isSuccess)
        XCTAssertFalse(OrderStatusType.cancelled.isSuccess)
    }

    func testOrderStatusType_Failure() {
        XCTAssertTrue(OrderStatusType.cancelled.isFailure)
        XCTAssertTrue(OrderStatusType.rejected.isFailure)
        XCTAssertFalse(OrderStatusType.acknowledged.isFailure)
    }

    func testOrderStatusType_Final() {
        XCTAssertTrue(OrderStatusType.filled.isFinal)
        XCTAssertTrue(OrderStatusType.cancelled.isFinal)
        XCTAssertFalse(OrderStatusType.unknown.isFinal)
    }

    func testOrderStatusType_Parse() {
        XCTAssertEqual(OrderStatusType(from: "Acknowledged"), .acknowledged)
        XCTAssertEqual(OrderStatusType(from: "Cancelled"), .cancelled)
        XCTAssertEqual(OrderStatusType(from: "Canceled"), .cancelled)
        XCTAssertEqual(OrderStatusType(from: "garbage"), .unknown)
    }

    func testPlaceOrderResult_Success() {
        let result = PlaceOrderResult.success(orderID: "123", transactionHash: "0xhash")
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.orderID, "123")
        XCTAssertEqual(result.transactionHash, "0xhash")
        XCTAssertNil(result.error)
    }

    func testPlaceOrderResult_Failure() {
        let result = PlaceOrderResult.failure(error: "Insufficient balance")
        XCTAssertFalse(result.success)
        XCTAssertNil(result.orderID)
        XCTAssertEqual(result.error, "Insufficient balance")
    }

    func testAggregationSizes() {
        XCTAssertEqual(MarketDepthAggregationSize.all.count, 6)
    }

    func testCandlestickInterval_Values() {
        XCTAssertEqual(CandlestickInterval.oneMinute.rawValue, "1m")
        XCTAssertEqual(CandlestickInterval.oneHour.rawValue, "1h")
        XCTAssertEqual(CandlestickInterval.oneDay.rawValue, "1d")
    }
}
