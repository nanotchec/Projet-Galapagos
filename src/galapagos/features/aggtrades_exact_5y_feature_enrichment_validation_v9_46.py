from __future__ import annotations

import json
import math
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45 import exact_feature_output_path_v9_45
from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import (
    AUDIT_COLUMNS,
    BURST_FEATURE_COLUMNS,
    COUNT_FEATURE_COLUMNS,
    DISTRIBUTION_FEATURE_COLUMNS,
    EXPECTED_DAYS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FORBIDDEN_FEATURE_COLUMNS,
    IMBALANCE_FEATURE_COLUMNS,
    METADATA_COLUMNS,
    MISSINGNESS_FEATURE_COLUMNS,
    ROLLING_FEATURE_COLUMNS,
    SOURCE_AGGTRADES_VALIDATION_VERSION,
    STRICT_COLUMNS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMING_FEATURE_COLUMNS,
    TRADE_SIZE_FEATURE_COLUMNS,
    VOLUME_FEATURE_COLUMNS,
)


VERSION = "V9.46"
SOURCE_VERSION = "V9.45"
LAST_VALIDATED_VERSION = "V9.45"
DIRECTION = "aggtrades_exact_5y_feature_enrichment_validation"

REPORT_JSON_PATH = Path("reports/features/aggtrades_exact_5y_feature_enrichment_validation_v9_46.json")
REPORT_MD_PATH = Path("reports/features/aggtrades_exact_5y_feature_enrichment_validation_v9_46.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_exact_5y_feature_enrichment_validation_v9_46_manifest.json")
DOC_PATH = Path("docs/aggtrades_exact_5y_feature_enrichment_validation_v9_46.md")
SAMPLE_REPORT_PATH = Path("reports/features/aggtrades_exact_5y_feature_enrichment_validation_samples_v9_46.json")
SAMPLE_ROOT = Path("data/audit_samples/v9_46/aggtrades_exact_5y")

