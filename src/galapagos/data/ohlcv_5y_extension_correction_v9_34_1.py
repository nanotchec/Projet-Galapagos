from __future__ import annotations

import json
import shutil
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from galapagos.data.ohlcv_5y_extension_v9_34 import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    FINDINGS,
    HOST,
    MARKET_TYPE,
    MISSING_WINDOW_END,
    MISSING_WINDOW_START,
    SAFETY_FLAGS,
    SILVER_COLUMNS,
    SYMBOL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAME_DELTAS,
    TIMEFRAMES,
    VENUE,
    DayResult,
    build_derivation_plan_v9_34,
    build_ohlcv_diagnostic_v9_34,
    build_ohlcv_quality_summary_v9_34,
    date_range_v9_34,
    discover_research_windows_v9_34,
    discover_silver_ohlcv_dates_v9_34,
    measure_disk_v9_34,
    normalize_klines_for_v9_34,
    raw_kline_path_v9_34,
    silver_ohlcv_path_v9_34,
    summarize_day_results_v9_34,
    validate_ohlcv_frame_v9_34,
    validate_raw_zip_v9_34,
    validate_silver_day_v9_34,
)
from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    download_public_archive,
    parse_binance_kline_zip,
)
from galapagos.data.public_market.storage import write_parquet


VERSION = "V9.34.1"
SOURCE_VERSION = "V9.34"
LAST_VALIDATED_VERSION = "V9.33"
DIRECTION = "ohlcv_5y_extension_correction"
BAD_DAY = "2021-08-13"
BAD_TIMEFRAME = "1m"

REPORT_JSON_PATH = Path("reports/data/ohlcv_5y_extension_correction_v9_34_1.json")
REPORT_MD_PATH = Path("reports/data/ohlcv_5y_extension_correction_v9_34_1.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_5y_extension_correction_v9_34_1_manifest.json")
DOC_PATH = Path("docs/ohlcv_5y_extension_correction_v9_34_1.md")
BAD_DAY_REPORT_PATH = Path("reports/data/ohlcv_5y_bad_day_2021_08_13_v9_34_1.json")

INPUT_PATHS = {
    "v9_34_report": Path("reports/data/ohlcv_5y_extension_v9_34.json"),
    "v9_34_manifest": Path("reports/manifests/ohlcv_5y_extension_v9_34_manifest.json"),
    "v9_33_report": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json"),
    "v9_33_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_33_manifest.json"),
    "v9_32_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
}

ALLOWED_DECISIONS = {
    "ohlcv_5y_extension_complete",
    "ohlcv_5y_extension_partial",
    "ohlcv_5y_extension_failed_source_issue",
    "ohlcv_5y_extension_failed_quality",
    "ohlcv_5y_extension_failed_storage",
    "ohlcv_from_aggtrades_derivation_plan_required",
    "ohlcv_5y_extension_not_executed_manual_review",
    "stop_ohlcv_5y_extension_branch",
}

Downloader = Callable[[str, Path], None]


