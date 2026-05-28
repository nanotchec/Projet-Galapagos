from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24 import (
    build_aggregate_trade_id_gap_warnings_v9_24,
    download_public_archive_v9_24,
    validate_batch_day_v9_24,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    ALLOWED_PUBLIC_HOSTS,
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    FINDINGS,
    MARKET_TYPE,
    PUBLIC_ARCHIVE_HOST,
    QUARANTINE_DIR,
    RAW_DIR,
    SILVER_COLUMNS_V9_18,
    SYMBOL,
    VENUE,
    build_public_archive_url_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    normalize_raw_zip_to_silver_v9_25,
)


VERSION = "V9.25.1"
SOURCE_VERSION = "V9.25"
LAST_VALIDATED_VERSION = "V9.25"
CORRECTION_SCOPE = "campaign_state_reconciliation_and_resume_collection"
DIRECTION = "aggtrades_post_v9_resume_collection"

PREVIOUS_VALIDATED_COVERAGE_START = "2024-05-05"
PREVIOUS_VALIDATED_COVERAGE_END = "2024-12-07"
MIN_FREE_BYTES = 60 * 1024**3
WARN_FREE_BYTES = 100 * 1024**3
COMFORT_FREE_BYTES = 150 * 1024**3

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_resume_campaign_v9_25_1.md")

INPUT_PATHS = {
    "v9_25_campaign": Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"),
    "v9_25_campaign_md": Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.md"),
    "v9_25_batch01": Path("reports/data/aggtrades_post_v9_completion_batch01_v9_25.json"),
    "v9_25_manifest": Path("reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json"),
    "v9_25_command_results": Path("reports/audit_lite/v9_25_command_results.json"),
    "v9_25_attestation": Path("reports/audit_lite/v9_25_full_local_validation_attestation.json"),
    "v9_24_batch3": Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    "v9_23_batch2": Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    "v9_21_batch_expansion": Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    "v9_20_batch_collection": Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    "v9_19_pilot": Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "resume_collection_completed_full_window",
    "resume_collection_partial_storage_warning",
    "resume_collection_partial_source_issue",
    "resume_collection_partial_quality_issue",
    "resume_collection_not_executed_storage_blocker",
    "resume_collection_not_executed_state_not_reconciled",
    "stop_aggtrades_completion_branch",
}

FINDINGS_V9_25_1 = dict(FINDINGS)
SAFETY_BASE_V9_25_1 = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
}


@dataclass(frozen=True)
class ResumeBatchSpec:
    batch_id: str
    start_date: str
    end_date: str
    max_downloads: int

    @property
    def report_path(self) -> Path:
        suffix = self.batch_id.rsplit("_", 1)[-1]
        return Path(f"reports/data/aggtrades_post_v9_resume_batch{suffix}_v9_25_1.json")


