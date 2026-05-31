from __future__ import annotations

from galapagos.labels.redesigned_5y_label_factory_v9_64_schemas import FINDINGS, SAFETY_FLAGS, SELECTED_PRIMARY_LABEL, TIMEFRAMES, VERSION
from galapagos.labels.redesigned_5y_label_factory_v9_64_validation import validate_manifest_payload_v9_64, validate_report_payload_v9_64


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "decision": "redesigned_labels_created",
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "labels_created": True,
        "dataset_created": False,
        "ml_executed": False,
        "leakage_guard": {"status": "PASS"},
        "row_counts": {timeframe: 10 for timeframe in TIMEFRAMES},
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def test_v9_64_validator_accepts_safe_report() -> None:
    assert validate_report_payload_v9_64(_valid_report()) == []


def test_v9_64_validator_rejects_leakage_failure() -> None:
    report = _valid_report()
    report["leakage_guard"]["status"] = "FAIL"
    assert any("leakage" in error for error in validate_report_payload_v9_64(report))


def test_v9_64_manifest_matches_report() -> None:
    report = _valid_report()
    manifest = {"version": VERSION, "decision": report["decision"], "selected_primary_label": report["selected_primary_label"]}
    assert validate_manifest_payload_v9_64(manifest, report) == []