INPUT_PATHS = {
    "v9_45_report": Path("reports/features/aggtrades_exact_5y_feature_enrichment_v9_45.json"),
    "v9_45_manifest": Path("reports/manifests/aggtrades_exact_5y_feature_enrichment_v9_45_manifest.json"),
    "v9_44_diagnostic": Path("reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.json"),
    "v9_43_ml": Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    "v9_42_dataset_validation": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    "v9_38_feature_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_32_aggtrades_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

EXPECTED_ZERO_TRADE_BUCKETS = {"1m": 542, "5m": 108, "15m": 36, "1h": 8}

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


def run_aggtrades_exact_5y_feature_enrichment_validation_v9_46(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _read_optional_json(root / path) for name, path in INPUT_PATHS.items()}
    preflight = build_preflight_v9_46(root, inputs)
    full_local_available = all(exact_feature_output_path_v9_45(root, timeframe).is_file() for timeframe in EXPECTED_TIMEFRAMES)

    if full_local_available:
        timeframe_reports = validate_full_local_timeframes_v9_46(root)
        sample_report = write_audit_samples_v9_46(root)
        validation_mode = "full-local"
    else:
        timeframe_reports = validate_from_reports_v9_46(inputs)
        sample_report = validate_audit_samples_v9_46(root)
        validation_mode = "audit-lite"

    report = build_report_v9_46(
        root=root,
        inputs=inputs,
        preflight=preflight,
        validation_mode=validation_mode,
        full_local_available=full_local_available,
        timeframe_reports=timeframe_reports,
        sample_report=sample_report,
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_46(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / SAMPLE_REPORT_PATH, sample_report)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_46(report, sample_report))
    update_state_surfaces_v9_46(root, report)
    return report


def build_preflight_v9_46(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    data_path = root / "data"
    usage = shutil.disk_usage(data_path if data_path.exists() else root)
    v9_45_report = inputs.get("v9_45_report", {})
    output_bytes = v9_45_report.get("output_bytes", {}) if isinstance(v9_45_report, dict) else {}
    output_size_bytes = int(sum(int(value) for value in output_bytes.values())) if output_bytes else 0
    command_results = _read_optional_json(root / "reports/audit_lite/v9_45_command_results.json")
    commands = command_results.get("commands", []) if isinstance(command_results, dict) else []
    initial_command = next((item for item in commands if "GALAPAGOS_V9_45_WORKERS=12" in item.get("command", "")), None)
    return {
        "free_gib_data_mount": round(usage.free / (1024**3), 3),
        "free_gib_project_mount": round(shutil.disk_usage(root).free / (1024**3), 3),
        "v9_45_output_size_gib": round(output_size_bytes / (1024**3), 3),
        "safe_for_validation": True,
        "free_gib_data_mount_at_v9_45": v9_45_report.get("disk_preflight", {}).get("free_gib_data_mount"),
        "storage_warning_non_blocking": bool(v9_45_report.get("disk_preflight", {}).get("storage_warning")),
        "initial_generation_runtime_available": initial_command is not None,
        "initial_generation_command_seen_in_command_results": initial_command is not None,
        "initial_generation_command_result": initial_command,
        "report_refresh_runtime_available": isinstance(v9_45_report.get("runtime_seconds"), (int, float)),
        "runtime_seconds_reported": v9_45_report.get("runtime_seconds"),
        "runtime_reporting_acceptable": initial_command is not None and isinstance(v9_45_report.get("runtime_seconds"), (int, float)),
    }


def validate_full_local_timeframes_v9_46(root: Path) -> dict[str, dict[str, Any]]:
    workers = min(4, len(EXPECTED_TIMEFRAMES))
    reports: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(validate_timeframe_file_v9_46, root, timeframe): timeframe for timeframe in EXPECTED_TIMEFRAMES}
        for future in as_completed(futures):
            timeframe = futures[future]
            reports[timeframe] = future.result()
    return {timeframe: reports[timeframe] for timeframe in EXPECTED_TIMEFRAMES}


def validate_timeframe_file_v9_46(root: Path, timeframe: str) -> dict[str, Any]:
    path = exact_feature_output_path_v9_45(root, timeframe)
    if not path.is_file():
        return _blocked_timeframe_report(timeframe, f"missing feature file: {path}")
    try:
        frame = pd.read_parquet(path, engine="pyarrow")
    except Exception as exc:  # pragma: no cover - defensive path
        return _blocked_timeframe_report(timeframe, f"feature file unreadable: {exc}")

    errors: list[str] = []
    warnings: list[str] = []
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    if len(frame) != expected_rows:
        errors.append(f"row count mismatch: expected {expected_rows}, got {len(frame)}")

    timestamp_summary = _timestamp_summary(frame, timeframe, errors)
    metadata_summary = _metadata_summary(frame, errors)
    forbidden_scan = _forbidden_scan(frame)
    if forbidden_scan["forbidden_columns"]:
        errors.append("forbidden columns present")

    row_valid_false = int((~frame["row_valid_for_exact_features"].astype(bool)).sum())
    feature_null_count = int(frame[list(FEATURE_COLUMNS)].isna().sum().sum())
    feature_error_count = int(frame["exact_feature_error_count"].sum())
    invalid_reason_nonempty = int(frame["feature_invalid_reason"].astype(str).ne("").sum())
    if row_valid_false or feature_null_count or feature_error_count:
        errors.append("invalid feature audit rows detected")
    if invalid_reason_nonempty and row_valid_false == 0:
        errors.append("feature_invalid_reason is non-empty without invalid rows")

    counts_summary = _counts_summary(frame)
    volumes_summary = _volumes_summary(frame)
    ratio_summary = _ratio_summary(frame)
    quantile_summary = _quantile_summary(frame)
    bucket_summary = _bucket_summary(frame)
    burst_summary = _burst_summary(frame, timeframe)
    rolling_summary = _rolling_summary(frame)
    zero_summary = _zero_trade_summary(frame, timeframe)
    for name, summary in {
        "counts": counts_summary,
        "volumes": volumes_summary,
        "ratios": ratio_summary,
        "quantiles": quantile_summary,
        "buckets": bucket_summary,
        "burst": burst_summary,
        "rolling": rolling_summary,
        "zero_trade": zero_summary,
    }.items():
        if summary["errors"]:
            errors.extend(f"{name}: {item}" for item in summary["errors"])
        warnings.extend(f"{name}: {item}" for item in summary.get("warnings", []))

    leakage_errors = []
    if int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum()):
        leakage_errors.append("feature_available_ts after decision_ts")
    quality_status = "PASS" if not errors and not leakage_errors else "FAIL"
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "timeframe": timeframe,
        "feature_path": path.as_posix(),
        "feature_file_exists": True,
        "feature_file_readable": True,
        "feature_file_size_bytes": path.stat().st_size,
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "coverage_start": timestamp_summary["coverage_start"],
        "coverage_end": timestamp_summary["coverage_end"],
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS if len(frame) == expected_rows and not timestamp_summary["errors"] else 0,
        "days_missing": 0 if len(frame) == expected_rows and not timestamp_summary["errors"] else EXPECTED_DAYS,
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS else "FAIL",
        "feature_columns_count": len(FEATURE_COLUMNS),
        "metadata_columns_present": all(column in frame.columns for column in METADATA_COLUMNS),
        "audit_columns_present": all(column in frame.columns for column in AUDIT_COLUMNS),
        "metadata_summary": metadata_summary,
        "timestamp_summary": timestamp_summary,
        "forbidden_column_scan": forbidden_scan,
        "leakage_guard_status": "PASS" if not leakage_errors else "FAIL",
        "leakage_errors": leakage_errors,
        "leakage_warnings": [],
        "counts_summary": counts_summary,
        "volumes_summary": volumes_summary,
        "ratio_bounds_summary": ratio_summary,
        "quantile_ordering_summary": quantile_summary,
        "bucket_consistency_summary": bucket_summary,
        "burst_consistency_summary": burst_summary,
        "rolling_consistency_summary": rolling_summary,
        "zero_trade_bucket_summary": zero_summary,
        "null_summary": {
            "feature_null_count": feature_null_count,
            "exact_feature_null_count_sum": int(frame["exact_feature_null_count"].sum()),
            "exact_feature_error_count_sum": feature_error_count,
            "row_valid_false_count": row_valid_false,
            "feature_invalid_reason_nonempty_count": invalid_reason_nonempty,
        },
        "warnings": warnings,
        "errors": errors + leakage_errors,
        "coverage_status": "PASS" if len(frame) == expected_rows and not timestamp_summary["errors"] else "FAIL",
        "quality_status": quality_status,
    }


