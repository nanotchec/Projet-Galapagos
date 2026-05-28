from __future__ import annotations

import copy

from galapagos.data.aggtrades_post_v9_bad_day_repair_v9_28 import BASE_SAFETY_FLAGS_V9_28, FINDINGS
from galapagos.data.aggtrades_post_v9_bad_day_repair_v9_28_validation import (
    validate_diagnostic_v9_28,
    validate_global_validation_v9_28,
    validate_report_payload_v9_28,
    validate_safety_v9_28,
)


def valid_report_v9_28() -> dict:
    safety = dict(BASE_SAFETY_FLAGS_V9_28)
    safety.update(
        {
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
            "no_new_data_download": False,
            "no_ingestion_executed": False,
            "network_scope": "public_archive_read_only",
            "new_data_download_scope": "public_historical_aggtrades_bad_day_or_final_tail_only",
            "ingestion_scope": "public_aggtrades_bad_day_repair_or_final_tail_only",
        }
    )
    return {
        "version": "V9.28",
        "source_version": "V9.27",
        "decision": "bad_day_repaired_and_remaining_window_completed",
        "findings": dict(FINDINGS),
        "bad_day_diagnostic": {
            "date": "2026-02-11",
            "duplicate_count": 3000,
            "duplicate_exact_count": 3000,
            "duplicate_conflict_count": 0,
            "duplicate_repair_possible": True,
            "repaired_aggregate_trade_id_monotone": True,
        },
        "bad_day_repair_report": {
            "date": "2026-02-11",
            "repair_applied": True,
            "duplicate_exact_count": 3000,
            "duplicate_conflict_count": 0,
            "quality_status": "PASS",
            "after_result": {"status": "day_complete", "duplicates": 0},
        },
        "global_validation": {
            "local_file_coverage_start": "2024-05-05",
            "local_file_coverage_end": "2026-05-05",
            "complete_collection_reached": True,
            "future_full_coverage_complete": True,
            "global_duplicate_count": 0,
            "global_invalid_rows": 0,
        },
        "safety_flags": safety,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "ingestion_executed": True,
    }


def test_validator_accepts_completed_repair_report_v9_28() -> None:
    assert validate_report_payload_v9_28(valid_report_v9_28()) == []


def test_validator_rejects_repair_possible_with_conflicts_v9_28() -> None:
    report = valid_report_v9_28()
    diagnostic = copy.deepcopy(report["bad_day_diagnostic"])
    diagnostic["duplicate_conflict_count"] = 1

    errors = validate_diagnostic_v9_28(diagnostic, report)

    assert any("zero conflicting" in error for error in errors)


def test_validator_rejects_completed_decision_without_full_coverage_v9_28() -> None:
    report = valid_report_v9_28()
    global_validation = copy.deepcopy(report["global_validation"])
    global_validation["local_file_coverage_end"] = "2026-05-04"

    errors = validate_global_validation_v9_28(global_validation, report)

    assert any("target end" in error for error in errors)


def test_validator_rejects_private_network_scope_v9_28() -> None:
    report = valid_report_v9_28()
    flags = copy.deepcopy(report["safety_flags"])
    flags["network_scope"] = "private_endpoint"

    errors = validate_safety_v9_28(flags, report)

    assert any("public archive" in error for error in errors)


def test_validator_rejects_trading_flag_v9_28() -> None:
    report = valid_report_v9_28()
    report["safety_flags"]["no_trading"] = False

    errors = validate_report_payload_v9_28(report)

    assert any("no_trading" in error for error in errors)
