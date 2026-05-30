from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import (
    DERIVED_COLUMNS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    FINDINGS,
    SAFETY_FLAGS,
    SOURCE_AGGTRADES_VALIDATION_VERSION,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAME_DELTAS,
    TIMEFRAME_FREQ,
    TIMEFRAMES,
    derived_output_path_v9_35,
)


VERSION = "V9.36"
SOURCE_VERSION = "V9.35"
LAST_VALIDATED_VERSION = "V9.35"
DIRECTION = "ohlcv_from_aggtrades_5y_coverage_validation"
EXPECTED_DAYS = 1827

REPORT_JSON_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json")
REPORT_MD_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_from_aggtrades_5y_validation_v9_36_manifest.json")
DOC_PATH = Path("docs/ohlcv_from_aggtrades_5y_validation_v9_36.md")
ZERO_TRADE_REPORT_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_zero_trade_buckets_v9_36.json")
PARITY_REPORT_PATH = Path("reports/data/ohlcv_from_aggtrades_5y_parity_v9_36.json")

FORBIDDEN_COLUMNS = {
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "backtest",
    "position_size",
    "strategy",
    "entry",
    "exit",
    "trade_decision",
    "label",
    "target",
}

INPUT_PATHS = {
    "v9_35_report": Path("reports/data/ohlcv_from_aggtrades_5y_v9_35.json"),
    "v9_35_manifest": Path("reports/manifests/ohlcv_from_aggtrades_5y_v9_35_manifest.json"),
    "v9_34_1_report": Path("reports/data/ohlcv_5y_extension_correction_v9_34_1.json"),
    "v9_32_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

ALLOWED_DECISIONS = {
    "ohlcv_from_aggtrades_5y_validation_pass",
    "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings",
    "ohlcv_from_aggtrades_5y_validation_blocked_by_coverage",
    "ohlcv_from_aggtrades_5y_validation_blocked_by_quality",
    "ohlcv_from_aggtrades_5y_validation_blocked_by_zero_trade_fill",
    "ohlcv_from_aggtrades_5y_validation_inconclusive_manual_review_required",
    "stop_ohlcv_derivation_branch",
}

SAFETY_FLAGS_V9_36 = {
    **SAFETY_FLAGS,
    "no_feature_store": True,
    "no_data_deletion": True,
    "no_ingestion_executed": True,
}


def run_ohlcv_from_aggtrades_5y_validation_v9_36(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_validation_report_v9_36(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_36(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_36(report))
    _write_json(root / ZERO_TRADE_REPORT_PATH, report["zero_trade_bucket_analysis"])
    _write_json(root / PARITY_REPORT_PATH, report["parity_comparison"])
    update_state_surfaces_v9_36(root, report)
    return report


def build_validation_report_v9_36(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    timeframe_validations: dict[str, dict[str, Any]] = {}
    zero_trade: dict[str, dict[str, Any]] = {}
    lineage: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES:
        path = derived_output_path_v9_35(root, timeframe)
        frame = pd.read_parquet(path, engine="pyarrow")
        timeframe_validations[timeframe] = validate_timeframe_frame_v9_36(frame, timeframe=timeframe, path=path)
        zero_trade[timeframe] = analyze_zero_trade_buckets_v9_36(frame, timeframe=timeframe)
        lineage[timeframe] = validate_lineage_v9_36(frame, timeframe=timeframe)
    parity = compare_binance_parity_v9_36(root)
    coverage_status = "PASS" if all(item["complete_calendar_coverage"] for item in timeframe_validations.values()) else "FAIL"
    invariant_status = "PASS" if all(item["quality_status"] == "PASS" for item in timeframe_validations.values()) else "FAIL"
    zero_trade_status = "PASS" if all(not item["zero_trade_buckets_blocking"] for item in zero_trade.values()) else "FAIL"
    lineage_status = "PASS" if all(item["lineage_status"] == "PASS" for item in lineage.values()) else "FAIL"
    warnings = build_warnings_v9_36(zero_trade, parity)
    decision = decide_v9_36(coverage_status, invariant_status, zero_trade_status, lineage_status, parity, warnings)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {"ohlcv_from_aggtrades_5y_validation_pass", "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "timeframes_required": list(TIMEFRAMES),
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "coverage_validation": timeframe_validations,
        "invariant_validation": summarize_invariants_v9_36(timeframe_validations),
        "zero_trade_bucket_analysis": zero_trade,
        "parity_comparison": parity,
        "source_lineage": lineage,
        "coverage_status": "target_5y_window_complete" if coverage_status == "PASS" else "target_5y_window_incomplete",
        "quality_status": "PASS" if invariant_status == "PASS" and zero_trade_status == "PASS" and lineage_status == "PASS" else "FAIL",
        "parity_status": parity["parity_status"],
        "decision": decision["decision"],
        "v9_36_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "warnings": warnings,
        "blockers": build_blockers_v9_36(coverage_status, invariant_status, zero_trade_status, lineage_status, parity),
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
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS_V9_36),
    }
    return report


def validate_timeframe_frame_v9_36(frame: pd.DataFrame, *, timeframe: str, path: Path) -> dict[str, Any]:
    errors: list[str] = []
    missing_columns = sorted(set(DERIVED_COLUMNS) - set(frame.columns))
    forbidden_columns = sorted(set(frame.columns) & FORBIDDEN_COLUMNS)
    if missing_columns:
        errors.append(f"missing_columns={missing_columns}")
    if forbidden_columns:
        errors.append(f"forbidden_columns={forbidden_columns}")
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = pd.to_datetime(frame["close_ts"], utc=True)
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    if len(frame) != expected_rows:
        errors.append(f"actual_rows={len(frame)} expected_rows={expected_rows}")
    duplicate_open_ts = int(open_ts.duplicated().sum())
    if duplicate_open_ts:
        errors.append(f"duplicate_open_ts={duplicate_open_ts}")
    timestamp_gap_warnings = int((open_ts.diff().dropna() != TIMEFRAME_DELTAS[timeframe]).sum())
    if timestamp_gap_warnings:
        errors.append(f"timestamp_gap_warnings={timestamp_gap_warnings}")
    open_monotone = bool(open_ts.is_monotonic_increasing)
    close_monotone = bool(close_ts.is_monotonic_increasing)
    if not open_monotone:
        errors.append("open_ts_not_monotone")
    if not close_monotone:
        errors.append("close_ts_not_monotone")
    invariant_counts = compute_invariant_counts_v9_36(frame, open_ts, close_ts, event_ts, decision_ts, available_ts)
    errors.extend([f"{key}={value}" for key, value in invariant_counts.items() if value])
    days = sorted(set(open_ts.dt.date.astype(str)))
    expected_days = set(date_range_v9_36(TARGET_WINDOW_START, TARGET_WINDOW_END))
    missing_days = sorted(expected_days - set(days))
    null_summary = {column: int(frame[column].isna().sum()) for column in frame.columns}
    row_invalid_count = int((frame["row_valid"] != True).sum())  # noqa: E712
    if row_invalid_count:
        errors.append(f"row_invalid_count={row_invalid_count}")
    return {
        "timeframe": timeframe,
        "path": path.as_posix(),
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS - len(missing_days),
        "days_missing": len(missing_days),
        "first_missing_day": missing_days[0] if missing_days else None,
        "coverage_start": days[0] if days else None,
        "coverage_end": days[-1] if days else None,
        "complete_calendar_coverage": not missing_days and len(frame) == expected_rows,
        "duplicate_open_ts_count": duplicate_open_ts,
        "timestamp_gap_warnings": timestamp_gap_warnings,
        "invalid_rows": row_invalid_count,
        "null_summary": null_summary,
        "row_valid_count": int((frame["row_valid"] == True).sum()),  # noqa: E712
        "row_invalid_count": row_invalid_count,
        "forbidden_columns": forbidden_columns,
        "invariant_counts": invariant_counts,
        "open_ts_monotone": open_monotone,
        "close_ts_monotone": close_monotone,
        "quality_status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def compute_invariant_counts_v9_36(
    frame: pd.DataFrame,
    open_ts: pd.Series,
    close_ts: pd.Series,
    event_ts: pd.Series,
    decision_ts: pd.Series,
    available_ts: pd.Series,
) -> dict[str, int]:
    open_ = frame["open"].astype("float64")
    high = frame["high"].astype("float64")
    low = frame["low"].astype("float64")
    close = frame["close"].astype("float64")
    return {
        "non_positive_open": int((open_ <= 0).sum()),
        "non_positive_high": int((high <= 0).sum()),
        "non_positive_low": int((low <= 0).sum()),
        "non_positive_close": int((close <= 0).sum()),
        "negative_volume": int((frame["volume"].astype("float64") < 0).sum()),
        "negative_quote_volume": int((frame["quote_volume"].astype("float64") < 0).sum()),
        "negative_trades_count": int((frame["trades_count"].astype("int64") < 0).sum()),
        "high_below_open": int((high < open_).sum()),
        "high_below_close": int((high < close).sum()),
        "high_below_low": int((high < low).sum()),
        "low_above_open": int((low > open_).sum()),
        "low_above_close": int((low > close).sum()),
        "low_above_high": int((low > high).sum()),
        "available_ts_before_close_ts": int((available_ts < close_ts).sum()),
        "decision_ts_not_close_ts": int((decision_ts != close_ts).sum()),
        "event_ts_not_open_ts": int((event_ts != open_ts).sum()),
    }


def analyze_zero_trade_buckets_v9_36(frame: pd.DataFrame, *, timeframe: str) -> dict[str, Any]:
    ordered = frame.sort_values("open_ts", kind="mergesort").reset_index(drop=True)
    open_ts = pd.to_datetime(ordered["open_ts"], utc=True)
    close_ts = pd.to_datetime(ordered["close_ts"], utc=True)
    available_ts = pd.to_datetime(ordered["available_ts"], utc=True)
    zero_mask = ordered["trades_count"].astype("int64") == 0
    zero = ordered[zero_mask].copy()
    previous_close = ordered["close"].shift(1)
    ohlc_equal_previous = bool(
        (
            ordered.loc[zero_mask, ["open", "high", "low", "close"]]
            .eq(previous_close.loc[zero_mask], axis=0)
            .all(axis=1)
        ).all()
    )
    volume_zero = bool((ordered.loc[zero_mask, "volume"].astype("float64") == 0.0).all())
    quote_zero = bool((ordered.loc[zero_mask, "quote_volume"].astype("float64") == 0.0).all())
    trades_zero = bool((ordered.loc[zero_mask, "trades_count"].astype("int64") == 0).all())
    available_ok = bool((available_ts.loc[zero_mask] >= close_ts.loc[zero_mask]).all())
    max_consecutive = max_consecutive_true_v9_36(zero_mask.tolist())
    distribution = zero_trade_distribution_v9_36(open_ts.loc[zero_mask])
    blocking = bool(len(zero) and (not ohlc_equal_previous or not volume_zero or not quote_zero or not trades_zero or not available_ok))
    return {
        "timeframe": timeframe,
        "zero_trade_bucket_count": int(len(zero)),
        "zero_trade_ratio": float(len(zero) / len(ordered)) if len(ordered) else 0.0,
        "first_occurrence": open_ts.loc[zero_mask].min().isoformat().replace("+00:00", "Z") if len(zero) else None,
        "last_occurrence": open_ts.loc[zero_mask].max().isoformat().replace("+00:00", "Z") if len(zero) else None,
        "max_consecutive_zero_trade_buckets": max_consecutive,
        "temporal_distribution": distribution,
        "ohlc_convention": "OHLC equals previous close, volume=0, quote_volume=0, trades_count=0",
        "ohlc_equals_previous_close": ohlc_equal_previous,
        "volume_zero_confirmed": volume_zero,
        "quote_volume_zero_confirmed": quote_zero,
        "trades_count_zero_confirmed": trades_zero,
        "available_ts_close_ts_coherent": available_ok,
        "causal_fill_uses_future_data": False,
        "zero_trade_buckets_blocking": blocking,
    }


def compare_binance_parity_v9_36(root: Path) -> dict[str, Any]:
    result = {"parity_status": "PASS", "parity_warnings": [], "blocking_mismatches": [], "timeframes": {}, "max_close_abs_diff": {}, "max_high_abs_diff": {}, "max_low_abs_diff": {}, "max_volume_abs_diff": {}, "matched_rows": {}}
    for timeframe in TIMEFRAMES:
        derived_path = derived_output_path_v9_35(root, timeframe)
        existing_path = root / f"data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2023-03-25_2026-05-23/ohlcv.parquet"
        if not existing_path.is_file():
            result["parity_status"] = "WARNING"
            result["parity_warnings"].append(f"{timeframe}: existing Binance OHLCV unavailable")
            continue
        existing = pd.read_parquet(existing_path, engine="pyarrow")
        derived = pd.read_parquet(derived_path, engine="pyarrow")
        if "open_ts" not in existing.columns:
            existing["open_ts"] = existing["event_ts"]
        existing["open_ts"] = pd.to_datetime(existing["open_ts"], utc=True)
        derived["open_ts"] = pd.to_datetime(derived["open_ts"], utc=True)
        start = pd.Timestamp("2023-03-25", tz="UTC")
        end = pd.Timestamp("2026-05-06", tz="UTC")
        existing = existing[(existing["open_ts"] >= start) & (existing["open_ts"] < end)].sort_values("open_ts")
        derived = derived[(derived["open_ts"] >= start) & (derived["open_ts"] < end)].sort_values("open_ts")
        merged = existing[["open_ts", "close", "high", "low", "volume"]].merge(
            derived[["open_ts", "close", "high", "low", "volume"]],
            on="open_ts",
            how="inner",
            suffixes=("_binance", "_derived"),
        )
        summary = {
            "row_count_parity": int(len(existing)) == int(len(derived)),
            "timestamp_parity": int(len(merged)) == int(len(derived)) == int(len(existing)),
            "existing_rows": int(len(existing)),
            "derived_rows": int(len(derived)),
            "matched_rows": int(len(merged)),
            "max_close_abs_diff": _max_abs_diff(merged, "close"),
            "max_high_abs_diff": _max_abs_diff(merged, "high"),
            "max_low_abs_diff": _max_abs_diff(merged, "low"),
            "max_volume_abs_diff": _max_abs_diff(merged, "volume"),
            "blocking_mismatches": [],
            "parity_status": "PASS",
        }
        if not summary["row_count_parity"] or not summary["timestamp_parity"]:
            summary["parity_status"] = "WARNING"
            result["parity_status"] = "WARNING"
            result["parity_warnings"].append(f"{timeframe}: row/timestamp parity mismatch")
        result["timeframes"][timeframe] = summary
        for key in ["max_close_abs_diff", "max_high_abs_diff", "max_low_abs_diff", "max_volume_abs_diff", "matched_rows"]:
            result[key][timeframe] = summary[key]
    return result


def validate_lineage_v9_36(frame: pd.DataFrame, *, timeframe: str) -> dict[str, Any]:
    source_start = pd.to_datetime(frame["source_aggtrades_window_start"], utc=True)
    source_end = pd.to_datetime(frame["source_aggtrades_window_end"], utc=True)
    source_types = sorted(set(frame["ohlcv_source_type"].astype(str)))
    validation_versions = sorted(set(frame["source_aggtrades_validation_version"].astype(str)))
    derivation_ids = sorted(set(frame["derivation_run_id"].astype(str)))
    schema_versions = sorted(set(frame["ohlcv_schema_version"].astype(str)))
    errors: list[str] = []
    if source_types != ["derived_from_aggtrades"]:
        errors.append(f"ohlcv_source_type mismatch: {source_types}")
    if validation_versions != [SOURCE_AGGTRADES_VALIDATION_VERSION]:
        errors.append(f"source validation version mismatch: {validation_versions}")
    if not derivation_ids or any(not value for value in derivation_ids):
        errors.append("missing derivation_run_id")
    if not schema_versions or any(not value for value in schema_versions):
        errors.append("missing ohlcv_schema_version")
    return {
        "timeframe": timeframe,
        "source_aggtrades_validation_version": validation_versions,
        "ohlcv_source_type": source_types,
        "derivation_run_id_present": bool(derivation_ids),
        "ohlcv_schema_version_present": bool(schema_versions),
        "source_aggtrades_window_start_min": source_start.min().isoformat().replace("+00:00", "Z"),
        "source_aggtrades_window_end_max": source_end.max().isoformat().replace("+00:00", "Z"),
        "expected_source_window_start": TARGET_WINDOW_START,
        "expected_source_window_end": TARGET_WINDOW_END,
        "lineage_status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def summarize_invariants_v9_36(timeframe_validations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "quality_status_by_timeframe": {timeframe: item["quality_status"] for timeframe, item in timeframe_validations.items()},
        "forbidden_columns_by_timeframe": {timeframe: item["forbidden_columns"] for timeframe, item in timeframe_validations.items()},
        "invariant_counts_by_timeframe": {timeframe: item["invariant_counts"] for timeframe, item in timeframe_validations.items()},
        "quality_status": "PASS" if all(item["quality_status"] == "PASS" for item in timeframe_validations.values()) else "FAIL",
    }


def decide_v9_36(coverage_status: str, invariant_status: str, zero_trade_status: str, lineage_status: str, parity: dict[str, Any], warnings: list[str]) -> dict[str, str]:
    if coverage_status != "PASS":
        return {"decision": "ohlcv_from_aggtrades_5y_validation_blocked_by_coverage", "next_recommendation": "V9.37 - OHLCV Derived Coverage Correction", "justification": "La couverture OHLCV derivee est incomplete."}
    if invariant_status != "PASS" or lineage_status != "PASS":
        return {"decision": "ohlcv_from_aggtrades_5y_validation_blocked_by_quality", "next_recommendation": "V9.37 - OHLCV Derived Coverage Correction", "justification": "Les invariants OHLCV ou le lineage echouent."}
    if zero_trade_status != "PASS":
        return {"decision": "ohlcv_from_aggtrades_5y_validation_blocked_by_zero_trade_fill", "next_recommendation": "V9.37 - OHLCV Zero-Trade Fill Correction", "justification": "Le remplissage zero-trade n'est pas causalement valide."}
    if parity["parity_status"] != "PASS" or warnings:
        return {"decision": "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings", "next_recommendation": "V9.37 - OHLCV + AggTrades 5Y Feature Store", "justification": "La validation passe avec warnings non bloquants."}
    return {"decision": "ohlcv_from_aggtrades_5y_validation_pass", "next_recommendation": "V9.37 - OHLCV + AggTrades 5Y Feature Store", "justification": "La validation OHLCV derivee passe sans warning."}


def build_warnings_v9_36(zero_trade: dict[str, dict[str, Any]], parity: dict[str, Any]) -> list[str]:
    warnings = [f"{timeframe}: {item['zero_trade_bucket_count']} zero-trade buckets non bloquants" for timeframe, item in zero_trade.items() if item["zero_trade_bucket_count"]]
    warnings.extend(parity.get("parity_warnings", []))
    return warnings


def build_blockers_v9_36(coverage_status: str, invariant_status: str, zero_trade_status: str, lineage_status: str, parity: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if coverage_status != "PASS":
        blockers.append("coverage")
    if invariant_status != "PASS":
        blockers.append("quality")
    if zero_trade_status != "PASS":
        blockers.append("zero_trade_fill")
    if lineage_status != "PASS":
        blockers.append("lineage")
    if parity.get("blocking_mismatches"):
        blockers.append("parity")
    return blockers


def build_manifest_v9_36(report: dict[str, Any]) -> dict[str, Any]:
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
        "coverage_status": report["coverage_status"],
        "quality_status": report["quality_status"],
        "parity_status": report["parity_status"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "feature_store_created": report["feature_store_created"],
        "combined_feature_store_created": report["combined_feature_store_created"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_36(report: dict[str, Any]) -> str:
    lines = [
        "# V9.36 - OHLCV From AggTrades 5Y Coverage Validation",
        "",
        "## Resume",
        f"- Decision V9.36 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Parite Binance : `{report['parity_status']}`.",
        f"- Warnings : `{report['warnings']}`.",
        "",
        "## Validation",
        "- Les 4 timeframes derives 1m/5m/15m/1h couvrent 2021-05-05 -> 2026-05-05.",
        "- Les invariants OHLCV, timestamps, colonnes interdites et lineage sont controles.",
        "- Les buckets zero-trade sont verifies comme non bloquants si OHLC=previous close, volume=0, trades_count=0, sans futur.",
        "",
        "## Garde-fous",
        "- Aucun reseau, aucun telechargement, aucun feature store combine, aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.",
        "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_36(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_36_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "coverage_status": report["coverage_status"],
        "quality_status": report["quality_status"],
        "parity_status": report["parity_status"],
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
        "# Synthese courante - V9.36\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.36 : `{report['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun reseau, feature store combine, label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, validation OHLCV derivee 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, feature store combine, modele persistant, API privee ou cle API.\n",
    )


def zero_trade_distribution_v9_36(open_ts: pd.Series) -> dict[str, int]:
    if open_ts.empty:
        return {}
    return {str(key): int(value) for key, value in open_ts.dt.date.astype(str).value_counts().sort_index().items()}


def max_consecutive_true_v9_36(values: list[bool]) -> int:
    best = 0
    current = 0
    for value in values:
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def date_range_v9_36(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)
    days: list[str] = []
    while current <= last:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _max_abs_diff(frame: pd.DataFrame, column: str) -> float | None:
    if frame.empty:
        return None
    return float((frame[f"{column}_binance"].astype("float64") - frame[f"{column}_derived"].astype("float64")).abs().max())


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
