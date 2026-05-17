from __future__ import annotations
import pytest
from pathlib import Path
from galapagos.research.microstructure_collector_network_disabled.fixture_loader import FixtureLoader
from galapagos.research.microstructure_collector_network_disabled.field_mapper import FieldMapper
from galapagos.research.microstructure_collector_network_disabled.timestamp_normalizer import TimestampNormalizer
from galapagos.research.microstructure_collector_network_disabled.network_guard import NetworkGuard, NetworkDisabledError


def test_network_guard_blocks_socket():
    """Verify that the network guard indeed blocks raw socket calls."""
    import socket
    with NetworkGuard(enabled=True):
        with pytest.raises(NetworkDisabledError):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_fixture_loader_path_safety():
    """Verify that the fixture loader rejects paths outside the allowed directory."""
    with pytest.raises(PermissionError):
        FixtureLoader.load_fixture("../../../PROJECT_STATE.json")
    
    with pytest.raises(PermissionError):
        FixtureLoader.load_fixture("/etc/passwd")


def test_binance_field_mapping():
    """Verify Binance field mapping from fixture."""
    raw = [
        1704067200000, "42280.00", "42350.00", "42250.00", "42300.00", "10.5",
        1704067259999, "444150.00", 150, "5.2", "219960.00", "0"
    ]
    rec = FieldMapper.map_binance_kline(raw, "BTCUSDT", "1m", 123456789)
    assert rec.source == "binance"
    assert rec.open == 42280.0
    assert rec.volume == 10.5
    assert rec.trade_count == 150
    assert rec.event_ts == 1704067200000
    assert rec.available_ts == 1704067260000 # 1704067259999 + 1


def test_bybit_field_mapping():
    """Verify Bybit field mapping from fixture."""
    raw = [
        "1704067200000", "42285.5", "42355.0", "42255.0", "42305.5", "8.4", "355320.0"
    ]
    rec = FieldMapper.map_bybit_kline(raw, "BTCUSDT", "1m", 123456789)
    assert rec.source == "bybit"
    assert rec.open == 42285.5
    assert rec.quote_volume == 355320.0
    assert rec.event_ts == 1704067200000
    assert rec.available_ts > rec.event_ts


def test_timestamp_causality():
    """Verify timestamp normalizer causality logic."""
    assert TimestampNormalizer.validate_causality(100, 110, 120) is True
    assert TimestampNormalizer.validate_causality(100, 90, 120) is False
    assert TimestampNormalizer.validate_causality(100, 110, 105) is False
