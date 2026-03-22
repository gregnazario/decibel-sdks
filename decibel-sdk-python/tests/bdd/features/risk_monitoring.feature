Feature: Risk Monitoring for Trading Bots
  As a trading bot using the Decibel SDK
  I need real-time risk metrics computed from local state
  So that I can detect dangerous conditions and react before liquidation

  Background:
    Given a PositionStateManager with account overview:
      | perp_equity_balance | total_margin | maintenance_margin |
      | 100000.0            | 20000.0      | 5000.0             |
    And subaccount "0xaaa1" is active

  # --- Liquidation distance ---

  Scenario: Liquidation distance computed for a long position
    Given a BTC-USD long position:
      | size | entry_price | estimated_liquidation_price |
      | 2.0  | 60000.0     | 55000.0                     |
    And the current BTC-USD mark price is 60000.0
    When the bot computes liquidation distance for BTC-USD
    Then the liquidation distance_pct is 8.33%
    # (60000.0 - 55000.0) / 60000.0 * 100 = 8.33%
    And the liquidation distance_usd is 10000.0
    # abs(60000 - 55000) * abs(size) = 5000 * 2.0 = 10000.0

  Scenario: Liquidation distance computed for a short position
    Given a BTC-USD short position:
      | size | entry_price | estimated_liquidation_price |
      | -1.5 | 60000.0     | 65000.0                     |
    And the current BTC-USD mark price is 60000.0
    When the bot computes liquidation distance for BTC-USD
    Then the liquidation distance_pct is 8.33%
    # (65000.0 - 60000.0) / 60000.0 * 100 = 8.33%
    And the liquidation distance_usd is 7500.0
    # abs(65000 - 60000) * abs(size) = 5000 * 1.5 = 7500.0

  # --- Margin warnings ---
  # margin_usage_pct returns a 0.0-1.0 fraction (0.8 = 80%)
  # margin_warning returns lowercase strings: "ok", "warn", "critical"

  Scenario: Margin warning fires at 80% usage
    Given the account overview has:
      | perp_equity_balance | total_margin |
      | 100000.0            | 80000.0      |
    When the bot checks margin_usage_pct("0xaaa1")
    Then margin_usage_pct is 0.8
    And the margin warning level is "warn"

  Scenario: Margin warning escalates to critical at 90%
    Given the account overview has:
      | perp_equity_balance | total_margin |
      | 100000.0            | 92000.0      |
    When the bot checks margin_usage_pct("0xaaa1")
    Then margin_usage_pct is 0.92
    And the margin warning level is "critical"

  # --- Funding accrual ---

  Scenario: Funding accrual rate computed for a position
    Given a BTC-USD long position with size 2.0
    And the BTC-USD mark price is 60000.0
    And the BTC-USD funding_rate_bps is 0.5
    And funding is positive (longs pay shorts)
    When the bot computes hourly funding cost for BTC-USD
    Then the hourly funding cost is 6.0 USD
    # notional = abs(2.0) * 60000.0 = 120000.0
    # hourly cost = 120000.0 * 0.5 / 10000 = 6.0

  # --- Unprotected position detection ---
  # positions_without_tp_sl() flags positions missing BOTH TP and SL

  Scenario: Unprotected positions identified when missing both TP and SL
    Given the following positions:
      | market  | size | tp_order_id | sl_order_id |
      | BTC-USD | 2.0  | tp-001      | sl-001      |
      | ETH-USD | -5.0 |             |             |
      | SOL-USD | 10.0 |             | sl-003      |
    When the bot checks for unprotected positions
    Then ETH-USD is flagged as unprotected (missing both TP and SL)
    And SOL-USD is NOT flagged (has SL, only missing TP)
    And BTC-USD is fully protected (has both TP and SL)

  # --- Risk summary ---

  Scenario: Risk summary provides all metrics in one call
    Given a BTC-USD long position with size 2.0 and entry_price 60000.0 and liquidation_price 55000.0
    And the BTC-USD mark price is 60000.0 with funding_rate_bps 0.5
    And the account overview has equity 100000.0 and total_margin 20000.0
    When the bot requests risk_summary("0xaaa1")
    Then the risk summary contains:
      | key                          | value    |
      | margin_warning               | ok       |
      | gross_exposure_usd           | 120000.0 |
      | net_exposure_usd             | 120000.0 |
      | total_funding_accrual_rate   | 6.0      |
      | unprotected_exposure_usd     | 0.0      |
      | min_liquidation_distance_pct | 8.33     |

  # --- Automated risk reactions ---
  # These scenarios describe bot behavior, not SDK API directly

  Scenario: Bot pauses trading when margin is critical
    Given the account overview has:
      | perp_equity_balance | total_margin |
      | 100000.0            | 95000.0      |
    When the bot evaluates risk and margin_usage_pct is 0.95
    And margin_warning returns "critical"
    Then the bot sets trading_paused to True
    And no new orders are placed until margin_warning returns "ok" or "warn"

  Scenario: Bot adds TP/SL to unprotected positions
    Given a BTC-USD long position with size 2.0 and entry_price 60000.0
    And the BTC-USD position has no TP and no SL orders
    When the bot detects the unprotected position via positions_without_tp_sl()
    Then the bot places a stop-loss at 57000.0 (5% below entry)
    And the bot places a take-profit at 66000.0 (10% above entry)
    And the BTC-USD position now has both tp_order_id and sl_order_id set
