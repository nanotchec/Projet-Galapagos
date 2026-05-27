from __future__ import annotations

from copy import deepcopy

from galapagos.research.label_failure_analysis_v9_11 import FINDINGS, SAFETY, SAFETY_FLAGS, VERSION
from galapagos.research.label_failure_analysis_v9_11_validation import (
    validate_manifest_payload_v9_11,
    validate_markdown_v9_11,
    validate_report_payload_v9_11,
)


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "status": "PASS",
        "decision_type": "label_failure_analysis_and_redesign_plan",
        "decision_recap": {
            "v9_4": {"decision": "backtest_not_justified_refine_labels"},
            "v9_5": {"decision": "label_redesign_candidate_volatility_normalized"},
            "v9_10": {"decision": "backtest_not_justified_refine_labels_again"},
        },
        "label_analysis_v9_6": {
            "target_name": "up_down_flat_volnorm_h1",
            "selected_k": 0.5,
            "timeframes": {"1m": {"class_distribution": {"FLAT": {"rate": 0.46}}}},
        },
        "ml_analysis_v9_8": {"decision": "offline_ml_completed_but_close_to_shuffled_labels"},
        "walk_forward_analysis_v9_9": {
            "decision": "strict_walk_forward_completed_but_close_to_shuffled_labels",
            "no_clear_edge_vs_shuffled_labels_count": 76,
        },
        "failure_hypotheses": [{"id": f"H{index}", "severity": "likely"} for index in range(1, 9)],
        "future_designs_compared": [{"design_id": f"design_{index}", "decision": "review_before_experiment"} for index in range(6)],
        "v9_11_decision": {"decision": "label_redesign_plan_horizon_extension"},
        "packaging_observations": {
            "exclude_icon_files_from_future_zips": True,
            "add_internal_timeouts_to_smoke_import_subprocesses": True,
            "do_not_reintroduce_sha256_sidecars": True,
        },
        "forbidden_terms_scan": {"passed": True},
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_v9_11_report_payload() -> None:
    assert validate_report_payload_v9_11(_valid_report()) == []


def test_validator_rejects_missing_no_clear_count_v9_11() -> None:
    report = _valid_report()
    report["walk_forward_analysis_v9_9"]["no_clear_edge_vs_shuffled_labels_count"] = 75

    assert "V9.11 must preserve the 76 no-clear walk-forward cases" in validate_report_payload_v9_11(report)


def test_validator_rejects_strategy_validated_true_v9_11() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.11 findings mismatch" in validate_report_payload_v9_11(report)


def test_validator_rejects_trading_safety_true_v9_11() -> None:
    report = _valid_report()
    report["safety"]["trading_enabled"] = True

    assert "V9.11 safety mismatch: trading_enabled" in validate_report_payload_v9_11(report)


def test_validator_rejects_sidecar_manifest_field_v9_11() -> None:
    report = _valid_report()
    manifest = {"version": VERSION, "status": "PASS", "decision_type": "label_failure_analysis_and_redesign_plan", "v9_11_decision": report["v9_11_decision"], "findings": report["findings"], "safety": report["safety"], "sidecar_json": "x"}

    assert "V9.11 manifest must not contain sidecar or ZIP hash fields" in validate_manifest_payload_v9_11(manifest, report)


def test_validator_rejects_forbidden_markdown_claim_v9_11() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_11(text))
