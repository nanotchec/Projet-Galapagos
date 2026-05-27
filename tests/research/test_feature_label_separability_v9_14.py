from __future__ import annotations

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13
from galapagos.research.feature_label_separability_v9_14 import (
    SAFETY_FLAGS,
    class_separability_v9_14,
    compute_univariate_separability_v9_14,
    decide_v9_14,
    distribution_by_group_v9_14,
    forbidden_metric_scan_v9_14,
)


def _frame() -> pd.DataFrame:
    labels = ["DOWN", "DOWN", "FLAT", "FLAT", "UP", "UP"] * 6
    frame = pd.DataFrame(
        {
            TARGET_NAME_V9_13: labels,
            "split": ["train"] * 18 + ["validation"] * 9 + ["test"] * 9,
        }
    )
    for index, feature in enumerate(ML_FEATURE_COLUMNS_V9_13):
        if feature == ML_FEATURE_COLUMNS_V9_13[0]:
            frame[feature] = [-2.0 if label == "DOWN" else 0.0 if label == "FLAT" else 2.0 for label in labels]
        elif feature == ML_FEATURE_COLUMNS_V9_13[1]:
            frame[feature] = [0.1 * (row % 3) for row in range(len(labels))]
        else:
            frame[feature] = float(index)
    return frame


def test_univariate_separability_ranks_discriminating_feature_v9_14() -> None:
    scores = compute_univariate_separability_v9_14(_frame(), ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13)

    assert scores[0]["feature_name"] == ML_FEATURE_COLUMNS_V9_13[0]
    assert scores[0]["eta_squared"] > 0.90
    assert scores[-1]["eta_squared"] == 0.0


def test_class_separability_identifies_all_classes_v9_14() -> None:
    result = class_separability_v9_14(_frame(), ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13)

    assert set(result["by_class"]) == {"DOWN", "FLAT", "UP"}
    assert result["weakest_class"] in {"DOWN", "FLAT", "UP"}


def test_distribution_by_group_has_rates_v9_14() -> None:
    distribution = distribution_by_group_v9_14(_frame(), "split", TARGET_NAME_V9_13)

    assert set(distribution) == {"train", "validation", "test"}
    assert abs(sum(item["rate"] for item in distribution["train"].values()) - 1.0) < 1e-9


def test_decision_is_feature_first_when_no_clear_wins_and_weak_common_features_v9_14() -> None:
    decision = decide_v9_14(
        [],
        {
            "learned_vs_baselines": {"clear_wins_count": 0},
            "learned_vs_shuffled_labels": {"no_clear_edge_vs_shuffled_labels_count": 14},
        },
        {"summary": {"common_top_features_count": 0}},
    )

    assert decision["decision"] == "feature_first_before_more_labels"
    assert "V9.15 Feature" in decision["next_step_recommendation"]


def test_forbidden_metric_scan_rejects_trading_metrics_v9_14() -> None:
    clean = forbidden_metric_scan_v9_14({"metric": "macro_f1"})
    dirty = forbidden_metric_scan_v9_14({"metric": "sharpe"})

    assert clean["passed"] is True
    assert dirty["passed"] is False


def test_safety_flags_disable_walk_forward_and_backtest_v9_14() -> None:
    assert SAFETY_FLAGS["no_backtest"] is True
    assert SAFETY_FLAGS["no_walk_forward"] is True
    assert SAFETY_FLAGS["no_trading"] is True
