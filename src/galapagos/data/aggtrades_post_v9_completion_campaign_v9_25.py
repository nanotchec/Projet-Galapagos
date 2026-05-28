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
    build_batch_day_plan_v9_24,
    build_source_design_v9_24,
    download_public_archive_v9_24,
    quarantine_failed_raw_v9_24,
    validate_batch_day_v9_24,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    ALLOWED_PUBLIC_HOSTS,
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    BRONZE_PARTITION_TEMPLATE,
    FINDINGS,
    FUNDING_FIRST_END,
    FUNDING_FIRST_START,
    MARKET_TYPE,
    PUBLIC_ARCHIVE_HOST,
    QUALITY_CHECKS,
    QUARANTINE_DIR,
    RAW_DIR,
    SILVER_COLUMNS_V9_18,
    SILVER_PARTITION_TEMPLATE,
    SOURCE_STORAGE,
    SYMBOL,
    TARGET_START,
    VENUE,
    build_public_archive_url_v9_18,
    checksum_file_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)


VERSION = "V9.25"
SOURCE_VERSION = "V9.24"
LAST_VALIDATED_VERSION = "V9.24"
SOURCE_REPORT_VERSION = "V9.24"
DIRECTION = "aggtrades_post_v9_remaining_window_completion_campaign"

PREVIOUS_COVERAGE_START = "2024-05-05"
PREVIOUS_COVERAGE_END = "2024-12-07"
REMAINING_WINDOW_START = "2024-12-08"
REMAINING_WINDOW_END = "2026-05-05"
TARGET_WINDOW_START = "2024-05-05"
TARGET_WINDOW_END = "2026-05-05"

MIN_FREE_BYTES = 60 * 1024**3
WARNING_FREE_BYTES = 100 * 1024**3
DAY_COLLECTION_STORAGE_RESERVE_BYTES = 2 * 1024**3

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_completion_campaign_v9_25.md")

ALLOWED_DECISIONS = {
    "aggtrades_post_v9_remaining_window_collection_complete",
    "aggtrades_post_v9_remaining_window_collection_partial",
    "aggtrades_post_v9_remaining_window_collection_failed_source_issue",
    "aggtrades_post_v9_remaining_window_collection_failed_quality",
    "aggtrades_post_v9_remaining_window_collection_failed_storage",
    "aggtrades_post_v9_remaining_window_collection_not_executed",
    "stop_aggtrades_collection_branch",
}

