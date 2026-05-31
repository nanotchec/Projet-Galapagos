from __future__ import annotations

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_schemas import FEATURE_COLUMNS
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51 import MODEL_NAMES, TARGET_NAME, _baseline_comparison, _run_timeframe_models
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51_quality import scan_forbidden_features_v9_51, scan_forbidden_metrics_v9_51


def test_v9_51_feature_scan_accepts_exact_v9_49_feature_set() -> None:
    scan = scan_forbidden_features_v9_51(list(FEATURE_COLUMNS))
    assert scan["status"] == "PASS"
    assert scan["features_checked"] == len(FEATURE_COLUMNS)


def test_v9_51_timeframe_models_are_classification_only() -> None:
    rows = []
    labels = ["DOWN", "FLAT", "UP"] * 20
    splits = ["train"] * 36 + ["validation"] * 12 + ["test"] * 12
    for index, split in enumerate(splits):
        row = {column: float(index % 7) for column in FEATURE_COLUMNS}
        row.update({"split": split, TARGET_NAME: labels[index], "row_valid_for_dataset": True})
        rows.append(row)
    frame = pd.DataFrame(rows)
    metrics, shuffled, deltas = _run_timeframe_models("1h", frame)
    assert {item["model_name"] for item in metrics.values()} == set(MODEL_NAMES)
    assert all(item["metrics_scope"] == "classification_only" for item in metrics.values())
    assert shuffled
    assert deltas
    assert scan_forbidden_metrics_v9_51({"metrics": metrics})["status"] == "PASS"


def test_v9_51_baseline_comparison_uses_validation_and_test_only() -> None:
    metrics = {
        "1h.majority_class_baseline.validation": {"timeframe": "1h", "model_name": "majority_class_baseline", "split": "validation", "macro_f1": 0.2, "accuracy": 0.6},
        "1h.random_seeded_baseline.validation": {"timeframe": "1h", "model_name": "random_seeded_baseline", "split": "validation", "macro_f1": 0.25, "accuracy": 0.4},
        "1h.logistic_regression.validation": {"timeframe": "1h", "model_name": "logistic_regression", "split": "validation", "macro_f1": 0.3, "accuracy": 0.65},
        "1h.logistic_regression.train": {"timeframe": "1h", "model_name": "logistic_regression", "split": "train", "macro_f1": 0.8, "accuracy": 0.8},
    }
    comparison = _baseline_comparison(metrics)
    assert list(comparison["comparisons"]) == ["1h.logistic_regression.validation"]
    assert comparison["clear_wins_count"] == 1
