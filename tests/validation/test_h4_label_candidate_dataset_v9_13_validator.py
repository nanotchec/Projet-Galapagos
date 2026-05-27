from __future__ import annotations

from copy import deepcopy

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import (
    DATASET_COLUMNS_V9_13,
    FINDINGS_V9_13,
    SAFETY_FLAGS_DATASET_V9_13,
    TARGET_NAME_V9_13,
    VERSION_V9_13_DATASET,
)
from galapagos.datasets.h4_label_candidate_dataset_v9_13_validation import (
    validate_dataset_manifest_payload_v9_13,
    validate_dataset_markdown_v9_13,
    validate_dataset_report_payload_v9_13,
)


def _valid_report() -> dict:
    return {
        "version": VERSION_V9_13_DATASET,
        "status": "PASS",
        "decision": "dataset_created_h4_label_candidate",
        "target_name": TARGET_NAME_V9_13,
        "dataset_columns": DATASET_COLUMNS_V9_13,
        "leakage_guard": {"passed": True},
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_DATASET_V9_13),
    }


def test_dataset_validator_accepts_valid_report_v9_13() -> None:
    assert validate_dataset_report_payload_v9_13(_valid_report()) == []


def test_dataset_validator_rejects_wrong_target_v9_13() -> None:
    report = _valid_report()
    report["target_name"] = "up_down_flat_volnorm_h1"

    assert "V9.13 dataset target mismatch" in validate_dataset_report_payload_v9_13(report)


def test_dataset_validator_rejects_strategy_validated_true_v9_13() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.13 dataset findings mismatch" in validate_dataset_report_payload_v9_13(report)


def test_dataset_validator_rejects_trading_safety_true_v9_13() -> None:
    report = _valid_report()
    report["safety"]["trading_enabled"] = True

    assert "V9.13 dataset safety mismatch: trading_enabled" in validate_dataset_report_payload_v9_13(report)


def test_dataset_validator_rejects_manifest_sidecar_field_v9_13() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest["sidecar_json"] = "forbidden"

    assert "V9.13 dataset manifest must not contain ZIP hash or sidecar fields" in validate_dataset_manifest_payload_v9_13(manifest, report)


def test_dataset_validator_rejects_markdown_forbidden_claim_v9_13() -> None:
    text = "Aucun backtest. Aucune strategie. Aucun signal actionnable. Aucun ordre. Aucun trading. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_dataset_markdown_v9_13(text))
