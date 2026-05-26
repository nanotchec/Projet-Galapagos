from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.datasets.refined_ohlcv_trades_window_validation import (
    validate_dataset_schema_v9_1,
    validate_dataset_values_against_sources_v9_1,
    validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1,
    validate_split_frame_v9_1,
)
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V9_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1,
    SPLIT_COLUMNS_V9_1,
)


ROOT = Path(__file__).resolve().parents[2]


def test_validator_v9_1_accepts_valid_refined_dataset() -> None:
    result = validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v9_1_rejects_extra_prediction_column() -> None:
    frame = _dataset_frame()
    frame["prediction"] = 0

    errors = validate_dataset_schema_v9_1(frame, "1m")

    assert any("forbidden" in error or "schema" in error for error in errors)


def test_validator_v9_1_rejects_extra_trading_signal_column() -> None:
    frame = _dataset_frame()
    frame["trading_signal"] = "hold"

    errors = validate_dataset_schema_v9_1(frame, "1m")

    assert any("forbidden" in error or "schema" in error for error in errors)


def test_validator_v9_1_rejects_column_order_mismatch() -> None:
    frame = _dataset_frame()
    reordered = frame[[DATASET_COLUMNS_V9_1[1], DATASET_COLUMNS_V9_1[0], *DATASET_COLUMNS_V9_1[2:]]]

    errors = validate_dataset_schema_v9_1(reordered, "1m")

    assert any("schema" in error for error in errors)


def test_validator_v9_1_rejects_wrong_source_features_sha256() -> None:
    dataset = _dataset_frame()
    features = _feature_frame()
    labels = _label_frame()
    dataset["source_features_sha256"] = "bad"

    errors = validate_dataset_values_against_sources_v9_1("1m", dataset, features, labels, "run", "feature-sha", "label-sha")

    assert any("source_features_sha256" in error for error in errors)


def test_validator_v9_1_rejects_wrong_source_labels_sha256() -> None:
    dataset = _dataset_frame()
    features = _feature_frame()
    labels = _label_frame()
    dataset["source_labels_sha256"] = "bad"

    errors = validate_dataset_values_against_sources_v9_1("1m", dataset, features, labels, "run", "feature-sha", "label-sha")

    assert any("source_labels_sha256" in error for error in errors)


def test_validator_v9_1_rejects_feature_available_ts_after_decision_ts() -> None:
    dataset = _dataset_frame()
    features = _feature_frame()
    labels = _label_frame()
    dataset["feature_available_ts"] = "2023-03-25T00:02:00Z"

    errors = validate_dataset_values_against_sources_v9_1("1m", dataset, features, labels, "run", "feature-sha", "label-sha")

    assert any("feature_available_ts" in error for error in errors)


def test_validator_v9_1_rejects_label_available_ts_before_or_equal_decision_ts() -> None:
    dataset = _dataset_frame()
    features = _feature_frame()
    labels = _label_frame()
    dataset["label_available_ts"] = "2023-03-25T00:01:00Z"

    errors = validate_dataset_values_against_sources_v9_1("1m", dataset, features, labels, "run", "feature-sha", "label-sha")

    assert any("label_available_ts" in error for error in errors)


def test_validator_v9_1_rejects_temporally_shuffled_split() -> None:
    dataset = pd.concat([_dataset_frame("2023-03-25T00:01:00Z"), _dataset_frame("2023-03-25T00:00:00Z")], ignore_index=True)
    split_frame = dataset[SPLIT_COLUMNS_V9_1].copy()

    errors = validate_split_frame_v9_1(dataset, split_frame, "1m")

    assert any("temporal order" in error for error in errors)


def test_validator_v9_1_rejects_missing_walk_forward_group() -> None:
    dataset = _dataset_frame()
    split_frame = dataset[SPLIT_COLUMNS_V9_1].copy()
    split_frame["walk_forward_group"] = None

    errors = validate_split_frame_v9_1(dataset, split_frame, "1m")

    assert any("walk_forward_group" in error or "split file mismatch" in error for error in errors)


def _dataset_frame(event_ts: str = "2023-03-25T00:00:00Z") -> pd.DataFrame:
    payload = {column: [_value_for_column(column, event_ts)] for column in DATASET_COLUMNS_V9_1}
    return pd.DataFrame(payload)


def _feature_frame() -> pd.DataFrame:
    columns = [*JOIN_KEYS, "feature_available_ts", *REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1]
    payload = {column: [_value_for_column(column, "2023-03-25T00:00:00Z")] for column in columns}
    return pd.DataFrame(payload)


def _label_frame() -> pd.DataFrame:
    columns = [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]
    payload = {column: [_value_for_column(column, "2023-03-25T00:00:00Z")] for column in columns}
    return pd.DataFrame(payload)


def _value_for_column(column: str, event_ts: str) -> object:
    timestamp_values = {
        "event_ts": event_ts,
        "close_ts": "2023-03-25T00:00:59Z",
        "available_ts": "2023-03-25T00:01:00Z",
        "decision_ts": "2023-03-25T00:01:00Z",
        "feature_available_ts": "2023-03-25T00:01:00Z",
        "label_available_ts": "2023-03-25T01:01:00Z",
        "label_end_ts_h1": "2023-03-25T01:00:00Z",
        "label_end_ts_h3": "2023-03-25T03:00:00Z",
        "label_end_ts_h5": "2023-03-25T05:00:00Z",
    }
    if column in timestamp_values:
        return timestamp_values[column]
    string_values = {
        "source": "binance_archive",
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "dataset_run_id": "run",
        "dataset_schema_version": "DATASET_COLUMNS_V9_1",
        "source_features_sha256": "feature-sha",
        "source_labels_sha256": "label-sha",
        "split": "train",
        "purge_embargo_group": "none_v9_1_preview",
        "walk_forward_group": "wf_2023_03_partial",
        "direction_h1": "up",
        "direction_h3": "flat",
        "direction_h5": "down",
        "up_down_flat_h1": "up",
        "up_down_flat_h3": "flat",
        "up_down_flat_h5": "down",
    }
    if column in string_values:
        return string_values[column]
    if column.startswith("label_valid") or column in {"warmup_row", "tail_row"}:
        return True
    if column in {"split_order", "label_null_count", "label_error_count", "dataset_null_count", "dataset_error_count"}:
        return 0
    return 1.0
