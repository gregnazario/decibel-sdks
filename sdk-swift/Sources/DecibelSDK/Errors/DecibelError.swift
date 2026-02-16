import Foundation

public enum DecibelError: Error, LocalizedError {
    case config(String)
    case network(Error)
    case api(status: Int, statusText: String, message: String)
    case validation(String)
    case transaction(hash: String?, vmStatus: String?, message: String)
    case simulation(String)
    case signing(String)
    case gasEstimation(String)
    case webSocket(String)
    case serialization(String)
    case timeout(String)

    public var errorDescription: String? {
        switch self {
        case .config(let msg): return "Configuration error: \(msg)"
        case .network(let err): return "Network error: \(err.localizedDescription)"
        case .api(let status, _, let msg): return "API error (status \(status)): \(msg)"
        case .validation(let msg): return "Validation error: \(msg)"
        case .transaction(_, _, let msg): return "Transaction error: \(msg)"
        case .simulation(let msg): return "Simulation error: \(msg)"
        case .signing(let msg): return "Signing error: \(msg)"
        case .gasEstimation(let msg): return "Gas estimation error: \(msg)"
        case .webSocket(let msg): return "WebSocket error: \(msg)"
        case .serialization(let msg): return "Serialization error: \(msg)"
        case .timeout(let msg): return "Timeout error: \(msg)"
        }
    }
}
