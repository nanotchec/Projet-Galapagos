from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24 import (
    build_aggregate_trade_id_gap_warnings_v9_24,
    build_batch_day_plan_v9_24,
    download_public_archive_v9_24,
    quarantine_failed_raw_v9_24,
    validate_batch_day_v9_24,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    BRONZE_PARTITION_TEMPLATE,
    FINDINGS,
    PUBLIC_ARCHIVE_HOST,
    QUALITY_CHECKS,
    QUARANTINE_DIR,
    RAW_DIR,
    SILVER_COLUMNS_V9_18,
    SILVER_PARTITION_TEMPLATE,
    build_public_archive_url_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import normalize_raw_zip_to_silver_v9_25


VERSION = "V9.31"
SOURCE_VERSION = "V9.30"
LAST_VALIDATED_VERSION = "V9.30"
DIRECTION = "aggtrades_5y_historical_extension_collection"

TARGET_5Y_WINDOW_START = "2021-05-05"
TARGET_5Y_WINDOW_END = "2026-05-05"
EXTENSION_WINDOW_START = "2021-05-05"
EXTENSION_WINDOW_END = "2024-05-04"
ALREADY_VALIDATED_WINDOW_START = "2024-05-05"
ALREADY_VALIDATED_WINDOW_END = "2026-05-05"
MIN_START_FREE_GIB = 80.0
LOW_SPACE_BATCH_GIB = 120.0
STOP_FREE_GIB = 60.0

REPORT_JSON_PATH = Path("reports/data/aggtrades_5y_extension_collection_v9_31.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_5y_extension_collection_v9_31.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_5y_extension_collection_v9_31_manifest.json")
DOC_PATH = Path("docs/aggtrades_5y_extension_collection_v9_31.md")

INPUT_PATHS = {
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "v9_30_manifest": Path("reports/manifests/aggtrades_5y_extension_plan_v9_30_manifest.json"),
    "v9_29_validation": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "v9_28_repair": Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "aggtrades_5y_extension_collection_complete",
    "aggtrades_5y_extension_collection_partial",
    "aggtrades_5y_extension_collection_failed_source_issue",
    "aggtrades_5y_extension_collection_failed_quality",
    "aggtrades_5y_extension_collection_failed_storage",
    "aggtrades_5y_extension_collection_not_executed",
    "stop_aggtrades_5y_extension_branch",
}

BASE_SAFETY_FLAGS = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_destructive_cleanup": True,
    "network_used": False,
    "new_data_downloaded": False,
    "ingestion_executed": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
}


@dataclass(frozen=True)
class FiveYearExtensionBatchSpec:
    batch_id: str
    start_date: str
    end_date: str
    max_downloads: int

    @property
    def report_path(self) -> Path:
        suffix = self.batch_id.rsplit("_", 1)[-1]
        return Path(f"reports/data/aggtrades_5y_extension_batch{suffix}_v9_31.json")


