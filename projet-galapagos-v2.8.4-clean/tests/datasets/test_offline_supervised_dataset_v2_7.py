from __future__ import annotations

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.assembly import build_offline_supervised_dataset
from galapagos.datasets.schemas import DATASET_COLUMNS_V2_7, FORBIDDEN_DATASET_COLUMN_TERMS, JOIN_KEYS
from galapagos.datasets.splits import build_split_frame
from galapagos.features.registry import get_feature_gold_path
from galapagos.labels.registry import get_label_gold_path


def test_build_dataset_row_count_matches_features_and_labels() -> None:
    features, labels = _source_frames("1m")
    dataset = _build_dataset(features, labels, "1m")
    assert len(dataset) == len(features) == len(labels)


def test_build_dataset_strict_columns() -> None:
    features, labels = _source_frames("5m")
    dataset = _build_dataset(features, labels, "5m")
    assert list(dataset.columns) == DATASET_COLUMNS_V2_7


def test_dataset_join_keys_match_sources() -> None:
    features, labels = _source_frames("15m")
    dataset = _build_dataset(features, labels, "15m")
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], features[JOIN_KEYS], check_dtype=False)
    pd.testing.assert_frame_equal(dataset[JOIN_KEYS], labels[JOIN_KEYS], check_dtype=False)


def test_dataset_feature_values_match_source() -> None:
    features, labels = _source_frames("1h")
    dataset = _build_dataset(features, labels, "1h")
    for column in ["return_1", "rolling_vol_5", "sma_15", "feature_null_count"]:
        pd.testing.assert_series_equal(dataset[column], features[column], check_names=False, check_dtype=False)


def test_dataset_label_values_match_source() -> None:
    features, labels = _source_frames("1m")
    dataset = _build_dataset(features, labels, "1m")
    for column in ["future_close_h1", "future_log_return_h3", "up_down_flat_h5", "tail_row"]:
        pd.testing.assert_series_equal(dataset[column], labels[column], check_names=False, check_dtype=False)


def test_split_counts_sum_to_rows() -> None:
    features, labels = _source_frames("5m")
    dataset = _build_dataset(features, labels, "5m")
    counts = dataset["split"].value_counts().to_dict()
    assert sum(counts.values()) == len(dataset)
    assert set(counts) == {"train", "validation", "test"}


def test_split_temporal_order() -> None:
    features, labels = _source_frames("15m")
    dataset = _build_dataset(features, labels, "15m")
    split_frame = build_split_frame(dataset)
    assert split_frame["split_order"].is_monotonic_increasing
    assert pd.to_datetime(split_frame["event_ts"], utc=True).is_monotonic_increasing
    assert split_frame["split"].map({"train": 0, "validation": 1, "test": 2}).is_monotonic_increasing


def test_feature_available_ts_not_after_decision_ts() -> None:
    features, labels = _source_frames("1m")
    dataset = _build_dataset(features, labels, "1m")
    assert (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()


def test_label_available_ts_after_decision_ts_for_valid_labels() -> None:
    features, labels = _source_frames("1m")
    dataset = _build_dataset(features, labels, "1m")
    valid = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    assert (pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)).all()


def test_no_forbidden_dataset_columns() -> None:
    features, labels = _source_frames("5m")
    dataset = _build_dataset(features, labels, "5m")
    unexpected = [
        column
        for column in dataset.columns
        if column not in DATASET_COLUMNS_V2_7
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    assert unexpected == []


def _source_frames(timeframe: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = __import__("pathlib").Path(__file__).resolve().parents[2]
    features = pd.read_parquet(get_feature_gold_path(root, timeframe))
    labels = pd.read_parquet(get_label_gold_path(root, timeframe))
    return features, labels


def _build_dataset(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    root = __import__("pathlib").Path(__file__).resolve().parents[2]
    return build_offline_supervised_dataset(
        features,
        labels,
        feature_sha256=sha256_file(get_feature_gold_path(root, timeframe)),
        label_sha256=sha256_file(get_label_gold_path(root, timeframe)),
        dataset_run_id="v2_7_20260519T000000Z_1234abcd",
    )
