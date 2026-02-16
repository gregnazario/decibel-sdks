package trade.decibel.sdk.config

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Network {
    @SerialName("mainnet") MAINNET,
    @SerialName("testnet") TESTNET,
    @SerialName("devnet") DEVNET,
    @SerialName("local") LOCAL,
    @SerialName("custom") CUSTOM
}

@Serializable
enum class CompatVersion(val value: String) {
    @SerialName("v0.4") V0_4("v0.4")
}

@Serializable
data class Deployment(
    @SerialName("package") val packageAddr: String = "",
    val usdc: String = "",
    val testc: String = "",
    @SerialName("perp_engine_global") val perpEngineGlobal: String = ""
)

@Serializable
data class DecibelConfig(
    val network: Network,
    @SerialName("fullnode_url") val fullnodeUrl: String,
    @SerialName("trading_http_url") val tradingHttpUrl: String,
    @SerialName("trading_ws_url") val tradingWsUrl: String,
    @SerialName("gas_station_url") val gasStationUrl: String? = null,
    @SerialName("gas_station_api_key") val gasStationApiKey: String? = null,
    val deployment: Deployment,
    @SerialName("chain_id") val chainId: UByte? = null,
    @SerialName("compat_version") val compatVersion: CompatVersion = CompatVersion.V0_4
) {
    fun validate() {
        require(fullnodeUrl.isNotEmpty()) { "fullnode_url must not be empty" }
        require(tradingHttpUrl.isNotEmpty()) { "trading_http_url must not be empty" }
        require(tradingWsUrl.isNotEmpty()) { "trading_ws_url must not be empty" }
        require(deployment.packageAddr.isNotEmpty()) { "deployment.package must not be empty" }
    }

    companion object {
        val MAINNET = DecibelConfig(
            network = Network.MAINNET,
            fullnodeUrl = "https://fullnode.mainnet.aptoslabs.com/v1",
            tradingHttpUrl = "https://api.decibel.trade",
            tradingWsUrl = "wss://api.decibel.trade/ws",
            gasStationUrl = "https://api.netna.aptoslabs.com/gs/v1",
            deployment = Deployment(
                packageAddr = "0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d",
                usdc = "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b"
            ),
            chainId = 1u
        )

        val TESTNET = DecibelConfig(
            network = Network.TESTNET,
            fullnodeUrl = "https://fullnode.testnet.aptoslabs.com/v1",
            tradingHttpUrl = "https://api.testnet.decibel.trade",
            tradingWsUrl = "wss://api.testnet.decibel.trade/ws",
            gasStationUrl = "https://api.testnet.aptoslabs.com/gs/v1",
            deployment = Deployment(),
            chainId = 2u
        )

        val LOCAL = DecibelConfig(
            network = Network.LOCAL,
            fullnodeUrl = "http://localhost:8080/v1",
            tradingHttpUrl = "http://localhost:3000",
            tradingWsUrl = "ws://localhost:3000/ws",
            gasStationUrl = "http://localhost:8081",
            deployment = Deployment(),
            chainId = 4u
        )

        fun named(name: String): DecibelConfig? = when (name.lowercase()) {
            "mainnet" -> MAINNET
            "testnet" -> TESTNET
            "local" -> LOCAL
            else -> null
        }
    }
}
