from __future__ import annotations

import copy

from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32 import SAFETY_FLAGS_V9_32, TOTAL_DAYS_EXPECTED_5Y
from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32_validation import (
    validate_coverage_quality_v9_32,
    validate_reconciliation_v9_32,
    validate_report_payload_v9_32,
    validate_safety_v9_32,
    validate_windows_v9_32,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS


def valid_report_v9_32() -> dict:
    return {
        "version": "V9.32",
        "source_version": "V9.31",
        "status": "PASS",
        "decision": "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings",
        "findings": dict(FINDINGS),
        "target_5y_window_start": "2021-05-05",
        "target_5y_window_end": "2026-05-05",
        "days_expected_5y": TOTAL_DAYS_EXPECTED_5Y,
        "days_complete": TOTAL_DAYS_EXPECTED_5Y,
        "days_missing": 0,
        "days_failed": 0,
        "global_duplicate_count": 0,
        "global_invalid_rows": 0,
        "schema_mismatch_count": 0,
        "non_positive_price_count": 0,
        "non_positive_quantity_count": 0,
        "available_ts_violation_count": 0,
        "partition_mismatch_count": 0,
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "quality_status": "PASS",
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "reporting_inconsistency_blocking": False,
        "v9_31_counter_reconciliation": {
            "days_complete_reported": 1096,
            "days_complete_canonical": 1096,
            "reporting_inconsistency_blocking": False,
        },
        "safety_flags": dict(SAFETY_FLAGS_V9_32),
    }


def test_v9_32_validator_accepts_valid_report() -> None:
    assert validate_report_payload_v9_32(valid_report_v9_32()) == []


def test_v9_32_validator_rejects_wrong_target_window() -> None:
    report = valid_report_v9_32()
    report["target_5y_window_start"] = "2021-05-06"

    errors = validate_windows_v9_32(report)

    assert any("target_5y_window_start" in error for error in errors)


def test_v9_32_validator_rejects_missing_day_on_validated_decision() -> None:
    report = valid_report_v9_32()
    report["days_missing"] = 1

    errors = validate_coverage_quality_v9_32(report)

    assert any("days_missing" in error for error in errors)


def test_v9_32_validator_rejects_blocking_v9_31_reconciliation() -> None:
    report = valid_report_v9_32()
    report["v9_31_counter_reconciliation"]["reporting_inconsistency_blocking"] = True

    errors = validate_reconciliation_v9_32(report)

    assert any("non-blocking" in error for error in errors)


def test_v9_32_validator_rejects_ml_execution_flag() -> None:
    report = valid_report_v9_32()
    report["ml_executed"] = True

    errors = validate_coverage_quality_v9_32(report)

    assert any("ml_executed" in error for error in errors)


def test_v9_32_validator_rejects_network_usage() -> None:
    report = valid_report_v9_32()
    flags = copy.deepcopy(report["safety_flags"])
    flags["network_used"] = True

    errors = validate_safety_v9_32(flags, report)

    assert any("network_used" in error for error in errors)
