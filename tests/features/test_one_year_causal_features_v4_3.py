from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.one_year_window import output_path as v4_2_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.one_year_window import TIMEFRAMES_V4_3, output_path
from galapagos.features.one_year_window_quality import EXPECTED_ROWS_V4_3
from galapagos.features.schemas import FEATURE_COLUMNS_V4_3, FORBIDDEN_TERMS


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v4_3_frames(project_root: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(project_root, timeframe)) for timeframe in TIMEFRAMES_V4_3}


def test_one_year_features_row_count_matches_input(project_root: Path, v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v4_3_frames.items():
        input_frame = read_parquet(v4_2_ohlcv_path(project_root, timeframe))
        assert len(frame) == len(input_frame) == EXPECTED_ROWS_V4_3[timeframe]


def test_one_year_features_strict_columns(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_3_frames.values():
        assert list(frame.columns) == FEATURE_COLUMNS_V4_3


def test_one_year_returns_are_past_only(project_root: Path, v4_3_frames: dict[str, pd.DataFrame]) -> None:
    input_frame = read_parquet(v4_2_ohlcv_path(project_root, "1m"))
    features = v4_3_frames["1m"]
    assert features.loc[1, "close_lag_1"] == pytest.approx(input_frame.loc[0, "close"])
    assert pd.isna(features.loc[0, "close_lag_1"])


def test_one_year_rolling_features_have_expected_warmup(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_3_frames.values():
        assert int(frame["warmup_row"].sum()) == 30
        assert frame.loc[:29, "warmup_row"].all()
        assert not bool(frame.loc[30, "warmup_row"])


def test_one_year_temporal_features_utc(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    frame = v4_3_frames["1m"]
    assert frame.loc[0, "hour_utc"] == 0
    assert frame.loc[0, "day_of_week_utc"] == 0
    assert not bool(frame.loc[0, "is_weekend_utc"])
    assert bool(frame.loc[5 * 1440, "is_weekend_utc"])


def test_one_year_feature_available_ts_not_before_available_ts(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_3_frames.values():
        assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()


def test_one_year_decision_ts_not_before_feature_available_ts(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_3_frames.values():
        assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_one_year_no_forbidden_feature_columns(v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_3_frames.values():
        for column in frame.columns:
            if column in FEATURE_COLUMNS_V4_3:
                continue
            assert not any(term in column.casefold() for term in FORBIDDEN_TERMS)


def test_one_year_source_hashes_match_inputs(project_root: Path, v4_3_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v4_3_frames.items():
        expected_sha = sha256_file(v4_2_ohlcv_path(project_root, timeframe))
        assert set(frame["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}
