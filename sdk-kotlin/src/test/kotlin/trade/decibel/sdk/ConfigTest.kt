package trade.decibel.sdk

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertDoesNotThrow
import org.junit.jupiter.api.assertThrows
import trade.decibel.sdk.config.CompatVersion
import trade.decibel.sdk.config.DecibelConfig
import trade.decibel.sdk.config.Network
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ConfigTest {

    @Test
    fun `mainnet config has all fields populated`() {
        val config = DecibelConfig.MAINNET
        assertEquals(Network.MAINNET, config.network)
        assertTrue(config.fullnodeUrl.isNotEmpty())
        assertTrue(config.tradingHttpUrl.isNotEmpty())
        assertTrue(config.tradingWsUrl.isNotEmpty())
        assertTrue(config.deployment.packageAddr.isNotEmpty())
        assertEquals(CompatVersion.V0_4, config.compatVersion)
        assertEquals(1u.toUByte(), config.chainId)
    }

    @Test
    fun `testnet config has correct network`() {
        val config = DecibelConfig.TESTNET
        assertEquals(Network.TESTNET, config.network)
        assertEquals(2u.toUByte(), config.chainId)
    }

    @Test
    fun `local config uses localhost`() {
        val config = DecibelConfig.LOCAL
        assertEquals(Network.LOCAL, config.network)
        assertTrue(config.fullnodeUrl.contains("localhost"))
        assertTrue(config.tradingHttpUrl.contains("localhost"))
        assertTrue(config.tradingWsUrl.contains("localhost"))
    }

    @Test
    fun `valid config validates successfully`() {
        assertDoesNotThrow { DecibelConfig.MAINNET.validate() }
    }

    @Test
    fun `empty fullnode url fails validation`() {
        val config = DecibelConfig.MAINNET.copy(fullnodeUrl = "")
        assertThrows<IllegalArgumentException> { config.validate() }
    }

    @Test
    fun `empty trading http url fails validation`() {
        val config = DecibelConfig.MAINNET.copy(tradingHttpUrl = "")
        assertThrows<IllegalArgumentException> { config.validate() }
    }

    @Test
    fun `named config returns mainnet`() {
        val config = DecibelConfig.named("mainnet")
        assertNotNull(config)
        assertEquals(Network.MAINNET, config.network)
    }

    @Test
    fun `named config returns null for unknown`() {
        val config = DecibelConfig.named("nonexistent")
        assertNull(config)
    }

    @Test
    fun `config serialization roundtrip`() {
        val json = Json { ignoreUnknownKeys = true }
        val config = DecibelConfig.MAINNET
        val serialized = json.encodeToString(DecibelConfig.serializer(), config)
        val deserialized = json.decodeFromString(DecibelConfig.serializer(), serialized)
        assertEquals(config.network, deserialized.network)
        assertEquals(config.fullnodeUrl, deserialized.fullnodeUrl)
    }
}
