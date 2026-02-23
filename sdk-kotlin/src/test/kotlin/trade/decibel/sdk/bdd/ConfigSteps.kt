package trade.decibel.sdk.bdd

import io.cucumber.java8.En
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Assertions.*
import trade.decibel.sdk.config.DecibelConfig

/**
 * Step definitions for SDK configuration scenarios.
 */
class ConfigSteps(private val world: TestWorld) : En {

    init {
        Given("I have an uninitialized Decibel configuration") {
            world.config = null
            world.lastError = null
        }

        When("I create a read client using the {string} preset configuration") { preset: String ->
            world.config = when (preset) {
                "mainnet" -> DecibelConfig.MAINNET
                "testnet" -> DecibelConfig.TESTNET
                "local" -> DecibelConfig.LOCAL
                else -> throw IllegalArgumentException("Unknown preset: $preset")
            }

            try {
                world.readClient = trade.decibel.sdk.client.DecibelReadClient(world.config!!, world.apiKey)
            } catch (e: Exception) {
                world.lastError = e
            }
        }

        Then("the client should be configured for the {string} environment") { env: String ->
            assertNull(world.lastError, "Expected no error, got: ${world.lastError}")
            assertNotNull(world.readClient, "Read client should not be null")
            assertNotNull(world.config, "Config should not be null")

            val expectedNetwork = when (env) {
                "mainnet" -> trade.decibel.sdk.config.Network.MAINNET
                "testnet" -> trade.decibel.sdk.config.Network.TESTNET
                "local" -> trade.decibel.sdk.config.Network.LOCAL
                else -> throw IllegalArgumentException("Unknown environment: $env")
            }

            assertEquals(expectedNetwork, world.config!!.network, "Network should match")
        }

        Then("the client should have a valid HTTP client") {
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.readClient, "Read client should not be null")
        }

        Then("the client should use the {string} API endpoint") { endpoint: String ->
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.config, "Config should not be null")

            val expectedUrl = when (endpoint) {
                "mainnet API" -> "https://api.decibel.trade"
                "testnet API" -> "https://api.testnet.decibel.trade"
                "local API" -> "http://localhost:3000"
                else -> throw IllegalArgumentException("Unknown endpoint: $endpoint")
            }

            assertEquals(expectedUrl, world.config!!.tradingHttpUrl, "Trading HTTP URL should match")
        }

        Then("the client should have chain ID set to {int}") { expectedChainId: Int ->
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.config, "Config should not be null")
            assertNotNull(world.config!!.chainId, "Chain ID should not be null")
            assertEquals(expectedChainId, world.config!!.chainId!!.toInt(), "Chain ID should match")
        }

        Then("the client should have the correct deployment addresses") {
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.config, "Config should not be null")
            assertTrue(world.config!!.deployment.packageAddr.isNotEmpty(), "Deployment package should not be empty")
        }

        When("I request a configuration named {string}") { name: String ->
            val config = when (name.lowercase()) {
                "mainnet" -> DecibelConfig.MAINNET
                "testnet" -> DecibelConfig.TESTNET
                "local" -> DecibelConfig.LOCAL
                else -> null
            }

            if (config == null) {
                world.lastError = IllegalArgumentException("Configuration not found: $name")
            } else {
                world.config = config
            }
        }

        Then("I should receive the {string} configuration") { name: String ->
            assertNull(world.lastError, "Expected no error")
            assertNotNull(world.config, "Config should not be nil")

            val expectedNetwork = when (name) {
                "mainnet" -> trade.decibel.sdk.config.Network.MAINNET
                "testnet" -> trade.decibel.sdk.config.Network.TESTNET
                "local" -> trade.decibel.sdk.config.Network.LOCAL
                else -> throw IllegalArgumentException("Unknown config name: $name")
            }

            assertEquals(expectedNetwork, world.config!!.network, "Network should match")
        }

        Then("the configuration should be valid") {
            assertNotNull(world.config, "Config should not be null")
            world.config!!.validate() // Will throw if invalid
        }
    }
}
