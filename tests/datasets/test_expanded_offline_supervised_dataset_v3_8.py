from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.expanded_window import input_feature_path, input_label_path
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V3_8,
    EXPECTED_ROWS_V3_8,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
    get_dataset_v3_8_path,
    get_split_v3_8_path,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def frames() -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    loaded: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
    for timeframe in EXPECTED_ROWS_V3_8:
        features = read_parquet(input_feature_path(ROOT, timeframe))
        labels = read_parquet(input_label_path(ROOT, timeframe))
        dataset = read_parquet(get_dataset_v3_8_path(ROOT, timeframe))
        splits = read_parquet(get_split_v3_8_path(ROOT, timeframe))
        loaded[timeframe] = (features, labels, dataset, splits)
    return loaded


def test_expanded_dataset_row_count_matches_features_and_labels(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    for timeframe, (features, labels, dataset, _splits) in frames.items():
        assert len(dataset) == len(features) == len(labels) == EXPECTED_ROWS_V3_8[timeframe]


def test_expanded_dataset_strict_columns(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    for _features, _labels, dataset, _splits in frames.values():
        assert list(dataset.columns) == DATASET_COLUMNS_V3_8


def test_expanded_dataset_join_keys_match_sources(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset, _splits = frames["15m"]
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], features[JOIN_KEYS], check_dtype=False)
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], labels[JOIN_KEYS], check_dtype=False)


def test_expanded_dataset_feature_values_match_source(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, _labels, dataset, _splits = frames["1h"]
    for column in ["return_1", "rolling_vol_5", "sma_15", "feature_null_count"]:
        pd.testing.assert_series_equal(dataset[column], features[column], check_names=False, check_dtype=False)


def test_expanded_dataset_label_values_match_source(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, labels, dataset, _splits = frames["1m"]
    for column in ["future_close_h1", "future_log_return_h3", "up_down_flat_h5", "tail_row"]:
        pd.testing.assert_series_equal(dataset[column], labels[column], check_names=False, check_dtype=False)


def test_expanded_split_counts_sum_to_rows(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _features, _labels, dataset, splits = frames["5m"]
    counts = dataset["split"].value_counts().to_dict()
    assert sum(counts.values()) == len(dataset)
    assert set(counts) == {"train", "validation", "test"}
    assert len(splits) == len(dataset)


def test_expanded_split_temporal_order(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]) -> None:
    _features, _labels, _dataset, splits = frames["15m"]
    assert splits["split_order"].is_monotonic_increasing
    assert pd.to_datetime(splits["event_ts"], utc=True).is_monotonic_increasing
    assert splits["split"].map({"train": 0, "validation": 1, "test": 2}).is_monotonic_increasing


def test_expanded_feature_available_ts_not_after_decision_ts(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = frames["1m"]
    assert (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()


def test_expanded_label_available_ts_after_decision_ts_for_valid_labels(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = frames["1m"]
    valid = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    assert (pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)).all()


def test_expanded_no_forbidden_dataset_columns(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = frames["5m"]
    unexpected = [
        column
        for column in dataset.columns
        if column not in DATASET_COLUMNS_V3_8
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    assert unexpected == []
