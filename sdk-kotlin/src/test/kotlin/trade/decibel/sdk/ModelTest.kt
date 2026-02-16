package trade.decibel.sdk

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Test
import trade.decibel.sdk.models.*
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ModelTest {

    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `market config deserialization`() {
        val data = """
        {
            "market_addr": "0xabc123",
            "market_name": "BTC-USD",
            "sz_decimals": 8,
            "px_decimals": 2,
            "max_leverage": 50.0,
            "min_size": 0.001,
            "lot_size": 0.001,
            "tick_size": 0.1,
            "max_open_interest": 1000000.0,
            "margin_call_fee_pct": 0.5,
            "taker_in_next_block": false
        }
        """.trimIndent()

        val config = json.decodeFromString(PerpMarketConfig.serializer(), data)
        assertEquals("BTC-USD", config.marketName)
        assertEquals(8, config.szDecimals)
        assertFalse(config.takerInNextBlock)
    }

    @Test
    fun `market depth deserialization`() {
        val data = """
        {
            "market": "BTC-USD",
            "bids": [{"price": 45100.0, "size": 2.5}],
            "asks": [{"price": 45150.0, "size": 3.0}],
            "unix_ms": 1708000000000
        }
        """.trimIndent()

        val depth = json.decodeFromString(MarketDepth.serializer(), data)
        assertEquals("BTC-USD", depth.market)
        assertEquals(1, depth.bids.size)
        assertEquals(45100.0, depth.bids[0].price)
    }

    @Test
    fun `account overview with nulls`() {
        val data = """
        {
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": 0.0,
            "unrealized_funding_cost": 0.0,
            "cross_margin_ratio": 0.0,
            "maintenance_margin": 0.0,
            "cross_account_leverage_ratio": null,
            "volume": null,
            "cross_account_position": 0.0,
            "total_margin": 0.0,
            "usdc_cross_withdrawable_balance": 0.0,
            "usdc_isolated_withdrawable_balance": 0.0
        }
        """.trimIndent()

        val overview = json.decodeFromString(AccountOverview.serializer(), data)
        assertEquals(10000.0, overview.perpEquityBalance)
        assertNull(overview.volume)
    }

    @Test
    fun `order status type success check`() {
        assertTrue(OrderStatusType.ACKNOWLEDGED.isSuccess)
        assertTrue(OrderStatusType.FILLED.isSuccess)
        assertFalse(OrderStatusType.CANCELLED.isSuccess)
    }

    @Test
    fun `order status type failure check`() {
        assertTrue(OrderStatusType.CANCELLED.isFailure)
        assertTrue(OrderStatusType.REJECTED.isFailure)
        assertFalse(OrderStatusType.ACKNOWLEDGED.isFailure)
    }

    @Test
    fun `order status type final check`() {
        assertTrue(OrderStatusType.FILLED.isFinal)
        assertTrue(OrderStatusType.CANCELLED.isFinal)
        assertFalse(OrderStatusType.UNKNOWN.isFinal)
    }

    @Test
    fun `parse order status type`() {
        assertEquals(OrderStatusType.ACKNOWLEDGED, OrderStatusType.fromString("Acknowledged"))
        assertEquals(OrderStatusType.CANCELLED, OrderStatusType.fromString("Cancelled"))
        assertEquals(OrderStatusType.CANCELLED, OrderStatusType.fromString("Canceled"))
        assertEquals(OrderStatusType.UNKNOWN, OrderStatusType.fromString("garbage"))
    }

    @Test
    fun `time in force values`() {
        assertEquals(0u.toUByte(), TimeInForce.GOOD_TILL_CANCELED.value)
        assertEquals(1u.toUByte(), TimeInForce.POST_ONLY.value)
        assertEquals(2u.toUByte(), TimeInForce.IMMEDIATE_OR_CANCEL.value)
    }

    @Test
    fun `place order result success`() {
        val result = PlaceOrderResult.success("123", "0xhash")
        assertTrue(result.success)
        assertEquals("123", result.orderId)
        assertEquals("0xhash", result.transactionHash)
        assertNull(result.error)
    }

    @Test
    fun `place order result failure`() {
        val result = PlaceOrderResult.failure("Insufficient balance")
        assertFalse(result.success)
        assertNull(result.orderId)
        assertEquals("Insufficient balance", result.error)
    }

    @Test
    fun `aggregation sizes count`() {
        assertEquals(6, MarketDepthAggregationSize.all.size)
    }

    @Test
    fun `candlestick interval values`() {
        assertEquals("1m", CandlestickInterval.ONE_MINUTE.value)
        assertEquals("1h", CandlestickInterval.ONE_HOUR.value)
        assertEquals("1d", CandlestickInterval.ONE_DAY.value)
    }
}
