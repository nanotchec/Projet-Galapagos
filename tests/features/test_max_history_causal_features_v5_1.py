from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.max_history_window import TIMEFRAMES_V5_1, input_ohlcv_path, load_v5_0_ohlcv_manifest, output_path
from galapagos.features.schemas import FEATURE_COLUMNS_V5_1, FORBIDDEN_TERMS


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v5_0_manifest(project_root: Path) -> dict:
    return load_v5_0_ohlcv_manifest(project_root)


@pytest.fixture(scope="session")
def v5_1_frames(project_root: Path, v5_0_manifest: dict) -> dict[str, pd.DataFrame]:
    window_start = v5_0_manifest["discovery"]["window_start"]
    window_end = v5_0_manifest["discovery"]["window_end"]
    return {
        timeframe: read_parquet(output_path(project_root, timeframe, window_start, window_end))
        for timeframe in TIMEFRAMES_V5_1
    }


def test_max_history_features_row_count_matches_input(
    project_root: Path,
    v5_0_manifest: dict,
    v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    for timeframe, frame in v5_1_frames.items():
        input_frame = read_parquet(input_ohlcv_path(project_root, timeframe, v5_0_manifest))
        assert len(frame) == len(input_frame) == v5_0_manifest["expected_rows"][timeframe]


def test_max_history_features_strict_columns(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v5_1_frames.values():
        assert list(frame.columns) == FEATURE_COLUMNS_V5_1


def test_max_history_returns_are_past_only(
    project_root: Path,
    v5_0_manifest: dict,
    v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    input_frame = read_parquet(input_ohlcv_path(project_root, "1m", v5_0_manifest))
    features = v5_1_frames["1m"]
    assert features.loc[1, "close_lag_1"] == pytest.approx(input_frame.loc[0, "close"])
    assert features.loc[31, "return_1"] == pytest.approx(input_frame.loc[31, "close"] / input_frame.loc[30, "close"] - 1.0)
    assert pd.isna(features.loc[0, "close_lag_1"])


def test_max_history_rolling_features_have_expected_warmup(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v5_1_frames.values():
        assert int(frame["warmup_row"].sum()) == 30
        assert frame.loc[:29, "warmup_row"].all()
        assert not bool(frame.loc[30, "warmup_row"])


def test_max_history_temporal_features_utc(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = v5_1_frames["1m"]
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    assert (frame["hour_utc"].to_numpy() == event_ts.dt.hour.to_numpy()).all()
    assert (frame["day_of_week_utc"].to_numpy() == event_ts.dt.dayofweek.to_numpy()).all()
    assert (frame["is_weekend_utc"].to_numpy() == event_ts.dt.dayofweek.isin([5, 6]).to_numpy()).all()


def test_max_history_feature_available_ts_not_before_available_ts(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v5_1_frames.values():
        assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()


def test_max_history_decision_ts_not_before_feature_available_ts(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v5_1_frames.values():
        assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_max_history_no_forbidden_feature_columns(v5_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v5_1_frames.values():
        for column in frame.columns:
            if column in FEATURE_COLUMNS_V5_1:
                continue
            assert not any(term in column.casefold() for term in FORBIDDEN_TERMS)


def test_max_history_source_hashes_match_inputs(
    project_root: Path,
    v5_0_manifest: dict,
    v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    for timeframe, frame in v5_1_frames.items():
        expected_sha = sha256_file(input_ohlcv_path(project_root, timeframe, v5_0_manifest))
        assert set(frame["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}