def run_ohlcv_5y_extension_correction_v9_34_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_and_run_correction_v9_34_1(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_34_1(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_34_1(report))
    _write_json(root / BAD_DAY_REPORT_PATH, report["bad_day_diagnostic"])
    for timeframe_report in report["timeframe_reports"]:
        _write_json(root / f"reports/data/ohlcv_5y_extension_correction_{timeframe_report['timeframe']}_v9_34_1.json", timeframe_report)
    update_state_surfaces_v9_34_1(root, report)
    return report


def build_and_run_correction_v9_34_1(root: Path, downloader: Downloader | None = None) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    diagnostic_before = build_ohlcv_diagnostic_v9_34(root, inputs)
    disk = measure_disk_v9_34(root)
    bad_day_before = diagnose_bad_day_v9_34_1(root)
    repair = repair_bad_day_if_needed_v9_34_1(root, bad_day_before, downloader=downloader)
    bad_day_after = diagnose_bad_day_v9_34_1(root)
    day_results: list[DayResult] = []
    source_error_detected = False
    quality_error_detected = False
    storage_error_detected = False
    if disk["free_gib_data_mount"] < 5.0:
        storage_error_detected = True
    elif repair["repair_status"] in {"source_issue", "repair_failed_quality"}:
        source_error_detected = repair["repair_status"] == "source_issue"
        quality_error_detected = repair["repair_status"] == "repair_failed_quality"
    else:
        day_results, source_error_detected, quality_error_detected, storage_error_detected = resume_missing_ohlcv_v9_34_1(root, downloader=downloader)
    diagnostic_after = build_ohlcv_diagnostic_v9_34(root, inputs)
    totals = summarize_day_results_v9_34(day_results)
    timeframe_reports = build_timeframe_reports_v9_34_1(day_results, diagnostic_after)
    decision = decide_v9_34_1(
        diagnostic_after=diagnostic_after,
        totals=totals,
        storage_error_detected=storage_error_detected,
        source_error_detected=source_error_detected,
        quality_error_detected=quality_error_detected,
    )
    runtime_seconds = round(time.monotonic() - started, 3)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {"ohlcv_5y_extension_complete", "ohlcv_5y_extension_partial", "ohlcv_from_aggtrades_derivation_plan_required"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "missing_window_start": MISSING_WINDOW_START,
        "missing_window_end": MISSING_WINDOW_END,
        "timeframes_required": list(TIMEFRAMES),
        "source": {
            "name": "Binance public archive",
            "host": HOST,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "data_type": "klines",
            "public_read_only": True,
            "authentication_used": False,
        },
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "disk_preflight": disk,
        "diagnostic_before": diagnostic_before,
        "diagnostic_after": diagnostic_after,
        "bad_day_diagnostic": {
            "before": bad_day_before,
            "repair": repair,
            "after": bad_day_after,
        },
        "redownload_attempted": repair["redownload_attempted"],
        "redownload_success": repair["redownload_success"],
        "redownload_raw_size_bytes": repair["redownload_raw_size_bytes"],
        "redownload_row_count": repair["redownload_row_count"],
        "redownload_quality_status": repair["redownload_quality_status"],
        "raw_replaced_or_backup_strategy": repair["raw_replaced_or_backup_strategy"],
        "silver_rebuilt_for_2021_08_13": repair["silver_rebuilt_for_2021_08_13"],
        "repair_status": repair["repair_status"],
        "collection_executed": bool(day_results),
        "timeframes_treated": sorted({result.timeframe for result in day_results}),
        "timeframe_reports": timeframe_reports,
        **totals,
        "ohlcv_quality": build_ohlcv_quality_summary_v9_34(diagnostic_after, totals),
        "ohlcv_5y_ready": diagnostic_after["ohlcv_5y_ready"],
        "derive_ohlcv_from_aggtrades_possible": True,
        "derive_ohlcv_from_aggtrades_recommended": source_error_detected,
        "derivation_plan": build_derivation_plan_v9_34(),
        "decision": decision["decision"],
        "v9_34_1_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "runtime_seconds": runtime_seconds,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "feature_store_created": False,
        "combined_feature_store_created": False,
        "network_used": repair["network_used"] or totals["network_used"],
        "network_scope": "public_archive_read_only" if repair["network_used"] or totals["network_used"] else "not_used",
        "new_data_downloaded": repair["redownload_success"] or totals["days_downloaded_total"] > 0,
        "new_data_download_scope": "public_historical_ohlcv_klines_5y_extension_correction_only" if repair["redownload_success"] or totals["days_downloaded_total"] > 0 else "none",
        "ingestion_executed": repair["silver_rebuilt_for_2021_08_13"] or totals["days_normalized_total"] > 0,
        "ingestion_scope": "public_ohlcv_bronze_silver_5y_extension_correction_only" if repair["silver_rebuilt_for_2021_08_13"] or totals["days_normalized_total"] > 0 else "none",
        "findings": dict(FINDINGS),
        "safety_flags": build_safety_flags_v9_34_1(repair, totals),
        "warnings": build_warnings_v9_34_1(diagnostic_after, repair, totals, source_error_detected),
        "blockers": build_blockers_v9_34_1(diagnostic_after, repair, storage_error_detected, source_error_detected, quality_error_detected),
        "limitations": [
            "V9.34.1 corrige uniquement l'extension OHLCV 5Y et ne cree pas le feature store combine.",
            "Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre n'est produit.",
        ],
    }
    return report


def diagnose_bad_day_v9_34_1(root: Path) -> dict[str, Any]:
    raw_path = raw_kline_path_v9_34(root, BAD_TIMEFRAME, BAD_DAY)
    result: dict[str, Any] = {
        "timeframe": BAD_TIMEFRAME,
        "date": BAD_DAY,
        "raw_path": raw_path.as_posix(),
        "raw_exists": raw_path.exists(),
        "raw_size_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
        "zip_readable": False,
        "csv_member_count": 0,
        "row_count": 0,
        "expected_row_count": EXPECTED_ROWS_BY_TIMEFRAME[BAD_TIMEFRAME],
        "min_open_ts": None,
        "max_open_ts": None,
        "duplicate_open_time_count": 0,
        "timestamp_gap_count": 0,
        "missing_intervals": [],
        "price_invariant_violations": 0,
        "non_positive_price_count": 0,
        "negative_volume_count": 0,
        "partition_mismatch_count": 0,
        "local_raw_quality_status": "MISSING",
        "local_raw_incomplete_or_invalid": True,
        "errors": [],
    }
    if not raw_path.exists():
        result["errors"].append("raw_missing")
        return result
    try:
        with zipfile.ZipFile(raw_path) as archive:
            csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
            result["csv_member_count"] = len(csv_names)
            result["zip_readable"] = archive.testzip() is None
    except zipfile.BadZipFile:
        result["errors"].append("zip_not_readable")
        return result
    try:
        frame = parse_binance_kline_zip(raw_path)
        raw_quality = diagnose_kline_frame_v9_34_1(frame, timeframe=BAD_TIMEFRAME, day=BAD_DAY)
        result.update(raw_quality)
        result["local_raw_quality_status"] = "PASS" if not raw_quality["errors"] else "FAIL"
        result["local_raw_incomplete_or_invalid"] = result["local_raw_quality_status"] != "PASS"
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(str(exc))
        result["local_raw_quality_status"] = "FAIL"
        result["local_raw_incomplete_or_invalid"] = True
    return result


def diagnose_kline_frame_v9_34_1(frame: pd.DataFrame, *, timeframe: str, day: str) -> dict[str, Any]:
    open_ts = pd.to_datetime(frame["event_ts"], utc=True)
    expected_delta = TIMEFRAME_DELTAS[timeframe]
    diffs = open_ts.sort_values().diff().dropna()
    gap_indexes = list(diffs[diffs != expected_delta].index)
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    open_ = frame["open"].astype(float)
    close = frame["close"].astype(float)
    errors: list[str] = []
    row_count = int(len(frame))
    if row_count != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
        errors.append(f"rows {row_count} != expected_rows {EXPECTED_ROWS_BY_TIMEFRAME[timeframe]}")
    if gap_indexes:
        errors.append(f"timestamp gaps detected: {len(gap_indexes)}")
    duplicate_count = int(open_ts.duplicated().sum())
    if duplicate_count:
        errors.append("duplicate open_time detected")
    price_invariant_violations = int((high < pd.concat([open_, close, low], axis=1).max(axis=1)).sum()) + int((low > pd.concat([open_, close, high], axis=1).min(axis=1)).sum())
    non_positive_price_count = int(((open_ <= 0) | (high <= 0) | (low <= 0) | (close <= 0)).sum())
    negative_volume_count = int((frame["volume"].astype(float) < 0).sum())
    partition_mismatch_count = int((open_ts.dt.date.astype(str) != day).sum())
    missing_intervals = []
    ordered = open_ts.sort_values().reset_index(drop=True)
    diffs_ordered = ordered.diff().dropna()
    for idx, delta in diffs_ordered[diffs_ordered != expected_delta].items():
        missing_intervals.append(
            {
                "previous_open_ts": ordered.iloc[idx - 1].isoformat().replace("+00:00", "Z"),
                "next_open_ts": ordered.iloc[idx].isoformat().replace("+00:00", "Z"),
                "delta_seconds": int(delta.total_seconds()),
            }
        )
    return {
        "row_count": row_count,
        "min_open_ts": open_ts.min().isoformat().replace("+00:00", "Z") if row_count else None,
        "max_open_ts": open_ts.max().isoformat().replace("+00:00", "Z") if row_count else None,
        "duplicate_open_time_count": duplicate_count,
        "timestamp_gap_count": len(missing_intervals),
        "missing_intervals": missing_intervals[:20],
        "price_invariant_violations": price_invariant_violations,
        "non_positive_price_count": non_positive_price_count,
        "negative_volume_count": negative_volume_count,
        "partition_mismatch_count": partition_mismatch_count,
        "errors": errors,
    }


def repair_bad_day_if_needed_v9_34_1(root: Path, diagnostic: dict[str, Any], downloader: Downloader | None = None) -> dict[str, Any]:
    raw_path = raw_kline_path_v9_34(root, BAD_TIMEFRAME, BAD_DAY)
    silver_path = silver_ohlcv_path_v9_34(root, BAD_TIMEFRAME, BAD_DAY)
    repair = {
        "redownload_attempted": False,
        "redownload_success": False,
        "redownload_raw_size_bytes": 0,
        "redownload_row_count": 0,
        "redownload_quality_status": "NOT_ATTEMPTED",
        "raw_replaced_or_backup_strategy": "not_needed",
        "silver_rebuilt_for_2021_08_13": False,
        "repair_status": "not_needed",
        "network_used": False,
        "backup_raw_path": None,
        "backup_silver_path": None,
        "errors": [],
    }
    if not diagnostic["local_raw_incomplete_or_invalid"]:
        silver_result = rebuild_silver_from_raw_v9_34_1(root, BAD_TIMEFRAME, BAD_DAY, backup_existing=True)
        repair.update(silver_result)
        repair["repair_status"] = "silver_rebuilt" if silver_result["silver_rebuilt_for_2021_08_13"] else "repair_failed_quality"
        return repair
    repair["redownload_attempted"] = True
    repair["network_used"] = True
    url = build_public_archive_url(market_type=MARKET_TYPE, symbol=SYMBOL, timeframe=BAD_TIMEFRAME, date=BAD_DAY)
    temp_path = raw_path.with_suffix(".zip.v9_34_1_download")
    try:
        if downloader is None:
            download_public_archive(url, temp_path)
        else:
            downloader(url, temp_path)
    except Exception as exc:  # noqa: BLE001
        repair["repair_status"] = "source_issue"
        repair["redownload_quality_status"] = "DOWNLOAD_FAILED"
        repair["errors"].append(str(exc))
        return repair
    repair["redownload_raw_size_bytes"] = temp_path.stat().st_size if temp_path.exists() else 0
    try:
        frame = parse_binance_kline_zip(temp_path)
        redownload_quality = diagnose_kline_frame_v9_34_1(frame, timeframe=BAD_TIMEFRAME, day=BAD_DAY)
        repair["redownload_row_count"] = redownload_quality["row_count"]
        repair["redownload_quality_status"] = "PASS" if not redownload_quality["errors"] else "FAIL"
        if redownload_quality["errors"]:
            repair["repair_status"] = "source_issue"
            repair["errors"].extend(redownload_quality["errors"])
            temp_path.unlink(missing_ok=True)
            return repair
    except Exception as exc:  # noqa: BLE001
        repair["repair_status"] = "source_issue"
        repair["redownload_quality_status"] = "FAIL"
        repair["errors"].append(str(exc))
        temp_path.unlink(missing_ok=True)
        return repair
    backup_raw = backup_path_v9_34_1(root, raw_path)
    backup_raw.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists():
        shutil.copy2(raw_path, backup_raw)
        repair["backup_raw_path"] = backup_raw.as_posix()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp_path, raw_path)
    temp_path.unlink(missing_ok=True)
    repair["redownload_success"] = True
    repair["raw_replaced_or_backup_strategy"] = "original raw copied to data/quarantine before replacing raw path with validated redownload"
    silver_result = rebuild_silver_from_raw_v9_34_1(root, BAD_TIMEFRAME, BAD_DAY, backup_existing=True)
    repair.update({key: value for key, value in silver_result.items() if key not in {"repair_status"}})
    repair["repair_status"] = "repaired" if silver_result["silver_rebuilt_for_2021_08_13"] else "repair_failed_quality"
    return repair


