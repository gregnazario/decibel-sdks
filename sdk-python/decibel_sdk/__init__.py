"""Decibel SDK — Python client for the Decibel perpetual futures exchange on Aptos."""

from decibel_sdk.client.read import DecibelReadClient
from decibel_sdk.client.write import (
    CancelOrderArgs,
    ConfigureMarketSettingsArgs,
    DecibelWriteClient,
    DelegateTradingArgs,
    PlaceOrderArgs,
    PlaceTpSlArgs,
    PlaceTwapOrderArgs,
    TransactionResponse,
)
from decibel_sdk.client.ws import Subscription, WebSocketManager, WsReadyState
from decibel_sdk.config import (
    CompatVersion,
    DecibelConfig,
    Deployment,
    Network,
    local_config,
    mainnet_config,
    named_config,
    testnet_config,
)
from decibel_sdk.errors import (
    ApiError,
    ApiResponse,
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
from decibel_sdk.gas.manager import GasPriceManager
from decibel_sdk.models.common import (
    CandlestickInterval,
    MarketDepthAggregationSize,
    OrderStatusType,
    PageParams,
    PaginatedResponse,
    PlaceOrderResult,
    SearchTermParams,
    SortDirection,
    SortParams,
    TimeInForce,
    TradeAction,
    TwapOrderResult,
    TwapStatus,
    VaultType,
    VolumeWindow,
)

__all__ = [
    # Clients
    "DecibelReadClient",
    "DecibelWriteClient",
    # WebSocket
    "WebSocketManager",
    "Subscription",
    "WsReadyState",
    # Config
    "DecibelConfig",
    "Deployment",
    "Network",
    "CompatVersion",
    "mainnet_config",
    "testnet_config",
    "local_config",
    "named_config",
    # Errors
    "DecibelError",
    "ConfigError",
    "NetworkError",
    "ApiError",
    "ValidationError",
    "TransactionError",
    "SimulationError",
    "SigningError",
    "GasEstimationError",
    "WebSocketError",
    "SerializationError",
    "TimeoutError",
    "ApiResponse",
    # Gas
    "GasPriceManager",
    # Write args
    "PlaceOrderArgs",
    "CancelOrderArgs",
    "PlaceTwapOrderArgs",
    "PlaceTpSlArgs",
    "ConfigureMarketSettingsArgs",
    "DelegateTradingArgs",
    "TransactionResponse",
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
    # Common types
    "PageParams",
    "PaginatedResponse",
    "SortParams",
    "SearchTermParams",
    "PlaceOrderResult",
    "TwapOrderResult",
]
