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

from galapagos.features.funding_only_feature_store_v9_57_schemas import (
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_TOKENS,
    MARKET_TYPE,
    SOURCE,
    STRICT_COLUMNS,
    SYMBOL,
    VENUE,
)
from galapagos.research.funding_tail_resolution_v9_56 import (
    load_local_funding_frame_v9_56,
    validate_funding_window_v9_56,
)


VERSION = "V9.57"
SOURCE_VERSION = "V9.56"
DIRECTION = "funding_only_feature_store_candidate"
REPORT_JSON_PATH = Path("reports/features/funding_only_feature_store_v9_57.json")
REPORT_MD_PATH = Path("reports/features/funding_only_feature_store_v9_57.md")
MANIFEST_PATH = Path("reports/manifests/funding_only_feature_store_v9_57_manifest.json")
DOC_PATH = Path("docs/funding_only_feature_store_v9_57.md")
V9_56_REPORT_PATH = Path("reports/research_decisions/funding_tail_resolution_v9_56.json")
BASE_FEATURE_ROOT = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
OUTPUT_ROOT = Path("data/research/v9_57/features/funding_only/source=binance_archive/market_type=futures_um/symbol=BTCUSDT")

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

SUCCESS_DECISIONS = {"funding_only_feature_store_created", "funding_only_feature_store_created_with_warnings"}