INTERNAL_BATCHES_60 = [
    FiveYearExtensionBatchSpec("V9.31_batch_01", "2021-05-05", "2021-07-03", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_02", "2021-07-04", "2021-09-01", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_03", "2021-09-02", "2021-10-31", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_04", "2021-11-01", "2021-12-30", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_05", "2021-12-31", "2022-02-28", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_06", "2022-03-01", "2022-04-29", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_07", "2022-04-30", "2022-06-28", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_08", "2022-06-29", "2022-08-27", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_09", "2022-08-28", "2022-10-26", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_10", "2022-10-27", "2022-12-25", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_11", "2022-12-26", "2023-02-23", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_12", "2023-02-24", "2023-04-24", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_13", "2023-04-25", "2023-06-23", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_14", "2023-06-24", "2023-08-22", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_15", "2023-08-23", "2023-10-21", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_16", "2023-10-22", "2023-12-20", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_17", "2023-12-21", "2024-02-18", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_18", "2024-02-19", "2024-04-18", 60),
    FiveYearExtensionBatchSpec("V9.31_batch_19", "2024-04-19", "2024-05-04", 16),
]


def run_aggtrades_5y_extension_collection_v9_31(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_5y_extension_collection_v9_31(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_31(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_31(report))
    update_state_surfaces_v9_31(root, report)
    return report


def build_aggtrades_5y_extension_collection_v9_31(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    preflight = build_preflight_v9_31(root, inputs)
    batches = build_batches_for_preflight_v9_31(preflight)
    batch_reports: list[dict[str, Any]] = []
    stop_reason: dict[str, Any] | None = None
    if not preflight["safe_to_start_collection"]:
        stop_reason = {"type": "storage", "message": "free disk below V9.31 start threshold"}
        for batch in batches:
            report = build_not_executed_batch_report_v9_31(batch, stop_reason)
            _write_json(root / batch.report_path, report)
    else:
        for batch in batches:
            before_batch = build_disk_measurement_v9_31(root)
            if before_batch["free_gib_data_mount"] < STOP_FREE_GIB:
                stop_reason = {"type": "storage", "batch_id": batch.batch_id, "message": "free disk below stop threshold before batch"}
                report = build_not_executed_batch_report_v9_31(batch, stop_reason)
                _write_json(root / batch.report_path, report)
                batch_reports.append(report)
                break
            report = execute_extension_batch_v9_31(root, batch, before_batch)
            _write_json(root / batch.report_path, report)
            batch_reports.append(report)
            if report["batch_summary"]["batch_success"] is not True:
                stop_reason = {
                    "type": report["batch_summary"].get("failure_type") or "batch_failure",
                    "batch_id": batch.batch_id,
                    "message": "campaign stopped after first non-complete V9.31 batch",
                }
                break
        if stop_reason is not None and len(batch_reports) < len(batches):
            for batch in batches[len(batch_reports) :]:
                _write_json(root / batch.report_path, build_not_executed_batch_report_v9_31(batch, stop_reason))
    runtime = round(time.monotonic() - started, 3)
    summary = build_campaign_summary_v9_31(root, batches, batch_reports, runtime, stop_reason)
    decision = decide_v9_31(summary, preflight, stop_reason)
    safety = safety_flags_v9_31(summary)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] == "aggtrades_5y_extension_collection_complete" else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "extension_window_start": EXTENSION_WINDOW_START,
        "extension_window_end": EXTENSION_WINDOW_END,
        "already_validated_window_start": ALREADY_VALIDATED_WINDOW_START,
        "already_validated_window_end": ALREADY_VALIDATED_WINDOW_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "preflight": preflight,
        "batches_planned_detail": [batch_to_dict_v9_31(batch) for batch in batches],
        "batch_report_paths": [batch.report_path.as_posix() for batch in batches],
        "campaign_summary": summary,
        **summary,
        "decision": decision["decision"],
        "v9_31_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": summary["days_attempted"] > 0,
        "new_data_downloaded": summary["days_downloaded"] > 0,
        "ingestion_executed": summary["days_normalized"] > 0,
        "source_public_target": build_source_design_v9_31(),
        "storage_convention": {
            "raw_pattern": BRONZE_PARTITION_TEMPLATE,
            "silver_pattern": SILVER_PARTITION_TEMPLATE,
            "raw_dir": RAW_DIR.as_posix(),
            "quarantine_dir": QUARANTINE_DIR.as_posix(),
        },
        "quality_checks": list(QUALITY_CHECKS),
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "blockers": decision["blockers"],
        "warnings": build_warnings_v9_31(preflight, summary),
        "limitations": [
            "V9.31 reste data-only et ne cree aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal.",
            "La validation globale 5Y definitive est reservee a V9.32.",
            "Les fichiers raw/silver complets restent locaux et sont exclus du ZIP audit-lite.",
        ],
        "findings": dict(FINDINGS),
        "safety_flags": safety,
    }
    return report


def build_preflight_v9_31(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    disk = build_disk_measurement_v9_31(root)
    plan = inputs["v9_30_plan"].get("payload", {})
    extension_total = int(plan.get("estimated_extension_total_bytes") or 0)
    required_gib = float(plan.get("required_free_gib_for_extension") or 0.0)
    free_gib = min(float(disk["free_gib_data_mount"]), float(disk["free_gib_project_mount"]))
    if free_gib < MIN_START_FREE_GIB:
        batch_days = 0
    elif free_gib <= LOW_SPACE_BATCH_GIB:
        batch_days = 30
    else:
        batch_days = 60
    return {
        **disk,
        "estimated_extension_total_bytes": extension_total,
        "required_free_gib_for_extension": required_gib,
        "safe_to_start_collection": free_gib >= MIN_START_FREE_GIB,
        "max_batch_days_allowed": batch_days,
        "validated_window_will_not_be_recollected": True,
        "extension_window_confirmed": True,
        "collection_window_start": EXTENSION_WINDOW_START,
        "collection_window_end": EXTENSION_WINDOW_END,
        "already_validated_window_start": ALREADY_VALIDATED_WINDOW_START,
        "already_validated_window_end": ALREADY_VALIDATED_WINDOW_END,
    }


def build_disk_measurement_v9_31(root: Path) -> dict[str, Any]:
    data_path = root / "data"
    project_stat = statvfs_free_v9_31(root)
    data_stat = statvfs_free_v9_31(data_path if data_path.exists() else root)
    return {
        "project_path": root.as_posix(),
        "data_path": data_path.as_posix(),
        "df_h_project_output": run_local_command_v9_31(["df", "-h", root.as_posix()]),
        "df_h_data_output": run_local_command_v9_31(["df", "-h", data_path.as_posix()]),
        "df_g_data_output": run_local_command_v9_31(["df", "-g", data_path.as_posix()]),
        "statvfs_project": project_stat,
        "statvfs_data": data_stat,
        "free_gib_project_mount": project_stat["free_gib"],
        "free_gib_data_mount": data_stat["free_gib"],
    }


def build_batches_for_preflight_v9_31(preflight: dict[str, Any]) -> list[FiveYearExtensionBatchSpec]:
    if int(preflight.get("max_batch_days_allowed") or 60) >= 60:
        return INTERNAL_BATCHES_60
    return build_dynamic_batches_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END, 30)


def build_dynamic_batches_v9_31(start: str, end: str, batch_size: int) -> list[FiveYearExtensionBatchSpec]:
    dates = date_range_v9_31(start, end)
    batches: list[FiveYearExtensionBatchSpec] = []
    for index, offset in enumerate(range(0, len(dates), batch_size), start=1):
        chunk = dates[offset : offset + batch_size]
        batches.append(FiveYearExtensionBatchSpec(f"V9.31_batch_{index:02d}", chunk[0], chunk[-1], len(chunk)))
    return batches


def execute_extension_batch_v9_31(root: Path, batch: FiveYearExtensionBatchSpec, disk_before_batch: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    requested_dates = date_range_v9_31(batch.start_date, batch.end_date)
    validate_batch_spec_v9_31(batch, requested_dates)
    day_plan_before = build_batch_day_plan_v9_24(root, requested_dates)
    collection_result = collect_extension_batch_v9_31(root, batch, requested_dates)
    day_plan_after = build_batch_day_plan_v9_24(root, requested_dates)
    day_validation = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    runtime = round(time.monotonic() - started, 3)
    summary = summarize_batch_v9_31(batch, requested_dates, day_plan_before, day_plan_after, collection_result, day_validation, runtime)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if summary["batch_success"] else "FAIL",
        "batch_id": batch.batch_id,
        "report_path": batch.report_path.as_posix(),
        "created_at_utc": _utc_now(),
        "batch_window": batch_to_dict_v9_31(batch) | {"days_requested": len(requested_dates), "requested_dates": requested_dates},
        "disk_before_batch": disk_before_batch,
        "day_plan_before": day_plan_before,
        "day_plan_after": day_plan_after,
        "collection_result": collection_result,
        "day_results": day_validation,
        "batch_summary": summary,
        "safety_flags": safety_flags_for_batch_v9_31(collection_result),
    }


def collect_extension_batch_v9_31(root: Path, batch: FiveYearExtensionBatchSpec, requested_dates: list[str]) -> dict[str, Any]:
    validate_batch_spec_v9_31(batch, requested_dates)
    attempted: list[str] = []
    downloaded: list[str] = []
    normalized: list[str] = []
    skipped: list[str] = []
    quarantined: list[str] = []
    errors: list[str] = []
    failure_type: str | None = None
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            skipped.append(day_value)
            continue
        if len(attempted) >= batch.max_downloads:
            break
        free_gib = statvfs_free_v9_31(root)["free_gib"]
        if free_gib < STOP_FREE_GIB:
            failure_type = "storage"
            errors.append(f"{day_value}: storage guard stopped before download; free_gib={free_gib}; stop_free_gib={STOP_FREE_GIB}")
            break
        attempted.append(day_value)
        try:
            before_ok = raw_path.exists() and raw_path.stat().st_size > 0
            download_public_archive_v9_24(build_public_archive_url_v9_18(day_value), raw_path)
            after_ok = raw_path.exists() and raw_path.stat().st_size > 0
            if after_ok and not before_ok:
                downloaded.append(day_value)
            normalize_raw_zip_to_silver_v9_25(raw_path, silver_path, day_value)
            normalized.append(day_value)
        except Exception as exc:  # noqa: BLE001
            failure_type = "source_or_quality" if failure_type is None else failure_type
            quarantine_path = quarantine_failed_raw_v9_24(root, day_value, raw_path)
            if quarantine_path is not None:
                quarantined.append(day_value)
            suffix = f"; quarantined={quarantine_path.as_posix()}" if quarantine_path else ""
            errors.append(f"{day_value}: {exc}{suffix}")
            break
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": bool(attempted or skipped),
        "network_used": bool(attempted),
        "network_scope": "public_archive_read_only",
        "new_data_downloaded": bool(downloaded),
        "new_data_download_scope": "public_historical_aggtrades_5y_extension_only",
        "ingestion_executed": bool(normalized),
        "ingestion_scope": "public_aggtrades_bronze_silver_5y_extension_only",
        "days_attempted": len(attempted),
        "days_downloaded": len(downloaded),
        "days_normalized": len(normalized),
        "days_skipped_existing": len(skipped),
        "days_quarantined": len(quarantined),
        "downloaded_dates": downloaded,
        "normalized_dates": normalized,
        "skipped_existing_dates": skipped,
        "quarantined_dates": quarantined,
        "errors": errors,
        "failure_type": failure_type,
    }


def summarize_batch_v9_31(
    batch: FiveYearExtensionBatchSpec,
    requested_dates: list[str],
    day_plan_before: list[dict[str, Any]],
    day_plan_after: list[dict[str, Any]],
    collection_result: dict[str, Any],
    day_validation: list[dict[str, Any]],
    runtime: float,
) -> dict[str, Any]:
    complete = [item for item in day_validation if item["status"] == "day_complete"]
    failed = [item for item in day_validation if item["status"] != "day_complete"]
    already_complete_before = {item["date"] for item in day_plan_before if item["status"] == "day_complete"}
    # V9.31 reports the extension footprint relative to V9.30. If a previous
    # interrupted V9.31 attempt already materialized a day, the resumable run
    # skips it but it still belongs to the V9.31 extension campaign.
    new_complete = list(complete)
    invalid = sum_int_v9_31(day_validation, "invalid_rows")
    duplicates = sum_int_v9_31(day_validation, "duplicates")
    gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete)
    batch_success = collection_result["status"] == "PASS" and len(complete) == len(requested_dates) and not failed and invalid == 0 and duplicates == 0
    return {
        "batch_id": batch.batch_id,
        "batch_start": batch.start_date,
        "batch_end": batch.end_date,
        "max_downloads": batch.max_downloads,
        "days_requested": len(requested_dates),
        "days_attempted": int(collection_result.get("days_attempted") or 0),
        "days_downloaded": int(collection_result.get("days_downloaded") or 0),
        "days_normalized": int(collection_result.get("days_normalized") or 0),
        "days_complete": len(complete),
        "days_missing": len([item for item in day_validation if item["status"] == "day_missing"]),
        "days_failed": len(failed),
        "days_quarantined": int(collection_result.get("days_quarantined") or 0),
        "days_skipped_existing": int(collection_result.get("days_skipped_existing") or 0),
        "days_already_complete_before": len(already_complete_before),
        "complete_dates": [item["date"] for item in complete],
        "failed_dates": [item["date"] for item in failed],
        "new_complete_dates": [item["date"] for item in new_complete],
        "total_rows": sum_int_v9_31(day_validation, "rows"),
        "total_rows_new": sum_int_v9_31(new_complete, "rows"),
        "invalid_rows": invalid,
        "duplicates": duplicates,
        "raw_bytes_total": sum_int_v9_31(day_validation, "raw_bytes"),
        "silver_bytes_total": sum_int_v9_31(day_validation, "silver_bytes"),
        "raw_bytes_new": sum_int_v9_31(new_complete, "raw_bytes"),
        "silver_bytes_new": sum_int_v9_31(new_complete, "silver_bytes"),
        "aggregate_trade_id_gap_warnings": gap_warnings,
        "runtime_seconds": runtime,
        "quality_status": "PASS" if batch_success else "FAIL",
        "coverage_status": "batch_complete" if len(complete) == len(requested_dates) else "batch_incomplete",
        "batch_success": batch_success,
        "failure_type": collection_result.get("failure_type"),
        "errors": list(collection_result.get("errors") or []),
        "quality_errors": [error for item in failed for error in item.get("errors", [])],
        "day_plan_after_status_counts": count_statuses_v9_31(day_plan_after),
    }


