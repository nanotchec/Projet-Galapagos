from __future__ import annotations

import json
import statistics
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    FINDINGS,
    SILVER_COLUMNS_V9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import TARGET_WINDOW_END, TARGET_WINDOW_START


VERSION = "V9.29"
SOURCE_VERSION = "V9.28"
LAST_VALIDATED_VERSION = "V9.28"
DIRECTION = "aggtrades_post_v9_full_coverage_validation"

TOTAL_DAYS_EXPECTED = 731
TAIL_START = "2026-03-31"
TAIL_END = "2026-05-05"

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_full_coverage_validation_v9_29_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_full_coverage_validation_v9_29.md")

INPUT_PATHS = {
    "v9_28_report": Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json"),
    "v9_28_repair": Path("reports/data/aggtrades_post_v9_bad_day_repair_2026_02_11_v9_28.json"),
    "v9_28_tail": Path("reports/data/aggtrades_post_v9_final_tail_collection_v9_28.json"),
    "v9_28_manifest": Path("reports/manifests/aggtrades_post_v9_bad_day_repair_v9_28_manifest.json"),
    "v9_27_campaign": Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json"),
    "v9_27_batch06": Path("reports/data/aggtrades_post_v9_storage_recheck_batch06_v9_27.json"),
    "v9_25_1_campaign": Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"),
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
    "aggtrades_full_coverage_validated",
    "aggtrades_full_coverage_validated_with_non_blocking_warnings",
    "aggtrades_full_coverage_blocked_by_quarantine",
    "aggtrades_full_coverage_blocked_by_missing_days",
    "aggtrades_full_coverage_blocked_by_quality",
    "aggtrades_full_coverage_inconclusive_manual_review_required",
    "stop_aggtrades_completion_branch",
}

SAFETY_FLAGS_V9_29 = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_ml": True,
    "no_dataset_supervised": True,
    "network_used": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
}


