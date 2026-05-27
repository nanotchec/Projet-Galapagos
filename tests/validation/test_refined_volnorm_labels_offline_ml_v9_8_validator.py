from __future__ import annotations

from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import (
    ALLOWED_FEATURE_COLUMNS_V9_8,
    EXPECTED_LIMITATIONS_V9_8,
    MODEL_NAMES_V9_8,
    SAFETY_FLAGS_V9_8,
    TARGET_NAME_V9_8,
    VERSION_V9_8,
)
from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8_validation import validate_manifest_payload_v9_8


def _payload() -> dict:
    return {
        "version": VERSION_V9_8,
        "status": "PASS",
        "target_name": TARGET_NAME_V9_8,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_8,
        "models": MODEL_NAMES_V9_8,
        "safety": SAFETY_FLAGS_V9_8,
        "limitations": EXPECTED_LIMITATIONS_V9_8,
        "feature_leakage_scan": {"passed": True, "forbidden_feature_columns_present": []},
        "metrics": {},
        "walk_forward_metrics": {},
    }


def test_validator_v9_8_accepts_valid_manifest_payload() -> None:
    assert validate_manifest_payload_v9_8(_payload()) == []


def test_validator_v9_8_rejects_forbidden_feature() -> None:
    payload = _payload()
    payload["feature_columns"] = [*ALLOWED_FEATURE_COLUMNS_V9_8, "future_log_return_h1"]
    assert "V9.8 feature columns mismatch" in validate_manifest_payload_v9_8(payload)


def test_validator_v9_8_rejects_unknown_model() -> None:
    payload = _payload()
    payload["models"] = [*MODEL_NAMES_V9_8, "random_forest"]
    assert "V9.8 model list mismatch" in validate_manifest_payload_v9_8(payload)
