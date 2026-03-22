Feature: Position State Management
  As a trading bot using the Decibel SDK
  I need to maintain accurate local position state
  So that I can make informed trading decisions without blocking on network calls

  Background:
    Given a PositionStateManager instance
    And subaccount "0xaaa1" is registered

  # --- Initial state bootstrap via WebSocket ---

  Scenario: Bot starts up and receives initial position state via WebSocket
    Given the bot subscribes to user positions for subaccount "0xaaa1"
    When the WebSocket delivers an initial snapshot with:
      | market  | size | entry_price | estimated_liquidation_price |
      | BTC-USD | 2.0  | 60000.0     | 55000.0                     |
      | ETH-USD | -5.0 | 3000.0      | 3500.0                      |
    Then the position manager contains 2 positions for subaccount "0xaaa1"
    And the BTC-USD position has size 2.0 and entry price 60000.0
    And the ETH-USD position has size -5.0 and entry price 3000.0

  # --- Live position updates ---

  Scenario: Position updates arrive via WebSocket and local state reflects them
    Given the position manager has a BTC-USD position with size 2.0 for subaccount "0xaaa1"
    When a WebSocket position update arrives for BTC-USD with size 3.5 and entry price 61000.0
    Then the BTC-USD position for subaccount "0xaaa1" has size 3.5
    And the BTC-USD entry price is 61000.0

  # --- Synchronous reads ---

  Scenario: Bot reads positions synchronously without awaiting
    Given the position manager has been populated with:
      | market  | size | entry_price |
      | BTC-USD | 1.0  | 60000.0     |
      | ETH-USD | -3.0 | 3200.0      |
    When the bot calls positions("0xaaa1") synchronously
    Then the result is a dict with keys "BTC-USD" and "ETH-USD"
    And no async await or network call is required

  # --- Flat / closed positions ---

  Scenario: Position size goes to zero means position is flat and closed
    Given the position manager has a BTC-USD position with size 1.0 for subaccount "0xaaa1"
    When a position update arrives for BTC-USD with size 0.0
    Then position("BTC-USD", "0xaaa1") returns None
    And has_position("BTC-USD", "0xaaa1") returns False
    And "BTC-USD" is not in the positions dict for subaccount "0xaaa1"

  # --- Multi-subaccount tracking ---

  Scenario: Multiple subaccounts tracked independently
    Given subaccount "0xaaa1" has a BTC-USD position with size 2.0 and entry price 60000.0
    And subaccount "0xbbb2" has a BTC-USD position with size -1.5 and entry price 62000.0
    When the bot queries positions for subaccount "0xaaa1"
    Then the BTC-USD position size is 2.0
    When the bot queries positions for subaccount "0xbbb2"
    Then the BTC-USD position size is -1.5

  # --- Net exposure ---

  Scenario: Net exposure calculated across multiple positions
    Given the position manager has:
      | market  | size  | entry_price |
      | BTC-USD | 2.0   | 60000.0     |
      | ETH-USD | -10.0 | 3000.0      |
    And the latest mark prices are:
      | market  | mark_px |
      | BTC-USD | 60000.0 |
      | ETH-USD | 3000.0  |
    When the bot computes net_exposure("0xaaa1")
    Then the net exposure is 90000.0
    # 2.0 * 60000.0 + (-10.0) * 3000.0 = 120000.0 - 30000.0 = 90000.0

  # --- Gross exposure ---

  Scenario: Gross exposure calculated as sum of absolute notionals
    Given the position manager has:
      | market  | size  | entry_price |
      | BTC-USD | 2.0   | 60000.0     |
      | ETH-USD | -10.0 | 3000.0      |
    And the latest mark prices are:
      | market  | mark_px |
      | BTC-USD | 60000.0 |
      | ETH-USD | 3000.0  |
    When the bot computes gross_exposure("0xaaa1")
    Then the gross exposure is 150000.0
    # |2.0 * 60000.0| + |-10.0 * 3000.0| = 120000.0 + 30000.0 = 150000.0

  # --- Mark price subscription ---

  Scenario: Mark price subscription updates latest price
    Given the bot subscribes to market price for "BTC-USD"
    When a market price update arrives with mark_px 61234.5 and mid_px 61234.0 and funding_rate_bps 0.5
    Then mark_price("BTC-USD") returns 61234.5
    And mid_price("BTC-USD") returns 61234.0
    And the cached MarketPrice for "BTC-USD" has funding_rate_bps 0.5

  # --- Depth subscription ---

  Scenario: Depth subscription updates local orderbook
    Given the bot subscribes to market depth for "BTC-USD" with aggregation size 1
    When a depth update arrives with:
      | side | price   | size |
      | bid  | 59999.0 | 2.0  |
      | bid  | 59998.0 | 5.0  |
      | ask  | 60001.0 | 1.5  |
      | ask  | 60002.0 | 3.0  |
    Then depth("BTC-USD") returns a MarketDepth with 2 bids and 2 asks
    And the best bid is 59999.0 with size 2.0
    And the best ask is 60001.0 with size 1.5
