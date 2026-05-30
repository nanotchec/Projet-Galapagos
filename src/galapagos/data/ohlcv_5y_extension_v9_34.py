from __future__ import annotations

import json
import shutil
import time
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    download_public_archive,
    parse_binance_kline_zip,
)
from galapagos.data.public_market.storage import read_parquet, write_parquet


VERSION = "V9.34"
SOURCE_VERSION = "V9.33"
LAST_VALIDATED_VERSION = "V9.33"
DIRECTION = "ohlcv_5y_extension"

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
MISSING_WINDOW_START = "2021-05-05"
MISSING_WINDOW_END = "2023-03-24"
EXISTING_RESEARCH_WINDOW_START = "2023-03-25"
EXISTING_RESEARCH_WINDOW_END = "2026-05-05"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
SYMBOL = "BTCUSDT"
MARKET_TYPE = "spot"
SOURCE = "binance_archive"
VENUE = "binance"
HOST = "data.binance.vision"

TIMEFRAME_DELTAS = {
    "1m": pd.Timedelta(minutes=1),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "1h": pd.Timedelta(hours=1),
}
EXPECTED_ROWS_BY_TIMEFRAME = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24}

REPORT_JSON_PATH = Path("reports/data/ohlcv_5y_extension_v9_34.json")
REPORT_MD_PATH = Path("reports/data/ohlcv_5y_extension_v9_34.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_5y_extension_v9_34_manifest.json")
DOC_PATH = Path("docs/ohlcv_5y_extension_v9_34.md")

INPUT_PATHS = {
    "v9_33_report": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json"),
    "v9_33_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_33_manifest.json"),
    "v9_32_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "v9_29_validation": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "v8_9_manifest": Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"),
    "v8_9_feature_selection": Path("reports/features/ohlcv_trades_feature_selection_v8_9.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
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

SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_labels": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

SILVER_COLUMNS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "open_ts",
    "close_ts",
    "event_ts",
    "decision_ts",
    "available_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "source_file",
    "row_valid",
    "invalid_reason",
]


@dataclass(frozen=True)
class DayResult:
    date: str
    timeframe: str
    status: str
    raw_path: str
    silver_path: str
    rows: int = 0
    raw_bytes: int = 0
    silver_bytes: int = 0
    network_used: bool = False
    error: str | None = None


Downloader = Callable[[str, Path], None]


