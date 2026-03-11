Feature: Vaults

  As a trader using the Decibel SDK
  I want to create and manage vaults or participate in existing vaults
  So that I can earn yield from my capital or follow skilled traders

  Background:
    Given I have an initialized Decibel write client
    And I have an Ed25519 account with sufficient USDC balance

  Scenario: Create a new vault
    When I create a vault with:
      | vault_name                | My Trading Vault         |
      | vault_description         | A high-frequency strategy |
      | vault_share_symbol        | MTV                      |
      | fee_bps                   | 1000                     |
      | fee_interval_s            | 86400                    |
      | contribution_lockup_s     | 604800                   |
      | initial_funding           | 10000 USDC               |
      | accepts_contributions     | true                     |
      | delegate_to_creator       | true                     |
    Then the vault should be created
    And I should receive the vault address
    And the vault should be funded with 10000 USDC
    And the vault should have a 10% fee (1000 bps)
    And the vault should charge fees daily (86400s)
    And contributions should be locked for 7 days (604800s)
    And trading should be delegated to me as the creator

  Scenario: Create a vault with social links
    When I create a vault with:
      | vault_name              | Social Vault         |
      | vault_share_symbol      | SOCL                 |
      | vault_social_links      | ["twitter.com/vault"] |
      | fee_bps                 | 500                  |
      | fee_interval_s          | 86400                |
      | contribution_lockup_s   | 0                    |
      | initial_funding         | 5000 USDC            |
      | accepts_contributions   | true                 |
      | delegate_to_creator     | false                |
    Then the vault should have the associated social links

  Scenario: Create a vault with custom share metadata
    When I create a vault with:
      | vault_name                  | Branded Vault            |
      | vault_share_symbol          | BRND                     |
      | vault_share_icon_uri        | https://example.com/icon |
      | vault_share_project_uri     | https://example.com      |
      | fee_bps                     | 1500                     |
      | fee_interval_s              | 86400                    |
      | contribution_lockup_s       | 2592000                  |
      | initial_funding             | 50000 USDC               |
      | accepts_contributions       | false                    |
      | delegate_to_creator         | true                     |
    Then the vault share token should have the custom icon URI
    And the vault share token should have the custom project URI

  Scenario: Activate a vault
    Given I have created a vault that is not yet active
    When I activate the vault
    Then the vault should become active
    And the vault should accept deposits from other users

  Scenario: Contribute to an active vault
    Given there is an active vault at address "0xabc..."
    And I want to contribute 1000 USDC
    When I deposit 1000 USDC to the vault
    Then the vault should issue me shares
    And my share count should reflect the contribution
    And the vault TVL should increase by 1000 USDC

  Scenario: Redeem shares from a vault
    Given I own shares in a vault at address "0xabc..."
    And I own 100 shares
    When I redeem 50 shares from the vault
    Then I should receive the proportional value of the shares
    And my remaining share count should be 50
    And the vault TVL should decrease accordingly

  Scenario: Redeem all shares from a vault
    Given I own 100 shares in a vault
    When I redeem all 100 shares
    Then I should receive the full value of my shares
    And my share count should be 0
    And I should have no remaining ownership in the vault

  Scenario: Contribution lockup prevents early withdrawal
    Given a vault has a 7-day contribution lockup
    And I contributed to the vault 1 day ago
    When I attempt to redeem my shares
    Then the redemption should fail
    And an error should indicate the lockup has not expired

  Scenario: Contribute after lockup expires
    Given a vault has a 7-day contribution lockup
    And I contributed to the vault 8 days ago
    When I redeem my shares
    Then the redemption should succeed

  Scenario: Delegate vault DEX actions
    Given I have created a vault
    When I delegate DEX actions to trader account "0xtrader..."
    Then the trader should be able to trade on behalf of the vault
    And the trader should not be able to withdraw vault funds

  Scenario: Delegate vault with expiration
    Given I have created a vault
    When I delegate DEX actions to trader "0xtrader..." with expiration in 30 days
    Then the delegation should expire in 30 days
    And the trader should lose trading permissions after expiration

  Scenario: Revoke vault delegation
    Given I have delegated vault trading to "0xtrader..."
    When I revoke the delegation
    Then the trader should no longer be able to trade on behalf of the vault

  Scenario: Retrieve all vaults
    When I request all vaults
    Then I should receive a list of vaults
    And each vault should include:
      | field                | description                        |
      | address              | Vault address                      |
      | name                 | Vault name                         |
      | description          | Vault description                  |
      | manager              | Manager account address            |
      | status               | Vault status                       |
      | created_at           | Creation timestamp                 |
      | tvl                  | Total value locked                 |
      | volume               | Trading volume                     |
      | all_time_pnl         | All-time profit and loss           |
      | all_time_return      | All-time return percentage         |
      | sharpe_ratio         | Sharpe ratio                       |
      | max_drawdown         | Maximum drawdown                   |
      | profit_share         | Profit share percentage            |
      | depositors           | Number of depositors               |
      | vault_type           | User or Protocol vault             |

  Scenario: Retrieve vaults with pagination
    Given there are more than 20 vaults
    When I request vaults with limit 20 and offset 0
    Then I should receive the first 20 vaults
    When I request vaults with limit 20 and offset 20
    Then I should receive the next 20 vaults

  Scenario: Retrieve vaults with sorting
    Given there are multiple vaults
    When I request vaults sorted by TVL in descending order
    Then vaults should be ordered from highest to lowest TVL
    When I request vaults sorted by sharpe ratio in descending order
    Then vaults should be ordered from highest to lowest Sharpe ratio

  Scenario: Retrieve vaults with search
    Given there are multiple vaults
    When I search for vaults with term "Bitcoin"
    Then I should only receive vaults matching "Bitcoin"

  Scenario: Retrieve user-owned vaults
    Given I have created multiple vaults
    When I request my owned vaults
    Then I should receive only vaults I manage
    And each vault should include:
      | field                | description                        |
      | vault_address        | Vault address                      |
      | vault_name           | Vault name                         |
      | vault_share_symbol   | Share token symbol                 |
      | status               | Vault status                       |
      | age_days             | Age in days                        |
      | num_managers         | Number of managers                 |
      | tvl                  | Total value locked                 |
      | apr                  | Annual percentage rate             |
      | manager_equity       | Manager equity                     |
      | manager_stake        | Manager stake percentage           |

  Scenario: Retrieve user performance on vaults
    Given I have contributed to multiple vaults
    When I request my performance on vaults
    Then I should receive my performance data for each vault
    And the data should include my contributions
    And the data should include my earnings

  Scenario: Retrieve vault share price
    Given there is a vault at address "0xabc..."
    When I request the share price for the vault
    Then I should receive the current share price
    And the share price should reflect the vault's NAV

  Scenario: Vault accepts contributions setting
    Given I created a vault with accepts_contributions set to false
    When another user attempts to contribute
    Then the contribution should be rejected
    And an error should indicate the vault is not accepting contributions

  Scenario: Vault that accepts contributions
    Given I created a vault with accepts_contributions set to true
    When another user attempts to contribute
    Then the contribution should be accepted
    And the user should receive vault shares

  Scenario: Manager stake in vault
    Given I created a vault with initial funding of 10000 USDC
    And another user contributed 90000 USDC
    When I request my owned vaults
    Then my manager_stake should be approximately 10%
    And the manager_equity should be 10000 USDC

  Scenario: Vault fee structure
    Given I created a vault with fee_bps of 1000 (10%)
    And the vault_interval_s is 86400 (daily)
    And the vault has generated profit
    When the fee interval elapses
    Then 10% of the profit should be allocated to the manager
