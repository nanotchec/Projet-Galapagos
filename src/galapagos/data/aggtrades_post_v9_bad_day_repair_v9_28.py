from __future__ import annotations

import json
import shutil
import time
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24 import (
    build_aggregate_trade_id_gap_warnings_v9_24,
    build_source_design_v9_24,
    download_public_archive_v9_24,
    quarantine_failed_raw_v9_24,
    validate_batch_day_v9_24,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    FINDINGS,
    MARKET_TYPE,
    PUBLIC_ARCHIVE_HOST,
    QUALITY_CHECKS,
    SILVER_COLUMNS_V9_18,
    SOURCE_STORAGE,
    SYMBOL,
    VENUE,
    build_public_archive_url_v9_18,
    checksum_file_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    _parse_binance_aggtrade_time_v9_25,
    normalize_raw_zip_to_silver_v9_25,
)
from galapagos.data.aggtrades_post_v9_storage_recheck_resume_v9_27 import (
    directory_size_bytes_v9_27,
    mount_path_for_v9_27,
)


VERSION = "V9.28"
SOURCE_VERSION = "V9.27"
LAST_VALIDATED_VERSION = "V9.27"
DIRECTION = "aggtrades_post_v9_bad_day_repair_final_completion"

BAD_DAY = "2026-02-11"
BAD_DAY_PREVIOUS = "2026-02-10"
BAD_DAY_NEXT = "2026-02-12"
TAIL_START = "2026-03-31"
TAIL_END = "2026-05-05"
TAIL_MAX_DOWNLOADS = 36
MIN_FREE_BYTES = 60 * 1024**3

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_bad_day_repair_v9_28_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_bad_day_repair_v9_28.md")
REPAIR_JSON_PATH = Path("reports/data/aggtrades_post_v9_bad_day_repair_2026_02_11_v9_28.json")
REPAIR_MD_PATH = Path("reports/data/aggtrades_post_v9_bad_day_repair_2026_02_11_v9_28.md")
TAIL_JSON_PATH = Path("reports/data/aggtrades_post_v9_final_tail_collection_v9_28.json")
TAIL_MD_PATH = Path("reports/data/aggtrades_post_v9_final_tail_collection_v9_28.md")

INPUT_PATHS = {
    "v9_27_campaign": Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json"),
    "v9_27_batch06": Path("reports/data/aggtrades_post_v9_storage_recheck_batch06_v9_27.json"),
    "v9_27_manifest": Path("reports/manifests/aggtrades_post_v9_storage_recheck_resume_v9_27_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "bad_day_repaired_and_remaining_window_completed",
    "bad_day_repaired_remaining_window_partial",
    "bad_day_not_repairable_remaining_window_collected",
    "bad_day_not_repairable_collection_blocked",
    "bad_day_repair_not_needed_report_false_positive",
    "bad_day_redownload_failed_source_issue",
    "bad_day_repair_failed_quality",
    "stop_aggtrades_completion_branch",
}

BASE_SAFETY_FLAGS_V9_28 = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_destructive_cleanup": True,
}


@dataclass(frozen=True)
class TailCollectionSpec:
    batch_id: str
    start_date: str
    end_date: str
    max_downloads: int


