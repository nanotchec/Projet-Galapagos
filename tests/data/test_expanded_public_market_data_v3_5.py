from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.expanded_window import DATES_V3_5, output_path, raw_zip_path, run_expanded_public_market_data_v3_5
from galapagos.data.public_market.expanded_window_quality import EXPECTED_ROWS_V3_5, parent_child_consistent
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import read_parquet


@pytest.fixture(scope="session")
def expanded_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("expanded_v3_5")
    workspace = Path(__file__).resolve().parents[2]
    raw_source = workspace / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"
    if raw_source.exists():
        for current_date in DATES_V3_5:
            source = raw_source / f"BTCUSDT-1m-{current_date}.zip"
            if source.exists():
                target = raw_zip_path(root, current_date)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    run_multi = run_expanded_public_market_data_v3_5
    run_multi(root, no_network=False, validate_project_state=False)
    return root


def test_expanded_window_expected_dates() -> None:
    assert len(DATES_V3_5) == 90
    assert DATES_V3_5[0] == "2024-01-01"
    assert DATES_V3_5[-1] == "2024-03-30"


def test_expanded_1m_row_count_129600(expanded_project: Path) -> None:
    assert len(read_parquet(output_path(expanded_project, "1m"))) == 129600


def test_expanded_resampled_row_counts(expanded_project: Path) -> None:
    for timeframe, expected_rows in EXPECTED_ROWS_V3_5.items():
        assert len(read_parquet(output_path(expanded_project, timeframe))) == expected_rows


def test_expanded_timestamp_bounds(expanded_project: Path) -> None:
    expected_max = {
        "1m": "2024-03-30T23:59:00Z",
        "5m": "2024-03-30T23:55:00Z",
        "15m": "2024-03-30T23:45:00Z",
        "1h": "2024-03-30T23:00:00Z",
    }
    for timeframe, max_event_ts in expected_max.items():
        frame = read_parquet(output_path(expanded_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert event_ts.min().isoformat().replace("+00:00", "Z") == "2024-01-01T00:00:00Z"
        assert event_ts.max().isoformat().replace("+00:00", "Z") == max_event_ts


def test_expanded_strict_ohlcv_columns(expanded_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V3_5:
        assert list(read_parquet(output_path(expanded_project, timeframe)).columns) == OHLCV_COLUMNS


def test_expanded_parent_child_consistency(expanded_project: Path) -> None:
    frame_1m = read_parquet(output_path(expanded_project, "1m"))
    for timeframe in ["5m", "15m", "1h"]:
        child = read_parquet(output_path(expanded_project, timeframe))
        assert parent_child_consistent(frame_1m, child, timeframe)


def test_expanded_no_gaps_no_duplicates(expanded_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V3_5:
        frame = read_parquet(output_path(expanded_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert frame.duplicated(subset=["source", "market_type", "symbol", "timeframe", "event_ts"]).sum() == 0
        assert event_ts.is_monotonic_increasing
        assert event_ts.diff().dropna().nunique() == 1
