use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PositionSafety {
    Safe,
    Unknown,
    Stale,
    Critical,
}

#[derive(Debug, Error)]
pub enum DecibelError {
    #[error("configuration error: {message}")]
    Config { message: String },

    #[error("authentication error: {message}")]
    Authentication { message: String },

    #[error("validation error on field '{field}': {constraint}")]
    Validation {
        field: String,
        constraint: String,
        value: Option<String>,
    },

    #[error("rate limited, retry after {retry_after_ms}ms")]
    RateLimit { retry_after_ms: u64 },

    #[error("API error {status}: {message}")]
    Api { status: u16, message: String },

    #[error("simulation error: {message}")]
    Simulation { vm_status: String, message: String },

    #[error("gas error: {message}")]
    Gas { message: String },

    #[error("submission error: {message}")]
    Submission {
        tx_hash: Option<String>,
        message: String,
    },

    #[error("VM error: {vm_status}")]
    Vm {
        transaction_hash: String,
        vm_status: String,
        abort_code: Option<u64>,
    },

    #[error("WebSocket error: {message}")]
    WebSocket {
        message: String,
        disconnect_duration_ms: Option<u64>,
    },

    #[error("critical trading error: {message}")]
    CriticalTrading {
        failed_operation: String,
        affected_market: Option<String>,
        affected_order_ids: Vec<String>,
        message: String,
    },

    #[error("serialization error: {message}")]
    Serialization { message: String },

    #[error("network error: {message}")]
    Network { message: String },

    #[error("timeout: {message}")]
    Timeout { message: String },
}

impl DecibelError {
    /// Classify how this error impacts the bot's view of its positions.
    pub fn position_safety(&self) -> PositionSafety {
        match self {
            Self::Config { .. } => PositionSafety::Safe,
            Self::Authentication { .. } => PositionSafety::Safe,
            Self::Validation { .. } => PositionSafety::Safe,
            Self::RateLimit { .. } => PositionSafety::Safe,
            Self::Api { status, .. } => {
                if *status >= 500 {
                    PositionSafety::Unknown
                } else {
                    PositionSafety::Safe
                }
            }
            Self::Simulation { .. } => PositionSafety::Safe,
            Self::Gas { .. } => PositionSafety::Safe,
            Self::Submission { .. } => PositionSafety::Unknown,
            Self::Vm { .. } => PositionSafety::Unknown,
            Self::WebSocket {
                disconnect_duration_ms,
                ..
            } => match disconnect_duration_ms {
                Some(ms) if *ms > 5000 => PositionSafety::Stale,
                _ => PositionSafety::Safe,
            },
            Self::CriticalTrading { .. } => PositionSafety::Critical,
            Self::Serialization { .. } => PositionSafety::Safe,
            Self::Network { .. } => PositionSafety::Unknown,
            Self::Timeout { .. } => PositionSafety::Safe,
        }
    }

    /// Whether this error is transient and the operation can be retried.
    pub fn is_retryable(&self) -> bool {
        match self {
            Self::RateLimit { .. } => true,
            Self::Network { .. } => true,
            Self::Timeout { .. } => true,
            Self::WebSocket { .. } => true,
            Self::Api { status, .. } => *status >= 500,
            _ => false,
        }
    }

    /// Suggested delay before retry, if applicable.
    pub fn retry_after_ms(&self) -> Option<u64> {
        match self {
            Self::RateLimit { retry_after_ms } => Some(*retry_after_ms),
            _ => None,
        }
    }

    /// Whether this error represents a critical condition requiring emergency action.
    pub fn is_critical(&self) -> bool {
        matches!(self, Self::CriticalTrading { .. })
    }

    /// Whether the bot must re-sync local state from REST before continuing.
    pub fn needs_resync(&self) -> bool {
        matches!(
            self.position_safety(),
            PositionSafety::Unknown | PositionSafety::Stale | PositionSafety::Critical
        )
    }
}

