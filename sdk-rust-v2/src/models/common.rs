use serde::{Deserialize, Serialize};

use super::enums::SortDirection;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct PageParams {
    #[serde(default = "default_limit")]
    pub limit: i32,
    #[serde(default)]
    pub offset: i32,
}

fn default_limit() -> i32 {
    10
}

impl Default for PageParams {
    fn default() -> Self {
        Self {
            limit: default_limit(),
            offset: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct SortParams {
    pub sort_key: String,
    #[serde(default = "default_sort_dir")]
    pub sort_dir: SortDirection,
}

fn default_sort_dir() -> SortDirection {
    SortDirection::Descending
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct PaginatedResponse<T> {
    pub items: Vec<T>,
    pub total_count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct PlaceOrderResult {
    pub success: bool,
    pub order_id: Option<String>,
    pub transaction_hash: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct TransactionResult {
    pub success: bool,
    pub transaction_hash: String,
    pub gas_used: Option<u64>,
    pub vm_status: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    /// PageParams default values must match the API defaults so omitting
    /// them from a request produces the expected behavior.
    #[test]
    fn page_params_defaults() {
        let pp = PageParams::default();
        assert_eq!(pp.limit, 10);
        assert_eq!(pp.offset, 0);
    }

    /// Roundtrip ensures pagination parameters survive serialization
    /// for caching query state between bot restarts.
    #[test]
    fn page_params_roundtrip() {
        let pp = PageParams {
            limit: 50,
            offset: 100,
        };
        let json = serde_json::to_string(&pp).unwrap();
        let restored: PageParams = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.limit, 50);
        assert_eq!(restored.offset, 100);
    }

    /// SortParams roundtrip with default direction.
    #[test]
    fn sort_params_roundtrip() {
        let sp = SortParams {
            sort_key: "volume".into(),
            sort_dir: SortDirection::Ascending,
        };
        let json = serde_json::to_string(&sp).unwrap();
        let restored: SortParams = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.sort_key, "volume");
        assert_eq!(restored.sort_dir, SortDirection::Ascending);
    }

    /// PaginatedResponse wraps any model type — testing with strings
    /// to verify the generic plumbing.
    #[test]
    fn paginated_response_roundtrip() {
        let resp = PaginatedResponse {
            items: vec!["a".to_string(), "b".to_string()],
            total_count: 42,
        };
        let json = serde_json::to_string(&resp).unwrap();
        let restored: PaginatedResponse<String> = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.items.len(), 2);
        assert_eq!(restored.total_count, 42);
    }

    /// PlaceOrderResult must distinguish success from failure, carrying
    /// enough context for the bot to decide on retry vs. abort.
    #[test]
    fn place_order_result_success() {
        let r = PlaceOrderResult {
            success: true,
            order_id: Some("order_123".into()),
            transaction_hash: Some("0xabc".into()),
            error: None,
        };
        let json = serde_json::to_string(&r).unwrap();
        let restored: PlaceOrderResult = serde_json::from_str(&json).unwrap();
        assert!(restored.success);
        assert_eq!(restored.order_id.as_deref(), Some("order_123"));
        assert!(restored.error.is_none());
    }

    /// Failure result carries the error message for logging/alerting.
    #[test]
    fn place_order_result_failure() {
        let r = PlaceOrderResult {
            success: false,
            order_id: None,
            transaction_hash: None,
            error: Some("insufficient margin".into()),
        };
        let json = serde_json::to_string(&r).unwrap();
        let restored: PlaceOrderResult = serde_json::from_str(&json).unwrap();
        assert!(!restored.success);
        assert_eq!(restored.error.as_deref(), Some("insufficient margin"));
    }

    /// TransactionResult roundtrip with all fields populated.
    #[test]
    fn transaction_result_roundtrip() {
        let tr = TransactionResult {
            success: true,
            transaction_hash: "0xdeadbeef".into(),
            gas_used: Some(1500),
            vm_status: Some("Executed successfully".into()),
        };
        let json = serde_json::to_string(&tr).unwrap();
        let restored: TransactionResult = serde_json::from_str(&json).unwrap();
        assert!(restored.success);
        assert_eq!(restored.transaction_hash, "0xdeadbeef");
        assert_eq!(restored.gas_used, Some(1500));
    }

    /// TransactionResult with optional fields absent.
    #[test]
    fn transaction_result_minimal() {
        let json = r#"{"success":false,"transaction_hash":"0x0"}"#;
        let tr: TransactionResult = serde_json::from_str(json).unwrap();
        assert!(!tr.success);
        assert!(tr.gas_used.is_none());
        assert!(tr.vm_status.is_none());
    }
}