def rebuild_silver_from_raw_v9_34_1(root: Path, timeframe: str, day: str, *, backup_existing: bool) -> dict[str, Any]:
    raw_path = raw_kline_path_v9_34(root, timeframe, day)
    silver_path = silver_ohlcv_path_v9_34(root, timeframe, day)
    result = {
        "silver_rebuilt_for_2021_08_13": False,
        "backup_silver_path": None,
        "errors": [],
    }
    try:
        raw_frame = parse_binance_kline_zip(raw_path)
        silver_frame = normalize_klines_for_v9_34(raw_frame, timeframe=timeframe, day=day, source_file=raw_path.as_posix())
        validation = validate_ohlcv_frame_v9_34(silver_frame, timeframe=timeframe, day=day)
        if not validation["passed"]:
            result["errors"].extend(validation["errors"])
            return result
        if backup_existing and silver_path.exists():
            backup_silver = backup_path_v9_34_1(root, silver_path)
            backup_silver.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(silver_path, backup_silver)
            result["backup_silver_path"] = backup_silver.as_posix()
        write_parquet(silver_frame[SILVER_COLUMNS], silver_path)
        result["silver_rebuilt_for_2021_08_13"] = timeframe == BAD_TIMEFRAME and day == BAD_DAY
        return result
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(str(exc))
        return result


