from __future__ import annotations

from copy import deepcopy

from galapagos.ml.h4_label_candidate_offline_ml_v9_13 import (
    FINDINGS_V9_13,
    MODEL_NAMES_V9_13,
    SAFETY_FLAGS_ML_V9_13,
    TARGET_NAME_V9_13,
    VERSION_V9_13_ML,
)
from galapagos.ml.h4_label_candidate_offline_ml_v9_13_validation import (
    validate_ml_manifest_payload_v9_13,
    validate_ml_markdown_v9_13,
    validate_ml_report_payload_v9_13,
)


def _valid_report() -> dict:
    return {
        "version": VERSION_V9_13_ML,
        "status": "PASS",
        "decision": "h4_offline_ml_completed_but_close_to_shuffled_labels",
        "global_decision": {"decision": "h4_candidate_not_ready_refine_labels_again"},
        "target_name": TARGET_NAME_V9_13,
        "models": MODEL_NAMES_V9_13,
        "feature_leakage_scan": {"passed": True},
        "metric_forbidden_scan": {"passed": True},
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_ML_V9_13),
    }


def test_ml_validator_accepts_valid_report_v9_13() -> None:
    assert validate_ml_report_payload_v9_13(_valid_report()) == []


def test_ml_validator_rejects_unknown_model_set_v9_13() -> None:
    report = _valid_report()
    report["models"] = [*MODEL_NAMES_V9_13, "random_forest"]

    assert "V9.13 ML models mismatch" in validate_ml_report_payload_v9_13(report)


def test_ml_validator_rejects_leakage_scan_failure_v9_13() -> None:
    report = _valid_report()
    report["feature_leakage_scan"]["passed"] = False

    assert "V9.13 ML leakage scan must pass" in validate_ml_report_payload_v9_13(report)


def test_ml_validator_rejects_backtest_enabled_true_v9_13() -> None:
    report = _valid_report()
    report["safety"]["backtest_enabled"] = True

    assert "V9.13 ML safety mismatch: backtest_enabled" in validate_ml_report_payload_v9_13(report)


def test_ml_validator_rejects_strategy_validated_true_v9_13() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.13 ML findings mismatch" in validate_ml_report_payload_v9_13(report)


def test_ml_validator_rejects_manifest_sidecar_field_v9_13() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest["sidecar_txt"] = "forbidden"

    assert "V9.13 ML manifest must not contain ZIP hash or sidecar fields" in validate_ml_manifest_payload_v9_13(manifest, report)


def test_ml_validator_rejects_markdown_forbidden_claim_v9_13() -> None:
    text = "Aucun backtest. Aucune strategie. Aucun signal actionnable. Aucun ordre. Aucun modele persistant. Aucun trading. live trading ready"

    assert any("forbidden claim" in error for error in validate_ml_markdown_v9_13(text))
