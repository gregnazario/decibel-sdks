Feature: TWAP (Time-Weighted Average Price) Orders

  As a trader using the Decibel SDK
  I want to execute large orders using TWAP to minimize market impact
  So that I can trade sizeable amounts without significantly affecting the price

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with a funded subaccount
    And I have configured my subaccount for the "BTC-USD" market

  Scenario: Place a basic TWAP buy order
    When I place a TWAP order with:
      | market_name            | BTC-USD |
      | size                   | 1.0     |
      | is_buy                 | true    |
      | twap_frequency_seconds | 60      |
      | twap_duration_seconds  | 3600    |
    Then the TWAP order should be created
    And the total size should be 1.0 BTC
    And the order should execute every 60 seconds
    And the order should run for 3600 seconds (1 hour)
    And each execution should be approximately 0.0167 BTC

  Scenario: Place a TWAP sell order
    When I place a TWAP order with:
      | market_name            | BTC-USD |
      | size                   | 2.0     |
      | is_buy                 | false   |
      | twap_frequency_seconds | 30      |
      | twap_duration_seconds  | 1800    |
    Then the TWAP order should sell 2.0 BTC
    And the order should execute every 30 seconds
    And the order should run for 1800 seconds (30 minutes)

  Scenario: Place a reduce-only TWAP order
    Given I have an open long position of 2.0 BTC
    When I place a TWAP order with:
      | market_name            | BTC-USD    |
      | size                   | 1.0        |
      | is_buy                 | false      |
      | is_reduce_only         | true       |
      | twap_frequency_seconds | 60         |
      | twap_duration_seconds  | 3600       |
    Then the TWAP order should only reduce my existing position
    And the TWAP should not open a new short position

  Scenario: Place TWAP order with client order ID
    When I place a TWAP order with:
      | market_name            | BTC-USD       |
      | size                   | 1.0           |
      | is_buy                 | true          |
      | twap_frequency_seconds | 60            |
      | twap_duration_seconds  | 3600          |
      | client_order_id        | twap-order-1  |
    Then I should be able to reference the TWAP order by "twap-order-1"

  Scenario: Place TWAP order with builder fee
    When I place a TWAP order with:
      | market_name            | BTC-USD  |
      | size                   | 1.0      |
      | is_buy                 | true     |
      | twap_frequency_seconds | 60       |
      | twap_duration_seconds  | 3600     |
      | builder_address        | 0xfeb... |
      | builder_fees           | 10       |
    Then the specified builder should receive fees on each TWAP execution

  Scenario: Retrieve active TWAP orders
    Given I have multiple active TWAP orders
    When I request my active TWAP orders
    Then I should receive all my active TWAP orders
    And each TWAP order should include:
      | field                | description                           |
      | market               | Market address                        |
      | is_buy               | Buy or sell                           |
      | order_id             | TWAP order ID                         |
      | client_order_id      | Client-assigned ID                    |
      | is_reduce_only       | Whether reduce-only                   |
      | start_unix_ms        | Start timestamp                       |
      | frequency_s          | Execution frequency in seconds        |
      | duration_s           | Total duration in seconds             |
      | orig_size            | Original total size                   |
      | remaining_size       | Remaining unfilled size               |
      | status               | TWAP status                           |
      | transaction_unix_ms  | Last transaction timestamp            |

  Scenario: Retrieve TWAP order history
    Given I have completed multiple TWAP orders
    When I request my TWAP order history
    Then I should receive my historical TWAP orders
    And the response should include both active and finished orders

  Scenario: Retrieve paginated TWAP history
    Given I have more than 10 historical TWAP orders
    When I request TWAP history with limit 10 and offset 0
    Then I should receive the first 10 TWAP orders
    And the total count should reflect all TWAP orders

  Scenario: Cancel an active TWAP order
    Given I have an active TWAP order with ID "twap-123"
    And the TWAP order has remaining size
    When I cancel the TWAP order with:
      | order_id    | twap-123 |
      | market_addr | 0xabc... |
    Then the TWAP order should be canceled
    And no further executions should occur
    And the status should be "Cancelled"

  Scenario: TWAP order status progression
    Given I place a new TWAP order
    Then the initial status should be "Activated"
    When the TWAP order completes all executions
    Then the status should be "Finished"
    When I cancel the TWAP order before completion
    Then the status should be "Cancelled"

  Scenario: TWAP order executes incrementally
    Given I place a TWAP order with:
      | size                   | 1.0     |
      | twap_frequency_seconds | 60      |
      | twap_duration_seconds  | 300     |
    Then there should be 5 total executions (300 / 60)
    And each execution should be approximately 0.2
    When I check after 2 minutes
    Then the remaining_size should be approximately 0.6
    And 2 executions should have occurred

  Scenario: TWAP order for specific subaccount
    Given I have multiple subaccounts
    When I place a TWAP order specifying subaccount address "0x123..."
    Then the TWAP order should be placed for subaccount "0x123..."

  Scenario: TWAP order with session account
    Given I have delegated trading to a session account
    When I place a TWAP order with the session account override
    Then the TWAP order should be placed as the session account
    And the TWAP order should be associated with my subaccount

  Scenario: Subscribe to TWAP updates via WebSocket
    Given I have active TWAP orders
    When I subscribe to TWAP updates for my subaccount
    Then I should receive real-time updates when TWAP orders execute
    And updates should include remaining size changes
    And updates should include status changes

  Scenario: TWAP frequency validation
    When I attempt to place a TWAP order with frequency of 0 seconds
    Then the order should be rejected
    And an error should indicate an invalid frequency

  Scenario: TWAP duration validation
    When I attempt to place a TWAP order with duration of 0 seconds
    Then the order should be rejected
    And an error should indicate an invalid duration

  Scenario: Insufficient size for TWAP execution
    Given the market has a minimum order size of 0.001
    When I place a TWAP order with:
      | size                   | 0.005   |
      | twap_frequency_seconds | 60      |
      | twap_duration_seconds  | 600     |
    Then each execution would be 0.001 (0.005 / 10)
    And the TWAP order should be accepted

  Scenario: TWAP order with very high frequency
    When I place a TWAP order with frequency of 1 second
    Then the TWAP should execute every second
    And the order should be accepted if the network can support it
