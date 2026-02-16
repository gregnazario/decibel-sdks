use decibel_sdk::utils::*;
use decibel_sdk::models::*;

// BDD: Utility Function Tests

#[test]
fn given_market_name_and_global_addr_when_deriving_market_addr_then_returns_hex_string() {
    let addr = get_market_addr("BTC-USD", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef");
    assert!(addr.starts_with("0x"));
    assert_eq!(addr.len(), 66); // 0x + 64 hex chars
}

#[test]
fn given_same_inputs_when_deriving_market_addr_twice_then_deterministic() {
    let global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890";
    let addr1 = get_market_addr("BTC-USD", global);
    let addr2 = get_market_addr("BTC-USD", global);
    assert_eq!(addr1, addr2);
}

#[test]
fn given_different_market_names_when_deriving_addr_then_different_addresses() {
    let global = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890";
    let btc_addr = get_market_addr("BTC-USD", global);
    let eth_addr = get_market_addr("ETH-USD", global);
    assert_ne!(btc_addr, eth_addr);
}

#[test]
fn given_account_addr_when_deriving_primary_subaccount_then_returns_hex_string() {
    let addr = get_primary_subaccount_addr(
        "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "v0.4",
        "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    );
    assert!(addr.starts_with("0x"));
    assert_eq!(addr.len(), 66);
}

#[test]
fn given_same_account_when_deriving_subaccount_twice_then_deterministic() {
    let account = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
    let package = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890";
    let addr1 = get_primary_subaccount_addr(account, "v0.4", package);
    let addr2 = get_primary_subaccount_addr(account, "v0.4", package);
    assert_eq!(addr1, addr2);
}

#[test]
fn given_vault_address_when_deriving_share_addr_then_returns_hex_string() {
    let addr = get_vault_share_address(
        "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    );
    assert!(addr.starts_with("0x"));
    assert_eq!(addr.len(), 66);
}

#[test]
fn given_price_and_tick_size_when_rounding_down_then_correct() {
    assert_eq!(round_to_tick_size(45123.45, 0.5, 2, false), 45123.0);
    assert_eq!(round_to_tick_size(100.0, 10.0, 0, false), 100.0);
    assert_eq!(round_to_tick_size(105.0, 10.0, 0, false), 100.0);
}

#[test]
fn given_price_and_tick_size_when_rounding_up_then_correct() {
    assert_eq!(round_to_tick_size(45123.45, 0.5, 2, true), 45123.5);
    assert_eq!(round_to_tick_size(105.0, 10.0, 0, true), 110.0);
}

#[test]
fn given_zero_tick_size_when_rounding_then_price_unchanged() {
    assert_eq!(round_to_tick_size(45123.45, 0.0, 2, false), 45123.45);
}

#[test]
fn given_negative_tick_size_when_rounding_then_price_unchanged() {
    assert_eq!(round_to_tick_size(45123.45, -1.0, 2, false), 45123.45);
}

#[test]
fn given_nonce_generated_when_called_twice_then_different_values() {
    let n1 = generate_random_replay_protection_nonce();
    let n2 = generate_random_replay_protection_nonce();
    assert_ne!(n1, n2);
}

#[test]
fn given_events_with_order_event_when_extracting_id_then_found() {
    let events = vec![serde_json::json!({
        "type": "0x1::market_types::OrderEvent",
        "data": {
            "user": "0xsubaccount",
            "order_id": "12345"
        }
    })];

    let id = extract_order_id_from_events(&events, "0xsubaccount");
    assert_eq!(id, Some("12345".to_string()));
}

#[test]
fn given_events_without_matching_user_when_extracting_id_then_none() {
    let events = vec![serde_json::json!({
        "type": "0x1::market_types::OrderEvent",
        "data": {
            "user": "0xother",
            "order_id": "12345"
        }
    })];

    let id = extract_order_id_from_events(&events, "0xsubaccount");
    assert_eq!(id, None);
}

#[test]
fn given_empty_events_when_extracting_id_then_none() {
    let events: Vec<serde_json::Value> = vec![];
    let id = extract_order_id_from_events(&events, "0xsubaccount");
    assert_eq!(id, None);
}

#[test]
fn given_page_params_when_constructing_query_params_then_correct() {
    let page = PageParams {
        limit: Some(10),
        offset: Some(20),
    };
    let sort = SortParams::default();
    let search = SearchTermParams::default();

    let params = construct_query_params(&page, &sort, &search);
    assert!(params.iter().any(|(k, v)| k == "limit" && v == "10"));
    assert!(params.iter().any(|(k, v)| k == "offset" && v == "20"));
}

#[test]
fn given_sort_params_when_constructing_query_params_then_correct() {
    let page = PageParams::default();
    let sort = SortParams {
        sort_key: Some("volume".to_string()),
        sort_dir: Some(SortDirection::Descending),
    };
    let search = SearchTermParams::default();

    let params = construct_query_params(&page, &sort, &search);
    assert!(params.iter().any(|(k, v)| k == "sort_key" && v == "volume"));
    assert!(params.iter().any(|(k, v)| k == "sort_dir" && v == "DESC"));
}

#[test]
fn given_search_params_when_constructing_query_params_then_correct() {
    let page = PageParams::default();
    let sort = SortParams::default();
    let search = SearchTermParams {
        search_term: Some("BTC".to_string()),
    };

    let params = construct_query_params(&page, &sort, &search);
    assert!(params.iter().any(|(k, v)| k == "search_term" && v == "BTC"));
}

#[test]
fn given_no_params_when_constructing_query_params_then_empty() {
    let page = PageParams::default();
    let sort = SortParams::default();
    let search = SearchTermParams::default();

    let params = construct_query_params(&page, &sort, &search);
    assert!(params.is_empty());
}
