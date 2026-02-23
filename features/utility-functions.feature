Feature: Utility Functions

  As a developer using the Decibel SDK
  I want to use utility functions for common operations
  So that I can efficiently work with addresses, prices, and transaction data

  Background:
    Given I have the Decibel SDK available

  Scenario: Derive market address from market name
    Given I have the perp engine global address "0xabc..."
    When I derive the market address for market name "BTC-USD"
    Then I should receive a valid market object address
    And the address should be deterministic for the same market name

  Scenario: Derive primary subaccount address
    Given I have an account address "0x123..."
    And I have the package address "0xpkg..."
    And I have the compatibility version "v0.4"
    When I derive the primary subaccount address
    Then I should receive the derived subaccount address
    And the address should be consistent across SDK implementations

  Scenario: Derive vault share token address
    Given I have a vault address "0xvault..."
    When I derive the vault share token address
    Then I should receive the address of the vault's share token

  Scenario: Round price to tick size
    Given the market has a tick size of 0.1
    And the market has 2 price decimals
    When I round the price 45000.05 with tick size 0.1
    Then the result should be 45000.0 or 45000.1
    When I round with round_up set to true
    Then the result should be 45000.1
    When I round with round_up set to false
    Then the result should be 45000.0

  Scenario: Round size to lot size
    Given the market has a lot size of 0.001
    When I round the size 0.0015
    Then the result should be 0.001 or 0.002

  Scenario: Generate random nonce for replay protection
    When I generate a random replay protection nonce
    Then the result should be a valid u64 value
    And each generated nonce should be unique
    And the nonce should be suitable for transaction replay protection

  Scenario: Extract order ID from transaction response
    Given I submitted a transaction that created an order
    And the transaction contains an OrderEvent
    When I extract the order ID from the transaction response
    Then I should receive the order ID
    And the order ID should match the ID in the OrderEvent

  Scenario: Extract order ID returns null when no order event
    Given I submitted a transaction that did not create an order
    When I attempt to extract the order ID
    Then the result should be null or empty

  Scenario: Construct query parameters for pagination
    Given I have page_params with limit 20 and offset 40
    When I construct the query parameters
    Then the result should include "limit=20"
    And the result should include "offset=40"

  Scenario: Construct query parameters for sorting
    Given I have sort_params with key "tvl" and direction "DESC"
    When I construct the query parameters
    Then the result should include "sort_key=tvl"
    And the result should include "sort_dir=DESC"

  Scenario: Construct query parameters for search
    Given I have search_params with term "Bitcoin"
    When I construct the query parameters
    Then the result should include "search_term=Bitcoin"

  Scenario: Construct combined query parameters
    Given I have page_params with limit 10
    And I have sort_params with key "name" and direction "ASC"
    And I have search_params with term "BTC"
    When I construct the combined query parameters
    Then the result should include all parameters:
      | parameter      | value        |
      | limit          | 10           |
      | sort_key       | name         |
      | sort_dir       | ASC          |
      | search_term    | BTC          |

  Scenario: Format amount with USDC decimals
    Given USDC has 6 decimals
    When I format the raw amount 1000000
    Then the result should be 1.0 USDC
    When I format the raw amount 500000
    Then the result should be 0.5 USDC

  Scenario: Parse amount to raw units
    Given USDC has 6 decimals
    When I parse the amount 1.5 USDC
    Then the result should be 1500000 raw units
    When I parse the amount 0.000001 USDC
    Then the result should be 1 raw unit

  Scenario: Validate address format
    When I validate a valid Aptos address "0x123..."
    Then the result should indicate the address is valid
    When I validate an invalid address "not-an-address"
    Then the result should indicate the address is invalid

  Scenario: Calculate position side from size
    Given I have a position size of 0.5 BTC
    When I determine the position side
    Then the result should indicate a long position
    Given I have a position size of -0.5 BTC
    When I determine the position side
    Then the result should indicate a short position
    Given I have a position size of 0 BTC
    When I determine the position side
    Then the result should indicate no position

  Scenario: Convert leverage to basis points
    When I convert 10x leverage to basis points
    Then the result should be 1000
    When I convert 100x leverage to basis points
    Then the result should be 10000
    When I convert 1x leverage to basis points
    Then the result should be 100

  Scenario: Convert basis points to leverage
    When I convert 1000 basis points to leverage
    Then the result should be 10x
    When I convert 10000 basis points to leverage
    Then the result should be 100x

  Scenario: Calculate percentage from basis points
    When I calculate percentage for 100 basis points
    Then the result should be 1%
    When I calculate percentage for 50 basis points
    Then the result should be 0.5%
    When I calculate percentage for 1 basis point
    Then the result should be 0.01%

  Scenario: Format timestamp to ISO string
    Given I have a unix millisecond timestamp of 1708000000000
    When I format the timestamp to ISO string
    Then the result should be a valid ISO 8601 datetime string

  Scenario: Parse ISO string to timestamp
    Given I have an ISO 8601 datetime string
    When I parse the string to unix milliseconds
    Then the result should be a valid timestamp in milliseconds

  Scenario: Calculate time elapsed since timestamp
    Given I have a timestamp from 1 hour ago
    When I calculate the time elapsed
    Then the result should indicate approximately 1 hour has passed