def build_campaign_summary_v9_31(root: Path, batches: list[FiveYearExtensionBatchSpec], reports: list[dict[str, Any]], runtime: float, stop_reason: dict[str, Any] | None) -> dict[str, Any]:
    summaries = [report["batch_summary"] for report in reports]
    complete_batches = [summary for summary in summaries if summary["batch_success"] is True]
    all_days = [day for report in reports for day in report.get("day_results", []) if day.get("status") == "day_complete"]
    extension_dates = set(date_range_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END))
    local = build_local_file_coverage_v9_31(root, TARGET_5Y_WINDOW_START, TARGET_5Y_WINDOW_END)
    complete_extension = len({day["date"] for day in all_days if day["date"] in extension_dates}) == len(extension_dates)
    target_reached = complete_extension and local["local_file_coverage_start"] == TARGET_5Y_WINDOW_START and local["local_file_coverage_end"] == TARGET_5Y_WINDOW_END
    source_issues = [error for summary in summaries for error in summary.get("errors", []) if "HTTP" in error or "url" in error.casefold() or "download" in error.casefold()]
    storage_warnings = [summary.get("errors", []) for summary in summaries if summary.get("failure_type") == "storage"]
    quality_errors = [error for summary in summaries for error in summary.get("quality_errors", [])]
    return {
        "batches_planned": len(batches),
        "batches_executed": len(reports),
        "batches_complete": len(complete_batches),
        "batches_failed": len([summary for summary in summaries if summary["batch_success"] is not True]),
        "days_expected_extension": len(extension_dates),
        "days_attempted": sum_int_v9_31(summaries, "days_attempted"),
        "days_downloaded": sum_int_v9_31(summaries, "days_downloaded"),
        "days_normalized": sum_int_v9_31(summaries, "days_normalized"),
        "days_complete": sum_int_v9_31(summaries, "days_complete"),
        "days_missing": sum_int_v9_31(summaries, "days_missing"),
        "days_failed": sum_int_v9_31(summaries, "days_failed"),
        "days_quarantined": sum_int_v9_31(summaries, "days_quarantined"),
        "days_skipped_existing": sum_int_v9_31(summaries, "days_skipped_existing"),
        "total_rows_new": sum_int_v9_31(summaries, "total_rows_new"),
        "raw_bytes_new": sum_int_v9_31(summaries, "raw_bytes_new"),
        "silver_bytes_new": sum_int_v9_31(summaries, "silver_bytes_new"),
        "local_file_coverage_start": local["local_file_coverage_start"],
        "local_file_coverage_end": local["local_file_coverage_end"],
        "complete_extension_reached": complete_extension,
        "target_5y_collection_reached": target_reached,
        "quality_status": "PASS" if complete_extension and not quality_errors else "FAIL",
        "coverage_status": "extension_complete" if complete_extension else "extension_incomplete",
        "source_availability_issues": source_issues,
        "storage_warnings": storage_warnings,
        "runtime_seconds_total": runtime,
        "stop_reason": stop_reason,
    }


