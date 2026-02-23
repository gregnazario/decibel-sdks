Feature: Analytics and Leaderboard

  As a trader using the Decibel SDK
  I want to access analytics and leaderboard data
  So that I can track my performance and compare with other traders

  Background:
    Given I have an initialized Decibel read client

  Scenario: Retrieve the trading leaderboard
    When I request the leaderboard
    Then I should receive a list of top traders
    And each trader should include:
      | field         | description                     |
      | rank          | Leaderboard rank                |
      | account       | Account address                 |
      | account_value | Total account value             |
      | realized_pnl  | Realized profit and loss        |
      | roi           | Return on investment percentage |
      | volume        | Trading volume                  |

  Scenario: Retrieve leaderboard with pagination
    Given there are more than 50 traders on the leaderboard
    When I request the leaderboard with limit 50 and offset 0
    Then I should receive the top 50 traders
    When I request the leaderboard with limit 50 and offset 50
    Then I should receive traders ranked 51-100

  Scenario: Retrieve leaderboard sorted by different metrics
    When I request the leaderboard sorted by account_value in descending order
    Then traders should be ordered by highest account value first
    When I request the leaderboard sorted by volume in descending order
    Then traders should be ordered by highest volume first
    When I request the leaderboard sorted by roi in descending order
    Then traders should be ordered by highest ROI first

  Scenario: Retrieve leaderboard with ascending sort
    When I request the leaderboard sorted by account_value in ascending order
    Then traders should be ordered by lowest account value first

  Scenario: Search leaderboard by account address
    Given I want to find a specific trader's rank
    When I search the leaderboard for account address "0x123..."
    Then I should receive the rank and data for that account
    If the account is not on the leaderboard
    Then I should receive an empty result

  Scenario: Retrieve leaderboard with limit
    When I request the leaderboard with limit 10
    Then I should receive at most 10 traders
    And the response should include the total count of all traders

  Scenario: Retrieve portfolio chart data
    Given I have a subaccount with trading history
    When I request portfolio chart data for my subaccount
    Then I should receive historical portfolio value data points
    And each data point should include:
      | field     | description                  |
      | timestamp | Data point timestamp         |
      | value     | Portfolio value at timestamp |

  Scenario: Retrieve portfolio chart with custom interval
    When I request portfolio chart data with interval "1h"
    Then data points should be spaced approximately 1 hour apart
    When I request portfolio chart data with interval "1d"
    Then data points should be spaced approximately 1 day apart

  Scenario: Retrieve account performance metrics
    Given I have a subaccount with trading activity
    When I request account overview with performance enabled
    Then I should receive advanced performance metrics including:
      | metric                | description                      |
      | all_time_return       | All-time return percentage       |
      | pnl_90d               | 90-day profit and loss           |
      | sharpe_ratio          | Sharpe ratio                     |
      | max_drawdown          | Maximum drawdown percentage      |
      | weekly_win_rate_12w   | Win rate over 12 weeks           |
      | average_cash_position | Average cash position            |
      | average_leverage      | Average leverage used            |

  Scenario: Retrieve performance with different volume windows
    When I request account overview with volume_window "7d"
    Then the volume metric should reflect 7-day trading volume
    When I request account overview with volume_window "30d"
    Then the volume metric should reflect 30-day trading volume
    When I request account overview with volume_window "90d"
    Then the volume metric should reflect 90-day trading volume

  Scenario: Retrieve trade history with performance data
    Given I have executed multiple trades
    When I request my trade history
    Then each trade should include performance information:
      | field                   | description                      |
      | action                  | Trade action (Open/Close/Net)    |
      | size                    | Trade size                       |
      | price                   | Trade price                      |
      | is_profit               | Whether trade was profitable     |
      | realized_pnl_amount     | Realized profit or loss          |
      | is_funding_positive     | Funding payment direction        |
      | realized_funding_amount | Funding payment amount           |
      | is_rebate               | Whether fee was a rebate         |
      | fee_amount              | Trading fee amount               |

  Scenario: Calculate win rate from trade history
    Given I have executed 100 trades
    And 60 of the trades were profitable
    When I request account overview performance metrics
    Then the win rate should be approximately 60%

  Scenario: Retrieve liquidation fees paid
    Given I have been liquidated in the past
    When I request my account overview
    Then the overview should include liquidation_fees_paid
    And the overview should include liquidation_losses

  Scenario: Retrieve realized PnL
    Given I have closed multiple positions
    When I request my account overview
    Then the overview should include realized_pnl
    And realized_pnl should be the sum of all closed position PnL

  Scenario: Portfolio chart data chronological order
    When I request portfolio chart data
    Then data points should be ordered by timestamp ascending
    And each timestamp should be later than the previous

  Scenario: Leaderboard excludes accounts with no activity
    Given there are accounts with no trading activity
    When I request the leaderboard
    Then inactive accounts should not appear on the leaderboard

  Scenario: Leaderboard updates in real-time
    Given I am viewing the leaderboard
    When a trader makes a significant profit
    Then their rank should update on the next leaderboard query

  Scenario: Retrieve average cash position metric
    Given I have been trading for 30 days
    When I request account overview with performance metrics
    Then the average_cash_position should reflect my average uninvested capital

  Scenario: Retrieve average leverage metric
    Given I have traded with varying leverage
    When I request account overview with performance metrics
    Then the average_leverage should reflect my average leverage usage

  Scenario: Sharpe ratio calculation
    Given I have positive returns with low volatility
    When I request account overview with performance metrics
    Then the sharpe_ratio should be relatively high
    Given I have highly volatile returns
    When I request account overview with performance metrics
    Then the sharpe_ratio should be relatively low

  Scenario: Max drawdown represents worst loss
    Given my account reached a peak of 10000 USDC
    And later declined to 7000 USDC before recovering
    When I request account overview with performance metrics
    Then the max_drawdown should be approximately 30%

  Scenario: Weekly win rate calculation
    Given I have 12 weeks of trading history
    And I was profitable in 9 of those weeks
    When I request account overview with performance metrics
    Then the weekly_win_rate_12w should be approximately 75%

  Scenario: Portfolio value includes unrealized PnL
    Given I have an open position with unrealized profit
    When I request portfolio chart data
    Then the current portfolio value should include unrealized PnL

  Scenario: Network deposits affect net deposits metric
    Given I started with 0 USDC
    And I deposited 10000 USDC
    And I withdrew 2000 USDC
    When I request my account overview
    Then the net_deposits should be 8000 USDC
