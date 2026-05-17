from __future__ import annotations
import pytest
import socket
from galapagos.research.microstructure_collector_network_disabled.network_guard import NetworkGuard, NetworkDisabledError
from galapagos.research.microstructure_collector_network_disabled.config_schema import CollectorConfig
from galapagos.research.microstructure_collector_network_disabled.source_adapter_base import SourceAdapter
from galapagos.research.microstructure_collector_network_disabled.binance_adapter_stub import BinanceAdapterStub
from galapagos.research.microstructure_collector_network_disabled.dry_run_executor import DryRunExecutor
from galapagos.research.microstructure_collector_network_disabled.request_builder import RequestBuilder


def test_network_guard_blocks_socket():
    """Verify that NetworkGuard correctly blocks socket calls."""
    with NetworkGuard(enabled=True):
        with pytest.raises(NetworkDisabledError):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_adapter_execute_request_raises_when_disabled():
    """Verify that execute_request raises RuntimeError when network_disabled is True."""
    config = CollectorConfig(
        version="V1.54",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start_ts=1704067200000,
        end_ts=1704153600000,
        network_disabled=True
    )
    adapter = BinanceAdapterStub(config)
    with pytest.raises(RuntimeError, match="network is disabled"):
        adapter.execute_request({"params": {}})


def test_dry_run_executor_does_not_call_network():
    """Verify that DryRunExecutor stays in dry-run mode."""
    config = CollectorConfig(
        version="V1.54",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start_ts=1704067200000,
        end_ts=1704067260000,
        network_disabled=True
    )
    builder = RequestBuilder(config)
    plan = builder.build_plan()
    executor = DryRunExecutor(plan)
    results = executor.execute()
    
    assert len(results) > 0
    for res in results:
        assert res["status"] == "PLANNED_BUT_NOT_EXECUTED"
        assert res["network_disabled"] is True


def test_request_builder_limit():
    """Verify that request builder respects max_requests."""
    config = CollectorConfig(
        version="V1.54",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start_ts=1704067200000,
        end_ts=1704067200000 + (2000 * 60000), # 2000 minutes
        max_requests=10,
        network_disabled=True
    )
    builder = RequestBuilder(config)
    plan = builder.build_plan()
    assert len(plan.requests) <= 10
