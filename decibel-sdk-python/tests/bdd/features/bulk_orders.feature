Feature: Bulk Order Management for Market Making
  As a market-making bot using the Decibel SDK
  I need to place and update two-sided quotes atomically
  So that I can maintain tight spreads with minimal latency and track fills accurately

  Background:
    Given the bot is configured for market "BTC-USD"
    And subaccount "0xaaa1" is active
    And the current BTC-USD mid price is 60000.0

  # --- Initial quote placement ---

  Scenario: Market maker sets initial two-sided quotes
    When the bot calls set_quotes with:
      | side | price   | size |
      | bid  | 59990.0 | 0.5  |
      | bid  | 59980.0 | 1.0  |
      | bid  | 59970.0 | 1.5  |
      | ask  | 60010.0 | 0.5  |
      | ask  | 60020.0 | 1.0  |
      | ask  | 60030.0 | 1.5  |
    Then the exchange acknowledges 6 bulk orders
    And open_orders contains 3 bid orders and 3 ask orders
    And the best bid quote is at 59990.0 for size 0.5
    And the best ask quote is at 60010.0 for size 0.5

  # --- Atomic quote replacement ---

  Scenario: Quote update atomically replaces previous quotes
    Given the bot has 3 bid quotes and 3 ask quotes on "BTC-USD"
    When the bot calls set_quotes with updated levels:
      | side | price   | size |
      | bid  | 59995.0 | 0.5  |
      | bid  | 59985.0 | 1.0  |
      | ask  | 60005.0 | 0.5  |
      | ask  | 60015.0 | 1.0  |
    Then the previous 6 quotes are cancelled
    And 4 new quotes are placed atomically
    And open_orders contains 2 bid orders and 2 ask orders

  # --- Sequence number auto-increment ---

  Scenario: Sequence number auto-increments on each set_quotes call
    When the bot calls set_quotes for the first time
    Then the sequence number in the request is 1
    When the bot calls set_quotes a second time
    Then the sequence number in the request is 2
    When the bot calls set_quotes a third time
    Then the sequence number in the request is 3

  # --- Fill tracking ---

  Scenario: Fill tracking records bid fills and ask fills separately
    Given the bot has active quotes:
      | side | price   | size |
      | bid  | 59990.0 | 1.0  |
      | ask  | 60010.0 | 1.0  |
    When a fill arrives on the bid side at 59990.0 for size 0.3
    And a fill arrives on the ask side at 60010.0 for size 0.5
    Then the bid fill tracker shows 0.3 filled at average price 59990.0
    And the ask fill tracker shows 0.5 filled at average price 60010.0

  # --- Fill summary ---

  Scenario: Fill summary reports net inventory change
    Given the bot has recorded fills:
      | side | price   | size |
      | bid  | 59990.0 | 0.8  |
      | bid  | 59985.0 | 0.2  |
      | ask  | 60010.0 | 0.5  |
    When the bot requests a fill summary
    Then the net inventory change is +0.5
    # bought 1.0 total, sold 0.5, net = +0.5
    And the total bid volume is 1.0
    And the total ask volume is 0.5
    And the average bid price is 59989.0
    # (0.8 * 59990.0 + 0.2 * 59985.0) / 1.0 = 59989.0

  # --- Cancel all ---

  Scenario: cancel_all removes all bulk orders
    Given the bot has 5 bid quotes and 5 ask quotes on "BTC-USD"
    When the bot calls cancel_all for "BTC-USD"
    Then open_orders for subaccount "0xaaa1" is empty
    And the cancel_all response confirms 10 orders cancelled

  # --- Max levels enforcement ---

  Scenario: Max 30 levels per side enforced
    When the bot attempts to set_quotes with 31 bid levels and 30 ask levels
    Then a ValidationError is raised with message containing "max 30 levels per side"
    And no orders are sent to the exchange

  # --- One-sided quoting ---

  Scenario: Empty quotes on one side is valid for one-sided quoting
    When the bot calls set_quotes with:
      | side | price   | size |
      | ask  | 60010.0 | 0.5  |
      | ask  | 60020.0 | 1.0  |
      | ask  | 60030.0 | 1.5  |
    And no bid levels are provided
    Then the exchange acknowledges 3 ask-only bulk orders
    And open_orders contains 0 bid orders and 3 ask orders
