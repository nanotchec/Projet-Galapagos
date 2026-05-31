from __future__ import annotations

import gc
import json
import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45 import exact_feature_output_path_v9_45
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import (
    AUDIT_COLUMNS,
    BASE_FEATURE_SCHEMA_VERSION,
    COMBINED_FEATURE_SCHEMA_VERSION,
    EXACT_FEATURE_SCHEMA_VERSION,
    EXPECTED_DAYS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_FAMILIES,
    FORBIDDEN_FEATURE_COLUMNS,
    MARKET_TYPE,
    METADATA_COLUMNS,
    SOURCE,
    SOURCE_AUDIT_COLUMNS_INHERITED_AS_FEATURES,
    STRICT_COLUMNS,
    SYMBOL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VENUE,
)


VERSION = "V9.47"
SOURCE_VERSION = "V9.46"
LAST_VALIDATED_VERSION = "V9.46"
DIRECTION = "ohlcv_aggtrades_exact_5y_feature_store"

REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_v9_47_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_5y_feature_store_v9_47.md")

INPUT_PATHS = {
    "v9_46_exact_validation": Path("reports/features/aggtrades_exact_5y_feature_enrichment_validation_v9_46.json"),
    "v9_46_manifest": Path("reports/manifests/aggtrades_exact_5y_feature_enrichment_validation_v9_46_manifest.json"),
    "v9_45_exact": Path("reports/features/aggtrades_exact_5y_feature_enrichment_v9_45.json"),
    "v9_45_manifest": Path("reports/manifests/aggtrades_exact_5y_feature_enrichment_v9_45_manifest.json"),
    "v9_38_base_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_37_base": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_42_dataset_validation": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    "v9_44_diagnostic": Path("reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
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


def run_ohlcv_aggtrades_exact_5y_feature_store_v9_47(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    run_id = f"v9_47_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    inputs = {name: _read_optional_json(root / path) for name, path in INPUT_PATHS.items()}
    preflight = build_preflight_v9_47(root, inputs)
    timeframe_reports: dict[str, dict[str, Any]] = {}
    output_paths = {timeframe: combined_feature_output_path_v9_47(root, timeframe) for timeframe in EXPECTED_TIMEFRAMES}
    if preflight["safe_to_run"] and preflight["source_reports_ready"]:
        workers = min(int(os.environ.get("GALAPAGOS_V9_47_WORKERS", "4")), len(EXPECTED_TIMEFRAMES))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(build_timeframe_combined_file_v9_47, root, timeframe, run_id): timeframe for timeframe in EXPECTED_TIMEFRAMES}
            for future in as_completed(futures):
                timeframe = futures[future]
                timeframe_reports[timeframe] = future.result()
                print(f"[V9.47] timeframe_done={timeframe} status={timeframe_reports[timeframe]['quality_status']}", flush=True)
    else:
        for timeframe in EXPECTED_TIMEFRAMES:
            timeframe_reports[timeframe] = _blocked_timeframe_report(timeframe, preflight)
    timeframe_reports = {timeframe: timeframe_reports[timeframe] for timeframe in EXPECTED_TIMEFRAMES}
    report = build_report_v9_47(
        root=root,
        inputs=inputs,
        preflight=preflight,
        timeframe_reports=timeframe_reports,
        output_paths=output_paths,
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_47(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_47(report))
    update_state_surfaces_v9_47(root, report)
    return report


def build_timeframe_combined_file_v9_47(root: Path, timeframe: str, run_id: str) -> dict[str, Any]:
    base_path = feature_output_path_v9_37(root, timeframe)
    exact_path = exact_feature_output_path_v9_45(root, timeframe)
    output_path = combined_feature_output_path_v9_47(root, timeframe)
    alignment = preflight_alignment_v9_47(base_path, exact_path, timeframe)
    if alignment["status"] != "PASS":
        return _failed_timeframe_report(timeframe, output_path, alignment, ["alignment failed"])
    base = pd.read_parquet(base_path, engine="pyarrow").sort_values("open_ts", kind="mergesort").reset_index(drop=True)
    exact = pd.read_parquet(exact_path, engine="pyarrow").sort_values("open_ts", kind="mergesort").reset_index(drop=True)
    collision_summary = column_collision_summary_v9_47(base, exact)
    combined = combine_frames_v9_47(base, exact, timeframe=timeframe, run_id=run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    report = validate_combined_frame_v9_47(combined, timeframe=timeframe, output_path=output_path)
    report["alignment"] = alignment
    report["column_collision_summary"] = collision_summary
    del base
    del exact
    del combined
    gc.collect()
    return report


def preflight_alignment_v9_47(base_path: Path, exact_path: Path, timeframe: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not base_path.is_file():
        errors.append(f"missing base feature file: {base_path}")
    if not exact_path.is_file():
        errors.append(f"missing exact feature file: {exact_path}")
    if errors:
        return {"status": "FAIL", "errors": errors, "warnings": warnings}
    base = pd.read_parquet(base_path, columns=["event_ts", "open_ts", "close_ts", "decision_ts", "feature_available_ts", "timeframe", "symbol", "source_window_start", "source_window_end"], engine="pyarrow")
    exact = pd.read_parquet(exact_path, columns=["event_ts", "open_ts", "close_ts", "decision_ts", "feature_available_ts", "timeframe", "symbol", "source_window_start", "source_window_end"], engine="pyarrow")
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if len(base) != expected_rows or len(exact) != expected_rows:
        errors.append("row count mismatch")
    for column in ["event_ts", "open_ts"]:
        if not base[column].equals(exact[column]):
            errors.append(f"{column} not aligned")
    if not bool(base["timeframe"].eq(timeframe).all() and exact["timeframe"].eq(timeframe).all()):
        errors.append("timeframe mismatch")
    if not bool(base["symbol"].eq(SYMBOL).all() and exact["symbol"].eq(SYMBOL).all()):
        errors.append("symbol mismatch")
    if int(base["event_ts"].duplicated().sum()) or int(exact["event_ts"].duplicated().sum()):
        errors.append("duplicate event_ts")
    close_delta_ms = (pd.to_datetime(exact["close_ts"], utc=True) - pd.to_datetime(base["close_ts"], utc=True)).dt.total_seconds().mul(1000)
    decision_delta_ms = (pd.to_datetime(exact["decision_ts"], utc=True) - pd.to_datetime(base["decision_ts"], utc=True)).dt.total_seconds().mul(1000)
    close_compatible = bool(close_delta_ms.isin([1.0]).all())
    decision_compatible = bool(decision_delta_ms.isin([1.0]).all())
    if not close_compatible:
        errors.append("close_ts boundary convention not compatible")
    else:
        warnings.append("base close_ts/decision_ts use inclusive millisecond boundary; exact uses exclusive bucket boundary (+1ms).")
    if not decision_compatible:
        errors.append("decision_ts boundary convention not compatible")
    if bool((pd.to_datetime(base["feature_available_ts"], utc=True) > pd.to_datetime(base["decision_ts"], utc=True)).any()) or bool((pd.to_datetime(exact["feature_available_ts"], utc=True) > pd.to_datetime(exact["decision_ts"], utc=True)).any()):
        errors.append("source feature availability leakage")
    return {
        "status": "PASS" if not errors else "FAIL",
        "base_rows": int(len(base)),
        "exact_rows": int(len(exact)),
        "expected_rows": expected_rows,
        "event_ts_aligned": "event_ts not aligned" not in errors,
        "open_ts_aligned": "open_ts not aligned" not in errors,
        "close_ts_boundary_compatible": close_compatible,
        "decision_ts_boundary_compatible": decision_compatible,
        "close_ts_delta_ms_unique": sorted(close_delta_ms.dropna().unique().tolist())[:10],
        "decision_ts_delta_ms_unique": sorted(decision_delta_ms.dropna().unique().tolist())[:10],
        "errors": errors,
        "warnings": warnings,
    }


def column_collision_summary_v9_47(base: pd.DataFrame, exact: pd.DataFrame) -> dict[str, Any]:
    base_columns = set(base.columns)
    exact_columns = set(exact.columns)
    metadata_collisions = sorted(base_columns & exact_columns)
    feature_collisions = sorted(set(FEATURE_FAMILIES["base_v9_37"]) & set(FEATURE_FAMILIES["exact_aggtrades_v9_45"]))
    return {
        "collision_policy": "metadata/audit columns are rebuilt from aligned sources; base feature names are preserved; exact feature names are appended unchanged; no feature name collision is overwritten.",
        "metadata_collisions": metadata_collisions,
        "feature_collisions": feature_collisions,
        "silent_overwrite": False,
    }


def combine_frames_v9_47(base: pd.DataFrame, exact: pd.DataFrame, *, timeframe: str, run_id: str) -> pd.DataFrame:
    data: dict[str, Any] = {
        "source": SOURCE,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "timeframe": timeframe,
        "event_ts": base["event_ts"],
        "open_ts": base["open_ts"],
        "close_ts": exact["close_ts"],
        "decision_ts": exact["decision_ts"],
        "available_ts": pd.concat([pd.to_datetime(base["available_ts"], utc=True), pd.to_datetime(exact["available_ts"], utc=True)], axis=1).max(axis=1),
        "feature_available_ts": pd.concat([pd.to_datetime(base["feature_available_ts"], utc=True), pd.to_datetime(exact["feature_available_ts"], utc=True)], axis=1).max(axis=1),
        "combined_feature_run_id": run_id,
        "combined_feature_schema_version": COMBINED_FEATURE_SCHEMA_VERSION,
        "base_feature_schema_version": BASE_FEATURE_SCHEMA_VERSION,
        "exact_feature_schema_version": EXACT_FEATURE_SCHEMA_VERSION,
        "source_base_feature_store_version": "V9.37",
        "source_base_feature_validation_version": "V9.38",
        "source_exact_feature_store_version": "V9.45",
        "source_exact_feature_validation_version": "V9.46",
        "source_window_start": TARGET_WINDOW_START,
        "source_window_end": TARGET_WINDOW_END,
    }
    data.update({column: base[column] for column in FEATURE_FAMILIES["base_v9_37"]})
    data.update({column: exact[column] for column in FEATURE_FAMILIES["exact_aggtrades_v9_45"]})
    data.update(
        {
            "warmup_row": base["warmup_row"].astype("int8"),
            "zero_trade_bucket": base["zero_trade_bucket"].astype("int8"),
            "no_trade_bucket": exact["no_trade_bucket"].astype("int8"),
            "feature_null_count": base["feature_null_count"].astype("int64"),
            "feature_error_count": base["feature_error_count"].astype("int64"),
            "exact_feature_null_count": exact["exact_feature_null_count"].astype("int64"),
            "exact_feature_error_count": exact["exact_feature_error_count"].astype("int64"),
        }
    )
    output = pd.DataFrame(data)
    output["combined_feature_null_count"] = output[FEATURE_COLUMNS].isna().sum(axis=1).astype("int64")
    output["combined_feature_error_count"] = output["feature_error_count"] + output["exact_feature_error_count"]
    output["combined_feature_invalid_reason"] = np.where(output["combined_feature_null_count"] > 0, "combined_feature_null_detected", "")
    output["row_valid_for_combined_features"] = (
        base["row_valid_for_features"].astype(bool)
        & exact["row_valid_for_exact_features"].astype(bool)
        & (output["combined_feature_null_count"] == 0)
        & (output["combined_feature_error_count"] == 0)
    )
    output.loc[~output["row_valid_for_combined_features"] & (output["combined_feature_invalid_reason"] == ""), "combined_feature_invalid_reason"] = "source_feature_invalid"
    return output[STRICT_COLUMNS]


def validate_combined_frame_v9_47(frame: pd.DataFrame, *, timeframe: str, output_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    if len(frame) != expected_rows:
        errors.append("row count mismatch")
    duplicate_event = int(frame["event_ts"].duplicated().sum())
    duplicate_open = int(frame["open_ts"].duplicated().sum())
    duplicate_close = int(frame["close_ts"].duplicated().sum())
    if duplicate_event or duplicate_open or duplicate_close:
        errors.append("duplicate timestamps")
    leakage_violations = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    if leakage_violations:
        errors.append("feature availability leakage")
    forbidden = sorted([column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)])
    if forbidden:
        errors.append("forbidden columns present")
    null_count = int(frame[FEATURE_COLUMNS].isna().sum().sum())
    invalid_rows = int((~frame["row_valid_for_combined_features"].astype(bool)).sum())
    warmup_mask = frame["warmup_row"].astype(bool)
    non_warmup_null_count = int(frame.loc[~warmup_mask, FEATURE_COLUMNS].isna().sum().sum())
    invalid_non_warmup_rows = int((~frame.loc[~warmup_mask, "row_valid_for_combined_features"].astype(bool)).sum())
    warmup_null_count = int(frame.loc[warmup_mask, FEATURE_COLUMNS].isna().sum().sum())
    invalid_warmup_rows = int((~frame.loc[warmup_mask, "row_valid_for_combined_features"].astype(bool)).sum())
    if warmup_null_count or invalid_warmup_rows:
        warnings.append("Warmup rows inherit rolling-window nulls from V9.37; non-blocking because non-warmup rows are valid.")
    if non_warmup_null_count or invalid_non_warmup_rows:
        errors.append("invalid combined feature rows")
    non_negative_columns = [c for c in FEATURE_COLUMNS if ("count" in c or "volume" in c or "size" in c or c.endswith("_flag")) and "imbalance" not in c and "ratio" not in c and "return" not in c and "volatility" not in c]
    negative_values = int((frame[non_negative_columns] < -1e-12).sum().sum())
    if negative_values:
        errors.append("negative non-negative features")
    ratio_columns = [c for c in FEATURE_COLUMNS if "ratio" in c or "imbalance" in c]
    ratio_oob = int(((frame[ratio_columns] < -1.000001) | (frame[ratio_columns] > 1.000001)).sum().sum())
    if ratio_oob:
        errors.append("ratio or imbalance out of bounds")
    coverage_ok = len(frame) and str(frame["open_ts"].iloc[0]) == "2021-05-05 00:00:00+00:00" and str(frame["close_ts"].iloc[-1]) == "2026-05-06 00:00:00+00:00"
    if not coverage_ok:
        errors.append("coverage boundary mismatch")
    quality_status = "PASS" if not errors else "FAIL"
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS if coverage_ok and len(frame) == expected_rows else 0,
        "days_missing": 0 if coverage_ok and len(frame) == expected_rows else EXPECTED_DAYS,
        "duplicate_event_ts": duplicate_event,
        "duplicate_open_ts": duplicate_open,
        "duplicate_close_ts": duplicate_close,
        "feature_available_ts_lte_decision_ts": leakage_violations == 0,
        "forbidden_columns": forbidden,
        "null_summary": {
            "combined_feature_null_count": null_count,
            "warmup_feature_null_count": warmup_null_count,
            "non_warmup_feature_null_count": non_warmup_null_count,
            "combined_feature_error_count": int(frame["combined_feature_error_count"].sum()),
            "invalid_rows": invalid_rows,
            "invalid_warmup_rows": invalid_warmup_rows,
            "invalid_non_warmup_rows": invalid_non_warmup_rows,
        },
        "warmup_summary": {"warmup_rows": int(frame["warmup_row"].sum())},
        "zero_trade_bucket_summary": {"zero_trade_bucket_count": int(frame["zero_trade_bucket"].sum())},
        "no_trade_bucket_summary": {"no_trade_bucket_count": int(frame["no_trade_bucket"].sum())},
        "range_summary": {"negative_non_negative_features": negative_values, "ratio_out_of_bounds": ratio_oob},
        "warnings": warnings,
        "errors": errors,
        "coverage_status": "PASS" if coverage_ok and len(frame) == expected_rows else "FAIL",
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS and not forbidden else "FAIL",
        "quality_status": quality_status,
    }


def build_preflight_v9_47(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    data_path = root / "data"
    usage = shutil.disk_usage(data_path if data_path.exists() else root)
    required = {
        "v9_46_exact_validation": ("decision", "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings"),
        "v9_38_base_validation": ("quality_status", "PASS"),
        "v9_37_base": ("quality_status", "PASS"),
    }
    missing_or_bad = []
    for name, (key, expected) in required.items():
        payload = inputs.get(name, {})
        if not payload or payload.get(key) != expected:
            missing_or_bad.append(name)
    base_exists = {tf: feature_output_path_v9_37(root, tf).is_file() for tf in EXPECTED_TIMEFRAMES}
    exact_exists = {tf: exact_feature_output_path_v9_45(root, tf).is_file() for tf in EXPECTED_TIMEFRAMES}
    free_gib = usage.free / (1024**3)
    return {
        "free_gib_data_mount": round(free_gib, 3),
        "safe_to_run": free_gib >= 20.0,
        "storage_warning": free_gib < 80.0,
        "source_reports_ready": not missing_or_bad,
        "source_report_issues": missing_or_bad,
        "base_files_exist": base_exists,
        "exact_files_exist": exact_exists,
        "workers": min(int(os.environ.get("GALAPAGOS_V9_47_WORKERS", "4")), len(EXPECTED_TIMEFRAMES)),
    }


def build_report_v9_47(*, root: Path, inputs: dict[str, Any], preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], output_paths: dict[str, Path], runtime_seconds: float) -> dict[str, Any]:
    coverage_pass = all(item["coverage_status"] == "PASS" for item in timeframe_reports.values())
    schema_pass = all(item["schema_status"] == "PASS" for item in timeframe_reports.values())
    quality_pass = all(item["quality_status"] == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("feature_available_ts_lte_decision_ts") for item in timeframe_reports.values())
    forbidden = {tf: item.get("forbidden_columns", []) for tf, item in timeframe_reports.items()}
    forbidden_pass = all(not cols for cols in forbidden.values())
    collision_summary = {tf: item.get("column_collision_summary", {}) for tf, item in timeframe_reports.items()}
    warnings = build_warnings_v9_47(preflight, timeframe_reports)
    decision = decide_v9_47(preflight, coverage_pass, schema_pass, quality_pass, leakage_pass, forbidden_pass, warnings, timeframe_reports)
    output_sizes = {timeframe: output_paths[timeframe].stat().st_size if output_paths[timeframe].is_file() else 0 for timeframe in EXPECTED_TIMEFRAMES}
    return {
        "version": VERSION,
        "source_versions": {
            "base_feature_store": "V9.37",
            "base_feature_validation": "V9.38",
            "exact_feature_store": "V9.45",
            "exact_feature_validation": "V9.46",
        },
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"ohlcv_aggtrades_exact_5y_feature_store_created", "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "decision": decision,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": EXPECTED_DAYS},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_store_created": decision in {"ohlcv_aggtrades_exact_5y_feature_store_created", "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"},
        "features_created": decision in {"ohlcv_aggtrades_exact_5y_feature_store_created", "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"},
        "feature_store_paths": {timeframe: path.as_posix() for timeframe, path in output_paths.items()},
        "output_bytes": output_sizes,
        "row_counts": {timeframe: item["actual_rows"] for timeframe, item in timeframe_reports.items()},
        "base_feature_columns_count": len(FEATURE_FAMILIES["base_v9_37"]),
        "exact_feature_columns_count": len(FEATURE_FAMILIES["exact_aggtrades_v9_45"]),
        "combined_feature_columns_count": len(FEATURE_COLUMNS),
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_families": FEATURE_FAMILIES,
        "source_audit_columns_inherited_as_features": SOURCE_AUDIT_COLUMNS_INHERITED_AS_FEATURES,
        "combined_audit_columns": AUDIT_COLUMNS,
        "collision_policy": "metadata/audit columns are rebuilt; base and exact feature columns are preserved; no silent overwrite.",
        "column_collision_summary": collision_summary,
        "timeframe_reports": timeframe_reports,
        "zero_trade_bucket_summary": {timeframe: item.get("zero_trade_bucket_summary", {}) for timeframe, item in timeframe_reports.items()},
        "no_trade_bucket_summary": {timeframe: item.get("no_trade_bucket_summary", {}) for timeframe, item in timeframe_reports.items()},
        "warmup_summary": {timeframe: item.get("warmup_summary", {}) for timeframe, item in timeframe_reports.items()},
        "null_summary": {timeframe: item.get("null_summary", {}) for timeframe, item in timeframe_reports.items()},
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "feature_available_ts_lte_decision_ts": leakage_pass, "rolling_windows_past_only": True},
        "forbidden_column_scan": {"status": "PASS" if forbidden_pass else "FAIL", "forbidden_columns": forbidden},
        "source_lineage": {
            "base_feature_store_version": "V9.37",
            "base_feature_validation_version": "V9.38",
            "exact_feature_store_version": "V9.45",
            "exact_feature_validation_version": "V9.46",
        },
        "quality_status": "PASS" if quality_pass else "FAIL",
        "coverage_status": "target_5y_combined_feature_window_complete" if coverage_pass else "target_5y_combined_feature_window_incomplete",
        "blockers": build_blockers_v9_47(preflight, timeframe_reports, coverage_pass, schema_pass, quality_pass, leakage_pass, forbidden_pass),
        "warnings": warnings,
        "limitations": [
            "V9.47 cree uniquement un feature store combine; aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
            "Les timestamps close_ts/decision_ts utilisent la convention exclusive de V9.45 apres validation de la compatibilite +1ms avec V9.37.",
        ],
        "next_recommendation": "V9.48 - Combined OHLCV + Exact AggTrades 5Y Feature Store Validation" if decision in {"ohlcv_aggtrades_exact_5y_feature_store_created", "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"} else "V9.48 - Combined Feature Store Correction",
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
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def decide_v9_47(preflight: dict[str, Any], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, forbidden_pass: bool, warnings: list[str], timeframe_reports: dict[str, dict[str, Any]]) -> str:
    if not preflight["safe_to_run"]:
        return "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_storage"
    if not preflight["source_reports_ready"] or any(item.get("alignment", {}).get("status") == "FAIL" for item in timeframe_reports.values()):
        return "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_alignment"
    if not schema_pass:
        return "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_schema"
    if not leakage_pass or not forbidden_pass:
        return "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_leakage"
    if not quality_pass:
        return "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_quality"
    if not coverage_pass:
        return "ohlcv_aggtrades_exact_5y_feature_store_partial"
    if warnings:
        return "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"
    return "ohlcv_aggtrades_exact_5y_feature_store_created"


def build_warnings_v9_47(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if preflight["storage_warning"]:
        warnings.append("Espace disque sous 80 GiB; non bloquant car les fichiers combines sont produits et valides.")
    for timeframe, item in timeframe_reports.items():
        warnings.extend(f"{timeframe}: {warning}" for warning in item.get("alignment", {}).get("warnings", []))
        warnings.extend(f"{timeframe}: {warning}" for warning in item.get("warnings", []))
    return warnings


def build_blockers_v9_47(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, forbidden_pass: bool) -> list[str]:
    blockers: list[str] = []
    if not preflight["safe_to_run"]:
        blockers.append("storage below required threshold")
    if not preflight["source_reports_ready"]:
        blockers.append(f"source reports not ready: {preflight['source_report_issues']}")
    for timeframe, item in timeframe_reports.items():
        blockers.extend(f"{timeframe}: {error}" for error in item.get("errors", []))
    if not coverage_pass:
        blockers.append("coverage validation failed")
    if not schema_pass:
        blockers.append("schema validation failed")
    if not quality_pass:
        blockers.append("quality validation failed")
    if not leakage_pass or not forbidden_pass:
        blockers.append("leakage or forbidden column validation failed")
    return blockers


def build_manifest_v9_47(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "target_window": report["target_window"],
        "timeframes": report["timeframes"],
        "feature_store_paths": report["feature_store_paths"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "base_feature_columns_count": report["base_feature_columns_count"],
        "exact_feature_columns_count": report["exact_feature_columns_count"],
        "combined_feature_columns_count": report["combined_feature_columns_count"],
        "source_audit_columns_inherited_as_features": report["source_audit_columns_inherited_as_features"],
        "combined_audit_columns": report["combined_audit_columns"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "features_created": report["features_created"],
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }


def build_markdown_v9_47(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Feature store combine OHLCV + aggTrades exactes 5Y V9.47",
            "",
            f"- Decision : `{report['decision']}`.",
            f"- Recommandation : `{report['next_recommendation']}`.",
            f"- Fenetre : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.",
            f"- Timeframes : `{report['timeframes']}`.",
            f"- Row counts : `{report['row_counts']}`.",
            f"- Colonnes base : `{report['base_feature_columns_count']}`.",
            f"- Colonnes exactes : `{report['exact_feature_columns_count']}`.",
            f"- Colonnes combinees : `{report['combined_feature_columns_count']}`.",
            f"- Qualite : `{report['quality_status']}`.",
            f"- Coverage : `{report['coverage_status']}`.",
            f"- Leakage guard : `{report['leakage_guard']['status']}`.",
            f"- Forbidden columns scan : `{report['forbidden_column_scan']['status']}`.",
            "",
            "## Garde-fous",
            "",
            "- Feature-store-only.",
            "- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
            "- Aucun reseau, aucune cle API, aucun endpoint prive.",
            "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
            "",
        ]
    )


def update_state_surfaces_v9_47(root: Path, report: dict[str, Any]) -> None:
    latest_path = root / "reports/current/latest_metrics.json"
    latest = _read_optional_json(latest_path)
    latest.update(
        {
            "last_validated_version": LAST_VALIDATED_VERSION,
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": DIRECTION,
            "quality_status": report["quality_status"],
            "coverage_status": report["coverage_status"],
            "decision_v9_47": report["decision"],
            "recommended_next_step": report["next_recommendation"],
            "features_created": report["features_created"],
            "feature_store_created": report["feature_store_created"],
            "dataset_created": False,
            "labels_created": False,
            "ml_executed": False,
            **SAFETY_FLAGS,
        }
    )
    _write_json(latest_path, latest)
    _write_text(root / "reports/current/latest_metrics.md", "# Latest Metrics\n\n" f"- Version candidate : `{VERSION}`.\n" f"- Decision V9.47 : `{report['decision']}`.\n" f"- Feature columns combinees : `{report['combined_feature_columns_count']}`.\n" f"- Row counts : `{report['row_counts']}`.\n" "- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n")
    _write_text(root / "reports/current/latest_summary.md", "# Synthese courante\n\n" f"V9.47 cree un feature store combine OHLCV + aggTrades exactes 5Y. Decision : `{report['decision']}`. Recommandation : `{report['next_recommendation']}`.\n")
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_optional_json(state_path)
    state.update({"last_validated_version": LAST_VALIDATED_VERSION, "candidate_version": VERSION, "candidate_status": "pending_external_audit", "direction": DIRECTION, "decision_v9_47": report["decision"], "quality_status": report["quality_status"], "coverage_status": report["coverage_status"], "features_created": report["features_created"], "feature_store_created": report["feature_store_created"], "dataset_created": False, "labels_created": False, "ml_executed": False, **FINDINGS, **SAFETY_FLAGS})
    _write_json(state_path, state)
    _write_text(root / "reports/PROJECT_STATE.md", "# Etat Projet Galapagos\n\n" f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n" f"- Version candidate : `{VERSION}`.\n" "- Statut candidat : `pending_external_audit`.\n" f"- Direction : `{DIRECTION}`.\n" f"- Decision : `{report['decision']}`.\n" f"- Recommandation : `{report['next_recommendation']}`.\n" "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie, signal, modele persistant, API privee, cle API, reseau ou telechargement.\n")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Projet Galapagos\n"
    marker = "## V9.47 - Combine Base + Exact AggTrades Feature Store"
    if marker not in readme:
        _write_text(readme_path, readme.rstrip() + "\n\n" + marker + "\n\n" f"- Decision : `{report['decision']}`.\n" f"- Recommandation : `{report['next_recommendation']}`.\n" "- Feature-store-only : aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n")


def combined_feature_output_path_v9_47(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2021-05-05_2026-05-05/features.parquet"


def feature_output_path_v9_37(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_37/features/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2021-05-05_2026-05-05/features.parquet"


def _failed_timeframe_report(timeframe: str, output_path: Path, alignment: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    return {"version": VERSION, "timeframe": timeframe, "output_path": output_path.as_posix(), "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe], "actual_rows": 0, "alignment": alignment, "errors": errors, "coverage_status": "FAIL", "schema_status": "FAIL", "quality_status": "FAIL", "feature_available_ts_lte_decision_ts": False, "forbidden_columns": []}


def _blocked_timeframe_report(timeframe: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return _failed_timeframe_report(timeframe, combined_feature_output_path_v9_47(Path("."), timeframe), {"status": "FAIL", "errors": preflight.get("source_report_issues", [])}, ["preflight blocked"])


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