def run_aggtrades_post_v9_full_coverage_validation_v9_29(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_full_coverage_validation_v9_29(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_29(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_29(report))
    update_state_surfaces_v9_29(root, report)
    return report


def build_aggtrades_post_v9_full_coverage_validation_v9_29(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    dates = date_range_v9_29(TARGET_WINDOW_START, TARGET_WINDOW_END)
    day_results = [validate_full_coverage_day_v9_29(root, day_value) for day_value in dates]
    calendar = build_calendar_validation_v9_29(root, day_results)
    quality = build_quality_validation_v9_29(day_results)
    quarantine = reconcile_quarantine_v9_29(root, day_results)
    tail = reconcile_tail_v9_29(inputs, day_results)
    row_outliers = build_row_count_outliers_v9_29(day_results)
    runtime_seconds = round(time.monotonic() - started, 3)
    decision = decide_v9_29(calendar, quality, quarantine, row_outliers)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"].startswith("aggtrades_full_coverage_validated") else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "total_days_expected": TOTAL_DAYS_EXPECTED,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "calendar_validation": calendar,
        "quality_validation": quality,
        "quarantine_reconciliation": quarantine,
        "tail_reconciliation": tail,
        "row_count_outliers": row_outliers,
        "runtime_seconds": runtime_seconds,
        "decision": decision["decision"],
        "v9_29_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS_V9_29),
        "warnings": build_warnings_v9_29(quality, quarantine, tail, row_outliers),
        "blockers": build_blockers_v9_29(calendar, quality, quarantine),
        "limitations": [
            "V9.29 valide la couverture aggTrades localement en lecture seule.",
            "Aucun telechargement, aucune ingestion et aucune reparation de donnees ne sont executes.",
            "Les alertes de volume ou de continuite sont documentees sans devenir bloquantes si les fichiers restent complets et valides.",
        ],
        **flatten_summary_v9_29(calendar, quality, quarantine, tail),
    }
    return report


def validate_full_coverage_day_v9_29(root: Path, day_value: str) -> dict[str, Any]:
    raw_path = root / raw_zip_path_for_date_v9_18(day_value)
    silver_path = root / silver_path_for_date_v9_18(day_value)
    errors: list[str] = []
    raw_errors: list[str] = []
    silver_errors: list[str] = []
    schema_errors: list[str] = []
    raw_bytes = raw_path.stat().st_size if raw_path.exists() else 0
    silver_bytes = silver_path.stat().st_size if silver_path.exists() else 0
    csv_names: list[str] = []
    if not raw_path.exists():
        raw_errors.append("raw_zip_missing")
    elif raw_bytes <= 0:
        raw_errors.append("raw_zip_empty")
    elif not zipfile.is_zipfile(raw_path):
        raw_errors.append("raw_zip_unreadable")
    else:
        try:
            with zipfile.ZipFile(raw_path) as archive:
                csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    raw_errors.append("raw_zip_expected_single_csv")
        except zipfile.BadZipFile:
            raw_errors.append("raw_zip_bad_zip")
    if not silver_path.exists():
        silver_errors.append("silver_parquet_missing")
        return day_result_v9_29(day_value, raw_path, silver_path, raw_bytes, silver_bytes, raw_errors, silver_errors, schema_errors, errors, csv_names)
    if silver_bytes <= 0:
        silver_errors.append("silver_parquet_empty")
        return day_result_v9_29(day_value, raw_path, silver_path, raw_bytes, silver_bytes, raw_errors, silver_errors, schema_errors, errors, csv_names)
    try:
        actual_columns = read_parquet_schema_columns_v9_29(silver_path)
        if actual_columns != list(SILVER_COLUMNS_V9_18):
            schema_errors.append(f"schema_mismatch={actual_columns}")
    except Exception as exc:  # noqa: BLE001
        schema_errors.append(f"schema_read_failed={exc}")
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
        duplicate_count = int(aggregate_trade_id.duplicated().sum())
        invalid_rows = int((frame["row_valid"] != True).sum())  # noqa: E712 - pandas boolean comparison.
        non_positive_price = int((frame["price"].astype(float) <= 0).sum())
        non_positive_quantity = int((frame["quantity"].astype(float) <= 0).sum())
        partition_mismatch = int((event_ts.dt.date.astype(str) != day_value).sum())
        available_ts_violations = int((available_ts < event_ts).sum())
        monotone = bool(aggregate_trade_id.is_monotonic_increasing)
        if rows == 0:
            silver_errors.append("silver_zero_rows")
        if duplicate_count:
            errors.append(f"duplicate_aggregate_trade_id={duplicate_count}")
        if invalid_rows:
            errors.append(f"invalid_rows={invalid_rows}")
        if non_positive_price:
            errors.append(f"price_non_positive={non_positive_price}")
        if non_positive_quantity:
            errors.append(f"quantity_non_positive={non_positive_quantity}")
        if partition_mismatch:
            errors.append(f"partition_event_ts_mismatch={partition_mismatch}")
        if available_ts_violations:
            errors.append(f"available_ts_before_event_ts={available_ts_violations}")
        if not monotone:
            errors.append("aggregate_trade_id_not_monotone")
        result = day_result_v9_29(day_value, raw_path, silver_path, raw_bytes, silver_bytes, raw_errors, silver_errors, schema_errors, errors, csv_names)
        result.update(
            {
                "rows": rows,
                "duplicates": duplicate_count,
                "invalid_rows": invalid_rows,
                "non_positive_price_count": non_positive_price,
                "non_positive_quantity_count": non_positive_quantity,
                "partition_mismatch_count": partition_mismatch,
                "available_ts_violation_count": available_ts_violations,
                "aggregate_trade_id_monotone": monotone,
                "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z") if rows else None,
                "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z") if rows else None,
                "min_aggregate_trade_id": int(aggregate_trade_id.min()) if rows else None,
                "max_aggregate_trade_id": int(aggregate_trade_id.max()) if rows else None,
            }
        )
        result["status"] = "day_complete" if not result["errors"] else "day_failed"
        return result
    except Exception as exc:  # noqa: BLE001
        silver_errors.append(f"silver_read_failed={exc}")
        return day_result_v9_29(day_value, raw_path, silver_path, raw_bytes, silver_bytes, raw_errors, silver_errors, schema_errors, errors, csv_names)


def read_parquet_schema_columns_v9_29(path: Path) -> list[str]:
    try:
        import pyarrow.parquet as pq

        return list(pq.ParquetFile(path).schema.names)
    except ImportError:
        import pandas as pd

        return list(pd.read_parquet(path).columns)