def resume_missing_ohlcv_v9_34_1(root: Path, downloader: Downloader | None = None) -> tuple[list[DayResult], bool, bool, bool]:
    results: list[DayResult] = []
    source_error = False
    quality_error = False
    storage_error = False
    for timeframe in TIMEFRAMES:
        for day in date_range_v9_34(MISSING_WINDOW_START, MISSING_WINDOW_END):
            free_gib = measure_disk_v9_34(root)["free_gib_data_mount"]
            if free_gib < 2.0:
                storage_error = True
                results.append(DayResult(day, timeframe, "day_failed_storage", raw_kline_path_v9_34(root, timeframe, day).as_posix(), silver_ohlcv_path_v9_34(root, timeframe, day).as_posix(), error=f"free_gib_data_mount={free_gib}"))
                return results, source_error, quality_error, storage_error
            result = collect_or_repair_day_v9_34_1(root, timeframe, day, downloader=downloader)
            results.append(result)
            if result.status == "day_failed_source":
                source_error = True
                return results, source_error, quality_error, storage_error
            if result.status in {"day_failed_quality", "day_quarantined", "day_partial"}:
                quality_error = True
                return results, source_error, quality_error, storage_error
    return results, source_error, quality_error, storage_error


def collect_or_repair_day_v9_34_1(root: Path, timeframe: str, day: str, *, downloader: Downloader | None = None) -> DayResult:
    raw_path = raw_kline_path_v9_34(root, timeframe, day)
    silver_path = silver_ohlcv_path_v9_34(root, timeframe, day)
    if silver_path.exists() and silver_path.stat().st_size > 0 and raw_path.exists() and raw_path.stat().st_size > 0:
        valid = validate_silver_day_v9_34(silver_path, timeframe=timeframe, day=day)
        if valid["passed"]:
            return DayResult(day, timeframe, "day_skipped_existing", raw_path.as_posix(), silver_path.as_posix(), rows=valid["rows"], raw_bytes=raw_path.stat().st_size, silver_bytes=silver_path.stat().st_size)
    downloaded = False
    if not raw_path.exists() or raw_path.stat().st_size <= 0:
        url = build_public_archive_url(market_type=MARKET_TYPE, symbol=SYMBOL, timeframe=timeframe, date=day)
        try:
            if downloader is None:
                download_public_archive(url, raw_path)
            else:
                downloader(url, raw_path)
            downloaded = True
        except Exception as exc:  # noqa: BLE001
            return DayResult(day, timeframe, "day_failed_source", raw_path.as_posix(), silver_path.as_posix(), network_used=True, error=str(exc))
    raw_validation = validate_raw_zip_v9_34(raw_path)
    if not raw_validation["passed"]:
        return DayResult(day, timeframe, "day_quarantined", raw_path.as_posix(), silver_path.as_posix(), raw_bytes=raw_path.stat().st_size if raw_path.exists() else 0, network_used=downloaded, error="; ".join(raw_validation["errors"]))
    try:
        raw_frame = parse_binance_kline_zip(raw_path)
        silver_frame = normalize_klines_for_v9_34(raw_frame, timeframe=timeframe, day=day, source_file=raw_path.as_posix())
        validation = validate_ohlcv_frame_v9_34(silver_frame, timeframe=timeframe, day=day)
        if not validation["passed"]:
            return DayResult(day, timeframe, "day_failed_quality", raw_path.as_posix(), silver_path.as_posix(), rows=len(silver_frame), raw_bytes=raw_path.stat().st_size, network_used=downloaded, error="; ".join(validation["errors"]))
        if silver_path.exists() and silver_path.stat().st_size > 0:
            backup_silver = backup_path_v9_34_1(root, silver_path)
            backup_silver.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(silver_path, backup_silver)
        write_parquet(silver_frame[SILVER_COLUMNS], silver_path)
        return DayResult(day, timeframe, "day_complete", raw_path.as_posix(), silver_path.as_posix(), rows=len(silver_frame), raw_bytes=raw_path.stat().st_size, silver_bytes=silver_path.stat().st_size, network_used=downloaded)
    except Exception as exc:  # noqa: BLE001
        return DayResult(day, timeframe, "day_failed_quality", raw_path.as_posix(), silver_path.as_posix(), raw_bytes=raw_path.stat().st_size if raw_path.exists() else 0, network_used=downloaded, error=str(exc))


