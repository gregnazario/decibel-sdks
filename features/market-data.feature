Feature: Market Data

  As a trader using the Decibel SDK
  I want to retrieve market data for available perpetual futures markets
  So that I can make informed trading decisions

  Background:
    Given I have an initialized Decibel read client

  Scenario: Retrieve all available markets
    When I request all markets
    Then I should receive a list of market configurations
    And each market should have a market address
    And each market should have a market name
    And each market should have size decimals
    And each market should have price decimals
    And each market should have maximum leverage
    And each market should have minimum order size
    And each market should have lot size
    And each market should have tick size

  Scenario: Retrieve a specific market by name
    When I request the market with name "BTC-USD"
    Then I should receive the BTC-USD market configuration
    And the market name should be "BTC-USD"
    And the market should have a valid market address

  Scenario: Retrieve market depth for a market
    When I request the market depth for "BTC-USD" with no limit
    Then I should receive the current order book
    And the order book should contain bid orders
    And the order book should contain ask orders
    And bid orders should be sorted by price descending
    And ask orders should be sorted by price ascending
    And each price level should have a price and size

  Scenario: Retrieve market depth with custom limit
    When I request the market depth for "BTC-USD" with a limit of 10
    Then I should receive up to 10 price levels on each side

  Scenario: Retrieve all market prices
    When I request all market prices
    Then I should receive current prices for all markets
    And each market price should include a mark price
    And each market price should include a mid price
    And each market price should include an oracle price
    And each market price should include a funding rate
    And each market price should include the funding direction
    And each market price should include open interest
    And each market price should include a timestamp

  Scenario: Retrieve price for a specific market
    When I request the price for "BTC-USD"
    Then I should receive the current BTC-USD market price
    And the price data should include mark price, mid price, and oracle price

  Scenario: Retrieve recent trades for a market
    When I request recent trades for "BTC-USD" with default limit
    Then I should receive a list of recent trades
    And each trade should have a price
    And each trade should have a size
    And each trade should indicate if it was a buy or sell
    And each trade should have a timestamp

  Scenario: Retrieve recent trades with custom limit
    When I request recent trades for "BTC-USD" with a limit of 50
    Then I should receive up to 50 recent trades

  Scenario: Retrieve candlesticks for a market
    When I request candlesticks for "BTC-USD" with interval "1h"
    Then I should receive historical candlestick data
    And each candlestick should have an open price
    And each candlestick should have a high price
    And each candlestick should have a low price
    And each candlestick should have a close price
    And each candlestick should have a volume
    And each candlestick should have an open timestamp
    And each candlestick should have a close timestamp

  Scenario: Retrieve candlesticks with custom time range
    When I request candlesticks for "BTC-USD" with interval "1h" between startTime and endTime
    Then I should receive candlesticks only within the specified time range

  Scenario: Retrieve candlesticks with different intervals
    When I request candlesticks for "BTC-USD" with interval "1m"
    Then I should receive 1-minute candlesticks
    When I request candlesticks for "BTC-USD" with interval "1d"
    Then I should receive daily candlesticks

  Scenario: Retrieve asset contexts
    When I request all asset contexts
    Then I should receive market context data for all markets
    And each context should include 24-hour volume
    And each context should include open interest
    And each context should include previous day price
    And each context should include 24-hour price change percentage

  Scenario: Market data uses valid enumeration types
    When I request candlesticks with an interval
    Then the interval should be one of the supported intervals:
      | 1m  | 5m  | 15m | 30m | 1h | 2h | 4h | 8h | 12h | 1d | 3d | 1w | 1mo |

  Scenario: Handle invalid market name
    When I request a market with name "INVALID-MARKET"
    Then I should receive an API error
    And the error should indicate that the market was not found

  Scenario: Handle invalid candlestick interval
    When I request candlesticks with interval "99x"
    Then I should receive a validation error
    And the error should indicate that the interval is not supported