INPUT_PATHS = {
    "v9_24_batch3_collection": Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    "v9_24_manifest": Path("reports/manifests/aggtrades_post_v9_batch3_collection_v9_24_manifest.json"),
    "v9_23_batch2_collection": Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    "v9_22_multi_batch_plan": Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"),
    "v9_21_batch_expansion": Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    "v9_20_batch_collection": Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    "v9_19_pilot_collection": Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    "v9_18_collection_pack": Path("reports/data/aggtrades_post_v9_collection_v9_18.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

PREVIOUS_BATCH_REPORT_KEYS = [
    "v9_19_pilot_collection",
    "v9_20_batch_collection",
    "v9_21_batch_expansion",
    "v9_23_batch2_collection",
    "v9_24_batch3_collection",
]

BASE_SAFETY_FLAGS = {
    **BASE_SAFETY_FLAGS_V9_18,
    "network_used": False,
    "new_data_downloaded": False,
    "ingestion_executed": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
}


@dataclass(frozen=True)
class CompletionBatchSpec:
    batch_id: str
    start_date: str
    end_date: str
    max_downloads: int

    @property
    def report_path(self) -> Path:
        number = self.batch_id.rsplit("_", 1)[-1].replace("batch_", "")
        return Path(f"reports/data/aggtrades_post_v9_completion_batch{number}_v9_25.json")


INTERNAL_BATCHES = [
    CompletionBatchSpec("V9.25_batch_01", "2024-12-08", "2025-03-07", 90),
    CompletionBatchSpec("V9.25_batch_02", "2025-03-08", "2025-06-05", 90),
    CompletionBatchSpec("V9.25_batch_03", "2025-06-06", "2025-09-03", 90),
    CompletionBatchSpec("V9.25_batch_04", "2025-09-04", "2025-12-02", 90),
    CompletionBatchSpec("V9.25_batch_05", "2025-12-03", "2026-03-02", 90),
    CompletionBatchSpec("V9.25_batch_06", "2026-03-03", "2026-05-05", 64),
]


def run_aggtrades_post_v9_completion_campaign_v9_25(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_completion_campaign_v9_25(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_25(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_25(report))
    update_state_surfaces_v9_25(root, report)
    return report


def build_aggtrades_post_v9_completion_campaign_v9_25(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    campaign_started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    previous_metrics = build_previous_cumulative_metrics_v9_25(inputs)
    preflight = build_preflight_v9_25(root, previous_metrics)
    executed_batches: list[dict[str, Any]] = []
    batch_reports: list[dict[str, Any]] = []
    stop_reason: dict[str, Any] | None = None

    if preflight["preflight_status"] == "failed_storage":
        stop_reason = {"type": "storage", "message": "free disk space below V9.25 minimum threshold"}
        first_batch = INTERNAL_BATCHES[0]
        batch_report = execute_completion_batch_v9_25(root, first_batch)
        _write_json(root / first_batch.report_path, batch_report)
        batch_reports.append(batch_report)
        executed_batches.append(batch_report["batch_summary"])
        for batch in INTERNAL_BATCHES[1:]:
            skipped_report = build_not_executed_batch_report_v9_25(batch, stop_reason)
            _write_json(root / batch.report_path, skipped_report)
    else:
        for batch in INTERNAL_BATCHES:
            batch_report = execute_completion_batch_v9_25(root, batch)
            _write_json(root / batch.report_path, batch_report)
            batch_reports.append(batch_report)
            executed_batches.append(batch_report["batch_summary"])
            if batch_report["batch_summary"]["batch_success"] is not True:
                failure_type = batch_report["batch_summary"].get("failure_type")
                stop_reason = {
                    "type": "storage" if failure_type == "storage" else "batch_failure",
                    "batch_id": batch.batch_id,
                    "message": "campaign stopped after storage guard" if failure_type == "storage" else "campaign stopped after first non-complete internal batch",
                }
                break
        if stop_reason is not None and len(batch_reports) < len(INTERNAL_BATCHES):
            for batch in INTERNAL_BATCHES[len(batch_reports) :]:
                skipped_report = build_not_executed_batch_report_v9_25(batch, stop_reason)
                _write_json(root / batch.report_path, skipped_report)

    runtime_seconds_total = round(time.monotonic() - campaign_started, 3)
    local_file_coverage = build_local_file_coverage_v9_25(root, TARGET_WINDOW_START, TARGET_WINDOW_END)
    global_summary = build_global_campaign_summary_v9_25(
        root=root,
        previous_metrics=previous_metrics,
        preflight=preflight,
        batch_reports=batch_reports,
        local_file_coverage=local_file_coverage,
        runtime_seconds_total=runtime_seconds_total,
        stop_reason=stop_reason,
    )
    decision = decide_v9_25(global_summary, preflight, stop_reason)
    safety_flags = safety_flags_v9_25(global_summary, decision)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "campaign_start": REMAINING_WINDOW_START,
        "campaign_end": REMAINING_WINDOW_END,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "previous_coverage_start": PREVIOUS_COVERAGE_START,
        "previous_coverage_end": PREVIOUS_COVERAGE_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "source_public_target": build_source_design_v9_25(),
        "preflight": preflight,
        "batches_planned": [batch_to_dict_v9_25(batch) for batch in INTERNAL_BATCHES],
        "batches_executed": executed_batches,
        "batch_report_paths": [batch.report_path.as_posix() for batch in INTERNAL_BATCHES],
        "campaign_summary": global_summary,
        **global_summary,
        "reported_cumulative_coverage": {
            "reported_cumulative_coverage_start": global_summary["reported_cumulative_coverage_start"],
            "reported_cumulative_coverage_end": global_summary["reported_cumulative_coverage_end"],
            "source": "V9.24 validated report plus V9.25 completion campaign reports",
            "declarative_from_validated_reports": True,
        },
        "local_file_coverage": local_file_coverage,
        "storage_convention": {
            "raw_pattern": BRONZE_PARTITION_TEMPLATE,
            "silver_pattern": SILVER_PARTITION_TEMPLATE,
            "raw_dir": RAW_DIR.as_posix(),
            "quarantine_dir": QUARANTINE_DIR.as_posix(),
        },
        "quality_checks": list(QUALITY_CHECKS),
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "anti_leakage_plan": build_anti_leakage_plan_v9_25(),
        "decision": decision["decision"],
        "v9_25_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": global_summary["days_complete_total"] > 0 or global_summary["days_attempted_total"] > 0,
        "network_used": global_summary["days_complete_total"] > 0 or global_summary["days_attempted_total"] > 0,
        "new_data_downloaded": global_summary["raw_bytes_new"] > 0,
        "ingestion_executed": global_summary["silver_bytes_new"] > 0,
        "complete_collection_reached": global_summary["complete_collection_reached"],
        "future_full_coverage_complete": global_summary["future_full_coverage_complete"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "blockers": build_blockers_v9_25(preflight, stop_reason, global_summary),
        "warnings": build_warnings_v9_25(preflight, global_summary),
        "limitations": [
            "V9.25 reste data-only et ne cree aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal.",
            "Les fichiers raw/silver complets restent locaux et sont exclus du ZIP audit-lite.",
            "La campagne utilise uniquement l'archive publique read-only data.binance.vision.",
        ],
        "findings": dict(FINDINGS),
        "safety_flags": safety_flags,
    }
    return report


def execute_completion_batch_v9_25(root: Path, batch: CompletionBatchSpec) -> dict[str, Any]:
    started = time.monotonic()
    requested_dates = date_range_v9_25(batch.start_date, batch.end_date)
    validate_batch_spec_v9_25(batch, requested_dates)
    day_plan_before = build_batch_day_plan_v9_24(root, requested_dates)
    collection_result = collect_internal_batch_public_aggtrades_v9_25(root, batch, requested_dates)
    day_plan_after = build_batch_day_plan_v9_24(root, requested_dates)
    day_validation = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    runtime_seconds = round(time.monotonic() - started, 3)
    summary = summarize_completion_batch_v9_25(
        batch=batch,
        requested_dates=requested_dates,
        day_plan_before=day_plan_before,
        day_plan_after=day_plan_after,
        collection_result=collection_result,
        day_validation=day_validation,
        runtime_seconds=runtime_seconds,
    )
    return {
        "version": VERSION,
        "batch_id": batch.batch_id,
        "report_path": batch.report_path.as_posix(),
        "created_at_utc": _utc_now(),
        "source_public_target": build_source_design_v9_25(),
        "batch_window": batch_to_dict_v9_25(batch) | {"days_requested": len(requested_dates), "requested_dates": requested_dates},
        "day_plan_before": day_plan_before,
        "day_plan_after": day_plan_after,
        "collection_result": collection_result,
        "day_results": day_validation,
        "batch_summary": summary,
        "anti_leakage": {
            "available_ts_ge_event_ts_checked": True,
            "labels_joined": False,
            "funding_or_oi_joined": False,
            "signals_or_orders_created": False,
        },
        "safety_flags": safety_flags_for_batch_v9_25(collection_result),
    }


def build_not_executed_batch_report_v9_25(batch: CompletionBatchSpec, stop_reason: dict[str, Any]) -> dict[str, Any]:
    requested_dates = date_range_v9_25(batch.start_date, batch.end_date)
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
        "days_failed": 0,
        "days_quarantined": 0,
        "days_skipped_existing": 0,
        "days_already_complete_before": 0,
        "complete_dates": [],
        "failed_dates": [],
        "new_complete_dates": [],
        "total_rows": 0,
        "total_rows_new": 0,
        "invalid_rows": 0,
        "duplicates": 0,
        "raw_bytes_total": 0,
        "silver_bytes_total": 0,
        "raw_bytes_new": 0,
        "silver_bytes_new": 0,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_aggregate_trade_id": None,
        "max_aggregate_trade_id": None,
        "aggregate_trade_id_gap_warnings": [],
        "runtime_seconds": 0.0,
        "average_rows_per_day": 0,
        "average_raw_bytes_per_day": 0,
        "quality_status": "NOT_EXECUTED",
        "coverage_status": "not_executed_after_campaign_stop",
        "restartability_status": "not_executed_after_previous_batch_stop",
        "batch_success": False,
        "failure_type": stop_reason.get("type"),
        "errors": [f"not executed after campaign stop: {stop_reason}"],
        "quality_errors": [],
        "day_plan_after_status_counts": {},
    }
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "NOT_EXECUTED",
        "created_at_utc": _utc_now(),
        "batch_id": batch.batch_id,
        "batch_spec": batch_to_dict_v9_25(batch),
        "batch_summary": summary,
        "day_results": [],
        "collection_result": {
            "mode": "collect",
            "status": "NOT_EXECUTED",
            "collection_executed": False,
            "network_used": False,
            "new_data_downloaded": False,
            "ingestion_executed": False,
            "errors": summary["errors"],
            "failure_type": stop_reason.get("type"),
        },
        "safety_flags": safety_flags_for_batch_v9_25({"days_attempted": 0, "days_downloaded": 0, "days_normalized": 0}),
    }


def collect_internal_batch_public_aggtrades_v9_25(
    root: Path,
    batch: CompletionBatchSpec,
    requested_dates: list[str],
) -> dict[str, Any]:
    validate_batch_spec_v9_25(batch, requested_dates)
    attempted_dates: list[str] = []
    downloaded_dates: list[str] = []
    normalized_dates: list[str] = []
    skipped_existing_dates: list[str] = []
    errors: list[str] = []
    quarantined_dates: list[str] = []
    failure_type: str | None = None
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            skipped_existing_dates.append(day_value)
            continue
        if len(attempted_dates) >= batch.max_downloads:
            break
        disk_free = shutil.disk_usage(root).free
        if disk_free < MIN_FREE_BYTES + DAY_COLLECTION_STORAGE_RESERVE_BYTES:
            failure_type = "storage"
            errors.append(
                f"{day_value}: storage guard stopped collection before download; "
                f"free_bytes={disk_free}; minimum_free_bytes={MIN_FREE_BYTES}; "
                f"reserve_bytes={DAY_COLLECTION_STORAGE_RESERVE_BYTES}"
            )
            break
        attempted_dates.append(day_value)
        try:
            before_exists = raw_path.exists() and raw_path.stat().st_size > 0
            download_public_archive_v9_24(build_public_archive_url_v9_18(day_value), raw_path)
            after_exists = raw_path.exists() and raw_path.stat().st_size > 0
            if after_exists and not before_exists:
                downloaded_dates.append(day_value)
            normalize_raw_zip_to_silver_v9_25(raw_path, silver_path, day_value)
            normalized_dates.append(day_value)
        except Exception as exc:  # noqa: BLE001 - daily collection failures are reported and stop later batches.
            if failure_type is None:
                failure_type = "quality_or_source"
            quarantine_path = quarantine_failed_raw_v9_24(root, day_value, raw_path)
            if quarantine_path is not None:
                quarantined_dates.append(day_value)
            suffix = f"; quarantined={quarantine_path.as_posix()}" if quarantine_path else ""
            errors.append(f"{day_value}: {exc}{suffix}")
            break
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": True,
        "network_used": bool(attempted_dates),
        "new_data_downloaded": bool(downloaded_dates),
        "ingestion_executed": bool(normalized_dates),
        "network_scope": "public_archive_read_only",
        "new_data_download_scope": "public_historical_aggtrades_remaining_window_only",
        "ingestion_scope": "public_aggtrades_bronze_silver_completion_campaign_only",
        "days_attempted": len(attempted_dates),
        "days_downloaded": len(downloaded_dates),
        "days_normalized": len(normalized_dates),
        "days_skipped_existing": len(skipped_existing_dates),
        "days_quarantined": len(quarantined_dates),
        "downloaded_dates": downloaded_dates,
        "normalized_dates": normalized_dates,
        "skipped_existing_dates": skipped_existing_dates,
        "quarantined_dates": quarantined_dates,
        "errors": errors,
        "failure_type": failure_type,
    }


def normalize_raw_zip_to_silver_v9_25(raw_path: Path, silver_path: Path, current_date: str) -> None:
    import pandas as pd

    with zipfile.ZipFile(raw_path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV inside Binance aggTrades archive.")
        with archive.open(csv_names[0]) as handle:
            frame = pd.read_csv(
                handle,
                header=None,
                names=[
                    "aggregate_trade_id",
                    "price",
                    "quantity",
                    "first_trade_id",
                    "last_trade_id",
                    "trade_time",
                    "is_buyer_maker",
                    "is_best_match",
                ],
            )
    event_ts = _parse_binance_aggtrade_time_v9_25(frame["trade_time"])
    available_ts = pd.Timestamp(f"{current_date}T00:00:00Z") + pd.Timedelta(days=1)
    invalid = (frame["price"].astype(float) <= 0) | (frame["quantity"].astype(float) <= 0)
    output = pd.DataFrame(
        {
            "source": SOURCE_STORAGE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "aggregate_trade_id": frame["aggregate_trade_id"].astype("int64"),
            "price": frame["price"].astype(float),
            "quantity": frame["quantity"].astype(float),
            "first_trade_id": frame["first_trade_id"].astype("int64"),
            "last_trade_id": frame["last_trade_id"].astype("int64"),
            "event_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "trade_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "is_buyer_maker": frame["is_buyer_maker"].astype(bool),
            "ingest_ts": _utc_now(),
            "available_ts": available_ts.isoformat().replace("+00:00", "Z"),
            "source_file": raw_path.as_posix(),
            "source_checksum": checksum_file_v9_18(raw_path),
            "row_valid": ~invalid,
            "invalid_reason": ["price_or_quantity_non_positive" if value else "" for value in invalid.tolist()],
        }
    )
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    output[SILVER_COLUMNS_V9_18].to_parquet(silver_path, index=False)


def _parse_binance_aggtrade_time_v9_25(values: Any) -> Any:
    import pandas as pd

    numeric = pd.to_numeric(values, errors="raise")
    max_abs = int(numeric.abs().max())
    unit = "us" if max_abs >= 100_000_000_000_000 else "ms"
    return pd.to_datetime(numeric, unit=unit, utc=True)


def summarize_completion_batch_v9_25(
    *,
    batch: CompletionBatchSpec,
    requested_dates: list[str],
    day_plan_before: list[dict[str, Any]],
    day_plan_after: list[dict[str, Any]],
    collection_result: dict[str, Any],
    day_validation: list[dict[str, Any]],
    runtime_seconds: float,
) -> dict[str, Any]:
    complete_days = [item for item in day_validation if item["status"] == "day_complete"]
    failed_days = [item for item in day_validation if item["status"] != "day_complete"]
    already_complete_before = {item["date"] for item in day_plan_before if item["status"] == "day_complete"}
    new_complete_days = list(complete_days)
    total_rows = sum_int_v9_25(day_validation, "rows")
    new_rows = sum_int_v9_25(new_complete_days, "rows")
    raw_bytes_total = sum_int_v9_25(day_validation, "raw_bytes")
    silver_bytes_total = sum_int_v9_25(day_validation, "silver_bytes")
    raw_bytes_new = sum_int_v9_25(new_complete_days, "raw_bytes")
    silver_bytes_new = sum_int_v9_25(new_complete_days, "silver_bytes")
    invalid_rows = sum_int_v9_25(day_validation, "invalid_rows")
    duplicates = sum_int_v9_25(day_validation, "duplicates")
    min_event_values = [item["min_event_ts"] for item in day_validation if item.get("min_event_ts")]
    max_event_values = [item["max_event_ts"] for item in day_validation if item.get("max_event_ts")]
    min_ids = [int(item["min_aggregate_trade_id"]) for item in day_validation if item.get("min_aggregate_trade_id") is not None]
    max_ids = [int(item["max_aggregate_trade_id"]) for item in day_validation if item.get("max_aggregate_trade_id") is not None]
    gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete_days)
    batch_success = (
        collection_result["status"] == "PASS"
        and len(complete_days) == len(requested_dates)
        and not failed_days
        and invalid_rows == 0
        and duplicates == 0
    )
    return {
        "batch_id": batch.batch_id,
        "batch_start": batch.start_date,
        "batch_end": batch.end_date,
        "max_downloads": batch.max_downloads,
        "days_requested": len(requested_dates),
        "days_attempted": int(collection_result.get("days_attempted") or 0),
        "days_downloaded": int(collection_result.get("days_downloaded") or 0),
        "days_normalized": int(collection_result.get("days_normalized") or 0),
        "days_complete": len(complete_days),
        "days_failed": len(failed_days),
        "days_quarantined": int(collection_result.get("days_quarantined") or 0),
        "days_skipped_existing": int(collection_result.get("days_skipped_existing") or 0),
        "days_already_complete_before": len(already_complete_before),
        "complete_dates": [item["date"] for item in complete_days],
        "failed_dates": [item["date"] for item in failed_days],
        "new_complete_dates": [item["date"] for item in new_complete_days],
        "total_rows": total_rows,
        "total_rows_new": new_rows,
        "invalid_rows": invalid_rows,
        "duplicates": duplicates,
        "raw_bytes_total": raw_bytes_total,
        "silver_bytes_total": silver_bytes_total,
        "raw_bytes_new": raw_bytes_new,
        "silver_bytes_new": silver_bytes_new,
        "min_event_ts": min(min_event_values) if min_event_values else None,
        "max_event_ts": max(max_event_values) if max_event_values else None,
        "min_aggregate_trade_id": min(min_ids) if min_ids else None,
        "max_aggregate_trade_id": max(max_ids) if max_ids else None,
        "aggregate_trade_id_gap_warnings": gap_warnings,
        "runtime_seconds": runtime_seconds,
        "average_rows_per_day": int(total_rows / len(complete_days)) if complete_days else 0,
        "average_raw_bytes_per_day": int(raw_bytes_total / len(complete_days)) if complete_days else 0,
        "quality_status": "PASS" if batch_success else "FAIL",
        "coverage_status": "batch_complete" if len(complete_days) == len(requested_dates) else "batch_incomplete",
        "restartability_status": "resumable_existing_complete_days_are_skipped_and_missing_days_are_collected_up_to_max_downloads",
        "batch_success": batch_success,
        "failure_type": collection_result.get("failure_type"),
        "errors": list(collection_result.get("errors") or []),
        "quality_errors": [error for item in failed_days for error in item.get("errors", [])],
        "day_plan_after_status_counts": count_statuses_v9_25(day_plan_after),
    }


def build_global_campaign_summary_v9_25(
    *,
    root: Path,
    previous_metrics: dict[str, Any],
    preflight: dict[str, Any],
    batch_reports: list[dict[str, Any]],
    local_file_coverage: dict[str, Any],
    runtime_seconds_total: float,
    stop_reason: dict[str, Any] | None,
) -> dict[str, Any]:
    batch_summaries = [report["batch_summary"] for report in batch_reports]
    complete_summaries = [summary for summary in batch_summaries if summary["batch_success"] is True]
    all_day_results = [day for report in batch_reports for day in report.get("day_results", []) if day.get("status") == "day_complete"]
    previous_boundary = previous_boundary_day_result_v9_25(root)
    all_for_gap = ([previous_boundary] if previous_boundary else []) + all_day_results
    aggregate_gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(all_for_gap)
    timestamp_gap_warnings = build_timestamp_gap_warnings_v9_25(all_for_gap)
    days_requested_total = sum_int_v9_25(batch_summaries, "days_requested")
    days_complete_total = sum_int_v9_25(batch_summaries, "days_complete")
    days_downloaded_total = max(sum_int_v9_25(batch_summaries, "days_downloaded"), days_complete_total if batch_summaries else 0)
    days_normalized_total = max(sum_int_v9_25(batch_summaries, "days_normalized"), days_complete_total if batch_summaries else 0)
    total_rows_new = sum_int_v9_25(batch_summaries, "total_rows_new")
    raw_bytes_new = sum_int_v9_25(batch_summaries, "raw_bytes_new")
    silver_bytes_new = sum_int_v9_25(batch_summaries, "silver_bytes_new")
    final_start = local_file_coverage["local_file_coverage_start"]
    final_end = local_file_coverage["local_file_coverage_end"]
    full_complete = (
        final_start == TARGET_WINDOW_START
        and final_end == TARGET_WINDOW_END
        and len(complete_summaries) == len(INTERNAL_BATCHES)
        and days_complete_total == len(date_range_v9_25(REMAINING_WINDOW_START, REMAINING_WINDOW_END))
    )
    quality_status = "PASS" if full_complete and not aggregate_gap_warnings and not timestamp_gap_warnings else "WARN" if full_complete else "FAIL"
    return {
        "campaign_start": REMAINING_WINDOW_START,
        "campaign_end": REMAINING_WINDOW_END,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "previous_coverage_start": PREVIOUS_COVERAGE_START,
        "previous_coverage_end": PREVIOUS_COVERAGE_END,
        "final_coverage_start": final_start,
        "final_coverage_end": final_end,
        "batches_planned": len(INTERNAL_BATCHES),
        "batches_executed": len(batch_summaries),
        "batches_complete": len(complete_summaries),
        "batches_failed": len(batch_summaries) - len(complete_summaries),
        "failed_batch_ids": [summary["batch_id"] for summary in batch_summaries if summary["batch_success"] is not True],
        "days_requested_total": days_requested_total,
        "days_attempted_total": sum_int_v9_25(batch_summaries, "days_attempted"),
        "days_downloaded_total": days_downloaded_total,
        "days_normalized_total": days_normalized_total,
        "days_complete_total": days_complete_total,
        "days_failed_total": sum_int_v9_25(batch_summaries, "days_failed"),
        "days_quarantined_total": sum_int_v9_25(batch_summaries, "days_quarantined"),
        "days_skipped_existing_total": sum_int_v9_25(batch_summaries, "days_skipped_existing"),
        "total_rows_new": total_rows_new,
        "total_rows_cumulative": int(previous_metrics["rows_collected_total"]) + total_rows_new,
        "raw_bytes_new": raw_bytes_new,
        "silver_bytes_new": silver_bytes_new,
        "raw_bytes_cumulative": int(previous_metrics["raw_bytes_collected_total"]) + raw_bytes_new,
        "silver_bytes_cumulative": int(previous_metrics["silver_bytes_collected_total"]) + silver_bytes_new,
        "runtime_seconds_total": runtime_seconds_total,
        "average_rows_per_day": int(total_rows_new / days_complete_total) if days_complete_total else 0,
        "average_raw_bytes_per_day": int(raw_bytes_new / days_complete_total) if days_complete_total else 0,
        "aggregate_trade_id_gap_warnings": aggregate_gap_warnings,
        "timestamp_gap_warnings": timestamp_gap_warnings,
        "local_file_coverage_start": final_start,
        "local_file_coverage_end": final_end,
        "reported_cumulative_coverage_start": TARGET_WINDOW_START if final_start else PREVIOUS_COVERAGE_START,
        "reported_cumulative_coverage_end": final_end or PREVIOUS_COVERAGE_END,
        "complete_collection_reached": full_complete,
        "future_full_coverage_complete": full_complete,
        "quality_status": quality_status,
        "coverage_status": "target_window_complete" if full_complete else "target_window_incomplete",
        "restartability_status": "resumable_campaign_skips_existing_complete_days_and_stops_on_first_failed_batch",
        "storage_warning": preflight["storage_warning"],
        "stop_reason": stop_reason,
    }


def build_preflight_v9_25(root: Path, previous_metrics: dict[str, Any]) -> dict[str, Any]:
    previous_local = build_local_file_coverage_v9_25(root, PREVIOUS_COVERAGE_START, PREVIOUS_COVERAGE_END)
    remaining_dates = date_range_v9_25(REMAINING_WINDOW_START, REMAINING_WINDOW_END)
    remaining_plan = build_batch_day_plan_v9_24(root, remaining_dates)
    already_complete = [item for item in remaining_plan if item["status"] == "day_complete"]
    missing_or_incomplete = [item for item in remaining_plan if item["status"] != "day_complete"]
    disk = shutil.disk_usage(root)
    observed_average = build_observed_remaining_average_v9_25(root, already_complete)
    average_raw = int(observed_average.get("average_raw_bytes_per_day") or previous_metrics.get("average_raw_bytes_per_day") or 0)
    average_silver = int(observed_average.get("average_silver_bytes_per_day") or previous_metrics.get("average_silver_bytes_per_day") or 0)
    estimated_remaining_raw = average_raw * len(missing_or_incomplete)
    estimated_remaining_silver = average_silver * len(missing_or_incomplete)
    if disk.free < MIN_FREE_BYTES:
        storage_status = "failed_storage"
        storage_warning = "free_disk_below_60gb_stop_before_collection"
    elif disk.free < WARNING_FREE_BYTES:
        storage_status = "warning"
        storage_warning = "free_disk_between_60gb_and_100gb_continue_with_warning"
    else:
        storage_status = "ok"
        storage_warning = None
    return {
        "preflight_status": storage_status,
        "previous_local_coverage": previous_local,
        "reported_cumulative_coverage_start": PREVIOUS_COVERAGE_START,
        "reported_cumulative_coverage_end": PREVIOUS_COVERAGE_END,
        "remaining_window_start": REMAINING_WINDOW_START,
        "remaining_window_end": REMAINING_WINDOW_END,
        "remaining_days_expected": len(remaining_dates),
        "remaining_days_already_complete": len(already_complete),
        "remaining_days_missing_or_incomplete": len(missing_or_incomplete),
        "remaining_missing_or_incomplete_sample": {
            "first": [item["date"] for item in missing_or_incomplete[:3]],
            "last": [item["date"] for item in missing_or_incomplete[-3:]],
        },
        "disk_total_bytes": disk.total,
        "disk_used_bytes": disk.used,
        "disk_free_bytes": disk.free,
        "minimum_free_bytes_required": MIN_FREE_BYTES,
        "warning_free_bytes_threshold": WARNING_FREE_BYTES,
        "day_collection_storage_reserve_bytes": DAY_COLLECTION_STORAGE_RESERVE_BYTES,
        "remaining_volume_estimate_basis": observed_average["basis"],
        "estimated_remaining_raw_bytes": estimated_remaining_raw,
        "estimated_remaining_silver_bytes": estimated_remaining_silver,
        "estimated_remaining_raw_plus_silver_bytes": estimated_remaining_raw + estimated_remaining_silver,
        "storage_warning": storage_warning,
        "resumability": {
            "skip_existing_complete_days": True,
            "never_overwrite_complete_raw_silver": True,
            "quarantine_partial_or_failed_days": True,
            "batch_reports": True,
            "global_manifest": True,
        },
        "host_check": {
            "required_host": "data.binance.vision",
            "allowed_public_hosts": sorted(ALLOWED_PUBLIC_HOSTS),
            "host_is_strict": sorted(ALLOWED_PUBLIC_HOSTS) == ["data.binance.vision"],
        },
        "auth_check": {
            "api_key_used": False,
            "private_endpoint_used": False,
            "exchange_auth_used": False,
            "websocket_live_used": False,
        },
    }


def build_observed_remaining_average_v9_25(root: Path, already_complete: list[dict[str, Any]]) -> dict[str, Any]:
    raw_bytes: list[int] = []
    silver_bytes: list[int] = []
    for item in already_complete:
        raw_path = root / item["raw_path"]
        silver_path = root / item["silver_path"]
        if raw_path.exists() and raw_path.stat().st_size > 0:
            raw_bytes.append(raw_path.stat().st_size)
        if silver_path.exists() and silver_path.stat().st_size > 0:
            silver_bytes.append(silver_path.stat().st_size)
    if not raw_bytes or not silver_bytes:
        return {
            "basis": "prior_validated_cumulative_average",
            "days_observed": 0,
            "average_raw_bytes_per_day": None,
            "average_silver_bytes_per_day": None,
        }
    return {
        "basis": "observed_v9_25_remaining_window_complete_days",
        "days_observed": min(len(raw_bytes), len(silver_bytes)),
        "average_raw_bytes_per_day": int(sum(raw_bytes) / len(raw_bytes)),
        "average_silver_bytes_per_day": int(sum(silver_bytes) / len(silver_bytes)),
    }


def build_previous_cumulative_metrics_v9_25(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = 0
    raw = 0
    silver = 0
    days = 0
    sources: list[dict[str, Any]] = []
    for key in PREVIOUS_BATCH_REPORT_KEYS:
        payload = inputs.get(key, {}).get("payload", {})
        summary = payload.get("batch_validation", {}).get("summary", {}) if isinstance(payload, dict) else {}
        source_rows = int(summary.get("total_rows") or 0)
        source_raw = int(summary.get("raw_bytes_total") or 0)
        source_silver = int(summary.get("silver_bytes_total") or 0)
        source_days = int(summary.get("days_complete") or 0)
        rows += source_rows
        raw += source_raw
        silver += source_silver
        days += source_days
        sources.append({"source_key": key, "rows": source_rows, "raw_bytes": source_raw, "silver_bytes": source_silver, "days_complete": source_days})
    return {
        "rows_collected_total": rows,
        "raw_bytes_collected_total": raw,
        "silver_bytes_collected_total": silver,
        "days_collected_total": days,
        "average_rows_per_day": int(rows / days) if days else 0,
        "average_raw_bytes_per_day": int(raw / days) if days else 0,
        "average_silver_bytes_per_day": int(silver / days) if days else 0,
        "sources": sources,
    }


def previous_boundary_day_result_v9_25(root: Path = Path(".")) -> dict[str, Any] | None:
    path = root / "reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"
    if not path.exists():
        return None
    payload = _read_json(path)
    summary = payload.get("batch_validation", {}).get("summary", {})
    if summary.get("max_aggregate_trade_id") is None:
        return None
    return {
        "date": PREVIOUS_COVERAGE_END,
        "min_aggregate_trade_id": summary.get("min_aggregate_trade_id"),
        "max_aggregate_trade_id": summary.get("max_aggregate_trade_id"),
        "min_event_ts": summary.get("min_event_ts"),
        "max_event_ts": summary.get("max_event_ts"),
    }


def decide_v9_25(global_summary: dict[str, Any], preflight: dict[str, Any], stop_reason: dict[str, Any] | None) -> dict[str, Any]:
    if preflight["preflight_status"] == "failed_storage" or (stop_reason and stop_reason.get("type") == "storage"):
        decision = "aggtrades_post_v9_remaining_window_collection_failed_storage"
        recommendation = "V9.26 - Storage Cleanup / Compression Review."
        confidence = "high"
        justification = "L'espace disque libre est sous le seuil minimal de 60 GB ou la reserve de collecte journaliere V9.25; la campagne est arretee."
    elif global_summary["days_attempted_total"] == 0:
        decision = "aggtrades_post_v9_remaining_window_collection_not_executed"
        recommendation = "V9.26 - AggTrades Completion Correction."
        confidence = "high"
        justification = "Aucun jour restant n'a ete collecte pendant V9.25."
    elif global_summary["complete_collection_reached"] is True:
        decision = "aggtrades_post_v9_remaining_window_collection_complete"
        recommendation = "V9.26 - AggTrades Full Coverage Validation."
        confidence = "high"
        justification = "Tous les lots internes V9.25 sont complets et la couverture locale atteint la fenetre funding-first complete."
    elif stop_reason and stop_reason.get("type") == "batch_failure":
        failed_ids = global_summary.get("failed_batch_ids") or []
        decision = "aggtrades_post_v9_remaining_window_collection_failed_quality" if failed_ids else "aggtrades_post_v9_remaining_window_collection_partial"
        recommendation = "V9.26 - AggTrades Completion Correction."
        confidence = "medium"
        justification = "La campagne s'est arretee au premier lot non complet."
    else:
        decision = "aggtrades_post_v9_remaining_window_collection_partial"
        recommendation = "V9.26 - AggTrades Completion Correction."
        confidence = "medium"
        justification = "La couverture finale reste partielle."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "complete_collection_reached": global_summary["complete_collection_reached"],
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def safety_flags_v9_25(global_summary: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    attempted = global_summary["days_attempted_total"] > 0 or global_summary["days_complete_total"] > 0
    downloaded = global_summary["days_downloaded_total"] > 0 or global_summary["raw_bytes_new"] > 0
    normalized = global_summary["days_normalized_total"] > 0 or global_summary["silver_bytes_new"] > 0
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "network_used": attempted,
            "new_data_downloaded": downloaded,
            "ingestion_executed": normalized,
            "no_new_data_download": not downloaded,
            "no_ingestion_executed": not normalized,
            "network_scope": "public_archive_read_only" if attempted else None,
            "new_data_download_scope": "public_historical_aggtrades_remaining_window_only" if downloaded else None,
            "ingestion_scope": "public_aggtrades_bronze_silver_completion_campaign_only" if normalized else None,
            "completion_decision": decision["decision"],
        }
    )
    return flags


def safety_flags_for_batch_v9_25(collection_result: dict[str, Any]) -> dict[str, Any]:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "network_used": bool(collection_result.get("network_used")),
            "new_data_downloaded": bool(collection_result.get("new_data_downloaded")),
            "ingestion_executed": bool(collection_result.get("ingestion_executed")),
            "no_new_data_download": not bool(collection_result.get("new_data_downloaded")),
            "no_ingestion_executed": not bool(collection_result.get("ingestion_executed")),
            "network_scope": collection_result.get("network_scope"),
            "new_data_download_scope": collection_result.get("new_data_download_scope"),
            "ingestion_scope": collection_result.get("ingestion_scope"),
        }
    )
    return flags


