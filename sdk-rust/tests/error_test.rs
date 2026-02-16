use decibel_sdk::error::*;

#[test]
fn test_config_error_display() {
    let err = DecibelError::Config("bad config".into());
    assert!(err.to_string().contains("Configuration error"));
    assert!(err.to_string().contains("bad config"));
}

#[test]
fn test_api_error_display() {
    let err = DecibelError::Api {
        status: 404,
        status_text: "Not Found".into(),
        message: "resource not found".into(),
    };
    let msg = err.to_string();
    assert!(msg.contains("404"));
    assert!(msg.contains("resource not found"));
}

#[test]
fn test_transaction_error_display() {
    let err = DecibelError::Transaction {
        transaction_hash: Some("0xabc".into()),
        vm_status: Some("MOVE_ABORT".into()),
        message: "execution failed".into(),
    };
    assert!(err.to_string().contains("execution failed"));
}

#[test]
fn test_validation_error_display() {
    let err = DecibelError::Validation("invalid input".into());
    assert!(err.to_string().contains("Validation error"));
}

#[test]
fn test_simulation_error_display() {
    let err = DecibelError::Simulation("sim failed".into());
    assert!(err.to_string().contains("Simulation error"));
}

#[test]
fn test_signing_error_display() {
    let err = DecibelError::Signing("bad key".into());
    assert!(err.to_string().contains("Signing error"));
}

#[test]
fn test_gas_estimation_error_display() {
    let err = DecibelError::GasEstimation("no estimate".into());
    assert!(err.to_string().contains("Gas estimation error"));
}

#[test]
fn test_websocket_error_display() {
    let err = DecibelError::WebSocket("connection refused".into());
    assert!(err.to_string().contains("WebSocket error"));
}

#[test]
fn test_timeout_error_display() {
    let err = DecibelError::Timeout("30s elapsed".into());
    assert!(err.to_string().contains("Timeout error"));
}

#[test]
fn test_api_response_fields() {
    let resp = ApiResponse {
        data: "hello",
        status: 200,
        status_text: "OK".into(),
    };
    assert_eq!(resp.data, "hello");
    assert_eq!(resp.status, 200);
    assert_eq!(resp.status_text, "OK");
}

#[test]
fn test_api_response_clone() {
    let resp = ApiResponse {
        data: 42,
        status: 201,
        status_text: "Created".into(),
    };
    let cloned = resp.clone();
    assert_eq!(cloned.data, 42);
    assert_eq!(cloned.status, 201);
}
