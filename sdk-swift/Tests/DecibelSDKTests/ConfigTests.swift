import XCTest
@testable import DecibelSDK

final class ConfigTests: XCTestCase {
    func testMainnetConfig_AllFieldsPopulated() {
        let config = DecibelConfig.mainnet
        XCTAssertEqual(config.network, .mainnet)
        XCTAssertFalse(config.fullnodeURL.isEmpty)
        XCTAssertFalse(config.tradingHTTPURL.isEmpty)
        XCTAssertFalse(config.tradingWsURL.isEmpty)
        XCTAssertFalse(config.deployment.package_addr.isEmpty)
        XCTAssertEqual(config.compatVersion, .v0_4)
        XCTAssertEqual(config.chainID, 1)
    }

    func testTestnetConfig_NetworkIsTestnet() {
        let config = DecibelConfig.testnet
        XCTAssertEqual(config.network, .testnet)
        XCTAssertEqual(config.chainID, 2)
    }

    func testLocalConfig_UsesLocalhost() {
        let config = DecibelConfig.local
        XCTAssertEqual(config.network, .local)
        XCTAssertTrue(config.fullnodeURL.contains("localhost"))
        XCTAssertTrue(config.tradingHTTPURL.contains("localhost"))
        XCTAssertTrue(config.tradingWsURL.contains("localhost"))
    }

    func testValidConfig_ValidateSucceeds() {
        XCTAssertNoThrow(try DecibelConfig.mainnet.validate())
    }

    func testEmptyFullnodeURL_ValidateFails() {
        let config = DecibelConfig(
            network: .mainnet,
            fullnodeURL: "",
            tradingHTTPURL: "https://api.decibel.trade",
            tradingWsURL: "wss://api.decibel.trade/ws",
            deployment: Deployment(package_addr: "0x123", usdc: "0x456")
        )
        XCTAssertThrowsError(try config.validate())
    }

    func testNamedConfig_Mainnet() {
        let config = DecibelConfig.named("mainnet")
        XCTAssertNotNil(config)
        XCTAssertEqual(config?.network, .mainnet)
    }

    func testNamedConfig_Unknown() {
        let config = DecibelConfig.named("nonexistent")
        XCTAssertNil(config)
    }

    func testConfig_SerializationRoundtrip() throws {
        let config = DecibelConfig.mainnet
        let encoder = JSONEncoder()
        let data = try encoder.encode(config)
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(DecibelConfig.self, from: data)
        XCTAssertEqual(decoded.network, config.network)
        XCTAssertEqual(decoded.fullnodeURL, config.fullnodeURL)
    }
}
