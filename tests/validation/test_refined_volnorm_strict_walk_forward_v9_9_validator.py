from __future__ import annotations

from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9 import (
    ALLOWED_FEATURE_COLUMNS_V9_9,
    EXPECTED_LIMITATIONS_V9_9,
    MODEL_NAMES_V9_9,
    SAFETY_FLAGS_V9_9,
    TARGET_NAME_V9_9,
    VERSION_V9_9,
)
from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9_validation import validate_manifest_payload_v9_9


def _payload() -> dict:
    return {
        "version": VERSION_V9_9,
        "status": "PASS",
        "target_name": TARGET_NAME_V9_9,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_9,
        "models": MODEL_NAMES_V9_9,
        "safety": SAFETY_FLAGS_V9_9,
        "limitations": EXPECTED_LIMITATIONS_V9_9,
        "feature_leakage_scan": {"passed": True, "forbidden_feature_columns_present": []},
        "metrics": {},
        "aggregate_metrics": {},
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "walk_forward_validated_for_trading": False,
            "trading_allowed": False,
            "paper_live_allowed": False,
            "real_trading_allowed": False,
        },
    }


def test_validator_v9_9_accepts_valid_manifest_payload() -> None:
    assert validate_manifest_payload_v9_9(_payload()) == []


def test_validator_v9_9_rejects_strategy_validated_true() -> None:
    payload = _payload()
    payload["findings"] = {**payload["findings"], "strategy_validated": True}
    assert any("finding must be false" in error for error in validate_manifest_payload_v9_9(payload))


def test_validator_v9_9_rejects_trading_safety_true() -> None:
    payload = _payload()
    payload["safety"] = {**SAFETY_FLAGS_V9_9, "trading_enabled": True}
    assert "V9.9 safety mismatch" in validate_manifest_payload_v9_9(payload)
