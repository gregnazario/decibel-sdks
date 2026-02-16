import XCTest
@testable import DecibelSDK

final class UtilsTests: XCTestCase {
    func testGetMarketAddr_ReturnsHexString() {
        let addr = AddressUtils.getMarketAddr(
            name: "BTC-USD",
            perpEngineGlobalAddr: "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )
        XCTAssertTrue(addr.hasPrefix("0x"))
        XCTAssertEqual(addr.count, 66)
    }

    func testGetMarketAddr_Deterministic() {
        let global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        let addr1 = AddressUtils.getMarketAddr(name: "BTC-USD", perpEngineGlobalAddr: global)
        let addr2 = AddressUtils.getMarketAddr(name: "BTC-USD", perpEngineGlobalAddr: global)
        XCTAssertEqual(addr1, addr2)
    }

    func testGetMarketAddr_DifferentMarkets() {
        let global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        let btcAddr = AddressUtils.getMarketAddr(name: "BTC-USD", perpEngineGlobalAddr: global)
        let ethAddr = AddressUtils.getMarketAddr(name: "ETH-USD", perpEngineGlobalAddr: global)
        XCTAssertNotEqual(btcAddr, ethAddr)
    }

    func testRoundToTickSize_Down() {
        XCTAssertEqual(AddressUtils.roundToTickSize(price: 45123.45, tickSize: 0.5, pxDecimals: 2, roundUp: false), 45123.0)
        XCTAssertEqual(AddressUtils.roundToTickSize(price: 105.0, tickSize: 10.0, pxDecimals: 0, roundUp: false), 100.0)
    }

    func testRoundToTickSize_Up() {
        XCTAssertEqual(AddressUtils.roundToTickSize(price: 45123.45, tickSize: 0.5, pxDecimals: 2, roundUp: true), 45123.5)
        XCTAssertEqual(AddressUtils.roundToTickSize(price: 105.0, tickSize: 10.0, pxDecimals: 0, roundUp: true), 110.0)
    }

    func testRoundToTickSize_ZeroTickSize() {
        XCTAssertEqual(AddressUtils.roundToTickSize(price: 45123.45, tickSize: 0.0, pxDecimals: 2, roundUp: false), 45123.45)
    }

    func testGenerateNonce_Unique() {
        let n1 = AddressUtils.generateRandomReplayProtectionNonce()
        let n2 = AddressUtils.generateRandomReplayProtectionNonce()
        XCTAssertNotEqual(n1, n2)
    }
}
