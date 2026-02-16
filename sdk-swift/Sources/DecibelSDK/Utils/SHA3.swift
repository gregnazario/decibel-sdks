/// Minimal SHA3-256 (Keccak) implementation for Aptos address derivation.
/// This follows the FIPS 202 specification for SHA3-256.
import Foundation

enum SHA3 {
    static func sha256(_ data: [UInt8]) -> [UInt8] {
        keccak(rate: 1088, capacity: 512, input: data, outputLength: 32, suffix: 0x06)
    }

    private static func keccak(rate: Int, capacity: Int, input: [UInt8], outputLength: Int, suffix: UInt8) -> [UInt8] {
        let rateInBytes = rate / 8
        var state = [UInt64](repeating: 0, count: 25)

        // Absorb
        var blockSize = 0
        var inputOffset = 0
        var block = [UInt8](repeating: 0, count: rateInBytes)

        for byte in input {
            block[blockSize] = byte
            blockSize += 1
            if blockSize == rateInBytes {
                xorBlock(state: &state, block: block, rateInBytes: rateInBytes)
                keccakF1600(state: &state)
                blockSize = 0
                block = [UInt8](repeating: 0, count: rateInBytes)
            }
            inputOffset += 1
        }

        // Pad
        block[blockSize] ^= suffix
        block[rateInBytes - 1] ^= 0x80
        xorBlock(state: &state, block: block, rateInBytes: rateInBytes)
        keccakF1600(state: &state)

        // Squeeze
        var output = [UInt8]()
        output.reserveCapacity(outputLength)
        var remaining = outputLength
        while remaining > 0 {
            let take = min(remaining, rateInBytes)
            for i in 0..<(take / 8) {
                var lane = state[i]
                for _ in 0..<8 {
                    if output.count < outputLength {
                        output.append(UInt8(lane & 0xFF))
                    }
                    lane >>= 8
                }
            }
            let extraBytes = take % 8
            if extraBytes > 0 {
                let laneIndex = take / 8
                var lane = state[laneIndex]
                for _ in 0..<extraBytes {
                    if output.count < outputLength {
                        output.append(UInt8(lane & 0xFF))
                    }
                    lane >>= 8
                }
            }
            remaining -= take
            if remaining > 0 {
                keccakF1600(state: &state)
            }
        }
        return Array(output.prefix(outputLength))
    }

    private static func xorBlock(state: inout [UInt64], block: [UInt8], rateInBytes: Int) {
        for i in 0..<(rateInBytes / 8) {
            var lane: UInt64 = 0
            for j in 0..<8 {
                lane |= UInt64(block[i * 8 + j]) << (j * 8)
            }
            state[i] ^= lane
        }
    }

    private static func keccakF1600(state: inout [UInt64]) {
        let roundConstants: [UInt64] = [
            0x0000000000000001, 0x0000000000008082, 0x800000000000808a, 0x8000000080008000,
            0x000000000000808b, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
            0x000000000000008a, 0x0000000000000088, 0x0000000080008009, 0x000000008000000a,
            0x000000008000808b, 0x800000000000008b, 0x8000000000008089, 0x8000000000008003,
            0x8000000000008002, 0x8000000000000080, 0x000000000000800a, 0x800000008000000a,
            0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
        ]
        let rotationOffsets: [[Int]] = [
            [ 0,  1, 62, 28, 27],
            [36, 44,  6, 55, 20],
            [ 3, 10, 43, 25, 39],
            [41, 45, 15, 21,  8],
            [18,  2, 61, 56, 14],
        ]

        for round in 0..<24 {
            // θ step
            var c = [UInt64](repeating: 0, count: 5)
            for x in 0..<5 {
                c[x] = state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
            }
            var d = [UInt64](repeating: 0, count: 5)
            for x in 0..<5 {
                d[x] = c[(x + 4) % 5] ^ rotl64(c[(x + 1) % 5], 1)
            }
            for x in 0..<5 {
                for y in 0..<5 {
                    state[x + 5 * y] ^= d[x]
                }
            }

            // ρ and π steps
            var b = [UInt64](repeating: 0, count: 25)
            for x in 0..<5 {
                for y in 0..<5 {
                    b[y + 5 * ((2 * x + 3 * y) % 5)] = rotl64(state[x + 5 * y], rotationOffsets[x][y])
                }
            }

            // χ step
            for x in 0..<5 {
                for y in 0..<5 {
                    state[x + 5 * y] = b[x + 5 * y] ^ (~b[(x + 1) % 5 + 5 * y] & b[(x + 2) % 5 + 5 * y])
                }
            }

            // ι step
            state[0] ^= roundConstants[round]
        }
    }

    private static func rotl64(_ x: UInt64, _ n: Int) -> UInt64 {
        (x << n) | (x >> (64 - n))
    }
}
