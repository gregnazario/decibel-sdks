Feature: Account Management

  As a trader using the Decibel SDK
  I want to manage my trading account and subaccounts
  So that I can organize my trading activities and monitor my performance

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with sufficient USDC balance

  Scenario: Create a new subaccount
    When I submit a transaction to create a new subaccount
    Then the transaction should be confirmed
    And a new subaccount address should be derived
    And the subaccount should be associated with my primary account

  Scenario: Deposit collateral to primary subaccount
    Given I have a primary subaccount
    And I want to deposit 1000 USDC
    When I submit a deposit transaction for 1000 USDC to my primary subaccount
    Then the transaction should be confirmed
    And the subaccount balance should increase by 1000 USDC

  Scenario: Deposit collateral to specific subaccount
    Given I have a subaccount with address "0x123..."
    And I want to deposit 500 USDC
    When I submit a deposit transaction for 500 USDC to "0x123..."
    Then the transaction should be confirmed
    And the subaccount "0x123..." balance should increase by 500 USDC

  Scenario: Withdraw collateral from subaccount
    Given I have a subaccount with 500 USDC balance
    When I submit a withdrawal transaction for 200 USDC from the subaccount
    Then the transaction should be confirmed
    And the subaccount balance should decrease by 200 USDC
    And my wallet balance should increase by 200 USDC

  Scenario: Withdraw exceeds available balance
    Given I have a subaccount with 100 USDC balance
    When I attempt to withdraw 500 USDC from the subaccount
    Then the transaction should fail
    And an error should indicate insufficient balance

  Scenario: Configure user settings for a market
    Given I want to trade on the "BTC-USD" market
    When I configure my subaccount with:
      | market_addr | 0xabc... |
      | is_cross    | true     |
      | leverage    | 1000     |
    Then the transaction should be confirmed
    And my subaccount should use cross margin for "BTC-USD"
    And my subaccount should have 10x leverage for "BTC-USD"

  Scenario: Configure isolated margin for a market
    Given I want to trade on the "ETH-USD" market with isolated margin
    When I configure my subaccount with:
      | market_addr | 0xdef... |
      | is_cross    | false    |
      | leverage    | 2000     |
    Then the transaction should be confirmed
    And my subaccount should use isolated margin for "ETH-USD"
    And my subaccount should have 20x leverage for "ETH-USD"

  Scenario: Retrieve account overview
    Given I have a subaccount with trading activity
    When I request the account overview for my subaccount
    Then I should receive account performance data including:
      | field                    | description                              |
      | perp_equity_balance      | Total equity balance                     |
      | unrealized_pnl           | Unrealized profit and loss               |
      | unrealized_funding_cost  | Unrealized funding cost                  |
      | cross_margin_ratio       | Cross margin ratio                       |
      | maintenance_margin       | Maintenance margin requirement           |
      | total_margin             | Total margin                             |
    And I should receive optional performance metrics including:
      | field                | description                    |
      | volume               | Trading volume                 |
      | net_deposits         | Net deposits                   |
      | all_time_return      | All-time return percentage     |
      | pnl_90d              | 90-day profit and loss         |
      | sharpe_ratio         | Sharpe ratio                   |
      | max_drawdown         | Maximum drawdown               |
      | weekly_win_rate_12w  | 12-week weekly win rate        |

  Scenario: Retrieve account overview with custom volume window
    When I request the account overview with volume window "7d"
    Then the volume metric should reflect 7-day trading volume
    When I request the account overview with volume window "90d"
    Then the volume metric should reflect 90-day trading volume

  Scenario: Retrieve account overview with performance metrics
    When I request the account overview with performance enabled
    Then the response should include Sharpe ratio
    And the response should include maximum drawdown
    And the response should include weekly win rate

  Scenario: List all subaccounts for an owner
    Given I have created multiple subaccounts
    When I request all subaccounts for my account address
    Then I should receive a list of all my subaccounts
    And each subaccount should have a subaccount address
    And each subaccount should have the primary account address
    And each subaccount should indicate if it is the primary subaccount
    And each subaccount may have a custom label

  Scenario: Rename a subaccount
    Given I have a subaccount with address "0x123..."
    When I rename the subaccount to "My Trading Account"
    Then the subaccount should have the custom label "My Trading Account"

  Scenario: Retrieve fund history
    Given I have made deposits and withdrawals
    When I request my fund history
    Then I should receive a list of fund transactions
    And each transaction should have an amount
    And each transaction should indicate if it was a deposit or withdrawal
    And each transaction should have a timestamp
    And each transaction should have a transaction version

  Scenario: Retrieve paginated fund history
    Given I have more than 10 fund transactions
    When I request fund history with limit 10 and offset 0
    Then I should receive the first 10 transactions
    When I request fund history with limit 10 and offset 10
    Then I should receive the next 10 transactions

  Scenario: Leverage must be in basis points
    When I attempt to configure leverage as 10 instead of 1000
    Then the transaction should use 1000 basis points internally
    And the effective leverage should be 10x

  Scenario: Maximum leverage is capped by market
    Given the "BTC-USD" market has a maximum leverage of 100x
    When I attempt to configure my subaccount with 200x leverage
    Then the transaction should fail
    And an error should indicate the leverage exceeds the maximum

  Scenario: Retrieve USDC decimals for amount conversion
    When I query the USDC decimals
    Then I should receive the decimal precision
    And the decimals should be cached for subsequent queries
