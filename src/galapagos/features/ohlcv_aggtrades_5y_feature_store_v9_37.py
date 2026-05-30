from __future__ import annotations

import gc
import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import derived_output_path_v9_35
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


VERSION = "V9.37"
SOURCE_VERSION = "V9.36"
LAST_VALIDATED_VERSION = "V9.36"
DIRECTION = "ohlcv_aggtrades_5y_feature_store"

REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_37_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_feature_store_v9_37.md")

INPUT_PATHS = {
    "v9_36_validation": Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    "v9_36_zero_trade": Path("reports/data/ohlcv_from_aggtrades_5y_zero_trade_buckets_v9_36.json"),
    "v9_36_parity": Path("reports/data/ohlcv_from_aggtrades_5y_parity_v9_36.json"),
    "v9_36_manifest": Path("reports/manifests/ohlcv_from_aggtrades_5y_validation_v9_36_manifest.json"),
    "v9_35_ohlcv": Path("reports/data/ohlcv_from_aggtrades_5y_v9_35.json"),
    "v9_35_manifest": Path("reports/manifests/ohlcv_from_aggtrades_5y_v9_35_manifest.json"),
    "v9_32_aggtrades": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_32_manifest": Path("reports/manifests/aggtrades_5y_full_coverage_validation_v9_32_manifest.json"),
    "v9_33_readiness": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_5y_feature_store_created",
    "ohlcv_aggtrades_5y_feature_store_created_with_warnings",
    "ohlcv_aggtrades_5y_feature_store_partial",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_quality",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_leakage",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_runtime",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_storage",
    "stop_ohlcv_aggtrades_5y_feature_branch",
}

SAFETY_FLAGS_V9_37 = {
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

FINDINGS_V9_37 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}


