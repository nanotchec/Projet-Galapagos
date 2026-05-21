from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.multi_day import (
    build_multi_day_offline_supervised_dataset_v3_2,
    build_split_frame_v3_2,
    input_feature_path,
    input_label_path,
)
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V3_2,
    EXPECTED_ROWS_V3_2,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def frames() -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    loaded: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
    for timeframe in EXPECTED_ROWS_V3_2:
        features = read_parquet(input_feature_path(ROOT, timeframe))
        labels = read_parquet(input_label_path(ROOT, timeframe))
        dataset = _build_dataset(features, labels, timeframe)
        loaded[timeframe] = (features, labels, dataset)
    return loaded


def test_multi_day_dataset_row_count_matches_features_and_labels(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    for timeframe, (features, labels, dataset) in frames.items():
        assert len(dataset) == len(features) == len(labels) == EXPECTED_ROWS_V3_2[timeframe]


def test_multi_day_dataset_strict_columns(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    for _, _, dataset in frames.values():
        assert list(dataset.columns) == DATASET_COLUMNS_V3_2


def test_multi_day_dataset_join_keys_match_sources(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    features, labels, dataset = frames["15m"]
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], features[JOIN_KEYS], check_dtype=False)
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], labels[JOIN_KEYS], check_dtype=False)


def test_multi_day_dataset_feature_values_match_source(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    features, _, dataset = frames["1h"]
    for column in ["return_1", "rolling_vol_5", "sma_15", "feature_null_count"]:
        pd.testing.assert_series_equal(dataset[column], features[column], check_names=False, check_dtype=False)


def test_multi_day_dataset_label_values_match_source(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, labels, dataset = frames["1m"]
    for column in ["future_close_h1", "future_log_return_h3", "up_down_flat_h5", "tail_row"]:
        pd.testing.assert_series_equal(dataset[column], labels[column], check_names=False, check_dtype=False)


def test_multi_day_split_counts_sum_to_rows(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, _, dataset = frames["5m"]
    counts = dataset["split"].value_counts().to_dict()
    assert sum(counts.values()) == len(dataset)
    assert set(counts) == {"train", "validation", "test"}


def test_multi_day_split_temporal_order(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, _, dataset = frames["15m"]
    split_frame = build_split_frame_v3_2(dataset)
    assert split_frame["split_order"].is_monotonic_increasing
    assert pd.to_datetime(split_frame["event_ts"], utc=True).is_monotonic_increasing
    assert split_frame["split"].map({"train": 0, "validation": 1, "test": 2}).is_monotonic_increasing


def test_multi_day_feature_available_ts_not_after_decision_ts(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, _, dataset = frames["1m"]
    assert (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()


def test_multi_day_label_available_ts_after_decision_ts_for_valid_labels(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, _, dataset = frames["1m"]
    valid = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    assert (pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)).all()


def test_multi_day_no_forbidden_dataset_columns(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _, _, dataset = frames["5m"]
    unexpected = [
        column
        for column in dataset.columns
        if column not in DATASET_COLUMNS_V3_2
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    assert unexpected == []


def _build_dataset(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    return build_multi_day_offline_supervised_dataset_v3_2(
        features,
        labels,
        feature_sha256=sha256_file(input_feature_path(ROOT, timeframe)),
        label_sha256=sha256_file(input_label_path(ROOT, timeframe)),
        dataset_run_id="v3_2_20260521T000000Z_1234abcd",
    )
