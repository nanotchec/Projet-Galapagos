from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.multi_day import output_path as v2_9_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.multi_day import TIMEFRAMES_V3_0, output_path, run_multi_day_causal_feature_store_v3_0
from galapagos.features.multi_day_quality import EXPECTED_ROWS_V3_0
from galapagos.features.schemas import FEATURE_COLUMNS_V3_0, FORBIDDEN_TERMS


@pytest.fixture(scope="session")
def valid_v3_0_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v3_0_features")
    workspace = Path(__file__).resolve().parents[2]
    for timeframe in TIMEFRAMES_V3_0:
        source = v2_9_ohlcv_path(workspace, timeframe)
        destination = v2_9_ohlcv_path(root, timeframe)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    run_multi_day_causal_feature_store_v3_0(root, validate_previous_layers=False)
    return root


@pytest.fixture(scope="session")
def v3_0_frames(valid_v3_0_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v3_0_template, timeframe)) for timeframe in TIMEFRAMES_V3_0}


def test_multi_day_features_row_count_matches_input(valid_v3_0_template: Path, v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v3_0_frames.items():
        input_frame = read_parquet(v2_9_ohlcv_path(valid_v3_0_template, timeframe))
        assert len(frame) == len(input_frame) == EXPECTED_ROWS_V3_0[timeframe]


def test_multi_day_features_strict_columns(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_0_frames.values():
        assert list(frame.columns) == FEATURE_COLUMNS_V3_0


def test_multi_day_returns_are_past_only(valid_v3_0_template: Path, v3_0_frames: dict[str, pd.DataFrame]) -> None:
    input_frame = read_parquet(v2_9_ohlcv_path(valid_v3_0_template, "1m"))
    features = v3_0_frames["1m"]
    assert features.loc[1, "close_lag_1"] == pytest.approx(input_frame.loc[0, "close"])
    assert pd.isna(features.loc[0, "close_lag_1"])


def test_multi_day_rolling_features_have_expected_warmup(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_0_frames.values():
        assert frame.loc[:29, "warmup_row"].all()
        assert not bool(frame.loc[30, "warmup_row"])


def test_multi_day_temporal_features_utc(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    frame = v3_0_frames["1m"]
    assert frame.loc[0, "hour_utc"] == 0
    assert frame.loc[0, "day_of_week_utc"] == 0
    assert not bool(frame.loc[0, "is_weekend_utc"])
    assert frame.loc[5 * 1440, "is_weekend_utc"]


def test_multi_day_feature_available_ts_not_before_available_ts(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_0_frames.values():
        assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()


def test_multi_day_decision_ts_not_before_feature_available_ts(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_0_frames.values():
        assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_multi_day_no_forbidden_feature_columns(v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_0_frames.values():
        for column in frame.columns:
            if column in FEATURE_COLUMNS_V3_0:
                continue
            assert not any(term in column.casefold() for term in FORBIDDEN_TERMS)


def test_multi_day_source_hashes_match_inputs(valid_v3_0_template: Path, v3_0_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v3_0_frames.items():
        expected_sha = sha256_file(v2_9_ohlcv_path(valid_v3_0_template, timeframe))
        assert set(frame["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}
