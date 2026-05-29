from __future__ import annotations

import copy

from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS
from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29 import SAFETY_FLAGS_V9_29
from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29_validation import (
    validate_calendar_v9_29,
    validate_quality_v9_29,
    validate_report_payload_v9_29,
    validate_safety_v9_29,
    validate_tail_v9_29,
)


def valid_report_v9_29() -> dict:
    return {
        "version": "V9.29",
        "source_version": "V9.28",
        "decision": "aggtrades_full_coverage_validated",
        "findings": dict(FINDINGS),
        "calendar_validation": {
            "days_expected": 731,
            "days_complete": 731,
            "days_missing": 0,
            "days_failed": 0,
            "days_partial": 0,
            "complete_calendar_coverage": True,
        },
        "quality_validation": {
            "quality_status": "PASS",
            "global_duplicate_count": 0,
            "global_invalid_rows": 0,
            "schema_mismatch_count": 0,
            "non_positive_price_count": 0,
            "non_positive_quantity_count": 0,
            "available_ts_violation_count": 0,
            "partition_mismatch_count": 0,
            "raw_read_errors": [],
            "silver_read_errors": [],
        },
        "quarantine_reconciliation": {"quarantine_blocking": False, "quarantine_active_count": 0, "active_quarantine_dates": []},
        "tail_reconciliation": {
            "tail_days_expected": 36,
            "tail_days_validated_by_v9_29": 36,
            "tail_reporting_acceptable": True,
        },
        "safety_flags": dict(SAFETY_FLAGS_V9_29),
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "days_expected": 731,
        "days_complete": 731,
        "days_missing": 0,
        "days_failed": 0,
        "days_partial": 0,
        "local_file_coverage_start": "2024-05-05",
        "local_file_coverage_end": "2026-05-05",
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "quality_status": "PASS",
    }


def test_validator_accepts_full_coverage_report_v9_29() -> None:
    assert validate_report_payload_v9_29(valid_report_v9_29()) == []


def test_validator_rejects_validated_decision_with_missing_day_v9_29() -> None:
    report = valid_report_v9_29()
    calendar = copy.deepcopy(report["calendar_validation"])
    calendar["days_missing"] = 1

    errors = validate_calendar_v9_29(calendar, report)

    assert any("days_missing=0" in error for error in errors)


def test_validator_rejects_global_duplicate_for_validated_decision_v9_29() -> None:
    report = valid_report_v9_29()
    quality = copy.deepcopy(report["quality_validation"])
    quality["global_duplicate_count"] = 1

    errors = validate_quality_v9_29(quality, report)

    assert any("global_duplicate_count=0" in error for error in errors)


def test_validator_rejects_network_usage_v9_29() -> None:
    report = valid_report_v9_29()
    flags = dict(report["safety_flags"])
    flags["network_used"] = True

    errors = validate_safety_v9_29(flags, report)

    assert any("network_used" in error for error in errors)


def test_validator_rejects_incomplete_tail_reconciliation_v9_29() -> None:
    tail = {"tail_days_expected": 36, "tail_days_validated_by_v9_29": 36, "tail_reporting_acceptable": False}

    errors = validate_tail_v9_29(tail)

    assert any("reporting acceptable" in error for error in errors)
