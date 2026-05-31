from __future__ import annotations

import gc
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.derivatives_funding_oi_feature_store_v9_54_schemas import (
    AUDIT_COLUMNS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_TOKENS,
    MARKET_TYPE,
    METADATA_COLUMNS,
    SOURCE,
    STRICT_COLUMNS,
    SYMBOL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VENUE,
)


VERSION = "V9.54"
SOURCE_VERSION = "V9.53"
DIRECTION = "derivatives_funding_oi_feature_store"
REPORT_JSON_PATH = Path("reports/features/derivatives_funding_oi_feature_store_v9_54.json")
REPORT_MD_PATH = Path("reports/features/derivatives_funding_oi_feature_store_v9_54.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_funding_oi_feature_store_v9_54_manifest.json")
DOC_PATH = Path("docs/derivatives_funding_oi_feature_store_v9_54.md")
V9_53_REPORT_PATH = Path("reports/data/derivatives_funding_oi_collection_v9_53.json")
FUNDING_SILVER_PATH = Path("data/silver/derivatives/binance_archive/futures_um/BTCUSDT/fundingRate/window=2021-05-05_2026-05-05/funding_rate.parquet")
BASE_FEATURE_ROOT = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
OUTPUT_ROOT = Path("data/research/v9_54/features/derivatives_funding_oi/source=binance_archive/market_type=futures_um/symbol=BTCUSDT")

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
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_derivatives_funding_oi_feature_store_v9_54(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    run_id = f"v9_54_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    collection_report = _read_json(root / V9_53_REPORT_PATH)
    preflight = build_preflight_v9_54(root, collection_report)
    output_paths = {timeframe: feature_output_path_v9_54(root, timeframe) for timeframe in EXPECTED_TIMEFRAMES}
    timeframe_reports: dict[str, dict[str, Any]] = {}
    if preflight["safe_to_run"]:
        workers = min(int(os.environ.get("GALAPAGOS_V9_54_WORKERS", "4")), len(EXPECTED_TIMEFRAMES))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(build_timeframe_derivatives_features_v9_54, root, timeframe, run_id): timeframe
                for timeframe in EXPECTED_TIMEFRAMES
            }
            for future in as_completed(futures):
                timeframe = futures[future]
                timeframe_reports[timeframe] = future.result()
                print(f"[V9.54] timeframe_done={timeframe} status={timeframe_reports[timeframe]['quality_status']}", flush=True)
    else:
        for timeframe in EXPECTED_TIMEFRAMES:
            timeframe_reports[timeframe] = _blocked_timeframe_report(timeframe, output_paths[timeframe], preflight)
    timeframe_reports = {timeframe: timeframe_reports[timeframe] for timeframe in EXPECTED_TIMEFRAMES}
    report = build_report_v9_54(
        root=root,
        collection_report=collection_report,
        preflight=preflight,
        output_paths=output_paths,
        timeframe_reports=timeframe_reports,
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_54(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_54(report))
    return report


def build_timeframe_derivatives_features_v9_54(root: Path, timeframe: str, run_id: str) -> dict[str, Any]:
    base_path = base_feature_path_v9_54(root, timeframe)
    output_path = feature_output_path_v9_54(root, timeframe)
    if not base_path.exists():
        return _failed_timeframe_report(timeframe, output_path, ["missing source V9.47 feature store"])
    funding = pd.read_parquet(root / FUNDING_SILVER_PATH, engine="pyarrow")
    funding_events = build_funding_event_features_v9_54(funding)
    base = pd.read_parquet(base_path, columns=["event_ts", "open_ts", "close_ts", "decision_ts"], engine="pyarrow").sort_values("decision_ts", kind="mergesort").reset_index(drop=True)
    features = align_funding_to_timeframe_v9_54(base, funding_events, timeframe=timeframe, run_id=run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    report = validate_derivatives_feature_frame_v9_54(features, timeframe=timeframe, output_path=output_path)
    del base
    del features
    gc.collect()
    return report


def build_funding_event_features_v9_54(funding: pd.DataFrame) -> pd.DataFrame:
    events = funding.copy()
    events["funding_time"] = pd.to_datetime(events["funding_time"], utc=True)
    events["available_ts"] = pd.to_datetime(events["available_ts"], utc=True)
    events["funding_rate"] = pd.to_numeric(events["funding_rate"], errors="coerce")
    events = events.sort_values("funding_time", kind="mergesort").reset_index(drop=True)
    rate = events["funding_rate"].astype(float)
    previous = rate.shift(1).fillna(rate)
    rolling_mean_past = rate.shift(1).rolling(9, min_periods=1).mean()
    rolling_std_past = rate.shift(1).rolling(9, min_periods=2).std().replace(0, np.nan)
    events["funding_rate_current"] = rate
    events["funding_rate_last"] = previous
    events["funding_rate_change_1"] = rate - previous
    events["funding_rate_abs"] = rate.abs()
    events["funding_rate_sign"] = np.sign(rate).astype("int8")
    events["funding_rate_rolling_mean_3"] = rate.rolling(3, min_periods=1).mean()
    events["funding_rate_rolling_mean_9"] = rate.rolling(9, min_periods=1).mean()
    events["funding_rate_rolling_std_9"] = rate.rolling(9, min_periods=2).std().fillna(0.0)
    events["funding_rate_zscore_past"] = ((rate - rolling_mean_past) / rolling_std_past).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    positive_streak: list[int] = []
    negative_streak: list[int] = []
    pos = 0
    neg = 0
    for value in rate:
        pos = pos + 1 if value > 0 else 0
        neg = neg + 1 if value < 0 else 0
        positive_streak.append(pos)
        negative_streak.append(neg)
    events["funding_rate_positive_streak"] = positive_streak
    events["funding_rate_negative_streak"] = negative_streak
    return events[["funding_time", "available_ts", *[column for column in FEATURE_COLUMNS if column.startswith("funding_rate_")]]]


def align_funding_to_timeframe_v9_54(base: pd.DataFrame, funding_events: pd.DataFrame, *, timeframe: str, run_id: str) -> pd.DataFrame:
    left = base.copy()
    for column in ["event_ts", "open_ts", "close_ts", "decision_ts"]:
        left[column] = pd.to_datetime(left[column], utc=True)
    right = funding_events.rename(columns={"available_ts": "funding_available_ts"}).sort_values("funding_available_ts", kind="mergesort")
    merged = pd.merge_asof(
        left.sort_values("decision_ts", kind="mergesort"),
        right,
        left_on="decision_ts",
        right_on="funding_available_ts",
        direction="backward",
        allow_exact_matches=True,
    )
    missing = merged["funding_time"].isna()
    feature_available = merged["funding_available_ts"].where(~missing, merged["decision_ts"])
    output = pd.DataFrame(
        {
            "source": SOURCE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "event_ts": merged["event_ts"],
            "open_ts": merged["open_ts"],
            "close_ts": merged["close_ts"],
            "decision_ts": merged["decision_ts"],
            "available_ts": feature_available,
            "feature_available_ts": feature_available,
            "derivatives_feature_run_id": run_id,
            "derivatives_feature_schema_version": FEATURE_SCHEMA_VERSION,
            "source_collection_version": "V9.53",
            "source_window_start": TARGET_WINDOW_START,
            "source_window_end": TARGET_WINDOW_END,
            "actual_window_start": TARGET_WINDOW_START,
            "actual_window_end": TARGET_WINDOW_END,
        }
    )
    for column in FEATURE_COLUMNS:
        if column in merged.columns:
            output[column] = pd.to_numeric(merged[column], errors="coerce")
        elif column == "hours_since_last_funding":
            output[column] = (merged["decision_ts"] - merged["funding_time"]).dt.total_seconds() / 3600.0
        elif column == "hours_to_next_funding_known_schedule":
            output[column] = ((merged["funding_time"] + pd.Timedelta(hours=8)) - merged["decision_ts"]).dt.total_seconds() / 3600.0
        elif column == "funding_missing_flag":
            output[column] = missing.astype("int8")
        elif column == "oi_missing_flag":
            output[column] = 1
        elif column == "premium_missing_flag":
            output[column] = 1
        else:
            output[column] = 0.0
    output["hours_since_last_funding"] = output["hours_since_last_funding"].fillna(-1.0)
    output["hours_to_next_funding_known_schedule"] = output["hours_to_next_funding_known_schedule"].fillna(-1.0).clip(lower=-1.0)
    numeric_features = output[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    output[FEATURE_COLUMNS] = numeric_features.fillna(0.0)
    leakage = pd.to_datetime(output["feature_available_ts"], utc=True) > pd.to_datetime(output["decision_ts"], utc=True)
    output["derivatives_feature_null_count"] = output[FEATURE_COLUMNS].isna().sum(axis=1).astype("int64")
    output["derivatives_feature_error_count"] = leakage.astype("int64")
    output["row_valid_for_derivatives_features"] = (
        (output["funding_missing_flag"].astype(int) == 0)
        & (output["derivatives_feature_null_count"] == 0)
        & (output["derivatives_feature_error_count"] == 0)
    )
    output["derivatives_feature_invalid_reason"] = ""
    output.loc[output["funding_missing_flag"].astype(int) == 1, "derivatives_feature_invalid_reason"] = "funding_missing"
    output.loc[leakage, "derivatives_feature_invalid_reason"] = "feature_available_ts_after_decision_ts"
    return output[STRICT_COLUMNS]


def validate_derivatives_feature_frame_v9_54(frame: pd.DataFrame, *, timeframe: str, output_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if len(frame) != expected_rows:
        errors.append("row count mismatch")
    duplicate_open_ts = int(frame["open_ts"].duplicated().sum())
    if duplicate_open_ts:
        errors.append("duplicate open_ts")
    leakage_count = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    if leakage_count:
        errors.append("feature availability leakage")
    forbidden = forbidden_columns_v9_54(frame.columns)
    if forbidden:
        errors.append("forbidden columns present")
    invalid_rows = int((~frame["row_valid_for_derivatives_features"].astype(bool)).sum())
    if invalid_rows:
        errors.append("invalid derivatives feature rows")
    funding_missing_rows = int(frame["funding_missing_flag"].sum())
    if funding_missing_rows:
        errors.append("funding missing rows")
    coverage_ok = len(frame) > 0 and str(frame["open_ts"].iloc[0]) == "2021-05-05 00:00:00+00:00" and str(frame["close_ts"].iloc[-1]) == "2026-05-06 00:00:00+00:00"
    if not coverage_ok:
        errors.append("coverage boundary mismatch")
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "duplicate_open_ts": duplicate_open_ts,
        "feature_available_ts_lte_decision_ts": leakage_count == 0,
        "leakage_count": leakage_count,
        "forbidden_columns": forbidden,
        "invalid_rows": invalid_rows,
        "funding_missing_rows": funding_missing_rows,
        "oi_missing_rows": int(frame["oi_missing_flag"].sum()),
        "premium_missing_rows": int(frame["premium_missing_flag"].sum()),
        "feature_null_count": int(frame[FEATURE_COLUMNS].isna().sum().sum()),
        "warnings": warnings,
        "errors": errors,
        "coverage_status": "PASS" if coverage_ok and len(frame) == expected_rows else "FAIL",
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS and not forbidden else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
    }


def build_preflight_v9_54(root: Path, collection_report: dict[str, Any]) -> dict[str, Any]:
    base_files = {timeframe: base_feature_path_v9_54(root, timeframe).is_file() for timeframe in EXPECTED_TIMEFRAMES}
    funding_exists = (root / FUNDING_SILVER_PATH).is_file()
    collection_ready = collection_report.get("decision") in {"funding_collection_complete", "funding_collection_complete_oi_not_ready"}
    errors = []
    if not collection_ready:
        errors.append("V9.53 collection report is not successful")
    if not funding_exists:
        errors.append("funding silver file missing")
    missing_base = [timeframe for timeframe, exists in base_files.items() if not exists]
    if missing_base:
        errors.append(f"missing V9.47 base feature files: {missing_base}")
    return {
        "safe_to_run": not errors,
        "errors": errors,
        "collection_ready": collection_ready,
        "funding_silver_exists": funding_exists,
        "base_files_exist": base_files,
        "workers": min(int(os.environ.get("GALAPAGOS_V9_54_WORKERS", "4")), len(EXPECTED_TIMEFRAMES)),
    }


def build_report_v9_54(*, root: Path, collection_report: dict[str, Any], preflight: dict[str, Any], output_paths: dict[str, Path], timeframe_reports: dict[str, dict[str, Any]], runtime_seconds: float) -> dict[str, Any]:
    coverage_pass = all(item["coverage_status"] == "PASS" for item in timeframe_reports.values())
    schema_pass = all(item["schema_status"] == "PASS" for item in timeframe_reports.values())
    quality_pass = all(item["quality_status"] == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("feature_available_ts_lte_decision_ts") for item in timeframe_reports.values())
    decision = decide_v9_54(preflight, coverage_pass, schema_pass, quality_pass, leakage_pass)
    output_bytes = {timeframe: output_paths[timeframe].stat().st_size if output_paths[timeframe].is_file() else 0 for timeframe in EXPECTED_TIMEFRAMES}
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in {"derivatives_funding_feature_store_created", "derivatives_funding_oi_feature_store_created", "derivatives_feature_store_created_with_warnings"} else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "actual_feature_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_store_created": decision in {"derivatives_funding_feature_store_created", "derivatives_funding_oi_feature_store_created", "derivatives_feature_store_created_with_warnings"},
        "features_created": decision in {"derivatives_funding_feature_store_created", "derivatives_funding_oi_feature_store_created", "derivatives_feature_store_created_with_warnings"},
        "feature_store_paths": {timeframe: path.as_posix() for timeframe, path in output_paths.items()},
        "output_bytes": output_bytes,
        "row_counts": {timeframe: item["actual_rows"] for timeframe, item in timeframe_reports.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "funding_included": True,
        "open_interest_included": False,
        "mark_premium_included": False,
        "collection_decision": collection_report.get("decision"),
        "preflight": preflight,
        "timeframe_reports": timeframe_reports,
        "coverage_status": "target_5y_derivatives_feature_window_complete" if coverage_pass else "target_5y_derivatives_feature_window_incomplete",
        "schema_status": "PASS" if schema_pass else "FAIL",
        "quality_status": "PASS" if quality_pass else "FAIL",
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "feature_available_ts_lte_decision_ts": leakage_pass, "forward_fill_causal": True},
        "forbidden_column_scan": {"status": "PASS" if all(not item.get("forbidden_columns") for item in timeframe_reports.values()) else "FAIL"},
        "blockers": build_blockers_v9_54(preflight, timeframe_reports, coverage_pass, schema_pass, quality_pass, leakage_pass),
        "warnings": ["OI and premium/mark context are not included in this first candidate; missing flags remain explicit."],
        "limitations": [
            "Feature store funding-only; OI reste non exploitable historiquement dans V9.54.",
            "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
        ],
        "next_recommendation": "V9.55 - Funding / OI Feature Store Validation" if quality_pass and coverage_pass and schema_pass and leakage_pass else "V9.55 - Derivatives Feature Store Correction",
        "runtime_seconds": runtime_seconds,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def decide_v9_54(preflight: dict[str, Any], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> str:
    if not preflight["safe_to_run"]:
        return "derivatives_feature_store_not_created_insufficient_coverage"
    if not leakage_pass:
        return "derivatives_feature_store_blocked_by_leakage"
    if not schema_pass:
        return "derivatives_feature_store_blocked_by_alignment"
    if not quality_pass:
        return "derivatives_feature_store_blocked_by_quality"
    if not coverage_pass:
        return "derivatives_feature_store_not_created_insufficient_coverage"
    return "derivatives_funding_feature_store_created"


def build_manifest_v9_54(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "manifest_path": MANIFEST_PATH.as_posix(),
        "feature_store_paths": report["feature_store_paths"],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "network_used": False,
        "new_data_downloaded": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_54(report: dict[str, Any]) -> str:
    return (
        "# V9.54 - Derivatives Funding/OI Feature Store Candidate\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Fenetre reelle : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.\n"
        f"- Funding inclus : `{report['funding_included']}`.\n"
        f"- OI inclus : `{report['open_interest_included']}`.\n"
        f"- Timeframes : `{report['timeframes']}`.\n"
        f"- Quality : `{report['quality_status']}`.\n"
        f"- Leakage : `{report['leakage_guard']['status']}`.\n\n"
        "Feature store research-only. Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n"
    )


def feature_output_path_v9_54(root: Path, timeframe: str) -> Path:
    return root / OUTPUT_ROOT / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "features.parquet"


def base_feature_path_v9_54(root: Path, timeframe: str) -> Path:
    return root / BASE_FEATURE_ROOT / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "features.parquet"


def forbidden_columns_v9_54(columns: Any) -> list[str]:
    return sorted([column for column in columns if any(token in str(column).casefold() for token in FORBIDDEN_FEATURE_TOKENS)])


def build_blockers_v9_54(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> list[str]:
    blockers = list(preflight.get("errors", []))
    for timeframe, report in timeframe_reports.items():
        blockers.extend(f"{timeframe}: {error}" for error in report.get("errors", []))
    if not coverage_pass:
        blockers.append("coverage validation failed")
    if not schema_pass:
        blockers.append("schema validation failed")
    if not quality_pass:
        blockers.append("quality validation failed")
    if not leakage_pass:
        blockers.append("leakage validation failed")
    return blockers


def _blocked_timeframe_report(timeframe: str, output_path: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "actual_rows": 0,
        "coverage_status": "FAIL",
        "schema_status": "FAIL",
        "quality_status": "FAIL",
        "feature_available_ts_lte_decision_ts": False,
        "errors": list(preflight.get("errors", [])),
        "warnings": [],
    }


def _failed_timeframe_report(timeframe: str, output_path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "actual_rows": 0,
        "coverage_status": "FAIL",
        "schema_status": "FAIL",
        "quality_status": "FAIL",
        "feature_available_ts_lte_decision_ts": False,
        "errors": errors,
        "warnings": [],
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
