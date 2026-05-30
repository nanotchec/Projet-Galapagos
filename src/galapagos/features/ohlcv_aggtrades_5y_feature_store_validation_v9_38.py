from __future__ import annotations

import gc
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import (
    AGGTRADES_SOURCE_TYPE,
    AUDIT_COLUMNS,
    EXPECTED_DAYS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_FAMILIES,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_COLUMNS,
    MARKET_TYPE,
    METADATA_COLUMNS,
    OHLCV_SOURCE_TYPE,
    SOURCE,
    SOURCE_AGGTRADES_VALIDATION_VERSION,
    SOURCE_OHLCV_VALIDATION_VERSION,
    STRICT_COLUMNS,
    SYMBOL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VENUE,
)


VERSION = "V9.38"
SOURCE_VERSION = "V9.37"
LAST_VALIDATED_VERSION = "V9.37"
DIRECTION = "ohlcv_aggtrades_5y_feature_store_validation"

REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_validation_v9_38_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_feature_store_validation_v9_38.md")

INPUT_PATHS = {
    "v9_37_report": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_37_markdown": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.md"),
    "v9_37_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_37_manifest.json"),
    "v9_36_validation": Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    "v9_36_zero_trade": Path("reports/data/ohlcv_from_aggtrades_5y_zero_trade_buckets_v9_36.json"),
    "v9_32_aggtrades": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_35_ohlcv": Path("reports/data/ohlcv_from_aggtrades_5y_v9_35.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_5y_feature_store_validated",
    "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_coverage",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_schema",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_quality",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_leakage",
    "ohlcv_aggtrades_5y_feature_store_inconclusive_manual_review_required",
    "stop_ohlcv_aggtrades_5y_feature_branch",
}

SAFETY_FLAGS_V9_38 = {
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

FINDINGS_V9_38 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}


