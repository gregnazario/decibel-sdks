import XCTest
@testable import DecibelSDK

final class OrderTests: XCTestCase {
    let decoder = JSONDecoder()

    func testUserOpenOrder_Deserialization() throws {
        let json = """
        {
            "market": "0xmarket",
            "order_id": "12345",
            "client_order_id": "my-1",
            "price": 45000.0,
            "orig_size": 1.0,
            "remaining_size": 0.5,
            "is_buy": true,
            "time_in_force": "GoodTillCanceled",
            "is_reduce_only": false,
            "status": "Acknowledged",
            "transaction_unix_ms": 1708000000000,
            "transaction_version": 100
        }
        """.data(using: .utf8)!

        let order = try decoder.decode(UserOpenOrder.self, from: json)
        XCTAssertEqual(order.orderID, "12345")
        XCTAssertEqual(order.clientOrderID, "my-1")
        XCTAssertTrue(order.isBuy)
        XCTAssertEqual(order.remainingSize, 0.5)
    }

    func testUserOpenOrder_NullClientOrderID() throws {
        let json = """
        {
            "market": "0xm", "order_id": "1", "client_order_id": null,
            "price": 100.0, "orig_size": 1.0, "remaining_size": 1.0,
            "is_buy": false, "time_in_force": "PostOnly",
            "is_reduce_only": true, "status": "Acknowledged",
            "transaction_unix_ms": 0, "transaction_version": 0
        }
        """.data(using: .utf8)!

        let order = try decoder.decode(UserOpenOrder.self, from: json)
        XCTAssertNil(order.clientOrderID)
        XCTAssertFalse(order.isBuy)
        XCTAssertTrue(order.isReduceOnly)
    }

    func testOrderStatus_Deserialization() throws {
        let json = """
        {
            "parent": "0xp", "market": "0xm", "order_id": "1",
            "status": "Filled", "orig_size": 1.0, "remaining_size": 0.0,
            "size_delta": 1.0, "price": 45000.0, "is_buy": true,
            "details": "fully filled", "transaction_version": 200, "unix_ms": 1708000000000
        }
        """.data(using: .utf8)!

        let status = try decoder.decode(OrderStatus.self, from: json)
        XCTAssertEqual(status.status, "Filled")
        XCTAssertEqual(status.remainingSize, 0.0)
    }

    func testUserActiveTwap_Deserialization() throws {
        let json = """
        {
            "market": "0xm", "is_buy": true, "order_id": "twap-1",
            "client_order_id": "c1", "is_reduce_only": false,
            "start_unix_ms": 1000, "frequency_s": 60, "duration_s": 3600,
            "orig_size": 10.0, "remaining_size": 5.0, "status": "Activated",
            "transaction_unix_ms": 1000, "transaction_version": 1
        }
        """.data(using: .utf8)!

        let twap = try decoder.decode(UserActiveTwap.self, from: json)
        XCTAssertEqual(twap.frequencyS, 60)
        XCTAssertEqual(twap.durationS, 3600)
    }
}
