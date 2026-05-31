from __future__ import annotations

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_validation_v9_50 import (
    distribution_drift_warning_v9_50,
    distribution_stats_v9_50,
    leakage_errors_v9_50,
    validate_temporal_v9_50,
)


def test_leakage_errors_detect_feature_and_label_violations() -> None:
    ts = pd.date_range("2021-05-05", periods=3, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "decision_ts": ts,
            "feature_available_ts": [ts[0], ts[1] + pd.Timedelta(seconds=1), ts[2]],
            "label_available_ts": [ts[0] + pd.Timedelta(hours=1), ts[1] + pd.Timedelta(hours=1), ts[2]],
            "row_valid_for_dataset": [True, True, True],
        }
    )

    errors = leakage_errors_v9_50(frame)

    assert errors == {
        "feature_available_ts_gt_decision_ts": 1,
        "label_available_ts_lte_decision_ts_for_valid_rows": 1,
    }


def test_distribution_stats_flags_majority_and_entropy() -> None:
    stats = distribution_stats_v9_50({"-1": 10, "0": 80, "1": 10})

    assert stats["majority_class_ratio"] == 0.8
    assert stats["flat_ratio"] == 0.8
    assert stats["entropy"] > 0


def test_distribution_drift_warning_threshold() -> None:
    warning = distribution_drift_warning_v9_50(
        {
            "train": {"majority_class_ratio": 0.50, "flat_ratio": 0.50},
            "test": {"majority_class_ratio": 0.80, "flat_ratio": 0.80},
        }
    )

    assert warning is True


def test_validate_temporal_rejects_shuffled_split() -> None:
    ts = pd.date_range("2021-05-05", periods=4, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "decision_ts": ts,
            "event_ts": ts,
            "close_ts": ts,
            "split": ["train", "test", "validation", "test"],
            "walk_forward_group": ts.strftime("%Y-%m"),
        }
    )

    errors = validate_temporal_v9_50(frame)

    assert "split is not monotone" in errors
