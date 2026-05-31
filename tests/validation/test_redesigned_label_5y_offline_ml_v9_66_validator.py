from __future__ import annotations

from galapagos.ml.redesigned_label_5y_offline_ml_v9_66 import FINDINGS, SAFETY_FLAGS, TARGET_NAME, VERSION
from galapagos.ml.redesigned_label_5y_offline_ml_v9_66_validation import validate_manifest_payload_v9_66, validate_report_payload_v9_66, validate_scores_payload_v9_66


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "decision": "redesigned_label_ml_completed_but_weak_vs_baselines",
        "status": "PASS",
        "target_name": TARGET_NAME,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "network_used": False,
        "new_data_downloaded": False,
        "forbidden_metric_scan": {"status": "PASS"},
        "no_persistent_model_check": {"status": "PASS"},
        "model_results_by_split": {"1h.logistic_regression.validation": {"accuracy": 0.5}},
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def test_v9_66_validator_accepts_safe_report() -> None:
    assert validate_report_payload_v9_66(_valid_report()) == []


def test_v9_66_validator_rejects_model_persistence() -> None:
    report = _valid_report()
    report["model_persisted"] = True
    assert any("model_persisted" in error for error in validate_report_payload_v9_66(report))


def test_v9_66_scores_and_manifest_match_report() -> None:
    report = _valid_report()
    scores = {"version": VERSION, "contains_predictions": False, "contains_actionable_signal": False, "model_results_by_split": report["model_results_by_split"]}
    manifest = {"version": VERSION, "decision": report["decision"], "target_name": report["target_name"]}
    assert validate_scores_payload_v9_66(scores, report) == []
    assert validate_manifest_payload_v9_66(manifest, report) == []
