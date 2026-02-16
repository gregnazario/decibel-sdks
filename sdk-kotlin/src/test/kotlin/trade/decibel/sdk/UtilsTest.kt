package trade.decibel.sdk

import org.junit.jupiter.api.Test
import trade.decibel.sdk.utils.AddressUtils
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class UtilsTest {

    @Test
    fun `get market addr returns hex string`() {
        val addr = AddressUtils.getMarketAddr(
            "BTC-USD",
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )
        assertTrue(addr.startsWith("0x"))
        assertEquals(66, addr.length)
    }

    @Test
    fun `get market addr is deterministic`() {
        val global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        val addr1 = AddressUtils.getMarketAddr("BTC-USD", global)
        val addr2 = AddressUtils.getMarketAddr("BTC-USD", global)
        assertEquals(addr1, addr2)
    }

    @Test
    fun `different markets produce different addresses`() {
        val global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        val btcAddr = AddressUtils.getMarketAddr("BTC-USD", global)
        val ethAddr = AddressUtils.getMarketAddr("ETH-USD", global)
        assertNotEquals(btcAddr, ethAddr)
    }

    @Test
    fun `get primary subaccount addr returns hex string`() {
        val addr = AddressUtils.getPrimarySubaccountAddr(
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "v0.4",
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        assertTrue(addr.startsWith("0x"))
        assertEquals(66, addr.length)
    }

    @Test
    fun `round to tick size down`() {
        assertEquals(45123.0, AddressUtils.roundToTickSize(45123.45, 0.5, 2, false))
        assertEquals(100.0, AddressUtils.roundToTickSize(105.0, 10.0, 0, false))
    }

    @Test
    fun `round to tick size up`() {
        assertEquals(45123.5, AddressUtils.roundToTickSize(45123.45, 0.5, 2, true))
        assertEquals(110.0, AddressUtils.roundToTickSize(105.0, 10.0, 0, true))
    }

    @Test
    fun `zero tick size returns price unchanged`() {
        assertEquals(45123.45, AddressUtils.roundToTickSize(45123.45, 0.0, 2, false))
    }

    @Test
    fun `generate nonce is unique`() {
        val n1 = AddressUtils.generateRandomReplayProtectionNonce()
        val n2 = AddressUtils.generateRandomReplayProtectionNonce()
        assertNotEquals(n1, n2)
    }
}