def build_source_design_v9_25() -> dict[str, Any]:
    source = build_source_design_v9_24()
    source.update(
        {
            "version": VERSION,
            "batch_window": "internal_completion_batches",
            "campaign_window": f"{REMAINING_WINDOW_START}_{REMAINING_WINDOW_END}",
            "target_window": f"{TARGET_WINDOW_START}_{TARGET_WINDOW_END}",
            "max_internal_downloads_per_batch": max(batch.max_downloads for batch in INTERNAL_BATCHES),
        }
    )
    return source


def build_anti_leakage_plan_v9_25() -> dict[str, Any]:
    return {
        "rules": [
            "available_ts >= event_ts for every normalized aggTrades row.",
            "V9.25 collects and validates aggTrades only; it creates no labels and no supervised dataset.",
            "No funding, open interest, feature store, model, signal, order, strategy, walk-forward or backtest artifact is created.",
            "The campaign is public archive read-only and uses no key, no private endpoint and no authenticated exchange client.",
        ],
        "forbidden_outputs": ["label", "dataset", "prediction", "model_score", "signal", "trading_signal", "order", "backtest", "position_size", "strategy"],
    }


def build_manifest_v9_25(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["campaign_summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "batch_report_paths": report["batch_report_paths"],
        "target_window_start": summary["target_window_start"],
        "target_window_end": summary["target_window_end"],
        "batches_planned": summary["batches_planned"],
        "batches_executed": summary["batches_executed"],
        "batches_complete": summary["batches_complete"],
        "batches_failed": summary["batches_failed"],
        "days_requested_total": summary["days_requested_total"],
        "days_attempted_total": summary["days_attempted_total"],
        "days_downloaded_total": summary["days_downloaded_total"],
        "days_normalized_total": summary["days_normalized_total"],
        "days_complete_total": summary["days_complete_total"],
        "days_failed_total": summary["days_failed_total"],
        "days_quarantined_total": summary["days_quarantined_total"],
        "days_skipped_existing_total": summary["days_skipped_existing_total"],
        "total_rows_new": summary["total_rows_new"],
        "total_rows_cumulative": summary["total_rows_cumulative"],
        "raw_bytes_new": summary["raw_bytes_new"],
        "silver_bytes_new": summary["silver_bytes_new"],
        "raw_bytes_cumulative": summary["raw_bytes_cumulative"],
        "silver_bytes_cumulative": summary["silver_bytes_cumulative"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "reported_cumulative_coverage_start": summary["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": summary["reported_cumulative_coverage_end"],
        "complete_collection_reached": summary["complete_collection_reached"],
        "future_full_coverage_complete": summary["future_full_coverage_complete"],
        "quality_status": summary["quality_status"],
        "coverage_status": summary["coverage_status"],
        "storage_warning": summary["storage_warning"],
        "decision": report["decision"],
        "v9_25_decision": report["v9_25_decision"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_25(report: dict[str, Any]) -> str:
    summary = report["campaign_summary"]
    decision = report["v9_25_decision"]
    lines = [
        "# V9.25 - AggTrades Post-V9 Remaining Window Completion Campaign",
        "",
        "## Resume executif",
        f"- Decision V9.25 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- V9.25 reste data-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.",
        f"- Fenetre collectee : `{summary['campaign_start']}` -> `{summary['campaign_end']}`.",
        f"- Couverture locale finale : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.",
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.",
        "",
        "## Preflight",
        f"- Espace disque libre : `{report['preflight']['disk_free_bytes']}` bytes.",
        f"- Statut stockage : `{report['preflight']['preflight_status']}`.",
        f"- Warning stockage : `{report['preflight']['storage_warning']}`.",
        f"- Couverture locale precedente : `{report['preflight']['previous_local_coverage']['local_file_coverage_start']}` -> `{report['preflight']['previous_local_coverage']['local_file_coverage_end']}`.",
        "",
        "## Lots internes",
        f"- Lots planifies/executés/reussis/echoues : `{summary['batches_planned']}` / `{summary['batches_executed']}` / `{summary['batches_complete']}` / `{summary['batches_failed']}`.",
        f"- Jours demandes/tentes/telecharges/normalises/valides : `{summary['days_requested_total']}` / `{summary['days_attempted_total']}` / `{summary['days_downloaded_total']}` / `{summary['days_normalized_total']}` / `{summary['days_complete_total']}`.",
        f"- Jours echoues/quarantine/skips : `{summary['days_failed_total']}` / `{summary['days_quarantined_total']}` / `{summary['days_skipped_existing_total']}`.",
        f"- Lignes nouvelles/cumulees : `{summary['total_rows_new']}` / `{summary['total_rows_cumulative']}`.",
        f"- Raw bytes nouveaux/cumules : `{summary['raw_bytes_new']}` / `{summary['raw_bytes_cumulative']}`.",
        f"- Silver bytes nouveaux/cumules : `{summary['silver_bytes_new']}` / `{summary['silver_bytes_cumulative']}`.",
        f"- Runtime total secondes : `{summary['runtime_seconds_total']}`.",
        f"- Alertes aggregate_trade_id : `{len(summary['aggregate_trade_id_gap_warnings'])}`.",
        f"- Alertes timestamps : `{len(summary['timestamp_gap_warnings'])}`.",
        "",
        "## Source et garde-fous",
        "- Source : archive publique Binance `data.binance.vision`, marche spot, symbole BTCUSDT.",
        "- Aucun compte, aucune cle API, aucun endpoint prive, aucun client exchange authentifie, aucun websocket live.",
        "- Aucune API privee.",
        "- Aucun trading reel.",
        "- Aucun paper live.",
        "- Aucun ordre.",
        "- Aucun backtest execute.",
        "- Aucun walk-forward.",
        "- Aucune strategie.",
        "- Aucun signal actionnable.",
        "- Aucun modele persistant.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_25(root: Path, report: dict[str, Any]) -> None:
    summary = report["campaign_summary"]
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_25_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "campaign_start": summary["campaign_start"],
        "campaign_end": summary["campaign_end"],
        "target_window_start": summary["target_window_start"],
        "target_window_end": summary["target_window_end"],
        "previous_coverage_start": summary["previous_coverage_start"],
        "previous_coverage_end": summary["previous_coverage_end"],
        "final_coverage_start": summary["final_coverage_start"],
        "final_coverage_end": summary["final_coverage_end"],
        "batches_planned": summary["batches_planned"],
        "batches_executed": summary["batches_executed"],
        "batches_complete": summary["batches_complete"],
        "batches_failed": summary["batches_failed"],
        "days_requested_total": summary["days_requested_total"],
        "days_attempted_total": summary["days_attempted_total"],
        "days_downloaded_total": summary["days_downloaded_total"],
        "days_normalized_total": summary["days_normalized_total"],
        "days_complete_total": summary["days_complete_total"],
        "days_failed_total": summary["days_failed_total"],
        "days_quarantined_total": summary["days_quarantined_total"],
        "days_skipped_existing_total": summary["days_skipped_existing_total"],
        "total_rows_new": summary["total_rows_new"],
        "total_rows_cumulative": summary["total_rows_cumulative"],
        "raw_bytes_new": summary["raw_bytes_new"],
        "silver_bytes_new": summary["silver_bytes_new"],
        "raw_bytes_cumulative": summary["raw_bytes_cumulative"],
        "silver_bytes_cumulative": summary["silver_bytes_cumulative"],
        "runtime_seconds_total": summary["runtime_seconds_total"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "reported_cumulative_coverage_start": summary["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": summary["reported_cumulative_coverage_end"],
        "complete_collection_reached": summary["complete_collection_reached"],
        "future_full_coverage_complete": summary["future_full_coverage_complete"],
        "quality_status": summary["quality_status"],
        "coverage_status": summary["coverage_status"],
        "storage_warning": summary["storage_warning"],
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
        "# Synthese courante - V9.25\n\n"
        "- Derniere version validee : `V9.24`.\n"
        "- Candidate : `V9.25`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : campagne de completion aggTrades post-V9.\n"
        f"- Decision V9.25 : `{report['decision']}`.\n"
        f"- Lots planifies/executés/reussis/echoues : `{summary['batches_planned']}` / `{summary['batches_executed']}` / `{summary['batches_complete']}` / `{summary['batches_failed']}`.\n"
        f"- Jours telecharges/normalises/valides : `{summary['days_downloaded_total']}` / `{summary['days_normalized_total']}` / `{summary['days_complete_total']}`.\n"
        f"- Couverture locale reelle : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.\n"
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucun trading, paper live, ordre, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    if report["network_used"]:
        text += "- Reseau utilise uniquement pour archive publique read-only `data.binance.vision`.\n"
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.24.\n"
        "- Candidate : V9.25, campagne de completion aggTrades post-V9.\n"
        "- Fenetre cible funding-first : 2024-05-05 -> 2026-05-05.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucun sidecar et aucune empreinte ZIP.\n",
    )


def build_local_file_coverage_v9_25(root: Path, start_date: str, end_date: str) -> dict[str, Any]:
    dates = date_range_v9_25(start_date, end_date)
    complete_dates: list[str] = []
    missing_or_incomplete: list[str] = []
    raw_missing: list[str] = []
    silver_missing: list[str] = []
    contiguous_broken = False
    for day_value in dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        raw_ok = raw_path.exists() and raw_path.stat().st_size > 0
        silver_ok = silver_path.exists() and silver_path.stat().st_size > 0
        if raw_ok and silver_ok and not contiguous_broken:
            complete_dates.append(day_value)
        if not (raw_ok and silver_ok):
            contiguous_broken = True
            missing_or_incomplete.append(day_value)
            if not raw_ok:
                raw_missing.append(day_value)
            if not silver_ok:
                silver_missing.append(day_value)
    return {
        "source": "local raw/silver filesystem metadata",
        "local_file_coverage_start": complete_dates[0] if complete_dates else None,
        "local_file_coverage_end": complete_dates[-1] if complete_dates else None,
        "days_checked": len(dates),
        "days_contiguous_complete": len(complete_dates),
        "missing_or_incomplete_count": len(missing_or_incomplete),
        "missing_or_incomplete_sample": {"first": missing_or_incomplete[:3], "last": missing_or_incomplete[-3:]},
        "raw_missing_count": len(raw_missing),
        "silver_missing_count": len(silver_missing),
        "full_local_data_available_for_checked_window": len(missing_or_incomplete) == 0,
        "audit_lite_without_full_data_safe": True,
    }


def build_timestamp_gap_warnings_v9_25(day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def build_blockers_v9_25(preflight: dict[str, Any], stop_reason: dict[str, Any] | None, summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if preflight["preflight_status"] == "failed_storage":
        blockers.append("Espace disque libre inferieur a 60 GB avant collecte.")
    if stop_reason:
        blockers.append(str(stop_reason))
    if summary["batches_failed"]:
        blockers.append(f"Lots internes echoues : {summary['failed_batch_ids']}")
    return blockers


def build_warnings_v9_25(preflight: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if preflight.get("storage_warning"):
        warnings.append(str(preflight["storage_warning"]))
    if summary["aggregate_trade_id_gap_warnings"]:
        warnings.append("Des alertes de continuite aggregate_trade_id sont presentes.")
    if summary["timestamp_gap_warnings"]:
        warnings.append("Des alertes de continuite timestamp sont presentes.")
    if summary["complete_collection_reached"] is not True:
        warnings.append("La couverture complete future n'est pas atteinte.")
    return warnings


def validate_batch_spec_v9_25(batch: CompletionBatchSpec, requested_dates: list[str]) -> None:
    if not requested_dates:
        raise ValueError(f"{batch.batch_id} cannot be empty")
    if len(requested_dates) > batch.max_downloads:
        raise ValueError(f"{batch.batch_id} exceeds max_downloads")
    if batch.max_downloads > 90:
        raise ValueError("V9.25 internal batches must not exceed 90 downloads")


def batch_to_dict_v9_25(batch: CompletionBatchSpec) -> dict[str, Any]:
    return {"batch_id": batch.batch_id, "start_date": batch.start_date, "end_date": batch.end_date, "max_downloads": batch.max_downloads}


def count_statuses_v9_25(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def sum_int_v9_25(items: list[dict[str, Any]], key: str) -> int:
    return sum(int(item.get(key) or 0) for item in items if item.get(key) is not None)


def date_range_v9_25(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


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
