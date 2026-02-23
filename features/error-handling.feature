Feature: Error Handling

  As a developer using the Decibel SDK
  I want to receive clear and actionable error messages
  So that I can handle failures gracefully in my application

  Background:
    Given I have an initialized Decibel client

  Scenario: Configuration error for missing required field
    When I attempt to create a configuration without a network
    Then I should receive a ConfigurationError
    And the error message should indicate which field is missing

  Scenario: Configuration error for invalid URL
    When I attempt to create a configuration with an invalid fullnode URL
    Then I should receive a ConfigurationError
    And the error message should indicate the URL is invalid

  Scenario: Network error for connection failure
    Given the API server is unreachable
    When I attempt to make a request
    Then I should receive a NetworkError
    And the error should include connection failure details

  Scenario: Network error for timeout
    Given the API server is slow to respond
    And I have configured a request timeout
    When the request exceeds the timeout
    Then I should receive a TimeoutError
    And the error should indicate the operation timed out

  Scenario: API error for 404 Not Found
    When I request a non-existent market with name "INVALID-MARKET"
    Then I should receive an ApiError
    And the error status should be 404
    And the error message should indicate the resource was not found

  Scenario: API error for 400 Bad Request
    When I submit a request with invalid parameters
    Then I should receive an ApiError
    And the error status should be 400
    And the error message should describe the validation issue

  Scenario: API error for 500 Internal Server Error
    Given the API server encounters an internal error
    When I make a request
    Then I should receive an ApiError
    And the error status should be 500
    And the error should include the server error message

  Scenario: API error includes response details
    When I receive an ApiError
    Then the error should include:
      | field       | description                    |
      | status      | HTTP status code                |
      | status_text | HTTP status text                |
      | message     | Error message from server       |

  Scenario: Validation error for malformed JSON
    When the API returns invalid JSON
    Then I should receive a ValidationError
    And the error should indicate the JSON could not be parsed

  Scenario: Validation error for schema mismatch
    When the API returns JSON that doesn't match the expected schema
    Then I should receive a ValidationError
    And the error should indicate which fields are invalid

  Scenario: Transaction error for on-chain failure
    When I submit a transaction that fails on-chain
    Then I should receive a TransactionError
    And the error should include:
      | field            | description                        |
      | transaction_hash | Transaction hash if submitted      |
      | vm_status        | Move VM error status               |
      | message          | Human-readable error message       |

  Scenario: Transaction error for insufficient balance
    Given my account has insufficient USDC balance
    When I attempt to deposit more than my balance
    Then the transaction should fail
    And I should receive a TransactionError
    And the error should indicate insufficient funds

  Scenario: Transaction error for insufficient gas
    When I submit a transaction without enough gas
    Then the transaction should fail
    And I should receive a TransactionError
    And the error should indicate insufficient gas

  Scenario: Simulation error for transaction simulation
    Given transaction simulation is enabled
    When I attempt to simulate a transaction that would fail
    Then I should receive a SimulationError
    And the error should include the simulation failure reason

  Scenario: Signing error for invalid private key
    Given I attempt to create a write client with an invalid private key
    Then I should receive a SigningError
    And the error should indicate the key format is invalid

  Scenario: Signing error for signature generation failure
    When the signing process fails
    Then I should receive a SigningError
    And the error should indicate the signature could not be generated

  Scenario: Gas estimation error
    When the gas estimation fails
    Then I should receive a GasEstimationError
    And the error should include the estimation failure details

  Scenario: WebSocket error for connection failure
    When I attempt to connect to the WebSocket server
    And the server is unreachable
    Then I should receive a WebSocketError
    And the error should indicate the connection failed

  Scenario: WebSocket error for subscription failure
    Given I have an active WebSocket connection
    When I attempt to subscribe to an invalid channel
    Then I should receive a WebSocketError
    And the error should indicate the subscription failed

  Scenario: WebSocket auto-reconnect on error
    Given I have an active WebSocket connection
    When the connection is lost
    Then the client should attempt to reconnect
    And reconnection attempts should use exponential backoff

  Scenario: Serialization error for request encoding
    When I attempt to serialize a request with invalid data
    Then I should receive a SerializationError
    And the error should indicate the data could not be serialized

  Scenario: Serialization error for response decoding
    When I receive a response that cannot be deserialized
    Then I should receive a SerializationError
    And the error should indicate the data could not be deserialized

  Scenario: Timeout error for long-running request
    Given I have configured a 30-second timeout
    When a request takes longer than 30 seconds
    Then I should receive a TimeoutError
    And the error should indicate the operation timed out

  Scenario: Timeout error for transaction confirmation
    Given I submit a transaction
    And the transaction is not confirmed within the timeout period
    Then I should receive a TimeoutError
    And the error should indicate the transaction was not confirmed

  Scenario: Error provides stack trace for debugging
    When I receive any SDK error
    And the SDK is in debug mode
    Then the error should include a stack trace
    And the stack trace should help identify the error source

  Scenario: Error is retryable for transient failures
    When I receive a NetworkError
    Then the error should indicate if it is retryable
    And I should be able to retry the operation

  Scenario: Error is not retryable for permanent failures
    When I receive an ApiError with status 401
    Then the error should indicate it is not retryable
    And retrying should return the same error

  Scenario: Custom error callback for WebSocket errors
    Given I have registered an error callback
    When a WebSocket error occurs
    Then the error callback should be invoked
    And the callback should receive the error details

  Scenario: Handle multiple concurrent errors
    Given I have multiple requests in flight
    When several requests fail simultaneously
    Then each request should return its appropriate error
    And errors should not be confused with each other

  Scenario: Error for unsupported market operation
    When I attempt an operation that is not supported for a market
    Then I should receive an appropriate error
    And the error should explain why the operation is not supported

  Scenario: Error for order below minimum size
    Given the market minimum order size is 0.001
    When I attempt to place an order with size 0.0001
    Then I should receive an error
    And the error should indicate the order size is below minimum

  Scenario: Error for invalid leverage setting
    Given the market maximum leverage is 100x
    When I attempt to set my leverage to 200x
    Then I should receive an error
    And the error should indicate the leverage exceeds maximum

  Scenario: Error for insufficient margin
    Given my account has insufficient margin
    When I attempt to place a large order
    Then I should receive an error
    And the error should indicate insufficient margin

  Scenario: Gas station error
    Given I am using gas station for fee payment
    When the gas station service is unavailable
    Then I should receive an error
    And the error should indicate the gas station is unavailable
    And I should have the option to retry without gas station
