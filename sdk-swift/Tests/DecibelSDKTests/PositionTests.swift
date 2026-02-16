import XCTest
@testable import DecibelSDK

final class PositionTests: XCTestCase {
    let decoder = JSONDecoder()

    func testUserPosition_LongWithTpSl() throws {
        let json = """
        {
            "market": "0xmarket",
            "user": "0xuser",
            "size": 1.5,
            "user_leverage": 10.0,
            "entry_price": 45000.0,
            "is_isolated": false,
            "unrealized_funding": -5.0,
            "estimated_liquidation_price": 40000.0,
            "tp_order_id": "tp-123",
            "tp_trigger_price": 50000.0,
            "tp_limit_price": 49500.0,
            "sl_order_id": "sl-456",
            "sl_trigger_price": 42000.0,
            "sl_limit_price": 42500.0,
            "has_fixed_sized_tpsls": true
        }
        """.data(using: .utf8)!

        let pos = try decoder.decode(UserPosition.self, from: json)
        XCTAssertEqual(pos.market, "0xmarket")
        XCTAssertEqual(pos.size, 1.5)
        XCTAssertFalse(pos.isIsolated)
        XCTAssertEqual(pos.tpOrderID, "tp-123")
        XCTAssertEqual(pos.tpTriggerPrice, 50000.0)
        XCTAssertEqual(pos.slOrderID, "sl-456")
        XCTAssertTrue(pos.hasFixedSizedTpsls)
    }

    func testUserPosition_ShortNoTpSl() throws {
        let json = """
        {
            "market": "0xm",
            "user": "0xu",
            "size": -2.0,
            "user_leverage": 5.0,
            "entry_price": 3000.0,
            "is_isolated": true,
            "unrealized_funding": 0.0,
            "estimated_liquidation_price": 3500.0,
            "tp_order_id": null,
            "tp_trigger_price": null,
            "tp_limit_price": null,
            "sl_order_id": null,
            "sl_trigger_price": null,
            "sl_limit_price": null,
            "has_fixed_sized_tpsls": false
        }
        """.data(using: .utf8)!

        let pos = try decoder.decode(UserPosition.self, from: json)
        XCTAssertEqual(pos.size, -2.0)
        XCTAssertTrue(pos.isIsolated)
        XCTAssertNil(pos.tpOrderID)
        XCTAssertNil(pos.slOrderID)
        XCTAssertFalse(pos.hasFixedSizedTpsls)
    }
}
