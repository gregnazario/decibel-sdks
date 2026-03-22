Feature: WebSocket Reconnection Without State Loss
  As a trading bot using the Decibel SDK
  I need the WebSocket to auto-reconnect and restore state
  So that I never trade on stale data after a network disruption

  Background:
    Given a WebSocketManager connected to "wss://api.decibel.trade/ws"
    And the bot has active subscriptions:
      | topic                       |
      | userPositions:0xaaa1        |
      | userOpenOrders:0xaaa1       |
      | marketPrice:BTC-USD         |
      | marketDepth:BTC-USD:1       |
    And a PositionStateManager with current positions

  # --- Auto-reconnect with backoff ---

  Scenario: WebSocket disconnects and auto-reconnects with exponential backoff
    Given the WebSocket is connected and receiving data
    When the WebSocket connection drops unexpectedly
    Then is_connected returns False
    And the first reconnection attempt occurs after 1.0 seconds
    When the first reconnect attempt fails
    Then the second attempt occurs after 2.0 seconds
    When the second reconnect attempt succeeds
    Then is_connected returns True
    And the reconnect delay is reset to 1.0 seconds

  # --- Subscription restoration ---

  Scenario: Subscriptions are restored after reconnection
    Given the WebSocket was subscribed to 4 topics before disconnect
    When the WebSocket disconnects and reconnects
    Then the manager automatically re-subscribes to:
      | topic                       |
      | userPositions:0xaaa1        |
      | userOpenOrders:0xaaa1       |
      | marketPrice:BTC-USD         |
      | marketDepth:BTC-USD:1       |
    And position updates resume flowing to the callback
    And price updates resume flowing to the callback

  # --- REST re-sync ---

  Scenario: REST re-sync fills state gap after reconnection
    Given the WebSocket was disconnected for 3 seconds
    And during the gap a fill occurred: order "exch-42" filled 0.5 BTC at 60100.0
    When the WebSocket reconnects
    And the bot triggers a REST re-sync:
      | endpoint                   | result                                   |
      | get_positions("0xaaa1")    | BTC-USD size changed from 2.0 to 2.5     |
      | get_open_orders("0xaaa1")  | order "exch-42" no longer in open orders  |
    Then the position manager has BTC-USD size 2.5
    And order "exch-42" is marked as FILLED in the tracker
    And the state is consistent with on-chain truth

  # --- Gap detection flag ---

  Scenario: gap_detected flag is set during re-sync and cleared after
    When the WebSocket disconnects
    Then the PositionStateManager's gap_detected is True
    When the REST re-sync completes for positions and orders
    And notify_resync_complete() is called
    Then gap_detected is False

  # --- Trading pause on disconnect ---

  Scenario: Bot detects is_connected is False and pauses trading
    Given the bot is running a trading loop that checks is_connected before each cycle
    When the WebSocket disconnects
    Then is_connected returns False
    And the bot skips order placement with log "WS disconnected, pausing trading"
    And no new orders are submitted while is_connected is False

  # --- Full recovery flow ---

  Scenario: Bot resumes trading after reconnection and re-sync complete
    Given the WebSocket was disconnected for 4 seconds
    When the WebSocket reconnects successfully
    And the bot performs REST re-sync:
      | call                        | positions_count | open_orders_count |
      | get_positions("0xaaa1")     | 2               | 3                 |
      | get_open_orders("0xaaa1")   | 3               | 3                 |
    And notify_resync_complete() is called
    Then gap_detected is False
    And is_connected is True
    And the bot resumes the trading loop
    And the bot logs "reconnected and re-synced, resuming trading"

  # --- Multiple disconnections ---

  Scenario: Multiple disconnections handled with increasing backoff
    When the WebSocket disconnects for the 1st time
    Then reconnect delay starts at 1.0 seconds
    And the connection is restored after 1 attempt

    When the WebSocket disconnects for the 2nd time within 30 seconds
    Then reconnect delay starts at 1.0 seconds
    When reconnect fails, delay increases to 2.0 seconds
    When reconnect fails again, delay increases to 4.0 seconds
    When reconnect succeeds on the 3rd attempt
    Then the total downtime was approximately 7.0 seconds
    And the reconnect delay is reset to 1.0 seconds

    When the WebSocket disconnects for the 3rd time
    And reconnect keeps failing
    Then the delay caps at 60.0 seconds
    And the bot continues retrying indefinitely
