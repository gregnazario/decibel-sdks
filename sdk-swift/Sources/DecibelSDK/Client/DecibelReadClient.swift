import Foundation

/// DecibelReadClient provides read-only access to the Decibel API.
public class DecibelReadClient {
    private let config: DecibelConfig
    private let apiKey: String?
    private let session: URLSession
    private let decoder: JSONDecoder

    /// Creates a new read client.
    public init(config: DecibelConfig, apiKey: String? = nil) {
        self.config = config
        self.apiKey = apiKey
        self.session = URLSession.shared

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder = decoder
    }

    /// Retrieves all market configurations.
    public func getAllMarkets() async throws -> [PerpMarketConfig] {
        return try await performRequest(endpoint: "/markets")
    }

    /// Retrieves a specific market by name.
    public func getMarketByName(name: String) async throws -> PerpMarketConfig {
        return try await performRequest(endpoint: "/markets/\(name)")
    }

    /// Retrieves the order book for a market.
    public func getMarketDepth(marketName: String, limit: Int? = nil) async throws -> MarketDepth {
        var endpoint = "/market_depth/\(marketName)"
        if let limit = limit {
            endpoint += "?limit=\(limit)"
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves prices for all markets.
    public func getAllMarketPrices() async throws -> [MarketPrice] {
        return try await performRequest(endpoint: "/market_prices")
    }

    /// Retrieves the price for a specific market.
    public func getMarketPriceByName(name: String) async throws -> [MarketPrice] {
        return try await performRequest(endpoint: "/market_prices/\(name)")
    }

    /// Retrieves recent trades for a market.
    public func getMarketTrades(marketName: String, limit: Int? = nil) async throws -> [MarketTrade] {
        var endpoint = "/market_trades/\(marketName)"
        if let limit = limit {
            endpoint += "?limit=\(limit)"
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves historical candlestick data.
    public func getCandlesticks(
        marketName: String,
        interval: String,
        startTime: Int64? = nil,
        endTime: Int64? = nil
    ) async throws -> [Candlestick] {
        var endpoint = "/candlesticks/\(marketName)/\(interval)"
        var queryParams = [String]()
        if let startTime = startTime {
            queryParams.append("start_time=\(startTime)")
        }
        if let endTime = endTime {
            queryParams.append("end_time=\(endTime)")
        }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves context data for all markets.
    public func getAllMarketContexts() async throws -> [MarketContext] {
        return try await performRequest(endpoint: "/market_contexts")
    }

    /// Retrieves the account overview for a subaccount.
    public func getAccountOverview(subaccountAddr: String) async throws -> AccountOverview {
        return try await performRequest(endpoint: "/account_overview/\(subaccountAddr)")
    }

    /// Retrieves all positions for a subaccount.
    public func getUserPositions(subaccountAddr: String) async throws -> [UserPosition] {
        return try await performRequest(endpoint: "/positions/\(subaccountAddr)")
    }

    /// Retrieves all open orders for a subaccount.
    public func getUserOpenOrders(subaccountAddr: String) async throws -> [UserOpenOrder] {
        return try await performRequest(endpoint: "/open_orders/\(subaccountAddr)")
    }

    /// Retrieves the order history for a subaccount.
    public func getUserOrderHistory(
        subaccountAddr: String,
        limit: Int? = nil,
        offset: Int? = nil,
        marketName: String? = nil
    ) async throws -> [UserOrderHistoryItem] {
        var endpoint = "/order_history/\(subaccountAddr)"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if let marketName = marketName { queryParams.append("market=\(marketName)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves the trade history for a subaccount.
    public func getUserTradeHistory(
        subaccountAddr: String,
        limit: Int? = nil,
        offset: Int? = nil,
        marketName: String? = nil
    ) async throws -> [UserTradeHistoryItem] {
        var endpoint = "/trade_history/\(subaccountAddr)"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if let marketName = marketName { queryParams.append("market=\(marketName)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves the funding payment history for a subaccount.
    public func getUserFundingHistory(
        subaccountAddr: String,
        limit: Int? = nil,
        offset: Int? = nil,
        marketName: String? = nil
    ) async throws -> [UserFundingHistoryItem] {
        var endpoint = "/funding_history/\(subaccountAddr)"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if let marketName = marketName { queryParams.append("market=\(marketName)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves the deposit/withdrawal history for a subaccount.
    public func getUserFundHistory(
        subaccountAddr: String,
        limit: Int? = nil,
        offset: Int? = nil
    ) async throws -> [UserFundHistoryItem] {
        var endpoint = "/fund_history/\(subaccountAddr)"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves all subaccounts for an owner address.
    public func getUserSubaccounts(ownerAddr: String) async throws -> [UserSubaccount] {
        return try await performRequest(endpoint: "/subaccounts/\(ownerAddr)")
    }

    /// Retrieves all delegations for a subaccount.
    public func getDelegations(subaccountAddr: String) async throws -> [Delegation] {
        return try await performRequest(endpoint: "/delegations/\(subaccountAddr)")
    }

    /// Retrieves all active TWAP orders for a subaccount.
    public func getActiveTwaps(subaccountAddr: String) async throws -> [UserActiveTwap] {
        return try await performRequest(endpoint: "/active_twaps/\(subaccountAddr)")
    }

    /// Retrieves the TWAP order history for a subaccount.
    public func getTwapHistory(
        subaccountAddr: String,
        limit: Int? = nil,
        offset: Int? = nil
    ) async throws -> [UserTwapHistoryItem] {
        var endpoint = "/twap_history/\(subaccountAddr)"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves all vaults.
    public func getVaults(limit: Int? = nil, offset: Int? = nil) async throws -> [Vault] {
        var endpoint = "/vaults"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    /// Retrieves vaults owned by a user.
    public func getUserOwnedVaults(ownerAddr: String) async throws -> [Vault] {
        return try await performRequest(endpoint: "/vaults/owner/\(ownerAddr)")
    }

    /// Retrieves performance metrics for vaults the user has interacted with.
    public func getUserPerformancesOnVaults(userAddr: String) async throws -> [VaultPerformance] {
        return try await performRequest(endpoint: "/vaults/performance/\(userAddr)")
    }

    /// Retrieves the leaderboard.
    public func getLeaderboard(limit: Int? = nil, offset: Int? = nil) async throws -> [LeaderboardEntry] {
        var endpoint = "/leaderboard"
        var queryParams = [String]()
        if let limit = limit { queryParams.append("limit=\(limit)") }
        if let offset = offset { queryParams.append("offset=\(offset)") }
        if !queryParams.isEmpty {
            endpoint += "?" + queryParams.joined(separator: "&")
        }
        return try await performRequest(endpoint: endpoint)
    }

    // MARK: - Private Methods

    private func performRequest<T: Decodable>(endpoint: String) async throws -> T {
        let urlString = config.tradingHttpUrl + endpoint
        guard let url = URL(string: urlString) else {
            throw DecibelError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let apiKey = apiKey {
            request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw DecibelError.invalidResponse
        }

        guard httpResponse.statusCode < 400 else {
            throw DecibelError.apiError(statusCode: httpResponse.statusCode, message: String(data: data, encoding: .utf8) ?? "Unknown error")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw DecibelError.decodingError(error)
        }
    }
}

/// DecibelError represents errors that can occur in the SDK.
public enum DecibelError: Error {
    case invalidURL
    case invalidResponse
    case apiError(statusCode: Int, message: String)
    case decodingError(Error)
}
