from __future__ import annotations

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_schemas import FEATURE_COLUMNS
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51 import FINDINGS, MODEL_NAMES, SAFETY_FLAGS, TARGET_NAME, VERSION
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51_validation import (
    validate_manifest_payload_v9_51,
    validate_report_payload_v9_51,
    validate_scores_payload_v9_51,
)


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "source_version": "V9.50",
        "decision": "combined_features_5y_ml_completed_but_weak_vs_baselines",
        "target_name": TARGET_NAME,
        "target": TARGET_NAME,
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "models_executed": MODEL_NAMES,
        "train_only_fit": True,
        "validation_test_not_used_for_fit": True,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "network_used": False,
        "new_data_downloaded": False,
        "forbidden_feature_scan": {"status": "PASS"},
        "forbidden_metric_scan": {"status": "PASS"},
        "no_persistent_model_check": {"status": "PASS"},
        "model_results_by_timeframe": {"1m": {}, "5m": {}, "15m": {}, "1h": {}},
        "model_results_by_split": {"1h.logistic_regression.validation": {"accuracy": 0.4}},
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def test_v9_51_report_validator_accepts_safe_payload() -> None:
    assert validate_report_payload_v9_51(_valid_report()) == []


def test_v9_51_report_validator_rejects_forbidden_execution() -> None:
    report = _valid_report()
    report["backtest_executed"] = True
    assert any("backtest" in error for error in validate_report_payload_v9_51(report))


def test_v9_51_scores_and_manifest_match_report() -> None:
    report = _valid_report()
    scores = {
        "version": VERSION,
        "contains_predictions": False,
        "contains_actionable_signal": False,
        "model_results_by_split": report["model_results_by_split"],
    }
    manifest = {"version": VERSION, "source_version": "V9.50", "decision": report["decision"], "safety_flags": report["safety_flags"]}
    assert validate_scores_payload_v9_51(scores, report) == []
    assert validate_manifest_payload_v9_51(manifest, report) == []
