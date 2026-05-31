from __future__ import annotations

from galapagos.research.label_redesign_diagnostic_v9_63 import FINDINGS, SAFETY_FLAGS, VERSION
from galapagos.research.label_redesign_diagnostic_v9_63_validation import validate_manifest_payload_v9_63, validate_report_payload_v9_63


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "decision": "label_redesign_candidate_binary_directional",
        "selected_primary_label": "binary_directional_volnorm_h4_5y",
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "selection_methodology": {"selected_from_ml_performance": False},
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def test_v9_63_validator_accepts_safe_report() -> None:
    assert validate_report_payload_v9_63(_valid_report()) == []


def test_v9_63_validator_rejects_ml_based_selection() -> None:
    report = _valid_report()
    report["selection_methodology"]["selected_from_ml_performance"] = True
    assert any("ML performance" in error for error in validate_report_payload_v9_63(report))


def test_v9_63_manifest_matches_report() -> None:
    report = _valid_report()
    manifest = {"version": VERSION, "decision": report["decision"], "selected_primary_label": report["selected_primary_label"]}
    assert validate_manifest_payload_v9_63(manifest, report) == []