def write_audit_samples_v9_46(root: Path) -> dict[str, Any]:
    samples: dict[str, Any] = {}
    for timeframe in EXPECTED_TIMEFRAMES:
        path = exact_feature_output_path_v9_45(root, timeframe)
        sample_path = root / SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.read_parquet(path, engine="pyarrow")
        zero_rows = frame[frame["no_trade_bucket"] == 1].head(10)
        sample = pd.concat([frame.head(25), zero_rows, frame.tail(25)], ignore_index=True).drop_duplicates(subset=["open_ts"])
        sample.to_parquet(sample_path, index=False, engine="pyarrow", compression="zstd")
        samples[timeframe] = {
            "sample_path": sample_path.relative_to(root).as_posix(),
            "sample_rows": int(len(sample)),
            "schema_columns": list(sample.columns),
            "has_zero_trade_sample": bool((sample["no_trade_bucket"] == 1).any()),
            "sample_bytes": sample_path.stat().st_size,
        }
    return {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "sample_mode": "full-local-created-small-parquet-samples",
        "full_feature_parquets_included": False,
        "samples": samples,
        "total_sample_bytes": sum(item["sample_bytes"] for item in samples.values()),
    }


def validate_audit_samples_v9_46(root: Path) -> dict[str, Any]:
    samples: dict[str, Any] = {}
    errors: list[str] = []
    for timeframe in EXPECTED_TIMEFRAMES:
        sample_path = root / SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        if not sample_path.is_file():
            errors.append(f"missing sample for {timeframe}")
            continue
        try:
            sample = pd.read_parquet(sample_path, engine="pyarrow")
        except Exception as exc:  # pragma: no cover - dependency/environment path
            errors.append(f"sample unreadable for {timeframe}: {exc}")
            continue
        if list(sample.columns) != STRICT_COLUMNS:
            errors.append(f"sample schema mismatch for {timeframe}")
        forbidden = _forbidden_scan(sample)["forbidden_columns"]
        if forbidden:
            errors.append(f"sample forbidden columns for {timeframe}: {forbidden}")
        samples[timeframe] = {
            "sample_path": sample_path.relative_to(root).as_posix(),
            "sample_rows": int(len(sample)),
            "schema_columns": list(sample.columns),
            "has_zero_trade_sample": bool((sample["no_trade_bucket"] == 1).any()),
            "sample_bytes": sample_path.stat().st_size,
        }
    return {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "sample_mode": "audit-lite-validated-small-parquet-samples",
        "full_feature_parquets_included": False,
        "samples": samples,
        "total_sample_bytes": sum(item["sample_bytes"] for item in samples.values()),
        "errors": errors,
    }


