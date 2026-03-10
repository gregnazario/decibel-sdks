"""Network configuration and preset environments for the Decibel SDK."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, model_validator

from decibel_sdk.errors import ConfigError


class Network(str, Enum):
    MAINNET = "Mainnet"
    TESTNET = "Testnet"
    DEVNET = "Devnet"
    LOCAL = "Local"
    CUSTOM = "Custom"


class CompatVersion(str, Enum):
    V0_4 = "v0.4"


class Deployment(BaseModel):
    package: str
    usdc: str
    testc: str
    perp_engine_global: str


class DecibelConfig(BaseModel):
    network: Network
    fullnode_url: str
    trading_http_url: str
    trading_ws_url: str
    gas_station_url: str | None = None
    gas_station_api_key: str | None = None
    deployment: Deployment
    chain_id: int | None = None
    compat_version: CompatVersion = CompatVersion.V0_4

    @model_validator(mode="after")
    def _validate_required_urls(self) -> DecibelConfig:
        if not self.fullnode_url:
            raise ConfigError("fullnode_url must not be empty")
        if not self.trading_http_url:
            raise ConfigError("trading_http_url must not be empty")
        if not self.trading_ws_url:
            raise ConfigError("trading_ws_url must not be empty")
        if not self.deployment.package:
            raise ConfigError("deployment.package must not be empty")
        return self


def mainnet_config() -> DecibelConfig:
    return DecibelConfig(
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
    )


def testnet_config() -> DecibelConfig:
    return DecibelConfig(
        network=Network.TESTNET,
        fullnode_url="https://fullnode.testnet.aptoslabs.com/v1",
        trading_http_url="https://api.testnet.decibel.trade",
        trading_ws_url="wss://api.testnet.decibel.trade/ws",
        gas_station_url="https://api.testnet.aptoslabs.com/gs/v1",
        deployment=Deployment(
            package="placeholder",
            usdc="",
            testc="",
            perp_engine_global="",
        ),
        chain_id=2,
    )


def local_config() -> DecibelConfig:
    return DecibelConfig(
        network=Network.LOCAL,
        fullnode_url="http://localhost:8080/v1",
        trading_http_url="http://localhost:3000",
        trading_ws_url="ws://localhost:3000/ws",
        gas_station_url="http://localhost:8081",
        deployment=Deployment(
            package="placeholder",
            usdc="",
            testc="",
            perp_engine_global="",
        ),
        chain_id=4,
    )


def named_config(name: str) -> DecibelConfig | None:
    configs = {
        "mainnet": mainnet_config,
        "testnet": testnet_config,
        "local": local_config,
    }
    factory = configs.get(name.lower())
    return factory() if factory else None
