from __future__ import annotations

from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9 import (
    ALLOWED_FEATURE_COLUMNS_V9_9,
    MODEL_NAMES_V9_9,
    TARGET_NAME_V9_9,
    WALK_FORWARD_POLICY_V9_3,
    feature_leakage_scan_v9_8,
)


def test_v9_9_walk_forward_policy_strict() -> None:
    assert WALK_FORWARD_POLICY_V9_3["shuffle"] is False
    assert WALK_FORWARD_POLICY_V9_3["purge_bars"] == 5
    assert WALK_FORWARD_POLICY_V9_3["embargo_bars"] == 5


def test_v9_9_target_and_features_are_volnorm_safe() -> None:
    assert TARGET_NAME_V9_9 == "up_down_flat_volnorm_h1"
    assert feature_leakage_scan_v9_8(ALLOWED_FEATURE_COLUMNS_V9_9)["passed"] is True


def test_v9_9_allowed_models_only() -> None:
    assert MODEL_NAMES_V9_9 == ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