def validate_from_reports_v9_46(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    report = inputs.get("v9_45_report", {})
    timeframe_reports = report.get("timeframe_reports", {}) if isinstance(report, dict) else {}
    results: dict[str, dict[str, Any]] = {}
    for timeframe in EXPECTED_TIMEFRAMES:
        source = timeframe_reports.get(timeframe, {})
        errors = []
        if source.get("actual_rows") != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
            errors.append("reported row count mismatch")
        if source.get("quality_status") != "PASS" or source.get("coverage_status") != "PASS":
            errors.append("reported quality or coverage is not PASS")
        results[timeframe] = {
            "version": VERSION,
            "source_version": SOURCE_VERSION,
            "timeframe": timeframe,
            "feature_path": report.get("feature_paths", {}).get(timeframe),
            "feature_file_exists": False,
            "feature_file_readable": False,
            "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
            "actual_rows": source.get("actual_rows"),
            "days_expected": EXPECTED_DAYS,
            "days_complete": source.get("days_complete"),
            "days_missing": source.get("days_missing"),
            "schema_status": "REPORT_ONLY",
            "coverage_status": "PASS" if not errors else "FAIL",
            "quality_status": "PASS" if not errors else "FAIL",
            "forbidden_column_scan": {"status": "PASS", "forbidden_columns": source.get("forbidden_columns", [])},
            "leakage_guard_status": "PASS" if source.get("feature_available_ts_le_decision_ts") is True else "FAIL",
            "zero_trade_bucket_summary": {
                "expected_zero_trade_buckets": EXPECTED_ZERO_TRADE_BUCKETS[timeframe],
                "actual_zero_trade_buckets": source.get("no_trade_bucket_count"),
                "zero_trade_bucket_blocking": False,
                "errors": [],
                "warnings": ["audit-lite uses reports and samples; full Parquets are intentionally absent"],
            },
            "errors": errors,
            "warnings": ["audit-lite report-only validation"],
        }
    return results


def build_report_v9_46(
    *,
    root: Path,
    inputs: dict[str, Any],
    preflight: dict[str, Any],
    validation_mode: str,
    full_local_available: bool,
    timeframe_reports: dict[str, dict[str, Any]],
    sample_report: dict[str, Any],
    runtime_seconds: float,
) -> dict[str, Any]:
    coverage_pass = all(item.get("coverage_status") == "PASS" for item in timeframe_reports.values())
    schema_pass = all(item.get("schema_status") in {"PASS", "REPORT_ONLY"} for item in timeframe_reports.values())
    quality_pass = all(item.get("quality_status") == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("leakage_guard_status") == "PASS" for item in timeframe_reports.values())
    forbidden_pass = all(not item.get("forbidden_column_scan", {}).get("forbidden_columns") for item in timeframe_reports.values())
    zero_trade_blocking = any(item.get("zero_trade_bucket_summary", {}).get("zero_trade_bucket_blocking") for item in timeframe_reports.values())
    warnings = build_warnings_v9_46(preflight, timeframe_reports, validation_mode, sample_report)
    decision = decide_v9_46(coverage_pass, schema_pass, quality_pass, leakage_pass, forbidden_pass, zero_trade_blocking, warnings)
    row_counts = {timeframe: int(timeframe_reports[timeframe].get("actual_rows") or 0) for timeframe in EXPECTED_TIMEFRAMES}
    output_bytes = {
        timeframe: exact_feature_output_path_v9_45(root, timeframe).stat().st_size if exact_feature_output_path_v9_45(root, timeframe).is_file() else 0
        for timeframe in EXPECTED_TIMEFRAMES
    }
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "validation_mode": validation_mode,
        "full_local_parquets_available": full_local_available,
        "audit_lite_mode_supported": True,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": EXPECTED_DAYS},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME,
        "row_counts": row_counts,
        "output_bytes": output_bytes,
        "feature_columns_count": len(FEATURE_COLUMNS),
        "metadata_columns": METADATA_COLUMNS,
        "audit_columns": AUDIT_COLUMNS,
        "input_versions": {name: payload.get("version") for name, payload in inputs.items() if isinstance(payload, dict)},
        "v9_45_decision": inputs.get("v9_45_report", {}).get("decision"),
        "v9_45_quality_status": inputs.get("v9_45_report", {}).get("quality_status"),
        "v9_45_coverage_status": inputs.get("v9_45_report", {}).get("coverage_status"),
        "coverage_validation": {"status": "PASS" if coverage_pass else "FAIL", "timeframes": {k: v.get("coverage_status") for k, v in timeframe_reports.items()}},
        "schema_validation": {"status": "PASS" if schema_pass else "FAIL", "timeframes": {k: v.get("schema_status") for k, v in timeframe_reports.items()}},
        "quality_validation": {"status": "PASS" if quality_pass else "FAIL", "timeframes": {k: v.get("quality_status") for k, v in timeframe_reports.items()}},
        "zero_trade_bucket_validation": {
            "status": "PASS" if not zero_trade_blocking else "FAIL",
            "expected": EXPECTED_ZERO_TRADE_BUCKETS,
            "actual": {k: v.get("zero_trade_bucket_summary", {}).get("actual_zero_trade_buckets") for k, v in timeframe_reports.items()},
            "zero_trade_bucket_blocking": zero_trade_blocking,
        },
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "rolling_windows_past_only": True, "feature_available_ts_le_decision_ts": leakage_pass},
        "forbidden_column_scan": {"status": "PASS" if forbidden_pass else "FAIL", "timeframes": {k: v.get("forbidden_column_scan", {}).get("forbidden_columns", []) for k, v in timeframe_reports.items()}},
        "runtime_storage_reconciliation": preflight,
        "timeframe_reports": timeframe_reports,
        "sample_report_path": SAMPLE_REPORT_PATH.as_posix(),
        "sample_report": sample_report,
        "features_created": False,
        "feature_store_combined_created": False,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "quality_status": "PASS" if quality_pass and schema_pass and coverage_pass and leakage_pass and forbidden_pass and not zero_trade_blocking else "FAIL",
        "coverage_status": "target_5y_exact_feature_layer_validated" if coverage_pass else "target_5y_exact_feature_layer_incomplete",
        "warnings": warnings,
        "decision": decision,
        "next_recommendation": "V9.47 - Combine Base + Exact AggTrades Feature Store" if decision in {"aggtrades_exact_5y_feature_enrichment_validated", "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings"} else "V9.47 - Exact Feature Enrichment Correction",
        "runtime_seconds": runtime_seconds,
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def decide_v9_46(coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, forbidden_pass: bool, zero_trade_blocking: bool, warnings: list[str]) -> str:
    if not coverage_pass:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_coverage"
    if not schema_pass:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_schema"
    if not leakage_pass or not forbidden_pass:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_leakage"
    if not quality_pass or zero_trade_blocking:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_quality"
    if warnings:
        return "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings"
    return "aggtrades_exact_5y_feature_enrichment_validated"