def day_result_v9_29(
    day_value: str,
    raw_path: Path,
    silver_path: Path,
    raw_bytes: int,
    silver_bytes: int,
    raw_errors: list[str],
    silver_errors: list[str],
    schema_errors: list[str],
    quality_errors: list[str],
    csv_names: list[str],
) -> dict[str, Any]:
    all_errors = [*raw_errors, *silver_errors, *schema_errors, *quality_errors]
    return {
        "date": day_value,
        "status": "day_complete" if not all_errors else "day_failed",
        "raw_path": raw_path.as_posix(),
        "silver_path": silver_path.as_posix(),
        "raw_exists": raw_path.exists(),
        "silver_exists": silver_path.exists(),
        "raw_bytes": raw_bytes,
        "silver_bytes": silver_bytes,
        "raw_csv_names": csv_names,
        "rows": 0,
        "duplicates": 0,
        "invalid_rows": 0,
        "non_positive_price_count": 0,
        "non_positive_quantity_count": 0,
        "available_ts_violation_count": 0,
        "partition_mismatch_count": 0,
        "schema_mismatch": bool(schema_errors),
        "aggregate_trade_id_monotone": None,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_aggregate_trade_id": None,
        "max_aggregate_trade_id": None,
        "raw_errors": raw_errors,
        "silver_errors": silver_errors,
        "schema_errors": schema_errors,
        "quality_errors": quality_errors,
        "errors": all_errors,
    }


