package decibel

import "fmt"

// DecibelError is the base error type for all SDK errors.
type DecibelError struct {
	Kind    ErrorKind
	Message string
	Cause   error
}

// ErrorKind categorizes the type of error.
type ErrorKind string

const (
	ErrConfig        ErrorKind = "config"
	ErrNetwork       ErrorKind = "network"
	ErrAPI           ErrorKind = "api"
	ErrValidation    ErrorKind = "validation"
	ErrTransaction   ErrorKind = "transaction"
	ErrSimulation    ErrorKind = "simulation"
	ErrSigning       ErrorKind = "signing"
	ErrGasEstimation ErrorKind = "gas_estimation"
	ErrWebSocket     ErrorKind = "websocket"
	ErrSerialization ErrorKind = "serialization"
	ErrTimeout       ErrorKind = "timeout"
)

func (e *DecibelError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s error: %s: %v", e.Kind, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s error: %s", e.Kind, e.Message)
}

func (e *DecibelError) Unwrap() error { return e.Cause }

// APIError represents an error from the REST API.
type APIError struct {
	Status     int    `json:"status"`
	StatusText string `json:"status_text"`
	Message    string `json:"message"`
}

func (e *APIError) Error() string {
	return fmt.Sprintf("API error (status %d %s): %s", e.Status, e.StatusText, e.Message)
}

// TransactionError represents an on-chain transaction error.
type TransactionError struct {
	TransactionHash string `json:"transaction_hash,omitempty"`
	VMStatus        string `json:"vm_status,omitempty"`
	Message         string `json:"message"`
}

func (e *TransactionError) Error() string {
	return fmt.Sprintf("transaction error: %s (hash: %s, vm_status: %s)", e.Message, e.TransactionHash, e.VMStatus)
}

// NewError creates a new DecibelError.
func NewError(kind ErrorKind, message string, cause error) *DecibelError {
	return &DecibelError{Kind: kind, Message: message, Cause: cause}
}
