import Foundation

public enum Network: String, Codable {
    case mainnet
    case testnet
    case devnet
    case local
    case custom
}

public enum CompatVersion: String, Codable {
    case v0_4 = "v0.4"
}

public struct Deployment: Codable {
    public let package_addr: String
    public let usdc: String
    public let testc: String
    public let perpEngineGlobal: String

    enum CodingKeys: String, CodingKey {
        case package_addr = "package"
        case usdc
        case testc
        case perpEngineGlobal = "perp_engine_global"
    }

    public init(package_addr: String, usdc: String, testc: String = "", perpEngineGlobal: String = "") {
        self.package_addr = package_addr
        self.usdc = usdc
        self.testc = testc
        self.perpEngineGlobal = perpEngineGlobal
    }
}

public struct DecibelConfig: Codable {
    public let network: Network
    public let fullnodeURL: String
    public let tradingHTTPURL: String
    public let tradingWsURL: String
    public let gasStationURL: String?
    public let gasStationAPIKey: String?
    public let deployment: Deployment
    public let chainID: UInt8?
    public let compatVersion: CompatVersion

    enum CodingKeys: String, CodingKey {
        case network
        case fullnodeURL = "fullnode_url"
        case tradingHTTPURL = "trading_http_url"
        case tradingWsURL = "trading_ws_url"
        case gasStationURL = "gas_station_url"
        case gasStationAPIKey = "gas_station_api_key"
        case deployment
        case chainID = "chain_id"
        case compatVersion = "compat_version"
    }

    public init(
        network: Network,
        fullnodeURL: String,
        tradingHTTPURL: String,
        tradingWsURL: String,
        gasStationURL: String? = nil,
        gasStationAPIKey: String? = nil,
        deployment: Deployment,
        chainID: UInt8? = nil,
        compatVersion: CompatVersion = .v0_4
    ) {
        self.network = network
        self.fullnodeURL = fullnodeURL
        self.tradingHTTPURL = tradingHTTPURL
        self.tradingWsURL = tradingWsURL
        self.gasStationURL = gasStationURL
        self.gasStationAPIKey = gasStationAPIKey
        self.deployment = deployment
        self.chainID = chainID
        self.compatVersion = compatVersion
    }

    public func validate() throws {
        guard !fullnodeURL.isEmpty else {
            throw DecibelError.config("fullnode_url must not be empty")
        }
        guard !tradingHTTPURL.isEmpty else {
            throw DecibelError.config("trading_http_url must not be empty")
        }
        guard !tradingWsURL.isEmpty else {
            throw DecibelError.config("trading_ws_url must not be empty")
        }
        guard !deployment.package_addr.isEmpty else {
            throw DecibelError.config("deployment.package must not be empty")
        }
    }
}

// MARK: - Preset Configurations

public extension DecibelConfig {
    static let mainnet = DecibelConfig(
        network: .mainnet,
        fullnodeURL: "https://fullnode.mainnet.aptoslabs.com/v1",
        tradingHTTPURL: "https://api.decibel.trade",
        tradingWsURL: "wss://api.decibel.trade/ws",
        gasStationURL: "https://api.netna.aptoslabs.com/gs/v1",
        deployment: Deployment(
            package_addr: "0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d",
            usdc: "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b"
        ),
        chainID: 1
    )

    static let testnet = DecibelConfig(
        network: .testnet,
        fullnodeURL: "https://fullnode.testnet.aptoslabs.com/v1",
        tradingHTTPURL: "https://api.testnet.decibel.trade",
        tradingWsURL: "wss://api.testnet.decibel.trade/ws",
        gasStationURL: "https://api.testnet.aptoslabs.com/gs/v1",
        deployment: Deployment(package_addr: "", usdc: ""),
        chainID: 2
    )

    static let local = DecibelConfig(
        network: .local,
        fullnodeURL: "http://localhost:8080/v1",
        tradingHTTPURL: "http://localhost:3000",
        tradingWsURL: "ws://localhost:3000/ws",
        gasStationURL: "http://localhost:8081",
        deployment: Deployment(package_addr: "", usdc: ""),
        chainID: 4
    )

    static func named(_ name: String) -> DecibelConfig? {
        switch name.lowercased() {
        case "mainnet": return .mainnet
        case "testnet": return .testnet
        case "local": return .local
        default: return nil
        }
    }
}
