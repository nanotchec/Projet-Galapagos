from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.one_year_window import DATES_V4_2, output_path
from galapagos.data.public_market.one_year_window_quality import EXPECTED_ROWS_V4_2, parent_child_consistent
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import read_parquet


@pytest.fixture(scope="session")
def expanded_project() -> Path:
    return Path(__file__).resolve().parents[2]


def test_one_year_window_expected_dates() -> None:
    assert len(DATES_V4_2) == 366
    assert DATES_V4_2[0] == "2024-01-01"
    assert DATES_V4_2[-1] == "2024-12-31"


def test_one_year_1m_row_count_527040(expanded_project: Path) -> None:
    assert len(read_parquet(output_path(expanded_project, "1m"))) == 527040


def test_one_year_resampled_row_counts(expanded_project: Path) -> None:
    for timeframe, expected_rows in EXPECTED_ROWS_V4_2.items():
        assert len(read_parquet(output_path(expanded_project, timeframe))) == expected_rows


def test_one_year_timestamp_bounds(expanded_project: Path) -> None:
    expected_max = {
        "1m": "2024-12-31T23:59:00Z",
        "5m": "2024-12-31T23:55:00Z",
        "15m": "2024-12-31T23:45:00Z",
        "1h": "2024-12-31T23:00:00Z",
    }
    for timeframe, max_event_ts in expected_max.items():
        frame = read_parquet(output_path(expanded_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert event_ts.min().isoformat().replace("+00:00", "Z") == "2024-01-01T00:00:00Z"
        assert event_ts.max().isoformat().replace("+00:00", "Z") == max_event_ts


def test_one_year_strict_ohlcv_columns(expanded_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V4_2:
        assert list(read_parquet(output_path(expanded_project, timeframe)).columns) == OHLCV_COLUMNS


def test_one_year_parent_child_consistency(expanded_project: Path) -> None:
    frame_1m = read_parquet(output_path(expanded_project, "1m"))
    for timeframe in ["5m", "15m", "1h"]:
        child = read_parquet(output_path(expanded_project, timeframe))
        assert parent_child_consistent(frame_1m, child, timeframe)


def test_one_year_no_gaps_no_duplicates(expanded_project: Path) -> None:
    for timeframe in EXPECTED_ROWS_V4_2:
        frame = read_parquet(output_path(expanded_project, timeframe))
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        assert frame.duplicated(subset=["source", "market_type", "symbol", "timeframe", "event_ts"]).sum() == 0
        assert event_ts.is_monotonic_increasing
        assert event_ts.diff().dropna().nunique() == 1
