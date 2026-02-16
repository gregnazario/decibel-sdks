package utils

import (
	"encoding/hex"
	"fmt"
	"math"
	"math/rand"
	"strings"

	"golang.org/x/crypto/sha3"
)

// GetMarketAddr derives a market object address from the market name and perp engine global address.
func GetMarketAddr(name string, perpEngineGlobalAddr string) string {
	addrBytes := hexToBytes(perpEngineGlobalAddr)
	seed := bcsSerializeString(name)
	objectAddr := createObjectAddress(addrBytes, seed)
	return fmt.Sprintf("0x%s", hex.EncodeToString(objectAddr[:]))
}

// GetPrimarySubaccountAddr derives the primary subaccount address for an account.
func GetPrimarySubaccountAddr(accountAddr string, compatVersion string, packageAddr string) string {
	addrBytes := hexToBytes(accountAddr)
	seed := fmt.Sprintf("%s::dex_accounts::primary_account", stripHexPrefix(packageAddr))
	objectAddr := createObjectAddress(addrBytes, []byte(seed))
	return fmt.Sprintf("0x%s", hex.EncodeToString(objectAddr[:]))
}

// GetVaultShareAddress derives a vault share token address.
func GetVaultShareAddress(vaultAddress string) string {
	addrBytes := hexToBytes(vaultAddress)
	objectAddr := createObjectAddress(addrBytes, []byte("vault_share"))
	return fmt.Sprintf("0x%s", hex.EncodeToString(objectAddr[:]))
}

// createObjectAddress computes SHA3-256(source || seed || 0xFE).
func createObjectAddress(source []byte, seed []byte) [32]byte {
	var paddedSource [32]byte
	srcLen := len(source)
	if srcLen > 32 {
		srcLen = 32
	}
	copy(paddedSource[32-srcLen:], source[:srcLen])

	hasher := sha3.New256()
	hasher.Write(paddedSource[:])
	hasher.Write(seed)
	hasher.Write([]byte{0xFE})

	var result [32]byte
	copy(result[:], hasher.Sum(nil))
	return result
}

// bcsSerializeString serializes a string with ULEB128 length prefix.
func bcsSerializeString(s string) []byte {
	bytes := []byte(s)
	var result []byte
	length := len(bytes)
	for {
		b := byte(length & 0x7f)
		length >>= 7
		if length > 0 {
			b |= 0x80
		}
		result = append(result, b)
		if length == 0 {
			break
		}
	}
	result = append(result, bytes...)
	return result
}

// hexToBytes converts a hex string (with optional 0x prefix) to bytes.
func hexToBytes(hexStr string) []byte {
	stripped := stripHexPrefix(hexStr)
	if len(stripped)%2 != 0 {
		stripped = "0" + stripped
	}
	bytes, _ := hex.DecodeString(stripped)
	return bytes
}

func stripHexPrefix(s string) string {
	return strings.TrimPrefix(s, "0x")
}

// RoundToTickSize rounds a price to the nearest valid tick size.
func RoundToTickSize(price float64, tickSize float64, pxDecimals int32, roundUp bool) float64 {
	if tickSize <= 0 {
		return price
	}
	ticks := price / tickSize
	var roundedTicks float64
	if roundUp {
		roundedTicks = math.Ceil(ticks)
	} else {
		roundedTicks = math.Floor(ticks)
	}
	return roundedTicks * tickSize
}

// GenerateRandomReplayProtectionNonce generates a random nonce for replay protection.
func GenerateRandomReplayProtectionNonce() uint64 {
	return rand.Uint64()
}

// ExtractOrderIDFromEvents extracts an order ID from transaction events.
func ExtractOrderIDFromEvents(events []map[string]interface{}, subaccountAddr string) *string {
	for _, event := range events {
		eventType, ok := event["type"].(string)
		if !ok {
			continue
		}
		if strings.Contains(eventType, "::market_types::OrderEvent") {
			data, ok := event["data"].(map[string]interface{})
			if !ok {
				continue
			}
			user, ok := data["user"].(string)
			if !ok {
				continue
			}
			if user == subaccountAddr {
				if orderID, ok := data["order_id"].(string); ok {
					return &orderID
				}
			}
		}
	}
	return nil
}

