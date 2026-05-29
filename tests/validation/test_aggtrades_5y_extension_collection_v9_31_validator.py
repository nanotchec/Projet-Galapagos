from __future__ import annotations

import copy

from galapagos.data.aggtrades_5y_extension_collection_v9_31 import BASE_SAFETY_FLAGS
from galapagos.data.aggtrades_5y_extension_collection_v9_31_validation import (
    validate_collection_outcome_v9_31,
    validate_report_payload_v9_31,
    validate_safety_v9_31,
    validate_windows_v9_31,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS


def valid_report_v9_31() -> dict:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "network_used": True,
            "network_scope": "public_archive_read_only",
            "new_data_downloaded": True,
            "new_data_download_scope": "public_historical_aggtrades_5y_extension_only",
            "ingestion_executed": True,
            "ingestion_scope": "public_aggtrades_bronze_silver_5y_extension_only",
            "no_new_data_download": False,
            "no_ingestion_executed": False,
        }
    )
    return {
        "version": "V9.31",
        "source_version": "V9.30",
        "status": "PASS",
        "decision": "aggtrades_5y_extension_collection_complete",
        "findings": dict(FINDINGS),
        "target_5y_window_start": "2021-05-05",
        "target_5y_window_end": "2026-05-05",
        "extension_window_start": "2021-05-05",
        "extension_window_end": "2024-05-04",
        "already_validated_window_start": "2024-05-05",
        "already_validated_window_end": "2026-05-05",
        "batches_planned_detail": [{"start_date": "2021-05-05", "end_date": "2024-05-04", "max_downloads": 60}],
        "days_expected_extension": 1096,
        "days_attempted": 1096,
        "days_complete": 1096,
        "days_missing": 0,
        "days_failed": 0,
        "days_quarantined": 0,
        "complete_extension_reached": True,
        "target_5y_collection_reached": True,
        "quality_status": "PASS",
        "coverage_status": "extension_complete",
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "safety_flags": flags,
    }


def test_v9_31_validator_accepts_valid_collection_report() -> None:
    report = valid_report_v9_31()

    assert validate_report_payload_v9_31(report) == []


def test_v9_31_validator_rejects_wrong_window() -> None:
    report = valid_report_v9_31()
    report["extension_window_end"] = "2024-05-05"

    errors = validate_windows_v9_31(report)

    assert any("extension_window_end" in error for error in errors)


def test_v9_31_validator_rejects_complete_decision_with_missing_day() -> None:
    report = valid_report_v9_31()
    report["days_missing"] = 1

    errors = validate_collection_outcome_v9_31(report)

    assert any("days_missing" in error for error in errors)


def test_v9_31_validator_rejects_ml_execution_flag() -> None:
    report = valid_report_v9_31()
    report["ml_executed"] = True

    errors = validate_collection_outcome_v9_31(report)

    assert any("ml_executed" in error for error in errors)


def test_v9_31_validator_rejects_private_endpoint_safety_flag() -> None:
    report = valid_report_v9_31()
    flags = copy.deepcopy(report["safety_flags"])
    flags["private_endpoint_used"] = True

    errors = validate_safety_v9_31(flags, report)

    assert any("private_endpoint_used" in error for error in errors)
