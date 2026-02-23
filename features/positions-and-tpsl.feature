Feature: Positions and Take-Profit/Stop-Loss Management

  As a trader using the Decibel SDK
  I want to monitor my positions and manage take-profit and stop-loss orders
  So that I can protect my trading capital and lock in profits

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with a funded subaccount
    And I have configured my subaccount for the "BTC-USD" market

  Scenario: Retrieve all open positions
    Given I have open positions on multiple markets
    When I request my positions
    Then I should receive all my open positions
    And each position should include:
      | field                       | description                        |
      | market                      | Market address                     |
      | user                        | Subaccount address                 |
      | size                        | Position size (negative = short)   |
      | user_leverage               | User leverage setting              |
      | entry_price                 | Average entry price                |
      | is_isolated                 | Whether isolated margin            |
      | unrealized_funding          | Unrealized funding cost            |
      | estimated_liquidation_price | Liquidation price estimate         |

  Scenario: Retrieve positions for specific market
    Given I have positions on multiple markets
    When I request my positions filtered by "BTC-USD" market address
    Then I should receive only my "BTC-USD" positions

  Scenario: Retrieve positions including deleted
    Given I have closed positions
    When I request my positions with include_deleted set to true
    Then I should receive both open and closed positions
    And closed positions should be marked as deleted

  Scenario: Position with take-profit order
    Given I have an open long position
    When I place a take-profit order with:
      | market_addr       | 0xabc... |
      | tp_trigger_price  | 50000    |
      | tp_limit_price    | 50050    |
      | tp_size           | 0.5      |
    Then a take-profit order should be created
    And the take-profit should trigger when price reaches 50000
    And the take-profit should limit at 50050

  Scenario: Position with stop-loss order
    Given I have an open long position
    When I place a stop-loss order with:
      | market_addr       | 0xabc... |
      | sl_trigger_price  | 40000    |
      | sl_limit_price    | 39950    |
      | sl_size           | 0.5      |
    Then a stop-loss order should be created
    And the stop-loss should trigger when price drops to 40000
    And the stop-loss should limit at 39950

  Scenario: Position with both take-profit and stop-loss
    Given I have an open long position
    When I place a TP/SL order with:
      | market_addr       | 0xabc... |
      | tp_trigger_price  | 50000    |
      | tp_limit_price    | 50050    |
      | tp_size           | 0.5      |
      | sl_trigger_price  | 40000    |
      | sl_limit_price    | 39950    |
      | sl_size           | 0.5      |
    Then both take-profit and stop-loss orders should be created
    And either order closing the position should cancel the other

  Scenario: Update take-profit order
    Given I have a position with an existing take-profit order
    And the existing take-profit order ID is "tp-123"
    When I update the take-profit order with:
      | market_addr       | 0xabc...  |
      | prev_order_id     | tp-123    |
      | tp_trigger_price  | 51000     |
      | tp_limit_price    | 51050     |
    Then the take-profit should be updated to the new prices
    And the old take-profit order should be canceled

  Scenario: Update stop-loss order
    Given I have a position with an existing stop-loss order
    And the existing stop-loss order ID is "sl-123"
    When I update the stop-loss order with:
      | market_addr       | 0xabc...  |
      | prev_order_id     | sl-123    |
      | sl_trigger_price  | 41000     |
      | sl_limit_price    | 40950     |
    Then the stop-loss should be updated to the new prices
    And the old stop-loss order should be canceled

  Scenario: Cancel take-profit order
    Given I have a position with a take-profit order
    And the take-profit order ID is "tp-123"
    When I cancel the take-profit order for the market
    Then the take-profit order should be canceled
    And the position should remain open without take-profit

  Scenario: Cancel stop-loss order
    Given I have a position with a stop-loss order
    And the stop-loss order ID is "sl-123"
    When I cancel the stop-loss order for the market
    Then the stop-loss order should be canceled
    And the position should remain open without stop-loss

  Scenario: Cancel both TP and SL orders
    Given I have a position with both take-profit and stop-loss orders
    When I cancel the TP/SL orders for the market
    Then both orders should be canceled
    And the position should remain open

  Scenario: TP/SL prices are rounded to tick size
    Given the market has a tick size of 0.1
    When I place a take-profit with trigger price 50000.05
    Then the trigger price should be rounded to the nearest tick

  Scenario: Partial TP/SL for position
    Given I have an open position of 1.0 BTC
    When I place a take-profit with size 0.5
    Then only 0.5 BTC should be closed at take-profit
    And 0.5 BTC should remain in the position

  Scenario: Fixed size TP/SL orders
    Given I have a position with fixed-size TP/SL enabled
    When I update the take-profit without specifying size
    Then the existing fixed size should be maintained

  Scenario: Position displays active TP/SL information
    Given I have a position with take-profit and stop-loss orders
    When I retrieve my positions
    Then the position should include:
      | field            | description                    |
      | tp_order_id      | Take-profit order ID           |
      | tp_trigger_price | Take-profit trigger price      |
      | tp_limit_price   | Take-profit limit price        |
      | sl_order_id      | Stop-loss order ID             |
      | sl_trigger_price | Stop-loss trigger price        |
      | sl_limit_price   | Stop-loss limit price          |

  Scenario: Calculate unrealized PnL for position
    Given I have a long position of 0.5 BTC
    And my entry price was 45000
    And the current mark price is 46000
    When I retrieve my position
    Then my unrealized PnL should be approximately $500

  Scenario: Liquidation price estimate for long position
    Given I have a long position with 10x leverage
    And my entry price was 45000
    When I retrieve my position
    Then I should see an estimated liquidation price
    And the liquidation price should be below my entry price

  Scenario: Liquidation price estimate for short position
    Given I have a short position with 10x leverage
    And my entry price was 45000
    When I retrieve my position
    Then I should see an estimated liquidation price
    And the liquidation price should be above my entry price

  Scenario: Cross margin position shares collateral
    Given I have a cross margin position on "BTC-USD"
    And I have another cross margin position on "ETH-USD"
    When I retrieve my account overview
    Then my total margin should be shared across both positions

  Scenario: Isolated margin position has dedicated collateral
    Given I have an isolated margin position on "BTC-USD"
    When I retrieve my position
    Then the position should be marked as isolated
    And the position should not share collateral with other positions

  Scenario: Position funding accrual
    Given I have held a position through multiple funding periods
    When I retrieve my position
    Then I should see an unrealized funding cost
    And the funding cost may be positive or negative

  Scenario: Subscribe to position updates via WebSocket
    Given I have open positions
    When I subscribe to position updates for my subaccount
    Then I should receive real-time updates when positions change
    And updates should include size changes, PnL changes, and TP/SL changes
