from __future__ import annotations

import json
import shutil
import subprocess
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
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    FINDINGS,
    QUARANTINE_DIR,
    build_public_archive_url_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    normalize_raw_zip_to_silver_v9_25,
)


VERSION = "V9.27"
SOURCE_VERSION = "V9.26"
LAST_VALIDATED_VERSION = "V9.26"
DIRECTION = "aggtrades_post_v9_storage_recheck_resume"
USER_REPORTED_AVAILABLE_GIB = 200.0

MIN_FREE_BYTES = 60 * 1024**3
MICRO_FREE_BYTES = 100 * 1024**3
COMFORT_FREE_BYTES = 150 * 1024**3
FULL_CAMPAIGN_FREE_BYTES = 180 * 1024**3

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_storage_recheck_resume_v9_27_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_storage_recheck_resume_v9_27.md")

INPUT_PATHS = {
    "v9_26_storage_gate": Path("reports/data/aggtrades_post_v9_storage_resume_campaign_v9_26.json"),
    "v9_26_manifest": Path("reports/manifests/aggtrades_post_v9_storage_resume_campaign_v9_26_manifest.json"),
    "v9_25_1_campaign": Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"),
    "v9_25_1_batch01": Path("reports/data/aggtrades_post_v9_resume_batch01_v9_25_1.json"),
    "v9_25_1_manifest": Path("reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json"),
    "v9_25_campaign": Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"),
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
    "storage_recheck_resume_completed_full_window",
    "storage_recheck_resume_partial_storage_warning",
    "storage_recheck_resume_partial_source_issue",
    "storage_recheck_resume_partial_quality_issue",
    "storage_recheck_not_executed_storage_blocker",
    "storage_recheck_not_executed_measurement_discrepancy",
    "storage_recheck_not_executed_state_not_reconciled",
    "stop_aggtrades_completion_branch",
}

FINDINGS_V9_27 = dict(FINDINGS)
SAFETY_BASE_V9_27 = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
}


@dataclass(frozen=True)
class StorageRecheckBatchSpec:
    batch_id: str
    start_date: str
    end_date: str
    max_downloads: int

    @property
    def report_path(self) -> Path:
        suffix = self.batch_id.rsplit("_", 1)[-1]
        return Path(f"reports/data/aggtrades_post_v9_storage_recheck_batch{suffix}_v9_27.json")


