from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.ohlcv_5y_extension_v9_34 import FINDINGS, measure_disk_v9_34
from galapagos.data.public_market.storage import write_parquet


VERSION = "V9.35"
SOURCE_VERSION = "V9.34.1"
LAST_VALIDATED_VERSION = "V9.34.1"
SOURCE_AGGTRADES_VALIDATION_VERSION = "V9.32"
DIRECTION = "ohlcv_from_aggtrades_5y_derivation"

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
SYMBOL = "BTCUSDT"
MARKET_TYPE = "spot"
SOURCE = "binance_archive"
VENUE = "binance"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
TIMEFRAME_FREQ = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}
TIMEFRAME_DELTAS = {"1m": pd.Timedelta(minutes=1), "5m": pd.Timedelta(minutes=5), "15m": pd.Timedelta(minutes=15), "1h": pd.Timedelta(hours=1)}
EXPECTED_ROWS_BY_TIMEFRAME = {"1m": 2_630_880, "5m": 526_176, "15m": 175_392, "1h": 43_848}
EXPECTED_DAYS = 1827
DERIVATION_RUN_ID = "ohlcv_from_aggtrades_5y_v9_35"
SCHEMA_VERSION = "ohlcv_from_aggtrades_v1"

REPORT_JSON_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_v9_35.json")
REPORT_MD_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_v9_35.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_from_aggtrades_5y_v9_35_manifest.json")
DOC_PATH = Path("docs/ohlcv_from_aggtrades_5y_v9_35.md")

