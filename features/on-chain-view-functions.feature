Feature: On-Chain View Functions

  As a developer using the Decibel SDK
  I want to query on-chain state directly via view functions
  So that I can access real-time blockchain data without waiting for API indexing

  Background:
    Given I have an initialized Decibel read client
    And I have access to the Aptos fullnode

  Scenario: Query global perp engine state
    When I query the global perp engine state
    Then I should receive the global state
    And the state should include engine configuration
    And the state should include global parameters

  Scenario: Query collateral balance decimals
    When I query the collateral balance decimals
    Then I should receive the decimal precision for collateral
    And the decimals should be consistent with the token standard

  Scenario: Query USDC decimals with caching
    When I first query the USDC decimals
    Then the decimals should be fetched from the chain
    When I query the USDC decimals again
    Then the cached value should be returned
    And no additional network call should be made

  Scenario: Query USDC balance for an address
    Given I have an account address "0x123..."
    When I query the USDC balance for the address
    Then I should receive the balance in raw units
    And I should receive the balance in human-readable format

  Scenario: Query account balance
    Given I have an account address "0x123..."
    When I query the account balance
    Then I should receive the total account balance
    And the balance should include all subaccount balances

  Scenario: Query position size for a market
    Given I have a subaccount address "0x123..."
    And I have a market address "0xmarket..."
    When I query the position size
    Then I should receive the current position size
    And a positive size should indicate a long position
    And a negative size should indicate a short position
    And zero should indicate no position

  Scenario: Query crossed positions
    Given I have a subaccount address "0x123..."
    When I query the crossed positions
    Then I should receive all cross-margin positions
    And the response should include position sizes
    And the response should include market addresses

  Scenario: Query generic token balance
    Given I have an account address "0x123..."
    And I have a token address "0xtoken..."
    And I know the token has 8 decimals
    When I query the token balance
    Then I should receive the balance in raw units
    And I should receive the balance converted using the decimals

  Scenario: View function does not require gas
    When I query any on-chain view function
    Then no gas should be consumed
    And no transaction should be submitted
    And the query should be read-only

  Scenario: View function returns current blockchain state
    Given I have an open position
    When I query the position size via view function
    Then the result should reflect the current on-chain state
    And the result should not be affected by API indexing delays

  Scenario: Handle view function for non-existent account
    Given I have an account address that has never been used
    When I query the account balance
    Then the balance should be 0
    And no error should be raised

  Scenario: Handle view function for invalid market
    When I query position size for an invalid market address
    Then the position size should be 0
    And no error should be raised

  Scenario: View function errors on invalid node
    Given the fullnode URL is incorrect
    When I attempt to query a view function
    Then I should receive a NetworkError
    And the error should indicate the connection failed

  Scenario: Compare view function with API data
    Given I have a position with size 1.0 BTC
    When I query the position size via view function
    And I query the position via REST API
    Then both results should match
    And the view function may be more current

  Scenario: Query multiple positions efficiently
    Given I have positions in 5 markets
    When I query each position size via view function
    Then all queries should complete
    And the total time should be less than querying via REST API

  Scenario: View function for market configuration
    Given I have a market address
    When I query the market configuration via view function
    Then I should receive the market parameters
    And the parameters should match the REST API data

  Scenario: Query subaccount creation
    Given I have a primary account address
    When I calculate the derived subaccount address
    And I query if the subaccount exists via view function
    Then the result should indicate if the subaccount has been created

  Scenario: View function respects compat version
    Given the SDK uses compat version "v0.4"
    When I derive the primary subaccount address
    Then the derivation should use "v0.4" format
    And the address should match other SDK implementations

  Scenario: Query oracle price
    Given I have a market address
    When I query the oracle price via view function
    Then I should receive the current oracle price
    And the price should match the price used in liquidation calculations

  Scenario: Query funding rate
    Given I have a market address
    When I query the current funding rate via view function
    Then I should receive the funding rate in basis points
    And the funding rate should indicate the payment direction

  Scenario: Query liquidation price
    Given I have a subaccount with an open position
    When I query the estimated liquidation price
    Then I should receive the price at which liquidation would occur
    And the calculation should use current on-chain state