def run_aggtrades_post_v9_storage_recheck_resume_v9_27(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_storage_recheck_resume_v9_27(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_27(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_27(report))
    update_state_surfaces_v9_27(root, report)
    return report


def build_aggtrades_post_v9_storage_recheck_resume_v9_27(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    canonical_before = reconcile_campaign_state_v9_27(root, inputs)
    disk_preflight = build_disk_preflight_v9_27(root, canonical_before)
    can_collect = (
        canonical_before["state_reconciled"]
        and disk_preflight["safe_to_continue_now"]
        and canonical_before["first_missing_day"] is not None
    )
    planned_batches = (
        build_storage_recheck_batches_v9_27(canonical_before["first_missing_day"], TARGET_WINDOW_END, disk_preflight["batch_size_days"])
        if can_collect
        else []
    )
    executed_batch_specs: list[StorageRecheckBatchSpec] = []
    batch_reports: list[dict[str, Any]] = []
    stop_reason = determine_initial_stop_reason_v9_27(canonical_before, disk_preflight)
    if can_collect:
        stop_reason = None
        while True:
            fresh_inventory = build_local_coverage_inventory_v9_27(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
            if fresh_inventory["local_contiguous_coverage_start"] == TARGET_WINDOW_START and fresh_inventory["local_contiguous_coverage_end"] == TARGET_WINDOW_END:
                break
            if fresh_inventory["first_missing_day"] is None:
                break
            fresh_preflight = build_disk_preflight_v9_27(root, fresh_inventory)
            if not fresh_preflight["safe_to_continue_now"]:
                stop_reason = {
                    "type": "storage",
                    "batch_id": f"V9.27_batch_{len(executed_batch_specs) + 1:02d}",
                    "message": "free disk fell below storage guard before next batch",
                }
                break
            batch = build_next_storage_recheck_batch_v9_27(
                first_missing_day=fresh_inventory["first_missing_day"],
                end=TARGET_WINDOW_END,
                batch_size_days=fresh_preflight["batch_size_days"],
                batch_index=len(executed_batch_specs) + 1,
            )
            executed_batch_specs.append(batch)
            batch_report = execute_storage_recheck_batch_v9_27(root, batch, fresh_preflight)
            _write_json(root / batch.report_path, batch_report)
            batch_reports.append(batch_report)
            if batch_report["batch_summary"]["batch_success"] is not True:
                stop_reason = {
                    "type": batch_report["batch_summary"].get("failure_type") or "quality",
                    "batch_id": batch.batch_id,
                    "message": "storage recheck campaign stopped after first non-complete internal batch",
                }
                break
    planned_batches_for_report = executed_batch_specs if executed_batch_specs else planned_batches
    runtime = round(time.monotonic() - started, 3)
    canonical_after = build_local_coverage_inventory_v9_27(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
    summary = build_storage_recheck_summary_v9_27(
        canonical_before=canonical_before,
        canonical_after=canonical_after,
        disk_preflight=disk_preflight,
        planned_batches=planned_batches_for_report,
        batch_reports=batch_reports,
        runtime_seconds_total=runtime,
        stop_reason=stop_reason,
    )
    decision = decide_v9_27(summary, canonical_before, disk_preflight, stop_reason)
    safety_flags = safety_flags_v9_27(summary)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "campaign_start": canonical_before["first_missing_day"],
        "campaign_end": TARGET_WINDOW_END,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "measurement_results": disk_preflight["measurement_results"],
        "measurement_discrepancy_detected": disk_preflight["measurement_discrepancy_detected"],
        "measurement_discrepancy_explanation": disk_preflight["measurement_discrepancy_explanation"],
        "disk_preflight": disk_preflight,
        "safe_to_resume_collection": bool(disk_preflight["safe_to_continue_now"] and disk_preflight["resume_allowed_now"]),
        "canonical_coverage_before_resume": canonical_before,
        "first_missing_day_before_resume": canonical_before["first_missing_day"],
        "batches_planned": [batch_to_dict_v9_27(batch) for batch in planned_batches_for_report],
        "batches_executed": [item["batch_summary"] for item in batch_reports],
        "batch_report_paths": [item["report_path"] for item in batch_reports],
        "storage_recheck_summary": summary,
        **summary,
        "decision": decision["decision"],
        "v9_27_decision": decision,
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
        "findings": FINDINGS_V9_27,
        "safety_flags": safety_flags,
        "blockers": build_blockers_v9_27(canonical_before, disk_preflight, stop_reason),
        "warnings": build_warnings_v9_27(summary, canonical_before, disk_preflight),
        "limitations": [
            "V9.27 mesure le volume reel du projet et de data avant toute reprise.",
            "Aucune suppression, compression, migration ou correction destructive de donnees n'est effectuee.",
            "Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal n'est cree.",
        ],
    }
    return report


def determine_initial_stop_reason_v9_27(canonical: dict[str, Any], disk: dict[str, Any]) -> dict[str, Any] | None:
    if not canonical["state_reconciled"]:
        return {"type": "state", "message": "canonical campaign state is not reconciled"}
    if canonical["first_missing_day"] is None:
        return {"type": "complete", "message": "target window already complete before V9.27"}
    if disk["storage_blocker"]:
        return {"type": "storage", "message": "free disk space is below V9.27 minimum threshold"}
    return None


def reconcile_campaign_state_v9_27(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    local = build_local_coverage_inventory_v9_27(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
    source = inputs.get("v9_26_storage_gate", {}).get("payload", {})
    source_end = source.get("local_file_coverage_end") if isinstance(source, dict) else None
    coverage_more_advanced = bool(local["local_contiguous_coverage_end"] and source_end and local["local_contiguous_coverage_end"] > source_end)
    return {
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "source_reported_coverage_start": source.get("local_file_coverage_start") if isinstance(source, dict) else None,
        "source_reported_coverage_end": source_end,
        "source_report_payload": source if isinstance(source, dict) else {},
        "local_coverage_more_advanced_than_v9_26": coverage_more_advanced,
        **local,
        "state_reconciled": local["days_partial"] == 0 and len(gaps_before_first_missing_v9_27(local)) == 0,
        "reconciliation_basis": "local raw/silver file metadata plus V9.26, V9.25 and prior reports",
    }


def build_local_coverage_inventory_v9_27(root: Path, start: str, end: str) -> dict[str, Any]:
    dates = date_range_v9_27(start, end)
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
    complete_set = set(complete)
    contiguous: list[str] = []
    for day_value in dates:
        if day_value not in complete_set:
            break
        contiguous.append(day_value)
    quarantined = quarantine_dates_v9_27(root, set(dates))
    first_gap = next((day_value for day_value in dates if day_value not in complete_set), None)
    return {
        "local_file_coverage_start": complete[0] if complete else None,
        "local_file_coverage_end": complete[-1] if complete else None,
        "local_contiguous_coverage_start": contiguous[0] if contiguous else None,
        "local_contiguous_coverage_end": contiguous[-1] if contiguous else None,
        "first_missing_day": first_gap,
        "last_complete_day_before_gap": previous_day_v9_27(first_gap) if first_gap else complete[-1] if complete else None,
        "days_complete": len(complete),
        "days_missing": len(missing),
        "days_partial": len(partial),
        "days_quarantined": len(quarantined),
        "gaps_detected": detect_gaps_v9_27(dates, complete_set),
        "complete_dates_sample": {"first": complete[:3], "last": complete[-3:]},
        "missing_dates_sample": {"first": missing[:3], "last": missing[-3:]},
        "partial_dates": partial,
        "quarantined_dates_sample": {"first": quarantined[:3], "last": quarantined[-3:]},
        "raw_bytes_complete_window": raw_bytes,
        "silver_bytes_complete_window": silver_bytes,
    }


def build_disk_preflight_v9_27(root: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    data_root = root / "data"
    measurement_results = build_measurement_results_v9_27(root, data_root if data_root.exists() else root)
    project_disk = shutil.disk_usage(root)
    data_disk = shutil.disk_usage(data_root if data_root.exists() else root)
    effective_free = data_disk.free
    policy = classify_disk_policy_v9_27(effective_free)
    days_remaining = int(canonical.get("days_missing") or 0) + int(canonical.get("days_partial") or 0)
    complete_days = int(canonical.get("days_complete") or 0)
    avg_raw = int(int(canonical.get("raw_bytes_complete_window") or 0) / complete_days) if complete_days else 0
    avg_silver = int(int(canonical.get("silver_bytes_complete_window") or 0) / complete_days) if complete_days else 0
    estimated_raw = avg_raw * days_remaining
    estimated_silver = avg_silver * days_remaining
    discrepancy = measurement_results["measurement_discrepancy_detected"]
    return {
        "measurement_results": measurement_results,
        "project_mount_path": mount_path_for_v9_27(root),
        "data_mount_path": mount_path_for_v9_27(data_root if data_root.exists() else root),
        "free_bytes_project_mount": project_disk.free,
        "free_gib_project_mount": round(project_disk.free / 1024**3, 3),
        "free_bytes_data_mount": data_disk.free,
        "free_gib_data_mount": round(data_disk.free / 1024**3, 3),
        "raw_bytes_current": directory_size_bytes_v9_27(root / "data/raw"),
        "silver_bytes_current": directory_size_bytes_v9_27(root / "data/silver"),
        "quarantine_bytes_current": directory_size_bytes_v9_27(root / "data/quarantine"),
        "estimated_remaining_raw_bytes": estimated_raw,
        "estimated_remaining_silver_bytes": estimated_silver,
        "estimated_remaining_total_bytes": estimated_raw + estimated_silver,
        "minimum_free_bytes_required": MIN_FREE_BYTES,
        "campaign_resume_free_bytes_required": COMFORT_FREE_BYTES,
        "full_campaign_free_bytes_required": FULL_CAMPAIGN_FREE_BYTES,
        "safe_to_continue_now": policy["safe_to_continue_now"],
        "resume_allowed_now": policy["resume_allowed_now"],
        "completion_campaign_allowed_now": policy["completion_campaign_allowed_now"],
        "storage_warning": policy["storage_warning"],
        "storage_blocker": policy["storage_blocker"],
        "measurement_discrepancy_detected": discrepancy,
        "measurement_discrepancy_explanation": measurement_results["measurement_discrepancy_explanation"],
        "batch_size_days": policy["batch_size_days"],
        "estimate_basis": "average local complete-day raw/silver bytes in target window",
    }


def build_measurement_results_v9_27(root: Path, data_root: Path) -> dict[str, Any]:
    commands = {
        "df_h_project": ["df", "-h", str(root)],
        "df_h_data": ["df", "-h", str(data_root)],
        "df_g_project": ["df", "-g", str(root)],
        "df_g_data": ["df", "-g", str(data_root)],
        "diskutil_info_project": ["diskutil", "info", str(root)],
        "diskutil_apfs_list": ["diskutil", "apfs", "list"],
        "du_raw": ["du", "-sh", str(root / "data/raw")],
        "du_silver": ["du", "-sh", str(root / "data/silver")],
        "du_quarantine": ["du", "-sh", str(root / "data/quarantine")],
    }
    raw_outputs = {name: run_measurement_command_v9_27(command) for name, command in commands.items()}
    project_stat = statvfs_measurement_v9_27(root)
    data_stat = statvfs_measurement_v9_27(data_root)
    apfs_text = raw_outputs["diskutil_apfs_list"]["stdout"]
    apfs_not_allocated = extract_first_bytes_before_label_v9_27(apfs_text, "Capacity Not Allocated:")
    diskutil_info_text = raw_outputs["diskutil_info_project"]["stdout"]
    diskutil_available = extract_first_bytes_before_label_v9_27(diskutil_info_text, "Container Free Space:")
    operational_free_gib = min(project_stat["free_gib_bavail"], data_stat["free_gib_bavail"])
    discrepancy = USER_REPORTED_AVAILABLE_GIB - operational_free_gib > 50.0
    explanation = (
        "L'utilisateur indique environ 200 GiB libres, mais df/statvfs et APFS exposent environ "
        f"{operational_free_gib:.3f} GiB utilisables sur le volume data. Si Finder inclut de l'espace purgeable ou une autre vue APFS, "
        "cet espace n'est pas considere sur pour une collecte massive tant qu'il n'apparait pas dans df/statvfs."
        if discrepancy
        else "Les mesures df/statvfs/APFS sont coherentes; aucun ecart operationnel majeur n'est detecte."
    )
    return {
        "project_path": str(root),
        "data_path": str(data_root),
        "project_mount_path": mount_path_for_v9_27(root),
        "data_mount_path": mount_path_for_v9_27(data_root),
        "df_free_gib_project": parse_df_available_gib_v9_27(raw_outputs["df_g_project"]["stdout"]),
        "df_free_gib_data": parse_df_available_gib_v9_27(raw_outputs["df_g_data"]["stdout"]),
        "statvfs_free_gib_project": project_stat["free_gib_bavail"],
        "statvfs_free_gib_data": data_stat["free_gib_bavail"],
        "diskutil_available_gib": round(diskutil_available / 1024**3, 3) if diskutil_available is not None else None,
        "diskutil_free_gib": round(apfs_not_allocated / 1024**3, 3) if apfs_not_allocated is not None else None,
        "apfs_purgeable_or_available_notes": extract_apfs_notes_v9_27(apfs_text),
        "raw_bytes_current": directory_size_bytes_v9_27(root / "data/raw"),
        "silver_bytes_current": directory_size_bytes_v9_27(root / "data/silver"),
        "quarantine_bytes_current": directory_size_bytes_v9_27(root / "data/quarantine"),
        "measurement_discrepancy_detected": discrepancy,
        "measurement_discrepancy_explanation": explanation,
        "user_reported_available_gib": USER_REPORTED_AVAILABLE_GIB,
        "raw_command_outputs": raw_outputs,
        "statvfs_project": project_stat,
        "statvfs_data": data_stat,
    }


def classify_disk_policy_v9_27(free_bytes: int) -> dict[str, Any]:
    if free_bytes < MIN_FREE_BYTES:
        return {
            "safe_to_continue_now": False,
            "resume_allowed_now": False,
            "completion_campaign_allowed_now": False,
            "storage_blocker": True,
            "storage_warning": "free_disk_below_60gib_stop_before_collection",
            "batch_size_days": 0,
        }
    if free_bytes < MICRO_FREE_BYTES:
        return {
            "safe_to_continue_now": True,
            "resume_allowed_now": True,
            "completion_campaign_allowed_now": False,
            "storage_blocker": False,
            "storage_warning": "free_disk_between_60gib_and_100gib_micro_batches_7_days",
            "batch_size_days": 7,
        }
    if free_bytes < COMFORT_FREE_BYTES:
        return {
            "safe_to_continue_now": True,
            "resume_allowed_now": True,
            "completion_campaign_allowed_now": False,
            "storage_blocker": False,
            "storage_warning": "free_disk_between_100gib_and_150gib_batches_30_days",
            "batch_size_days": 30,
        }
    if free_bytes < FULL_CAMPAIGN_FREE_BYTES:
        return {
            "safe_to_continue_now": True,
            "resume_allowed_now": True,
            "completion_campaign_allowed_now": False,
            "storage_blocker": False,
            "storage_warning": "free_disk_between_150gib_and_180gib_batches_60_days",
            "batch_size_days": 60,
        }
    return {
        "safe_to_continue_now": True,
        "resume_allowed_now": True,
        "completion_campaign_allowed_now": True,
        "storage_blocker": False,
        "storage_warning": "free_disk_above_180gib_completion_campaign_allowed",
        "batch_size_days": 90,
    }


def build_storage_recheck_batches_v9_27(start: str | None, end: str, batch_size_days: int) -> list[StorageRecheckBatchSpec]:
    if start is None or batch_size_days <= 0:
        return []
    dates = date_range_v9_27(start, end)
    batches: list[StorageRecheckBatchSpec] = []
    for index, offset in enumerate(range(0, len(dates), batch_size_days), start=1):
        chunk = dates[offset : offset + batch_size_days]
        batches.append(StorageRecheckBatchSpec(f"V9.27_batch_{index:02d}", chunk[0], chunk[-1], len(chunk)))
    return batches


def build_next_storage_recheck_batch_v9_27(
    *,
    first_missing_day: str,
    end: str,
    batch_size_days: int,
    batch_index: int,
) -> StorageRecheckBatchSpec:
    if batch_size_days <= 0:
        raise ValueError("V9.27 cannot build a collection batch without a positive max_downloads limit.")
    dates = date_range_v9_27(first_missing_day, end)
    chunk = dates[:batch_size_days]
    return StorageRecheckBatchSpec(f"V9.27_batch_{batch_index:02d}", chunk[0], chunk[-1], len(chunk))


def execute_storage_recheck_batch_v9_27(root: Path, batch: StorageRecheckBatchSpec, preflight: dict[str, Any]) -> dict[str, Any]:
    requested_dates = date_range_v9_27(batch.start_date, batch.end_date)
    started = time.monotonic()
    collection_result = collect_storage_recheck_batch_v9_27(root, batch, requested_dates, preflight)
    day_results = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    summary = summarize_storage_recheck_batch_v9_27(batch, requested_dates, collection_result, day_results, round(time.monotonic() - started, 3))
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if summary["batch_success"] else "FAIL",
        "created_at_utc": _utc_now(),
        "report_path": batch.report_path.as_posix(),
        "batch_id": batch.batch_id,
        "batch_spec": batch_to_dict_v9_27(batch),
        "collection_result": collection_result,
        "batch_summary": summary,
        "day_results": day_results,
        "safety_flags": safety_flags_v9_27(summary),
    }


def collect_storage_recheck_batch_v9_27(root: Path, batch: StorageRecheckBatchSpec, requested_dates: list[str], preflight: dict[str, Any]) -> dict[str, Any]:
    attempted: list[str] = []
    downloaded: list[str] = []
    normalized: list[str] = []
    skipped_existing: list[str] = []
    quarantined: list[str] = []
    errors: list[str] = []
    failure_type: str | None = None
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            skipped_existing.append(day_value)
            continue
        if shutil.disk_usage(root / "data" if (root / "data").exists() else root).free < MIN_FREE_BYTES:
            failure_type = "storage"
            errors.append(f"{day_value}: storage guard stopped resume before download")
            break
        attempted.append(day_value)
        try:
            if not (raw_path.exists() and raw_path.stat().st_size > 0):
                download_public_archive_v9_24(build_public_archive_url_v9_18(day_value), raw_path)
                downloaded.append(day_value)
            normalize_raw_zip_to_silver_v9_25(raw_path, silver_path, day_value)
            normalized.append(day_value)
        except Exception as exc:  # noqa: BLE001
            failure_type = "source_or_quality"
            q_path = quarantine_failed_raw_v9_27(root, day_value, raw_path)
            if q_path:
                quarantined.append(day_value)
            errors.append(f"{day_value}: {exc}")
            break
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": bool(attempted),
        "network_used": bool(attempted),
        "new_data_downloaded": bool(downloaded),
        "ingestion_executed": bool(normalized),
        "network_scope": "public_archive_read_only" if attempted else None,
        "new_data_download_scope": "public_historical_aggtrades_storage_recheck_resume_only" if downloaded else None,
        "ingestion_scope": "public_aggtrades_bronze_silver_storage_recheck_resume_only" if normalized else None,
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


def summarize_storage_recheck_batch_v9_27(
    batch: StorageRecheckBatchSpec,
    requested_dates: list[str],
    collection_result: dict[str, Any],
    day_results: list[dict[str, Any]],
    runtime_seconds: float,
) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    failed = [item for item in day_results if item["status"] != "day_complete"]
    invalid_rows = sum_int_v9_27(day_results, "invalid_rows")
    duplicates = sum_int_v9_27(day_results, "duplicates")
    gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete)
    batch_success = collection_result["status"] == "PASS" and len(complete) == len(requested_dates) and not failed and invalid_rows == 0 and duplicates == 0
    failure_type = collection_result.get("failure_type")
    if failure_type is None and not batch_success:
        failure_type = "quality"
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
        "total_rows_new": sum_int_v9_27(complete, "rows"),
        "raw_bytes_new": sum_int_v9_27(complete, "raw_bytes"),
        "silver_bytes_new": sum_int_v9_27(complete, "silver_bytes"),
        "invalid_rows": invalid_rows,
        "duplicates": duplicates,
        "aggregate_trade_id_gap_warnings": gap_warnings,
        "runtime_seconds": runtime_seconds,
        "quality_status": "PASS" if batch_success else "FAIL",
        "coverage_status": "batch_complete" if len(complete) == len(requested_dates) else "batch_incomplete",
        "restartability_status": "resumable_skip_existing_never_overwrite_complete_raw_silver",
        "batch_success": batch_success,
        "failure_type": failure_type,
        "errors": list(collection_result.get("errors") or []),
        "failed_dates": [item["date"] for item in failed],
    }


def build_storage_recheck_summary_v9_27(
    *,
    canonical_before: dict[str, Any],
    canonical_after: dict[str, Any],
    disk_preflight: dict[str, Any],
    planned_batches: list[StorageRecheckBatchSpec],
    batch_reports: list[dict[str, Any]],
    runtime_seconds_total: float,
    stop_reason: dict[str, Any] | None,
) -> dict[str, Any]:
    summaries = [report["batch_summary"] for report in batch_reports]
    complete_summaries = [item for item in summaries if item["batch_success"] is True]
    full_complete = canonical_after["local_contiguous_coverage_start"] == TARGET_WINDOW_START and canonical_after["local_contiguous_coverage_end"] == TARGET_WINDOW_END
    aggregate_warnings = [warning for report in batch_reports for warning in report["batch_summary"].get("aggregate_trade_id_gap_warnings", [])]
    timestamp_warnings: list[dict[str, Any]] = []
    rows_before = _source_cumulative_int_v9_27(canonical_before, "total_rows_cumulative")
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
        "days_requested_total": sum_int_v9_27(summaries, "days_requested"),
        "days_attempted_total": sum_int_v9_27(summaries, "days_attempted"),
        "days_downloaded_total": sum_int_v9_27(summaries, "days_downloaded"),
        "days_normalized_total": sum_int_v9_27(summaries, "days_normalized"),
        "days_complete_total": sum_int_v9_27(summaries, "days_complete"),
        "days_failed_total": sum_int_v9_27(summaries, "days_failed"),
        "days_quarantined_total": sum_int_v9_27(summaries, "days_quarantined"),
        "days_skipped_existing_total": sum_int_v9_27(summaries, "days_skipped_existing"),
        "total_rows_new": sum_int_v9_27(summaries, "total_rows_new"),
        "total_rows_cumulative": rows_before + sum_int_v9_27(summaries, "total_rows_new"),
        "raw_bytes_new": sum_int_v9_27(summaries, "raw_bytes_new"),
        "silver_bytes_new": sum_int_v9_27(summaries, "silver_bytes_new"),
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
        "quality_status": "PASS" if full_complete and not aggregate_warnings and not timestamp_warnings else "FAIL" if not summaries else "WARN",
        "coverage_status": "target_window_complete" if full_complete else "target_window_incomplete",
        "restartability_status": "storage_recheck_uses_first_missing_day_skips_existing_and_never_deletes_data",
        "storage_warning": disk_preflight["storage_warning"],
        "stop_reason": stop_reason,
    }


def decide_v9_27(summary: dict[str, Any], canonical: dict[str, Any], disk: dict[str, Any], stop_reason: dict[str, Any] | None) -> dict[str, Any]:
    if not canonical["state_reconciled"]:
        decision = "storage_recheck_not_executed_state_not_reconciled"
        recommendation = "V9.28 - Manual Storage Diagnosis Pack"
    elif disk.get("measurement_discrepancy_detected") and summary["days_attempted_total"] == 0:
        decision = "storage_recheck_not_executed_measurement_discrepancy"
        recommendation = "V9.28 - Manual Storage Diagnosis Pack"
    elif not disk["safe_to_continue_now"] and summary["days_attempted_total"] == 0:
        decision = "storage_recheck_not_executed_storage_blocker"
        recommendation = "V9.28 - Storage Cleanup / Compression Review"
    elif not disk["resume_allowed_now"] and summary["days_attempted_total"] == 0:
        decision = "storage_recheck_not_executed_storage_blocker"
        recommendation = "V9.28 - Storage Cleanup / Compression Review"
    elif summary["complete_collection_reached"]:
        decision = "storage_recheck_resume_completed_full_window"
        recommendation = "V9.28 - AggTrades Full Coverage Validation"
    elif stop_reason and stop_reason.get("type") in {"source_or_quality", "quality", "batch_failure"}:
        decision = "storage_recheck_resume_partial_quality_issue"
        recommendation = "V9.28 - Resume Collection Continuation"
    elif stop_reason and stop_reason.get("type") == "storage":
        decision = "storage_recheck_resume_partial_storage_warning" if summary["days_complete_total"] > 0 else "storage_recheck_not_executed_storage_blocker"
        recommendation = "V9.28 - Storage Cleanup / Compression Review"
    elif summary["days_complete_total"] > 0:
        decision = "storage_recheck_resume_partial_storage_warning"
        recommendation = "V9.28 - Resume Collection Continuation"
    else:
        decision = "storage_recheck_not_executed_storage_blocker"
        recommendation = "V9.28 - Storage Cleanup / Compression Review"
    return {
        "decision": decision,
        "confidence": "high",
        "next_recommendation": recommendation,
        "justification": "Decision fondee sur le volume reel contenant data/raw et data/silver, la reconciliation locale et les resultats de reprise.",
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def safety_flags_v9_27(summary: dict[str, Any]) -> dict[str, Any]:
    attempted = int(summary.get("days_attempted_total", summary.get("days_attempted", 0)) or 0) > 0
    downloaded = int(summary.get("days_downloaded_total", summary.get("days_downloaded", 0)) or 0) > 0
    normalized = int(summary.get("days_normalized_total", summary.get("days_normalized", 0)) or 0) > 0
    flags = dict(SAFETY_BASE_V9_27)
    flags.update(
        {
            "network_used": attempted,
            "new_data_downloaded": downloaded,
            "ingestion_executed": normalized,
            "no_new_data_download": not downloaded,
            "no_ingestion_executed": not normalized,
            "network_scope": "public_archive_read_only" if attempted else None,
            "new_data_download_scope": "public_historical_aggtrades_storage_recheck_resume_only" if downloaded else None,
            "ingestion_scope": "public_aggtrades_bronze_silver_storage_recheck_resume_only" if normalized else None,
        }
    )
    return flags


def build_manifest_v9_27(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["storage_recheck_summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
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
        "disk_preflight": report["disk_preflight"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_27(report: dict[str, Any]) -> str:
    summary = report["storage_recheck_summary"]
    canonical = report["canonical_coverage_before_resume"]
    disk = report["disk_preflight"]
    lines = [
        "# V9.27 - Storage Recheck & Resume Collection",
        "",
        "## Resume",
        f"- Decision V9.27 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture canonique avant reprise : `{canonical['local_contiguous_coverage_start']}` -> `{canonical['local_contiguous_coverage_end']}`.",
        f"- Premiere journee manquante : `{canonical['first_missing_day']}`.",
        f"- Couverture locale finale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.",
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.",
        "",
        "## Preflight disque reel",
        f"- Volume projet : `{disk['project_mount_path']}` avec `{disk['free_bytes_project_mount']}` bytes libres (`{disk['free_gib_project_mount']}` GiB).",
        f"- Volume data : `{disk['data_mount_path']}` avec `{disk['free_bytes_data_mount']}` bytes libres (`{disk['free_gib_data_mount']}` GiB).",
        f"- Raw actuel : `{disk['raw_bytes_current']}` bytes.",
        f"- Silver actuel : `{disk['silver_bytes_current']}` bytes.",
        f"- Quarantine actuelle : `{disk['quarantine_bytes_current']}` bytes.",
        f"- Safe to continue now : `{disk['safe_to_continue_now']}`.",
        f"- Resume allowed now : `{disk['resume_allowed_now']}`.",
        f"- Warning stockage : `{disk['storage_warning']}`.",
        "",
        "## Reprise",
        f"- Lots planifies/executés/reussis/echoues : `{summary['batches_planned']}` / `{summary['batches_executed']}` / `{summary['batches_complete']}` / `{summary['batches_failed']}`.",
        f"- Jours telecharges/normalises/valides : `{summary['days_downloaded_total']}` / `{summary['days_normalized_total']}` / `{summary['days_complete_total']}`.",
        f"- Jours echoues/quarantine/skips : `{summary['days_failed_total']}` / `{summary['days_quarantined_total']}` / `{summary['days_skipped_existing_total']}`.",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression de donnees, aucun nettoyage destructif.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_27(root: Path, report: dict[str, Any]) -> None:
    summary = report["storage_recheck_summary"]
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_27_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        **summary,
        "disk_preflight": report["disk_preflight"],
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
        "# Synthese courante - V9.27\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Decision V9.27 : `{report['decision']}`.\n"
        f"- Espace libre data : `{report['disk_preflight']['free_gib_data_mount']}` GiB.\n"
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
        f"- Candidate : {VERSION}, reprise aggTrades post-nettoyage stockage.\n"
        f"- Couverture locale : {summary['local_file_coverage_start']} -> {summary['local_file_coverage_end']}.\n"
        f"- Espace libre data mesure : {report['disk_preflight']['free_gib_data_mount']} GiB.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression de donnees, aucun nettoyage destructif, aucun sidecar et aucune empreinte ZIP.\n",
    )


def date_range_v9_27(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    values: list[str] = []
    while current <= stop:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def previous_day_v9_27(value: str | None) -> str | None:
    if value is None:
        return None
    return (date.fromisoformat(value) - timedelta(days=1)).isoformat()


def detect_gaps_v9_27(dates: list[str], complete_set: set[str]) -> list[dict[str, Any]]:
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


def gaps_before_first_missing_v9_27(local: dict[str, Any]) -> list[dict[str, Any]]:
    first_missing = local.get("first_missing_day")
    if first_missing is None:
        return []
    return [gap for gap in local.get("gaps_detected", []) if gap.get("start") < first_missing]


def quarantine_dates_v9_27(root: Path, target_dates: set[str]) -> list[str]:
    base = root / QUARANTINE_DIR
    dates: set[str] = set()
    if base.exists():
        for path in base.glob("date=*"):
            value = path.name.split("=", 1)[-1]
            if value in target_dates:
                dates.add(value)
    return sorted(dates)


def directory_size_bytes_v9_27(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def mount_path_for_v9_27(path: Path) -> str:
    completed = subprocess.run(["df", "-Pk", str(path)], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return str(path)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return str(path)
    return lines[-1].split()[-1]


def batch_to_dict_v9_27(batch: StorageRecheckBatchSpec) -> dict[str, Any]:
    return {
        "batch_id": batch.batch_id,
        "start_date": batch.start_date,
        "end_date": batch.end_date,
        "max_downloads": batch.max_downloads,
        "expected_days": len(date_range_v9_27(batch.start_date, batch.end_date)),
    }


def sum_int_v9_27(items: list[dict[str, Any]], key: str) -> int:
    return sum(int(item.get(key) or 0) for item in items)


def _source_cumulative_int_v9_27(canonical: dict[str, Any], key: str) -> int:
    source = canonical.get("source_report_payload") or {}
    return int(source.get(key) or 0)


def quarantine_failed_raw_v9_27(root: Path, day_value: str, raw_path: Path) -> Path | None:
    if not raw_path.exists():
        return None
    quarantine_dir = root / QUARANTINE_DIR / f"date={day_value}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / raw_path.name
    raw_path.replace(target)
    return target


def build_blockers_v9_27(canonical: dict[str, Any], disk: dict[str, Any], stop_reason: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not canonical["state_reconciled"]:
        blockers.append("Etat local non reconciliable avant reprise.")
    if disk["storage_blocker"] or not disk["resume_allowed_now"]:
        blockers.append("Espace disque insuffisant pour la reprise V9.27 sur le volume data.")
    if stop_reason:
        blockers.append(str(stop_reason))
    return blockers


def build_warnings_v9_27(summary: dict[str, Any], canonical: dict[str, Any], disk: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if canonical["local_coverage_more_advanced_than_v9_26"]:
        warnings.append("La couverture locale est plus avancee que le rapport V9.26.")
    if disk.get("measurement_discrepancy_detected"):
        warnings.append(str(disk.get("measurement_discrepancy_explanation")))
    if disk["storage_warning"]:
        warnings.append(str(disk["storage_warning"]))
    if not summary["complete_collection_reached"]:
        warnings.append("La couverture complete future n'est pas atteinte.")
    return warnings


def run_measurement_command_v9_27(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def statvfs_measurement_v9_27(path: Path) -> dict[str, Any]:
    stat = path.stat()
    statvfs = __import__("os").statvfs(path)
    free_bytes_bavail = statvfs.f_bavail * statvfs.f_frsize
    free_bytes_bfree = statvfs.f_bfree * statvfs.f_frsize
    return {
        "path": str(path),
        "st_dev": stat.st_dev,
        "f_bsize": statvfs.f_bsize,
        "f_frsize": statvfs.f_frsize,
        "f_blocks": statvfs.f_blocks,
        "f_bavail": statvfs.f_bavail,
        "f_bfree": statvfs.f_bfree,
        "free_bytes_bavail": free_bytes_bavail,
        "free_gib_bavail": round(free_bytes_bavail / 1024**3, 3),
        "free_bytes_bfree": free_bytes_bfree,
        "free_gib_bfree": round(free_bytes_bfree / 1024**3, 3),
    }


def parse_df_available_gib_v9_27(stdout: str) -> float | None:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    parts = lines[-1].split()
    if len(parts) < 4:
        return None
    try:
        return float(parts[3])
    except ValueError:
        return None


def extract_first_bytes_before_label_v9_27(text: str, label: str) -> int | None:
    for line in text.splitlines():
        if label in line:
            tail = line.split(label, 1)[-1].strip()
            token = tail.split("B", 1)[0].strip().split()[-1] if " B" not in tail[:30] else tail.split(" B", 1)[0].strip().split()[-1]
            try:
                return int(token)
            except ValueError:
                digits = "".join(ch for ch in tail if ch.isdigit())
                if digits:
                    return int(digits)
    return None


def extract_apfs_notes_v9_27(text: str) -> list[str]:
    notes: list[str] = []
    for line in text.splitlines():
        lowered = line.casefold()
        if "capacity not allocated" in lowered or "capacity in use" in lowered or "purgeable" in lowered:
            notes.append(line.strip())
    return notes


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
