from __future__ import annotations

from copy import deepcopy

from galapagos.research.feature_label_separability_v9_14 import (
    DECISION_TYPE,
    FINDINGS,
    SAFETY,
    SAFETY_FLAGS,
    TARGET_NAME_V9_13,
    VERSION,
)
from galapagos.research.feature_label_separability_v9_14_validation import (
    validate_manifest_payload_v9_14,
    validate_markdown_v9_14,
    validate_report_payload_v9_14,
)


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "status": "PASS",
        "decision_type": DECISION_TYPE,
        "target_name": TARGET_NAME_V9_13,
        "label_diagnostic_v9_13": {"timeframes": {"1m": {}, "1h": {}}},
        "ml_diagnostic_v9_13": {
            "learned_vs_baselines": {"clear_wins_count": 0},
            "learned_vs_shuffled_labels": {"no_clear_edge_vs_shuffled_labels_count": 14},
            "walk_forward_not_repeated_in_v9_14": True,
        },
        "feature_label_separability": {
            "model_training_performed": False,
            "signal_produced": False,
            "by_timeframe": {"1m": {"top_features": ["a"]}},
        },
        "hypotheses": [{"id": f"H{index}", "hypothesis": "x"} for index in range(1, 9)],
        "v9_14_decision": {"decision": "feature_first_before_more_labels"},
        "forbidden_metric_scan": {"passed": True},
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_report_v9_14() -> None:
    assert validate_report_payload_v9_14(_valid_report()) == []


def test_validator_rejects_wrong_no_clear_count_v9_14() -> None:
    report = _valid_report()
    report["ml_diagnostic_v9_13"]["learned_vs_shuffled_labels"]["no_clear_edge_vs_shuffled_labels_count"] = 13

    assert "V9.14 must preserve V9.13 no-clear shuffle count" in validate_report_payload_v9_14(report)


def test_validator_rejects_walk_forward_repeated_v9_14() -> None:
    report = _valid_report()
    report["ml_diagnostic_v9_13"]["walk_forward_not_repeated_in_v9_14"] = False

    assert "V9.14 must not repeat walk-forward" in validate_report_payload_v9_14(report)


def test_validator_rejects_model_training_true_v9_14() -> None:
    report = _valid_report()
    report["feature_label_separability"]["model_training_performed"] = True

    assert "V9.14 separability must not train a model" in validate_report_payload_v9_14(report)


def test_validator_rejects_forbidden_metric_scan_failure_v9_14() -> None:
    report = _valid_report()
    report["forbidden_metric_scan"]["passed"] = False

    assert "V9.14 forbidden metric scan must pass" in validate_report_payload_v9_14(report)


def test_validator_rejects_strategy_validated_true_v9_14() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.14 findings mismatch" in validate_report_payload_v9_14(report)


def test_validator_rejects_sidecar_field_v9_14() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest["sidecar_json"] = "forbidden"

    assert "V9.14 manifest must not contain sidecar or ZIP hash fields" in validate_manifest_payload_v9_14(manifest, report)


def test_validator_rejects_markdown_forbidden_claim_v9_14() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_14(text))


def test_validator_rejects_markdown_trading_metric_v9_14() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. Sharpe."

    assert any("forbidden metric term" in error for error in validate_markdown_v9_14(text))
