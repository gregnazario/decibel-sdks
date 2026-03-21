Feature: Human-Readable Price and Size Conversion
  As a trading bot developer using the Decibel SDK
  I need the SDK to convert between human-readable and chain-native units
  So that I can work with intuitive numbers like 45000.0 instead of raw integer units

  Background:
    Given a BTC-USD market config:
      | field        | value          |
      | market_addr  | 0xbtc_market   |
      | market_name  | BTC-USD        |
      | sz_decimals  | 8              |
      | px_decimals  | 8              |
      | max_leverage | 50.0           |
      | min_size     | 0.001          |
      | lot_size     | 0.001          |
      | tick_size    | 0.1            |

  # --- Price conversion ---

  Scenario: Bot passes human price, SDK converts to chain units using market config
    When the bot submits a buy order at human price 45000.0
    Then the SDK converts price to chain units: 4500000000000
    # 45000.0 * 10^8 = 4500000000000
    And the on-chain transaction uses price 4500000000000

  # --- Size conversion ---

  Scenario: Bot passes human size, SDK rounds to lot_size and converts
    When the bot submits an order with human size 0.257
    Then the SDK rounds size to the nearest lot_size: 0.257
    # 0.257 is already a multiple of 0.001
    And the SDK converts size to chain units: 25700000
    # 0.257 * 10^8 = 25700000

  # --- Min size clamping ---

  Scenario: Size below min_size is clamped to min_size
    When the bot submits an order with human size 0.0005
    Then the SDK clamps size to min_size: 0.001
    And the SDK converts size to chain units: 100000
    # 0.001 * 10^8 = 100000

  # --- Price tick rounding ---

  Scenario: Price is rounded to nearest tick_size
    When the bot submits a buy order at human price 45000.37
    Then the SDK rounds the price down to the nearest tick_size: 45000.3
    # For buy orders, round down to nearest 0.1
    And chain units are 4500030000000

    When the bot submits a sell order at human price 45000.37
    Then the SDK rounds the price up to the nearest tick_size: 45000.4
    # For sell orders, round up to nearest 0.1
    And chain units are 4500040000000

  # --- Raw mode ---

  Scenario: Raw mode bypasses conversion
    When the bot submits an order with raw price 4500000000000 and raw size 25700000 in raw mode
    Then no rounding or conversion is applied
    And the on-chain transaction uses price 4500000000000 and size 25700000 exactly

  # --- Round-trip fidelity ---

  Scenario: Round-trip from human to chain to human preserves value within tick precision
    Given a human price of 45000.5
    When the SDK converts to chain units: 4500050000000
    And the SDK converts back to human units
    Then the result is 45000.5
    And the round-trip error is 0.0

    Given a human price of 45000.37
    When the SDK rounds to tick_size 0.1 for a buy: 45000.3
    And converts to chain units: 4500030000000
    And converts back to human units
    Then the result is 45000.3
    And the round-trip error relative to the rounded price is 0.0

    Given a human size of 1.2345
    When the SDK rounds to lot_size 0.001: 1.234
    And converts to chain units: 123400000
    And converts back to human units
    Then the result is 1.234
    And the round-trip error relative to the rounded size is 0.0