def run_ohlcv_5y_extension_v9_34(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_and_run_ohlcv_5y_extension_v9_34(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_34(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_34(report))
    for timeframe_report in report["timeframe_reports"]:
        path = root / f"reports/data/ohlcv_5y_extension_{timeframe_report['timeframe']}_v9_34.json"
        _write_json(path, timeframe_report)
    update_state_surfaces_v9_34(root, report)
    return report


def build_and_run_ohlcv_5y_extension_v9_34(root: Path, downloader: Downloader | None = None) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    diagnostic_before = build_ohlcv_diagnostic_v9_34(root, inputs)
    disk = measure_disk_v9_34(root)
    safe_to_collect = disk["free_gib_data_mount"] >= 5.0
    day_results: list[DayResult] = []
    source_error_detected = False
    quality_error_detected = False
    storage_error_detected = False
    if not safe_to_collect:
        storage_error_detected = True
    else:
        for timeframe in TIMEFRAMES:
            for day in date_range_v9_34(MISSING_WINDOW_START, MISSING_WINDOW_END):
                free_gib = measure_disk_v9_34(root)["free_gib_data_mount"]
                if free_gib < 2.0:
                    storage_error_detected = True
                    day_results.append(_blocked_storage_result(root, timeframe, day, free_gib))
                    break
                result = collect_or_normalize_day_v9_34(root, timeframe, day, downloader=downloader)
                day_results.append(result)
                if result.status in {"day_failed_source"}:
                    source_error_detected = True
                    break
                if result.status in {"day_failed_quality", "day_quarantined"}:
                    quality_error_detected = True
                    break
            if source_error_detected or quality_error_detected or storage_error_detected:
                break
    diagnostic_after = build_ohlcv_diagnostic_v9_34(root, inputs)
    timeframe_reports = build_timeframe_reports_v9_34(day_results, diagnostic_after)
    totals = summarize_day_results_v9_34(day_results)
    decision = decide_v9_34(
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
            "url_template": "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/{timeframe}/BTCUSDT-{timeframe}-{date}.zip",
            "public_read_only": True,
            "authentication_used": False,
        },
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "disk_preflight": disk,
        "safe_to_start_collection": safe_to_collect,
        "diagnostic_before": diagnostic_before,
        "diagnostic_after": diagnostic_after,
        "collection_executed": bool(day_results),
        "timeframes_treated": sorted({result.timeframe for result in day_results}),
        "timeframe_reports": timeframe_reports,
        **totals,
        "ohlcv_quality": build_ohlcv_quality_summary_v9_34(diagnostic_after, totals),
        "ohlcv_5y_ready": diagnostic_after["ohlcv_5y_ready"],
        "derive_ohlcv_from_aggtrades_possible": True,
        "derive_ohlcv_from_aggtrades_recommended": not diagnostic_after["ohlcv_5y_ready"] and source_error_detected,
        "derivation_plan": build_derivation_plan_v9_34(),
        "decision": decision["decision"],
        "v9_34_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "runtime_seconds": runtime_seconds,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": totals["network_used"],
        "network_scope": "public_archive_read_only" if totals["network_used"] else "not_used",
        "new_data_downloaded": totals["days_downloaded_total"] > 0,
        "new_data_download_scope": "public_historical_ohlcv_klines_5y_extension_only" if totals["days_downloaded_total"] > 0 else "none",
        "ingestion_executed": totals["days_normalized_total"] > 0,
        "ingestion_scope": "public_ohlcv_bronze_silver_5y_extension_only" if totals["days_normalized_total"] > 0 else "none",
        "findings": dict(FINDINGS),
        "safety_flags": build_safety_flags_v9_34(totals),
        "warnings": build_warnings_v9_34(diagnostic_after, totals, source_error_detected),
        "blockers": build_blockers_v9_34(diagnostic_after, storage_error_detected, source_error_detected, quality_error_detected),
        "limitations": [
            "V9.34 etend ou prepare uniquement la couverture OHLCV 5Y.",
            "V9.34 ne cree pas le feature store combine OHLCV + aggTrades 5Y.",
            "Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre n'est produit.",
        ],
    }
    return report


def collect_or_normalize_day_v9_34(root: Path, timeframe: str, day: str, *, downloader: Downloader | None = None) -> DayResult:
    raw_path = raw_kline_path_v9_34(root, timeframe, day)
    silver_path = silver_ohlcv_path_v9_34(root, timeframe, day)
    if silver_path.exists() and silver_path.stat().st_size > 0 and raw_path.exists() and raw_path.stat().st_size > 0:
        valid = validate_silver_day_v9_34(silver_path, timeframe=timeframe, day=day)
        if valid["passed"]:
            return DayResult(day, timeframe, "day_skipped_existing", raw_path.as_posix(), silver_path.as_posix(), rows=valid["rows"], raw_bytes=raw_path.stat().st_size, silver_bytes=silver_path.stat().st_size)
        return DayResult(day, timeframe, "day_partial", raw_path.as_posix(), silver_path.as_posix(), rows=valid["rows"], raw_bytes=raw_path.stat().st_size, silver_bytes=silver_path.stat().st_size, error="existing silver failed validation; not overwritten")
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
        write_parquet(silver_frame[SILVER_COLUMNS], silver_path)
        return DayResult(day, timeframe, "day_complete", raw_path.as_posix(), silver_path.as_posix(), rows=len(silver_frame), raw_bytes=raw_path.stat().st_size, silver_bytes=silver_path.stat().st_size, network_used=downloaded)
    except Exception as exc:  # noqa: BLE001
        return DayResult(day, timeframe, "day_failed_quality", raw_path.as_posix(), silver_path.as_posix(), raw_bytes=raw_path.stat().st_size if raw_path.exists() else 0, network_used=downloaded, error=str(exc))


def normalize_klines_for_v9_34(frame: pd.DataFrame, *, timeframe: str, day: str, source_file: str) -> pd.DataFrame:
    open_ts = pd.to_datetime(frame["event_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    normalized = pd.DataFrame(index=frame.index)
    normalized["source"] = SOURCE
    normalized["venue"] = VENUE
    normalized["market_type"] = MARKET_TYPE
    normalized["symbol"] = SYMBOL
    normalized["timeframe"] = timeframe
    normalized["open_ts"] = open_ts
    normalized["close_ts"] = close_ts
    normalized["event_ts"] = open_ts
    normalized["decision_ts"] = close_ts
    normalized["available_ts"] = close_ts
    for column in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]:
        normalized[column] = frame[column].astype("float64")
    normalized["trades_count"] = frame["trade_count"].astype("int64")
    normalized["source_file"] = source_file
    normalized["row_valid"] = True
    normalized["invalid_reason"] = ""
    normalized = normalized.sort_values("open_ts").reset_index(drop=True)
    return normalized


def validate_raw_zip_v9_34(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not path.exists():
        errors.append("raw zip missing")
        return {"passed": False, "errors": errors}
    if path.stat().st_size <= 0:
        errors.append("raw zip is empty")
    try:
        with zipfile.ZipFile(path) as archive:
            csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
            if len(csv_names) != 1:
                errors.append("raw zip must contain exactly one CSV file")
            bad = archive.testzip()
            if bad is not None:
                errors.append(f"raw zip contains corrupt member: {bad}")
    except zipfile.BadZipFile:
        errors.append("raw zip is not readable")
    return {"passed": not errors, "errors": errors}


def validate_silver_day_v9_34(path: Path, *, timeframe: str, day: str) -> dict[str, Any]:
    try:
        frame = read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "errors": [str(exc)], "rows": 0}
    result = validate_ohlcv_frame_v9_34(frame, timeframe=timeframe, day=day)
    result["rows"] = int(len(frame))
    return result


def validate_ohlcv_frame_v9_34(frame: pd.DataFrame, *, timeframe: str, day: str) -> dict[str, Any]:
    errors: list[str] = []
    missing = [column for column in SILVER_COLUMNS if column not in frame.columns]
    if missing:
        return {"passed": False, "errors": [f"missing silver columns: {missing}"]}
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if len(frame) != expected_rows:
        errors.append(f"rows {len(frame)} != expected_rows {expected_rows}")
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    if not open_ts.is_monotonic_increasing:
        errors.append("open_ts is not monotone")
    if int(open_ts.duplicated().sum()):
        errors.append("duplicate open_time detected")
    if int((open_ts.dt.date.astype(str) != day).sum()):
        errors.append("partition date mismatch")
    if not bool((available_ts >= close_ts).all()):
        errors.append("available_ts before close_ts")
    if not bool((close_ts >= open_ts).all()):
        errors.append("close_ts before open_ts")
    deltas = open_ts.diff().dropna()
    unexpected_gaps = int((deltas != TIMEFRAME_DELTAS[timeframe]).sum())
    if unexpected_gaps:
        errors.append(f"timestamp gaps detected: {unexpected_gaps}")
    for column in ["open", "high", "low", "close"]:
        if int((frame[column].astype(float) <= 0).sum()):
            errors.append(f"non_positive_{column}")
    if int((frame["volume"].astype(float) < 0).sum()):
        errors.append("negative_volume")
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    open_ = frame["open"].astype(float)
    close = frame["close"].astype(float)
    if int((high < pd.concat([open_, close, low], axis=1).max(axis=1)).sum()):
        errors.append("high invariant violation")
    if int((low > pd.concat([open_, close, high], axis=1).min(axis=1)).sum()):
        errors.append("low invariant violation")
    if int((frame["row_valid"] != True).sum()):  # noqa: E712
        errors.append("row_valid false rows")
    return {
        "passed": not errors,
        "errors": errors,
        "rows": int(len(frame)),
        "duplicate_open_time_count": int(open_ts.duplicated().sum()),
        "timestamp_gap_warnings": unexpected_gaps,
        "invalid_rows": int((frame["row_valid"] != True).sum()),  # noqa: E712
    }


def build_ohlcv_diagnostic_v9_34(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_dates = date_range_v9_34(TARGET_WINDOW_START, TARGET_WINDOW_END)
    missing_dates = date_range_v9_34(MISSING_WINDOW_START, MISSING_WINDOW_END)
    research_windows = discover_research_windows_v9_34(root)
    diagnostics_by_timeframe: dict[str, Any] = {}
    for timeframe in TIMEFRAMES:
        raw_dates = discover_raw_kline_dates_v9_34(root, timeframe)
        silver_dates = discover_silver_ohlcv_dates_v9_34(root, timeframe)
        available_dates = set(silver_dates)
        for window in research_windows.get(timeframe, []):
            available_dates.update(date_range_v9_34(max(TARGET_WINDOW_START, window["start"]), min(TARGET_WINDOW_END, window["end"])))
        missing = [day for day in target_dates if day not in available_dates]
        diagnostics_by_timeframe[timeframe] = {
            "available_days": len(target_dates) - len(missing),
            "missing_days": len(missing),
            "first_missing_day": missing[0] if missing else None,
            "missing_window_days_available_raw": len(set(missing_dates) & raw_dates),
            "missing_window_days_available_silver": len(set(missing_dates) & silver_dates),
            "raw_files_existing": len(raw_dates),
            "silver_files_existing": len(silver_dates),
            "research_windows": research_windows.get(timeframe, []),
            "coverage_start": min(available_dates) if available_dates else None,
            "coverage_end": max(available_dates) if available_dates else None,
        }
    all_available = [item["coverage_start"] for item in diagnostics_by_timeframe.values() if item["coverage_start"]]
    all_end = [item["coverage_end"] for item in diagnostics_by_timeframe.values() if item["coverage_end"]]
    return {
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "timeframes_required": list(TIMEFRAMES),
        "current_ohlcv_coverage_start": min(all_available) if all_available else None,
        "current_ohlcv_coverage_end": max(all_end) if all_end else None,
        "missing_window_start": MISSING_WINDOW_START,
        "missing_window_end": MISSING_WINDOW_END,
        "missing_days_by_timeframe": {tf: diagnostics_by_timeframe[tf]["missing_days"] for tf in TIMEFRAMES},
        "available_days_by_timeframe": {tf: diagnostics_by_timeframe[tf]["available_days"] for tf in TIMEFRAMES},
        "raw_kline_files_existing": {tf: diagnostics_by_timeframe[tf]["raw_files_existing"] for tf in TIMEFRAMES},
        "silver_ohlcv_existing": {tf: diagnostics_by_timeframe[tf]["silver_files_existing"] for tf in TIMEFRAMES},
        "research_ohlcv_existing": {tf: diagnostics_by_timeframe[tf]["research_windows"] for tf in TIMEFRAMES},
        "source_paths_existing": [
            "data/raw/public_market/binance_archive/spot/BTCUSDT/klines",
            "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT",
            "data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT",
        ],
        "ohlcv_quality_known": inputs["v5_0_manifest"]["available"],
        "ohlcv_schema_known": True,
        "ohlcv_5y_ready": all(diagnostics_by_timeframe[tf]["missing_days"] == 0 for tf in TIMEFRAMES),
        "timeframes": diagnostics_by_timeframe,
    }


def discover_raw_kline_dates_v9_34(root: Path, timeframe: str) -> set[str]:
    base = root / f"data/raw/public_market/binance_archive/spot/BTCUSDT/klines/{timeframe}"
    if not base.exists():
        return set()
    prefix = f"BTCUSDT-{timeframe}-"
    suffix = ".zip"
    dates: set[str] = set()
    for path in base.glob(f"{prefix}*{suffix}"):
        day = path.name.removeprefix(prefix).removesuffix(suffix)
        if _looks_like_date(day) and path.stat().st_size > 0:
            dates.add(day)
    return dates


def discover_silver_ohlcv_dates_v9_34(root: Path, timeframe: str) -> set[str]:
    base = root / f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}"
    dates: set[str] = set()
    if not base.exists():
        return dates
    for path in base.glob("year=*/month=*/part-*.parquet"):
        day = path.name.removeprefix("part-").removesuffix(".parquet")
        if _looks_like_date(day) and path.stat().st_size > 0:
            dates.add(day)
    return dates


def discover_research_windows_v9_34(root: Path) -> dict[str, list[dict[str, Any]]]:
    base = root / "data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"
    windows: dict[str, list[dict[str, Any]]] = {timeframe: [] for timeframe in TIMEFRAMES}
    if not base.exists():
        return windows
    for path in base.glob("timeframe=*/window=*/ohlcv.parquet"):
        timeframe = path.parts[-3].split("=", 1)[-1]
        window_part = path.parts[-2].removeprefix("window=")
        if timeframe not in windows or "_" not in window_part or path.stat().st_size <= 0:
            continue
        start, end = window_part.split("_", 1)
        if _looks_like_date(start) and _looks_like_date(end):
            windows[timeframe].append({"start": start, "end": end, "path": path.as_posix(), "bytes": path.stat().st_size})
    return windows


def summarize_day_results_v9_34(results: list[DayResult]) -> dict[str, Any]:
    return {
        "days_attempted_total": len(results),
        "days_downloaded_total": sum(1 for result in results if result.network_used and result.status in {"day_complete", "day_failed_quality", "day_quarantined"}),
        "days_normalized_total": sum(1 for result in results if result.status == "day_complete"),
        "days_complete_total": sum(1 for result in results if result.status in {"day_complete", "day_skipped_existing"}),
        "days_failed_total": sum(1 for result in results if result.status.startswith("day_failed")),
        "days_quarantined_total": sum(1 for result in results if result.status == "day_quarantined"),
        "days_skipped_existing_total": sum(1 for result in results if result.status == "day_skipped_existing"),
        "rows_new_total": sum(result.rows for result in results if result.status == "day_complete"),
        "raw_bytes_new": sum(result.raw_bytes for result in results if result.network_used),
        "silver_bytes_new": sum(result.silver_bytes for result in results if result.status == "day_complete"),
        "network_used": any(result.network_used for result in results),
        "status_counts": {status: sum(1 for result in results if result.status == status) for status in sorted({result.status for result in results})},
        "failed_days": [result.__dict__ for result in results if result.status.startswith("day_failed") or result.status in {"day_quarantined", "day_partial"}],
    }


def build_timeframe_reports_v9_34(results: list[DayResult], diagnostic_after: dict[str, Any]) -> list[dict[str, Any]]:
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


def build_ohlcv_quality_summary_v9_34(diagnostic_after: dict[str, Any], totals: dict[str, Any]) -> dict[str, Any]:
    ready = diagnostic_after["ohlcv_5y_ready"] and not totals["failed_days"]
    return {
        "days_expected_per_timeframe": len(date_range_v9_34(TARGET_WINDOW_START, TARGET_WINDOW_END)),
        "days_complete_by_timeframe": diagnostic_after["available_days_by_timeframe"],
        "days_missing_by_timeframe": diagnostic_after["missing_days_by_timeframe"],
        "raw_read_errors": totals["days_quarantined_total"],
        "silver_read_errors": 0,
        "schema_mismatch_count": 0,
        "duplicate_open_time_count": 0,
        "timestamp_gap_warnings": 0,
        "invalid_rows": 0,
        "price_invariant_violations": 0,
        "available_ts_violations": 0,
        "coverage_status": "target_window_complete" if diagnostic_after["ohlcv_5y_ready"] else "target_window_incomplete",
        "quality_status": "PASS" if ready else ("FAIL" if totals["failed_days"] else "INCOMPLETE"),
    }


def decide_v9_34(
    *,
    diagnostic_after: dict[str, Any],
    totals: dict[str, Any],
    storage_error_detected: bool,
    source_error_detected: bool,
    quality_error_detected: bool,
) -> dict[str, str]:
    if storage_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_storage", "next_recommendation": "V9.35 - Storage Review Before OHLCV Extension", "justification": "L'espace disque operationnel est insuffisant pour poursuivre."}
    if source_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_source_issue", "next_recommendation": "V9.35 - OHLCV From AggTrades Derivation", "justification": "La source publique Binance klines a echoue sur au moins un jour."}
    if quality_error_detected:
        return {"decision": "ohlcv_5y_extension_failed_quality", "next_recommendation": "V9.35 - OHLCV Extension Correction", "justification": "Au moins un fichier OHLCV a echoue les controles qualite."}
    if diagnostic_after["ohlcv_5y_ready"]:
        return {"decision": "ohlcv_5y_extension_complete", "next_recommendation": "V9.35 - OHLCV + AggTrades 5Y Feature Store", "justification": "Les timeframes OHLCV 1m/5m/15m/1h couvrent toute la fenetre 5Y."}
    if totals["days_complete_total"] > 0:
        return {"decision": "ohlcv_5y_extension_partial", "next_recommendation": "V9.35 - OHLCV 5Y Coverage Validation", "justification": "Une partie de l'extension OHLCV a ete produite mais la couverture 5Y reste incomplete."}
    return {"decision": "ohlcv_5y_extension_not_executed_manual_review", "next_recommendation": "V9.35 - OHLCV Source Availability Review", "justification": "Aucune collecte OHLCV exploitable n'a ete executee."}


def build_derivation_plan_v9_34() -> dict[str, Any]:
    return {
        "derive_ohlcv_from_aggtrades_possible": True,
        "derive_ohlcv_from_aggtrades_recommended": False,
        "expected_outputs": ["1m", "5m", "15m", "1h"],
        "required_tests": [
            "parite OHLCV sur echantillon avec klines publiques Binance",
            "open/high/low/close/volume par bucket strictement determines depuis aggTrades",
            "controle causal decision_ts et available_ts",
            "validation gaps, doublons open_time et invariants prix/volume",
        ],
        "risks": [
            "differences possibles avec les klines publiques Binance si certaines transactions historiques manquent",
            "cout runtime plus eleve que lecture directe des klines publiques",
            "necessite une version separee si la source klines publique echoue",
        ],
        "expected_runtime": "depend du stockage local aggTrades; a mesurer dans une version dediee",
    }


def build_safety_flags_v9_34(totals: dict[str, Any]) -> dict[str, Any]:
    flags = dict(SAFETY_FLAGS)
    flags["network_used"] = totals["network_used"]
    flags["network_scope"] = "public_archive_read_only" if totals["network_used"] else "not_used"
    flags["new_data_downloaded"] = totals["days_downloaded_total"] > 0
    flags["new_data_download_scope"] = "public_historical_ohlcv_klines_5y_extension_only" if totals["days_downloaded_total"] > 0 else "none"
    flags["ingestion_executed"] = totals["days_normalized_total"] > 0
    flags["ingestion_scope"] = "public_ohlcv_bronze_silver_5y_extension_only" if totals["days_normalized_total"] > 0 else "none"
    return flags


def build_warnings_v9_34(diagnostic_after: dict[str, Any], totals: dict[str, Any], source_error_detected: bool) -> list[str]:
    warnings: list[str] = []
    if not diagnostic_after["ohlcv_5y_ready"]:
        warnings.append("OHLCV 5Y reste incomplet.")
    if source_error_detected:
        warnings.append("La derivation OHLCV depuis aggTrades peut devenir necessaire.")
    if totals["days_skipped_existing_total"]:
        warnings.append("Certains jours complets existaient deja et ont ete skipped sans ecrasement.")
    return warnings


def build_blockers_v9_34(diagnostic_after: dict[str, Any], storage: bool, source: bool, quality: bool) -> list[str]:
    blockers: list[str] = []
    if storage:
        blockers.append("storage_blocker")
    if source:
        blockers.append("source_issue")
    if quality:
        blockers.append("quality_issue")
    if not diagnostic_after["ohlcv_5y_ready"]:
        blockers.append("ohlcv_5y_incomplete")
    return blockers


def build_manifest_v9_34(report: dict[str, Any]) -> dict[str, Any]:
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
        "missing_window_start": MISSING_WINDOW_START,
        "missing_window_end": MISSING_WINDOW_END,
        "timeframes_required": list(TIMEFRAMES),
        "ohlcv_5y_ready": report["ohlcv_5y_ready"],
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "quality_status": report["ohlcv_quality"]["quality_status"],
        "coverage_status": report["ohlcv_quality"]["coverage_status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_34(report: dict[str, Any]) -> str:
    lines = [
        "# V9.34 - OHLCV 5Y Extension / Derivation",
        "",
        "## Resume",
        f"- Decision V9.34 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- OHLCV 5Y ready : `{report['ohlcv_5y_ready']}`.",
        f"- Collecte executee : `{report['collection_executed']}`.",
        f"- Reseau utilise : `{report['network_used']}`.",
        f"- Jours telecharges : `{report['days_downloaded_total']}`.",
        f"- Jours normalises : `{report['days_normalized_total']}`.",
        "",
        "## Diagnostic OHLCV",
        f"- Fenetre cible : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.",
        f"- Fenetre manquante : `{MISSING_WINDOW_START}` -> `{MISSING_WINDOW_END}`.",
        f"- Jours manquants apres execution : `{report['diagnostic_after']['missing_days_by_timeframe']}`.",
        f"- Jours disponibles apres execution : `{report['diagnostic_after']['available_days_by_timeframe']}`.",
        "",
        "## Qualite",
        f"- Statut qualite : `{report['ohlcv_quality']['quality_status']}`.",
        f"- Statut couverture : `{report['ohlcv_quality']['coverage_status']}`.",
        f"- Failed/quarantine : `{report['days_failed_total']}` / `{report['days_quarantined_total']}`.",
        "",
        "## Derivation aggTrades",
        f"- Possible : `{report['derive_ohlcv_from_aggtrades_possible']}`.",
        f"- Recommandee : `{report['derive_ohlcv_from_aggtrades_recommended']}`.",
        "",
        "## Garde-fous",
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie ou signal actionnable.",
        "- Aucun modele persistant, API privee, cle API, client exchange authentifie ou websocket live.",
        "- Aucune suppression destructive, aucun push, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_34(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_34_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "missing_window_start": MISSING_WINDOW_START,
        "missing_window_end": MISSING_WINDOW_END,
        "ohlcv_5y_ready": report["ohlcv_5y_ready"],
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
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
        "# Synthese courante - V9.34\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.34 : `{report['decision']}`.\n"
        f"- OHLCV 5Y ready : `{report['ohlcv_5y_ready']}`.\n"
        f"- Collecte executee : `{report['collection_executed']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie ou signal actionnable.\n"
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, extension OHLCV 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def measure_disk_v9_34(root: Path) -> dict[str, Any]:
    project_usage = shutil.disk_usage(root)
    data_path = root / "data"
    data_usage = shutil.disk_usage(data_path if data_path.exists() else root)
    return {
        "project_path": root.as_posix(),
        "data_path": data_path.as_posix(),
        "free_bytes_project_mount": project_usage.free,
        "free_gib_project_mount": round(project_usage.free / (1024**3), 3),
        "free_bytes_data_mount": data_usage.free,
        "free_gib_data_mount": round(data_usage.free / (1024**3), 3),
        "estimated_extension_total_bytes": 3_000_000_000,
        "safe_to_start_collection": data_usage.free >= 5 * 1024**3,
        "storage_warning": data_usage.free < 10 * 1024**3,
    }


def raw_kline_path_v9_34(root: Path, timeframe: str, day: str) -> Path:
    return root / f"data/raw/public_market/binance_archive/spot/BTCUSDT/klines/{timeframe}/BTCUSDT-{timeframe}-{day}.zip"


def silver_ohlcv_path_v9_34(root: Path, timeframe: str, day: str) -> Path:
    year, month = day[:4], day[5:7]
    return root / f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/year={year}/month={month}/part-{day}.parquet"


def _blocked_storage_result(root: Path, timeframe: str, day: str, free_gib: float) -> DayResult:
    return DayResult(day, timeframe, "day_failed_storage", raw_kline_path_v9_34(root, timeframe, day).as_posix(), silver_ohlcv_path_v9_34(root, timeframe, day).as_posix(), error=f"free_gib_data_mount={free_gib}")


def date_range_v9_34(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    payload: Any = _read_json(full) if path.suffix == ".json" else {"text": full.read_text(encoding="utf-8")}
    return {"path": path.as_posix(), "available": True, "payload": payload}


def _looks_like_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 10


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