def build_local_file_coverage_v9_31(root: Path, start: str, end: str) -> dict[str, Any]:
    complete: list[str] = []
    for day_value in date_range_v9_31(start, end):
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            complete.append(day_value)
        else:
            break
    return {"local_file_coverage_start": complete[0] if complete else None, "local_file_coverage_end": complete[-1] if complete else None, "days_contiguous": len(complete)}


def decide_v9_31(summary: dict[str, Any], preflight: dict[str, Any], stop_reason: dict[str, Any] | None) -> dict[str, Any]:
    if not preflight["safe_to_start_collection"]:
        decision = "aggtrades_5y_extension_collection_not_executed"
        recommendation = "V9.32 - Storage Review / Compression Plan"
        blockers = ["storage preflight failed"]
    elif summary["complete_extension_reached"] and summary["target_5y_collection_reached"] and summary["quality_status"] == "PASS":
        decision = "aggtrades_5y_extension_collection_complete"
        recommendation = "V9.32 - AggTrades 5Y Full Coverage Validation"
        blockers = []
    elif stop_reason and stop_reason.get("type") == "storage":
        decision = "aggtrades_5y_extension_collection_failed_storage"
        recommendation = "V9.32 - Storage Review / Compression Plan"
        blockers = ["storage stopped campaign"]
    elif summary["source_availability_issues"]:
        decision = "aggtrades_5y_extension_collection_failed_source_issue"
        recommendation = "V9.32 - Historical Source Gap Review"
        blockers = ["source issue during collection"]
    elif summary["quality_status"] != "PASS":
        decision = "aggtrades_5y_extension_collection_failed_quality"
        recommendation = "V9.32 - AggTrades 5Y Extension Correction"
        blockers = ["quality failed during collection"]
    else:
        decision = "aggtrades_5y_extension_collection_partial"
        recommendation = "V9.32 - AggTrades 5Y Extension Correction"
        blockers = ["extension incomplete"]
    return {"decision": decision, "next_recommendation": recommendation, "blockers": blockers, "no_backtest": True, "no_trading": True, "no_signal": True}


