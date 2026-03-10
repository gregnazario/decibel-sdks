"""Shared fixtures for Decibel SDK tests."""

from __future__ import annotations

import pytest

from decibel_sdk.config import DecibelConfig, Deployment, Network


@pytest.fixture
def sample_deployment() -> Deployment:
    return Deployment(
        package="0xabc123",
        usdc="0xusdc",
        testc="0xtestc",
        perp_engine_global="0xperp",
    )


@pytest.fixture
def sample_config(sample_deployment: Deployment) -> DecibelConfig:
    return DecibelConfig(
        network=Network.TESTNET,
        fullnode_url="https://fullnode.testnet.aptoslabs.com/v1",
        trading_http_url="https://api.testnet.decibel.trade",
        trading_ws_url="wss://api.testnet.decibel.trade/ws",
        deployment=sample_deployment,
        chain_id=2,
    )
