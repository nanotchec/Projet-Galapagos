from __future__ import annotations

import copy

from galapagos.data.aggtrades_post_v9_storage_recheck_resume_v9_27_validation import (
    validate_disk_preflight_v9_27,
    validate_report_payload_v9_27,
    validate_safety_v9_27,
)


def valid_report_v9_27() -> dict:
    return {
        "version": "V9.27",
        "source_version": "V9.26",
        "decision": "storage_recheck_not_executed_measurement_discrepancy",
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "walk_forward_validated_for_trading": False,
            "trading_allowed": False,
            "paper_live_allowed": False,
            "real_trading_allowed": False,
        },
        "canonical_coverage_before_resume": {
            "target_window_start": "2024-05-05",
            "target_window_end": "2026-05-05",
            "first_missing_day": "2025-02-04",
            "last_complete_day_before_gap": "2025-02-03",
            "days_partial": 0,
            "days_complete": 276,
            "state_reconciled": True,
        },
        "disk_preflight": {
            "minimum_free_bytes_required": 60 * 1024**3,
            "free_bytes_project_mount": 59 * 1024**3,
            "free_bytes_data_mount": 59 * 1024**3,
            "raw_bytes_current": 10,
            "silver_bytes_current": 20,
            "quarantine_bytes_current": 0,
            "batch_size_days": 0,
            "measurement_discrepancy_detected": True,
        },
        "storage_recheck_summary": {
            "target_window_start": "2024-05-05",
            "target_window_end": "2026-05-05",
            "batches_executed": 0,
            "batches_planned": 0,
            "days_quarantined_total": 0,
            "days_failed_total": 0,
            "complete_collection_reached": False,
            "days_attempted_total": 0,
        },
        "safety_flags": {
            "no_trading": True,
            "no_paper_live": True,
            "no_orders": True,
            "no_backtest": True,
            "no_walk_forward": True,
            "no_strategy": True,
            "no_actionable_signal": True,
            "no_persistent_model": True,
            "api_key_used": False,
            "private_endpoint_used": False,
            "exchange_auth_used": False,
            "websocket_live_used": False,
            "no_sidecars": True,
            "no_zip_fingerprints": True,
            "no_data_deletion": True,
            "no_destructive_cleanup": True,
            "network_used": False,
            "no_new_data_download": True,
            "no_ingestion_executed": True,
        },
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "collection_executed": False,
    }


def test_validator_accepts_measurement_discrepancy_report_v9_27(tmp_path) -> None:
    errors = validate_report_payload_v9_27(valid_report_v9_27(), tmp_path)

    assert errors == []


def test_validator_rejects_measurement_discrepancy_without_flag_v9_27() -> None:
    report = valid_report_v9_27()
    report["disk_preflight"]["measurement_discrepancy_detected"] = False

    errors = validate_disk_preflight_v9_27(report["disk_preflight"], report)

    assert any("measurement discrepancy" in error for error in errors)


def test_validator_rejects_collection_flags_when_no_collection_v9_27() -> None:
    report = valid_report_v9_27()
    flags = copy.deepcopy(report["safety_flags"])
    flags["network_used"] = True

    errors = validate_safety_v9_27(flags, report)

    assert any("no-collection flags" in error for error in errors)


def test_validator_rejects_trading_flag_v9_27(tmp_path) -> None:
    report = valid_report_v9_27()
    report["safety_flags"]["no_trading"] = False

    errors = validate_report_payload_v9_27(report, tmp_path)

    assert any("no_trading" in error for error in errors)
