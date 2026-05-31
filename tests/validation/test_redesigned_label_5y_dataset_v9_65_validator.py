from __future__ import annotations

from galapagos.datasets.redesigned_label_5y_dataset_v9_65_schemas import FINDINGS, SAFETY_FLAGS, SELECTED_PRIMARY_LABEL, TIMEFRAMES, VERSION
from galapagos.datasets.redesigned_label_5y_dataset_v9_65_validation import validate_manifest_payload_v9_65, validate_report_payload_v9_65


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "decision": "redesigned_label_dataset_created",
        "target_name": SELECTED_PRIMARY_LABEL,
        "dataset_created": True,
        "ml_executed": False,
        "leakage_guard": {"status": "PASS"},
        "row_counts": {timeframe: 10 for timeframe in TIMEFRAMES},
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def test_v9_65_validator_accepts_safe_report() -> None:
    assert validate_report_payload_v9_65(_valid_report()) == []


def test_v9_65_validator_rejects_ml_execution() -> None:
    report = _valid_report()
    report["ml_executed"] = True
    assert any("ml_executed" in error for error in validate_report_payload_v9_65(report))


def test_v9_65_manifest_matches_report() -> None:
    report = _valid_report()
    manifest = {"version": VERSION, "decision": report["decision"], "target_name": report["target_name"]}
    assert validate_manifest_payload_v9_65(manifest, report) == []
