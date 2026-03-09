"""Account-related data models."""

from pydantic import BaseModel, Field

from .enums import TradeAction


class AccountOverview(BaseModel):
    """Comprehensive account information.

    Attributes:
        perp_equity_balance: Perpetual equity balance
        unrealized_pnl: Unrealized profit/loss
        unrealized_funding_cost: Unrealized funding cost
        cross_margin_ratio: Cross margin ratio
        maintenance_margin: Maintenance margin
        cross_account_leverage_ratio: Cross account leverage
        volume: Trading volume (per window)
        net_deposits: Net deposits
        all_time_return: All-time return
        pnl_90d: 90-day PnL
        sharpe_ratio: Sharpe ratio
        max_drawdown: Maximum drawdown
        weekly_win_rate_12w: 12-week weekly win rate
        average_cash_position: Average cash position
        average_leverage: Average leverage
        cross_account_position: Cross account position value
        total_margin: Total margin
        usdc_cross_withdrawable_balance: USDC cross withdrawable
        usdc_isolated_withdrawable_balance: USDC isolated withdrawable
        realized_pnl: Realized PnL
        liquidation_fees_paid: Liquidation fees paid
        liquidation_losses: Liquidation losses
    """

    perp_equity_balance: float
    unrealized_pnl: float
    unrealized_funding_cost: float
    cross_margin_ratio: float
    maintenance_margin: float
    cross_account_position: float
    total_margin: float
    usdc_cross_withdrawable_balance: float
    usdc_isolated_withdrawable_balance: float
    cross_account_leverage_ratio: float | None = None
    volume: float | None = None
    net_deposits: float | None = None
    all_time_return: float | None = None
    pnl_90d: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    weekly_win_rate_12w: float | None = None
    average_cash_position: float | None = None
    average_leverage: float | None = None
    realized_pnl: float | None = None
    liquidation_fees_paid: float | None = None
    liquidation_losses: float | None = None


class UserPosition(BaseModel):
    """User's position in a market.

    Attributes:
        market: Market address
        user: Subaccount address
        size: Position size (negative = short)
        user_leverage: User leverage setting
        entry_price: Entry price
        is_isolated: Whether position is isolated margin
        unrealized_funding: Unrealized funding
        estimated_liquidation_price: Estimated liquidation price
        tp_order_id: Take-profit order ID
        tp_trigger_price: Take-profit trigger price
        tp_limit_price: Take-profit limit price
        sl_order_id: Stop-loss order ID
        sl_trigger_price: Stop-loss trigger price
        sl_limit_price: Stop-loss limit price
        has_fixed_sized_tpsls: Whether TP/SL has fixed sizes
    """

    market: str
    user: str
    size: float
    user_leverage: float
    entry_price: float
    is_isolated: bool
    unrealized_funding: float
    estimated_liquidation_price: float
    has_fixed_sized_tpsls: bool
    tp_order_id: str | None = None
    tp_trigger_price: float | None = None
    tp_limit_price: float | None = None
    sl_order_id: str | None = None
    sl_trigger_price: float | None = None
    sl_limit_price: float | None = None


class UserOpenOrder(BaseModel):
    """Active open order.

    Attributes:
        market: Market address
        order_id: Order ID
        client_order_id: Client-assigned order ID
        price: Limit price
        orig_size: Original order size
        remaining_size: Remaining unfilled size
        is_buy: Buy or sell
        time_in_force: Time in force type
        is_reduce_only: Whether reduce-only
        status: Order status
        transaction_unix_ms: Transaction timestamp in milliseconds
        transaction_version: Transaction version
    """

    market: str
    order_id: str
    price: float
    orig_size: float
    remaining_size: float
    is_buy: bool
    time_in_force: str
    is_reduce_only: bool
    status: str
    transaction_unix_ms: int
    transaction_version: int
    client_order_id: str | None = None


class UserOrderHistoryItem(BaseModel):
    """Order in history.

    Attributes:
        market: Market address
        order_id: Order ID
        client_order_id: Client-assigned order ID
        price: Limit price
        orig_size: Original size
        remaining_size: Remaining size
        is_buy: Buy or sell
        time_in_force: Time in force type
        is_reduce_only: Reduce only flag
        status: Order status
        transaction_unix_ms: Transaction timestamp in milliseconds
        transaction_version: Transaction version
    """

    market: str
    order_id: str
    price: float
    orig_size: float
    remaining_size: float
    is_buy: bool
    time_in_force: str
    is_reduce_only: bool
    status: str
    transaction_unix_ms: int
    transaction_version: int
    client_order_id: str | None = None


class UserTradeHistoryItem(BaseModel):
    """Trade in user history.

    Attributes:
        account: Account address
        market: Market address
        action: Trade action type
        size: Trade size
        price: Trade price
        is_profit: Whether trade was profitable
        realized_pnl_amount: Realized PnL
        is_funding_positive: Funding direction
        realized_funding_amount: Realized funding
        is_rebate: Whether fee was a rebate
        fee_amount: Fee amount
        transaction_unix_ms: Timestamp in milliseconds
        transaction_version: Transaction version
    """

    account: str
    market: str
    action: TradeAction
    size: float
    price: float
    is_profit: bool
    realized_pnl_amount: float
    is_funding_positive: bool
    realized_funding_amount: float
    is_rebate: bool
    fee_amount: float
    transaction_unix_ms: int
    transaction_version: int


class UserFundingHistoryItem(BaseModel):
    """Funding payment.

    Attributes:
        market: Market address
        funding_rate_bps: Funding rate in basis points
        is_funding_positive: Funding direction
        funding_amount: Funding amount
        position_size: Position size at time
        transaction_unix_ms: Timestamp in milliseconds
        transaction_version: Transaction version
    """

    market: str
    funding_rate_bps: float
    is_funding_positive: bool
    funding_amount: float
    position_size: float
    transaction_unix_ms: int
    transaction_version: int


class UserFundHistoryItem(BaseModel):
    """Deposit/withdrawal.

    Attributes:
        amount: Deposit/withdrawal amount
        is_deposit: Whether deposit (true) or withdrawal (false)
        transaction_unix_ms: Timestamp in milliseconds
        transaction_version: Transaction version
    """

    amount: float
    is_deposit: bool
    transaction_unix_ms: int
    transaction_version: int


class UserSubaccount(BaseModel):
    """User's subaccount.

    Attributes:
        subaccount_address: Subaccount address
        primary_account_address: Owner account address
        is_primary: Whether primary subaccount
        custom_label: Custom label/name
        is_active: Whether subaccount is active
    """

    subaccount_address: str
    primary_account_address: str
    is_primary: bool
    custom_label: str | None = None
    is_active: bool | None = None


class Delegation(BaseModel):
    """Trading delegation.

    Attributes:
        delegated_account: Delegated account address
        permission_type: Permission type
        expiration_time_s: Expiration timestamp in seconds
    """

    delegated_account: str
    permission_type: str
    expiration_time_s: int | None = None


class LeaderboardItem(BaseModel):
    """Single leaderboard entry.

    Attributes:
        rank: Leaderboard rank
        account: Account address
        account_value: Account value
        realized_pnl: Realized PnL
        roi: Return on investment
        volume: Trading volume
    """

    rank: int
    account: str
    account_value: float
    realized_pnl: float
    roi: float
    volume: float


class PortfolioChartData(BaseModel):
    """Portfolio chart data point.

    Attributes:
        timestamp: Data point timestamp
        value: Portfolio value
    """

    timestamp: int
    value: float