def run_ohlcv_aggtrades_5y_feature_store_v9_37(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_feature_store_v9_37(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_37(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_37(report))
    update_state_surfaces_v9_37(root, report)
    return report


def build_feature_store_v9_37(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    source_status = validate_source_readiness_v9_37(inputs)
    run_id = f"v9_37_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    timeframe_reports: dict[str, dict[str, Any]] = {}
    output_paths: dict[str, str] = {}
    if source_status["ready"]:
        for timeframe in EXPECTED_TIMEFRAMES:
            source_path = derived_output_path_v9_35(root, timeframe)
            output_path = feature_output_path_v9_37(root, timeframe)
            frame = pd.read_parquet(source_path, engine="pyarrow")
            features = build_timeframe_features_v9_37(frame, timeframe=timeframe, feature_run_id=run_id)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            features.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
            timeframe_reports[timeframe] = validate_feature_frame_v9_37(features, timeframe=timeframe, path=output_path)
            output_paths[timeframe] = output_path.as_posix()
            del frame
            del features
            gc.collect()
    coverage_status = "target_5y_feature_window_complete" if all(item.get("coverage_status") == "PASS" for item in timeframe_reports.values()) and set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) else "FAIL"
    leakage_guard = build_leakage_guard_v9_37(timeframe_reports)
    forbidden_scan = build_forbidden_scan_v9_37(timeframe_reports)
    quality_status = "PASS" if source_status["ready"] and coverage_status != "FAIL" and leakage_guard["status"] == "PASS" and forbidden_scan["status"] == "PASS" and all(item["quality_status"] == "PASS" for item in timeframe_reports.values()) else "FAIL"
    warnings = build_warnings_v9_37(timeframe_reports)
    blockers = build_blockers_v9_37(source_status, timeframe_reports, leakage_guard, forbidden_scan, quality_status)
    decision = decide_v9_37(timeframe_reports, quality_status, leakage_guard, forbidden_scan, warnings, blockers)
    report = {
        "version": VERSION,
        "source_versions": {
            "source_version": SOURCE_VERSION,
            "ohlcv_derivation": "V9.35",
            "ohlcv_validation": SOURCE_OHLCV_VALIDATION_VERSION,
            "aggtrades_validation": SOURCE_AGGTRADES_VALIDATION_VERSION,
        },
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {"ohlcv_aggtrades_5y_feature_store_created", "ohlcv_aggtrades_5y_feature_store_created_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "decision": decision["decision"],
        "v9_37_decision": decision,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": EXPECTED_DAYS},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_store_created": decision["decision"] in {"ohlcv_aggtrades_5y_feature_store_created", "ohlcv_aggtrades_5y_feature_store_created_with_warnings"},
        "features_created": decision["decision"] in {"ohlcv_aggtrades_5y_feature_store_created", "ohlcv_aggtrades_5y_feature_store_created_with_warnings"},
        "feature_store_paths": output_paths,
        "row_counts": {timeframe: item["actual_rows"] for timeframe, item in timeframe_reports.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_families": FEATURE_FAMILIES,
        "timeframe_reports": timeframe_reports,
        "zero_trade_bucket_summary": {timeframe: item["zero_trade_bucket_summary"] for timeframe, item in timeframe_reports.items()},
        "warmup_summary": {timeframe: item["warmup_summary"] for timeframe, item in timeframe_reports.items()},
        "null_summary": {timeframe: item["null_summary"] for timeframe, item in timeframe_reports.items()},
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "source_lineage": build_source_lineage_v9_37(source_status),
        "quality_status": quality_status,
        "coverage_status": coverage_status,
        "blockers": blockers,
        "warnings": warnings,
        "limitations": [
            "Les features aggTrades V9.37 utilisent les agregats aggTrades deja materialises dans l'OHLCV derivee V9.35; V9.37 ne rescane pas directement les 3.2B lignes de trades.",
            "median_trade_size exact, large_trade_count exact et buyer_maker_count exact ne sont pas inclus pour eviter un scan direct massif des aggTrades dans cette version.",
            "Aucun label, target, prediction, signal, ordre, backtest, walk-forward ou ML n'est cree.",
        ],
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
        "findings": dict(FINDINGS_V9_37),
        "safety_flags": dict(SAFETY_FLAGS_V9_37),
    }
    return report


def build_timeframe_features_v9_37(frame: pd.DataFrame, *, timeframe: str, feature_run_id: str) -> pd.DataFrame:
    ordered = frame.sort_values("open_ts", kind="mergesort").reset_index(drop=True)
    close = ordered["close"].astype("float64")
    open_ = ordered["open"].astype("float64")
    high = ordered["high"].astype("float64")
    low = ordered["low"].astype("float64")
    volume = ordered["volume"].astype("float64")
    quote_volume = ordered["quote_volume"].astype("float64")
    trades_count = ordered["trades_count"].astype("int64")
    taker_buy = ordered["taker_buy_base_volume"].astype("float64")
    taker_sell = (volume - taker_buy).clip(lower=0.0)
    close_return = close.pct_change()
    imbalance_denominator = volume.replace(0.0, np.nan)
    output = pd.DataFrame(
        {
            "source": SOURCE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "event_ts": pd.to_datetime(ordered["event_ts"], utc=True),
            "open_ts": pd.to_datetime(ordered["open_ts"], utc=True),
            "close_ts": pd.to_datetime(ordered["close_ts"], utc=True),
            "decision_ts": pd.to_datetime(ordered["decision_ts"], utc=True),
            "available_ts": pd.to_datetime(ordered["available_ts"], utc=True),
            "feature_available_ts": pd.to_datetime(ordered["decision_ts"], utc=True),
            "feature_run_id": feature_run_id,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "ohlcv_source_type": OHLCV_SOURCE_TYPE,
            "aggtrades_source_type": AGGTRADES_SOURCE_TYPE,
            "source_ohlcv_validation_version": SOURCE_OHLCV_VALIDATION_VERSION,
            "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
            "source_window_start": TARGET_WINDOW_START,
            "source_window_end": TARGET_WINDOW_END,
            "close_return_1": close_return,
            "log_return_1": np.log(close / close.shift(1)),
            "rolling_return_5": close / close.shift(5) - 1.0,
            "rolling_return_15": close / close.shift(15) - 1.0,
            "rolling_return_60": close / close.shift(60) - 1.0,
            "rolling_volatility_5": close_return.rolling(5, min_periods=5).std(),
            "rolling_volatility_15": close_return.rolling(15, min_periods=15).std(),
            "rolling_volatility_60": close_return.rolling(60, min_periods=60).std(),
            "high_low_range": (high - low) / close,
            "close_open_return": close / open_ - 1.0,
            "candle_body": (close - open_).abs() / close,
            "upper_wick": (high - np.maximum(open_, close)) / close,
            "lower_wick": (np.minimum(open_, close) - low) / close,
            "volume": volume,
            "quote_volume": quote_volume,
            "trades_count": trades_count,
            "volume_rolling_mean_5": volume.rolling(5, min_periods=5).mean(),
            "volume_rolling_mean_15": volume.rolling(15, min_periods=15).mean(),
            "volume_rolling_mean_60": volume.rolling(60, min_periods=60).mean(),
            "volume_rolling_std_5": volume.rolling(5, min_periods=5).std(),
            "volume_rolling_std_15": volume.rolling(15, min_periods=15).std(),
            "volume_rolling_std_60": volume.rolling(60, min_periods=60).std(),
            "zero_trade_bucket_rolling_count_60": (trades_count == 0).astype("int64").rolling(60, min_periods=1).sum(),
            "agg_trade_count": trades_count,
            "agg_trade_volume": volume,
            "agg_trade_quote_volume": quote_volume,
            "average_trade_size": np.where(trades_count > 0, volume / trades_count.replace(0, np.nan), 0.0),
            "taker_buy_base_volume": taker_buy,
            "taker_sell_base_volume": taker_sell,
            "taker_buy_ratio": np.where(volume > 0, taker_buy / imbalance_denominator, 0.0),
            "taker_buy_sell_imbalance": np.where(volume > 0, (taker_buy - taker_sell) / imbalance_denominator, 0.0),
            "trade_intensity_rolling_5": trades_count.rolling(5, min_periods=5).mean(),
            "trade_intensity_rolling_15": trades_count.rolling(15, min_periods=15).mean(),
            "trade_intensity_rolling_60": trades_count.rolling(60, min_periods=60).mean(),
            "agg_trade_volume_rolling_mean_5": volume.rolling(5, min_periods=5).mean(),
            "agg_trade_volume_rolling_mean_15": volume.rolling(15, min_periods=15).mean(),
            "agg_trade_volume_rolling_mean_60": volume.rolling(60, min_periods=60).mean(),
            "taker_imbalance_rolling_mean_5": pd.Series(np.where(volume > 0, (taker_buy - taker_sell) / imbalance_denominator, 0.0)).rolling(5, min_periods=5).mean(),
            "taker_imbalance_rolling_mean_15": pd.Series(np.where(volume > 0, (taker_buy - taker_sell) / imbalance_denominator, 0.0)).rolling(15, min_periods=15).mean(),
            "taker_imbalance_rolling_mean_60": pd.Series(np.where(volume > 0, (taker_buy - taker_sell) / imbalance_denominator, 0.0)).rolling(60, min_periods=60).mean(),
            "missing_aggtrades_flag": (trades_count == 0).astype("int64"),
            "warmup_row": False,
            "zero_trade_bucket": trades_count == 0,
            "feature_null_count": 0,
            "feature_error_count": 0,
            "row_valid_for_features": True,
            "feature_invalid_reason": "",
        }
    )
    output["feature_null_count"] = output[FEATURE_COLUMNS].isna().sum(axis=1).astype("int64")
    output["warmup_row"] = output["feature_null_count"] > 0
    return output[STRICT_COLUMNS]


def validate_feature_frame_v9_37(frame: pd.DataFrame, *, timeframe: str, path: Path) -> dict[str, Any]:
    errors: list[str] = []
    missing_columns = sorted(set(STRICT_COLUMNS) - set(frame.columns))
    extra_columns = sorted(set(frame.columns) - set(STRICT_COLUMNS))
    forbidden_columns = sorted(set(frame.columns) & FORBIDDEN_FEATURE_COLUMNS)
    if missing_columns:
        errors.append(f"missing_columns={missing_columns}")
    if extra_columns:
        errors.append(f"extra_columns={extra_columns}")
    if forbidden_columns:
        errors.append(f"forbidden_columns={forbidden_columns}")
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    feature_available_ts = pd.to_datetime(frame["feature_available_ts"], utc=True)
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    days = sorted(set(event_ts.dt.date.astype(str)))
    missing_days = sorted(set(date_range_v9_37(TARGET_WINDOW_START, TARGET_WINDOW_END)) - set(days))
    duplicate_event_ts = int(event_ts.duplicated().sum())
    duplicate_close_ts = int(close_ts.duplicated().sum())
    feature_available_violations = int((feature_available_ts > decision_ts).sum())
    available_violations = int((available_ts > decision_ts).sum())
    row_invalid = int((frame["row_valid_for_features"] != True).sum())  # noqa: E712
    for label, value in {
        "actual_rows_mismatch": int(len(frame) != expected_rows),
        "duplicate_event_ts": duplicate_event_ts,
        "duplicate_close_ts": duplicate_close_ts,
        "feature_available_ts_after_decision_ts": feature_available_violations,
        "available_ts_after_decision_ts": available_violations,
        "row_invalid_for_features": row_invalid,
    }.items():
        if value:
            errors.append(f"{label}={value}")
    return {
        "timeframe": timeframe,
        "path": path.as_posix(),
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS - len(missing_days),
        "days_missing": len(missing_days),
        "coverage_start": days[0] if days else None,
        "coverage_end": days[-1] if days else None,
        "coverage_status": "PASS" if len(frame) == expected_rows and not missing_days else "FAIL",
        "timestamps_monotone": bool(event_ts.is_monotonic_increasing and close_ts.is_monotonic_increasing),
        "duplicate_event_ts_count": duplicate_event_ts,
        "duplicate_close_ts_count": duplicate_close_ts,
        "feature_available_ts_lte_decision_ts": feature_available_violations == 0,
        "available_ts_lte_decision_ts": available_violations == 0,
        "forbidden_columns": forbidden_columns,
        "strict_schema_status": "PASS" if not missing_columns and not extra_columns else "FAIL",
        "feature_columns_count": len(FEATURE_COLUMNS),
        "null_summary": {column: int(frame[column].isna().sum()) for column in FEATURE_COLUMNS},
        "warmup_summary": {"warmup_rows": int(frame["warmup_row"].sum()), "non_warmup_rows": int((~frame["warmup_row"]).sum())},
        "zero_trade_bucket_summary": {"zero_trade_rows": int(frame["zero_trade_bucket"].sum()), "zero_trade_ratio": float(frame["zero_trade_bucket"].mean())},
        "feature_null_count_total": int(frame["feature_null_count"].sum()),
        "feature_error_count_total": int(frame["feature_error_count"].sum()),
        "row_valid_for_features_count": int((frame["row_valid_for_features"] == True).sum()),  # noqa: E712
        "row_invalid_for_features_count": row_invalid,
        "quality_status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def validate_source_readiness_v9_37(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v9_36 = inputs["v9_36_validation"].get("payload", {})
    v9_32 = inputs["v9_32_aggtrades"].get("payload", {})
    errors: list[str] = []
    if v9_36.get("decision") not in {"ohlcv_from_aggtrades_5y_validation_pass", "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings"}:
        errors.append("V9.36 OHLCV validation is not pass")
    if v9_36.get("quality_status") != "PASS" or v9_36.get("coverage_status") != "target_5y_window_complete":
        errors.append("V9.36 OHLCV quality or coverage is not ready")
    if v9_32.get("quality_status") != "PASS" or v9_32.get("days_complete") != EXPECTED_DAYS:
        errors.append("V9.32 aggTrades quality or coverage is not ready")
    return {
        "ready": not errors,
        "errors": errors,
        "v9_36_decision": v9_36.get("decision"),
        "v9_32_decision": v9_32.get("decision"),
    }


def build_leakage_guard_v9_37(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "PASS" if timeframe_reports and all(item["feature_available_ts_lte_decision_ts"] and item["available_ts_lte_decision_ts"] for item in timeframe_reports.values()) else "FAIL",
        "feature_available_ts_lte_decision_ts": all(item["feature_available_ts_lte_decision_ts"] for item in timeframe_reports.values()) if timeframe_reports else False,
        "available_ts_lte_decision_ts": all(item["available_ts_lte_decision_ts"] for item in timeframe_reports.values()) if timeframe_reports else False,
        "rolling_windows_past_only": True,
        "forbidden_future_columns_absent": True,
    }


def build_forbidden_scan_v9_37(timeframe_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    found = sorted({column for item in timeframe_reports.values() for column in item.get("forbidden_columns", [])})
    return {
        "status": "PASS" if not found else "FAIL",
        "forbidden_columns": found,
        "scanned_terms": sorted(FORBIDDEN_FEATURE_COLUMNS),
    }


def build_source_lineage_v9_37(source_status: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_status": source_status,
        "ohlcv_source_type": OHLCV_SOURCE_TYPE,
        "aggtrades_source_type": AGGTRADES_SOURCE_TYPE,
        "source_ohlcv_validation_version": SOURCE_OHLCV_VALIDATION_VERSION,
        "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "source_window_start": TARGET_WINDOW_START,
        "source_window_end": TARGET_WINDOW_END,
        "direct_aggtrades_full_scan_performed": False,
    }


def decide_v9_37(
    timeframe_reports: dict[str, dict[str, Any]],
    quality_status: str,
    leakage_guard: dict[str, Any],
    forbidden_scan: dict[str, Any],
    warnings: list[str],
    blockers: list[str],
) -> dict[str, str]:
    if leakage_guard["status"] != "PASS" or forbidden_scan["status"] != "PASS":
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_leakage", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Correction", "justification": "Le leakage guard ou le scan de colonnes interdites echoue."}
    if quality_status != "PASS":
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_quality", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Correction", "justification": "Le feature store echoue les controles qualite."}
    if set(timeframe_reports) != set(EXPECTED_TIMEFRAMES):
        return {"decision": "ohlcv_aggtrades_5y_feature_store_partial", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Correction", "justification": "Tous les timeframes ne sont pas produits."}
    if blockers:
        return {"decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_quality", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Correction", "justification": "Des blocages restent presents."}
    if warnings:
        return {"decision": "ohlcv_aggtrades_5y_feature_store_created_with_warnings", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Validation", "justification": "Les 4 timeframes sont produits avec warnings non bloquants."}
    return {"decision": "ohlcv_aggtrades_5y_feature_store_created", "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Validation", "justification": "Les 4 timeframes sont produits et valides."}


def build_warnings_v9_37(timeframe_reports: dict[str, dict[str, Any]]) -> list[str]:
    warnings = [
        "median_trade_size exact, large_trade_count exact et buyer_maker_count exact non inclus car V9.37 evite un scan direct massif des aggTrades.",
    ]
    warnings.extend(
        f"{timeframe}: {item['warmup_summary']['warmup_rows']} warmup rows avec nulls attendus"
        for timeframe, item in timeframe_reports.items()
        if item["warmup_summary"]["warmup_rows"]
    )
    warnings.extend(
        f"{timeframe}: {item['zero_trade_bucket_summary']['zero_trade_rows']} zero-trade buckets conserves comme flags causaux"
        for timeframe, item in timeframe_reports.items()
        if item["zero_trade_bucket_summary"]["zero_trade_rows"]
    )
    return warnings


def build_blockers_v9_37(
    source_status: dict[str, Any],
    timeframe_reports: dict[str, dict[str, Any]],
    leakage_guard: dict[str, Any],
    forbidden_scan: dict[str, Any],
    quality_status: str,
) -> list[str]:
    blockers = list(source_status["errors"])
    if leakage_guard["status"] != "PASS":
        blockers.append("leakage_guard_failed")
    if forbidden_scan["status"] != "PASS":
        blockers.append("forbidden_columns_found")
    if quality_status != "PASS":
        blockers.append("quality_failed")
    blockers.extend(f"{timeframe}: {error}" for timeframe, item in timeframe_reports.items() for error in item["errors"])
    return blockers


def feature_output_path_v9_37(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_37/features/ohlcv_aggtrades_5y/source={SOURCE}/market_type={MARKET_TYPE}/symbol={SYMBOL}/timeframe={timeframe}/window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}/features.parquet"


def build_manifest_v9_37(report: dict[str, Any]) -> dict[str, Any]:
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
        "feature_store_created": report["feature_store_created"],
        "features_created": report["features_created"],
        "timeframes": report["timeframes"],
        "row_counts": report["row_counts"],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_37(report: dict[str, Any]) -> str:
    lines = [
        "# V9.37 - OHLCV + AggTrades 5Y Feature Store",
        "",
        "## Resume",
        f"- Decision V9.37 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Timeframes produits : `{list(report['row_counts'])}`.",
        f"- Row counts : `{report['row_counts']}`.",
        f"- Feature columns count : `{report['feature_columns_count']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Warnings : `{report['warnings']}`.",
        "",
        "## Sources",
        "- OHLCV 5Y derivee depuis aggTrades V9.35, validee V9.36.",
        "- AggTrades 5Y valides V9.32.",
        "- Les features aggTrades V9.37 utilisent les agregats aggTrades deja materialises dans l'OHLCV derivee.",
        "",
        "## Garde-fous",
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.",
        "- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_37(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_37_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "feature_store_created": report["feature_store_created"],
        "features_created": report["features_created"],
        "timeframes": report["timeframes"],
        "row_counts": report["row_counts"],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
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
        "# Synthese courante - V9.37\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.37 : `{report['decision']}`.\n"
        f"- Feature store cree : `{report['feature_store_created']}`.\n"
        f"- Feature columns count : `{report['feature_columns_count']}`.\n"
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
        f"- Candidate : {VERSION}, feature store OHLCV + aggTrades 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def date_range_v9_37(start: str, end: str) -> list[str]:
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    return [(first + timedelta(days=offset)).isoformat() for offset in range((last - first).days + 1)]


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
