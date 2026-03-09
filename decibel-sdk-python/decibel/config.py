"""Configuration classes for the Decibel SDK."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Network(str, Enum):
    """Aptos network types."""

    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"
    LOCAL = "local"
    CUSTOM = "custom"


class CompatVersion(str, Enum):
    """SDK compatibility versions."""

    V04 = "v0.4"


@dataclass(frozen=True)
class Deployment:
    """Smart contract deployment addresses."""

    package: str
    usdc: str
    testc: str
    perp_engine_global: str


@dataclass(frozen=True)
class DecibelConfig:
    """SDK configuration.

    Attributes:
        network: Aptos network type
        fullnode_url: Aptos fullnode RPC URL
        trading_http_url: Decibel REST API base URL
        trading_ws_url: Decibel WebSocket URL
        gas_station_url: Gas station URL for sponsored transactions (optional)
        gas_station_api_key: API key for Aptos Labs Gas Station (optional)
        deployment: Smart contract deployment addresses
        chain_id: Override chain ID (auto-detected if not provided)
        compat_version: SDK compatibility version
    """

    network: Network
    fullnode_url: str
    trading_http_url: str
    trading_ws_url: str
    deployment: Deployment
    gas_station_url: str | None = None
    gas_station_api_key: str | None = None
    chain_id: int | None = None
    compat_version: CompatVersion = CompatVersion.V04

    def validate(self) -> None:
        """Validate that required configuration fields are set.

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not self.fullnode_url:
            raise ValueError("fullnode_url must not be empty")
        if not self.trading_http_url:
            raise ValueError("trading_http_url must not be empty")
        if not self.trading_ws_url:
            raise ValueError("trading_ws_url must not be empty")
        if not self.deployment.package:
            raise ValueError("deployment.package must not be empty")

    @classmethod
    def mainnet(cls) -> "DecibelConfig":
        """Production mainnet configuration."""
        return cls(
            network=Network.MAINNET,
            fullnode_url="https://fullnode.mainnet.aptoslabs.com/v1",
            trading_http_url="https://api.decibel.trade",
            trading_ws_url="wss://api.decibel.trade/ws",
            gas_station_url="https://api.netna.aptoslabs.com/gs/v1",
            deployment=Deployment(
                package="0x2a4e9bee4b09f5b8e9c996a489c6993abe1e9e45e61e81bb493e38e53a3e7e3d",
                usdc="0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b",
                testc="",
                perp_engine_global="",
            ),
            chain_id=1,
            compat_version=CompatVersion.V04,
        )

    @classmethod
    def testnet(cls) -> "DecibelConfig":
        """Testnet configuration."""
        return cls(
            network=Network.TESTNET,
            fullnode_url="https://fullnode.testnet.aptoslabs.com/v1",
            trading_http_url="https://api.testnet.decibel.trade",
            trading_ws_url="wss://api.testnet.decibel.trade/ws",
            gas_station_url="https://api.testnet.aptoslabs.com/gs/v1",
            deployment=Deployment(
                package="",
                usdc="",
                testc="",
                perp_engine_global="",
            ),
            chain_id=2,
            compat_version=CompatVersion.V04,
        )

    @classmethod
    def local(cls) -> "DecibelConfig":
        """Local development configuration."""
        return cls(
            network=Network.LOCAL,
            fullnode_url="http://localhost:8080/v1",
            trading_http_url="http://localhost:3000",
            trading_ws_url="ws://localhost:3000/ws",
            gas_station_url="http://localhost:8081",
            deployment=Deployment(
                package="",
                usdc="",
                testc="",
                perp_engine_global="",
            ),
            chain_id=4,
            compat_version=CompatVersion.V04,
        )

    @classmethod
    def named(cls, name: str) -> "DecibelConfig | None":
        """Get a configuration by name.

        Args:
            name: Configuration name ("mainnet", "testnet", "local")

        Returns:
            Configuration if found, None otherwise
        """
        configs: dict[str, type[DecibelConfig] | None] = {
            "mainnet": cls.mainnet,
            "testnet": cls.testnet,
            "local": cls.local,
        }
        factory = configs.get(name)
        if factory:
            return factory()  # type: ignore[call-arg]
        return None