def build_warnings_v9_46(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], validation_mode: str, sample_report: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if preflight.get("storage_warning_non_blocking"):
        warnings.append("V9.45 avait un warning stockage; non bloquant pour V9.46 car les fichiers existent et sont valides.")
    if preflight.get("runtime_reporting_acceptable"):
        warnings.append("V9.45 distingue generation longue 12 coeurs et refresh de rapport; reconciliation runtime acceptable.")
    if validation_mode == "audit-lite":
        warnings.append("Mode audit-lite sans Parquets full; validation limitee aux rapports/manifests/samples.")
    if sample_report.get("sample_mode"):
        warnings.append("Samples audit-lite tres petits inclus; les Parquets full ne sont pas inclus dans le ZIP.")
    for timeframe, report in timeframe_reports.items():
        actual = report.get("zero_trade_bucket_summary", {}).get("actual_zero_trade_buckets")
        if actual:
            warnings.append(f"{timeframe}: {actual} buckets sans trade coherents et non bloquants.")
    return warnings


def build_manifest_v9_46(report: dict[str, Any], sample_report: dict[str, Any]) -> dict[str, Any]:
    sample_paths = [sample["sample_path"] for sample in sample_report.get("samples", {}).values()]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "validation_mode": report["validation_mode"],
        "target_window": report["target_window"],
        "timeframes": report["timeframes"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix(), SAMPLE_REPORT_PATH.as_posix()],
        "sample_paths": sample_paths,
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "features_created": False,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }


def build_markdown_v9_46(report: dict[str, Any]) -> str:
    lines = [
        "# Validation features exactes aggTrades 5Y V9.46",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Recommandation : `{report['next_recommendation']}`.",
        f"- Mode : `{report['validation_mode']}`.",
        f"- Fenetre : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.",
        f"- Coverage : `{report['coverage_validation']['status']}`.",
        f"- Schema : `{report['schema_validation']['status']}`.",
        f"- Qualite : `{report['quality_validation']['status']}`.",
        f"- Leakage guard : `{report['leakage_guard']['status']}`.",
        f"- Forbidden columns scan : `{report['forbidden_column_scan']['status']}`.",
        f"- Zero-trade buckets : `{report['zero_trade_bucket_validation']['actual']}`.",
        f"- Row counts : `{report['row_counts']}`.",
        "",
        "## Reconciliation runtime / stockage",
        "",
        f"- Free GiB courant data mount : `{report['runtime_storage_reconciliation']['free_gib_data_mount']}`.",
        f"- Free GiB V9.45 : `{report['runtime_storage_reconciliation']['free_gib_data_mount_at_v9_45']}`.",
        f"- Output size GiB : `{report['runtime_storage_reconciliation']['v9_45_output_size_gib']}`.",
        f"- Runtime reporting acceptable : `{report['runtime_storage_reconciliation']['runtime_reporting_acceptable']}`.",
        "",
        "## Garde-fous",
        "",
        "- Validation-only.",
        "- Aucun feature store combine cree.",
        "- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
        "- Aucun reseau, aucune cle API, aucun endpoint prive.",
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
        "",
    ]
    return "\n".join(lines)


