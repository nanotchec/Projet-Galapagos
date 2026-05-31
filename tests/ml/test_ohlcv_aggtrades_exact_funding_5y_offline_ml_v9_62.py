from __future__ import annotations

import pandas as pd

from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62 import (
    FEATURE_VARIANT_WITH_FUNDING,
    FEATURE_VARIANT_WITHOUT_FUNDING,
    MODEL_FEATURE_COLUMNS_WITH_FUNDING,
    MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING,
    MODEL_NAMES,
    TARGET_NAME,
    baseline_comparison_v9_62,
    funding_ablation_comparison_v9_62,
    run_timeframe_models_v9_62,
)
from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_quality import scan_forbidden_features_v9_62, scan_forbidden_metrics_v9_62


def test_v9_62_feature_variants_are_nested_and_safe() -> None:
    assert set(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING).issubset(set(MODEL_FEATURE_COLUMNS_WITH_FUNDING))
    assert len(MODEL_FEATURE_COLUMNS_WITH_FUNDING) > len(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING)
    assert scan_forbidden_features_v9_62(list(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING))["status"] == "PASS"
    assert scan_forbidden_features_v9_62(list(MODEL_FEATURE_COLUMNS_WITH_FUNDING))["status"] == "PASS"


def test_v9_62_timeframe_models_are_classification_only() -> None:
    rows = []
    labels = ["DOWN", "FLAT", "UP"] * 20
    splits = ["train"] * 36 + ["validation"] * 12 + ["test"] * 12
    for index, split in enumerate(splits):
        row = {column: float(index % 7) for column in MODEL_FEATURE_COLUMNS_WITH_FUNDING}
        row.update({"split": split, TARGET_NAME: labels[index], "row_valid_for_dataset": True})
        rows.append(row)
    frame = pd.DataFrame(rows)
    metrics, shuffled, deltas, variant_rows = run_timeframe_models_v9_62("1h", frame)
    assert {item["model_name"] for item in metrics.values()} == set(MODEL_NAMES)
    assert {item["feature_variant"] for item in metrics.values()} == {FEATURE_VARIANT_WITHOUT_FUNDING, FEATURE_VARIANT_WITH_FUNDING}
    assert all(item["metrics_scope"] == "classification_only" for item in metrics.values())
    assert shuffled
    assert deltas
    assert variant_rows[FEATURE_VARIANT_WITH_FUNDING] == len(frame)
    assert scan_forbidden_metrics_v9_62({"metrics": metrics})["status"] == "PASS"


def test_v9_62_ablation_compares_funding_against_no_funding() -> None:
    metrics = {
        "1h.without_funding.majority_class_baseline.validation": {"timeframe": "1h", "feature_variant": FEATURE_VARIANT_WITHOUT_FUNDING, "model_name": "majority_class_baseline", "split": "validation", "macro_f1": 0.2, "accuracy": 0.6},
        "1h.without_funding.random_seeded_baseline.validation": {"timeframe": "1h", "feature_variant": FEATURE_VARIANT_WITHOUT_FUNDING, "model_name": "random_seeded_baseline", "split": "validation", "macro_f1": 0.25, "accuracy": 0.4},
        "1h.without_funding.logistic_regression.validation": {"timeframe": "1h", "feature_variant": FEATURE_VARIANT_WITHOUT_FUNDING, "model_name": "logistic_regression", "split": "validation", "macro_f1": 0.3, "accuracy": 0.65, "balanced_accuracy": 0.31},
        "1h.with_funding.logistic_regression.validation": {"timeframe": "1h", "feature_variant": FEATURE_VARIANT_WITH_FUNDING, "model_name": "logistic_regression", "split": "validation", "macro_f1": 0.33, "accuracy": 0.67, "balanced_accuracy": 0.34},
    }
    comparison = funding_ablation_comparison_v9_62(metrics)
    assert comparison["clear_improvement_with_funding_count"] == 1
    baseline = baseline_comparison_v9_62(metrics)
    assert baseline["clear_wins_count"] >= 1
