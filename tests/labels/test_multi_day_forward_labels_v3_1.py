from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galapagos.data.public_market.multi_day import output_path as v2_9_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.multi_day import TIMEFRAMES_V3_1, output_path, run_multi_day_label_factory_v3_1
from galapagos.labels.multi_day_quality import EXPECTED_ROWS_V3_1
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import FORBIDDEN_COLUMNS_V3_1, LABEL_COLUMNS_V3_1


@pytest.fixture(scope="session")
def valid_v3_1_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v3_1_labels")
    workspace = Path(__file__).resolve().parents[2]
    for timeframe in TIMEFRAMES_V3_1:
        source = v2_9_ohlcv_path(workspace, timeframe)
        destination = v2_9_ohlcv_path(root, timeframe)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    run_multi_day_label_factory_v3_1(root, validate_previous_layers=False)
    return root


@pytest.fixture(scope="session")
def v3_1_frames(valid_v3_1_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v3_1_template, timeframe)) for timeframe in TIMEFRAMES_V3_1}


def test_multi_day_labels_row_count_matches_input(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v3_1_frames.items():
        input_frame = read_parquet(v2_9_ohlcv_path(valid_v3_1_template, timeframe))
        assert len(frame) == len(input_frame) == EXPECTED_ROWS_V3_1[timeframe]


def test_multi_day_labels_strict_columns(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        assert list(frame.columns) == LABEL_COLUMNS_V3_1


def test_multi_day_future_close_h1_matches_shift_minus_1(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close_matches_shift(valid_v3_1_template, v3_1_frames, 1)


def test_multi_day_future_close_h3_matches_shift_minus_3(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close_matches_shift(valid_v3_1_template, v3_1_frames, 3)


def test_multi_day_future_close_h5_matches_shift_minus_5(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close_matches_shift(valid_v3_1_template, v3_1_frames, 5)


def test_multi_day_future_returns_match_future_close(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v3_1_frames.items():
        close = read_parquet(v2_9_ohlcv_path(valid_v3_1_template, timeframe))["close"].astype(float)
        for horizon in HORIZONS:
            valid = frame[f"label_valid_h{horizon}"]
            expected_simple = frame.loc[valid, f"future_close_h{horizon}"].astype(float) / close.loc[valid].astype(float) - 1.0
            expected_log = np.log(frame.loc[valid, f"future_close_h{horizon}"].astype(float) / close.loc[valid].astype(float))
            assert np.allclose(frame.loc[valid, f"future_simple_return_h{horizon}"], expected_simple)
            assert np.allclose(frame.loc[valid, f"future_log_return_h{horizon}"], expected_log)


def test_multi_day_direction_matches_future_log_return(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        for horizon in HORIZONS:
            valid = frame[f"label_valid_h{horizon}"]
            log_return = frame.loc[valid, f"future_log_return_h{horizon}"].astype(float)
            expected = np.where(log_return > 0.0, 1.0, np.where(log_return < 0.0, -1.0, 0.0))
            assert np.array_equal(frame.loc[valid, f"direction_h{horizon}"].to_numpy(dtype=float), expected)


def test_multi_day_up_down_flat_uses_fixed_threshold(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        for horizon in HORIZONS:
            valid = frame[f"label_valid_h{horizon}"]
            log_return = frame.loc[valid, f"future_log_return_h{horizon}"].astype(float)
            expected = np.where(log_return > THRESHOLD, "UP", np.where(log_return < -THRESHOLD, "DOWN", "FLAT"))
            assert list(frame.loc[valid, f"up_down_flat_h{horizon}"]) == list(expected)


def test_multi_day_label_available_ts_after_decision_ts_for_valid_labels(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        valid_any = frame[[f"label_valid_h{horizon}" for horizon in HORIZONS]].any(axis=1)
        assert (pd.to_datetime(frame.loc[valid_any, "label_available_ts"], utc=True) > pd.to_datetime(frame.loc[valid_any, "decision_ts"], utc=True)).all()


def test_multi_day_tail_rows_invalid_at_end(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        assert int(frame["tail_row"].sum()) == 5
        for horizon in HORIZONS:
            assert not frame.tail(horizon)[f"label_valid_h{horizon}"].any()
            assert frame.iloc[: -horizon][f"label_valid_h{horizon}"].all()


def test_multi_day_no_forbidden_label_columns(v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v3_1_frames.values():
        for column in frame.columns:
            if column in LABEL_COLUMNS_V3_1:
                continue
            assert not any(term in column.casefold() for term in FORBIDDEN_COLUMNS_V3_1)


def test_multi_day_source_hashes_match_inputs(valid_v3_1_template: Path, v3_1_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v3_1_frames.items():
        expected_sha = sha256_file(v2_9_ohlcv_path(valid_v3_1_template, timeframe))
        assert set(frame["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}


def _assert_future_close_matches_shift(valid_v3_1_template: Path, frames: dict[str, pd.DataFrame], horizon: int) -> None:
    for timeframe, frame in frames.items():
        input_frame = read_parquet(v2_9_ohlcv_path(valid_v3_1_template, timeframe))
        expected = input_frame["close"].astype(float).shift(-horizon)
        valid = frame[f"label_valid_h{horizon}"]
        assert np.allclose(frame.loc[valid, f"future_close_h{horizon}"].astype(float), expected.loc[valid].astype(float))
        assert frame.tail(horizon)[f"future_close_h{horizon}"].isna().all()
