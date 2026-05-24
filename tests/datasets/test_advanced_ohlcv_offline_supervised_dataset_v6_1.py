from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from galapagos.datasets.advanced_ohlcv_window import (
    dataset_output_path,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v6_0_feature_manifest,
    split_output_path,
)
from galapagos.datasets.schemas import (
    ADVANCED_DATASET_FEATURE_COLUMNS_V6_1,
    DATASET_COLUMNS_V6_1,
    FORBIDDEN_DATASET_COLUMNS_EXACT_V6_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    SPLIT_COLUMNS_V6_1,
    TIMEFRAMES_V6_1,
)
from galapagos.features.advanced_ohlcv_schemas import ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def manifests() -> tuple[dict, dict]:
    return load_v6_0_feature_manifest(ROOT), load_v5_2_label_manifest(ROOT)


def test_advanced_dataset_row_count_matches_features_and_labels(manifests: tuple[dict, dict]) -> None:
    feature_manifest, label_manifest = manifests
    for timeframe in TIMEFRAMES_V6_1:
        dataset_path = dataset_output_path(ROOT, timeframe)
        assert _parquet_rows(dataset_path) == _parquet_rows(input_feature_path(ROOT, timeframe, feature_manifest))
        assert _parquet_rows(dataset_path) == _parquet_rows(input_label_path(ROOT, timeframe, label_manifest))
        assert _parquet_rows(dataset_path) == feature_manifest["outputs"][timeframe]["rows"]


def test_advanced_dataset_strict_columns() -> None:
    for timeframe in TIMEFRAMES_V6_1:
        assert _parquet_columns(dataset_output_path(ROOT, timeframe)) == DATASET_COLUMNS_V6_1
        assert _parquet_columns(split_output_path(ROOT, timeframe)) == SPLIT_COLUMNS_V6_1


def test_advanced_dataset_join_keys_match_sources(manifests: tuple[dict, dict]) -> None:
    feature_manifest, label_manifest = manifests
    features = _read_columns(input_feature_path(ROOT, "15m", feature_manifest), JOIN_KEYS)
    labels = _read_columns(input_label_path(ROOT, "15m", label_manifest), JOIN_KEYS)
    dataset = _read_columns(dataset_output_path(ROOT, "15m"), JOIN_KEYS)
    pd.testing.assert_frame_equal(dataset, features, check_dtype=False)
    pd.testing.assert_frame_equal(dataset, labels, check_dtype=False)


def test_advanced_dataset_feature_values_match_source(manifests: tuple[dict, dict]) -> None:
    feature_manifest, _label_manifest = manifests
    columns = ["return_1", "rolling_vol_120", "macd_like_signal", "warmup_row", "advanced_feature_null_count"]
    features = _read_columns(input_feature_path(ROOT, "1h", feature_manifest), columns)
    dataset = _read_columns(dataset_output_path(ROOT, "1h"), columns)
    pd.testing.assert_frame_equal(dataset, features, check_dtype=False, check_exact=False, atol=1e-6, rtol=1e-6)


def test_advanced_dataset_label_values_match_source(manifests: tuple[dict, dict]) -> None:
    _feature_manifest, label_manifest = manifests
    columns = ["future_close_h1", "future_log_return_h3", "up_down_flat_h5", "tail_row"]
    labels = _read_columns(input_label_path(ROOT, "1h", label_manifest), columns)
    dataset = _read_columns(dataset_output_path(ROOT, "1h"), columns)
    pd.testing.assert_frame_equal(dataset, labels, check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)


def test_advanced_dataset_contains_advanced_feature_families() -> None:
    columns = _parquet_columns(dataset_output_path(ROOT, "1h"))
    for feature_column in ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0:
        assert feature_column in columns
    for audit_column in ["warmup_row", "advanced_feature_null_count", "advanced_feature_error_count"]:
        assert audit_column in columns
    assert len(ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0) == 158


def test_advanced_dataset_allows_macd_like_signal_feature() -> None:
    columns = _parquet_columns(dataset_output_path(ROOT, "1h"))
    assert "macd_like_signal" in columns
    assert "macd_like_signal" in ADVANCED_DATASET_FEATURE_COLUMNS_V6_1
    assert "macd_like_signal" not in FORBIDDEN_DATASET_COLUMNS_EXACT_V6_1


def test_advanced_split_counts_sum_to_rows(manifests: tuple[dict, dict]) -> None:
    feature_manifest, _label_manifest = manifests
    splits = _read_columns(split_output_path(ROOT, "5m"), ["split"])
    counts = splits["split"].value_counts().to_dict()
    expected_rows = int(feature_manifest["outputs"]["5m"]["rows"])
    assert sum(counts.values()) == expected_rows
    assert counts == {
        "train": int(expected_rows * 0.6),
        "validation": int(expected_rows * 0.2),
        "test": expected_rows - int(expected_rows * 0.6) - int(expected_rows * 0.2),
    }


def test_advanced_split_temporal_order() -> None:
    splits = _read_columns(split_output_path(ROOT, "15m"), ["event_ts", "split", "split_order"])
    assert splits["split_order"].is_monotonic_increasing
    assert pd.to_datetime(splits["event_ts"], utc=True).is_monotonic_increasing
    assert splits["split"].map({"train": 0, "validation": 1, "test": 2}).is_monotonic_increasing


def test_advanced_walk_forward_groups_present() -> None:
    splits = _read_columns(split_output_path(ROOT, "1h"), ["event_ts", "walk_forward_group"])
    assert splits["walk_forward_group"].notna().all()
    assert splits["walk_forward_group"].str.startswith("wf_").all()
    assert splits["walk_forward_group"].nunique() >= 10


def test_advanced_feature_available_ts_not_after_decision_ts() -> None:
    dataset = _read_columns(dataset_output_path(ROOT, "1h"), ["feature_available_ts", "decision_ts"])
    assert (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()


def test_advanced_label_available_ts_after_decision_ts_for_valid_labels() -> None:
    dataset = _read_columns(
        dataset_output_path(ROOT, "1h"),
        ["label_available_ts", "decision_ts", "label_valid_h1", "label_valid_h3", "label_valid_h5"],
    )
    valid = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    assert (
        pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True)
        > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)
    ).all()


def test_advanced_no_forbidden_dataset_columns_except_macd_like_signal() -> None:
    forbidden_exact = set(FORBIDDEN_DATASET_COLUMNS_EXACT_V6_1)
    for timeframe in TIMEFRAMES_V6_1:
        columns = _parquet_columns(dataset_output_path(ROOT, timeframe))
        present = sorted(column for column in columns if column.casefold() in forbidden_exact)
        assert present == []
        assert "macd_like_signal" in columns


def _parquet_rows(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def _parquet_columns(path: Path) -> list[str]:
    return pq.ParquetFile(path).schema.names


def _read_columns(path: Path, columns: list[str]) -> pd.DataFrame:
    return pd.read_parquet(path, columns=columns, engine="pyarrow")
