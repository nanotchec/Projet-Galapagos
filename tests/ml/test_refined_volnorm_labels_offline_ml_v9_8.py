from __future__ import annotations

from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import (
    ALLOWED_FEATURE_COLUMNS_V9_8,
    MODEL_NAMES_V9_8,
    TARGET_NAME_V9_8,
    feature_leakage_scan_v9_8,
    metric_forbidden_scan_v9_8,
)


def test_v9_8_uses_refined_features_only() -> None:
    assert ALLOWED_FEATURE_COLUMNS_V9_8
    assert not feature_leakage_scan_v9_8(ALLOWED_FEATURE_COLUMNS_V9_8)["forbidden_feature_columns_present"]


def test_v9_8_allowed_models_only() -> None:
    assert MODEL_NAMES_V9_8 == ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]


def test_v9_8_target_is_volnorm_label() -> None:
    assert TARGET_NAME_V9_8 == "up_down_flat_volnorm_h1"


def test_v9_8_metric_scan_rejects_trading_metric() -> None:
    assert metric_forbidden_scan_v9_8({"metrics": {"sharpe": 1.0}})["passed"] is False
