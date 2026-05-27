from __future__ import annotations

from copy import deepcopy

from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import (
    FINDINGS_V9_12,
    HORIZON_EVENT_LABEL_COLUMNS_V9_12,
    SAFETY_FLAGS_V9_12,
    SAFETY_V9_12,
    VERSION_V9_12,
)
from galapagos.labels.horizon_event_label_redesign_v9_12_validation import (
    validate_manifest_payload_v9_12,
    validate_markdown_v9_12,
    validate_report_payload_v9_12,
)


def _valid_report() -> dict:
    return {
        "version": VERSION_V9_12,
        "status": "PASS",
        "full_data_available": True,
        "designs_tested": {
            "horizon_extension": {"horizons": ["h2", "h4", "h8"]},
            "event_based_diagnostic": {"classes": ["EVENT_UP", "EVENT_DOWN", "NO_EVENT", "AMBIGUOUS"]},
        },
        "recommended_candidate": {"target_name": "up_down_flat_volnorm_h4", "multiplier": 1.25},
        "comparison_with_v9_6": {"1m": {"v9_12_target": "up_down_flat_volnorm_h4"}},
        "leakage_guard": {"passed": True},
        "event_based_safety_guard": {"passed": True},
        "forbidden_output_scan": {"passed": True},
        "v9_12_decision": {"decision": "label_redesign_candidate_horizon_event_created_requires_review"},
        "findings": dict(FINDINGS_V9_12),
        "safety": dict(SAFETY_V9_12),
        "safety_flags": dict(SAFETY_FLAGS_V9_12),
    }


def test_validator_accepts_valid_v9_12_report_payload() -> None:
    assert validate_report_payload_v9_12(_valid_report()) == []


def test_validator_rejects_wrong_recommended_target_v9_12() -> None:
    report = _valid_report()
    report["recommended_candidate"]["target_name"] = "up_down_flat_volnorm_h1"

    assert "V9.12 recommended candidate must be up_down_flat_volnorm_h4" in validate_report_payload_v9_12(report)


def test_validator_rejects_strategy_validated_true_v9_12() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.12 findings mismatch" in validate_report_payload_v9_12(report)


def test_validator_rejects_backtest_safety_true_v9_12() -> None:
    report = _valid_report()
    report["safety"]["backtest_enabled"] = True

    assert "V9.12 safety mismatch" in validate_report_payload_v9_12(report)


def test_validator_rejects_zip_sha256_field_v9_12() -> None:
    report = _valid_report()
    report["zip_sha256"] = "forbidden"

    assert any("forbidden hash or sidecar field" in error for error in validate_report_payload_v9_12(report))


def test_validator_rejects_manifest_schema_mismatch_v9_12() -> None:
    report = _valid_report()
    manifest = {
        "version": VERSION_V9_12,
        "status": "PASS",
        "label_columns": HORIZON_EVENT_LABEL_COLUMNS_V9_12[:-1],
        "v9_12_decision": report["v9_12_decision"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }

    assert "V9.12 manifest schema mismatch" in validate_manifest_payload_v9_12(manifest, report)


def test_validator_rejects_markdown_forbidden_claim_v9_12() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun sidecar. Aucune empreinte ZIP. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_12(text))


def test_validator_accepts_required_markdown_safety_phrases_v9_12() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun sidecar. Aucune empreinte ZIP."

    assert validate_markdown_v9_12(text) == []