def build_calendar_validation_v9_29(root: Path, day_results: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    complete_set = {item["date"] for item in complete}
    contiguous: list[str] = []
    for item in day_results:
        if item["date"] not in complete_set:
            break
        contiguous.append(item["date"])
    missing_raw = [item["date"] for item in day_results if not item["raw_exists"] or item["raw_bytes"] <= 0]
    missing_silver = [item["date"] for item in day_results if not item["silver_exists"] or item["silver_bytes"] <= 0]
    failed = [item["date"] for item in day_results if item["status"] != "day_complete"]
    partial = [item["date"] for item in day_results if (item["raw_exists"] or item["silver_exists"]) and item["status"] != "day_complete"]
    missing_days = sorted(set(missing_raw) | set(missing_silver))
    quarantined = quarantine_dates_v9_29(root, {item["date"] for item in day_results})
    return {
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "days_expected": len(day_results),
        "days_with_raw": sum(1 for item in day_results if item["raw_exists"] and item["raw_bytes"] > 0),
        "days_with_silver": sum(1 for item in day_results if item["silver_exists"] and item["silver_bytes"] > 0),
        "days_complete": len(complete),
        "days_missing_raw": len(missing_raw),
        "days_missing_silver": len(missing_silver),
        "days_missing": len(missing_days),
        "days_failed": len(failed),
        "days_partial": len(partial),
        "days_quarantined": len(quarantined),
        "first_missing_or_failed_day": failed[0] if failed else None,
        "last_complete_day": complete[-1]["date"] if complete else None,
        "local_file_coverage_start": complete[0]["date"] if complete else None,
        "local_file_coverage_end": complete[-1]["date"] if complete else None,
        "local_contiguous_clean_coverage_start": contiguous[0] if contiguous else None,
        "local_contiguous_clean_coverage_end": contiguous[-1] if contiguous else None,
        "complete_calendar_coverage": len(complete) == len(day_results) and not failed and not missing_raw and not missing_silver,
        "missing_raw_dates_sample": {"first": missing_raw[:3], "last": missing_raw[-3:]},
        "missing_silver_dates_sample": {"first": missing_silver[:3], "last": missing_silver[-3:]},
        "missing_dates_sample": {"first": missing_days[:3], "last": missing_days[-3:]},
        "failed_dates_sample": {"first": failed[:5], "last": failed[-5:]},
    }


def build_quality_validation_v9_29(day_results: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    aggregate_warnings = build_aggregate_trade_id_gap_warnings_v9_29(complete)
    timestamp_warnings = build_timestamp_gap_warnings_v9_29(complete)
    raw_read_errors = [item for item in day_results if item["raw_errors"]]
    silver_read_errors = [item for item in day_results if item["silver_errors"]]
    schema_mismatches = [item for item in day_results if item["schema_mismatch"]]
    blocking_count = (
        sum_int_v9_29(day_results, "duplicates")
        + sum_int_v9_29(day_results, "invalid_rows")
        + len(schema_mismatches)
        + sum_int_v9_29(day_results, "non_positive_price_count")
        + sum_int_v9_29(day_results, "non_positive_quantity_count")
        + sum_int_v9_29(day_results, "available_ts_violation_count")
        + sum_int_v9_29(day_results, "partition_mismatch_count")
        + len(raw_read_errors)
        + len(silver_read_errors)
    )
    return {
        "global_duplicate_count": sum_int_v9_29(day_results, "duplicates"),
        "global_invalid_rows": sum_int_v9_29(day_results, "invalid_rows"),
        "aggregate_trade_id_gap_warnings": aggregate_warnings,
        "timestamp_gap_warnings": timestamp_warnings,
        "schema_mismatch_count": len(schema_mismatches),
        "non_positive_price_count": sum_int_v9_29(day_results, "non_positive_price_count"),
        "non_positive_quantity_count": sum_int_v9_29(day_results, "non_positive_quantity_count"),
        "available_ts_violation_count": sum_int_v9_29(day_results, "available_ts_violation_count"),
        "partition_mismatch_count": sum_int_v9_29(day_results, "partition_mismatch_count"),
        "raw_read_errors": [{"date": item["date"], "errors": item["raw_errors"]} for item in raw_read_errors[:20]],
        "silver_read_errors": [{"date": item["date"], "errors": item["silver_errors"]} for item in silver_read_errors[:20]],
        "quality_status": "PASS" if blocking_count == 0 else "FAIL",
        "total_rows": sum_int_v9_29(complete, "rows"),
        "raw_bytes_total": sum_int_v9_29(complete, "raw_bytes"),
        "silver_bytes_total": sum_int_v9_29(complete, "silver_bytes"),
        "min_event_ts": min([item["min_event_ts"] for item in complete if item["min_event_ts"]], default=None),
        "max_event_ts": max([item["max_event_ts"] for item in complete if item["max_event_ts"]], default=None),
        "min_aggregate_trade_id": min([int(item["min_aggregate_trade_id"]) for item in complete if item["min_aggregate_trade_id"] is not None], default=None),
        "max_aggregate_trade_id": max([int(item["max_aggregate_trade_id"]) for item in complete if item["max_aggregate_trade_id"] is not None], default=None),
    }


def reconcile_quarantine_v9_29(root: Path, day_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_date = {item["date"]: item for item in day_results}
    quarantine_dates = quarantine_dates_v9_29(root, set(by_date))
    stale: list[str] = []
    active: list[str] = []
    overlap_complete: list[str] = []
    for day_value in quarantine_dates:
        result = by_date.get(day_value)
        if result and result["status"] == "day_complete":
            stale.append(day_value)
            overlap_complete.append(day_value)
        else:
            active.append(day_value)
    return {
        "quarantine_dates": quarantine_dates,
        "quarantine_dates_overlap_complete_days": overlap_complete,
        "quarantine_active_count": len(active),
        "quarantine_stale_count": len(stale),
        "quarantine_blocking": bool(active),
        "active_quarantine_dates": active,
        "stale_quarantine_dates": stale,
        "quarantine_notes": (
            "Les fichiers quarantine sont stale_non_blocking car les jours correspondants sont complets et valides."
            if stale and not active
            else "Aucune quarantine detectee dans la fenetre cible."
            if not quarantine_dates
            else "Au moins une quarantine reste active et bloquante."
        ),
    }


def reconcile_tail_v9_29(inputs: dict[str, dict[str, Any]], day_results: list[dict[str, Any]]) -> dict[str, Any]:
    tail_dates = date_range_v9_29(TAIL_START, TAIL_END)
    by_date = {item["date"]: item for item in day_results}
    tail_results = [by_date[day_value] for day_value in tail_dates]
    tail_report = inputs.get("v9_28_tail", {}).get("payload", {})
    downloaded = int(tail_report.get("days_downloaded") or 0) if isinstance(tail_report, dict) else 0
    skipped = int(tail_report.get("days_skipped_existing") or 0) if isinstance(tail_report, dict) else 0
    validated = sum(1 for item in tail_results if item["status"] == "day_complete")
    return {
        "tail_days_expected": len(tail_dates),
        "tail_days_downloaded_by_v9_28": downloaded,
        "tail_days_skipped_existing_by_v9_28": skipped,
        "tail_days_validated_by_v9_28": int(tail_report.get("days_complete") or 0) if isinstance(tail_report, dict) else 0,
        "tail_days_validated_by_v9_29": validated,
        "tail_coverage_status": "tail_complete" if validated == len(tail_dates) else "tail_incomplete",
        "tail_reporting_acceptable": validated == len(tail_dates) and downloaded + skipped >= len(tail_dates),
        "tail_notes": "La queue finale etait deja presente localement lors du dernier run V9.28; V9.29 confirme qu'elle est lisible et valide.",
    }


def build_row_count_outliers_v9_29(day_results: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    rows = [int(item["rows"]) for item in complete]
    if len(rows) < 2:
        return {"outlier_count": 0, "outliers": [], "method": "insufficient_data"}
    median = statistics.median(rows)
    low = median * 0.2
    high = median * 5.0
    outliers = [
        {"date": item["date"], "rows": int(item["rows"]), "severity": "warning"}
        for item in complete
        if int(item["rows"]) < low or int(item["rows"]) > high
    ]
    return {
        "outlier_count": len(outliers),
        "outliers": outliers[:50],
        "method": "non_blocking_row_count_outlier_scan_threshold_0.2x_to_5x_median",
        "median_rows_per_day": int(median),
    }


def decide_v9_29(
    calendar: dict[str, Any],
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    row_outliers: dict[str, Any],
) -> dict[str, Any]:
    if quarantine["quarantine_blocking"]:
        decision = "aggtrades_full_coverage_blocked_by_quarantine"
        recommendation = "V9.30 - Quarantine Review Pack"
        justification = "Une quarantine active recouvre au moins un jour non complet ou non valide."
    elif not calendar["complete_calendar_coverage"]:
        decision = "aggtrades_full_coverage_blocked_by_missing_days"
        recommendation = "V9.30 - AggTrades Full Coverage Correction"
        justification = "La couverture calendrier complete n'est pas atteinte."
    elif quality["quality_status"] != "PASS":
        decision = "aggtrades_full_coverage_blocked_by_quality"
        recommendation = "V9.30 - AggTrades Full Coverage Correction"
        justification = "La validation globale detecte une anomalie qualite bloquante."
    elif quarantine["quarantine_stale_count"] or quality["aggregate_trade_id_gap_warnings"] or quality["timestamp_gap_warnings"] or row_outliers["outlier_count"]:
        decision = "aggtrades_full_coverage_validated_with_non_blocking_warnings"
        recommendation = "V9.30 - AggTrades 5Y Historical Extension Plan"
        justification = "La couverture et la qualite sont validees; seules des alertes non bloquantes restent documentees."
    else:
        decision = "aggtrades_full_coverage_validated"
        recommendation = "V9.30 - AggTrades 5Y Historical Extension Plan"
        justification = "Tous les jours sont complets, les controles qualite passent et aucune quarantine bloquante n'est active."
    return {
        "decision": decision,
        "confidence": "high",
        "next_recommendation": recommendation,
        "justification": justification,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def flatten_summary_v9_29(
    calendar: dict[str, Any],
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    tail: dict[str, Any],
) -> dict[str, Any]:
    return {
        "days_expected": calendar["days_expected"],
        "days_complete": calendar["days_complete"],
        "days_missing": calendar["days_missing"],
        "days_failed": calendar["days_failed"],
        "days_partial": calendar["days_partial"],
        "days_quarantined": calendar["days_quarantined"],
        "complete_calendar_coverage": calendar["complete_calendar_coverage"],
        "local_file_coverage_start": calendar["local_file_coverage_start"],
        "local_file_coverage_end": calendar["local_file_coverage_end"],
        "local_contiguous_clean_coverage_start": calendar["local_contiguous_clean_coverage_start"],
        "local_contiguous_clean_coverage_end": calendar["local_contiguous_clean_coverage_end"],
        "complete_collection_reached": calendar["complete_calendar_coverage"] and quality["quality_status"] == "PASS" and not quarantine["quarantine_blocking"],
        "future_full_coverage_complete": calendar["complete_calendar_coverage"] and quality["quality_status"] == "PASS" and not quarantine["quarantine_blocking"],
        "global_duplicate_count": quality["global_duplicate_count"],
        "global_invalid_rows": quality["global_invalid_rows"],
        "aggregate_trade_id_gap_warnings": quality["aggregate_trade_id_gap_warnings"],
        "timestamp_gap_warnings": quality["timestamp_gap_warnings"],
        "schema_mismatch_count": quality["schema_mismatch_count"],
        "quality_status": quality["quality_status"],
        "coverage_status": "target_window_validated" if calendar["complete_calendar_coverage"] and quality["quality_status"] == "PASS" and not quarantine["quarantine_blocking"] else "target_window_blocked",
        "total_rows_cumulative": quality["total_rows"],
        "raw_bytes_cumulative": quality["raw_bytes_total"],
        "silver_bytes_cumulative": quality["silver_bytes_total"],
        "quarantine_active_count": quarantine["quarantine_active_count"],
        "quarantine_stale_count": quarantine["quarantine_stale_count"],
        "quarantine_blocking": quarantine["quarantine_blocking"],
        "tail_days_expected": tail["tail_days_expected"],
        "tail_days_downloaded_by_v9_28": tail["tail_days_downloaded_by_v9_28"],
        "tail_days_skipped_existing_by_v9_28": tail["tail_days_skipped_existing_by_v9_28"],
        "tail_days_validated_by_v9_28": tail["tail_days_validated_by_v9_28"],
        "tail_days_validated_by_v9_29": tail["tail_days_validated_by_v9_29"],
        "tail_reporting_acceptable": tail["tail_reporting_acceptable"],
    }


def build_warnings_v9_29(
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    tail: dict[str, Any],
    row_outliers: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if quarantine["quarantine_stale_count"]:
        warnings.append("Des fichiers quarantine stale_non_blocking existent pour des jours complets et valides.")
    if quality["aggregate_trade_id_gap_warnings"]:
        warnings.append("Des alertes de continuite aggregate_trade_id inter-jours sont documentees.")
    if quality["timestamp_gap_warnings"]:
        warnings.append("Des alertes de continuite timestamp inter-jours sont documentees.")
    if row_outliers["outlier_count"]:
        warnings.append("Des outliers de row count sont signales comme non bloquants.")
    if not tail["tail_reporting_acceptable"]:
        warnings.append("La reconciliation de reporting tail V9.28 doit etre revue.")
    return warnings


def build_blockers_v9_29(calendar: dict[str, Any], quality: dict[str, Any], quarantine: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not calendar["complete_calendar_coverage"]:
        blockers.append("Couverture calendrier incomplete.")
    if quality["quality_status"] != "PASS":
        blockers.append("Validation qualite globale en echec.")
    if quarantine["quarantine_blocking"]:
        blockers.append("Quarantine active bloquante.")
    return blockers


def build_manifest_v9_29(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "days_expected": report["days_expected"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "global_duplicate_count": report["global_duplicate_count"],
        "global_invalid_rows": report["global_invalid_rows"],
        "quarantine_active_count": report["quarantine_active_count"],
        "quarantine_stale_count": report["quarantine_stale_count"],
        "tail_reporting_acceptable": report["tail_reporting_acceptable"],
        "complete_collection_reached": report["complete_collection_reached"],
        "future_full_coverage_complete": report["future_full_coverage_complete"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_29(report: dict[str, Any]) -> str:
    lines = [
        "# V9.29 - AggTrades Full Coverage Validation",
        "",
        "## Resume",
        f"- Decision V9.29 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture : `{report['local_file_coverage_start']}` -> `{report['local_file_coverage_end']}`.",
        f"- Jours attendus/complets/manquants/failed : `{report['days_expected']}` / `{report['days_complete']}` / `{report['days_missing']}` / `{report['days_failed']}`.",
        f"- Couverture calendrier complete : `{report['complete_calendar_coverage']}`.",
        f"- Qualite globale : `{report['quality_status']}`.",
        f"- Duplicats globaux : `{report['global_duplicate_count']}`.",
        f"- Lignes invalides globales : `{report['global_invalid_rows']}`.",
        "",
        "## Quarantine",
        f"- Quarantine active/stale/blocking : `{report['quarantine_active_count']}` / `{report['quarantine_stale_count']}` / `{report['quarantine_blocking']}`.",
        f"- Notes : {report['quarantine_reconciliation']['quarantine_notes']}",
        "",
        "## Queue finale V9.28",
        f"- Jours attendus : `{report['tail_days_expected']}`.",
        f"- Telecharges par V9.28 : `{report['tail_days_downloaded_by_v9_28']}`.",
        f"- Skipped existing par V9.28 : `{report['tail_days_skipped_existing_by_v9_28']}`.",
        f"- Valides V9.28/V9.29 : `{report['tail_days_validated_by_v9_28']}` / `{report['tail_days_validated_by_v9_29']}`.",
        f"- Reporting acceptable : `{report['tail_reporting_acceptable']}`.",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun telechargement de nouvelles donnees, aucune ingestion, aucune suppression destructive, aucun push.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_29(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_29_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "days_expected": report["days_expected"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "global_duplicate_count": report["global_duplicate_count"],
        "global_invalid_rows": report["global_invalid_rows"],
        "complete_collection_reached": report["complete_collection_reached"],
        "future_full_coverage_complete": report["future_full_coverage_complete"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "quarantine_active_count": report["quarantine_active_count"],
        "quarantine_stale_count": report["quarantine_stale_count"],
        "tail_reporting_acceptable": report["tail_reporting_acceptable"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "network_scope": None,
        "new_data_downloaded": False,
        "new_data_download_scope": None,
        "ingestion_executed": False,
        "ingestion_scope": None,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.29\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.29 : `{report['decision']}`.\n"
        f"- Couverture validee : `{report['local_file_coverage_start']}` -> `{report['local_file_coverage_end']}`.\n"
        f"- Jours complets/manquants/failed : `{report['days_complete']}` / `{report['days_missing']}` / `{report['days_failed']}`.\n"
        f"- Duplicats/lignes invalides : `{report['global_duplicate_count']}` / `{report['global_invalid_rows']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie ou signal actionnable.\n"
        "- Aucun telechargement, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, validation globale de couverture aggTrades.\n"
        f"- Couverture locale : {report['local_file_coverage_start']} -> {report['local_file_coverage_end']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun telechargement de nouvelles donnees, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n",
    )


def build_aggregate_trade_id_gap_warnings_v9_29(day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        [item for item in day_results if item.get("min_aggregate_trade_id") is not None and item.get("max_aggregate_trade_id") is not None],
        key=lambda item: item["date"],
    )
    warnings: list[dict[str, Any]] = []
    for previous, current in zip(ordered, ordered[1:]):
        expected_next = int(previous["max_aggregate_trade_id"]) + 1
        actual_next = int(current["min_aggregate_trade_id"])
        if actual_next != expected_next:
            warnings.append(
                {
                    "previous_date": previous["date"],
                    "current_date": current["date"],
                    "previous_max_aggregate_trade_id": int(previous["max_aggregate_trade_id"]),
                    "current_min_aggregate_trade_id": actual_next,
                    "expected_next_aggregate_trade_id": expected_next,
                    "gap_size": actual_next - expected_next,
                    "severity": "warning",
                }
            )
    return warnings


def build_timestamp_gap_warnings_v9_29(day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted([item for item in day_results if item.get("date")], key=lambda item: item["date"])
    warnings: list[dict[str, Any]] = []
    for previous, current in zip(ordered, ordered[1:]):
        expected_current = (date.fromisoformat(previous["date"]) + timedelta(days=1)).isoformat()
        if current["date"] != expected_current:
            warnings.append({"previous_date": previous["date"], "current_date": current["date"], "expected_current_date": expected_current, "severity": "warning"})
    return warnings


def quarantine_dates_v9_29(root: Path, target_dates: set[str]) -> list[str]:
    base = root / "data/quarantine/public_trades"
    dates: set[str] = set()
    if base.exists():
        for path in base.rglob("date=*"):
            value = path.name.split("=", 1)[-1]
            if value in target_dates:
                dates.add(value)
    return sorted(dates)


def date_range_v9_29(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def sum_int_v9_29(items: list[dict[str, Any]], key: str) -> int:
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
