Feature: SDK Configuration and Initialization

  As a developer using the Decibel SDK
  I want to configure and initialize the SDK clients
  So that I can interact with the Decibel perpetual futures exchange

  Scenario: Initialize read client with mainnet configuration
    Given I have the Decibel SDK installed
    When I create a read client using the mainnet preset configuration
    Then the client should be configured for the mainnet environment
    And the client should connect to the mainnet REST API
    And the client should connect to the mainnet WebSocket API

  Scenario: Initialize read client with testnet configuration
    Given I have the Decibel SDK installed
    When I create a read client using the testnet preset configuration
    Then the client should be configured for the testnet environment
    And the client should connect to the testnet REST API
    And the client should connect to the testnet WebSocket API

  Scenario: Initialize read client with custom configuration
    Given I have the Decibel SDK installed
    And I have a custom network configuration with:
      | fullnode_url        | https://custom.fullnode.com |
      | trading_http_url    | https://custom.api.com       |
      | trading_ws_url      | wss://custom.ws.com          |
    When I create a read client with the custom configuration
    Then the client should use the provided fullnode URL
    And the client should use the provided trading HTTP URL
    And the client should use the provided trading WebSocket URL

  Scenario: Initialize read client with API key
    Given I have the Decibel SDK installed
    And I have a valid API key for rate limit increases
    When I create a read client with the API key
    Then the client should include the API key in REST requests
    And the client should include the API key in WebSocket connections

  Scenario: Initialize write client with Ed25519 account
    Given I have the Decibel SDK installed
    And I have an Ed25519 keypair with a private key
    When I create a write client with the account
    Then the write client should be able to sign transactions
    And the write client should use the account address as the primary account

  Scenario: Initialize write client with gas station enabled
    Given I have the Decibel SDK installed
    And I have a valid gas station URL and API key
    And I have an Ed25519 keypair
    When I create a write client with gas station enabled
    Then transactions should be submitted through the gas station
    And the account should not be charged gas fees

  Scenario: Initialize write client with gas station disabled
    Given I have the Decibel SDK installed
    And I have an Ed25519 keypair
    When I create a write client with gas station disabled
    Then transactions should be submitted directly to the Aptos network
    And the account should be charged gas fees

  Scenario: Initialize write client with custom gas price manager
    Given I have the Decibel SDK installed
    And I have an Ed25519 keypair
    And I have a custom gas price manager with a 1.5x multiplier
    When I create a write client with the custom gas price manager
    Then the gas price manager should be used for transaction gas estimates
    And gas estimates should be multiplied by 1.5

  Scenario: Initialize write client with simulation disabled
    Given I have the Decibel SDK installed
    And I have an Ed25519 keypair
    When I create a write client with simulation disabled
    Then transactions should be built without prior simulation
    And transactions should use estimated gas amounts

  Scenario: Validate configuration requires all mandatory fields
    Given I have the Decibel SDK installed
    When I attempt to create a configuration missing the network
    Then a configuration error should be raised
    When I attempt to create a configuration missing the fullnode URL
    Then a configuration error should be raised
    When I attempt to create a configuration missing the trading HTTP URL
    Then a configuration error should be raised
    When I attempt to create a configuration missing the trading WebSocket URL
    Then a configuration error should be raised

  Scenario: Write client requires valid Ed25519 account
    Given I have the Decibel SDK installed
    And I have a valid configuration
    When I attempt to create a write client without an account
    Then a configuration error should be raised

  Scenario: Configuration includes deployment addresses
    Given I have a valid SDK configuration
    Then the configuration should include the package address
    And the configuration should include the USDC token address
    And the configuration should include the test collateral address
    And the configuration should include the perp engine global address

  Scenario: Configuration includes compatibility version
    Given I have a valid SDK configuration
    Then the configuration should include the compatibility version
    And the compatibility version should be "v0.4"

  Scenario: Auto-detect chain ID when not provided
    Given I have a valid SDK configuration without a chain ID
    When I initialize a client with the configuration
    Then the SDK should auto-detect the chain ID from the network
