"""Tests for config presets, validation, and named_config."""

from __future__ import annotations

import pytest

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
from decibel_sdk.errors import ConfigError


class TestPresets:
    def test_mainnet_config(self) -> None:
        cfg = mainnet_config()
        assert cfg.network == Network.MAINNET
        assert cfg.chain_id == 1
        assert "mainnet" in cfg.fullnode_url
        assert cfg.trading_http_url == "https://api.decibel.trade"
        assert cfg.trading_ws_url == "wss://api.decibel.trade/ws"
        assert cfg.deployment.package.startswith("0x")
        assert cfg.compat_version == CompatVersion.V0_4

    def test_testnet_config(self) -> None:
        cfg = testnet_config()
        assert cfg.network == Network.TESTNET
        assert cfg.chain_id == 2
        assert "testnet" in cfg.fullnode_url

    def test_local_config(self) -> None:
        cfg = local_config()
        assert cfg.network == Network.LOCAL
        assert cfg.chain_id == 4
        assert "localhost" in cfg.fullnode_url


class TestNamedConfig:
    def test_mainnet_lookup(self) -> None:
        cfg = named_config("mainnet")
        assert cfg is not None
        assert cfg.network == Network.MAINNET

    def test_case_insensitive(self) -> None:
        cfg = named_config("TESTNET")
        assert cfg is not None
        assert cfg.network == Network.TESTNET

    def test_unknown_returns_none(self) -> None:
        assert named_config("unknown") is None


class TestValidation:
    def test_empty_fullnode_url(self, sample_deployment: Deployment) -> None:
        with pytest.raises(ConfigError, match="fullnode_url"):
            DecibelConfig(
                network=Network.TESTNET,
                fullnode_url="",
                trading_http_url="https://api.test",
                trading_ws_url="wss://api.test/ws",
                deployment=sample_deployment,
            )

    def test_empty_trading_http_url(self, sample_deployment: Deployment) -> None:
        with pytest.raises(ConfigError, match="trading_http_url"):
            DecibelConfig(
                network=Network.TESTNET,
                fullnode_url="https://node",
                trading_http_url="",
                trading_ws_url="wss://api.test/ws",
                deployment=sample_deployment,
            )

    def test_empty_trading_ws_url(self, sample_deployment: Deployment) -> None:
        with pytest.raises(ConfigError, match="trading_ws_url"):
            DecibelConfig(
                network=Network.TESTNET,
                fullnode_url="https://node",
                trading_http_url="https://api.test",
                trading_ws_url="",
                deployment=sample_deployment,
            )

    def test_empty_package(self) -> None:
        with pytest.raises(ConfigError, match="deployment.package"):
            DecibelConfig(
                network=Network.TESTNET,
                fullnode_url="https://node",
                trading_http_url="https://api.test",
                trading_ws_url="wss://api.test/ws",
                deployment=Deployment(
                    package="",
                    usdc="",
                    testc="",
                    perp_engine_global="",
                ),
            )

    def test_valid_config_passes(self, sample_deployment: Deployment) -> None:
        cfg = DecibelConfig(
            network=Network.CUSTOM,
            fullnode_url="https://node",
            trading_http_url="https://api",
            trading_ws_url="wss://ws",
            deployment=sample_deployment,
        )
        assert cfg.network == Network.CUSTOM


class TestNetworkEnum:
    def test_all_variants(self) -> None:
        assert len(Network) == 5
        assert Network.MAINNET == "Mainnet"
        assert Network.DEVNET == "Devnet"


class TestCompatVersion:
    def test_default(self) -> None:
        assert CompatVersion.V0_4 == "v0.4"