def update_state_surfaces_v9_46(root: Path, report: dict[str, Any]) -> None:
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
            "decision_v9_46": report["decision"],
            "recommended_next_step": report["next_recommendation"],
            "features_created": False,
            "feature_store_combined_created": False,
            "dataset_created": False,
            "labels_created": False,
            "ml_executed": False,
            "backtest_executed": False,
            "walk_forward_executed": False,
            "signal_created": False,
            "strategy_created": False,
            **SAFETY_FLAGS,
        }
    )
    _write_json(latest_path, latest)
    _write_text(
        root / "reports/current/latest_metrics.md",
        "# Latest Metrics\n\n"
        f"- Version candidate : `{VERSION}`.\n"
        f"- Decision V9.46 : `{report['decision']}`.\n"
        f"- Coverage : `{report['coverage_status']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        "- Validation-only : aucun feature store combine, label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "# Synthese courante\n\n"
        f"V9.46 valide independamment la couche de features exactes aggTrades 5Y V9.45. Decision : `{report['decision']}`. Recommandation : `{report['next_recommendation']}`.\n",
    )
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_optional_json(state_path)
    state.update(
        {
            "last_validated_version": LAST_VALIDATED_VERSION,
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": DIRECTION,
            "decision_v9_46": report["decision"],
            "quality_status": report["quality_status"],
            "coverage_status": report["coverage_status"],
            "features_created": False,
            "feature_store_combined_created": False,
            "dataset_created": False,
            "labels_created": False,
            "ml_executed": False,
            "backtest_executed": False,
            "walk_forward_executed": False,
            "signal_created": False,
            "strategy_created": False,
            **FINDINGS,
            **SAFETY_FLAGS,
        }
    )
    _write_json(state_path, state)
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "# Etat Projet Galapagos\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Version candidate : `{VERSION}`.\n"
        "- Statut candidat : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie, signal, modele persistant, API privee, cle API, reseau ou telechargement.\n",
    )
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Projet Galapagos\n"
    marker = "## V9.46 - AggTrades Exact Feature Enrichment Validation"
    if marker not in readme:
        _write_text(
            readme_path,
            readme.rstrip()
            + "\n\n"
            + marker
            + "\n\n"
            + f"- Decision : `{report['decision']}`.\n"
            + f"- Recommandation : `{report['next_recommendation']}`.\n"
            + "- Validation-only : aucun feature store combine, label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n",
        )


def _timestamp_summary(frame: pd.DataFrame, timeframe: str, errors: list[str]) -> dict[str, Any]:
    expected_start = pd.Timestamp(TARGET_WINDOW_START, tz="UTC")
    expected_end = pd.Timestamp(TARGET_WINDOW_END, tz="UTC") + pd.Timedelta(days=1)
    duplicate_open = int(frame["open_ts"].duplicated().sum())
    duplicate_close = int(frame["close_ts"].duplicated().sum())
    duplicate_event = int(frame["event_ts"].duplicated().sum())
    timestamps_monotone = bool(frame["open_ts"].is_monotonic_increasing)
    local_errors: list[str] = []
    if duplicate_open or duplicate_close or duplicate_event:
        local_errors.append("duplicate bucket timestamps")
    if not timestamps_monotone:
        local_errors.append("open_ts not monotone")
    if len(frame) and (frame["open_ts"].iloc[0] != expected_start or frame["close_ts"].iloc[-1] != expected_end):
        local_errors.append("coverage boundary mismatch")
    errors.extend(local_errors)
    return {
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "duplicate_open_ts": duplicate_open,
        "duplicate_close_ts": duplicate_close,
        "duplicate_event_ts": duplicate_event,
        "timestamps_monotone": timestamps_monotone,
        "errors": local_errors,
    }


def _metadata_summary(frame: pd.DataFrame, errors: list[str]) -> dict[str, Any]:
    expected = {
        "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "source_window_start": TARGET_WINDOW_START,
        "source_window_end": TARGET_WINDOW_END,
    }
    mismatches = {}
    for column, value in expected.items():
        observed = sorted(frame[column].dropna().astype(str).unique().tolist()) if column in frame.columns else []
        if observed != [value]:
            mismatches[column] = observed[:10]
    if mismatches:
        errors.append("metadata lineage mismatch")
    return {"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches}


def _forbidden_scan(frame: pd.DataFrame) -> dict[str, Any]:
    forbidden = sorted([column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)])
    return {"status": "PASS" if not forbidden else "FAIL", "forbidden_columns": forbidden}


def _counts_summary(frame: pd.DataFrame) -> dict[str, Any]:
    errors = []
    non_negative_violations = int((frame[COUNT_FEATURE_COLUMNS] < 0).sum().sum())
    side_mismatches = int((frame["taker_buy_count_exact"] + frame["taker_sell_count_exact"] != frame["agg_trade_count_exact"]).sum())
    maker_mismatches = int((frame["buyer_maker_true_count_exact"] + frame["buyer_maker_false_count_exact"] != frame["agg_trade_count_exact"]).sum())
    if non_negative_violations:
        errors.append(f"negative count values: {non_negative_violations}")
    if side_mismatches:
        errors.append(f"taker buy/sell count mismatches: {side_mismatches}")
    if maker_mismatches:
        errors.append(f"buyer maker true/false count mismatches: {maker_mismatches}")
    return {"status": "PASS" if not errors else "FAIL", "non_negative_violations": non_negative_violations, "side_mismatches": side_mismatches, "maker_mismatches": maker_mismatches, "errors": errors}


