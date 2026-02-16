package trade.decibel.sdk.utils

import java.security.MessageDigest
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.random.Random

object AddressUtils {

    fun getMarketAddr(name: String, perpEngineGlobalAddr: String): String {
        val addrBytes = hexToBytes(perpEngineGlobalAddr)
        val seed = bcsSerializeString(name)
        val objectAddr = createObjectAddress(addrBytes, seed)
        return "0x" + objectAddr.joinToString("") { "%02x".format(it) }
    }

    fun getPrimarySubaccountAddr(accountAddr: String, compatVersion: String, packageAddr: String): String {
        val addrBytes = hexToBytes(accountAddr)
        val seedStr = "${stripHexPrefix(packageAddr)}::dex_accounts::primary_account"
        val seed = seedStr.toByteArray()
        val objectAddr = createObjectAddress(addrBytes, seed)
        return "0x" + objectAddr.joinToString("") { "%02x".format(it) }
    }

    fun getVaultShareAddress(vaultAddress: String): String {
        val addrBytes = hexToBytes(vaultAddress)
        val seed = "vault_share".toByteArray()
        val objectAddr = createObjectAddress(addrBytes, seed)
        return "0x" + objectAddr.joinToString("") { "%02x".format(it) }
    }

    fun roundToTickSize(price: Double, tickSize: Double, pxDecimals: Int, roundUp: Boolean): Double {
        if (tickSize <= 0) return price
        val ticks = price / tickSize
        val roundedTicks = if (roundUp) ceil(ticks) else floor(ticks)
        return roundedTicks * tickSize
    }

    fun generateRandomReplayProtectionNonce(): ULong {
        return Random.nextLong().toULong()
    }

    private fun createObjectAddress(source: ByteArray, seed: ByteArray): ByteArray {
        val paddedSource = ByteArray(32)
        val srcLen = minOf(source.size, 32)
        System.arraycopy(source, 0, paddedSource, 32 - srcLen, srcLen)

        // Note: Using SHA-256 as placeholder. Aptos uses SHA3-256.
        val digest = MessageDigest.getInstance("SHA-256")
        digest.update(paddedSource)
        digest.update(seed)
        digest.update(byteArrayOf(0xFE.toByte()))
        return digest.digest()
    }

    private fun bcsSerializeString(s: String): ByteArray {
        val bytes = s.toByteArray()
        val result = mutableListOf<Byte>()
        var length = bytes.size
        do {
            var byte = (length and 0x7f).toByte()
            length = length shr 7
            if (length > 0) byte = (byte.toInt() or 0x80).toByte()
            result.add(byte)
        } while (length > 0)
        result.addAll(bytes.toList())
        return result.toByteArray()
    }

    private fun hexToBytes(hexStr: String): ByteArray {
        val stripped = stripHexPrefix(hexStr)
        val padded = if (stripped.length % 2 != 0) "0$stripped" else stripped
        return padded.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    }

    private fun stripHexPrefix(s: String): String {
        return if (s.startsWith("0x")) s.substring(2) else s
    }
}
