from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.max_history_discovery import DISCOVERY_JSON_PATH_V5_0, expected_rows_from_days_v5_0
from galapagos.data.public_market.max_history_window import MANIFEST_PATH_V5_0, output_path
from galapagos.data.public_market.max_history_window_quality import TIMEFRAMES_V5_0, parent_child_consistent
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import read_parquet


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v5_0_manifest(project_root: Path) -> dict:
    return json.loads((project_root / MANIFEST_PATH_V5_0).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def v5_0_discovery(project_root: Path) -> dict:
    return json.loads((project_root / DISCOVERY_JSON_PATH_V5_0).read_text(encoding="utf-8"))


def test_max_history_discovery_has_window(v5_0_discovery: dict) -> None:
    assert v5_0_discovery["status"] == "PASS"
    assert v5_0_discovery["window_start"] <= v5_0_discovery["window_end"]
    assert v5_0_discovery["total_days"] > 366
    assert v5_0_discovery["missing_dates"] == []


def test_max_history_expected_rows_match_days(v5_0_manifest: dict) -> None:
    assert v5_0_manifest["expected_rows"] == expected_rows_from_days_v5_0(v5_0_manifest["discovery"]["total_days"])


def test_max_history_resampled_row_counts(project_root: Path, v5_0_manifest: dict) -> None:
    for timeframe, expected_rows in v5_0_manifest["expected_rows"].items():
        frame = read_parquet(output_path(project_root, timeframe))
        assert len(frame) == expected_rows


def test_max_history_timestamp_bounds(project_root: Path, v5_0_manifest: dict) -> None:
    expected_max = {
        "1m": f"{v5_0_manifest['discovery']['window_end']}T23:59:00Z",
        "5m": f"{v5_0_manifest['discovery']['window_end']}T23:55:00Z",
        "15m": f"{v5_0_manifest['discovery']['window_end']}T23:45:00Z",
        "1h": f"{v5_0_manifest['discovery']['window_end']}T23:00:00Z",
    }
    for timeframe, max_event_ts in expected_max.items():
        frame = read_parquet(output_path(project_root, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert event_ts.min().isoformat().replace("+00:00", "Z") == f"{v5_0_manifest['discovery']['window_start']}T00:00:00Z"
        assert event_ts.max().isoformat().replace("+00:00", "Z") == max_event_ts


def test_max_history_strict_ohlcv_columns(project_root: Path) -> None:
    for timeframe in TIMEFRAMES_V5_0:
        assert list(read_parquet(output_path(project_root, timeframe)).columns) == OHLCV_COLUMNS


def test_max_history_parent_child_consistency(project_root: Path) -> None:
    frame_1m = read_parquet(output_path(project_root, "1m"))
    for timeframe in ["5m", "15m", "1h"]:
        child = read_parquet(output_path(project_root, timeframe))
        assert parent_child_consistent(frame_1m, child, timeframe)


def test_max_history_no_gaps_no_duplicates(project_root: Path) -> None:
    for timeframe in TIMEFRAMES_V5_0:
        frame = read_parquet(output_path(project_root, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert int(frame.duplicated(subset=["source", "market_type", "symbol", "timeframe", "event_ts"]).sum()) == 0
        assert event_ts.is_monotonic_increasing
        assert event_ts.diff().dropna().nunique() == 1
