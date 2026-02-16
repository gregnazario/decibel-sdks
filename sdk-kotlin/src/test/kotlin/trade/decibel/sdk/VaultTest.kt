package trade.decibel.sdk

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Test
import trade.decibel.sdk.models.*
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class VaultTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `vault deserialization with values`() {
        val data = """
        {
            "address": "0xvault", "name": "Alpha", "description": "A vault",
            "manager": "0xmgr", "status": "Active", "created_at": 1700000000000,
            "tvl": 500000.0, "volume": 1000000.0, "volume_30d": null,
            "all_time_pnl": 50000.0, "depositors": 42,
            "vault_type": "user", "social_links": ["https://x.com"]
        }
        """.trimIndent()

        val vault = json.decodeFromString(Vault.serializer(), data)
        assertEquals("Alpha", vault.name)
        assertEquals(42, vault.depositors)
        assertEquals("user", vault.vaultType)
        assertNull(vault.volume30d)
    }

    @Test
    fun `vault deserialization all nulls`() {
        val data = """
        {
            "address": "0x", "name": "V", "description": null,
            "manager": "0xm", "status": "Pending", "created_at": 0,
            "tvl": null, "volume": null, "depositors": null, "vault_type": null
        }
        """.trimIndent()

        val vault = json.decodeFromString(Vault.serializer(), data)
        assertNull(vault.description)
        assertNull(vault.tvl)
        assertNull(vault.vaultType)
    }

    @Test
    fun `user owned vault deserialization`() {
        val data = """
        {
            "vault_address": "0xv", "vault_name": "My Vault",
            "vault_share_symbol": "MV", "status": "Active",
            "age_days": 30, "num_managers": 2,
            "tvl": 100000.0, "apr": 0.15
        }
        """.trimIndent()

        val vault = json.decodeFromString(UserOwnedVault.serializer(), data)
        assertEquals("My Vault", vault.vaultName)
        assertEquals(30, vault.ageDays)
    }

    @Test
    fun `user open order deserialization`() {
        val data = """
        {
            "market": "0xm", "order_id": "12345", "client_order_id": "my-1",
            "price": 45000.0, "orig_size": 1.0, "remaining_size": 0.5,
            "is_buy": true, "time_in_force": "GTC", "is_reduce_only": false,
            "status": "Acknowledged", "transaction_unix_ms": 0, "transaction_version": 0
        }
        """.trimIndent()

        val order = json.decodeFromString(UserOpenOrder.serializer(), data)
        assertEquals("12345", order.orderId)
        assertEquals("my-1", order.clientOrderId)
        assertEquals(0.5, order.remainingSize)
    }

    @Test
    fun `user open order null client order id`() {
        val data = """
        {
            "market": "0xm", "order_id": "1", "client_order_id": null,
            "price": 100.0, "orig_size": 1.0, "remaining_size": 1.0,
            "is_buy": false, "time_in_force": "PostOnly", "is_reduce_only": true,
            "status": "Acknowledged", "transaction_unix_ms": 0, "transaction_version": 0
        }
        """.trimIndent()

        val order = json.decodeFromString(UserOpenOrder.serializer(), data)
        assertNull(order.clientOrderId)
    }

    @Test
    fun `user position deserialization`() {
        val data = """
        {
            "market": "0xm", "user": "0xu", "size": -2.0,
            "user_leverage": 5.0, "entry_price": 3000.0,
            "is_isolated": true, "unrealized_funding": 0.0,
            "estimated_liquidation_price": 3500.0,
            "tp_order_id": null, "tp_trigger_price": null, "tp_limit_price": null,
            "sl_order_id": null, "sl_trigger_price": null, "sl_limit_price": null,
            "has_fixed_sized_tpsls": false
        }
        """.trimIndent()

        val pos = json.decodeFromString(UserPosition.serializer(), data)
        assertEquals(-2.0, pos.size)
        assertNull(pos.tpOrderId)
    }
}