pub type Result<T> = std::result::Result<T, DecibelError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn config_error_is_safe() {
        let err = DecibelError::Config {
            message: "bad config".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
        assert!(!err.is_critical());
        assert!(!err.needs_resync());
    }

    #[test]
    fn authentication_error_is_safe() {
        let err = DecibelError::Authentication {
            message: "expired".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn validation_error_is_safe() {
        let err = DecibelError::Validation {
            field: "price".into(),
            constraint: "must be positive".into(),
            value: Some("-1.0".into()),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn rate_limit_is_safe_and_retryable() {
        let err = DecibelError::RateLimit {
            retry_after_ms: 1500,
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(err.is_retryable());
        assert_eq!(err.retry_after_ms(), Some(1500));
        assert!(!err.needs_resync());
    }

    #[test]
    fn api_4xx_is_safe_not_retryable() {
        let err = DecibelError::Api {
            status: 400,
            message: "bad request".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn api_5xx_is_unknown_and_retryable() {
        let err = DecibelError::Api {
            status: 500,
            message: "internal server error".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Unknown);
        assert!(err.is_retryable());
        assert!(err.needs_resync());
    }

    #[test]
    fn api_503_is_unknown_and_retryable() {
        let err = DecibelError::Api {
            status: 503,
            message: "service unavailable".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Unknown);
        assert!(err.is_retryable());
    }

    #[test]
    fn simulation_error_is_safe() {
        let err = DecibelError::Simulation {
            vm_status: "INSUFFICIENT_BALANCE".into(),
            message: "not enough margin".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn gas_error_is_safe() {
        let err = DecibelError::Gas {
            message: "insufficient gas".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn submission_error_is_unknown() {
        let err = DecibelError::Submission {
            tx_hash: Some("0xabc".into()),
            message: "confirmation timeout".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Unknown);
        assert!(err.needs_resync());
    }

    #[test]
    fn vm_error_is_unknown() {
        let err = DecibelError::Vm {
            transaction_hash: "0xdef".into(),
            vm_status: "ORDER_NOT_FOUND".into(),
            abort_code: Some(42),
        };
        assert_eq!(err.position_safety(), PositionSafety::Unknown);
        assert!(err.needs_resync());
    }

    #[test]
    fn websocket_short_disconnect_is_safe() {
        let err = DecibelError::WebSocket {
            message: "brief disconnect".into(),
            disconnect_duration_ms: Some(3000),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(err.is_retryable());
        assert!(!err.needs_resync());
    }

    #[test]
    fn websocket_exactly_5000ms_is_safe() {
        let err = DecibelError::WebSocket {
            message: "borderline disconnect".into(),
            disconnect_duration_ms: Some(5000),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
    }

    #[test]
    fn websocket_long_disconnect_is_stale() {
        let err = DecibelError::WebSocket {
            message: "long disconnect".into(),
            disconnect_duration_ms: Some(6000),
        };
        assert_eq!(err.position_safety(), PositionSafety::Stale);
        assert!(err.is_retryable());
        assert!(err.needs_resync());
    }

    #[test]
    fn websocket_no_duration_is_safe() {
        let err = DecibelError::WebSocket {
            message: "connection error".into(),
            disconnect_duration_ms: None,
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(err.is_retryable());
    }

    #[test]
    fn critical_trading_is_critical() {
        let err = DecibelError::CriticalTrading {
            failed_operation: "place_stop_loss".into(),
            affected_market: Some("BTC-USD".into()),
            affected_order_ids: vec!["0x1".into(), "0x2".into()],
            message: "SL placement failed".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Critical);
        assert!(err.is_critical());
        assert!(err.needs_resync());
    }

    #[test]
    fn only_critical_trading_is_critical() {
        let non_critical_errors: Vec<DecibelError> = vec![
            DecibelError::Config {
                message: "x".into(),
            },
            DecibelError::Authentication {
                message: "x".into(),
            },
            DecibelError::Validation {
                field: "x".into(),
                constraint: "x".into(),
                value: None,
            },
            DecibelError::RateLimit {
                retry_after_ms: 100,
            },
            DecibelError::Api {
                status: 500,
                message: "x".into(),
            },
            DecibelError::Simulation {
                vm_status: "x".into(),
                message: "x".into(),
            },
            DecibelError::Gas {
                message: "x".into(),
            },
            DecibelError::Submission {
                tx_hash: None,
                message: "x".into(),
            },
            DecibelError::Vm {
                transaction_hash: "x".into(),
                vm_status: "x".into(),
                abort_code: None,
            },
            DecibelError::WebSocket {
                message: "x".into(),
                disconnect_duration_ms: None,
            },
            DecibelError::Serialization {
                message: "x".into(),
            },
            DecibelError::Network {
                message: "x".into(),
            },
            DecibelError::Timeout {
                message: "x".into(),
            },
        ];
        for err in &non_critical_errors {
            assert!(
                !err.is_critical(),
                "expected is_critical()=false for {:?}",
                err
            );
        }
    }

    #[test]
    fn serialization_error_is_safe() {
        let err = DecibelError::Serialization {
            message: "invalid json".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(!err.is_retryable());
    }

    #[test]
    fn network_error_is_unknown_and_retryable() {
        let err = DecibelError::Network {
            message: "connection reset".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Unknown);
        assert!(err.is_retryable());
        assert!(err.needs_resync());
    }

    #[test]
    fn timeout_error_is_safe_and_retryable() {
        let err = DecibelError::Timeout {
            message: "request timed out".into(),
        };
        assert_eq!(err.position_safety(), PositionSafety::Safe);
        assert!(err.is_retryable());
        assert_eq!(err.retry_after_ms(), None);
    }

    #[test]
    fn needs_resync_for_unknown_and_stale() {
        let unknown_err = DecibelError::Submission {
            tx_hash: None,
            message: "timeout".into(),
        };
        assert!(unknown_err.needs_resync());

        let stale_err = DecibelError::WebSocket {
            message: "disconnect".into(),
            disconnect_duration_ms: Some(10_000),
        };
        assert!(stale_err.needs_resync());

        let safe_err = DecibelError::Config {
            message: "x".into(),
        };
        assert!(!safe_err.needs_resync());
    }

    #[test]
    fn retry_after_ms_only_for_rate_limit() {
        let rl = DecibelError::RateLimit {
            retry_after_ms: 2000,
        };
        assert_eq!(rl.retry_after_ms(), Some(2000));

        let net = DecibelError::Network {
            message: "x".into(),
        };
        assert_eq!(net.retry_after_ms(), None);

        let timeout = DecibelError::Timeout {
            message: "x".into(),
        };
        assert_eq!(timeout.retry_after_ms(), None);
    }

    #[test]
    fn display_formatting() {
        let err = DecibelError::Config {
            message: "missing key".into(),
        };
        assert_eq!(err.to_string(), "configuration error: missing key");

        let err = DecibelError::Validation {
            field: "price".into(),
            constraint: "must be > 0".into(),
            value: Some("-5".into()),
        };
        assert_eq!(
            err.to_string(),
            "validation error on field 'price': must be > 0"
        );

        let err = DecibelError::RateLimit {
            retry_after_ms: 500,
        };
        assert_eq!(err.to_string(), "rate limited, retry after 500ms");

        let err = DecibelError::Api {
            status: 404,
            message: "not found".into(),
        };
        assert_eq!(err.to_string(), "API error 404: not found");
    }

    #[test]
    fn result_type_alias_works() {
        fn ok_fn() -> Result<u64> {
            Ok(42)
        }
        fn err_fn() -> Result<u64> {
            Err(DecibelError::Config {
                message: "fail".into(),
            })
        }
        assert!(ok_fn().is_ok());
        assert!(err_fn().is_err());
    }

    #[test]
    fn position_safety_serde_roundtrip() {
        let safety = PositionSafety::Critical;
        let json = serde_json::to_string(&safety).unwrap();
        let deserialized: PositionSafety = serde_json::from_str(&json).unwrap();
        assert_eq!(safety, deserialized);
    }
}
