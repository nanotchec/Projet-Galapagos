from __future__ import annotations

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61 import (
    decide_v9_61,
    distribution_stats_v9_61,
    leakage_guard_v9_61,
    split_temporal_order_v9_61,
)


def test_v9_61_decision_blocks_leakage_before_quality() -> None:
    decision = decide_v9_61(
        "PASS",
        "PASS",
        "FAIL",
        {"status": "FAIL"},
        {"status": "PASS"},
        [],
        [],
    )
    assert decision == "funding_common_window_dataset_blocked_by_leakage"


def test_v9_61_split_order_is_strictly_temporal() -> None:
    frame = pd.DataFrame(
        {
            "split": ["train", "train", "validation", "validation", "test", "test"],
            "decision_ts": pd.to_datetime(
                [
                    "2021-01-01T00:00:00Z",
                    "2021-01-02T00:00:00Z",
                    "2021-01-03T00:00:00Z",
                    "2021-01-04T00:00:00Z",
                    "2021-01-05T00:00:00Z",
                    "2021-01-06T00:00:00Z",
                ],
                utc=True,
            ),
        }
    )
    assert split_temporal_order_v9_61(frame) is True


def test_v9_61_distribution_stats_reports_flat_ratio() -> None:
    stats = distribution_stats_v9_61({"-1": 2, "0": 6, "1": 2})
    assert stats["flat_ratio"] == 0.6
    assert stats["majority_class_ratio"] == 0.6
    assert stats["entropy"] > 0


def test_v9_61_leakage_guard_aggregates_results() -> None:
    result = leakage_guard_v9_61(
        {
            "1m": {"leakage_errors": {"feature_available_ts_gt_decision_ts": 0, "label_available_ts_lte_decision_ts_for_valid_rows": 0}},
            "1h": {"leakage_errors": {"feature_available_ts_gt_decision_ts": 1, "label_available_ts_lte_decision_ts_for_valid_rows": 0}},
        }
    )
    assert result["status"] == "FAIL"
    assert result["feature_available_ts_gt_decision_ts"] == 1