def build_timeframe_reports_v9_34_1(results: list[DayResult], diagnostic_after: dict[str, Any]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES:
        tf_results = [result for result in results if result.timeframe == timeframe]
        reports.append(
            {
                "version": VERSION,
                "timeframe": timeframe,
                "target_window_start": TARGET_WINDOW_START,
                "target_window_end": TARGET_WINDOW_END,
                "missing_window_start": MISSING_WINDOW_START,
                "missing_window_end": MISSING_WINDOW_END,
                "days_attempted": len(tf_results),
                "days_downloaded": sum(1 for result in tf_results if result.network_used and result.status in {"day_complete", "day_failed_quality", "day_quarantined"}),
                "days_normalized": sum(1 for result in tf_results if result.status == "day_complete"),
                "days_complete": diagnostic_after["available_days_by_timeframe"][timeframe],
                "days_missing": diagnostic_after["missing_days_by_timeframe"][timeframe],
                "days_failed": sum(1 for result in tf_results if result.status.startswith("day_failed")),
                "days_quarantined": sum(1 for result in tf_results if result.status == "day_quarantined"),
                "days_skipped_existing": sum(1 for result in tf_results if result.status == "day_skipped_existing"),
                "rows_new": sum(result.rows for result in tf_results if result.status == "day_complete"),
                "raw_bytes_new": sum(result.raw_bytes for result in tf_results if result.network_used),
                "silver_bytes_new": sum(result.silver_bytes for result in tf_results if result.status == "day_complete"),
                "quality_status": "PASS" if diagnostic_after["missing_days_by_timeframe"][timeframe] == 0 else "INCOMPLETE",
            }
        )
    return reports


def decide_v9_34_1(
    *,
    diagnostic_after: dict[str, Any],
    totals: dict[str, Any],
    storage_error_detected: bool,
    source_error_detected: bool,
    quality_error_detected: bool,
) -> dict[str, str]:
    if storage_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_storage", "next_recommendation": "V9.35 - Storage Review Before OHLCV Extension", "justification": "L'espace disque operationnel est insuffisant."}
    if source_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_source_issue", "next_recommendation": "V9.35 - OHLCV From AggTrades Derivation", "justification": "Le fichier public Binance est indisponible ou incomplet."}
    if quality_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_quality", "next_recommendation": "V9.35 - OHLCV 5Y Coverage Correction", "justification": "Un fichier OHLCV echoue les controles qualite apres correction."}
    if diagnostic_after["ohlcv_5y_ready"]:
        return {"decision": "ohlcv_5y_extension_complete", "next_recommendation": "V9.35 - OHLCV + AggTrades 5Y Feature Store", "justification": "OHLCV 5Y complet et valide pour 1m/5m/15m/1h."}
    if totals["days_complete_total"] > 0:
        return {"decision": "ohlcv_5y_extension_partial", "next_recommendation": "V9.35 - OHLCV 5Y Coverage Correction", "justification": "Une partie de l'extension est completee mais la couverture reste incomplete."}
    return {"decision": "ohlcv_5y_extension_not_executed_manual_review", "next_recommendation": "V9.35 - OHLCV Source Gap Review", "justification": "Aucune reprise exploitable n'a ete executee."}


def build_safety_flags_v9_34_1(repair: dict[str, Any], totals: dict[str, Any]) -> dict[str, Any]:
    flags = dict(SAFETY_FLAGS)
    network_used = repair["network_used"] or totals["network_used"]
    new_data_downloaded = repair["redownload_success"] or totals["days_downloaded_total"] > 0
    ingestion_executed = repair["silver_rebuilt_for_2021_08_13"] or totals["days_normalized_total"] > 0
    flags.update(
        {
            "network_used": network_used,
            "network_scope": "public_archive_read_only" if network_used else "not_used",
            "new_data_downloaded": new_data_downloaded,
            "new_data_download_scope": "public_historical_ohlcv_klines_5y_extension_correction_only" if new_data_downloaded else "none",
            "ingestion_executed": ingestion_executed,
            "ingestion_scope": "public_ohlcv_bronze_silver_5y_extension_correction_only" if ingestion_executed else "none",
            "no_combined_feature_store": True,
        }
    )
    return flags


def build_warnings_v9_34_1(diagnostic_after: dict[str, Any], repair: dict[str, Any], totals: dict[str, Any], source_error: bool) -> list[str]:
    warnings: list[str] = []
    if not diagnostic_after["ohlcv_5y_ready"]:
        warnings.append("OHLCV 5Y reste incomplet.")
    if repair["redownload_attempted"]:
        warnings.append("Le raw local 2021-08-13 1m etait incomplet/invalide et a declenche un re-download public.")
    if source_error:
        warnings.append("La derivation OHLCV depuis aggTrades doit etre consideree.")
    if totals["days_skipped_existing_total"]:
        warnings.append("Des jours silver deja complets ont ete skipped sans ecrasement.")
    return warnings


def build_blockers_v9_34_1(diagnostic_after: dict[str, Any], repair: dict[str, Any], storage: bool, source: bool, quality: bool) -> list[str]:
    blockers: list[str] = []
    if storage:
        blockers.append("storage_blocker")
    if source:
        blockers.append("source_issue")
    if quality:
        blockers.append("quality_issue")
    if repair["repair_status"] in {"source_issue", "repair_failed_quality"}:
        blockers.append(f"bad_day_{repair['repair_status']}")
    if not diagnostic_after["ohlcv_5y_ready"]:
        blockers.append("ohlcv_5y_incomplete")
    return blockers


def build_manifest_v9_34_1(report: dict[str, Any]) -> dict[str, Any]:
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
        "ohlcv_5y_ready": report["ohlcv_5y_ready"],
        "repair_status": report["repair_status"],
        "redownload_attempted": report["redownload_attempted"],
        "redownload_success": report["redownload_success"],
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "feature_store_created": report["feature_store_created"],
        "quality_status": report["ohlcv_quality"]["quality_status"],
        "coverage_status": report["ohlcv_quality"]["coverage_status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_34_1(report: dict[str, Any]) -> str:
    bad = report["bad_day_diagnostic"]
    lines = [
        "# V9.34.1 - OHLCV 5Y Extension Correction",
        "",
        "## Resume",
        f"- Decision V9.34.1 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- OHLCV 5Y ready : `{report['ohlcv_5y_ready']}`.",
        f"- Re-download 2021-08-13 1m : `{report['redownload_attempted']}` / `{report['redownload_success']}`.",
        f"- Repair status : `{report['repair_status']}`.",
        "",
        "## Diagnostic 2021-08-13 1m",
        f"- Rows avant : `{bad['before']['row_count']}` / `{bad['before']['expected_row_count']}`.",
        f"- Gaps avant : `{bad['before']['timestamp_gap_count']}`.",
        f"- Rows re-download : `{report['redownload_row_count']}`.",
        f"- Qualite re-download : `{report['redownload_quality_status']}`.",
        f"- Silver reconstruit : `{report['silver_rebuilt_for_2021_08_13']}`.",
        "",
        "## Reprise",
        f"- Timeframes traites : `{report['timeframes_treated']}`.",
        f"- Jours telecharges/normalises/complets : `{report['days_downloaded_total']}` / `{report['days_normalized_total']}` / `{report['days_complete_total']}`.",
        f"- Failed/quarantine/skipped : `{report['days_failed_total']}` / `{report['days_quarantined_total']}` / `{report['days_skipped_existing_total']}`.",
        f"- Jours manquants apres reprise : `{report['diagnostic_after']['missing_days_by_timeframe']}`.",
        "",
        "## Garde-fous",
        "- Aucun feature store combine OHLCV + aggTrades, aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.",
        "- Aucun endpoint prive, aucune cle API, aucun websocket live, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_34_1(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_34_1_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "ohlcv_5y_ready": report["ohlcv_5y_ready"],
        "repair_status": report["repair_status"],
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "feature_store_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.34.1\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.34.1 : `{report['decision']}`.\n"
        f"- OHLCV 5Y ready : `{report['ohlcv_5y_ready']}`.\n"
        f"- Repair status : `{report['repair_status']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun feature store combine, aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, correction extension OHLCV 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, feature store combine, modele persistant, API privee ou cle API.\n",
    )


def backup_path_v9_34_1(root: Path, source_path: Path) -> Path:
    relative = source_path.relative_to(root)
    return root / "data/quarantine/public_market/ohlcv/v9_34_1" / relative


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
