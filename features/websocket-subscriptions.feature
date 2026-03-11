Feature: WebSocket Subscriptions

  As a trader using the Decibel SDK
  I want to receive real-time updates via WebSocket connections
  So that I can react quickly to market and account changes

  Background:
    Given I have an initialized Decibel read client

  Scenario: Establish WebSocket connection
    When I initiate a WebSocket connection
    Then the connection should be established
    And the connection should use the configured WebSocket URL
    And the connection should support authentication via API key

  Scenario: WebSocket auto-reconnect on disconnect
    Given I have an active WebSocket connection
    When the connection is disconnected
    Then the client should attempt to reconnect
    And reconnection should use exponential backoff

  Scenario: Subscribe to account overview updates
    Given I have an active WebSocket connection
    When I subscribe to account overview for subaccount address "0x123..."
    Then I should receive real-time updates for the account
    And updates should include balance changes
    And updates should include margin changes
    And updates should include PnL changes
    When I unsubscribe from account overview
    Then I should stop receiving account updates

  Scenario: Subscribe to user positions updates
    Given I have an active WebSocket connection
    When I subscribe to positions for subaccount address "0x123..."
    Then I should receive real-time position updates
    And updates should include new positions
    And updates should include size changes
    And updates should include entry price changes
    And updates should include unrealized PnL changes
    When I unsubscribe from positions
    Then I should stop receiving position updates

  Scenario: Subscribe to user open orders updates
    Given I have an active WebSocket connection
    When I subscribe to open orders for subaccount address "0x123..."
    Then I should receive real-time open order updates
    And updates should include new orders
    And updates should include order fills
    And updates should include order cancellations
    And updates should include remaining size changes
    When I unsubscribe from open orders
    Then I should stop receiving open order updates

  Scenario: Subscribe to user order history updates
    Given I have an active WebSocket connection
    When I subscribe to order history for subaccount address "0x123..."
    Then I should receive real-time order history updates
    And updates should include newly filled orders
    And updates should include newly canceled orders
    When I unsubscribe from order history
    Then I should stop receiving order history updates

  Scenario: Subscribe to user trade history updates
    Given I have an active WebSocket connection
    When I subscribe to trade history for subaccount address "0x123..."
    Then I should receive real-time trade updates
    And each trade should include:
      | field                   | description                      |
      | market                  | Market address                   |
      | action                  | Trade action type                |
      | size                    | Trade size                       |
      | price                   | Trade price                      |
      | is_profit               | Whether trade was profitable     |
      | realized_pnl_amount     | Realized PnL                     |
      | fee_amount              | Trading fee                      |
      | transaction_unix_ms     | Transaction timestamp            |
    When I unsubscribe from trade history
    Then I should stop receiving trade updates

  Scenario: Subscribe to user funding history updates
    Given I have an active WebSocket connection
    When I subscribe to funding history for subaccount address "0x123..."
    Then I should receive real-time funding updates
    And each funding update should include:
      | field                   | description                      |
      | market                  | Market address                   |
      | funding_rate_bps        | Funding rate in basis points     |
      | is_funding_positive     | Funding direction                |
      | funding_amount          | Funding payment amount           |
      | position_size           | Position size at funding time    |
      | transaction_unix_ms     | Timestamp                        |
    When I unsubscribe from funding history
    Then I should stop receiving funding updates

  Scenario: Subscribe to market depth updates
    Given I have an active WebSocket connection
    When I subscribe to market depth for "BTC-USD" with aggregation size 1
    Then I should receive real-time order book updates
    And updates should include bid changes
    And updates should include ask changes
    And updates should include the timestamp
    When I unsubscribe from market depth
    Then I should stop receiving depth updates

  Scenario: Subscribe to market depth with aggregation
    Given I have an active WebSocket connection
    When I subscribe to market depth for "BTC-USD" with aggregation size 10
    Then I should receive aggregated order book updates
    And price levels should be grouped by the aggregation size

  Scenario: Supported aggregation sizes for market depth
    When I request the available aggregation sizes
    Then I should receive [1, 2, 5, 10, 100, 1000]

  Scenario: Subscribe to market price updates
    Given I have an active WebSocket connection
    When I subscribe to market price for "BTC-USD"
    Then I should receive real-time price updates
    And each update should include:
      | field                | description                    |
      | market               | Market name                    |
      | mark_px              | Mark price                     |
      | mid_px               | Mid price                      |
      | oracle_px            | Oracle price                   |
      | funding_rate_bps     | Funding rate                   |
      | is_funding_positive  | Funding direction              |
      | open_interest        | Open interest                  |
      | transaction_unix_ms  | Timestamp                      |
    When I unsubscribe from market price
    Then I should stop receiving price updates

  Scenario: Subscribe to all market prices
    Given I have an active WebSocket connection
    When I subscribe to all market prices
    Then I should receive price updates for all markets
    And each update should include all markets
    When I unsubscribe from all market prices
    Then I should stop receiving price updates

  Scenario: Subscribe to market trades
    Given I have an active WebSocket connection
    When I subscribe to trades for "BTC-USD"
    Then I should receive real-time trade updates
    And each update should include the price, size, and direction
    And each update should include a timestamp
    When I unsubscribe from market trades
    Then I should stop receiving trade updates

  Scenario: Subscribe to candlestick updates
    Given I have an active WebSocket connection
    When I subscribe to candlesticks for "BTC-USD" with interval "1m"
    Then I should receive real-time candlestick updates
    And each update should include a complete candlestick
    And updates should arrive at the end of each interval
    When I unsubscribe from candlesticks
    Then I should stop receiving candlestick updates

  Scenario: Subscribe to candlesticks with different intervals
    Given I have an active WebSocket connection
    When I subscribe to candlesticks for "BTC-USD" with interval "1h"
    Then I should receive hourly candlestick updates
    When I subscribe to candlesticks for "ETH-USD" with interval "5m"
    Then I should receive 5-minute candlestick updates for ETH-USD

  Scenario: Subscribe to order updates
    Given I have an active WebSocket connection
    When I subscribe to order updates for subaccount address "0x123..."
    Then I should receive real-time order status changes
    And updates should include order acknowledgments
    And updates should include order fills
    And updates should include order cancellations
    And updates should include order rejections
    When I unsubscribe from order updates
    Then I should stop receiving order updates

  Scenario: Subscribe to notifications
    Given I have an active WebSocket connection
    When I subscribe to notifications for subaccount address "0x123..."
    Then I should receive real-time account notifications
    And each notification should include:
      | field      | description                |
      | id         | Notification ID            |
      | type       | Notification type          |
      | message    | Notification message       |
      | timestamp  | Timestamp                  |
      | read       | Read status                |
    When I unsubscribe from notifications
    Then I should stop receiving notifications

  Scenario: Subscribe to bulk orders
    Given I have an active WebSocket connection
    When I subscribe to bulk orders for subaccount address "0x123..."
    Then I should receive bulk order updates
    And updates should include bulk order placements
    And updates should include bulk order modifications
    When I unsubscribe from bulk orders
    Then I should stop receiving bulk order updates

  Scenario: Subscribe to bulk order fills
    Given I have an active WebSocket connection
    When I subscribe to bulk order fills for subaccount address "0x123..."
    Then I should receive real-time bulk order fill updates
    And updates should include partial fills
    And updates should include complete fills
    When I unsubscribe from bulk order fills
    Then I should stop receiving fill updates

  Scenario: Subscribe to active TWAP orders
    Given I have an active WebSocket connection
    When I subscribe to active TWAPs for subaccount address "0x123..."
    Then I should receive real-time TWAP order updates
    And updates should include new TWAP orders
    And updates should include TWAP executions
    And updates should include remaining size changes
    And updates should include TWAP completions
    And updates should include TWAP cancellations
    When I unsubscribe from active TWAPs
    Then I should stop receiving TWAP updates

  Scenario: Maintain single WebSocket connection for multiple subscriptions
    Given I have an active WebSocket connection
    When I subscribe to market depth for "BTC-USD"
    And I subscribe to market price for "BTC-USD"
    And I subscribe to positions for my subaccount
    Then all subscriptions should use the same WebSocket connection
    And I should receive updates for all subscriptions

  Scenario: Unsubscribe returns a handle
    Given I have an active WebSocket connection
    When I subscribe to market price for "BTC-USD"
    Then I should receive an unsubscribe handle
    And I can use the handle to unsubscribe from the specific subscription

  Scenario: Reset subscription
    Given I have an active subscription to market depth for "BTC-USD"
    When I reset the market depth subscription
    Then the subscription should be re-subscribed
    And I should receive a fresh snapshot of the data

  Scenario: Close WebSocket connection
    Given I have an active WebSocket connection with multiple subscriptions
    When I close the WebSocket connection
    Then all subscriptions should be cleaned up
    And no further updates should be received

  Scenario: Check WebSocket connection state
    Given I have a WebSocket client
    When I check the connection state
    Then the state should be one of:
      | Connecting | Open | Closing | Closed |

  Scenario: WebSocket message parsing is thread-safe
    Given I have an active WebSocket connection
    And I am receiving rapid updates
    Then message parsing should happen on a background thread
    And callbacks should not block the WebSocket read loop

  Scenario: WebSocket error callback
    Given I have a WebSocket client
    And I have registered an error callback
    When a WebSocket error occurs
    Then the error callback should be invoked
    And the error should include details about the failure

  Scenario: Subscribe with API key authentication
    Given I have a valid API key
    When I establish a WebSocket connection with the API key
    Then the connection should include the API key
    And I should be able to subscribe to authenticated channels
