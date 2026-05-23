from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galapagos.data.public_market.one_year_window import output_path as v4_2_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.one_year_window import TIMEFRAMES_V4_4, output_path
from galapagos.labels.one_year_window_quality import EXPECTED_ROWS_V4_4
from galapagos.labels.registry import THRESHOLD
from galapagos.labels.schemas import FORBIDDEN_COLUMNS_V4_4, LABEL_COLUMNS_V4_4


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v4_4_frames(project_root: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(project_root, timeframe)) for timeframe in TIMEFRAMES_V4_4}


def test_one_year_labels_row_count_matches_input(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v4_4_frames.items():
        input_frame = read_parquet(v4_2_ohlcv_path(project_root, timeframe))
        assert len(frame) == len(input_frame) == EXPECTED_ROWS_V4_4[timeframe]


def test_one_year_labels_strict_columns(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_4_frames.values():
        assert list(frame.columns) == LABEL_COLUMNS_V4_4


def test_one_year_future_close_h1_matches_shift_minus_1(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close(project_root, v4_4_frames, "1m", 1)


def test_one_year_future_close_h3_matches_shift_minus_3(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close(project_root, v4_4_frames, "5m", 3)


def test_one_year_future_close_h5_matches_shift_minus_5(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    _assert_future_close(project_root, v4_4_frames, "15m", 5)


def test_one_year_future_returns_match_future_close(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    frame = v4_4_frames["1m"]
    input_frame = read_parquet(v4_2_ohlcv_path(project_root, "1m"))
    close = input_frame["close"].astype(float)
    expected_simple = close.shift(-3) / close - 1.0
    expected_log = np.log(close.shift(-3) / close)
    pd.testing.assert_series_equal(
        frame["future_simple_return_h3"].reset_index(drop=True),
        expected_simple.reset_index(drop=True),
        check_names=False,
        check_exact=False,
    )
    pd.testing.assert_series_equal(
        frame["future_log_return_h3"].reset_index(drop=True),
        expected_log.reset_index(drop=True),
        check_names=False,
        check_exact=False,
    )


def test_one_year_direction_matches_future_log_return(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    frame = v4_4_frames["1m"]
    sample = frame.iloc[100:1000]
    expected = np.where(
        sample["future_log_return_h1"] > 0.0,
        1.0,
        np.where(sample["future_log_return_h1"] < 0.0, -1.0, 0.0),
    )
    assert np.array_equal(sample["direction_h1"].to_numpy(), expected)


def test_one_year_up_down_flat_uses_fixed_threshold(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    frame = v4_4_frames["1m"].iloc[100:1000]
    expected = np.where(
        frame["future_log_return_h1"] > THRESHOLD,
        "UP",
        np.where(frame["future_log_return_h1"] < -THRESHOLD, "DOWN", "FLAT"),
    )
    assert np.array_equal(frame["up_down_flat_h1"].to_numpy(), expected)


def test_one_year_label_available_ts_after_decision_ts_for_valid_labels(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_4_frames.values():
        valid = frame[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
        assert (pd.to_datetime(frame.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(frame.loc[valid, "decision_ts"], utc=True)).all()


def test_one_year_tail_rows_invalid_at_end(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_4_frames.values():
        assert int(frame["tail_row"].sum()) == 5
        assert frame.tail(5)["tail_row"].all()
        assert not bool(frame.iloc[-6]["tail_row"])
        assert not bool(frame.iloc[-1]["label_valid_h1"])
        assert not frame.tail(5)["label_valid_h5"].any()


def test_one_year_no_forbidden_label_columns(v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for frame in v4_4_frames.values():
        for column in frame.columns:
            if column in LABEL_COLUMNS_V4_4:
                continue
            assert not any(term in column.casefold() for term in FORBIDDEN_COLUMNS_V4_4)


def test_one_year_source_hashes_match_inputs(project_root: Path, v4_4_frames: dict[str, pd.DataFrame]) -> None:
    for timeframe, frame in v4_4_frames.items():
        expected_sha = sha256_file(v4_2_ohlcv_path(project_root, timeframe))
        assert set(frame["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}


def _assert_future_close(project_root: Path, frames: dict[str, pd.DataFrame], timeframe: str, horizon: int) -> None:
    frame = frames[timeframe]
    input_frame = read_parquet(v4_2_ohlcv_path(project_root, timeframe))
    expected = input_frame["close"].astype(float).shift(-horizon)
    pd.testing.assert_series_equal(
        frame[f"future_close_h{horizon}"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
        check_exact=False,
    )
