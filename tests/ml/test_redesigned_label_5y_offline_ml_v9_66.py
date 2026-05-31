from __future__ import annotations

import pandas as pd

from galapagos.ml.redesigned_label_5y_offline_ml_v9_66 import MODEL_FEATURE_COLUMNS, MODEL_NAMES, TARGET_NAME, baseline_comparison_v9_66, run_timeframe_models_v9_66


def test_v9_66_timeframe_models_are_binary_classification_only() -> None:
    rows = []
    labels = ["DOWN", "UP"] * 30
    splits = ["train"] * 36 + ["validation"] * 12 + ["test"] * 12
    for index, split in enumerate(splits):
        row = {column: float(index % 5) for column in MODEL_FEATURE_COLUMNS}
        row.update({"split": split, TARGET_NAME: labels[index], "row_valid_for_dataset": True})
        rows.append(row)
    metrics, shuffled, deltas = run_timeframe_models_v9_66("1h", pd.DataFrame(rows))
    assert {item["model_name"] for item in metrics.values()} == set(MODEL_NAMES)
    assert all(item["metrics_scope"] == "classification_only" for item in metrics.values())
    assert shuffled
    assert deltas


def test_v9_66_baseline_comparison_counts_clear_wins() -> None:
    metrics = {
        "1h.majority_class_baseline.validation": {"timeframe": "1h", "model_name": "majority_class_baseline", "split": "validation", "macro_f1": 0.4, "accuracy": 0.5},
        "1h.random_seeded_baseline.validation": {"timeframe": "1h", "model_name": "random_seeded_baseline", "split": "validation", "macro_f1": 0.45, "accuracy": 0.51},
        "1h.logistic_regression.validation": {"timeframe": "1h", "model_name": "logistic_regression", "split": "validation", "macro_f1": 0.50, "accuracy": 0.55, "balanced_accuracy": 0.55},
    }
    assert baseline_comparison_v9_66(metrics)["clear_wins_count"] == 1