INPUT_PATHS = {
    "v9_34_1_report": Path("reports/data/ohlcv_5y_extension_correction_v9_34_1.json"),
    "v9_34_1_manifest": Path("reports/manifests/ohlcv_5y_extension_correction_v9_34_1_manifest.json"),
    "v9_34_report": Path("reports/data/ohlcv_5y_extension_v9_34.json"),
    "v9_33_report": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json"),
    "v9_32_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_32_manifest": Path("reports/manifests/aggtrades_5y_full_coverage_validation_v9_32_manifest.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "v9_29_validation": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

DERIVED_COLUMNS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "ohlcv_source_type",
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
    "source_aggtrades_window_start",
    "source_aggtrades_window_end",
    "source_aggtrades_validation_version",
    "row_valid",
    "invalid_reason",
    "derivation_run_id",
    "ohlcv_schema_version",
]

AGGTRADES_COLUMNS = ["aggregate_trade_id", "price", "quantity", "event_ts", "is_buyer_maker", "row_valid"]

ALLOWED_DECISIONS = {
    "ohlcv_from_aggtrades_5y_derivation_complete",
    "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings",
    "ohlcv_from_aggtrades_5y_derivation_partial",
    "ohlcv_from_aggtrades_5y_derivation_failed_quality",
    "ohlcv_from_aggtrades_5y_derivation_failed_storage",
    "ohlcv_from_aggtrades_5y_derivation_failed_runtime",
    "stop_ohlcv_derivation_branch",
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
    "no_combined_feature_store": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


@dataclass(frozen=True)
class TimeframeResult:
    timeframe: str
    path: str
    rows: int
    bytes: int
    days_complete: int
    days_missing: int
    first_missing_day: str | None
    invalid_rows: int
    duplicate_open_ts: int
    timestamp_gap_warnings: int
    quality_status: str


def run_ohlcv_from_aggtrades_5y_v9_35(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_and_run_v9_35(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_35(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_35(report))
    for timeframe_report in report["timeframe_reports"]:
        _write_json(root / f"reports/data/ohlcv_from_aggtrades_5y_{timeframe_report['timeframe']}_v9_35.json", timeframe_report)
    update_state_surfaces_v9_35(root, report)
    return report


def build_and_run_v9_35(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    disk_before = measure_disk_v9_34(root)
    source_coverage = inspect_aggtrades_source_coverage_v9_35(root)
    storage_blocker = disk_before["free_gib_data_mount"] < 10.0
    runtime_error: str | None = None
    timeframe_results: list[TimeframeResult] = []
    parity: dict[str, Any] = {"parity_status": "NOT_RUN", "timeframes": {}, "parity_warnings": [], "acceptable_tolerance": {"price_abs": 1e-8, "volume_abs": 1e-8}, "blocking_mismatches": []}
    if not storage_blocker and source_coverage["days_missing"] == 0:
        try:
            derived_1m = derive_or_reuse_1m_window_v9_35(root)
            timeframe_results.append(write_and_validate_timeframe_v9_35(root, "1m", derived_1m))
            for timeframe in ("5m", "15m", "1h"):
                frame = resample_derived_ohlcv_v9_35(derived_1m, timeframe)
                timeframe_results.append(write_and_validate_timeframe_v9_35(root, timeframe, frame))
            parity = compare_with_existing_binance_ohlcv_v9_35(root, {result.timeframe: derived_output_path_v9_35(root, result.timeframe) for result in timeframe_results})
        except Exception as exc:  # noqa: BLE001
            runtime_error = str(exc)
    disk_after = measure_disk_v9_34(root)
    quality_status = decide_quality_status_v9_35(timeframe_results, source_coverage, runtime_error, storage_blocker)
    zero_trade_counts = {result.timeframe: count_zero_trade_buckets_v9_35(derived_output_path_v9_35(root, result.timeframe)) for result in timeframe_results}
    warnings = build_warnings_v9_35(timeframe_results, parity, source_coverage, storage_blocker, runtime_error, zero_trade_counts)
    decision = decide_v9_35(quality_status, timeframe_results, warnings, storage_blocker, runtime_error)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {"ohlcv_from_aggtrades_5y_derivation_complete", "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings", "ohlcv_from_aggtrades_5y_derivation_partial"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "timeframes_required": list(TIMEFRAMES),
        "method": {
            "source": "validated silver aggTrades",
            "source_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
            "ohlcv_source_type": "derived_from_aggtrades",
            "derivation": "1m buckets are derived directly from aggTrades ordered by event_ts then aggregate_trade_id; 5m/15m/1h buckets are deterministic resamples of the derived 1m bars.",
            "causality": "Each candle uses only aggTrades with event_ts inside the candle interval; decision_ts and available_ts equal close_ts.",
            "network_used": False,
        },
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "disk_preflight": disk_before,
        "disk_after": disk_after,
        "source_aggtrades_coverage": source_coverage,
        "storage_blocker": storage_blocker,
        "runtime_error": runtime_error,
        "timeframe_reports": [result.__dict__ for result in timeframe_results],
        "zero_trade_bucket_counts": zero_trade_counts,
        "timeframes_produced": [result.timeframe for result in timeframe_results],
        "row_counts": {result.timeframe: result.rows for result in timeframe_results},
        "days_complete_by_timeframe": {result.timeframe: result.days_complete for result in timeframe_results},
        "days_missing_by_timeframe": {result.timeframe: result.days_missing for result in timeframe_results},
        "quality_status": quality_status,
        "coverage_status": "target_5y_window_complete" if all(result.days_missing == 0 for result in timeframe_results) and len(timeframe_results) == len(TIMEFRAMES) else "target_5y_window_incomplete",
        "parity_comparison": parity,
        "warnings": warnings,
        "decision": decision["decision"],
        "v9_35_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "feature_store_created": False,
        "combined_feature_store_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": bool(timeframe_results),
        "ingestion_scope": "local_derived_ohlcv_from_validated_aggtrades_only" if timeframe_results else "none",
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
        "blockers": build_blockers_v9_35(source_coverage, storage_blocker, runtime_error, quality_status),
        "limitations": [
            "V9.35 produit uniquement une base OHLCV derivee depuis aggTrades et ne cree pas de feature store combine OHLCV + aggTrades.",
            "La parite avec les klines Binance existantes est documentee comme controle de coherence, pas comme source de verite.",
            "Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre n'est produit.",
        ],
    }
    return report


def derive_1m_window_from_aggtrades_v9_35(root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for day in date_range_v9_35(TARGET_WINDOW_START, TARGET_WINDOW_END):
        source_path = aggtrades_silver_path_v9_35(root, day)
        frame = pd.read_parquet(source_path, columns=AGGTRADES_COLUMNS, engine="pyarrow")
        frames.append(derive_1m_day_from_aggtrades_v9_35(frame, day=day))
    return fill_zero_trade_buckets_v9_35(pd.concat(frames, ignore_index=True), timeframe="1m")


def derive_or_reuse_1m_window_v9_35(root: Path) -> pd.DataFrame:
    path = derived_output_path_v9_35(root, "1m")
    if path.is_file() and path.stat().st_size > 0:
        frame = pd.read_parquet(path, engine="pyarrow")
        if set(DERIVED_COLUMNS).issubset(frame.columns):
            return fill_zero_trade_buckets_v9_35(frame[DERIVED_COLUMNS], timeframe="1m")
    return derive_1m_window_from_aggtrades_v9_35(root)


def derive_1m_day_from_aggtrades_v9_35(frame: pd.DataFrame, *, day: str) -> pd.DataFrame:
    required = set(AGGTRADES_COLUMNS)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing aggTrades columns for {day}: {missing}")
    work = frame.copy()
    work = work[work["row_valid"] == True].copy()  # noqa: E712
    work["event_ts"] = pd.to_datetime(work["event_ts"], utc=True)
    work["price"] = work["price"].astype("float64")
    work["quantity"] = work["quantity"].astype("float64")
    work["quote"] = work["price"] * work["quantity"]
    work["taker_buy_base"] = work["quantity"].where(~work["is_buyer_maker"].astype(bool), 0.0)
    work["taker_buy_quote"] = work["quote"].where(~work["is_buyer_maker"].astype(bool), 0.0)
    work = work.sort_values(["event_ts", "aggregate_trade_id"], kind="mergesort")
    work["open_ts"] = work["event_ts"].dt.floor("1min")
    grouped = work.groupby("open_ts", sort=True)
    out = grouped.agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("quantity", "sum"),
        quote_volume=("quote", "sum"),
        trades_count=("price", "size"),
        taker_buy_base_volume=("taker_buy_base", "sum"),
        taker_buy_quote_volume=("taker_buy_quote", "sum"),
    ).reset_index()
    expected = pd.date_range(day, periods=1440, freq="1min", tz="UTC")
    out = out.set_index("open_ts").reindex(expected).rename_axis("open_ts").reset_index()
    missing_mask = out["open"].isna()
    if bool(missing_mask.any()):
        out["row_valid"] = ~missing_mask
        out["invalid_reason"] = missing_mask.map(lambda value: "empty_bucket_no_aggtrades" if value else "")
    else:
        out["row_valid"] = True
        out["invalid_reason"] = ""
    return finalize_ohlcv_frame_v9_35(out, timeframe="1m")


def resample_derived_ohlcv_v9_35(frame_1m: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    work = frame_1m[frame_1m["row_valid"] == True].copy()  # noqa: E712
    work = work.sort_values("open_ts", kind="mergesort")
    work["bucket"] = pd.to_datetime(work["open_ts"], utc=True).dt.floor(TIMEFRAME_FREQ[timeframe])
    grouped = work.groupby("bucket", sort=True)
    out = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        quote_volume=("quote_volume", "sum"),
        trades_count=("trades_count", "sum"),
        taker_buy_base_volume=("taker_buy_base_volume", "sum"),
        taker_buy_quote_volume=("taker_buy_quote_volume", "sum"),
    ).reset_index().rename(columns={"bucket": "open_ts"})
    expected = pd.date_range(TARGET_WINDOW_START, periods=EXPECTED_ROWS_BY_TIMEFRAME[timeframe], freq=TIMEFRAME_FREQ[timeframe], tz="UTC")
    out = out.set_index("open_ts").reindex(expected).rename_axis("open_ts").reset_index()
    missing_mask = out["open"].isna()
    if bool(missing_mask.any()):
        out["row_valid"] = ~missing_mask
        out["invalid_reason"] = missing_mask.map(lambda value: "empty_bucket_no_1m_source" if value else "")
    else:
        out["row_valid"] = True
        out["invalid_reason"] = ""
    return fill_zero_trade_buckets_v9_35(finalize_ohlcv_frame_v9_35(out, timeframe=timeframe), timeframe=timeframe)


def fill_zero_trade_buckets_v9_35(frame: pd.DataFrame, *, timeframe: str) -> pd.DataFrame:
    out = frame.sort_values("open_ts", kind="mergesort").reset_index(drop=True).copy()
    missing_mask = out["row_valid"] != True  # noqa: E712
    if not bool(missing_mask.any()):
        return out[DERIVED_COLUMNS]
    previous_close = out["close"].ffill()
    missing_indexes = out.index[missing_mask]
    if bool(previous_close.loc[missing_indexes].isna().any()):
        return out[DERIVED_COLUMNS]
    for column in ["open", "high", "low", "close"]:
        out.loc[missing_mask, column] = previous_close.loc[missing_indexes].to_numpy()
    for column in ["volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]:
        out.loc[missing_mask, column] = 0.0
    out.loc[missing_mask, "trades_count"] = 0
    out.loc[missing_mask, "row_valid"] = True
    out.loc[missing_mask, "invalid_reason"] = ""
    return out[DERIVED_COLUMNS]


def count_zero_trade_buckets_v9_35(path: Path) -> int:
    if not path.is_file():
        return 0
    frame = pd.read_parquet(path, columns=["trades_count"], engine="pyarrow")
    return int((frame["trades_count"].astype("int64") == 0).sum())


def finalize_ohlcv_frame_v9_35(frame: pd.DataFrame, *, timeframe: str) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = open_ts + TIMEFRAME_DELTAS[timeframe] - pd.Timedelta(milliseconds=1)
    out["source"] = SOURCE
    out["venue"] = VENUE
    out["market_type"] = MARKET_TYPE
    out["symbol"] = SYMBOL
    out["timeframe"] = timeframe
    out["ohlcv_source_type"] = "derived_from_aggtrades"
    out["open_ts"] = open_ts
    out["close_ts"] = close_ts
    out["event_ts"] = open_ts
    out["decision_ts"] = close_ts
    out["available_ts"] = close_ts
    for column in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]:
        out[column] = frame[column].astype("float64")
    out["trades_count"] = frame["trades_count"].fillna(0).astype("int64")
    out["source_aggtrades_window_start"] = open_ts
    out["source_aggtrades_window_end"] = close_ts
    out["source_aggtrades_validation_version"] = SOURCE_AGGTRADES_VALIDATION_VERSION
    out["row_valid"] = frame["row_valid"].astype(bool)
    out["invalid_reason"] = frame["invalid_reason"].astype("string").fillna("")
    out["derivation_run_id"] = DERIVATION_RUN_ID
    out["ohlcv_schema_version"] = SCHEMA_VERSION
    return out[DERIVED_COLUMNS]


def write_and_validate_timeframe_v9_35(root: Path, timeframe: str, frame: pd.DataFrame) -> TimeframeResult:
    path = derived_output_path_v9_35(root, timeframe)
    write_parquet(frame[DERIVED_COLUMNS], path)
    validation = validate_derived_ohlcv_frame_v9_35(frame, timeframe=timeframe)
    return TimeframeResult(
        timeframe=timeframe,
        path=path.as_posix(),
        rows=int(len(frame)),
        bytes=path.stat().st_size,
        days_complete=validation["days_complete"],
        days_missing=validation["days_missing"],
        first_missing_day=validation["first_missing_day"],
        invalid_rows=validation["invalid_rows"],
        duplicate_open_ts=validation["duplicate_open_ts"],
        timestamp_gap_warnings=validation["timestamp_gap_warnings"],
        quality_status=validation["quality_status"],
    )


def validate_derived_ohlcv_frame_v9_35(frame: pd.DataFrame, *, timeframe: str) -> dict[str, Any]:
    errors: list[str] = []
    missing_columns = sorted(set(DERIVED_COLUMNS) - set(frame.columns))
    if missing_columns:
        return {"quality_status": "FAIL", "errors": [f"missing columns: {missing_columns}"], "days_complete": 0, "days_missing": EXPECTED_DAYS, "first_missing_day": TARGET_WINDOW_START, "invalid_rows": len(frame), "duplicate_open_ts": 0, "timestamp_gap_warnings": 0}
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if len(frame) != expected_rows:
        errors.append(f"rows {len(frame)} != expected_rows {expected_rows}")
    duplicate_open_ts = int(open_ts.duplicated().sum())
    if duplicate_open_ts:
        errors.append(f"duplicate_open_ts={duplicate_open_ts}")
    if not open_ts.is_monotonic_increasing:
        errors.append("open_ts_not_monotone")
    timestamp_gap_warnings = int((open_ts.diff().dropna() != TIMEFRAME_DELTAS[timeframe]).sum())
    if timestamp_gap_warnings:
        errors.append(f"timestamp_gap_warnings={timestamp_gap_warnings}")
    invalid_rows = int((frame["row_valid"] != True).sum())  # noqa: E712
    if invalid_rows:
        errors.append(f"invalid_rows={invalid_rows}")
    for column in ["open", "high", "low", "close"]:
        count = int((frame[column].astype("float64") <= 0).sum())
        if count:
            errors.append(f"non_positive_{column}={count}")
    for column in ["volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]:
        count = int((frame[column].astype("float64") < 0).sum())
        if count:
            errors.append(f"negative_{column}={count}")
    high = frame["high"].astype("float64")
    low = frame["low"].astype("float64")
    open_ = frame["open"].astype("float64")
    close = frame["close"].astype("float64")
    high_violations = int((high < pd.concat([open_, close, low], axis=1).max(axis=1)).sum())
    low_violations = int((low > pd.concat([open_, close, high], axis=1).min(axis=1)).sum())
    if high_violations:
        errors.append(f"high_invariant_violations={high_violations}")
    if low_violations:
        errors.append(f"low_invariant_violations={low_violations}")
    if not bool((available_ts >= close_ts).all()):
        errors.append("available_ts_before_close_ts")
    dates = set(open_ts.dt.date.astype(str))
    expected_dates = set(date_range_v9_35(TARGET_WINDOW_START, TARGET_WINDOW_END))
    missing_days = sorted(expected_dates - dates)
    return {
        "quality_status": "PASS" if not errors and not missing_days else "FAIL",
        "errors": errors,
        "days_complete": EXPECTED_DAYS - len(missing_days),
        "days_missing": len(missing_days),
        "first_missing_day": missing_days[0] if missing_days else None,
        "invalid_rows": invalid_rows,
        "duplicate_open_ts": duplicate_open_ts,
        "timestamp_gap_warnings": timestamp_gap_warnings,
    }


def inspect_aggtrades_source_coverage_v9_35(root: Path) -> dict[str, Any]:
    expected = date_range_v9_35(TARGET_WINDOW_START, TARGET_WINDOW_END)
    present: list[str] = []
    missing: list[str] = []
    total_bytes = 0
    for day in expected:
        path = aggtrades_silver_path_v9_35(root, day)
        if path.is_file() and path.stat().st_size > 0:
            present.append(day)
            total_bytes += path.stat().st_size
        else:
            missing.append(day)
    return {
        "source_type": "silver_public_trades_aggtrades",
        "source_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "days_expected": len(expected),
        "days_present": len(present),
        "days_missing": len(missing),
        "first_missing_day": missing[0] if missing else None,
        "coverage_start": present[0] if present else None,
        "coverage_end": present[-1] if present else None,
        "silver_bytes": total_bytes,
    }


def compare_with_existing_binance_ohlcv_v9_35(root: Path, derived_paths: dict[str, Path]) -> dict[str, Any]:
    result = {"parity_status": "PASS", "timeframes": {}, "parity_warnings": [], "acceptable_tolerance": {"price_abs": 1e-8, "volume_abs": 1e-8}, "blocking_mismatches": []}
    for timeframe, derived_path in derived_paths.items():
        existing_path = root / f"data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2023-03-25_2026-05-23/ohlcv.parquet"
        if not existing_path.is_file():
            result["timeframes"][timeframe] = {"parity_status": "NOT_AVAILABLE", "existing_path": existing_path.as_posix()}
            result["parity_warnings"].append(f"{timeframe}: existing Binance OHLCV research window not available")
            continue
        try:
            existing = pd.read_parquet(existing_path, engine="pyarrow")
            derived = pd.read_parquet(derived_path, engine="pyarrow")
            if "open_ts" not in existing.columns and "event_ts" in existing.columns:
                existing["open_ts"] = existing["event_ts"]
            existing["open_ts"] = pd.to_datetime(existing["open_ts"], utc=True)
            derived["open_ts"] = pd.to_datetime(derived["open_ts"], utc=True)
            start = pd.Timestamp("2023-03-25", tz="UTC")
            end = pd.Timestamp("2026-05-06", tz="UTC")
            existing = existing[(existing["open_ts"] >= start) & (existing["open_ts"] < end)].sort_values("open_ts")
            derived = derived[(derived["open_ts"] >= start) & (derived["open_ts"] < end)].sort_values("open_ts")
            merged = existing[["open_ts", "close", "volume", "high", "low"]].merge(
                derived[["open_ts", "close", "volume", "high", "low"]],
                on="open_ts",
                how="inner",
                suffixes=("_binance", "_derived"),
            )
            summary = {
                "parity_status": "PASS",
                "existing_rows": int(len(existing)),
                "derived_rows": int(len(derived)),
                "matched_rows": int(len(merged)),
                "row_count_delta": int(len(derived) - len(existing)),
                "max_close_abs_diff": float((merged["close_binance"] - merged["close_derived"]).abs().max()) if len(merged) else None,
                "max_volume_abs_diff": float((merged["volume_binance"] - merged["volume_derived"]).abs().max()) if len(merged) else None,
                "max_high_abs_diff": float((merged["high_binance"] - merged["high_derived"]).abs().max()) if len(merged) else None,
                "max_low_abs_diff": float((merged["low_binance"] - merged["low_derived"]).abs().max()) if len(merged) else None,
            }
            if summary["row_count_delta"] != 0 or summary["matched_rows"] != summary["derived_rows"]:
                summary["parity_status"] = "WARNING"
                result["parity_warnings"].append(f"{timeframe}: row parity differs on overlap")
            result["timeframes"][timeframe] = summary
        except Exception as exc:  # noqa: BLE001
            result["timeframes"][timeframe] = {"parity_status": "ERROR", "error": str(exc)}
            result["parity_warnings"].append(f"{timeframe}: parity comparison failed")
    if result["parity_warnings"]:
        result["parity_status"] = "WARNING"
    return result


def decide_quality_status_v9_35(results: list[TimeframeResult], source_coverage: dict[str, Any], runtime_error: str | None, storage_blocker: bool) -> str:
    if storage_blocker or runtime_error or source_coverage["days_missing"]:
        return "FAIL"
    if len(results) != len(TIMEFRAMES):
        return "INCOMPLETE"
    if any(result.quality_status != "PASS" for result in results):
        return "FAIL"
    return "PASS"


def decide_v9_35(quality_status: str, results: list[TimeframeResult], warnings: list[str], storage_blocker: bool, runtime_error: str | None) -> dict[str, str]:
    if storage_blocker:
        return {"decision": "ohlcv_from_aggtrades_5y_derivation_failed_storage", "next_recommendation": "V9.36 - Storage Review Before OHLCV Derivation", "justification": "Espace disque insuffisant pour la derivation locale."}
    if runtime_error:
        return {"decision": "ohlcv_from_aggtrades_5y_derivation_failed_runtime", "next_recommendation": "V9.36 - OHLCV Derivation Correction", "justification": "La derivation a leve une exception runtime."}
    if quality_status == "FAIL":
        return {"decision": "ohlcv_from_aggtrades_5y_derivation_failed_quality", "next_recommendation": "V9.36 - OHLCV Derivation Correction", "justification": "La sortie derivee echoue les controles qualite."}
    if len(results) != len(TIMEFRAMES):
        return {"decision": "ohlcv_from_aggtrades_5y_derivation_partial", "next_recommendation": "V9.36 - OHLCV Derivation Correction", "justification": "Tous les timeframes n'ont pas ete produits."}
    if warnings:
        return {"decision": "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings", "next_recommendation": "V9.36 - OHLCV From AggTrades 5Y Coverage Validation", "justification": "Les 4 timeframes sont produits avec warnings non bloquants."}
    return {"decision": "ohlcv_from_aggtrades_5y_derivation_complete", "next_recommendation": "V9.36 - OHLCV From AggTrades 5Y Coverage Validation", "justification": "Les 4 timeframes OHLCV derives sont produits et valides."}


def build_warnings_v9_35(results: list[TimeframeResult], parity: dict[str, Any], source_coverage: dict[str, Any], storage_blocker: bool, runtime_error: str | None, zero_trade_counts: dict[str, int] | None = None) -> list[str]:
    warnings: list[str] = []
    if storage_blocker:
        warnings.append("storage_blocker_before_derivation")
    if runtime_error:
        warnings.append("runtime_error_during_derivation")
    if source_coverage["days_missing"]:
        warnings.append("aggtrades_source_missing_days")
    for result in results:
        if result.quality_status != "PASS":
            warnings.append(f"{result.timeframe}_quality_not_pass")
    for timeframe, count in (zero_trade_counts or {}).items():
        if count:
            warnings.append(f"{timeframe}: {count} zero-trade buckets filled causally from previous close")
    warnings.extend(parity.get("parity_warnings", []))
    return warnings


def build_blockers_v9_35(source_coverage: dict[str, Any], storage_blocker: bool, runtime_error: str | None, quality_status: str) -> list[str]:
    blockers: list[str] = []
    if storage_blocker:
        blockers.append("storage_blocker")
    if runtime_error:
        blockers.append("runtime_error")
    if source_coverage["days_missing"]:
        blockers.append("aggtrades_source_missing_days")
    if quality_status == "FAIL":
        blockers.append("quality_failure")
    return blockers


def build_manifest_v9_35(report: dict[str, Any]) -> dict[str, Any]:
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
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "timeframes_produced": report["timeframes_produced"],
        "row_counts": report["row_counts"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "feature_store_created": report["feature_store_created"],
        "combined_feature_store_created": report["combined_feature_store_created"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_35(report: dict[str, Any]) -> str:
    lines = [
        "# V9.35 - OHLCV From AggTrades 5Y Derivation",
        "",
        "## Resume",
        f"- Decision V9.35 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Timeframes produits : `{report['timeframes_produced']}`.",
        f"- Row counts : `{report['row_counts']}`.",
        f"- Buckets zero-trade remplis causalement : `{report['zero_trade_bucket_counts']}`.",
        "",
        "## Methode",
        "- Les bougies 1m sont derivees directement depuis les aggTrades silver valides V9.32, ordonnes par `event_ts` puis `aggregate_trade_id`.",
        "- Les bougies 5m/15m/1h sont derivees par resampling deterministe du 1m derive.",
        "- `decision_ts` et `available_ts` sont fixes a `close_ts`, sans donnees futures.",
        "- `ohlcv_source_type = derived_from_aggtrades` distingue explicitement cette base des klines Binance.",
        "",
        "## Parite Binance",
        f"- Statut parite : `{report['parity_comparison']['parity_status']}`.",
        f"- Warnings : `{report['parity_comparison']['parity_warnings']}`.",
        "",
        "## Garde-fous",
        "- Aucun reseau, aucun telechargement, aucun feature store combine, aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.",
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_35(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_35_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "timeframes_produced": report["timeframes_produced"],
        "row_counts": report["row_counts"],
        "feature_store_created": False,
        "combined_feature_store_created": False,
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
        "# Synthese courante - V9.35\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.35 : `{report['decision']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        f"- Couverture : `{report['coverage_status']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun reseau, feature store combine, label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, derivation OHLCV 5Y depuis aggTrades.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, feature store combine, modele persistant, API privee ou cle API.\n",
    )


def aggtrades_silver_path_v9_35(root: Path, day: str) -> Path:
    return root / f"data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date={day}/agg_trades.parquet"


def derived_output_path_v9_35(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_35/ohlcv_from_aggtrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}/ohlcv.parquet"


def date_range_v9_35(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)
    days: list[str] = []
    while current <= last:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


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
