from __future__ import annotations

from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_validation import validate_payload_v9_7
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import (
    DATASET_COLUMNS_V9_7,
    EXPECTED_LIMITATIONS_V9_7,
    SAFETY_FLAGS_V9_7,
    TARGET_NAME_V9_7,
    VERSION_V9_7,
)


def _payload() -> dict:
    return {
        "version": VERSION_V9_7,
        "status": "PASS",
        "decision": "dataset_created_with_volnorm_labels",
        "target_name": TARGET_NAME_V9_7,
        "dataset_columns": DATASET_COLUMNS_V9_7,
        "safety": SAFETY_FLAGS_V9_7,
        "limitations": EXPECTED_LIMITATIONS_V9_7,
        "leakage_guard": {"passed": True},
    }


def test_validator_v9_7_accepts_valid_payload() -> None:
    assert validate_payload_v9_7(_payload()) == []


def test_validator_v9_7_rejects_prediction_column() -> None:
    payload = _payload()
    payload["dataset_columns"] = [*DATASET_COLUMNS_V9_7, "prediction"]
    assert "V9.7 dataset columns mismatch" in validate_payload_v9_7(payload)


def test_validator_v9_7_rejects_bad_safety() -> None:
    payload = _payload()
    payload["safety"] = {**SAFETY_FLAGS_V9_7, "trading_enabled": True}
    assert "V9.7 safety mismatch" in validate_payload_v9_7(payload)
