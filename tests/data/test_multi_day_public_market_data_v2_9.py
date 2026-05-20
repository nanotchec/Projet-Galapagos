from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.multi_day import DATES_V2_9, output_path, raw_zip_path, run_multi_day_public_market_data_v2_9
from galapagos.data.public_market.multi_day_quality import EXPECTED_ROWS_V2_9, parent_child_consistent
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import read_parquet


@pytest.fixture(scope="session")
def multi_day_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("multi_day_v2_9")
    workspace = Path(__file__).resolve().parents[2]
    raw_source = workspace / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"
    if raw_source.exists():
        for date in DATES_V2_9:
            source = raw_source / f"BTCUSDT-1m-{date}.zip"
            if source.exists():
                target = raw_zip_path(root, date)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    run_multi_day_public_market_data_v2_9(root, no_network=False, validate_previous_layers=False)
    return root


def test_multi_day_window_expected_dates() -> None:
    assert DATES_V2_9 == [
        "2024-01-15",
        "2024-01-16",
        "2024-01-17",
        "2024-01-18",
        "2024-01-19",
        "2024-01-20",
        "2024-01-21",
    ]


def test_multi_day_1m_row_count_10080(multi_day_project: Path) -> None:
    frame = read_parquet(output_path(multi_day_project, "1m"))
    assert len(frame) == 10080


def test_multi_day_resampled_row_counts(multi_day_project: Path) -> None:
    for timeframe, expected_rows in EXPECTED_ROWS_V2_9.items():
        assert len(read_parquet(output_path(multi_day_project, timeframe))) == expected_rows


def test_multi_day_timestamp_bounds(multi_day_project: Path) -> None:
    expected_max = {
        "1m": "2024-01-21T23:59:00Z",
        "5m": "2024-01-21T23:55:00Z",
        "15m": "2024-01-21T23:45:00Z",
        "1h": "2024-01-21T23:00:00Z",
    }
    for timeframe, max_event_ts in expected_max.items():
        frame = read_parquet(output_path(multi_day_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert event_ts.min().isoformat().replace("+00:00", "Z") == "2024-01-15T00:00:00Z"
        assert event_ts.max().isoformat().replace("+00:00", "Z") == max_event_ts


def test_multi_day_strict_ohlcv_columns(multi_day_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V2_9:
        assert list(read_parquet(output_path(multi_day_project, timeframe)).columns) == OHLCV_COLUMNS


def test_multi_day_parent_child_consistency(multi_day_project: Path) -> None:
    frame_1m = read_parquet(output_path(multi_day_project, "1m"))
    for timeframe in ["5m", "15m", "1h"]:
        child = read_parquet(output_path(multi_day_project, timeframe))
        assert parent_child_consistent(frame_1m, child, timeframe)


def test_multi_day_no_gaps_no_duplicates(multi_day_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V2_9:
        frame = read_parquet(output_path(multi_day_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert frame.duplicated(subset=["source", "market_type", "symbol", "timeframe", "event_ts"]).sum() == 0
        assert event_ts.is_monotonic_increasing
        assert event_ts.diff().dropna().nunique() == 1