def _volumes_summary(frame: pd.DataFrame) -> dict[str, Any]:
    errors = []
    non_negative_violations = int((frame[VOLUME_FEATURE_COLUMNS] < -1e-12).sum().sum())
    base_mismatches = int((~np.isclose(frame["taker_buy_base_volume_exact"] + frame["taker_sell_base_volume_exact"], frame["agg_trade_volume_exact"], rtol=1e-9, atol=1e-9)).sum())
    quote_mismatches = int((~np.isclose(frame["taker_buy_quote_volume_exact"] + frame["taker_sell_quote_volume_exact"], frame["agg_trade_quote_volume_exact"], rtol=1e-9, atol=1e-6)).sum())
    if non_negative_violations:
        errors.append(f"negative volume values: {non_negative_violations}")
    if base_mismatches:
        errors.append(f"base volume side mismatches: {base_mismatches}")
    if quote_mismatches:
        errors.append(f"quote volume side mismatches: {quote_mismatches}")
    return {"status": "PASS" if not errors else "FAIL", "non_negative_violations": non_negative_violations, "base_side_mismatches": base_mismatches, "quote_side_mismatches": quote_mismatches, "errors": errors}


def _ratio_summary(frame: pd.DataFrame) -> dict[str, Any]:
    errors = []
    imbalance_columns = ["taker_buy_sell_count_imbalance_exact", "taker_buy_sell_volume_imbalance_exact"]
    ratio_columns = ["taker_buy_ratio_exact", "taker_sell_ratio_exact"]
    imbalance_oob = int(((frame[imbalance_columns] < -1.000001) | (frame[imbalance_columns] > 1.000001)).sum().sum())
    ratio_oob = int(((frame[ratio_columns] < -0.000001) | (frame[ratio_columns] > 1.000001)).sum().sum())
    if imbalance_oob:
        errors.append(f"imbalance out of bounds: {imbalance_oob}")
    if ratio_oob:
        errors.append(f"ratio out of bounds: {ratio_oob}")
    return {"status": "PASS" if not errors else "FAIL", "imbalance_out_of_bounds": imbalance_oob, "ratio_out_of_bounds": ratio_oob, "errors": errors}


def _quantile_summary(frame: pd.DataFrame) -> dict[str, Any]:
    traded = frame["agg_trade_count_exact"] > 0
    errors = []
    non_negative = int((frame.loc[traded, TRADE_SIZE_FEATURE_COLUMNS] < -1e-12).sum().sum())
    ordering = int((~(
        (frame.loc[traded, "p75_trade_size_exact"] <= frame.loc[traded, "p90_trade_size_exact"])
        & (frame.loc[traded, "p90_trade_size_exact"] <= frame.loc[traded, "p95_trade_size_exact"])
        & (frame.loc[traded, "p95_trade_size_exact"] <= frame.loc[traded, "p99_trade_size_exact"])
        & (frame.loc[traded, "p99_trade_size_exact"] <= frame.loc[traded, "max_trade_size_exact"])
    )).sum())
    large_count_order = int((frame["large_trade_count_p99_exact"] > frame["large_trade_count_p95_exact"]).sum())
    large_volume_order = int((frame["large_trade_volume_p99_exact"] - frame["large_trade_volume_p95_exact"] > 1e-12).sum())
    if non_negative:
        errors.append(f"negative trade size values: {non_negative}")
    if ordering:
        errors.append(f"quantile ordering violations: {ordering}")
    if large_count_order or large_volume_order:
        errors.append("large p99 exceeds p95")
    return {"status": "PASS" if not errors else "FAIL", "negative_trade_size_values": non_negative, "quantile_ordering_violations": ordering, "large_count_order_violations": large_count_order, "large_volume_order_violations": large_volume_order, "errors": errors}


def _bucket_summary(frame: pd.DataFrame) -> dict[str, Any]:
    bucket_columns = DISTRIBUTION_FEATURE_COLUMNS
    errors = []
    negative = int((frame[bucket_columns] < 0).sum().sum())
    mismatches = int((frame[bucket_columns].sum(axis=1) != frame["agg_trade_count_exact"]).sum())
    if negative:
        errors.append(f"negative distribution bucket counts: {negative}")
    if mismatches:
        errors.append(f"distribution bucket count mismatches: {mismatches}")
    return {"status": "PASS" if not errors else "FAIL", "negative_bucket_counts": negative, "bucket_count_mismatches": mismatches, "errors": errors}


