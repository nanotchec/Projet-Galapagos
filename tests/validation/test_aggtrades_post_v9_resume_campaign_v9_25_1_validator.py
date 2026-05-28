from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1 import FINDINGS_V9_25_1, SAFETY_BASE_V9_25_1, VERSION
from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1_validation import (
    validate_disk_preflight_v9_25_1,
    validate_markdown_v9_25_1,
    validate_report_payload_v9_25_1,
    validate_safety_v9_25_1,
)


def _summary() -> dict:
    return {
        "campaign_start": "2025-02-03",
        "campaign_end": "2026-05-05",
        "target_window_start": "2024-05-05",
        "target_window_end": "2026-05-05",
        "batches_planned": 1,
        "batches_executed": 1,
        "batches_complete": 1,
        "batches_failed": 0,
        "failed_batch_ids": [],
        "days_requested_total": 1,
        "days_attempted_total": 1,
        "days_downloaded_total": 1,
        "days_normalized_total": 1,
        "days_complete_total": 1,
        "days_failed_total": 0,
        "days_quarantined_total": 0,
        "days_skipped_existing_total": 0,
        "total_rows_new": 10,
        "total_rows_cumulative": 20,
        "raw_bytes_new": 30,
        "silver_bytes_new": 40,
        "raw_bytes_cumulative": 50,
        "silver_bytes_cumulative": 60,
        "runtime_seconds_total": 1.0,
        "aggregate_trade_id_gap_warnings": [],
        "timestamp_gap_warnings": [],
        "local_file_coverage_start": "2024-05-05",
        "local_file_coverage_end": "2026-05-05",
        "reported_cumulative_coverage_start": "2024-05-05",
        "reported_cumulative_coverage_end": "2026-05-05",
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "quality_status": "PASS",
        "coverage_status": "target_window_complete",
        "restartability_status": "resume",
        "storage_warning": None,
        "stop_reason": None,
    }


def _report() -> dict:
    flags = dict(SAFETY_BASE_V9_25_1)
    flags.update(
        {
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
            "no_new_data_download": False,
            "no_ingestion_executed": False,
            "network_scope": "public_archive_read_only",
            "new_data_download_scope": "public_historical_aggtrades_resume_only",
            "ingestion_scope": "public_aggtrades_bronze_silver_resume_only",
        }
    )
    summary = _summary()
    return {
        "version": VERSION,
        "source_version": "V9.25",
        "correction_scope": "campaign_state_reconciliation_and_resume_collection",
        "status": "PASS",
        "decision": "resume_collection_completed_full_window",
        "campaign_summary": summary,
        "resume_summary": summary,
        **summary,
        "canonical_coverage_before_resume": {
            "target_window_start": "2024-05-05",
            "target_window_end": "2026-05-05",
            "first_missing_day": "2025-02-03",
            "last_complete_day_before_gap": "2025-02-02",
            "days_complete": 274,
            "days_partial": 0,
        },
        "disk_preflight": {
            "minimum_free_bytes_required": 60 * 1024**3,
            "free_bytes_current": 200 * 1024**3,
            "batch_size_days": 90,
        },
        "batch_report_paths": [],
        "collection_executed": True,
        "network_used": True,
        "new_data_downloaded": True,
        "ingestion_executed": True,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS_V9_25_1),
        "safety_flags": flags,
    }


def test_validator_accepts_valid_resume_report_v9_25_1() -> None:
    assert validate_report_payload_v9_25_1(_report()) == []


def test_validator_rejects_ml_execution_v9_25_1() -> None:
    report = _report()
    report["ml_executed"] = True

    errors = validate_report_payload_v9_25_1(report)

    assert "V9.25.1 must keep ml_executed=false" in errors


def test_validator_rejects_bad_disk_batch_size_v9_25_1() -> None:
    errors = validate_disk_preflight_v9_25_1({"minimum_free_bytes_required": 60 * 1024**3, "free_bytes_current": 1, "batch_size_days": 45})

    assert "V9.25.1 batch size must follow disk policy" in errors


def test_validator_rejects_wrong_download_scope_v9_25_1() -> None:
    report = _report()
    report["safety_flags"]["new_data_download_scope"] = "private_api"

    errors = validate_safety_v9_25_1(report["safety_flags"], report)

    assert "V9.25.1 download scope mismatch" in errors


def test_validator_rejects_markdown_forbidden_metric_v9_25_1() -> None:
    text = "aucun trading aucun paper live aucun ordre aucun backtest aucun walk-forward aucun ml aucun dataset supervise aucune suppression de donnees aucun nettoyage destructif aucun sidecar aucune empreinte zip Sharpe"

    errors = validate_markdown_v9_25_1(text)

    assert any("forbidden metric term" in error for error in errors)


def test_validator_rejects_sidecar_field_v9_25_1() -> None:
    report = deepcopy(_report())
    report["sidecar_json"] = "forbidden"

    errors = validate_report_payload_v9_25_1(report)

    assert "V9.25.1 report must not contain ZIP fingerprint or sidecar field" in errors


def test_v9_25_1_validator_tests_do_not_use_placeholder_bodies() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]

    assert pass_nodes == []
