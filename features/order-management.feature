Feature: Order Management

  As a trader using the Decibel SDK
  I want to place, cancel, and manage orders on the perpetual futures exchange
  So that I can execute my trading strategies

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with a funded subaccount
    And I have configured my subaccount for the "BTC-USD" market

  Scenario: Place a simple limit buy order
    When I place a limit order with:
      | market_name | BTC-USD |
      | price       | 45000   |
      | size        | 0.1     |
      | is_buy      | true    |
    Then the order should be accepted
    And I should receive an order ID
    And I should receive a transaction hash
    And the order should appear in my open orders

  Scenario: Place a simple limit sell order
    When I place a limit order with:
      | market_name | BTC-USD |
      | price       | 46000   |
      | size        | 0.1     |
      | is_buy      | false   |
    Then the order should be accepted
    And I should receive an order ID

  Scenario: Place a limit order with Good Till Cancel time in force
    When I place a limit order with:
      | market_name   | BTC-USD               |
      | price         | 45000                 |
      | size          | 0.1                   |
      | is_buy        | true                  |
      | time_in_force | GoodTillCanceled      |
    Then the order should remain on the book until filled or canceled

  Scenario: Place a Post-Only order
    When I place a limit order with:
      | market_name   | BTC-USD    |
      | price         | 45000      |
      | size          | 0.1        |
      | is_buy        | true       |
      | time_in_force | PostOnly   |
    Then the order should only be added to the book as a maker order
    If the order would immediately match, it should be rejected

  Scenario: Place an Immediate or Cancel order
    When I place a limit order with:
      | market_name   | BTC-USD           |
      | price         | 45000             |
      | size          | 0.1               |
      | is_buy        | true              |
      | time_in_force | ImmediateOrCancel |
    Then any portion that can be filled immediately should be filled
    And any remaining portion should be canceled

  Scenario: Place a reduce-only order
    Given I have an open long position of 0.5 BTC
    When I place a limit order with:
      | market_name    | BTC-USD    |
      | price          | 46000      |
      | size           | 0.3        |
      | is_buy         | false      |
      | is_reduce_only | true       |
    Then the order should only reduce my existing position
    And the order should not open a new short position

  Scenario: Place a stop market order
    When I place a stop order with:
      | market_name | BTC-USD |
      | price       | 44000   |
      | stop_price  | 44500   |
      | size        | 0.1     |
      | is_buy      | false   |
    Then when the market price reaches 44500
    And a market sell order should be triggered

  Scenario: Place an order with client order ID
    When I place a limit order with:
      | market_name     | BTC-USD       |
      | price           | 45000         |
      | size            | 0.1           |
      | is_buy          | true          |
      | client_order_id | my-order-123  |
    Then I should be able to reference the order by "my-order-123"

  Scenario: Place an order with builder fee
    When I place a limit order with:
      | market_name   | BTC-USD            |
      | price         | 45000              |
      | size          | 0.1                |
      | is_buy        | true               |
      | builder_addr  | 0xfeb...           |
      | builder_fee   | 10                 |
    Then the specified builder should receive a 10 basis point fee

  Scenario: Cancel an order by order ID
    Given I have an open order with ID "12345"
    When I cancel the order with order ID "12345"
    Then the order should be canceled
    And the order should be removed from my open orders

  Scenario: Cancel an order by client order ID
    Given I have an open order with client order ID "my-order-123"
    When I cancel the order with client order ID "my-order-123"
    Then the order should be canceled

  Scenario: Cancel order requires market identification
    Given I have an open order with ID "12345"
    When I cancel the order providing only the order ID
    Then the cancellation should fail
    When I cancel the order providing order ID and market name
    Then the cancellation should succeed

  Scenario: Order price is rounded to tick size
    Given the "BTC-USD" market has a tick size of 0.1
    When I place a limit order with price 45000.05
    Then the order price should be rounded to 45000.0 or 45000.1

  Scenario: Order size must meet minimum size requirement
    Given the "BTC-USD" market has a minimum order size of 0.001
    When I attempt to place an order with size 0.0001
    Then the order should be rejected
    And an error should indicate the size is below minimum

  Scenario: Order size must be a multiple of lot size
    Given the "BTC-USD" market has a lot size of 0.001
    When I place an order with size 0.0015
    Then the order size should be rounded to the nearest lot size

  Scenario: Retrieve open orders
    Given I have multiple open orders across different markets
    When I request my open orders
    Then I should receive all my open orders
    And each order should include:
      | field             | description                      |
      | order_id          | Unique order identifier          |
      | client_order_id   | Client-assigned identifier       |
      | market            | Market address                   |
      | price             | Limit price                      |
      | orig_size         | Original order size              |
      | remaining_size    | Remaining unfilled size          |
      | is_buy            | Buy or sell                      |
      | time_in_force     | Time in force type               |
      | is_reduce_only    | Whether reduce-only              |
      | status            | Order status                     |
      | transaction_unix_ms | Transaction timestamp         |

  Scenario: Retrieve order history
    Given I have placed and filled multiple orders
    When I request my order history
    Then I should receive my historical orders
    And the response should include pagination information

  Scenario: Retrieve paginated order history
    Given I have more than 10 historical orders
    When I request order history with limit 10 and offset 0
    Then I should receive the first 10 orders
    And the total count should reflect all historical orders

  Scenario: Filter order history by market
    Given I have orders on multiple markets
    When I request order history filtered by "BTC-USD" market address
    Then I should only receive orders for the "BTC-USD" market

  Scenario: Query order status
    Given I have placed an order with ID "12345"
    When I query the order status for "12345"
    Then I should receive the current order status
    And the status should be one of:
      | Acknowledged | Filled | Cancelled | Rejected | Unknown |

  Scenario: Insufficient margin for order
    Given my subaccount has insufficient margin
    When I attempt to place a large order
    Then the order should be rejected
    And an error should indicate insufficient margin

  Scenario: Place order for specific subaccount
    Given I have multiple subaccounts
    When I place an order specifying subaccount address "0x123..."
    Then the order should be placed for subaccount "0x123..."

  Scenario: Place order with session account
    Given I have delegated trading to a session account
    When I place an order with the session account override
    Then the order should be placed as the session account
    And the order should be associated with my subaccount
