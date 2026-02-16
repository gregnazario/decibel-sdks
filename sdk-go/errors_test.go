package decibel

import (
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDecibelError_Error(t *testing.T) {
	err := NewError(ErrConfig, "bad config", nil)
	assert.Contains(t, err.Error(), "config error")
	assert.Contains(t, err.Error(), "bad config")
}

func TestDecibelError_ErrorWithCause(t *testing.T) {
	cause := errors.New("underlying")
	err := NewError(ErrNetwork, "connection failed", cause)
	assert.Contains(t, err.Error(), "network error")
	assert.Contains(t, err.Error(), "underlying")
}

func TestDecibelError_Unwrap(t *testing.T) {
	cause := errors.New("root cause")
	err := NewError(ErrNetwork, "failed", cause)
	assert.Equal(t, cause, err.Unwrap())
}

func TestDecibelError_UnwrapNil(t *testing.T) {
	err := NewError(ErrConfig, "no cause", nil)
	assert.Nil(t, err.Unwrap())
}

func TestAPIError_Error(t *testing.T) {
	err := &APIError{
		Status:     404,
		StatusText: "Not Found",
		Message:    "resource not found",
	}
	assert.Contains(t, err.Error(), "404")
	assert.Contains(t, err.Error(), "Not Found")
	assert.Contains(t, err.Error(), "resource not found")
}

func TestTransactionError_Error(t *testing.T) {
	err := &TransactionError{
		TransactionHash: "0xabc",
		VMStatus:        "MOVE_ABORT",
		Message:         "execution failed",
	}
	assert.Contains(t, err.Error(), "execution failed")
	assert.Contains(t, err.Error(), "0xabc")
	assert.Contains(t, err.Error(), "MOVE_ABORT")
}

func TestNewError(t *testing.T) {
	err := NewError(ErrValidation, "invalid", nil)
	assert.Equal(t, ErrValidation, err.Kind)
	assert.Equal(t, "invalid", err.Message)
	assert.Nil(t, err.Cause)
}

func TestAllErrorKinds(t *testing.T) {
	kinds := []ErrorKind{
		ErrConfig, ErrNetwork, ErrAPI, ErrValidation,
		ErrTransaction, ErrSimulation, ErrSigning,
		ErrGasEstimation, ErrWebSocket, ErrSerialization, ErrTimeout,
	}
	for _, kind := range kinds {
		err := NewError(kind, "test", nil)
		assert.Contains(t, err.Error(), string(kind))
	}
}

func TestNamedConfig_Testnet(t *testing.T) {
	config, ok := NamedConfig("testnet")
	assert.True(t, ok)
	assert.Equal(t, NetworkTestnet, config.Network)
}

func TestNamedConfig_Local(t *testing.T) {
	config, ok := NamedConfig("local")
	assert.True(t, ok)
	assert.Equal(t, NetworkLocal, config.Network)
}

func TestValidate_EmptyWsURL(t *testing.T) {
	config := MainnetConfig()
	config.TradingWsURL = ""
	err := config.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "trading_ws_url")
}

func TestValidate_EmptyPackage(t *testing.T) {
	config := MainnetConfig()
	config.Deployment.Package = ""
	err := config.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "package")
}