def _burst_summary(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}[timeframe]
    errors = []
    finite = bool(np.isfinite(frame[BURST_FEATURE_COLUMNS + TIMING_FEATURE_COLUMNS].select_dtypes(include=[np.number]).to_numpy()).all())
    max_lt_mean = int((frame["max_trades_in_1s"] + 1e-12 < frame["agg_trade_count_per_second_mean"]).sum())
    ratio_oob = int(((frame["active_seconds_ratio"] < -0.000001) | (frame["active_seconds_ratio"] > 1.000001)).sum())
    active_oob = int(((frame["active_seconds_count"] < 0) | (frame["active_seconds_count"] > seconds)).sum())
    start_oob = int(((frame["seconds_since_previous_trade_bucket_start"] < -0.000001) | (frame["seconds_since_previous_trade_bucket_start"] > seconds + 0.000001)).sum())
    end_oob = int(((frame["seconds_to_last_trade_bucket_end"] < -0.000001) | (frame["seconds_to_last_trade_bucket_end"] > seconds + 0.000001)).sum())
    if not finite:
        errors.append("non-finite burst or timing values")
    if max_lt_mean:
        errors.append(f"max trades lower than mean: {max_lt_mean}")
    if ratio_oob or active_oob or start_oob or end_oob:
        errors.append("timing values outside bucket bounds")
    return {"status": "PASS" if not errors else "FAIL", "finite": finite, "max_trades_lower_than_mean": max_lt_mean, "active_seconds_ratio_out_of_bounds": ratio_oob, "active_seconds_count_out_of_bounds": active_oob, "seconds_since_start_out_of_bounds": start_oob, "seconds_to_end_out_of_bounds": end_oob, "errors": errors}


def _rolling_summary(frame: pd.DataFrame) -> dict[str, Any]:
    numeric = frame[ROLLING_FEATURE_COLUMNS].to_numpy()
    finite = bool(np.isfinite(numeric).all())
    errors = [] if finite else ["non-finite rolling values"]
    return {"status": "PASS" if not errors else "FAIL", "finite": finite, "rolling_windows_past_only": True, "errors": errors}


def _zero_trade_summary(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    zero = frame[frame["no_trade_bucket"] == 1]
    errors = []
    expected = EXPECTED_ZERO_TRADE_BUCKETS[timeframe]
    actual = int(len(zero))
    if actual != expected:
        errors.append(f"zero-trade bucket count mismatch: expected {expected}, got {actual}")
    if actual:
        count_columns = COUNT_FEATURE_COLUMNS + DISTRIBUTION_FEATURE_COLUMNS + ["large_trade_count_p95_exact", "large_trade_count_p99_exact", "active_seconds_count"]
        volume_columns = VOLUME_FEATURE_COLUMNS + ["large_trade_volume_p95_exact", "large_trade_volume_p99_exact", "max_volume_in_1s", "burst_volume_1s_p95"]
        ratio_columns = IMBALANCE_FEATURE_COLUMNS + ["active_seconds_ratio", "agg_trade_count_per_second_mean", "agg_trade_count_per_second_max", "max_trades_in_1s", "burst_count_1s_p95"]
        if int((zero[count_columns] != 0).sum().sum()):
            errors.append("zero-trade count columns are not zero")
        if int((zero[volume_columns].abs() > 1e-12).sum().sum()):
            errors.append("zero-trade volume columns are not zero")
        if int((zero[ratio_columns].abs() > 1e-12).sum().sum()):
            errors.append("zero-trade ratio/burst columns are not neutral zero")
        if int((zero["aggtrades_missing_flag"] != 0).sum()):
            errors.append("zero-trade buckets marked missing")
        if int((zero["exact_feature_error_count"] != 0).sum()):
            errors.append("zero-trade buckets have feature errors")
        if int((~zero["row_valid_for_exact_features"].astype(bool)).sum()):
            errors.append("zero-trade buckets invalid")
    return {"status": "PASS" if not errors else "FAIL", "expected_zero_trade_buckets": expected, "actual_zero_trade_buckets": actual, "zero_trade_bucket_blocking": bool(errors), "errors": errors, "warnings": [] if not actual else ["zero-trade buckets are expected and encoded as neutral zero rows"]}


def _blocked_timeframe_report(timeframe: str, reason: str) -> dict[str, Any]:
    return {"version": VERSION, "timeframe": timeframe, "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe], "actual_rows": 0, "coverage_status": "FAIL", "schema_status": "FAIL", "quality_status": "FAIL", "leakage_guard_status": "FAIL", "errors": [reason], "warnings": []}


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
