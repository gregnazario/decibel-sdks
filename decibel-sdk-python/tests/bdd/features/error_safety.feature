Feature: Error Position Safety Classification
  As a trading bot using the Decibel SDK
  I need every error to carry a position_safety classification
  So that I know whether my local state is still trustworthy after a failure

  Background:
    Given the SDK error hierarchy with PositionSafety levels: SAFE, UNKNOWN, STALE, CRITICAL

  # --- SAFE errors: no state change occurred ---

  Scenario: Validation error is SAFE — bot continues trading
    When the bot sends an order with size 0.0001 below the min_size of 0.001
    Then a ValidationError is raised with field "size" and constraint "min_size=0.001"
    And the error's position_safety is SAFE
    And the bot can continue trading without re-syncing state
    And is_retryable is False

  Scenario: Rate limit error is SAFE — bot waits and retries
    When the bot exceeds the API rate limit
    Then a RateLimitError is raised with retry_after_ms 500
    And the error's position_safety is SAFE
    And is_retryable is True
    And the bot sleeps for 500 milliseconds before retrying
    And no state re-sync is needed

  # --- UNKNOWN errors: state may have changed ---

  Scenario: Transaction submission timeout is UNKNOWN — bot re-syncs state
    When the bot places an order but the HTTP request times out after 30 seconds
    Then a SubmissionError is raised with message "broadcast timeout"
    And the error's position_safety is UNKNOWN
    And is_retryable is True
    And needs_resync is True
    And the bot must call get_positions() and get_open_orders() to reconcile
    And the bot must not place new orders until re-sync is complete

  Scenario: Cancel failure is UNKNOWN — bot checks if order is still live
    When the bot cancels order "exch-77" but receives a VmError
    Then the VmError has position_safety UNKNOWN
    And the VmError has tx_hash "0xdef456"
    And the VmError has vm_status "MOVE_ABORT(0x1::coin, 10)"
    And needs_resync is True
    And the bot fetches open orders via REST to check if "exch-77" is still live
    And if "exch-77" is still in open_orders, the bot retries the cancel

  # --- CRITICAL errors: protective orders may have failed ---

  Scenario: Stop-loss placement failure is CRITICAL — bot takes emergency action
    Given the bot has a BTC-USD long position of 2.0 BTC at 60000.0
    When the bot attempts to place a stop-loss at 57000.0
    And the placement fails with a CriticalTradingError
    Then the error's position_safety is CRITICAL
    And the error's affected_market is "BTC-USD"
    And the error's affected_order_ids includes the failed SL order
    And is_critical is True
    And the bot initiates emergency close: market sell 2.0 BTC on "BTC-USD"

  Scenario: Cancel-all partial failure is CRITICAL — bot checks for residual exposure
    Given the bot has 10 open quotes on "BTC-USD"
    When the bot calls cancel_all but only 7 of 10 cancels succeed
    Then a CriticalTradingError is raised
    And the error's affected_market is "BTC-USD"
    And the error's affected_order_ids contains the 3 uncancelled order IDs
    And the bot fetches open_orders via REST
    And the bot individually cancels each residual order
    And if any residual cancel fails, the bot logs "CRITICAL: residual exposure on BTC-USD"

  # --- STALE errors: local state is outdated ---

  Scenario: WebSocket disconnect longer than 5 seconds is STALE — bot re-syncs before continuing
    When the WebSocket disconnects for 6000 milliseconds
    Then a WebSocketError is raised with disconnect_duration_ms 6000
    And the error's position_safety is STALE
    And needs_resync is True
    And the bot performs a full REST re-sync:
      | call                     |
      | get_positions("0xaaa1")  |
      | get_open_orders("0xaaa1")|
      | get_account_overview()   |
    And the bot does not place new orders until the re-sync completes
    And gap_detected is cleared after notify_resync_complete()
