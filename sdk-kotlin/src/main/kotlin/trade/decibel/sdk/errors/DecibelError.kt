package trade.decibel.sdk.errors

sealed class DecibelException(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class ConfigException(message: String) : DecibelException("Configuration error: $message")
    class NetworkException(message: String, cause: Throwable? = null) : DecibelException("Network error: $message", cause)
    class ApiException(val status: Int, val statusText: String, message: String) : DecibelException("API error (status $status): $message")
    class ValidationException(message: String) : DecibelException("Validation error: $message")
    class TransactionException(val txHash: String? = null, val vmStatus: String? = null, message: String) : DecibelException("Transaction error: $message")
    class SimulationException(message: String) : DecibelException("Simulation error: $message")
    class SigningException(message: String) : DecibelException("Signing error: $message")
    class GasEstimationException(message: String) : DecibelException("Gas estimation error: $message")
    class WebSocketException(message: String) : DecibelException("WebSocket error: $message")
    class SerializationException(message: String, cause: Throwable? = null) : DecibelException("Serialization error: $message", cause)
    class TimeoutException(message: String) : DecibelException("Timeout error: $message")
}