def build_not_executed_batch_report_v9_31(batch: FiveYearExtensionBatchSpec, stop_reason: dict[str, Any]) -> dict[str, Any]:
    requested_dates = date_range_v9_31(batch.start_date, batch.end_date)
    summary = {
        "batch_id": batch.batch_id,
        "batch_start": batch.start_date,
        "batch_end": batch.end_date,
        "max_downloads": batch.max_downloads,
        "days_requested": len(requested_dates),
        "days_attempted": 0,
        "days_downloaded": 0,
        "days_normalized": 0,
        "days_complete": 0,
        "days_missing": 0,
        "days_failed": 0,
        "days_quarantined": 0,
        "days_skipped_existing": 0,
        "total_rows_new": 0,
        "raw_bytes_new": 0,
        "silver_bytes_new": 0,
        "batch_success": False,
        "failure_type": stop_reason.get("type"),
        "errors": [f"not executed after campaign stop: {stop_reason}"],
        "quality_errors": [],
    }
    return {"version": VERSION, "source_version": SOURCE_VERSION, "status": "NOT_EXECUTED", "batch_id": batch.batch_id, "batch_summary": summary, "day_results": [], "collection_result": {"status": "NOT_EXECUTED", "network_used": False}, "safety_flags": safety_flags_for_batch_v9_31({"days_attempted": 0, "days_downloaded": 0, "days_normalized": 0})}


