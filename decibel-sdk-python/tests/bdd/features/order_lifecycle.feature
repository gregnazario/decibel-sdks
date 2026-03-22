Feature: Order Lifecycle Tracking
  As a trading bot using the Decibel SDK
  I need to track orders from placement through fill or cancellation
  So that I always know which orders are live, pending, or completed

  Background:
    Given an OrderLifecycleTracker instance
    And a PositionStateManager instance
    And subaccount "0xaaa1" is configured for market "BTC-USD"

  # --- Placement ---

  Scenario: Bot places an order and receives order_id in the result
    When the bot places a limit buy order on "BTC-USD" at price 59500.0 for size 1.0 with client_order_id "my-bot-001"
    Then the PlaceOrderResult has success True
    And the PlaceOrderResult contains an order_id like "exch-42"
    And the PlaceOrderResult contains a transaction_hash

  # --- Open orders via WebSocket ---

  Scenario: Order appears in open_orders via WebSocket update
    Given the bot placed order "exch-42" on "BTC-USD" at 59500.0 for size 1.0
    When a WebSocket open_orders update arrives with:
      | order_id | market  | price   | orig_size | remaining_size | is_buy | status       | client_order_id |
      | exch-42  | BTC-USD | 59500.0 | 1.0       | 1.0            | true   | Acknowledged | my-bot-001      |
    Then open_orders("0xaaa1") contains order "exch-42"
    And the tracker state for "exch-42" is ACKNOWLEDGED
    And the order's remaining_size is 1.0

  # --- Partial fill ---

  Scenario: Partial fill updates remaining_size
    Given order "exch-42" is acknowledged with orig_size 1.0 and remaining_size 1.0
    When a WebSocket open_orders update arrives for "exch-42" with remaining_size 0.6
    Then the open order "exch-42" has remaining_size 0.6
    And the tracker state for "exch-42" is PARTIALLY_FILLED
    And the filled quantity so far is 0.4

  # --- Full fill ---

  Scenario: Full fill removes order from open orders and triggers position update
    Given order "exch-42" has remaining_size 0.6 on "BTC-USD"
    When a WebSocket order update arrives with order_id "exch-42" status "Filled" and remaining_size 0.0
    Then open_orders("0xaaa1") does not contain "exch-42"
    And the tracker state for "exch-42" is FILLED
    And a position update for "BTC-USD" reflects the new size

  # --- Cancel ---

  Scenario: Cancel removes order from open orders
    Given order "exch-55" is acknowledged on "BTC-USD" with remaining_size 2.0
    When the bot cancels order "exch-55" on "BTC-USD"
    And a WebSocket order update arrives with order_id "exch-55" status "Cancelled"
    Then open_orders("0xaaa1") does not contain "exch-55"
    And the tracker state for "exch-55" is CANCELLED

  # --- client_order_id in WS and REST ---

  Scenario: client_order_id is returned in WebSocket updates and REST queries
    Given the bot placed an order with client_order_id "strategy-alpha-007"
    When a WebSocket open_orders update includes client_order_id "strategy-alpha-007" for order "exch-99"
    Then order_by_client_id("strategy-alpha-007") returns the order with order_id "exch-99"
    And get_by_client_id("strategy-alpha-007") on the tracker returns order_id "exch-99"

  # --- client_order_id lookup after restart ---

  Scenario: client_order_id lookup works after bot restart via REST fetch
    Given the bot previously placed order "exch-100" with client_order_id "session-2-order-5"
    And the bot has restarted with a fresh OrderLifecycleTracker
    When the bot fetches open orders via REST for subaccount "0xaaa1"
    And the REST response includes:
      | order_id | client_order_id     | market  | price   | remaining_size | status       |
      | exch-100 | session-2-order-5   | BTC-USD | 58000.0 | 0.5            | Acknowledged |
    Then after merging REST data, order_by_client_id("session-2-order-5") returns order "exch-100"
    And the tracker has the order in ACKNOWLEDGED state