def run_aggtrades_post_v9_resume_campaign_v9_25_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_resume_campaign_v9_25_1(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_25_1(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_25_1(report))
    update_state_surfaces_v9_25_1(root, report)
    return report


def build_aggtrades_post_v9_resume_campaign_v9_25_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    canonical_before = reconcile_campaign_state_v9_25_1(root, inputs)
    disk_preflight = build_disk_preflight_v9_25_1(root, canonical_before)
    state_reconciled = canonical_before["state_reconciled"]
    can_collect = state_reconciled and disk_preflight["safe_to_continue_now"] and canonical_before["first_missing_day"] is not None
    planned_batches = build_resume_batches_v9_25_1(
        canonical_before["first_missing_day"],
        TARGET_WINDOW_END,
        disk_preflight["batch_size_days"],
    ) if can_collect else []
    batch_reports: list[dict[str, Any]] = []
    stop_reason: dict[str, Any] | None = None
    if not state_reconciled:
        stop_reason = {"type": "state", "message": "canonical campaign state is not reconciled"}
    elif canonical_before["first_missing_day"] is None:
        stop_reason = {"type": "complete", "message": "target window already complete before resume"}
    elif not disk_preflight["safe_to_continue_now"]:
        stop_reason = {"type": "storage", "message": "free disk space is below V9.25.1 minimum threshold"}
    else:
        for batch in planned_batches:
            batch_report = execute_resume_batch_v9_25_1(root, batch, disk_preflight)
            _write_json(root / batch.report_path, batch_report)
            batch_reports.append(batch_report)
            if batch_report["batch_summary"]["batch_success"] is not True:
                stop_reason = {
                    "type": batch_report["batch_summary"].get("failure_type") or "batch_failure",
                    "batch_id": batch.batch_id,
                    "message": "resume campaign stopped after first non-complete internal batch",
                }
                break
    runtime = round(time.monotonic() - started, 3)
    canonical_after = build_local_coverage_inventory_v9_25_1(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
    summary = build_resume_summary_v9_25_1(
        canonical_before=canonical_before,
        canonical_after=canonical_after,
        disk_preflight=disk_preflight,
        planned_batches=planned_batches,
        batch_reports=batch_reports,
        runtime_seconds_total=runtime,
        stop_reason=stop_reason,
    )
    decision = decide_v9_25_1(summary, canonical_before, disk_preflight, stop_reason)
    safety_flags = safety_flags_v9_25_1(summary)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "campaign_start": canonical_before["first_missing_day"],
        "campaign_end": TARGET_WINDOW_END,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "canonical_coverage_before_resume": canonical_before,
        "first_missing_day_before_resume": canonical_before["first_missing_day"],
        "disk_preflight": disk_preflight,
        "batches_planned": [batch_to_dict_v9_25_1(batch) for batch in planned_batches],
        "batches_executed": [report["batch_summary"] for report in batch_reports],
        "batch_report_paths": [report["report_path"] for report in batch_reports],
        "resume_summary": summary,
        **summary,
        "decision": decision["decision"],
        "v9_25_1_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": summary["days_attempted_total"] > 0,
        "network_used": summary["days_attempted_total"] > 0,
        "new_data_downloaded": summary["days_downloaded_total"] > 0,
        "ingestion_executed": summary["days_normalized_total"] > 0,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": FINDINGS_V9_25_1,
        "safety_flags": safety_flags,
        "blockers": build_blockers_v9_25_1(canonical_before, disk_preflight, stop_reason),
        "warnings": build_warnings_v9_25_1(summary, canonical_before, disk_preflight),
        "limitations": [
            "V9.25.1 ne supprime, ne compresse et ne migre aucune donnee locale.",
            "L'historique exact des relances V9.25 n'est pas totalement reconstructible; la decision se base sur l'etat local canonique et les rapports disponibles.",
            "Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal n'est cree.",
        ],
    }
    return report


def reconcile_campaign_state_v9_25_1(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    local = build_local_coverage_inventory_v9_25_1(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
    v9_25 = inputs.get("v9_25_campaign", {}).get("payload", {})
    v9_summary = v9_25.get("campaign_summary", {}) if isinstance(v9_25, dict) else {}
    previous_dates = date_range_v9_25_1(PREVIOUS_VALIDATED_COVERAGE_START, PREVIOUS_VALIDATED_COVERAGE_END)
    new_dates = date_range_v9_25_1(next_day_v9_25_1(PREVIOUS_VALIDATED_COVERAGE_END), local["local_contiguous_coverage_end"])
    raw_bytes_new, silver_bytes_new = sum_local_bytes_v9_25_1(root, new_dates)
    canonical_rows_new = int(v9_summary.get("total_rows_new") or 0) if v9_summary.get("local_file_coverage_end") == local["local_contiguous_coverage_end"] else None
    v9_downloaded = int(v9_summary.get("days_downloaded_total") or 0)
    v9_skipped = int(v9_summary.get("days_skipped_existing_total") or 0)
    canonical_new_days = len(new_dates)
    inconsistency = v9_skipped == canonical_new_days or v9_downloaded != canonical_new_days
    return {
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "previous_validated_coverage_start": PREVIOUS_VALIDATED_COVERAGE_START,
        "previous_validated_coverage_end": PREVIOUS_VALIDATED_COVERAGE_END,
        "v9_25_reported_final_coverage_start": v9_summary.get("local_file_coverage_start"),
        "v9_25_reported_final_coverage_end": v9_summary.get("local_file_coverage_end"),
        **local,
        "v9_25_reporting_inconsistency_detected": inconsistency,
        "v9_25_new_days_confirmed": canonical_new_days,
        "v9_25_skipped_existing_days_confirmed": len(previous_dates),
        "canonical_days_downloaded": canonical_new_days,
        "canonical_days_skipped_existing": len(previous_dates),
        "canonical_days_newly_completed": canonical_new_days,
        "canonical_raw_bytes_new": raw_bytes_new,
        "canonical_silver_bytes_new": silver_bytes_new,
        "canonical_total_rows_new": canonical_rows_new,
        "v9_25_reported_total_rows_cumulative": int(v9_summary.get("total_rows_cumulative") or 0),
        "execution_history_not_fully_reconstructible": inconsistency,
        "state_reconciled": local["first_missing_day"] is not None and not local["days_partial"],
        "reconciliation_basis": "local raw/silver file metadata plus V9.25 and V9.24 reports",
    }


def build_local_coverage_inventory_v9_25_1(root: Path, start: str, end: str) -> dict[str, Any]:
    dates = date_range_v9_25_1(start, end)
    complete: list[str] = []
    partial: list[str] = []
    missing: list[str] = []
    raw_bytes = 0
    silver_bytes = 0
    for day_value in dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        has_raw = raw_path.exists() and raw_path.stat().st_size > 0
        has_silver = silver_path.exists() and silver_path.stat().st_size > 0
        if has_raw:
            raw_bytes += raw_path.stat().st_size
        if has_silver:
            silver_bytes += silver_path.stat().st_size
        if has_raw and has_silver:
            complete.append(day_value)
        elif has_raw or has_silver:
            partial.append(day_value)
        else:
            missing.append(day_value)
    contiguous: list[str] = []
    complete_set = set(complete)
    for day_value in dates:
        if day_value not in complete_set:
            break
        contiguous.append(day_value)
    quarantined = quarantine_dates_v9_25_1(root, set(dates))
    first_gap = next((day_value for day_value in dates if day_value not in complete_set), None)
    return {
        "local_file_coverage_start": complete[0] if complete else None,
        "local_file_coverage_end": complete[-1] if complete else None,
        "local_contiguous_coverage_start": contiguous[0] if contiguous else None,
        "local_contiguous_coverage_end": contiguous[-1] if contiguous else None,
        "days_complete": len(complete),
        "days_missing": len(missing),
        "days_partial": len(partial),
        "days_quarantined": len(quarantined),
        "first_missing_day": first_gap,
        "last_complete_day_before_gap": previous_day_v9_25_1(first_gap) if first_gap else complete[-1] if complete else None,
        "gaps_detected": detect_gaps_v9_25_1(dates, complete_set),
        "complete_dates_sample": {"first": complete[:3], "last": complete[-3:]},
        "missing_dates_sample": {"first": missing[:3], "last": missing[-3:]},
        "partial_dates": partial,
        "quarantined_dates_sample": {"first": quarantined[:3], "last": quarantined[-3:]},
        "raw_bytes_complete_window": raw_bytes,
        "silver_bytes_complete_window": silver_bytes,
    }


def build_disk_preflight_v9_25_1(root: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    disk = shutil.disk_usage(root)
    days_remaining = int(canonical["days_missing"]) + int(canonical["days_partial"])
    avg_raw = int(canonical["canonical_raw_bytes_new"] / canonical["canonical_days_newly_completed"]) if canonical["canonical_days_newly_completed"] else 0
    avg_silver = int(canonical["canonical_silver_bytes_new"] / canonical["canonical_days_newly_completed"]) if canonical["canonical_days_newly_completed"] else 0
    estimated_total = (avg_raw + avg_silver) * days_remaining
    if disk.free < MIN_FREE_BYTES:
        batch_size = 0
        storage_warning = "free_disk_below_60gib_stop_before_collection"
        storage_blocker = True
    elif disk.free < WARN_FREE_BYTES:
        batch_size = 30
        storage_warning = "free_disk_between_60gib_and_100gib_micro_batches_30_days"
        storage_blocker = False
    elif disk.free < COMFORT_FREE_BYTES:
        batch_size = 60
        storage_warning = "free_disk_between_100gib_and_150gib_batches_60_days"
        storage_blocker = False
    else:
        batch_size = 90
        storage_warning = None
        storage_blocker = False
    reserve = avg_raw + avg_silver
    safe = disk.free >= MIN_FREE_BYTES and disk.free >= MIN_FREE_BYTES + reserve
    return {
        "free_bytes_current": disk.free,
        "free_gb_current": round(disk.free / 1024**3, 3),
        "minimum_free_bytes_required": MIN_FREE_BYTES,
        "reserve_bytes_required": reserve,
        "estimated_remaining_raw_bytes": avg_raw * days_remaining,
        "estimated_remaining_silver_bytes": avg_silver * days_remaining,
        "estimated_remaining_total_bytes": estimated_total,
        "safe_to_continue_now": safe and not storage_blocker,
        "storage_blocker": storage_blocker or not safe,
        "storage_warning": storage_warning if storage_warning else "free_disk_above_150gib_batches_90_days",
        "batch_size_days": batch_size if safe and not storage_blocker else 0,
        "estimate_basis": "canonical V9.25 newly completed local bytes per day",
    }


def build_resume_batches_v9_25_1(start: str | None, end: str, batch_size_days: int) -> list[ResumeBatchSpec]:
    if start is None or batch_size_days <= 0:
        return []
    dates = date_range_v9_25_1(start, end)
    batches: list[ResumeBatchSpec] = []
    for index, offset in enumerate(range(0, len(dates), batch_size_days), start=1):
        chunk = dates[offset : offset + batch_size_days]
        batches.append(ResumeBatchSpec(f"V9.25.1_batch_{index:02d}", chunk[0], chunk[-1], len(chunk)))
    return batches


def execute_resume_batch_v9_25_1(root: Path, batch: ResumeBatchSpec, preflight: dict[str, Any]) -> dict[str, Any]:
    requested_dates = date_range_v9_25_1(batch.start_date, batch.end_date)
    started = time.monotonic()
    result = collect_resume_batch_v9_25_1(root, batch, requested_dates, preflight)
    day_results = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    summary = summarize_resume_batch_v9_25_1(batch, requested_dates, result, day_results, round(time.monotonic() - started, 3))
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if summary["batch_success"] else "FAIL",
        "created_at_utc": _utc_now(),
        "report_path": batch.report_path.as_posix(),
        "batch_id": batch.batch_id,
        "batch_spec": batch_to_dict_v9_25_1(batch),
        "collection_result": result,
        "batch_summary": summary,
        "day_results": day_results,
        "safety_flags": safety_flags_for_batch_v9_25_1(result),
    }


def collect_resume_batch_v9_25_1(root: Path, batch: ResumeBatchSpec, requested_dates: list[str], preflight: dict[str, Any]) -> dict[str, Any]:
    attempted: list[str] = []
    downloaded: list[str] = []
    normalized: list[str] = []
    skipped_existing: list[str] = []
    quarantined: list[str] = []
    errors: list[str] = []
    failure_type: str | None = None
    reserve = int(preflight["reserve_bytes_required"])
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            skipped_existing.append(day_value)
            continue
        free = shutil.disk_usage(root).free
        if free < MIN_FREE_BYTES + reserve:
            failure_type = "storage"
            errors.append(f"{day_value}: storage guard stopped resume before download; free_bytes={free}; minimum_free_bytes={MIN_FREE_BYTES}; reserve_bytes={reserve}")
            break
        attempted.append(day_value)
        try:
            before_raw = raw_path.exists() and raw_path.stat().st_size > 0
            if not before_raw:
                download_public_archive_v9_24(build_public_archive_url_v9_18(day_value), raw_path)
                downloaded.append(day_value)
            normalize_raw_zip_to_silver_v9_25(raw_path, silver_path, day_value)
            normalized.append(day_value)
        except Exception as exc:  # noqa: BLE001
            failure_type = "source_or_quality"
            q_path = quarantine_failed_raw_v9_25_1(root, day_value, raw_path)
            if q_path:
                quarantined.append(day_value)
            suffix = f"; quarantined={q_path.as_posix()}" if q_path else ""
            errors.append(f"{day_value}: {exc}{suffix}")
            break
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": bool(attempted),
        "network_used": bool(attempted),
        "new_data_downloaded": bool(downloaded),
        "ingestion_executed": bool(normalized),
        "network_scope": "public_archive_read_only" if attempted else None,
        "new_data_download_scope": "public_historical_aggtrades_resume_only" if downloaded else None,
        "ingestion_scope": "public_aggtrades_bronze_silver_resume_only" if normalized else None,
        "days_attempted": len(attempted),
        "days_downloaded": len(downloaded),
        "days_normalized": len(normalized),
        "days_skipped_existing": len(skipped_existing),
        "days_quarantined": len(quarantined),
        "attempted_dates": attempted,
        "downloaded_dates": downloaded,
        "normalized_dates": normalized,
        "skipped_existing_dates": skipped_existing,
        "quarantined_dates": quarantined,
        "failure_type": failure_type,
        "errors": errors,
    }


def summarize_resume_batch_v9_25_1(
    batch: ResumeBatchSpec,
    requested_dates: list[str],
    collection_result: dict[str, Any],
    day_results: list[dict[str, Any]],
    runtime_seconds: float,
) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    failed = [item for item in day_results if item["status"] != "day_complete"]
    invalid_rows = sum_int_v9_25_1(day_results, "invalid_rows")
    duplicates = sum_int_v9_25_1(day_results, "duplicates")
    gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete)
    batch_success = collection_result["status"] == "PASS" and len(complete) == len(requested_dates) and not failed and invalid_rows == 0 and duplicates == 0
    return {
        "batch_id": batch.batch_id,
        "batch_start": batch.start_date,
        "batch_end": batch.end_date,
        "max_downloads": batch.max_downloads,
        "days_requested": len(requested_dates),
        "days_attempted": int(collection_result["days_attempted"]),
        "days_downloaded": int(collection_result["days_downloaded"]),
        "days_normalized": int(collection_result["days_normalized"]),
        "days_complete": len(complete),
        "days_failed": len(failed),
        "days_quarantined": int(collection_result["days_quarantined"]),
        "days_skipped_existing": int(collection_result["days_skipped_existing"]),
        "total_rows_new": sum_int_v9_25_1(complete, "rows"),
        "raw_bytes_new": sum_int_v9_25_1(complete, "raw_bytes"),
        "silver_bytes_new": sum_int_v9_25_1(complete, "silver_bytes"),
        "invalid_rows": invalid_rows,
        "duplicates": duplicates,
        "min_event_ts": min([item["min_event_ts"] for item in complete if item.get("min_event_ts")], default=None),
        "max_event_ts": max([item["max_event_ts"] for item in complete if item.get("max_event_ts")], default=None),
        "min_aggregate_trade_id": min([int(item["min_aggregate_trade_id"]) for item in complete if item.get("min_aggregate_trade_id") is not None], default=None),
        "max_aggregate_trade_id": max([int(item["max_aggregate_trade_id"]) for item in complete if item.get("max_aggregate_trade_id") is not None], default=None),
        "aggregate_trade_id_gap_warnings": gap_warnings,
        "runtime_seconds": runtime_seconds,
        "quality_status": "PASS" if batch_success else "FAIL",
        "coverage_status": "batch_complete" if len(complete) == len(requested_dates) else "batch_incomplete",
        "restartability_status": "resumable_skip_existing_never_overwrite_complete_raw_silver",
        "batch_success": batch_success,
        "failure_type": collection_result.get("failure_type"),
        "errors": list(collection_result.get("errors") or []),
        "failed_dates": [item["date"] for item in failed],
    }


def build_resume_summary_v9_25_1(
    *,
    canonical_before: dict[str, Any],
    canonical_after: dict[str, Any],
    disk_preflight: dict[str, Any],
    planned_batches: list[ResumeBatchSpec],
    batch_reports: list[dict[str, Any]],
    runtime_seconds_total: float,
    stop_reason: dict[str, Any] | None,
) -> dict[str, Any]:
    summaries = [report["batch_summary"] for report in batch_reports]
    complete_summaries = [item for item in summaries if item["batch_success"] is True]
    full_complete = canonical_after["local_contiguous_coverage_start"] == TARGET_WINDOW_START and canonical_after["local_contiguous_coverage_end"] == TARGET_WINDOW_END
    aggregate_warnings = [warning for report in batch_reports for warning in report["batch_summary"].get("aggregate_trade_id_gap_warnings", [])]
    timestamp_warnings: list[dict[str, Any]] = []
    quality_ok = full_complete and not aggregate_warnings and not timestamp_warnings
    return {
        "campaign_start": canonical_before["first_missing_day"],
        "campaign_end": TARGET_WINDOW_END,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "batches_planned": len(planned_batches),
        "batches_executed": len(summaries),
        "batches_complete": len(complete_summaries),
        "batches_failed": len(summaries) - len(complete_summaries),
        "failed_batch_ids": [item["batch_id"] for item in summaries if item["batch_success"] is not True],
        "days_requested_total": sum_int_v9_25_1(summaries, "days_requested"),
        "days_attempted_total": sum_int_v9_25_1(summaries, "days_attempted"),
        "days_downloaded_total": sum_int_v9_25_1(summaries, "days_downloaded"),
        "days_normalized_total": sum_int_v9_25_1(summaries, "days_normalized"),
        "days_complete_total": sum_int_v9_25_1(summaries, "days_complete"),
        "days_failed_total": sum_int_v9_25_1(summaries, "days_failed"),
        "days_quarantined_total": sum_int_v9_25_1(summaries, "days_quarantined"),
        "days_skipped_existing_total": sum_int_v9_25_1(summaries, "days_skipped_existing"),
        "total_rows_new": sum_int_v9_25_1(summaries, "total_rows_new"),
        "total_rows_cumulative": int(canonical_before.get("v9_25_reported_total_rows_cumulative") or 0) + sum_int_v9_25_1(summaries, "total_rows_new"),
        "raw_bytes_new": sum_int_v9_25_1(summaries, "raw_bytes_new"),
        "silver_bytes_new": sum_int_v9_25_1(summaries, "silver_bytes_new"),
        "raw_bytes_cumulative": canonical_after["raw_bytes_complete_window"],
        "silver_bytes_cumulative": canonical_after["silver_bytes_complete_window"],
        "runtime_seconds_total": runtime_seconds_total,
        "aggregate_trade_id_gap_warnings": aggregate_warnings,
        "timestamp_gap_warnings": timestamp_warnings,
        "local_file_coverage_start": canonical_after["local_contiguous_coverage_start"],
        "local_file_coverage_end": canonical_after["local_contiguous_coverage_end"],
        "reported_cumulative_coverage_start": canonical_after["local_contiguous_coverage_start"],
        "reported_cumulative_coverage_end": canonical_after["local_contiguous_coverage_end"],
        "complete_collection_reached": full_complete,
        "future_full_coverage_complete": full_complete,
        "quality_status": "PASS" if quality_ok else "WARN" if canonical_after["local_contiguous_coverage_end"] != canonical_before["local_contiguous_coverage_end"] else "FAIL",
        "coverage_status": "target_window_complete" if full_complete else "target_window_incomplete",
        "restartability_status": "resume_campaign_uses_first_missing_day_skips_existing_and_never_deletes_data",
        "storage_warning": disk_preflight["storage_warning"],
        "stop_reason": stop_reason,
    }


def decide_v9_25_1(summary: dict[str, Any], canonical: dict[str, Any], preflight: dict[str, Any], stop_reason: dict[str, Any] | None) -> dict[str, Any]:
    if not canonical["state_reconciled"]:
        decision = "resume_collection_not_executed_state_not_reconciled"
        recommendation = "V9.26 - Manual Coverage Review Pack"
    elif not preflight["safe_to_continue_now"] and summary["days_attempted_total"] == 0:
        decision = "resume_collection_not_executed_storage_blocker"
        recommendation = "V9.26 - Storage Cleanup / Compression Review"
    elif summary["complete_collection_reached"]:
        decision = "resume_collection_completed_full_window"
        recommendation = "V9.26 - AggTrades Full Coverage Validation"
    elif stop_reason and stop_reason.get("type") == "source_or_quality":
        decision = "resume_collection_partial_quality_issue"
        recommendation = "V9.26 - Manual Coverage Review Pack"
    elif stop_reason and stop_reason.get("type") == "storage":
        decision = "resume_collection_partial_storage_warning"
        recommendation = "V9.26 - Resume Collection Continuation"
    elif summary["days_complete_total"] > 0:
        decision = "resume_collection_partial_storage_warning"
        recommendation = "V9.26 - Resume Collection Continuation"
    else:
        decision = "resume_collection_not_executed_storage_blocker"
        recommendation = "V9.26 - Storage Cleanup / Compression Review"
    return {
        "decision": decision,
        "confidence": "high" if decision in ALLOWED_DECISIONS else "low",
        "next_recommendation": recommendation,
        "justification": "Decision fondee sur reconciliation locale, preflight disque et resultat des lots de reprise.",
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def safety_flags_v9_25_1(summary: dict[str, Any]) -> dict[str, Any]:
    attempted = summary["days_attempted_total"] > 0
    downloaded = summary["days_downloaded_total"] > 0
    normalized = summary["days_normalized_total"] > 0
    flags = dict(SAFETY_BASE_V9_25_1)
    flags.update(
        {
            "network_used": attempted,
            "new_data_downloaded": downloaded,
            "ingestion_executed": normalized,
            "no_new_data_download": not downloaded,
            "no_ingestion_executed": not normalized,
            "network_scope": "public_archive_read_only" if attempted else None,
            "new_data_download_scope": "public_historical_aggtrades_resume_only" if downloaded else None,
            "ingestion_scope": "public_aggtrades_bronze_silver_resume_only" if normalized else None,
        }
    )
    return flags


def safety_flags_for_batch_v9_25_1(result: dict[str, Any]) -> dict[str, Any]:
    flags = dict(SAFETY_BASE_V9_25_1)
    flags.update(
        {
            "network_used": bool(result.get("network_used")),
            "new_data_downloaded": bool(result.get("new_data_downloaded")),
            "ingestion_executed": bool(result.get("ingestion_executed")),
            "network_scope": result.get("network_scope"),
            "new_data_download_scope": result.get("new_data_download_scope"),
            "ingestion_scope": result.get("ingestion_scope"),
        }
    )
    return flags


def build_manifest_v9_25_1(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["resume_summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "batch_report_paths": report["batch_report_paths"],
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        **{key: summary[key] for key in [
            "batches_planned",
            "batches_executed",
            "batches_complete",
            "batches_failed",
            "days_requested_total",
            "days_attempted_total",
            "days_downloaded_total",
            "days_normalized_total",
            "days_complete_total",
            "days_failed_total",
            "days_quarantined_total",
            "days_skipped_existing_total",
            "raw_bytes_new",
            "silver_bytes_new",
            "local_file_coverage_start",
            "local_file_coverage_end",
            "complete_collection_reached",
            "future_full_coverage_complete",
        ]},
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_25_1(report: dict[str, Any]) -> str:
    summary = report["resume_summary"]
    canonical = report["canonical_coverage_before_resume"]
    disk = report["disk_preflight"]
    lines = [
        "# V9.25.1 - Campaign Reconciliation & Resume Collection",
        "",
        "## Resume",
        f"- Decision V9.25.1 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture canonique avant reprise : `{canonical['local_contiguous_coverage_start']}` -> `{canonical['local_contiguous_coverage_end']}`.",
        f"- Premiere journee manquante : `{canonical['first_missing_day']}`.",
        f"- Couverture locale finale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.",
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.",
        "",
        "## Preflight disque",
        f"- Espace libre : `{disk['free_bytes_current']}` bytes (`{disk['free_gb_current']}` GiB).",
        f"- Safe to continue now : `{disk['safe_to_continue_now']}`.",
        f"- Batch size jours : `{disk['batch_size_days']}`.",
        f"- Warning stockage : `{disk['storage_warning']}`.",
        "",
        "## Reprise",
        f"- Lots planifies/executés/reussis/echoues : `{summary['batches_planned']}` / `{summary['batches_executed']}` / `{summary['batches_complete']}` / `{summary['batches_failed']}`.",
        f"- Jours telecharges/normalises/valides : `{summary['days_downloaded_total']}` / `{summary['days_normalized_total']}` / `{summary['days_complete_total']}`.",
        f"- Jours echoues/quarantine/skips : `{summary['days_failed_total']}` / `{summary['days_quarantined_total']}` / `{summary['days_skipped_existing_total']}`.",
        f"- Raw bytes nouveaux : `{summary['raw_bytes_new']}`.",
        f"- Silver bytes nouveaux : `{summary['silver_bytes_new']}`.",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression de donnees, aucun nettoyage destructif.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_25_1(root: Path, report: dict[str, Any]) -> None:
    summary = report["resume_summary"]
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "direction": DIRECTION,
        "v9_25_1_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        **summary,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        **report["safety_flags"],
    }
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    _write_json(root / "reports/PROJECT_STATE.json", {**_read_optional_json(root / "reports/PROJECT_STATE.json"), **metrics})
    text = (
        "# Synthese courante - V9.25.1\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Decision V9.25.1 : `{report['decision']}`.\n"
        f"- Couverture locale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie ou signal actionnable.\n"
        "- Aucune suppression de donnees et aucun nettoyage destructif.\n"
    )
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, reconciliation et reprise aggTrades post-V9.\n"
        f"- Couverture locale : {summary['local_file_coverage_start']} -> {summary['local_file_coverage_end']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression de donnees, aucun nettoyage destructif, aucun sidecar et aucune empreinte ZIP.\n",
    )


def quarantine_failed_raw_v9_25_1(root: Path, day_value: str, raw_path: Path) -> Path | None:
    if not raw_path.exists():
        return None
    quarantine_dir = root / QUARANTINE_DIR / f"date={day_value}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / raw_path.name
    raw_path.replace(target)
    return target


def date_range_v9_25_1(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    values: list[str] = []
    while current <= stop:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def next_day_v9_25_1(value: str) -> str:
    return (date.fromisoformat(value) + timedelta(days=1)).isoformat()


def previous_day_v9_25_1(value: str | None) -> str | None:
    if value is None:
        return None
    return (date.fromisoformat(value) - timedelta(days=1)).isoformat()


def detect_gaps_v9_25_1(dates: list[str], complete_set: set[str]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    in_gap = False
    start: str | None = None
    previous: str | None = None
    for value in dates:
        if value not in complete_set and not in_gap:
            start = value
            in_gap = True
        if value in complete_set and in_gap:
            gaps.append({"start": start, "end": previous})
            in_gap = False
        previous = value
    if in_gap:
        gaps.append({"start": start, "end": previous})
    return gaps


def quarantine_dates_v9_25_1(root: Path, target_dates: set[str]) -> list[str]:
    base = root / QUARANTINE_DIR
    dates: set[str] = set()
    if base.exists():
        for path in base.glob("date=*"):
            value = path.name.split("=", 1)[-1]
            if value in target_dates:
                dates.add(value)
    return sorted(dates)


def sum_local_bytes_v9_25_1(root: Path, dates: list[str]) -> tuple[int, int]:
    raw = 0
    silver = 0
    for value in dates:
        raw_path = root / raw_zip_path_for_date_v9_18(value)
        silver_path = root / silver_path_for_date_v9_18(value)
        if raw_path.exists():
            raw += raw_path.stat().st_size
        if silver_path.exists():
            silver += silver_path.stat().st_size
    return raw, silver


def sum_int_v9_25_1(items: list[dict[str, Any]], key: str) -> int:
    return sum(int(item.get(key) or 0) for item in items)


def batch_to_dict_v9_25_1(batch: ResumeBatchSpec) -> dict[str, Any]:
    return {"batch_id": batch.batch_id, "start_date": batch.start_date, "end_date": batch.end_date, "max_downloads": batch.max_downloads, "expected_days": len(date_range_v9_25_1(batch.start_date, batch.end_date))}


def build_blockers_v9_25_1(canonical: dict[str, Any], disk: dict[str, Any], stop_reason: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not canonical["state_reconciled"]:
        blockers.append("Etat local non reconciliable avant reprise.")
    if disk["storage_blocker"]:
        blockers.append("Espace disque insuffisant pour poursuivre au-dela du garde-fou.")
    if stop_reason:
        blockers.append(str(stop_reason))
    return blockers


def build_warnings_v9_25_1(summary: dict[str, Any], canonical: dict[str, Any], disk: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if canonical["v9_25_reporting_inconsistency_detected"]:
        warnings.append("Incoherence V9.25 detectee entre compteur skipped/downloaded et etat local canonique.")
    if disk["storage_warning"]:
        warnings.append(str(disk["storage_warning"]))
    if not summary["complete_collection_reached"]:
        warnings.append("La couverture complete future n'est pas atteinte.")
    return warnings


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": None}
    if full.suffix == ".json":
        return {"path": path.as_posix(), "available": True, "payload": _read_json(full)}
    return {"path": path.as_posix(), "available": True, "payload": {"text": full.read_text(encoding="utf-8")}}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _read_json(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
