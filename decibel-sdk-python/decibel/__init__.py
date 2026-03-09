"""Decibel Python SDK - Perpetual futures trading on Aptos.

The SDK provides:
- Async REST API client for market data and account queries
- WebSocket client for real-time data streaming
- On-chain transaction builder for placing orders and managing accounts
- Type-safe data models using Pydantic v2
"""

from decibel.config import CompatVersion, DecibelConfig, Deployment, Network
from decibel.client.read import DecibelReadClient
from decibel.client.write import DecibelWriteClient
from decibel.client.websocket import WebSocketManager
from decibel.errors import (
    APIError,
    ConfigError,
    DecibelError,
    GasEstimationError,
    NetworkError,
    SerializationError,
    SigningError,
    SimulationError,
    TimeoutError,
    TransactionError,
    ValidationError,
    WebSocketError,
)
from decibel.models.account import (
    AccountOverview,
    Delegation,
    LeaderboardItem,
    PortfolioChartData,
    UserFundingHistoryItem,
    UserFundHistoryItem,
    UserOpenOrder,
    UserOrderHistoryItem,
    UserPosition,
    UserSubaccount,
    UserTradeHistoryItem,
)
from decibel.models.common import PageParams, PaginatedResponse, PlaceOrderResult, SearchTermParams, SortParams, TwapOrderResult
from decibel.models.enums import (
    CandlestickInterval,
    MarketDepthAggregationSize,
    OrderStatusType,
    SortDirection,
    TimeInForce,
    TradeAction,
    TwapStatus,
    VaultType,
    VolumeWindow,
)
from decibel.models.market import Candlestick, MarketContext, MarketDepth, MarketOrder, MarketPrice, MarketTrade, PerpMarketConfig
from decibel.models.order import OrderStatus, UserActiveTwap
from decibel.models.vault import UserOwnedVault, UserPerformanceOnVault, Vault, VaultsResponse
from decibel.transaction.signer import Ed25519Signer
from decibel.gas.manager import GasPriceManager
from decibel.utils.address import get_market_addr, get_primary_subaccount_addr, get_vault_share_address
from decibel.utils.crypto import generate_random_replay_protection_nonce
from decibel.utils.price import round_to_tick_size

__version__ = "0.1.0"
__all__ = [
    # Version
    "__version__",
    # Configuration
    "DecibelConfig",
    "Network",
    "CompatVersion",
    "Deployment",
    # Clients
    "DecibelReadClient",
    "DecibelWriteClient",
    "WebSocketManager",
    # Errors
    "DecibelError",
    "ConfigError",
    "NetworkError",
    "APIError",
    "ValidationError",
    "TransactionError",
    "SimulationError",
    "SigningError",
    "GasEstimationError",
    "WebSocketError",
    "SerializationError",
    "TimeoutError",
    # Market Models
    "PerpMarketConfig",
    "MarketDepth",
    "MarketOrder",
    "MarketPrice",
    "MarketContext",
    "Candlestick",
    "MarketTrade",
    # Account Models
    "AccountOverview",
    "UserPosition",
    "UserOpenOrder",
    "UserOrderHistoryItem",
    "UserTradeHistoryItem",
    "UserFundingHistoryItem",
    "UserFundHistoryItem",
    "UserSubaccount",
    "Delegation",
    "LeaderboardItem",
    "PortfolioChartData",
    # Order Models
    "OrderStatus",
    "UserActiveTwap",
    # Vault Models
    "Vault",
    "VaultsResponse",
    "UserOwnedVault",
    "UserPerformanceOnVault",
    # Common Models
    "PageParams",
    "SortParams",
    "SearchTermParams",
    "PaginatedResponse",
    "PlaceOrderResult",
    "TwapOrderResult",
    # Enums
    "TimeInForce",
    "CandlestickInterval",
    "VolumeWindow",
    "OrderStatusType",
    "SortDirection",
    "TwapStatus",
    "TradeAction",
    "VaultType",
    "MarketDepthAggregationSize",
    # Utilities
    "Ed25519Signer",
    "GasPriceManager",
    "get_market_addr",
    "get_primary_subaccount_addr",
    "get_vault_share_address",
    "round_to_tick_size",
    "generate_random_replay_protection_nonce",
]
