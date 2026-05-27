from __future__ import annotations

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13 import (
    assign_temporal_splits_v9_13,
    build_h4_label_candidate_dataset_frame_v9_13,
    leakage_guard_v9_13,
    target_distribution_v9_13,
)
from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import (
    DATASET_COLUMNS_V9_13,
    FEATURE_COLUMNS_V9_13,
    TARGET_NAME_V9_13,
)


def _features(rows: int = 20) -> pd.DataFrame:
    ts = pd.date_range("2023-03-25", periods=rows, freq="h", tz="UTC")
    data = {
        "source": "binance_archive",
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "event_ts": ts,
        "close_ts": ts,
        "available_ts": ts,
        "decision_ts": ts,
        "feature_available_ts": ts,
    }
    for column in FEATURE_COLUMNS_V9_13:
        data[column] = False if column == "warmup_row" else 1.0
    return pd.DataFrame(data)


def _labels(rows: int = 20) -> pd.DataFrame:
    ts = pd.date_range("2023-03-25", periods=rows, freq="h", tz="UTC")
    labels = ["DOWN", "FLAT", "UP", "UP"] * 5
    return pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "event_ts": ts,
            "close_ts": ts,
            "decision_ts": ts,
            "label_available_ts": ts + pd.Timedelta(hours=4),
            "label_start_ts": ts,
            "label_end_ts": ts + pd.Timedelta(hours=4),
            "label_run_id": "test",
            "label_schema_version": "test",
            "source_dataset_version": "V9.7",
            "source_label_design_version": "V9.12",
            "candidate_family": "horizon_extension",
            "target_name": TARGET_NAME_V9_13,
            "horizon_name": "h4",
            "horizon_duration_minutes": 240,
            "future_log_return": 0.01,
            "causal_vol_window_bars": 30,
            "causal_vol_min_periods": 10,
            "causal_realized_vol": 0.02,
            "volatility_threshold_multiplier": 1.25,
            "volatility_normalized_threshold": 0.025,
            "up_down_flat_volnorm_h2": labels,
            "up_down_flat_volnorm_h4": labels,
            "up_down_flat_volnorm_h8": labels,
            "event_based_label": "NO_EVENT",
            "event_horizon_name": "h8",
            "event_threshold_multiplier": 3.0,
            "event_valid": True,
            "label_valid": True,
            "label_invalid_reason": "valid",
            "warmup_row": False,
            "label_null_count": 0,
            "label_error_count": 0,
        }
    )


def test_build_h4_dataset_schema_and_target_v9_13() -> None:
    dataset = build_h4_label_candidate_dataset_frame_v9_13(
        _features(),
        _labels(),
        source_features_path="features.parquet",
        source_labels_path="labels.parquet",
        dataset_run_id="test",
    )

    assert list(dataset.columns) == DATASET_COLUMNS_V9_13
    assert dataset["target_name"].unique().tolist() == [TARGET_NAME_V9_13]
    assert "event_based_label" not in FEATURE_COLUMNS_V9_13
    assert dataset["label_available_ts"].gt(dataset["decision_ts"]).all()


def test_temporal_splits_are_not_shuffled_v9_13() -> None:
    split = assign_temporal_splits_v9_13(_features(100))

    assert split["split"].iloc[0] == "train"
    assert split["split"].iloc[60] == "validation"
    assert split["split"].iloc[80] == "test"
    assert split["split_order"].is_monotonic_increasing


def test_target_distribution_contains_three_classes_v9_13() -> None:
    dataset = build_h4_label_candidate_dataset_frame_v9_13(
        _features(),
        _labels(),
        source_features_path="features.parquet",
        source_labels_path="labels.parquet",
        dataset_run_id="test",
    )
    distribution = target_distribution_v9_13(dataset)

    assert set(distribution["class_distribution"]) == {"DOWN", "FLAT", "UP"}
    assert distribution["majority_rate"] < 0.70


def test_leakage_guard_confirms_label_exclusions_v9_13() -> None:
    guard = leakage_guard_v9_13()

    assert guard["passed"] is True
    assert guard["event_based_label_excluded_from_features"] is True
    assert guard["v9_12_label_columns_excluded_from_features"] is True
    assert guard["future_columns_excluded_from_features"] is True
