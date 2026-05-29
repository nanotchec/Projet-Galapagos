from __future__ import annotations

import copy

from galapagos.data.aggtrades_5y_extension_plan_v9_30 import SAFETY_FLAGS_V9_30
from galapagos.data.aggtrades_5y_extension_plan_v9_30_validation import (
    validate_collection_plan_v9_30,
    validate_report_payload_v9_30,
    validate_safety_v9_30,
    validate_source_v9_30,
    validate_windows_v9_30,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS


def valid_report_v9_30() -> dict:
    return {
        "version": "V9.30",
        "source_version": "V9.29",
        "decision": "aggtrades_5y_extension_plan_ready",
        "mode": "plan-only",
        "findings": dict(FINDINGS),
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "target_5y_window_start": "2021-05-05",
        "target_5y_window_end": "2026-05-05",
        "target_5y_days_expected": 1827,
        "already_validated_days": 731,
        "extension_window_start": "2021-05-05",
        "extension_window_end": "2024-05-04",
        "extension_days_needed": 1096,
        "safe_for_5y_extension_collection": True,
        "estimated_volume": {
            "safety_margin_factor": 1.3,
            "estimated_extension_raw_bytes": 100,
            "estimated_extension_silver_bytes": 200,
            "estimated_extension_total_bytes": 300,
            "required_free_bytes_for_extension": 390,
        },
        "source_availability_assessment": {
            "host": "data.binance.vision",
            "availability_needs_confirmation": True,
            "network_check_required_in_future_collection": True,
        },
        "collection_plan_v9_31": [
            {
                "start_date": "2021-05-05",
                "end_date": "2021-05-06",
                "expected_days": 2,
                "max_downloads": 2,
                "overwrite_complete_days": False,
            },
            {
                "start_date": "2021-05-07",
                "end_date": "2024-05-04",
                "expected_days": 1094,
                "max_downloads": 90,
                "overwrite_complete_days": False,
            },
        ],
        "safety_flags": dict(SAFETY_FLAGS_V9_30),
    }


def test_validator_accepts_valid_plan_report_v9_30() -> None:
    report = valid_report_v9_30()
    report["collection_plan_v9_31"] = [
        {"start_date": "2021-05-05", "end_date": "2024-05-04", "expected_days": 1096, "max_downloads": 90, "overwrite_complete_days": False}
    ]

    assert validate_report_payload_v9_30(report) == []


def test_validator_rejects_wrong_extension_days_v9_30() -> None:
    report = valid_report_v9_30()
    report["extension_days_needed"] = 1095

    errors = validate_windows_v9_30(report)

    assert any("extension_days_needed" in error for error in errors)


def test_validator_rejects_source_without_future_confirmation_v9_30() -> None:
    source = copy.deepcopy(valid_report_v9_30()["source_availability_assessment"])
    source["availability_needs_confirmation"] = False

    errors = validate_source_v9_30(source)

    assert any("future availability" in error for error in errors)


def test_validator_rejects_batch_over_ninety_days_v9_30() -> None:
    report = valid_report_v9_30()
    batches = [{"start_date": "2021-05-05", "end_date": "2024-05-04", "expected_days": 1096, "max_downloads": 1096, "overwrite_complete_days": False}]

    errors = validate_collection_plan_v9_30(batches, report)

    assert any("90 days" in error for error in errors)


def test_validator_rejects_network_safety_flag_v9_30() -> None:
    flags = dict(SAFETY_FLAGS_V9_30)
    flags["network_used"] = True

    errors = validate_safety_v9_30(flags)

    assert any("network_used" in error for error in errors)