def run_ohlcv_aggtrades_5y_feature_store_validation_v9_38(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_feature_store_validation_report_v9_38(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_38(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_38(report))
    update_state_surfaces_v9_38(root, report)
    return report


def build_feature_store_validation_report_v9_38(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    source_readiness = validate_source_readiness_v9_38(inputs)
    timeframe_reports: dict[str, dict[str, Any]] = {}
    if source_readiness["ready"]:
        for timeframe in EXPECTED_TIMEFRAMES:
            path = feature_output_path_v9_38(root, timeframe)
            timeframe_reports[timeframe] = validate_feature_file_v9_38(path=path, timeframe=timeframe)
            gc.collect()
    coverage_validation = build_coverage_validation_v9_38(timeframe_reports)
    schema_validation = build_schema_validation_v9_38(timeframe_reports)
    quality_validation = build_quality_validation_v9_38(timeframe_reports)
    leakage_guard = build_leakage_guard_v9_38(timeframe_reports)
    zero_trade_validation = build_zero_trade_validation_v9_38(inputs, timeframe_reports)
    limitations = build_aggtrades_limitations_v9_38()
    blockers = build_blockers_v9_38(
        source_readiness,
        coverage_validation,
        schema_validation,
        quality_validation,
        leakage_guard,
        zero_trade_validation,
    )
    warnings = build_warnings_v9_38(timeframe_reports, zero_trade_validation, limitations)
    decision = decide_v9_38(blockers, warnings, coverage_validation, schema_validation, quality_validation, leakage_guard)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "source_versions": {
            "feature_store": SOURCE_VERSION,
            "ohlcv_validation": SOURCE_OHLCV_VALIDATION_VERSION,
            "aggtrades_validation": SOURCE_AGGTRADES_VALIDATION_VERSION,
        },
        "status": "PASS" if decision["decision"] in {"ohlcv_aggtrades_5y_feature_store_validated", "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "decision": decision["decision"],
        "decision_details": decision,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": EXPECTED_DAYS},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "expected_rows": dict(EXPECTED_ROWS_BY_TIMEFRAME),
        "actual_rows": {timeframe: item.get("actual_rows") for timeframe, item in timeframe_reports.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "metadata_columns": list(METADATA_COLUMNS),
        "audit_columns": list(AUDIT_COLUMNS),
        "feature_families": FEATURE_FAMILIES,
        "feature_store_validation": timeframe_reports,
        "coverage_validation": coverage_validation,
        "schema_validation": schema_validation,
        "quality_validation": quality_validation,
        "leakage_guard": leakage_guard,
        "zero_trade_bucket_validation": zero_trade_validation,
        "aggtrades_feature_limitations": limitations,
        "source_readiness": source_readiness,
        "quality_status": quality_validation["status"],
        "coverage_status": coverage_validation["status"],
        "schema_status": schema_validation["status"],
        "leakage_guard_status": leakage_guard["status"],
        "blockers": blockers,
        "warnings": warnings,
        "next_recommendation": decision["next_recommendation"],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "features_full_modified": False,
        "findings": dict(FINDINGS_V9_38),
        "safety_flags": dict(SAFETY_FLAGS_V9_38),
    }
    return report


def validate_feature_file_v9_38(*, path: Path, timeframe: str) -> dict[str, Any]:
    if not path.is_file():
        return _failed_timeframe(timeframe, path, [f"missing_feature_file={path.as_posix()}"])
    try:
        frame = pd.read_parquet(path, engine="pyarrow")
    except Exception as exc:  # pragma: no cover - exercised only when local parquet engine/file fails.
        return _failed_timeframe(timeframe, path, [f"feature_file_read_error={type(exc).__name__}: {exc}"])
    return validate_feature_frame_v9_38(frame, timeframe=timeframe, path=path)


def validate_feature_frame_v9_38(frame: pd.DataFrame, *, timeframe: str, path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = sorted(set(STRICT_COLUMNS) - set(frame.columns))
    extra_columns = sorted(set(frame.columns) - set(STRICT_COLUMNS))
    forbidden_columns = sorted(set(frame.columns) & FORBIDDEN_FEATURE_COLUMNS)
    if missing_columns:
        errors.append(f"missing_columns={missing_columns}")
    if extra_columns:
        errors.append(f"extra_columns={extra_columns}")
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict_column_order_mismatch")
    if forbidden_columns:
        errors.append(f"forbidden_columns={forbidden_columns}")
    if missing_columns:
        return _failed_timeframe(timeframe, path, errors, warnings)
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    feature_available_ts = pd.to_datetime(frame["feature_available_ts"], utc=True)
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    days = sorted(set(event_ts.dt.date.astype(str)))
    expected_days = _date_range(TARGET_WINDOW_START, TARGET_WINDOW_END)
    missing_days = sorted(set(expected_days) - set(days))
    duplicate_event_ts = int(event_ts.duplicated().sum())
    duplicate_close_ts = int(close_ts.duplicated().sum())
    duplicate_open_ts = int(open_ts.duplicated().sum())
    feature_available_violations = int((feature_available_ts > decision_ts).sum())
    available_violations = int((available_ts > decision_ts).sum())
    event_open_mismatch = int((event_ts != open_ts).sum())
    decision_close_mismatch = int((decision_ts != close_ts).sum())
    row_invalid = int((frame["row_valid_for_features"] != True).sum())  # noqa: E712
    feature_error_count_total = int(pd.to_numeric(frame["feature_error_count"], errors="coerce").fillna(1).sum())
    non_warmup = frame["warmup_row"] != True  # noqa: E712
    nulls_outside_warmup = int(frame.loc[non_warmup, FEATURE_COLUMNS].isna().sum().sum())
    numeric_features = frame[FEATURE_COLUMNS].select_dtypes(include=[np.number])
    inf_count = int(np.isinf(numeric_features.to_numpy(dtype="float64", copy=False)).sum()) if not numeric_features.empty else 0
    range_summary, range_errors, outlier_warnings = build_feature_range_summary_v9_38(frame)
    rolling_errors = validate_rolling_features_v9_38(frame)
    metadata_errors = validate_metadata_lineage_v9_38(frame, timeframe)
    zero_trade_summary, zero_trade_errors = validate_zero_trade_rows_v9_38(frame)
    for label, value in {
        "actual_rows_mismatch": int(len(frame) != expected_rows),
        "days_missing": len(missing_days),
        "duplicate_event_ts": duplicate_event_ts,
        "duplicate_close_ts": duplicate_close_ts,
        "duplicate_open_ts": duplicate_open_ts,
        "feature_available_ts_after_decision_ts": feature_available_violations,
        "available_ts_after_decision_ts": available_violations,
        "event_ts_not_open_ts": event_open_mismatch,
        "decision_ts_not_close_ts": decision_close_mismatch,
        "row_invalid_for_features": row_invalid,
        "feature_error_count_total": feature_error_count_total,
        "feature_nulls_outside_warmup": nulls_outside_warmup,
        "feature_inf_count": inf_count,
    }.items():
        if value:
            errors.append(f"{label}={value}")
    errors.extend(range_errors)
    errors.extend(rolling_errors)
    errors.extend(metadata_errors)
    errors.extend(zero_trade_errors)
    warnings.extend(outlier_warnings)
    null_summary = {column: int(frame[column].isna().sum()) for column in FEATURE_COLUMNS}
    warmup_rows = int((frame["warmup_row"] == True).sum())  # noqa: E712
    report = {
        "timeframe": timeframe,
        "path": path.as_posix(),
        "file_exists": True,
        "file_readable": True,
        "file_bytes": path.stat().st_size if path.exists() else 0,
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS - len(missing_days),
        "days_missing": len(missing_days),
        "coverage_start": days[0] if days else None,
        "coverage_end": days[-1] if days else None,
        "complete_calendar_coverage": len(frame) == expected_rows and not missing_days,
        "timestamps_monotone": bool(event_ts.is_monotonic_increasing and close_ts.is_monotonic_increasing),
        "duplicate_event_ts_count": duplicate_event_ts,
        "duplicate_close_ts_count": duplicate_close_ts,
        "duplicate_open_ts_count": duplicate_open_ts,
        "strict_schema_status": "PASS" if not missing_columns and not extra_columns and list(frame.columns) == STRICT_COLUMNS else "FAIL",
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "forbidden_columns": forbidden_columns,
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_schema_version_values": sorted(str(value) for value in frame["feature_schema_version"].dropna().unique()),
        "feature_run_id_values": sorted(str(value) for value in frame["feature_run_id"].dropna().unique())[:5],
        "source_lineage_status": "PASS" if not metadata_errors else "FAIL",
        "feature_available_ts_lte_decision_ts": feature_available_violations == 0,
        "available_ts_lte_decision_ts": available_violations == 0,
        "rolling_windows_past_only_status": "PASS" if not rolling_errors else "FAIL",
        "null_summary": null_summary,
        "nulls_outside_warmup": nulls_outside_warmup,
        "warmup_summary": {
            "warmup_rows": warmup_rows,
            "expected_warmup_rows": 60,
            "non_warmup_rows": int((frame["warmup_row"] != True).sum()),  # noqa: E712
        },
        "invalid_row_summary": {
            "feature_error_count_total": feature_error_count_total,
            "row_valid_for_features_count": int((frame["row_valid_for_features"] == True).sum()),  # noqa: E712
            "row_invalid_for_features_count": row_invalid,
            "feature_invalid_reason_non_empty": int((frame["feature_invalid_reason"].astype(str) != "").sum()),
        },
        "feature_range_summary": range_summary,
        "outlier_warning_summary": warnings,
        "zero_trade_bucket_summary": zero_trade_summary,
        "quality_status": "PASS" if not errors else "FAIL",
        "coverage_status": "PASS" if len(frame) == expected_rows and not missing_days else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }
    return report


def build_feature_range_summary_v9_38(frame: pd.DataFrame) -> tuple[dict[str, dict[str, float | int | None]], list[str], list[str]]:
    summary: dict[str, dict[str, float | int | None]] = {}
    errors: list[str] = []
    warnings: list[str] = []
    for column in FEATURE_COLUMNS:
        series = pd.to_numeric(frame[column], errors="coerce") if column != "zero_trade_bucket" else frame[column].astype("int8")
        finite = series[np.isfinite(series.to_numpy(dtype="float64", na_value=np.nan))]
        summary[column] = {
            "nulls": int(series.isna().sum()),
            "min": _safe_float(finite.min()) if len(finite) else None,
            "max": _safe_float(finite.max()) if len(finite) else None,
        }
    for column in ["volume", "quote_volume", "trades_count", "agg_trade_count", "agg_trade_volume", "agg_trade_quote_volume", "average_trade_size", "taker_buy_base_volume", "taker_sell_base_volume"]:
        negative = int((pd.to_numeric(frame[column], errors="coerce").fillna(0) < 0).sum())
        if negative:
            errors.append(f"{column}_negative_count={negative}")
    ratio = pd.to_numeric(frame["taker_buy_ratio"], errors="coerce").dropna()
    ratio_bad = int(((ratio < -1e-12) | (ratio > 1.0 + 1e-12)).sum())
    if ratio_bad:
        errors.append(f"taker_buy_ratio_out_of_bounds={ratio_bad}")
    imbalance = pd.to_numeric(frame["taker_buy_sell_imbalance"], errors="coerce").dropna()
    imbalance_bad = int(((imbalance < -1.0 - 1e-12) | (imbalance > 1.0 + 1e-12)).sum())
    if imbalance_bad:
        errors.append(f"taker_buy_sell_imbalance_out_of_bounds={imbalance_bad}")
    rolling_zero = pd.to_numeric(frame["zero_trade_bucket_rolling_count_60"], errors="coerce").dropna()
    rolling_zero_bad = int(((rolling_zero < 0) | (rolling_zero > 60)).sum())
    if rolling_zero_bad:
        errors.append(f"zero_trade_bucket_rolling_count_60_out_of_bounds={rolling_zero_bad}")
    missing_flag_values = set(pd.to_numeric(frame["missing_aggtrades_flag"], errors="coerce").dropna().astype(int).unique())
    if not missing_flag_values.issubset({0, 1}):
        errors.append(f"missing_aggtrades_flag_invalid_values={sorted(missing_flag_values)}")
    for column in ["close_return_1", "log_return_1", "rolling_return_5", "rolling_return_15", "rolling_return_60"]:
        series = pd.to_numeric(frame[column], errors="coerce").dropna()
        extreme = int((series.abs() > 0.5).sum())
        if extreme:
            warnings.append(f"{column}: {extreme} valeurs absolues > 0.5 a examiner comme outliers non bloquants")
    return summary, errors, warnings


def validate_rolling_features_v9_38(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    checks = {
        "volume_rolling_mean_5": frame["volume"].rolling(5, min_periods=5).mean(),
        "volume_rolling_mean_15": frame["volume"].rolling(15, min_periods=15).mean(),
        "volume_rolling_mean_60": frame["volume"].rolling(60, min_periods=60).mean(),
        "volume_rolling_std_5": frame["volume"].rolling(5, min_periods=5).std(),
        "volume_rolling_std_15": frame["volume"].rolling(15, min_periods=15).std(),
        "volume_rolling_std_60": frame["volume"].rolling(60, min_periods=60).std(),
        "trade_intensity_rolling_5": frame["trades_count"].rolling(5, min_periods=5).mean(),
        "trade_intensity_rolling_15": frame["trades_count"].rolling(15, min_periods=15).mean(),
        "trade_intensity_rolling_60": frame["trades_count"].rolling(60, min_periods=60).mean(),
        "agg_trade_volume_rolling_mean_5": frame["agg_trade_volume"].rolling(5, min_periods=5).mean(),
        "agg_trade_volume_rolling_mean_15": frame["agg_trade_volume"].rolling(15, min_periods=15).mean(),
        "agg_trade_volume_rolling_mean_60": frame["agg_trade_volume"].rolling(60, min_periods=60).mean(),
        "zero_trade_bucket_rolling_count_60": frame["zero_trade_bucket"].astype("int64").rolling(60, min_periods=1).sum(),
    }
    denominator = frame["volume"].replace(0, np.nan)
    imbalance = pd.Series(np.where(frame["volume"] > 0, (frame["taker_buy_base_volume"] - frame["taker_sell_base_volume"]) / denominator, 0.0), index=frame.index)
    checks.update(
        {
            "taker_imbalance_rolling_mean_5": imbalance.rolling(5, min_periods=5).mean(),
            "taker_imbalance_rolling_mean_15": imbalance.rolling(15, min_periods=15).mean(),
            "taker_imbalance_rolling_mean_60": imbalance.rolling(60, min_periods=60).mean(),
        }
    )
    for column, expected in checks.items():
        actual = pd.to_numeric(frame[column], errors="coerce")
        mismatch = _series_mismatch_count(actual, expected)
        if mismatch:
            errors.append(f"{column}_rolling_mismatch={mismatch}")
    return errors


def validate_metadata_lineage_v9_38(frame: pd.DataFrame, timeframe: str) -> list[str]:
    expected = {
        "source": SOURCE,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "timeframe": timeframe,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "ohlcv_source_type": OHLCV_SOURCE_TYPE,
        "aggtrades_source_type": AGGTRADES_SOURCE_TYPE,
        "source_ohlcv_validation_version": SOURCE_OHLCV_VALIDATION_VERSION,
        "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "source_window_start": TARGET_WINDOW_START,
        "source_window_end": TARGET_WINDOW_END,
    }
    errors: list[str] = []
    for column, expected_value in expected.items():
        values = set(str(value) for value in frame[column].dropna().unique())
        if values != {expected_value}:
            errors.append(f"{column}_lineage_mismatch={sorted(values)[:5]}")
    if frame["feature_run_id"].isna().any() or len(frame["feature_run_id"].dropna().unique()) != 1:
        errors.append("feature_run_id_must_be_single_non_null_value")
    return errors


def validate_zero_trade_rows_v9_38(frame: pd.DataFrame) -> tuple[dict[str, Any], list[str]]:
    zero = frame["zero_trade_bucket"] == True  # noqa: E712
    zero_count = int(zero.sum())
    errors: list[str] = []
    for column in ["volume", "quote_volume", "trades_count", "agg_trade_count", "agg_trade_volume", "agg_trade_quote_volume"]:
        violations = int((pd.to_numeric(frame.loc[zero, column], errors="coerce").fillna(-1) != 0).sum())
        if violations:
            errors.append(f"zero_trade_{column}_non_zero={violations}")
    missing_flag_mismatch = int((frame["missing_aggtrades_flag"].astype("int64") != zero.astype("int64")).sum())
    if missing_flag_mismatch:
        errors.append(f"missing_aggtrades_flag_zero_trade_mismatch={missing_flag_mismatch}")
    rolling_expected = zero.astype("int64").rolling(60, min_periods=1).sum()
    rolling_mismatch = _series_mismatch_count(pd.to_numeric(frame["zero_trade_bucket_rolling_count_60"], errors="coerce"), rolling_expected)
    if rolling_mismatch:
        errors.append(f"zero_trade_bucket_rolling_count_60_mismatch={rolling_mismatch}")
    return {
        "zero_trade_rows": zero_count,
        "zero_trade_ratio": float(zero.mean()) if len(frame) else 0.0,
        "volume_zero_on_zero_trade": not any(error.startswith("zero_trade_volume") for error in errors),
        "trades_count_zero_on_zero_trade": not any(error.startswith("zero_trade_trades_count") for error in errors),
        "agg_trade_count_zero_on_zero_trade": not any(error.startswith("zero_trade_agg_trade_count") for error in errors),
        "rolling_count_coherent": rolling_mismatch == 0,
        "no_future_fill": True,
        "zero_trade_bucket_blocking": bool(errors),
    }, errors


def build_coverage_validation_v9_38(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "target_5y_feature_window_complete" if timeframe_reports and all(item.get("coverage_status") == "PASS" for item in timeframe_reports.values()) and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL",
        "timeframes": {
            timeframe: {
                "file_exists": item.get("file_exists"),
                "file_readable": item.get("file_readable"),
                "expected_rows": item.get("expected_rows"),
                "actual_rows": item.get("actual_rows"),
                "days_expected": item.get("days_expected"),
                "days_missing": item.get("days_missing"),
                "coverage_start": item.get("coverage_start"),
                "coverage_end": item.get("coverage_end"),
                "timestamps_monotone": item.get("timestamps_monotone"),
                "duplicate_event_ts_count": item.get("duplicate_event_ts_count"),
                "duplicate_close_ts_count": item.get("duplicate_close_ts_count"),
                "complete_calendar_coverage": item.get("complete_calendar_coverage"),
                "coverage_status": item.get("coverage_status"),
            }
            for timeframe, item in timeframe_reports.items()
        },
    }


def build_schema_validation_v9_38(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors = [
        f"{timeframe}: schema failed"
        for timeframe, item in timeframe_reports.items()
        if item.get("strict_schema_status") != "PASS" or item.get("forbidden_columns")
    ]
    return {
        "status": "PASS" if not errors and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL",
        "errors": errors,
        "metadata_columns": list(METADATA_COLUMNS),
        "feature_columns": list(FEATURE_COLUMNS),
        "audit_columns": list(AUDIT_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "source_ohlcv_validation_version": SOURCE_OHLCV_VALIDATION_VERSION,
        "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "ohlcv_source_type": OHLCV_SOURCE_TYPE,
        "aggtrades_source_type": AGGTRADES_SOURCE_TYPE,
        "forbidden_scan": build_forbidden_scan_v9_38(timeframe_reports),
    }


def build_quality_validation_v9_38(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors = [f"{timeframe}: {error}" for timeframe, item in timeframe_reports.items() for error in item.get("errors", [])]
    return {
        "status": "PASS" if not errors and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL",
        "errors": errors,
        "null_summary_by_timeframe": {timeframe: item.get("null_summary", {}) for timeframe, item in timeframe_reports.items()},
        "warmup_summary_by_timeframe": {timeframe: item.get("warmup_summary", {}) for timeframe, item in timeframe_reports.items()},
        "invalid_row_summary_by_timeframe": {timeframe: item.get("invalid_row_summary", {}) for timeframe, item in timeframe_reports.items()},
        "feature_range_summary_by_timeframe": {timeframe: item.get("feature_range_summary", {}) for timeframe, item in timeframe_reports.items()},
        "outlier_warning_summary_by_timeframe": {timeframe: item.get("outlier_warning_summary", []) for timeframe, item in timeframe_reports.items()},
    }


def build_leakage_guard_v9_38(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    leakage_errors = [
        f"{timeframe}: leakage guard failed"
        for timeframe, item in timeframe_reports.items()
        if item.get("feature_available_ts_lte_decision_ts") is not True
        or item.get("available_ts_lte_decision_ts") is not True
        or item.get("rolling_windows_past_only_status") != "PASS"
        or item.get("forbidden_columns")
    ]
    return {
        "status": "PASS" if not leakage_errors and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL",
        "feature_available_ts_lte_decision_ts": all(item.get("feature_available_ts_lte_decision_ts") is True for item in timeframe_reports.values()) if timeframe_reports else False,
        "available_ts_lte_decision_ts": all(item.get("available_ts_lte_decision_ts") is True for item in timeframe_reports.values()) if timeframe_reports else False,
        "rolling_windows_past_only": all(item.get("rolling_windows_past_only_status") == "PASS" for item in timeframe_reports.values()) if timeframe_reports else False,
        "forbidden_future_columns_absent": not build_forbidden_scan_v9_38(timeframe_reports)["forbidden_columns"],
        "leakage_errors": leakage_errors,
        "leakage_warnings": [],
    }


def build_zero_trade_validation_v9_38(inputs: dict[str, dict[str, Any]], timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = inputs.get("v9_36_zero_trade", {}).get("payload", {}).get("zero_trade_bucket_counts")
    if expected is None:
        expected = inputs.get("v9_35_ohlcv", {}).get("payload", {}).get("zero_trade_bucket_counts", {})
    actual = {timeframe: item.get("zero_trade_bucket_summary", {}).get("zero_trade_rows", 0) for timeframe, item in timeframe_reports.items()}
    errors: list[str] = []
    if expected and {key: int(value) for key, value in expected.items()} != {key: int(value) for key, value in actual.items()}:
        errors.append(f"zero_trade_counts_mismatch expected={expected} actual={actual}")
    errors.extend(
        f"{timeframe}: zero-trade validation failed"
        for timeframe, item in timeframe_reports.items()
        if item.get("zero_trade_bucket_summary", {}).get("zero_trade_bucket_blocking") is True
    )
    return {
        "status": "PASS" if not errors and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL",
        "expected_counts_from_v9_36": expected,
        "actual_counts": actual,
        "details_by_timeframe": {timeframe: item.get("zero_trade_bucket_summary", {}) for timeframe, item in timeframe_reports.items()},
        "zero_trade_bucket_blocking": bool(errors),
        "errors": errors,
    }


def build_aggtrades_limitations_v9_38() -> dict[str, Any]:
    return {
        "direct_aggtrades_full_scan_performed": False,
        "median_trade_size_exact_included": False,
        "large_trade_count_exact_included": False,
        "buyer_maker_count_exact_included": False,
        "non_blocking_for_current_feature_store_validation": True,
        "blocking_for_next_dataset": False,
        "notes": [
            "V9.38 valide le feature store V9.37 cree a partir des agregats aggTrades materialises dans l'OHLCV derivee V9.35.",
            "L'absence de median_trade_size exact, large_trade_count exact et buyer_maker_count exact reste une limitation documentee, non bloquante pour V9.39 si la qualite V9.38 passe.",
        ],
    }


def build_forbidden_scan_v9_38(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    found = sorted({column for item in timeframe_reports.values() for column in item.get("forbidden_columns", [])})
    return {
        "status": "PASS" if not found else "FAIL",
        "forbidden_columns": found,
        "scanned_terms": sorted(FORBIDDEN_FEATURE_COLUMNS),
    }


def validate_source_readiness_v9_38(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v9_37 = inputs["v9_37_report"].get("payload", {})
    errors: list[str] = []
    missing = [name for name, item in inputs.items() if not item.get("available")]
    if missing:
        errors.append(f"missing_inputs={missing}")
    if v9_37.get("decision") != "ohlcv_aggtrades_5y_feature_store_created_with_warnings":
        errors.append("V9.37 feature store decision is not the expected externally validated warning decision")
    if v9_37.get("quality_status") != "PASS" or v9_37.get("coverage_status") != "target_5y_feature_window_complete":
        errors.append("V9.37 feature store quality or coverage is not ready")
    if v9_37.get("feature_store_created") is not True or v9_37.get("features_created") is not True:
        errors.append("V9.37 feature store was not created")
    return {"ready": not errors, "errors": errors, "v9_37_decision": v9_37.get("decision")}


def build_blockers_v9_38(
    source_readiness: dict[str, Any],
    coverage_validation: dict[str, Any],
    schema_validation: dict[str, Any],
    quality_validation: dict[str, Any],
    leakage_guard: dict[str, Any],
    zero_trade_validation: dict[str, Any],
) -> list[str]:
    blockers = list(source_readiness.get("errors", []))
    if coverage_validation["status"] != "target_5y_feature_window_complete":
        blockers.append("coverage_validation_failed")
    if schema_validation["status"] != "PASS":
        blockers.append("schema_validation_failed")
    if quality_validation["status"] != "PASS":
        blockers.append("quality_validation_failed")
    if leakage_guard["status"] != "PASS":
        blockers.append("leakage_guard_failed")
    if zero_trade_validation["zero_trade_bucket_blocking"]:
        blockers.append("zero_trade_bucket_validation_failed")
    return blockers


def build_warnings_v9_38(
    timeframe_reports: dict[str, dict[str, Any]],
    zero_trade_validation: dict[str, Any],
    limitations: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if limitations["non_blocking_for_current_feature_store_validation"]:
        warnings.append("Les features aggTrades exactes median_trade_size, large_trade_count et buyer_maker_count restent absentes; limitation non bloquante pour V9.38.")
    for timeframe, item in timeframe_reports.items():
        warmup = item.get("warmup_summary", {}).get("warmup_rows", 0)
        zero = item.get("zero_trade_bucket_summary", {}).get("zero_trade_rows", 0)
        if warmup:
            warnings.append(f"{timeframe}: {warmup} warmup rows attendues.")
        if zero:
            warnings.append(f"{timeframe}: {zero} zero-trade buckets coherents et non bloquants.")
        warnings.extend(f"{timeframe}: {warning}" for warning in item.get("warnings", []))
    if zero_trade_validation.get("status") == "PASS":
        warnings.append("Zero-trade buckets herites de V9.36 valides comme flags causaux non bloquants.")
    return warnings


def decide_v9_38(
    blockers: list[str],
    warnings: list[str],
    coverage_validation: dict[str, Any],
    schema_validation: dict[str, Any],
    quality_validation: dict[str, Any],
    leakage_guard: dict[str, Any],
) -> dict[str, str]:
    if coverage_validation["status"] != "target_5y_feature_window_complete":
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_coverage", "next_recommendation": "V9.39 - Feature Store Correction", "justification": "La couverture du feature store est incomplete."}
    if schema_validation["status"] != "PASS":
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_schema", "next_recommendation": "V9.39 - Feature Store Correction", "justification": "Le schema strict echoue."}
    if leakage_guard["status"] != "PASS":
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_leakage", "next_recommendation": "V9.39 - Feature Store Correction", "justification": "Le leakage guard echoue."}
    if quality_validation["status"] != "PASS" or blockers:
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_quality", "next_recommendation": "V9.39 - Feature Store Correction", "justification": "La qualite des features echoue."}
    if warnings:
        return {"decision": "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings", "next_recommendation": "V9.39 - OHLCV + AggTrades 5Y Dataset", "justification": "Le feature store est valide avec warnings documentes non bloquants."}
    return {"decision": "ohlcv_aggtrades_5y_feature_store_validated", "next_recommendation": "V9.39 - OHLCV + AggTrades 5Y Dataset", "justification": "Le feature store est valide sans warning bloquant."}


def build_manifest_v9_38(report: dict[str, Any]) -> dict[str, Any]:
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
        "timeframes": report["timeframes"],
        "actual_rows": report["actual_rows"],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "schema_status": report["schema_status"],
        "leakage_guard_status": report["leakage_guard_status"],
        "features_full_modified": report["features_full_modified"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_38(report: dict[str, Any]) -> str:
    lines = [
        "# V9.38 - Validation Feature Store OHLCV + AggTrades 5Y",
        "",
        "## Resume",
        f"- Decision V9.38 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Schema : `{report['schema_status']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Leakage guard : `{report['leakage_guard_status']}`.",
        f"- Row counts : `{report['actual_rows']}`.",
        f"- Feature columns count : `{report['feature_columns_count']}`.",
        "",
        "## Zero-trade buckets",
        f"- Statut : `{report['zero_trade_bucket_validation']['status']}`.",
        f"- Counts : `{report['zero_trade_bucket_validation']['actual_counts']}`.",
        "",
        "## Limitations",
        "- V9.38 confirme que V9.37 ne rescane pas directement les 3.2B lignes aggTrades.",
        "- median_trade_size exact, large_trade_count exact et buyer_maker_count exact restent absents, non bloquants pour le dataset V9.39.",
        "",
        "## Garde-fous",
        "- Validation-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.",
        "- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_38(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_38_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "feature_store_validated": report["status"] == "PASS",
        "timeframes": report["timeframes"],
        "row_counts": report["actual_rows"],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "schema_status": report["schema_status"],
        "leakage_guard_status": report["leakage_guard_status"],
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.38\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.38 : `{report['decision']}`.\n"
        f"- Couverture : `{report['coverage_status']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        f"- Leakage guard : `{report['leakage_guard_status']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal actionnable ou ordre.\n"
        "- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, validation du feature store OHLCV + aggTrades 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def _failed_timeframe(timeframe: str, path: Path, errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "timeframe": timeframe,
        "path": path.as_posix(),
        "file_exists": path.is_file(),
        "file_readable": False,
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "actual_rows": 0,
        "days_expected": EXPECTED_DAYS,
        "days_complete": 0,
        "days_missing": EXPECTED_DAYS,
        "coverage_start": None,
        "coverage_end": None,
        "complete_calendar_coverage": False,
        "coverage_status": "FAIL",
        "strict_schema_status": "FAIL",
        "quality_status": "FAIL",
        "errors": errors,
        "warnings": warnings or [],
    }


def feature_output_path_v9_38(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_37/features/ohlcv_aggtrades_5y/source={SOURCE}/market_type={MARKET_TYPE}/symbol={SYMBOL}/timeframe={timeframe}/window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}/features.parquet"


def _series_mismatch_count(actual: pd.Series, expected: pd.Series, *, atol: float = 1e-10) -> int:
    actual_values = actual.to_numpy(dtype="float64", na_value=np.nan)
    expected_values = expected.to_numpy(dtype="float64", na_value=np.nan)
    both_nan = np.isnan(actual_values) & np.isnan(expected_values)
    close = np.isclose(actual_values, expected_values, rtol=1e-9, atol=atol, equal_nan=False)
    return int((~(both_nan | close)).sum())


def _date_range(start: str, end: str) -> list[str]:
    return [item.date().isoformat() for item in pd.date_range(start=start, end=end, freq="D", tz="UTC")]


def _safe_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


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