def validate_batch_spec_v9_31(batch: FiveYearExtensionBatchSpec, requested_dates: list[str]) -> None:
    if len(requested_dates) > batch.max_downloads:
        raise ValueError("V9.31 batch cannot request more days than max_downloads")
    if date.fromisoformat(batch.start_date) < date.fromisoformat(EXTENSION_WINDOW_START) or date.fromisoformat(batch.end_date) > date.fromisoformat(EXTENSION_WINDOW_END):
        raise ValueError("V9.31 batch must stay inside extension window")


def safety_flags_for_batch_v9_31(result: dict[str, Any]) -> dict[str, Any]:
    flags = dict(BASE_SAFETY_FLAGS)
    if int(result.get("days_attempted") or 0) > 0:
        flags.update(
            {
                "network_used": True,
                "network_scope": "public_archive_read_only",
                "new_data_downloaded": int(result.get("days_downloaded") or 0) > 0,
                "new_data_download_scope": "public_historical_aggtrades_5y_extension_only",
                "ingestion_executed": int(result.get("days_normalized") or 0) > 0,
                "ingestion_scope": "public_aggtrades_bronze_silver_5y_extension_only",
                "no_new_data_download": False,
                "no_ingestion_executed": False,
            }
        )
    return flags


def safety_flags_v9_31(summary: dict[str, Any]) -> dict[str, Any]:
    return safety_flags_for_batch_v9_31({"days_attempted": summary["days_attempted"], "days_downloaded": summary["days_downloaded"], "days_normalized": summary["days_normalized"]})


def build_manifest_v9_31(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "days_expected_extension": report["days_expected_extension"],
        "days_complete": report["days_complete"],
        "days_failed": report["days_failed"],
        "complete_extension_reached": report["complete_extension_reached"],
        "target_5y_collection_reached": report["target_5y_collection_reached"],
        "safety_flags": report["safety_flags"],
        "findings": report["findings"],
    }