def run_aggtrades_post_v9_bad_day_repair_v9_28(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_bad_day_repair_v9_28(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_28(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    if report.get("bad_day_repair_report"):
        _write_json(root / REPAIR_JSON_PATH, report["bad_day_repair_report"])
        _write_text(root / REPAIR_MD_PATH, build_repair_markdown_v9_28(report["bad_day_repair_report"]))
    if report.get("tail_collection_report"):
        _write_json(root / TAIL_JSON_PATH, report["tail_collection_report"])
        _write_text(root / TAIL_MD_PATH, build_tail_markdown_v9_28(report["tail_collection_report"]))
    _write_json(root / MANIFEST_PATH, build_manifest_v9_28(report))
    update_state_surfaces_v9_28(root, report)
    return report


def build_aggtrades_post_v9_bad_day_repair_v9_28(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    disk_preflight = build_disk_snapshot_v9_28(root)
    bad_day_before = validate_batch_day_v9_24(root, BAD_DAY)
    diagnosis = diagnose_bad_day_v9_28(root)
    repair_report = apply_bad_day_repair_v9_28(root, diagnosis) if diagnosis["duplicate_repair_possible"] else build_not_repaired_report_v9_28(diagnosis)
    bad_day_after = validate_batch_day_v9_24(root, BAD_DAY)
    repair_acceptable = bool(repair_report["repair_applied"] and bad_day_after["status"] == "day_complete")
    tail_report = collect_final_tail_v9_28(root) if repair_acceptable or diagnosis["duplicate_repair_possible"] is False else None
    global_validation = validate_global_target_window_v9_28(root)
    runtime_seconds = round(time.monotonic() - started, 3)
    decision = decide_v9_28(repair_report, tail_report, global_validation, diagnosis)
    summary = build_global_summary_v9_28(
        bad_day_before=bad_day_before,
        bad_day_after=bad_day_after,
        repair_report=repair_report,
        tail_report=tail_report,
        global_validation=global_validation,
        runtime_seconds=runtime_seconds,
    )
    safety_flags = safety_flags_v9_28(repair_report, tail_report)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {
            "bad_day_repaired_and_remaining_window_completed",
            "bad_day_repaired_remaining_window_partial",
            "bad_day_not_repairable_remaining_window_collected",
            "bad_day_repair_not_needed_report_false_positive",
        } else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "bad_day": BAD_DAY,
        "final_tail_start": TAIL_START,
        "final_tail_end": TAIL_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "source_public_target": build_source_design_v9_28(),
        "disk_preflight": disk_preflight,
        "bad_day_before": bad_day_before,
        "bad_day_diagnostic": diagnosis,
        "bad_day_repair_report": repair_report,
        "bad_day_after": bad_day_after,
        "tail_collection_report": tail_report,
        "global_validation": global_validation,
        "v9_28_summary": summary,
        **summary,
        "decision": decision["decision"],
        "v9_28_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": bool(repair_report.get("repair_applied") or tail_report),
        "network_used": bool(tail_report and tail_report["days_attempted"] > 0),
        "new_data_downloaded": bool(tail_report and tail_report["days_downloaded"] > 0),
        "ingestion_executed": bool(repair_report.get("repair_applied") or (tail_report and tail_report["days_normalized"] > 0)),
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "quality_checks": list(QUALITY_CHECKS),
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "findings": dict(FINDINGS),
        "safety_flags": safety_flags,
        "blockers": build_blockers_v9_28(repair_report, tail_report, global_validation),
        "warnings": build_warnings_v9_28(diagnosis, repair_report, tail_report, global_validation),
        "limitations": [
            "V9.28 reste data-only et ne cree aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal.",
            "Le raw public original du jour repare n'est pas supprime.",
            "Le ZIP audit-lite exclut les donnees raw/silver completes.",
        ],
    }
    return report


def build_source_design_v9_28() -> dict[str, Any]:
    source = build_source_design_v9_24()
    source.update(
        {
            "version": VERSION,
            "host": PUBLIC_ARCHIVE_HOST,
            "repair_day": BAD_DAY,
            "final_tail_window": f"{TAIL_START}_{TAIL_END}",
            "network_scope": "public_archive_read_only",
            "account_required": False,
            "api_key_required": False,
            "private_endpoint_required": False,
            "exchange_auth_required": False,
            "websocket_live_required": False,
        }
    )
    return source


def diagnose_bad_day_v9_28(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    raw_path = root / raw_zip_path_for_date_v9_18(BAD_DAY)
    silver_path = root / silver_path_for_date_v9_18(BAD_DAY)
    errors: list[str] = []
    raw_readable = raw_path.exists() and raw_path.stat().st_size > 0 and zipfile.is_zipfile(raw_path)
    csv_names: list[str] = []
    frame = None
    if not raw_path.exists():
        errors.append("raw_zip_missing")
    elif raw_path.stat().st_size <= 0:
        errors.append("raw_zip_empty")
    elif not zipfile.is_zipfile(raw_path):
        errors.append("raw_zip_unreadable")
    else:
        try:
            import pandas as pd

            with zipfile.ZipFile(raw_path) as archive:
                csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    errors.append("raw_zip_expected_single_csv")
                else:
                    with archive.open(csv_names[0]) as handle:
                        frame = pd.read_csv(handle, header=None, names=raw_csv_columns_v9_28())
        except Exception as exc:  # noqa: BLE001
            errors.append(f"raw_zip_read_failed={exc}")
    if frame is None:
        return {
            "date": BAD_DAY,
            "raw_path": raw_zip_path_for_date_v9_18(BAD_DAY).as_posix(),
            "silver_path": silver_path_for_date_v9_18(BAD_DAY).as_posix(),
            "raw_zip_readable": raw_readable,
            "csv_internal_unique": len(csv_names) == 1,
            "csv_names": csv_names,
            "duplicate_count": 0,
            "duplicate_exact_count": 0,
            "duplicate_conflict_count": 0,
            "duplicate_conflict_group_count": 0,
            "non_monotone_count": 0,
            "duplicate_repair_possible": False,
            "repair_strategy": "not_repairable_raw_unavailable_or_unreadable",
            "repair_risk": "high",
            "raw_re_download_needed": True,
            "errors": errors,
        }
    import pandas as pd

    id_values = frame["aggregate_trade_id"].astype("int64")
    duplicate_count = int(id_values.duplicated().sum())
    duplicate_exact_count = int(frame.duplicated().sum())
    duplicate_conflict_group_count = 0
    duplicate_conflict_count = 0
    duplicate_ids = frame[id_values.duplicated(keep=False)].groupby("aggregate_trade_id", sort=True)
    for _, group in duplicate_ids:
        unique_rows = group.drop_duplicates()
        if len(unique_rows) > 1:
            duplicate_conflict_group_count += 1
            duplicate_conflict_count += len(group) - 1
    non_monotone_count = int((id_values.diff().dropna() < 0).sum())
    event_ts = _parse_binance_aggtrade_time_v9_25(frame["trade_time"])
    event_dates = pd.Series(event_ts.dt.date.astype(str))
    available_ts = pd.Timestamp(f"{BAD_DAY}T00:00:00Z") + pd.Timedelta(days=1)
    partition_mismatch = int((event_dates != BAD_DAY).sum())
    non_positive_price = int((frame["price"].astype(float) <= 0).sum())
    non_positive_quantity = int((frame["quantity"].astype(float) <= 0).sum())
    availability_violations = int((available_ts < event_ts).sum())
    repaired = frame.drop_duplicates().sort_values("aggregate_trade_id", kind="mergesort").reset_index(drop=True)
    repaired_ids = repaired["aggregate_trade_id"].astype("int64")
    repaired_event_ts = _parse_binance_aggtrade_time_v9_25(repaired["trade_time"])
    repaired_monotone = bool(repaired_ids.is_monotonic_increasing)
    repaired_duplicates = int(repaired_ids.duplicated().sum())
    repaired_timestamp_not_monotone = int((repaired_event_ts.diff().dropna() < pd.Timedelta(0)).sum())
    neighbor_results = [validate_batch_day_v9_24(root, day_value) for day_value in [BAD_DAY_PREVIOUS, BAD_DAY_NEXT]]
    repaired_day_projection = {
        "date": BAD_DAY,
        "min_aggregate_trade_id": int(repaired_ids.min()) if len(repaired_ids) else None,
        "max_aggregate_trade_id": int(repaired_ids.max()) if len(repaired_ids) else None,
        "min_event_ts": repaired_event_ts.min().isoformat().replace("+00:00", "Z") if len(repaired_ids) else None,
        "max_event_ts": repaired_event_ts.max().isoformat().replace("+00:00", "Z") if len(repaired_ids) else None,
    }
    continuity_results = [neighbor_results[0], repaired_day_projection, neighbor_results[1]]
    continuity_warnings = build_aggregate_trade_id_gap_warnings_v9_24(continuity_results)
    continuity_overlap = any(int(item.get("gap_size") or 0) < 0 for item in continuity_warnings)
    repair_possible = (
        raw_readable
        and len(csv_names) == 1
        and duplicate_count > 0
        and duplicate_count == duplicate_exact_count
        and duplicate_conflict_count == 0
        and repaired_monotone
        and repaired_duplicates == 0
        and partition_mismatch == 0
        and non_positive_price == 0
        and non_positive_quantity == 0
        and availability_violations == 0
        and not continuity_overlap
    )
    return {
        "date": BAD_DAY,
        "raw_path": raw_zip_path_for_date_v9_18(BAD_DAY).as_posix(),
        "silver_path": silver_path_for_date_v9_18(BAD_DAY).as_posix(),
        "raw_zip_exists": raw_path.exists(),
        "raw_zip_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
        "raw_zip_readable": raw_readable,
        "csv_internal_unique": len(csv_names) == 1,
        "csv_names": csv_names,
        "rows_raw": int(len(frame)),
        "rows_after_exact_dedup": int(len(repaired)),
        "duplicate_count": duplicate_count,
        "duplicate_exact_count": duplicate_exact_count,
        "duplicate_conflict_count": duplicate_conflict_count,
        "duplicate_conflict_group_count": duplicate_conflict_group_count,
        "non_monotone_count": non_monotone_count,
        "price_non_positive": non_positive_price,
        "quantity_non_positive": non_positive_quantity,
        "partition_event_ts_mismatch": partition_mismatch,
        "available_ts_before_event_ts": availability_violations,
        "repaired_duplicate_count": repaired_duplicates,
        "repaired_aggregate_trade_id_monotone": repaired_monotone,
        "repaired_timestamp_non_monotone_count": repaired_timestamp_not_monotone,
        "min_event_ts_after_repair": repaired_day_projection["min_event_ts"],
        "max_event_ts_after_repair": repaired_day_projection["max_event_ts"],
        "min_aggregate_trade_id_after_repair": repaired_day_projection["min_aggregate_trade_id"],
        "max_aggregate_trade_id_after_repair": repaired_day_projection["max_aggregate_trade_id"],
        "neighbor_day_results": neighbor_results,
        "neighbor_continuity_warnings_after_repair": continuity_warnings,
        "duplicate_repair_possible": repair_possible,
        "repair_strategy": "exact_deduplicate_then_sort_by_aggregate_trade_id" if repair_possible else "not_repairable_without_manual_review",
        "repair_risk": "low" if repair_possible else "high",
        "raw_re_download_needed": False,
        "source_public_file_intrinsically_duplicated": bool(duplicate_count and duplicate_count == duplicate_exact_count and duplicate_conflict_count == 0),
        "errors": errors,
    }


def apply_bad_day_repair_v9_28(root: Path, diagnosis: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    if not diagnosis["duplicate_repair_possible"]:
        return build_not_repaired_report_v9_28(diagnosis)
    import pandas as pd

    raw_path = root / raw_zip_path_for_date_v9_18(BAD_DAY)
    silver_path = root / silver_path_for_date_v9_18(BAD_DAY)
    before_result = validate_batch_day_v9_24(root, BAD_DAY)
    frame = read_raw_aggtrades_frame_v9_28(raw_path)
    deduped = frame.drop_duplicates().sort_values("aggregate_trade_id", kind="mergesort").reset_index(drop=True)
    event_ts = _parse_binance_aggtrade_time_v9_25(deduped["trade_time"])
    available_ts = pd.Timestamp(f"{BAD_DAY}T00:00:00Z") + pd.Timedelta(days=1)
    invalid = (deduped["price"].astype(float) <= 0) | (deduped["quantity"].astype(float) <= 0)
    output = pd.DataFrame(
        {
            "source": SOURCE_STORAGE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "aggregate_trade_id": deduped["aggregate_trade_id"].astype("int64"),
            "price": deduped["price"].astype(float),
            "quantity": deduped["quantity"].astype(float),
            "first_trade_id": deduped["first_trade_id"].astype("int64"),
            "last_trade_id": deduped["last_trade_id"].astype("int64"),
            "event_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "trade_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "is_buyer_maker": deduped["is_buyer_maker"].astype(bool),
            "ingest_ts": _utc_now(),
            "available_ts": available_ts.isoformat().replace("+00:00", "Z"),
            "source_file": raw_path.as_posix(),
            "source_checksum": checksum_file_v9_18(raw_path),
            "row_valid": ~invalid,
            "invalid_reason": ["price_or_quantity_non_positive" if value else "" for value in invalid.tolist()],
        }
    )
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = silver_path.with_name(f"{silver_path.name}.v9_28.tmp")
    output[SILVER_COLUMNS_V9_18].to_parquet(temp_path, index=False)
    temp_path.replace(silver_path)
    after_result = validate_batch_day_v9_24(root, BAD_DAY)
    neighbor_results = [validate_batch_day_v9_24(root, day_value) for day_value in [BAD_DAY_PREVIOUS, BAD_DAY, BAD_DAY_NEXT]]
    repair_quality_pass = after_result["status"] == "day_complete" and int(after_result.get("duplicates") or 0) == 0 and int(after_result.get("invalid_rows") or 0) == 0
    return {
        "version": VERSION,
        "date": BAD_DAY,
        "created_at_utc": _utc_now(),
        "repair_applied": True,
        "repair_strategy": diagnosis["repair_strategy"],
        "repair_risk": diagnosis["repair_risk"],
        "raw_path": raw_zip_path_for_date_v9_18(BAD_DAY).as_posix(),
        "silver_path": silver_path_for_date_v9_18(BAD_DAY).as_posix(),
        "raw_untouched": True,
        "raw_re_download_needed": False,
        "duplicate_count": diagnosis["duplicate_count"],
        "duplicate_exact_count": diagnosis["duplicate_exact_count"],
        "duplicate_conflict_count": diagnosis["duplicate_conflict_count"],
        "rows_before": diagnosis["rows_raw"],
        "rows_after": int(len(output)),
        "rows_removed_as_exact_duplicates": int(diagnosis["rows_raw"] - len(output)),
        "before_result": before_result,
        "after_result": after_result,
        "neighbor_results_after_repair": neighbor_results,
        "aggregate_trade_id_gap_warnings": build_aggregate_trade_id_gap_warnings_v9_24(neighbor_results),
        "quality_status": "PASS" if repair_quality_pass else "FAIL",
        "repair_runtime_seconds": round(time.monotonic() - started, 3),
    }


def build_not_repaired_report_v9_28(diagnosis: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "date": BAD_DAY,
        "created_at_utc": _utc_now(),
        "repair_applied": False,
        "repair_strategy": diagnosis.get("repair_strategy", "not_repairable"),
        "repair_risk": diagnosis.get("repair_risk", "high"),
        "raw_re_download_needed": bool(diagnosis.get("raw_re_download_needed")),
        "duplicate_count": int(diagnosis.get("duplicate_count") or 0),
        "duplicate_exact_count": int(diagnosis.get("duplicate_exact_count") or 0),
        "duplicate_conflict_count": int(diagnosis.get("duplicate_conflict_count") or 0),
        "quality_status": "FAIL",
        "reason": "repair conditions were not met",
    }


def collect_final_tail_v9_28(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    spec = TailCollectionSpec("V9.28_final_tail", TAIL_START, TAIL_END, TAIL_MAX_DOWNLOADS)
    requested_dates = date_range_v9_28(spec.start_date, spec.end_date)
    if len(requested_dates) > spec.max_downloads:
        raise ValueError("V9.28 final tail would exceed max_downloads.")
    started = time.monotonic()
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
        existing = validate_batch_day_v9_24(root, day_value)
        if existing["status"] == "day_complete":
            skipped_existing.append(day_value)
            continue
        if len(attempted) >= spec.max_downloads:
            break
        if shutil.disk_usage(root / "data" if (root / "data").exists() else root).free < MIN_FREE_BYTES:
            failure_type = "storage"
            errors.append(f"{day_value}: storage guard stopped V9.28 final tail before download")
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
            q_path = quarantine_failed_raw_v9_24(root, day_value, raw_path)
            if q_path is not None:
                quarantined.append(day_value)
            errors.append(f"{day_value}: {exc}")
            break
    day_results = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    complete = [item for item in day_results if item["status"] == "day_complete"]
    failed = [item for item in day_results if item["status"] != "day_complete"]
    invalid_rows = sum_int_v9_28(day_results, "invalid_rows")
    duplicates = sum_int_v9_28(day_results, "duplicates")
    batch_success = len(complete) == len(requested_dates) and not failed and invalid_rows == 0 and duplicates == 0 and not errors
    return {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "batch_id": spec.batch_id,
        "start_date": spec.start_date,
        "end_date": spec.end_date,
        "max_downloads": spec.max_downloads,
        "days_requested": len(requested_dates),
        "days_attempted": len(attempted),
        "days_downloaded": len(downloaded),
        "days_normalized": len(normalized),
        "days_complete": len(complete),
        "days_failed": len(failed),
        "days_quarantined": len(quarantined),
        "days_skipped_existing": len(skipped_existing),
        "attempted_dates": attempted,
        "downloaded_dates": downloaded,
        "normalized_dates": normalized,
        "skipped_existing_dates": skipped_existing,
        "quarantined_dates": quarantined,
        "complete_dates": [item["date"] for item in complete],
        "failed_dates": [item["date"] for item in failed],
        "total_rows": sum_int_v9_28(complete, "rows"),
        "raw_bytes_total": sum_int_v9_28(day_results, "raw_bytes"),
        "silver_bytes_total": sum_int_v9_28(day_results, "silver_bytes"),
        "invalid_rows": invalid_rows,
        "duplicates": duplicates,
        "aggregate_trade_id_gap_warnings": build_aggregate_trade_id_gap_warnings_v9_24(complete),
        "day_results": day_results,
        "runtime_seconds": round(time.monotonic() - started, 3),
        "quality_status": "PASS" if batch_success else "FAIL",
        "coverage_status": "final_tail_complete" if len(complete) == len(requested_dates) else "final_tail_incomplete",
        "batch_success": batch_success,
        "failure_type": failure_type,
        "errors": errors,
        "network_scope": "public_archive_read_only" if attempted else None,
        "new_data_download_scope": "public_historical_aggtrades_bad_day_or_final_tail_only" if downloaded else None,
    }


def validate_global_target_window_v9_28(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    dates = date_range_v9_28(TARGET_WINDOW_START, TARGET_WINDOW_END)
    cached = read_cached_complete_global_validation_v9_28(root, len(dates))
    if cached is not None:
        return cached
    day_results = [validate_global_day_fast_v9_28(root, day_value) for day_value in dates]
    complete = [item for item in day_results if item["status"] == "day_complete"]
    failed = [item for item in day_results if item["status"] == "day_failed" and (root / raw_zip_path_for_date_v9_18(item["date"])).exists() and (root / silver_path_for_date_v9_18(item["date"])).exists()]
    missing = [item for item in day_results if item["status"] == "day_failed" and item["date"] not in {failed_item["date"] for failed_item in failed}]
    complete_set = {item["date"] for item in complete}
    contiguous: list[str] = []
    for day_value in dates:
        if day_value not in complete_set:
            break
        contiguous.append(day_value)
    first_missing_or_failed = next((day_value for day_value in dates if day_value not in complete_set), None)
    quarantined_dates = quarantine_dates_v9_28(root, set(dates))
    duplicate_count = sum_int_v9_28(day_results, "duplicates")
    invalid_rows = sum_int_v9_28(day_results, "invalid_rows")
    gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete)
    timestamp_warnings = build_timestamp_gap_warnings_v9_28(complete)
    full_complete = len(complete) == len(dates) and first_missing_or_failed is None and duplicate_count == 0 and invalid_rows == 0
    return {
        "total_days_expected": len(dates),
        "days_complete": len(complete),
        "days_failed": len(failed),
        "days_quarantined": len(quarantined_dates),
        "days_missing": len(dates) - len(complete) - len(failed),
        "first_missing_or_failed_day": first_missing_or_failed,
        "local_file_coverage_start": complete[0]["date"] if complete else None,
        "local_file_coverage_end": complete[-1]["date"] if complete else None,
        "local_contiguous_clean_coverage_start": contiguous[0] if contiguous else None,
        "local_contiguous_clean_coverage_end": contiguous[-1] if contiguous else None,
        "complete_collection_reached": full_complete,
        "future_full_coverage_complete": full_complete,
        "global_duplicate_count": duplicate_count,
        "global_invalid_rows": invalid_rows,
        "aggregate_trade_id_gap_warnings": gap_warnings,
        "timestamp_gap_warnings": timestamp_warnings,
        "quality_status": "PASS" if full_complete and not timestamp_warnings else "FAIL" if not full_complete else "WARN",
        "coverage_status": "target_window_complete" if full_complete else "target_window_incomplete_or_quality_blocked",
        "complete_dates_sample": {"first": [item["date"] for item in complete[:3]], "last": [item["date"] for item in complete[-3:]]},
        "failed_dates": [item["date"] for item in failed],
        "missing_dates_sample": {"first": [item["date"] for item in missing[:3]], "last": [item["date"] for item in missing[-3:]]},
        "quarantined_dates_sample": {"first": quarantined_dates[:3], "last": quarantined_dates[-3:]},
        "total_rows_cumulative": sum_int_v9_28(complete, "rows"),
        "raw_bytes_cumulative": sum_int_v9_28(complete, "raw_bytes"),
        "silver_bytes_cumulative": sum_int_v9_28(complete, "silver_bytes"),
    }


def read_cached_complete_global_validation_v9_28(root: Path, expected_days: int) -> dict[str, Any] | None:
    report_path = root / REPORT_JSON_PATH
    if not report_path.exists():
        return None
    try:
        payload = _read_json(report_path)
    except Exception:  # noqa: BLE001 - cache reuse must be optional.
        return None
    cached = payload.get("global_validation")
    if not isinstance(cached, dict):
        return None
    if cached.get("total_days_expected") != expected_days:
        return None
    if cached.get("complete_collection_reached") is not True:
        return None
    if cached.get("global_duplicate_count") != 0 or cached.get("global_invalid_rows") != 0:
        return None
    cached = dict(cached)
    cached["cache_reused_by_v9_28"] = True
    return cached


def validate_global_day_fast_v9_28(root: Path, day_value: str) -> dict[str, Any]:
    raw_path = root / raw_zip_path_for_date_v9_18(day_value)
    silver_path = root / silver_path_for_date_v9_18(day_value)
    errors: list[str] = []
    raw_bytes = raw_path.stat().st_size if raw_path.exists() else 0
    silver_bytes = silver_path.stat().st_size if silver_path.exists() else 0
    if not raw_path.exists():
        errors.append("raw_zip_missing")
    elif raw_bytes <= 0:
        errors.append("raw_zip_empty")
    elif not zipfile.is_zipfile(raw_path):
        errors.append("raw_zip_unreadable")
    else:
        try:
            with zipfile.ZipFile(raw_path) as archive:
                csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    errors.append("raw_zip_expected_single_csv")
        except zipfile.BadZipFile:
            errors.append("raw_zip_bad_zip")
    if not silver_path.exists():
        errors.append("silver_parquet_missing")
        return global_day_result_v9_28(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)
    try:
        import pandas as pd

        frame = pd.read_parquet(
            silver_path,
            columns=["aggregate_trade_id", "price", "quantity", "event_ts", "available_ts", "row_valid"],
        )
        rows = len(frame)
        aggregate_trade_id = frame["aggregate_trade_id"].astype("int64")
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        available_ts = pd.to_datetime(frame["available_ts"], utc=True)
        duplicates = int(aggregate_trade_id.duplicated().sum())
        invalid_rows = int((frame["row_valid"] != True).sum())  # noqa: E712 - pandas boolean comparison.
        partition_mismatch = int((event_ts.dt.date.astype(str) != day_value).sum())
        non_positive_price = int((frame["price"].astype(float) <= 0).sum())
        non_positive_quantity = int((frame["quantity"].astype(float) <= 0).sum())
        availability_violations = int((available_ts < event_ts).sum())
        if rows == 0:
            errors.append("silver_zero_rows")
        if duplicates:
            errors.append(f"duplicate_aggregate_trade_id={duplicates}")
        if invalid_rows:
            errors.append(f"invalid_rows={invalid_rows}")
        if partition_mismatch:
            errors.append(f"partition_event_ts_mismatch={partition_mismatch}")
        if non_positive_price:
            errors.append(f"price_non_positive={non_positive_price}")
        if non_positive_quantity:
            errors.append(f"quantity_non_positive={non_positive_quantity}")
        if availability_violations:
            errors.append(f"available_ts_before_event_ts={availability_violations}")
        if not bool(aggregate_trade_id.is_monotonic_increasing):
            errors.append("aggregate_trade_id_not_monotone")
        result = global_day_result_v9_28(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)
        result.update(
            {
                "rows": rows,
                "invalid_rows": invalid_rows,
                "duplicates": duplicates,
                "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z") if rows else None,
                "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z") if rows else None,
                "min_aggregate_trade_id": int(aggregate_trade_id.min()) if rows else None,
                "max_aggregate_trade_id": int(aggregate_trade_id.max()) if rows else None,
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001 - validator reports dependency or parquet failures explicitly.
        errors.append(f"silver_fast_read_failed={exc}")
        return global_day_result_v9_28(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)


def global_day_result_v9_28(
    day_value: str,
    raw_path: Path,
    silver_path: Path,
    raw_bytes: int,
    silver_bytes: int,
    errors: list[str],
) -> dict[str, Any]:
    return {
        "date": day_value,
        "status": "day_complete" if not errors else "day_failed",
        "raw_path": raw_path.as_posix(),
        "silver_path": silver_path.as_posix(),
        "raw_bytes": raw_bytes,
        "silver_bytes": silver_bytes,
        "rows": 0,
        "invalid_rows": None,
        "duplicates": None,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_aggregate_trade_id": None,
        "max_aggregate_trade_id": None,
        "errors": errors,
    }


def build_global_summary_v9_28(
    *,
    bad_day_before: dict[str, Any],
    bad_day_after: dict[str, Any],
    repair_report: dict[str, Any],
    tail_report: dict[str, Any] | None,
    global_validation: dict[str, Any],
    runtime_seconds: float,
) -> dict[str, Any]:
    tail = tail_report or {}
    repair_rows = int(repair_report.get("rows_after") or 0) if repair_report.get("repair_applied") else 0
    repair_silver_bytes = int(bad_day_after.get("silver_bytes") or 0) if repair_report.get("repair_applied") else 0
    raw_new = int(tail.get("raw_bytes_total") or 0) if tail.get("batch_success") else sum(
        (Path(".") / raw_zip_path_for_date_v9_18(day_value)).stat().st_size
        for day_value in tail.get("downloaded_dates", [])
        if (Path(".") / raw_zip_path_for_date_v9_18(day_value)).exists()
    )
    return {
        "bad_day": BAD_DAY,
        "duplicate_exact_count": int(repair_report.get("duplicate_exact_count") or 0),
        "duplicate_conflict_count": int(repair_report.get("duplicate_conflict_count") or 0),
        "repair_applied": bool(repair_report.get("repair_applied")),
        "repair_strategy": repair_report.get("repair_strategy"),
        "repair_quality_status": repair_report.get("quality_status"),
        "tail_collection_executed": bool(tail_report),
        "tail_days_requested": int(tail.get("days_requested") or 0),
        "tail_days_attempted": int(tail.get("days_attempted") or 0),
        "tail_days_downloaded": int(tail.get("days_downloaded") or 0),
        "tail_days_normalized": int(tail.get("days_normalized") or 0),
        "tail_days_complete": int(tail.get("days_complete") or 0),
        "tail_days_failed": int(tail.get("days_failed") or 0),
        "days_requested_total": int(tail.get("days_requested") or 0) + 1,
        "days_attempted_total": int(tail.get("days_attempted") or 0),
        "days_downloaded_total": int(tail.get("days_downloaded") or 0),
        "days_normalized_total": int(tail.get("days_normalized") or 0) + (1 if repair_report.get("repair_applied") else 0),
        "days_complete_total": int(tail.get("days_complete") or 0) + (1 if bad_day_after.get("status") == "day_complete" else 0),
        "days_failed_total": int(tail.get("days_failed") or 0) + (0 if bad_day_after.get("status") == "day_complete" else 1),
        "days_quarantined_total": int(tail.get("days_quarantined") or 0),
        "days_skipped_existing_total": int(tail.get("days_skipped_existing") or 0),
        "total_rows_new": repair_rows + int(tail.get("total_rows") or 0),
        "total_rows_cumulative": global_validation["total_rows_cumulative"],
        "raw_bytes_new": raw_new,
        "silver_bytes_new": repair_silver_bytes + int(tail.get("silver_bytes_total") or 0),
        "raw_bytes_cumulative": global_validation["raw_bytes_cumulative"],
        "silver_bytes_cumulative": global_validation["silver_bytes_cumulative"],
        "runtime_seconds_total": runtime_seconds,
        "aggregate_trade_id_gap_warnings": global_validation["aggregate_trade_id_gap_warnings"],
        "timestamp_gap_warnings": global_validation["timestamp_gap_warnings"],
        "local_file_coverage_start": global_validation["local_file_coverage_start"],
        "local_file_coverage_end": global_validation["local_file_coverage_end"],
        "local_contiguous_clean_coverage_start": global_validation["local_contiguous_clean_coverage_start"],
        "local_contiguous_clean_coverage_end": global_validation["local_contiguous_clean_coverage_end"],
        "complete_collection_reached": global_validation["complete_collection_reached"],
        "future_full_coverage_complete": global_validation["future_full_coverage_complete"],
        "quality_status": global_validation["quality_status"],
        "coverage_status": global_validation["coverage_status"],
        "bad_day_before_errors": bad_day_before.get("errors", []),
        "bad_day_after_errors": bad_day_after.get("errors", []),
    }


def decide_v9_28(
    repair_report: dict[str, Any],
    tail_report: dict[str, Any] | None,
    global_validation: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    if global_validation["complete_collection_reached"] and repair_report.get("repair_applied") and tail_report and tail_report.get("batch_success"):
        decision = "bad_day_repaired_and_remaining_window_completed"
        recommendation = "V9.29 - AggTrades Full Coverage Validation"
        justification = "Le jour 2026-02-11 est repare par deduplication exacte et la queue finale est complete."
    elif repair_report.get("repair_applied") and tail_report and not tail_report.get("batch_success"):
        decision = "bad_day_repaired_remaining_window_partial"
        recommendation = "V9.29 - Coverage Gap / Quality Correction"
        justification = "Le mauvais jour est repare mais la queue finale reste partielle."
    elif not repair_report.get("repair_applied") and tail_report and tail_report.get("days_complete", 0) > 0:
        decision = "bad_day_not_repairable_remaining_window_collected"
        recommendation = "V9.29 - AggTrades Bad-Day Manual Review"
        justification = "Le mauvais jour n'est pas reparable automatiquement mais la queue finale a ete collectee."
    elif not repair_report.get("repair_applied") and diagnosis.get("raw_re_download_needed"):
        decision = "bad_day_redownload_failed_source_issue"
        recommendation = "V9.29 - AggTrades Bad-Day Manual Review"
        justification = "Le raw du mauvais jour n'est pas exploitable sans retelechargement ou revue manuelle."
    elif repair_report.get("repair_applied") and global_validation["quality_status"] != "PASS":
        decision = "bad_day_repair_failed_quality"
        recommendation = "V9.29 - Coverage Gap / Quality Correction"
        justification = "La reparation a ete appliquee mais la validation globale reste en echec qualite."
    else:
        decision = "bad_day_not_repairable_collection_blocked"
        recommendation = "V9.29 - AggTrades Bad-Day Manual Review"
        justification = "Les conditions de reparation automatique ne sont pas satisfaites."
    return {
        "decision": decision,
        "confidence": "high" if decision == "bad_day_repaired_and_remaining_window_completed" else "medium",
        "next_recommendation": recommendation,
        "justification": justification,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def safety_flags_v9_28(repair_report: dict[str, Any], tail_report: dict[str, Any] | None) -> dict[str, Any]:
    network_used = bool(tail_report and tail_report.get("days_attempted", 0) > 0)
    downloaded = bool(tail_report and tail_report.get("days_downloaded", 0) > 0)
    ingested = bool(repair_report.get("repair_applied") or (tail_report and tail_report.get("days_normalized", 0) > 0))
    flags = dict(BASE_SAFETY_FLAGS_V9_28)
    flags.update(
        {
            "network_used": network_used,
            "new_data_downloaded": downloaded,
            "ingestion_executed": ingested,
            "no_new_data_download": not downloaded,
            "no_ingestion_executed": not ingested,
            "network_scope": "public_archive_read_only" if network_used else None,
            "new_data_download_scope": "public_historical_aggtrades_bad_day_or_final_tail_only" if downloaded else None,
            "ingestion_scope": "public_aggtrades_bad_day_repair_or_final_tail_only" if ingested else None,
        }
    )
    return flags


def build_disk_snapshot_v9_28(root: Path) -> dict[str, Any]:
    data_root = root / "data"
    project_disk = shutil.disk_usage(root)
    data_disk = shutil.disk_usage(data_root if data_root.exists() else root)
    return {
        "project_mount_path": mount_path_for_v9_27(root),
        "data_mount_path": mount_path_for_v9_27(data_root if data_root.exists() else root),
        "free_bytes_project_mount": project_disk.free,
        "free_gib_project_mount": round(project_disk.free / 1024**3, 3),
        "free_bytes_data_mount": data_disk.free,
        "free_gib_data_mount": round(data_disk.free / 1024**3, 3),
        "raw_bytes_current": directory_size_bytes_v9_27(root / "data/raw"),
        "silver_bytes_current": directory_size_bytes_v9_27(root / "data/silver"),
        "quarantine_bytes_current": directory_size_bytes_v9_27(root / "data/quarantine"),
        "minimum_free_bytes_required_before_tail": MIN_FREE_BYTES,
        "safe_for_tail_collection": data_disk.free >= MIN_FREE_BYTES,
    }


def build_manifest_v9_28(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["v9_28_summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "repair_report_path": REPAIR_JSON_PATH.as_posix() if report.get("bad_day_repair_report") else None,
        "tail_report_path": TAIL_JSON_PATH.as_posix() if report.get("tail_collection_report") else None,
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "bad_day": BAD_DAY,
        "repair_applied": summary["repair_applied"],
        "duplicate_exact_count": summary["duplicate_exact_count"],
        "duplicate_conflict_count": summary["duplicate_conflict_count"],
        "tail_collection_executed": summary["tail_collection_executed"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "local_contiguous_clean_coverage_start": summary["local_contiguous_clean_coverage_start"],
        "local_contiguous_clean_coverage_end": summary["local_contiguous_clean_coverage_end"],
        "complete_collection_reached": summary["complete_collection_reached"],
        "future_full_coverage_complete": summary["future_full_coverage_complete"],
        "quality_status": summary["quality_status"],
        "coverage_status": summary["coverage_status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_28(report: dict[str, Any]) -> str:
    summary = report["v9_28_summary"]
    diagnosis = report["bad_day_diagnostic"]
    return "\n".join(
        [
            "# V9.28 - AggTrades Bad-Day Repair & Final Coverage Completion",
            "",
            "## Resume",
            f"- Decision V9.28 : `{report['decision']}`.",
            f"- Recommandation suivante : `{report['next_recommendation']}`.",
            f"- Jour problematique : `{BAD_DAY}`.",
            f"- Duplicate exact count : `{summary['duplicate_exact_count']}`.",
            f"- Duplicate conflict count : `{summary['duplicate_conflict_count']}`.",
            f"- Reparation appliquee : `{summary['repair_applied']}`.",
            f"- Strategie : `{summary['repair_strategy']}`.",
            f"- Qualite apres reparation : `{summary['repair_quality_status']}`.",
            f"- Queue finale collectee : `{summary['tail_collection_executed']}` (`{TAIL_START}` -> `{TAIL_END}`).",
            f"- Couverture finale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.",
            f"- Couverture propre contigue : `{summary['local_contiguous_clean_coverage_start']}` -> `{summary['local_contiguous_clean_coverage_end']}`.",
            f"- complete_collection_reached : `{summary['complete_collection_reached']}`.",
            f"- future_full_coverage_complete : `{summary['future_full_coverage_complete']}`.",
            "",
            "## Diagnostic 2026-02-11",
            f"- Raw ZIP lisible : `{diagnosis['raw_zip_readable']}`.",
            f"- CSV interne unique : `{diagnosis['csv_internal_unique']}`.",
            f"- Duplicats exacts : `{diagnosis['duplicate_exact_count']}`.",
            f"- Duplicats conflictuels : `{diagnosis['duplicate_conflict_count']}`.",
            f"- Non-monotonicite initiale : `{diagnosis['non_monotone_count']}`.",
            f"- Reparation possible : `{diagnosis['duplicate_repair_possible']}`.",
            f"- Source publique intrinsequement dupliquee : `{diagnosis['source_public_file_intrinsically_duplicated']}`.",
            "",
            "## Validation globale",
            f"- Jours attendus : `{report['global_validation']['total_days_expected']}`.",
            f"- Jours complets : `{report['global_validation']['days_complete']}`.",
            f"- Jours failed/missing/quarantine : `{report['global_validation']['days_failed']}` / `{report['global_validation']['days_missing']}` / `{report['global_validation']['days_quarantined']}`.",
            f"- Premier jour manquant ou failed : `{report['global_validation']['first_missing_or_failed_day']}`.",
            f"- Duplicats globaux : `{report['global_validation']['global_duplicate_count']}`.",
            f"- Lignes invalides globales : `{report['global_validation']['global_invalid_rows']}`.",
            "",
            "## Garde-fous",
            "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.",
            "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
            "- Aucun client exchange authentifie, aucun websocket live, aucune suppression destructive, aucun push.",
            "- Aucun sidecar et aucune empreinte ZIP.",
        ]
    ) + "\n"


def build_repair_markdown_v9_28(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Reparation 2026-02-11 - V9.28",
            "",
            f"- Reparation appliquee : `{report['repair_applied']}`.",
            f"- Strategie : `{report['repair_strategy']}`.",
            f"- Risque : `{report['repair_risk']}`.",
            f"- Duplicats exacts retires : `{report.get('rows_removed_as_exact_duplicates', 0)}`.",
            f"- Qualite apres reparation : `{report['quality_status']}`.",
            "- Raw original conserve, silver regenere avec manifest et rapport.",
        ]
    ) + "\n"


def build_tail_markdown_v9_28(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Collecte queue finale - V9.28",
            "",
            f"- Fenetre : `{report['start_date']}` -> `{report['end_date']}`.",
            f"- Jours demandes/tentes/telecharges/normalises/complets : `{report['days_requested']}` / `{report['days_attempted']}` / `{report['days_downloaded']}` / `{report['days_normalized']}` / `{report['days_complete']}`.",
            f"- Jours failed/quarantine/skipped : `{report['days_failed']}` / `{report['days_quarantined']}` / `{report['days_skipped_existing']}`.",
            f"- Lignes : `{report['total_rows']}`.",
            f"- Raw bytes total : `{report['raw_bytes_total']}`.",
            f"- Silver bytes total : `{report['silver_bytes_total']}`.",
            f"- Qualite : `{report['quality_status']}`.",
        ]
    ) + "\n"


def update_state_surfaces_v9_28(root: Path, report: dict[str, Any]) -> None:
    summary = report["v9_28_summary"]
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_28_decision": report["decision"],
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
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    for stale_key in ["recommended_next_version", "recommended_next_action"]:
        state.pop(stale_key, None)
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.28\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.28 : `{report['decision']}`.\n"
        f"- Jour repare : `{BAD_DAY}`, reparation appliquee `{summary['repair_applied']}`.\n"
        f"- Couverture locale finale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.\n"
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie ou signal actionnable.\n"
        "- Aucun modele persistant, API privee, cle API, suppression destructive, sidecar ou empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, reparation mauvais jour aggTrades et completion finale.\n"
        f"- Couverture locale : {summary['local_file_coverage_start']} -> {summary['local_file_coverage_end']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n",
    )


def read_raw_aggtrades_frame_v9_28(raw_path: Path) -> Any:
    import pandas as pd

    with zipfile.ZipFile(raw_path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV inside Binance aggTrades archive.")
        with archive.open(csv_names[0]) as handle:
            return pd.read_csv(handle, header=None, names=raw_csv_columns_v9_28())


def raw_csv_columns_v9_28() -> list[str]:
    return [
        "aggregate_trade_id",
        "price",
        "quantity",
        "first_trade_id",
        "last_trade_id",
        "trade_time",
        "is_buyer_maker",
        "is_best_match",
    ]


def build_timestamp_gap_warnings_v9_28(day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted([item for item in day_results if item.get("date")], key=lambda item: item["date"])
    warnings: list[dict[str, Any]] = []
    for previous, current in zip(ordered, ordered[1:]):
        previous_date = date.fromisoformat(previous["date"])
        current_date = date.fromisoformat(current["date"])
        if current_date != previous_date + timedelta(days=1):
            warnings.append(
                {
                    "previous_date": previous["date"],
                    "current_date": current["date"],
                    "expected_current_date": (previous_date + timedelta(days=1)).isoformat(),
                    "severity": "warning",
                }
            )
    return warnings


def quarantine_dates_v9_28(root: Path, target_dates: set[str]) -> list[str]:
    base = root / "data/quarantine/public_trades"
    dates: set[str] = set()
    if base.exists():
        for path in base.rglob("date=*"):
            value = path.name.split("=", 1)[-1]
            if value in target_dates:
                dates.add(value)
    return sorted(dates)


def build_blockers_v9_28(repair_report: dict[str, Any], tail_report: dict[str, Any] | None, global_validation: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not repair_report.get("repair_applied"):
        blockers.append("Le jour 2026-02-11 n'a pas ete repare automatiquement.")
    if tail_report and not tail_report.get("batch_success"):
        blockers.extend(tail_report.get("errors", []))
    if not global_validation["complete_collection_reached"]:
        blockers.append("La fenetre cible complete n'est pas proprement atteinte.")
    return blockers


def build_warnings_v9_28(
    diagnosis: dict[str, Any],
    repair_report: dict[str, Any],
    tail_report: dict[str, Any] | None,
    global_validation: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if diagnosis.get("source_public_file_intrinsically_duplicated"):
        warnings.append("Le raw public source 2026-02-11 contient des doublons exacts.")
    if repair_report.get("aggregate_trade_id_gap_warnings"):
        warnings.append("Des alertes de continuite aggregate_trade_id existent autour du jour repare.")
    if tail_report and tail_report.get("aggregate_trade_id_gap_warnings"):
        warnings.append("Des alertes de continuite aggregate_trade_id existent dans la queue finale.")
    if global_validation.get("timestamp_gap_warnings"):
        warnings.append("Des alertes de continuite timestamp existent dans la validation globale.")
    return warnings


def date_range_v9_28(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def sum_int_v9_28(items: list[dict[str, Any]], key: str) -> int:
    return sum(int(item.get(key) or 0) for item in items if item.get(key) is not None)


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    if path.suffix == ".json":
        payload: Any = _read_json(full)
    else:
        payload = {"text": full.read_text(encoding="utf-8")}
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
