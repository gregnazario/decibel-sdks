"""Tests for configuration."""

import pytest

from decibel.config import CompatVersion, DecibelConfig, Deployment, Network


def test_mainnet_config():
    """Test mainnet configuration."""
    config = DecibelConfig.mainnet()
    assert config.network == Network.MAINNET
    assert config.fullnode_url == "https://fullnode.mainnet.aptoslabs.com/v1"
    assert config.trading_http_url == "https://api.decibel.trade"
    assert config.trading_ws_url == "wss://api.decibel.trade/ws"
    assert config.chain_id == 1
    assert config.compat_version == CompatVersion.V04


def test_testnet_config():
    """Test testnet configuration."""
    config = DecibelConfig.testnet()
    assert config.network == Network.TESTNET
    assert config.fullnode_url == "https://fullnode.testnet.aptoslabs.com/v1"
    assert config.chain_id == 2


def test_local_config():
    """Test local configuration."""
    config = DecibelConfig.local()
    assert config.network == Network.LOCAL
    assert config.fullnode_url == "http://localhost:8080/v1"
    assert config.chain_id == 4


def test_named_config():
    """Test named configuration lookup."""
    mainnet = DecibelConfig.named("mainnet")
    assert mainnet is not None
    assert mainnet.network == Network.MAINNET

    testnet = DecibelConfig.named("testnet")
    assert testnet is not None
    assert testnet.network == Network.TESTNET

    local = DecibelConfig.named("local")
    assert local is not None
    assert local.network == Network.LOCAL

    invalid = DecibelConfig.named("invalid")
    assert invalid is None


def test_config_validation():
    """Test configuration validation."""
    # Valid config should not raise
    config = DecibelConfig.mainnet()
    config.validate()  # Should not raise

    # Invalid config should raise
    with pytest.raises(ValueError, match="fullnode_url"):
        invalid = DecibelConfig(
            network=Network.CUSTOM,
            fullnode_url="",
            trading_http_url="https://api.test.com",
            trading_ws_url="wss://api.test.com/ws",
            deployment=Deployment(
                package="0x123",
                usdc="0x456",
                testc="",
                perp_engine_global="",
            ),
        )
        invalid.validate()

    with pytest.raises(ValueError, match="trading_http_url"):
        invalid = DecibelConfig(
            network=Network.CUSTOM,
            fullnode_url="https://fullnode.com",
            trading_http_url="",
            trading_ws_url="wss://api.test.com/ws",
            deployment=Deployment(
                package="0x123",
                usdc="0x456",
                testc="",
                perp_engine_global="",
            ),
        )
        invalid.validate()
