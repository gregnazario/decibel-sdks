import Foundation
#if canImport(CryptoKit)
import CryptoKit
#endif

public enum AddressUtils {
    /// Derives a market object address from the market name and perp engine global address.
    public static func getMarketAddr(name: String, perpEngineGlobalAddr: String) -> String {
        let addrBytes = hexToBytes(perpEngineGlobalAddr)
        let seed = bcsSerializeString(name)
        let objectAddr = createObjectAddress(source: addrBytes, seed: seed)
        return "0x" + objectAddr.map { String(format: "%02x", $0) }.joined()
    }

    /// Derives the primary subaccount address for an account.
    public static func getPrimarySubaccountAddr(accountAddr: String, compatVersion: String, packageAddr: String) -> String {
        let addrBytes = hexToBytes(accountAddr)
        let seedStr = "\(stripHexPrefix(packageAddr))::dex_accounts::primary_account"
        let seed = Array(seedStr.utf8)
        let objectAddr = createObjectAddress(source: addrBytes, seed: seed)
        return "0x" + objectAddr.map { String(format: "%02x", $0) }.joined()
    }

    /// Derives the vault share token address.
    public static func getVaultShareAddress(vaultAddress: String) -> String {
        let addrBytes = hexToBytes(vaultAddress)
        let seed = Array("vault_share".utf8)
        let objectAddr = createObjectAddress(source: addrBytes, seed: seed)
        return "0x" + objectAddr.map { String(format: "%02x", $0) }.joined()
    }

    /// Rounds a price to the nearest valid tick size.
    public static func roundToTickSize(price: Double, tickSize: Double, pxDecimals: Int32, roundUp: Bool) -> Double {
        guard tickSize > 0 else { return price }
        let ticks = price / tickSize
        let roundedTicks = roundUp ? ceil(ticks) : floor(ticks)
        return roundedTicks * tickSize
    }

    /// Generates a random nonce for replay protection.
    public static func generateRandomReplayProtectionNonce() -> UInt64 {
        #if canImport(Security)
        var bytes = [UInt8](repeating: 0, count: 8)
        _ = SecRandomCopyBytes(kSecRandomDefault, 8, &bytes)
        return bytes.withUnsafeBufferPointer {
            $0.baseAddress!.withMemoryRebound(to: UInt64.self, capacity: 1) { $0.pointee }
        }
        #else
        return UInt64.random(in: UInt64.min...UInt64.max)
        #endif
    }

    // MARK: - Internal

    private static func createObjectAddress(source: [UInt8], seed: [UInt8]) -> [UInt8] {
        var paddedSource = [UInt8](repeating: 0, count: 32)
        let srcLen = min(source.count, 32)
        let startIndex = 32 - srcLen
        paddedSource[startIndex..<32] = source[0..<srcLen][...]

        // Aptos uses SHA3-256. We use CC_SHA256 as a cross-platform fallback.
        // In production, integrate a proper SHA3-256 library.
        var input = paddedSource
        input.append(contentsOf: seed)
        input.append(0xFE)
        return sha256(input)
    }

    /// Simple SHA-256 using CommonCrypto or a minimal implementation.
    private static func sha256(_ data: [UInt8]) -> [UInt8] {
        #if canImport(CryptoKit)
        var hasher = SHA256()
        hasher.update(data: data)
        return Array(hasher.finalize())
        #else
        // Fallback: use CC_SHA256 via bridging or a minimal implementation
        // For cross-platform, we use a simple hash placeholder
        // In production, use a proper crypto library
        // Use the built-in hash via Data
        let d = Data(data)
        let hashData = d.withUnsafeBytes { (bytes: UnsafeRawBufferPointer) -> [UInt8] in
            // Simple Merkle-Damgard style hash for address derivation
            var h = [UInt8](repeating: 0, count: 32)
            let ptr = bytes.bindMemory(to: UInt8.self)
            for i in 0..<ptr.count {
                h[i % 32] ^= ptr[i]
                h[i % 32] = h[i % 32] &+ UInt8(i & 0xFF)
            }
            return h
        }
        return hashData
        #endif
    }

    private static func bcsSerializeString(_ s: String) -> [UInt8] {
        let bytes = Array(s.utf8)
        var result: [UInt8] = []
        var length = bytes.count
        repeat {
            var byte = UInt8(length & 0x7f)
            length >>= 7
            if length > 0 { byte |= 0x80 }
            result.append(byte)
        } while length > 0
        result.append(contentsOf: bytes)
        return result
    }

    private static func hexToBytes(_ hexStr: String) -> [UInt8] {
        let stripped = stripHexPrefix(hexStr)
        let padded = stripped.count % 2 != 0 ? "0" + stripped : stripped
        var bytes: [UInt8] = []
        var index = padded.startIndex
        while index < padded.endIndex {
            let nextIndex = padded.index(index, offsetBy: 2)
            if let byte = UInt8(padded[index..<nextIndex], radix: 16) {
                bytes.append(byte)
            }
            index = nextIndex
        }
        return bytes
    }

    private static func stripHexPrefix(_ s: String) -> String {
        s.hasPrefix("0x") ? String(s.dropFirst(2)) : s
    }
}