def run_funding_only_feature_store_v9_57(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    run_id = f"v9_57_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    source_report = _read_json(root / V9_56_REPORT_PATH)
    preflight = build_preflight_v9_57(root, source_report)
    output_paths = {timeframe: feature_output_path_v9_57(root, timeframe, source_report) for timeframe in EXPECTED_TIMEFRAMES}
    timeframe_reports: dict[str, dict[str, Any]] = {}
    if preflight["safe_to_run"]:
        workers = min(int(os.environ.get("GALAPAGOS_V9_57_WORKERS", "4")), len(EXPECTED_TIMEFRAMES))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(build_timeframe_funding_features_v9_57, root, timeframe, run_id, source_report): timeframe
                for timeframe in EXPECTED_TIMEFRAMES
            }
            for future in as_completed(futures):
                timeframe = futures[future]
                timeframe_reports[timeframe] = future.result()
                print(f"[V9.57] timeframe_done={timeframe} status={timeframe_reports[timeframe]['quality_status']}", flush=True)
    else:
        for timeframe in EXPECTED_TIMEFRAMES:
            timeframe_reports[timeframe] = _blocked_timeframe_report(timeframe, output_paths[timeframe], preflight)
    timeframe_reports = {timeframe: timeframe_reports[timeframe] for timeframe in EXPECTED_TIMEFRAMES}
    report = build_report_v9_57(
        source_report=source_report,
        preflight=preflight,
        output_paths=output_paths,
        timeframe_reports=timeframe_reports,
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_57(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_57(report))
    return report


def build_timeframe_funding_features_v9_57(root: Path, timeframe: str, run_id: str, source_report: dict[str, Any]) -> dict[str, Any]:
    base_path = base_feature_path_v9_57(root, timeframe)
    output_path = feature_output_path_v9_57(root, timeframe, source_report)
    if not base_path.exists():
        return _failed_timeframe_report(timeframe, output_path, ["missing source V9.47 feature store"])
    window = source_report["actual_feature_window"]
    start = pd.Timestamp(window["start"])
    end = pd.Timestamp(window["end"])
    funding = load_local_funding_frame_v9_56(root)
    funding_events = build_funding_event_features_v9_57(funding, start=start, end=end)
    base = pd.read_parquet(base_path, columns=["event_ts", "open_ts", "close_ts", "decision_ts"], engine="pyarrow")
    for column in ["event_ts", "open_ts", "close_ts", "decision_ts"]:
        base[column] = pd.to_datetime(base[column], utc=True)
    base = base.loc[(base["decision_ts"] > start) & (base["decision_ts"] <= end)].sort_values("decision_ts", kind="mergesort").reset_index(drop=True)
    features = align_funding_to_timeframe_v9_57(base, funding_events, timeframe=timeframe, run_id=run_id, source_report=source_report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    report = validate_funding_feature_frame_v9_57(features, timeframe=timeframe, output_path=output_path)
    del base
    del features
    gc.collect()
    return report


def build_funding_event_features_v9_57(funding: pd.DataFrame, *, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    events = funding.copy()
    events["funding_time"] = pd.to_datetime(events["funding_time"], utc=True)
    events["available_ts"] = pd.to_datetime(events["available_ts"], utc=True)
    events["funding_rate"] = pd.to_numeric(events["funding_rate"], errors="coerce")
    events["funding_interval_hours"] = pd.to_numeric(events["funding_interval_hours"], errors="coerce").fillna(8)
    events = events.loc[(events["funding_time"] >= start) & (events["funding_time"] <= end)].sort_values("funding_time", kind="mergesort").reset_index(drop=True)
    events["_rounded_funding_time"] = events["funding_time"].dt.round("s")
    events = events.drop_duplicates("_rounded_funding_time", keep="last").reset_index(drop=True)
    rate = events["funding_rate"].astype(float)
    previous = rate.shift(1).fillna(rate)
    rolling_mean_past = rate.shift(1).rolling(9, min_periods=1).mean()
    rolling_std_past = rate.shift(1).rolling(9, min_periods=2).std().replace(0, np.nan)
    gap_hours = events["funding_time"].diff().dt.total_seconds().div(3600.0)
    expected_gap = events["funding_interval_hours"].astype(float)
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
    events["funding_interval_gap_flag"] = ((gap_hours.notna()) & (gap_hours > expected_gap + 0.1)).astype("int8")
    return events[["funding_time", "available_ts", *[column for column in FEATURE_COLUMNS if column.startswith("funding_rate_")], "funding_interval_gap_flag"]]


def align_funding_to_timeframe_v9_57(
    base: pd.DataFrame,
    funding_events: pd.DataFrame,
    *,
    timeframe: str,
    run_id: str,
    source_report: dict[str, Any],
) -> pd.DataFrame:
    window = source_report["actual_feature_window"]
    right = funding_events.rename(columns={"available_ts": "funding_available_ts"}).sort_values("funding_available_ts", kind="mergesort")
    merged = pd.merge_asof(
        base.sort_values("decision_ts", kind="mergesort"),
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
            "funding_feature_run_id": run_id,
            "funding_feature_schema_version": FEATURE_SCHEMA_VERSION,
            "source_collection_version": SOURCE_VERSION,
            "source_window_start": window["start"],
            "source_window_end": window["end"],
            "actual_window_start": window["start"],
            "actual_window_end": window["end"],
            "common_window_policy": source_report.get("common_window_policy"),
        }
    )
    for column in FEATURE_COLUMNS:
        if column in merged.columns:
            output[column] = pd.to_numeric(merged[column], errors="coerce")
        elif column == "hours_since_last_funding":
            output[column] = (merged["decision_ts"] - merged["funding_time"]).dt.total_seconds() / 3600.0
        elif column == "funding_missing_flag":
            output[column] = missing.astype("int8")
        else:
            output[column] = 0.0
    output["hours_since_last_funding"] = output["hours_since_last_funding"].fillna(-1.0)
    output[FEATURE_COLUMNS] = output[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    leakage = pd.to_datetime(output["feature_available_ts"], utc=True) > pd.to_datetime(output["decision_ts"], utc=True)
    output["funding_feature_null_count"] = output[FEATURE_COLUMNS].isna().sum(axis=1).astype("int64")
    output["funding_feature_error_count"] = leakage.astype("int64")
    output["row_valid_for_funding_features"] = (
        (output["funding_missing_flag"].astype(int) == 0)
        & (output["funding_feature_null_count"] == 0)
        & (output["funding_feature_error_count"] == 0)
    )
    output["funding_feature_invalid_reason"] = ""
    output.loc[output["funding_missing_flag"].astype(int) == 1, "funding_feature_invalid_reason"] = "funding_missing"
    output.loc[leakage, "funding_feature_invalid_reason"] = "feature_available_ts_after_decision_ts"
    return output[STRICT_COLUMNS]


def validate_funding_feature_frame_v9_57(frame: pd.DataFrame, *, timeframe: str, output_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    duplicate_open_ts = int(frame["open_ts"].duplicated().sum()) if "open_ts" in frame else 0
    if duplicate_open_ts:
        errors.append("duplicate open_ts")
    leakage_count = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum()) if len(frame) else 0
    if leakage_count:
        errors.append("feature availability leakage")
    forbidden = forbidden_columns_v9_57(frame.columns)
    if forbidden:
        errors.append("forbidden columns present")
    invalid_rows = int((~frame["row_valid_for_funding_features"].astype(bool)).sum()) if len(frame) else 0
    if invalid_rows:
        errors.append("invalid funding feature rows")
    funding_missing_rows = int(frame["funding_missing_flag"].sum()) if len(frame) else 0
    if funding_missing_rows:
        errors.append("funding missing rows")
    feature_null_count = int(frame[FEATURE_COLUMNS].isna().sum().sum()) if len(frame) else 0
    if feature_null_count:
        errors.append("feature nulls")
    if frame.empty:
        errors.append("empty feature frame")
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": int(len(frame)),
        "actual_rows": int(len(frame)),
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "decision_start": str(frame["decision_ts"].iloc[0]) if len(frame) else None,
        "decision_end": str(frame["decision_ts"].iloc[-1]) if len(frame) else None,
        "duplicate_open_ts": duplicate_open_ts,
        "feature_available_ts_lte_decision_ts": leakage_count == 0,
        "leakage_count": leakage_count,
        "forbidden_columns": forbidden,
        "invalid_rows": invalid_rows,
        "funding_missing_rows": funding_missing_rows,
        "funding_interval_gap_rows": int(frame["funding_interval_gap_flag"].sum()) if len(frame) else 0,
        "feature_null_count": feature_null_count,
        "warnings": warnings,
        "errors": errors,
        "coverage_status": "PASS" if len(frame) > 0 else "FAIL",
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS and not forbidden else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
    }


def build_preflight_v9_57(root: Path, source_report: dict[str, Any]) -> dict[str, Any]:
    base_files = {timeframe: base_feature_path_v9_57(root, timeframe).is_file() for timeframe in EXPECTED_TIMEFRAMES}
    window = source_report.get("actual_feature_window", {})
    authorized = source_report.get("funding_feature_store_authorized") is True and source_report.get("decision") in {
        "funding_tail_resolved_full_target_window",
        "funding_tail_unavailable_use_closed_common_window",
    }
    errors: list[str] = []
    if not authorized:
        errors.append("V9.56 did not authorize a funding common window")
    if not window.get("start") or not window.get("end"):
        errors.append("missing actual feature window")
    missing_base = [timeframe for timeframe, exists in base_files.items() if not exists]
    if missing_base:
        errors.append(f"missing V9.47 base feature files: {missing_base}")
    funding_quality: dict[str, Any] = {}
    if window.get("start") and window.get("end"):
        funding = load_local_funding_frame_v9_56(root)
        funding_quality = validate_funding_window_v9_56(funding, start_ts=window["start"], end_ts=window["end"], expected_end_label=window["end"])
        if funding_quality.get("quality_status") != "PASS":
            errors.append("funding source is not clean on actual common window")
    return {
        "safe_to_run": not errors,
        "errors": errors,
        "source_decision": source_report.get("decision"),
        "actual_feature_window": window,
        "base_files_exist": base_files,
        "funding_quality": funding_quality,
        "workers": min(int(os.environ.get("GALAPAGOS_V9_57_WORKERS", "4")), len(EXPECTED_TIMEFRAMES)),
    }


def build_report_v9_57(
    *,
    source_report: dict[str, Any],
    preflight: dict[str, Any],
    output_paths: dict[str, Path],
    timeframe_reports: dict[str, dict[str, Any]],
    runtime_seconds: float,
) -> dict[str, Any]:
    coverage_pass = all(item["coverage_status"] == "PASS" for item in timeframe_reports.values())
    schema_pass = all(item["schema_status"] == "PASS" for item in timeframe_reports.values())
    quality_pass = all(item["quality_status"] == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("feature_available_ts_lte_decision_ts") for item in timeframe_reports.values())
    decision = decide_v9_57(preflight, coverage_pass, schema_pass, quality_pass, leakage_pass, source_report)
    output_bytes = {timeframe: output_paths[timeframe].stat().st_size if output_paths[timeframe].is_file() else 0 for timeframe in EXPECTED_TIMEFRAMES}
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "source_decision": source_report.get("decision"),
        "actual_feature_window": source_report.get("actual_feature_window"),
        "common_window_policy": source_report.get("common_window_policy"),
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_store_created": decision in SUCCESS_DECISIONS,
        "features_created": decision in SUCCESS_DECISIONS,
        "feature_store_paths": {timeframe: path.as_posix() for timeframe, path in output_paths.items()},
        "output_bytes": output_bytes,
        "row_counts": {timeframe: item["actual_rows"] for timeframe, item in timeframe_reports.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "funding_included": True,
        "open_interest_included": False,
        "preflight": preflight,
        "timeframe_reports": timeframe_reports,
        "coverage_status": "funding_common_window_feature_store_complete" if coverage_pass else "funding_common_window_feature_store_incomplete",
        "schema_status": "PASS" if schema_pass else "FAIL",
        "quality_status": "PASS" if quality_pass else "FAIL",
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "feature_available_ts_lte_decision_ts": leakage_pass, "forward_fill_causal": True, "no_future_funding": leakage_pass},
        "forbidden_column_scan": {"status": "PASS" if all(not item.get("forbidden_columns") for item in timeframe_reports.values()) else "FAIL"},
        "blockers": build_blockers_v9_57(preflight, timeframe_reports, coverage_pass, schema_pass, quality_pass, leakage_pass),
        "warnings": build_warnings_v9_57(source_report),
        "limitations": [
            "Feature store funding-only; OI n'est pas inclus car l'historique public long n'est pas pret.",
            "Fenetre commune fermee si la queue mai 2026 funding reste indisponible.",
            "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
        ],
        "next_recommendation": "V9.58 - Funding-only feature store validation" if decision in SUCCESS_DECISIONS else "V9.58 - Funding-only feature store correction",
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


def decide_v9_57(preflight: dict[str, Any], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, source_report: dict[str, Any]) -> str:
    if not preflight["safe_to_run"]:
        return "funding_only_feature_store_blocked_by_quality"
    if not leakage_pass:
        return "funding_only_feature_store_blocked_by_leakage"
    if not schema_pass:
        return "funding_only_feature_store_blocked_by_alignment"
    if not quality_pass:
        return "funding_only_feature_store_blocked_by_quality"
    if not coverage_pass:
        return "funding_only_feature_store_partial"
    if source_report.get("decision") == "funding_tail_unavailable_use_closed_common_window":
        return "funding_only_feature_store_created_with_warnings"
    return "funding_only_feature_store_created"


def build_manifest_v9_57(report: dict[str, Any]) -> dict[str, Any]:
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


def build_markdown_v9_57(report: dict[str, Any]) -> str:
    window = report.get("actual_feature_window", {})
    return (
        "# V9.57 - Feature store funding-only\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Fenetre reelle : `{window.get('start')}` -> `{window.get('end')}`.\n"
        f"- Funding inclus : `{report['funding_included']}`.\n"
        f"- OI inclus : `{report['open_interest_included']}`.\n"
        f"- Timeframes : `{report['timeframes']}`.\n"
        f"- Quality : `{report['quality_status']}`.\n"
        f"- Leakage : `{report['leakage_guard']['status']}`.\n\n"
        "Feature store research-only funding. Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n"
    )


def feature_output_path_v9_57(root: Path, timeframe: str, source_report: dict[str, Any]) -> Path:
    label = source_report.get("actual_feature_window", {}).get("label") or "no_window"
    return root / OUTPUT_ROOT / f"timeframe={timeframe}" / f"window={label}" / "features.parquet"


def base_feature_path_v9_57(root: Path, timeframe: str) -> Path:
    return root / BASE_FEATURE_ROOT / f"timeframe={timeframe}" / "window=2021-05-05_2026-05-05" / "features.parquet"


def forbidden_columns_v9_57(columns: Any) -> list[str]:
    return sorted([column for column in columns if any(token in str(column).casefold() for token in FORBIDDEN_FEATURE_TOKENS)])


def build_blockers_v9_57(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> list[str]:
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


def build_warnings_v9_57(source_report: dict[str, Any]) -> list[str]:
    warnings = ["OI not included; explicit funding-only feature layer."]
    if source_report.get("decision") == "funding_tail_unavailable_use_closed_common_window":
        warnings.append("Feature store built on closed common window because May 2026 funding tail remains unavailable.")
    return warnings


def _blocked_timeframe_report(timeframe: str, output_path: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": 0,
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
        "expected_rows": 0,
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
