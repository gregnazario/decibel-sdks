import XCTest
@testable import DecibelSDK

final class ErrorTests: XCTestCase {

    func testConfigError() {
        let error = DecibelError.config("bad config")
        XCTAssertTrue(error.errorDescription?.contains("Configuration error") ?? false)
        XCTAssertTrue(error.errorDescription?.contains("bad config") ?? false)
    }

    func testNetworkError() {
        let underlying = NSError(domain: "test", code: -1, userInfo: [NSLocalizedDescriptionKey: "timeout"])
        let error = DecibelError.network(underlying)
        XCTAssertTrue(error.errorDescription?.contains("Network error") ?? false)
    }

    func testApiError() {
        let error = DecibelError.api(status: 404, statusText: "Not Found", message: "resource missing")
        XCTAssertTrue(error.errorDescription?.contains("404") ?? false)
        XCTAssertTrue(error.errorDescription?.contains("resource missing") ?? false)
    }

    func testValidationError() {
        let error = DecibelError.validation("invalid input")
        XCTAssertTrue(error.errorDescription?.contains("Validation error") ?? false)
    }

    func testTransactionError() {
        let error = DecibelError.transaction(hash: "0xabc", vmStatus: "ABORT", message: "failed")
        XCTAssertTrue(error.errorDescription?.contains("Transaction error") ?? false)
        XCTAssertTrue(error.errorDescription?.contains("failed") ?? false)
    }

    func testSimulationError() {
        let error = DecibelError.simulation("sim failed")
        XCTAssertTrue(error.errorDescription?.contains("Simulation error") ?? false)
    }

    func testSigningError() {
        let error = DecibelError.signing("bad key")
        XCTAssertTrue(error.errorDescription?.contains("Signing error") ?? false)
    }

    func testGasEstimationError() {
        let error = DecibelError.gasEstimation("no estimate")
        XCTAssertTrue(error.errorDescription?.contains("Gas estimation error") ?? false)
    }

    func testWebSocketError() {
        let error = DecibelError.webSocket("connection refused")
        XCTAssertTrue(error.errorDescription?.contains("WebSocket error") ?? false)
    }

    func testSerializationError() {
        let error = DecibelError.serialization("parse failure")
        XCTAssertTrue(error.errorDescription?.contains("Serialization error") ?? false)
    }

    func testTimeoutError() {
        let error = DecibelError.timeout("30s elapsed")
        XCTAssertTrue(error.errorDescription?.contains("Timeout error") ?? false)
    }

    func testErrorConformsToErrorProtocol() {
        let error: Error = DecibelError.config("test")
        XCTAssertNotNil(error.localizedDescription)
    }
}
