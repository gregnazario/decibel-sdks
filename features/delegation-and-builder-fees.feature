Feature: Trading Delegation and Builder Fees

  As a trader using the Decibel SDK
  I want to delegate my trading authority and manage builder fees
  So that I can use automated trading strategies and support frontend integrators

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with a funded subaccount

  Scenario: Delegate trading to another account
    Given I have a subaccount at address "0x123..."
    And I want to delegate trading to "0xdelegate..."
    When I delegate trading to "0xdelegate..." for my subaccount
    Then "0xdelegate..." should be able to trade on behalf of my subaccount
    And "0xdelegate..." should not be able to withdraw funds

  Scenario: Delegate trading with expiration
    Given I have a subaccount at address "0x123..."
    When I delegate trading to "0xdelegate..." with expiration in 7 days
    Then the delegation should be valid for 7 days
    And the delegation should expire after 7 days
    And "0xdelegate..." should not be able to trade after expiration

  Scenario: Delegate trading without expiration
    Given I have a subaccount at address "0x123..."
    When I delegate trading to "0xdelegate..." without expiration
    Then the delegation should remain valid indefinitely
    And only I should be able to revoke the delegation

  Scenario: Revoke trading delegation
    Given I have delegated trading to "0xdelegate..." for my subaccount
    When I revoke the delegation from "0xdelegate..."
    Then "0xdelegate..." should no longer be able to trade on my behalf
    And "0xdelegate..." should not be able to place new orders

  Scenario: Retrieve active delegations
    Given I have delegated trading to multiple accounts
    When I request my delegations
    Then I should receive a list of active delegations
    And each delegation should include:
      | field                 | description                    |
      | delegated_account     | Delegated account address      |
      | permission_type       | Type of permissions granted    |
      | expiration_time_s     | Expiration timestamp in seconds |

  Scenario: Delegated account can place orders
    Given I have delegated trading to "0xdelegate..." for my subaccount
    When "0xdelegate..." places an order for my subaccount
    Then the order should be accepted
    And the order should be associated with my subaccount

  Scenario: Delegated account cannot withdraw funds
    Given I have delegated trading to "0xdelegate..." for my subaccount
    When "0xdelegate..." attempts to withdraw from my subaccount
    Then the withdrawal should fail
    And an error should indicate insufficient permissions

  Scenario: Delegated account with expired delegation cannot trade
    Given I delegated trading to "0xdelegate..." with 1-day expiration
    And 1 day has passed
    When "0xdelegate..." attempts to place an order
    Then the order should be rejected
    And an error should indicate the delegation has expired

  Scenario: Approve builder fee for specific builder
    Given I have a subaccount at address "0x123..."
    And I want to trade through a frontend with builder address "0xfeb..."
    When I approve a max builder fee of 50 basis points for "0xfeb..."
    Then orders placed through "0xfeb..." can include up to 50 bps fees
    And the builder will receive fees from my trading activity

  Scenario: Approve builder fee for subaccount
    Given I have multiple subaccounts
    When I approve builder fees for subaccount "0x123..."
    Then the approval should apply only to "0x123..."
    And other subaccounts should not be affected

  Scenario: Place order with approved builder fee
    Given I have approved 10 bps builder fee for "0xfeb..."
    When I place an order with:
      | builder_addr  | 0xfeb... |
      | builder_fee   | 10       |
    Then the order should be accepted
    And "0xfeb..." should receive 10 basis points as a fee

  Scenario: Place order exceeding approved builder fee
    Given I have approved 10 bps builder fee for "0xfeb..."
    When I place an order with:
      | builder_addr  | 0xfeb... |
      | builder_fee   | 50       |
    Then the order should be rejected
    And an error should indicate the fee exceeds the approved maximum

  Scenario: Place order with unapproved builder
    Given I have not approved any builder fees for "0xfeb..."
    When I place an order with:
      | builder_addr  | 0xfeb... |
      | builder_fee   | 10       |
    Then the order should be rejected
    And an error should indicate the builder is not approved

  Scenario: Revoke builder fee approval
    Given I have approved builder fees for "0xfeb..."
    When I revoke the builder fee approval for "0xfeb..."
    Then "0xfeb..." should no longer receive fees
    And future orders through "0xfeb..." should be rejected

  Scenario: Builder fee is deducted from trade proceeds
    Given I have approved 10 bps builder fee for "0xfeb..."
    And I place a buy order for 1 BTC at 50000 USDC
    And the order is filled
    Then the builder fee should be 50 USDC (50000 * 0.001)
    And my trading cost should include the builder fee

  Scenario: Approve different fee levels for different builders
    Given I have two frontend builders
    When I approve 10 bps for "0xfeb..."
    And I approve 20 bps for "0xabc..."
    Then orders through "0xfeb..." can have up to 10 bps fees
    And orders through "0xabc..." can have up to 20 bps fees

  Scenario: Session account delegation
    Given I want to use a session key for trading
    When I delegate trading to my session account
    Then the session account should be able to place orders
    And the session account should have a limited expiration
    And I should be able to revoke the session at any time

  Scenario: Session account order with builder fee
    Given I have delegated trading to my session account
    And I have approved builder fees
    When I place an order using the session account with builder fee
    Then the order should be placed through the session account
    And the builder fee should be applied

  Scenario: Revoke delegation while orders are open
    Given I have delegated trading to "0xdelegate..."
    And "0xdelegate..." has open orders on my subaccount
    When I revoke the delegation
    Then existing open orders should remain active
    And "0xdelegate..." should not be able to place new orders
    And I should still be able to manage the existing orders

  Scenario: Multiple delegations for same subaccount
    Given I have a subaccount
    When I delegate trading to "0xdelegate1..."
    And I delegate trading to "0xdelegate2..."
    Then both delegates should be able to trade on my behalf
    And both delegates should have independent permissions

  Scenario: Builder fee in basis points
    When I approve a builder fee of 100 basis points
    Then the fee should be 1% (100 / 10000)
    When I approve a builder fee of 1000 basis points
    Then the fee should be 10% (1000 / 10000)

  Scenario: Zero builder fee approval
    When I approve 0 basis points for a builder
    Then orders should not include builder fees
    And the builder should receive no compensation