def build_markdown_v9_31(report: dict[str, Any]) -> str:
    return (
        "# V9.31 - AggTrades 5Y Historical Extension Collection\n\n"
        f"- Decision V9.31 : `{report['decision']}`.\n"
        f"- Recommandation suivante : `{report['next_recommendation']}`.\n"
        f"- Fenetre collectee : `{EXTENSION_WINDOW_START}` -> `{EXTENSION_WINDOW_END}`.\n"
        f"- Batches planifies/executés/complets/failed : `{report['batches_planned']}` / `{report['batches_executed']}` / `{report['batches_complete']}` / `{report['batches_failed']}`.\n"
        f"- Jours telecharges/normalises/complets : `{report['days_downloaded']}` / `{report['days_normalized']}` / `{report['days_complete']}`.\n"
        f"- Jours manquants/failed/quarantine/skipped : `{report['days_missing']}` / `{report['days_failed']}` / `{report['days_quarantined']}` / `{report['days_skipped_existing']}`.\n"
        f"- Rows nouvelles : `{report['total_rows_new']}`.\n"
        f"- Raw/Silver bytes nouveaux : `{report['raw_bytes_new']}` / `{report['silver_bytes_new']}`.\n"
        f"- Couverture locale : `{report['local_file_coverage_start']}` -> `{report['local_file_coverage_end']}`.\n"
        f"- Extension complete : `{report['complete_extension_reached']}`.\n"
        f"- Cible 5Y collectee : `{report['target_5y_collection_reached']}`.\n\n"
        "## Garde-fous\n"
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.\n"
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression destructive, aucun push.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )


def update_state_surfaces_v9_31(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_31_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "extension_window_start": EXTENSION_WINDOW_START,
        "extension_window_end": EXTENSION_WINDOW_END,
        "days_expected_extension": report["days_expected_extension"],
        "days_downloaded": report["days_downloaded"],
        "days_normalized": report["days_normalized"],
        "days_complete": report["days_complete"],
        "days_failed": report["days_failed"],
        "days_quarantined": report["days_quarantined"],
        "total_rows_new": report["total_rows_new"],
        "raw_bytes_new": report["raw_bytes_new"],
        "silver_bytes_new": report["silver_bytes_new"],
        "complete_extension_reached": report["complete_extension_reached"],
        "target_5y_collection_reached": report["target_5y_collection_reached"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.31\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Decision V9.31 : `{report['decision']}`.\n"
        f"- Fenetre extension : `{EXTENSION_WINDOW_START}` -> `{EXTENSION_WINDOW_END}`.\n"
        f"- Jours complets/failed/quarantine : `{report['days_complete']}` / `{report['days_failed']}` / `{report['days_quarantined']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie ou signal actionnable.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, collecte extension aggTrades 5Y.\n"
        f"- Extension : {EXTENSION_WINDOW_START} -> {EXTENSION_WINDOW_END}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def build_source_design_v9_31() -> dict[str, Any]:
    return {"source_name": "Binance public archive", "host": PUBLIC_ARCHIVE_HOST, "market_type": "spot", "symbol": "BTCUSDT", "read_only": True, "api_key_required": False, "account_required": False}


def build_warnings_v9_31(preflight: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if preflight["free_gib_data_mount"] <= LOW_SPACE_BATCH_GIB:
        warnings.append("V9.31 utilise des lots reduits a cause de l'espace disque.")
    if summary["storage_warnings"]:
        warnings.append("La campagne a rencontre un warning stockage.")
    return warnings


def batch_to_dict_v9_31(batch: FiveYearExtensionBatchSpec) -> dict[str, Any]:
    return {"batch_id": batch.batch_id, "start_date": batch.start_date, "end_date": batch.end_date, "max_downloads": batch.max_downloads}


def count_statuses_v9_31(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def date_range_v9_31(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def statvfs_free_v9_31(path: Path) -> dict[str, Any]:
    stat = os.statvfs(path)
    free = stat.f_bavail * stat.f_frsize
    return {"path": path.as_posix(), "free_bytes": free, "free_gib": round(free / 1024**3, 3)}


def run_local_command_v9_31(command: list[str]) -> dict[str, Any]:
    import subprocess

    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def sum_int_v9_31(items: list[dict[str, Any]], key: str) -> int:
    return sum(int(item.get(key) or 0) for item in items if item.get(key) is not None)


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    payload: Any = _read_json(full) if path.suffix == ".json" else {"text": full.read_text(encoding="utf-8")}
    return {"path": path.as_posix(), "available": True, "payload": payload}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
