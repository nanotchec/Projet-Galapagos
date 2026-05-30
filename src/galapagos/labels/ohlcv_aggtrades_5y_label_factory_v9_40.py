from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_schemas import (
    ALLOWED_DECISIONS,
    DATACARD_MD_PATH,
    DIRECTION,
    DISTRIBUTION_JSON_PATH,
    DOC_PATH,
    EXPECTED_FEATURE_ROWS,
    FEATURE_BASE_PATH,
    FINDINGS,
    INPUT_PATHS,
    LABEL_BASE_PATH,
    LABEL_DESIGNS,
    LABEL_RUN_ID_PREFIX,
    LABEL_SCHEMA_VERSION,
    LAST_VALIDATED_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    REQUIRED_LABEL_COLUMNS,
    SAFETY_FLAGS,
    SELECTED_PRIMARY_LABEL,
    SOURCE_FEATURE_STORE_VERSION,
    SOURCE_FEATURE_VALIDATION_VERSION,
    SOURCE_OHLCV_VERSION,
    SOURCE_VERSION,
    STABILITY_JSON_PATH,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAME_MINUTES,
    TIMEFRAMES,
    TOTAL_DAYS,
    VERSION,
)


def run_ohlcv_aggtrades_5y_label_factory_v9_40(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_label_factory_report_v9_40(root)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_json(root / DISTRIBUTION_JSON_PATH, report["label_distribution"])
    _write_json(root / STABILITY_JSON_PATH, report["label_stability"])
    markdown = build_markdown_v9_40(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DATACARD_MD_PATH, build_datacard_v9_40(report))
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_40(report))
    update_state_surfaces_v9_40(root, report)
    return report


def build_label_factory_report_v9_40(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    source_readiness = assess_source_readiness_v9_40(inputs)
    label_run_id = f"{LABEL_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    outputs: dict[str, Any] = {}
    timeframe_metrics: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    if source_readiness["ready"]:
        for timeframe in TIMEFRAMES:
            try:
                output = create_timeframe_labels_v9_40(root, timeframe, label_run_id)
                outputs[timeframe] = output["output"]
                timeframe_metrics[timeframe] = output["metrics"]
                warnings.extend(output["metrics"]["warnings"])
            except Exception as exc:  # pragma: no cover - exercised by integration failure paths.
                errors.append(f"{timeframe}: {exc}")
                outputs[timeframe] = {"created": False, "error": str(exc)}
    else:
        errors.extend(source_readiness["errors"])

    leakage_guard = build_leakage_guard_v9_40(timeframe_metrics)
    forbidden_column_scan = build_forbidden_column_scan_v9_40(timeframe_metrics)
    label_selection = select_primary_label_v9_40(timeframe_metrics, leakage_guard, errors)
    labels_created = bool(timeframe_metrics) and not errors and all(item.get("created") is True for item in outputs.values())
    quality_status = quality_status_v9_40(labels_created, leakage_guard, label_selection, warnings, errors)
    decision = decide_v9_40(labels_created, leakage_guard, quality_status, warnings, errors)
    row_counts = {timeframe: timeframe_metrics.get(timeframe, {}).get("row_count", 0) for timeframe in TIMEFRAMES}
    valid_label_counts = {
        timeframe: timeframe_metrics.get(timeframe, {}).get("valid_label_counts", {})
        for timeframe in TIMEFRAMES
    }
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"ohlcv_aggtrades_5y_labels_created", "ohlcv_aggtrades_5y_labels_created_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": TOTAL_DAYS},
        "timeframes": list(TIMEFRAMES),
        "source_feature_store": {
            "source_feature_store_version": SOURCE_FEATURE_STORE_VERSION,
            "source_feature_validation_version": SOURCE_FEATURE_VALIDATION_VERSION,
            "source_ohlcv_version": SOURCE_OHLCV_VERSION,
            "readiness": source_readiness,
        },
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "label_run_id": label_run_id,
        "label_designs": LABEL_DESIGNS,
        "labels_created": labels_created,
        "dataset_created": False,
        "outputs": outputs,
        "row_counts": row_counts,
        "valid_label_counts": valid_label_counts,
        "timeframe_metrics": timeframe_metrics,
        "label_distribution": {
            timeframe: timeframe_metrics.get(timeframe, {}).get("label_distribution", {})
            for timeframe in TIMEFRAMES
        },
        "label_stability": {
            timeframe: timeframe_metrics.get(timeframe, {}).get("stability", {})
            for timeframe in TIMEFRAMES
        },
        "selected_primary_label": label_selection["selected_primary_label"],
        "label_selection": label_selection,
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_column_scan,
        "quality_status": quality_status,
        "coverage_status": coverage_status_v9_40(labels_created, row_counts),
        "decision": decision,
        "next_recommendation": next_recommendation_v9_40(decision),
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "limitations": [
            "V9.40 cree des labels candidats auditables, pas un dataset supervise.",
            "La selection primaire repose sur causalite, couverture et distribution descriptive; elle ne valide aucune performance de trading.",
            "Aucun ML, walk-forward, backtest, strategie, signal ou ordre n'est execute.",
        ],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.40 decision: {report['decision']}")
    return report


def assess_source_readiness_v9_40(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    v9_39 = inputs["v9_39_dataset_readiness"].get("payload", {})
    v9_38 = inputs["v9_38_feature_validation"].get("payload", {})
    if not inputs["v9_39_dataset_readiness"].get("available"):
        errors.append("missing V9.39 dataset readiness report")
    if v9_39.get("decision") != "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels":
        errors.append("V9.39 decision is not the expected missing-label blocker")
    if not inputs["v9_38_feature_validation"].get("available"):
        errors.append("missing V9.38 feature validation report")
    if v9_38.get("quality_status") != "PASS" or v9_38.get("leakage_guard_status") != "PASS":
        errors.append("V9.38 feature store quality/leakage guard is not PASS")
    if v9_38.get("actual_rows", {}) != EXPECTED_FEATURE_ROWS:
        errors.append(f"V9.38 feature row counts mismatch: {v9_38.get('actual_rows')}")
    return {
        "ready": not errors,
        "errors": errors,
        "v9_39_decision": v9_39.get("decision"),
        "v9_38_quality_status": v9_38.get("quality_status"),
        "v9_38_leakage_guard_status": v9_38.get("leakage_guard_status"),
        "expected_feature_rows": EXPECTED_FEATURE_ROWS,
    }


def create_timeframe_labels_v9_40(root: Path, timeframe: str, label_run_id: str) -> dict[str, Any]:
    feature_path = root / FEATURE_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "features.parquet"
    if not feature_path.is_file():
        raise FileNotFoundError(f"missing feature parquet for {timeframe}: {feature_path}")
    frame = pd.read_parquet(
        feature_path,
        columns=[
            "source",
            "venue",
            "market_type",
            "symbol",
            "timeframe",
            "event_ts",
            "close_ts",
            "decision_ts",
            "log_return_1",
            "rolling_volatility_60",
            "warmup_row",
            "row_valid_for_features",
            "feature_error_count",
        ],
    )
    labels = create_label_frame_v9_40(frame, timeframe, label_run_id)
    output_path = root / label_output_path_v9_40(timeframe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    metrics = summarize_labels_v9_40(labels, timeframe, output_path)
    return {
        "output": {
            "created": True,
            "path": label_output_path_v9_40(timeframe).as_posix(),
            "bytes": output_path.stat().st_size,
            "rows": int(len(labels)),
        },
        "metrics": metrics,
    }


def create_label_frame_v9_40(frame: pd.DataFrame, timeframe: str, label_run_id: str) -> pd.DataFrame:
    minutes = TIMEFRAME_MINUTES[timeframe]
    h4_bars = LABEL_DESIGNS["up_down_flat_volnorm_h4_5y"]["horizon_minutes"] // minutes
    h1_bars = LABEL_DESIGNS["up_down_flat_volnorm_h1_5y"]["horizon_minutes"] // minutes
    returns = pd.to_numeric(frame["log_return_1"], errors="coerce").to_numpy(dtype="float64")
    h4_future = future_log_return_v9_40(returns, h4_bars)
    h1_future = future_log_return_v9_40(returns, h1_bars)
    causal_vol = pd.to_numeric(frame["rolling_volatility_60"], errors="coerce").to_numpy(dtype="float64")
    h4_threshold = causal_vol * math.sqrt(h4_bars) * LABEL_DESIGNS["up_down_flat_volnorm_h4_5y"]["threshold_multiplier"]
    h1_threshold = causal_vol * math.sqrt(h1_bars) * LABEL_DESIGNS["up_down_flat_volnorm_h1_5y"]["threshold_multiplier"]
    valid_features = frame["row_valid_for_features"].fillna(False).astype(bool).to_numpy()
    warmup = frame["warmup_row"].fillna(False).astype(bool).to_numpy()
    vol_valid = np.isfinite(causal_vol) & (causal_vol > 0)
    h4_valid = valid_features & ~warmup & vol_valid & np.isfinite(h4_future)
    h1_valid = valid_features & ~warmup & vol_valid & np.isfinite(h1_future)
    h4_label = ternary_volnorm_label_v9_40(h4_future, h4_threshold, h4_valid)
    h1_label = ternary_volnorm_label_v9_40(h1_future, h1_threshold, h1_valid)
    binary_h4 = binary_directional_label_v9_40(h4_future, h4_valid)
    label_end_ts = frame["close_ts"].shift(-h4_bars)
    label_available_ts = label_end_ts + pd.Timedelta(milliseconds=1)
    invalid_reason = invalid_reasons_v9_40(valid_features, warmup, vol_valid, np.isfinite(h4_future))
    null_count = (
        pd.Series(h4_label).isna().astype("int16")
        + pd.Series(h1_label).isna().astype("int16")
        + pd.Series(binary_h4).isna().astype("int16")
    )
    label_error_count = np.where(h4_valid, 0, 1).astype("int16")
    out = pd.DataFrame(
        {
            "source": frame["source"],
            "venue": frame["venue"],
            "market_type": frame["market_type"],
            "symbol": frame["symbol"],
            "timeframe": frame["timeframe"],
            "event_ts": frame["event_ts"],
            "close_ts": frame["close_ts"],
            "decision_ts": frame["decision_ts"],
            "label_start_ts": frame["decision_ts"],
            "label_end_ts": label_end_ts,
            "label_available_ts": label_available_ts,
            "label_run_id": label_run_id,
            "label_schema_version": LABEL_SCHEMA_VERSION,
            "source_feature_store_version": SOURCE_FEATURE_STORE_VERSION,
            "source_ohlcv_version": SOURCE_OHLCV_VERSION,
            "target_name": "ohlcv_aggtrades_5y_label_candidates_v9_40",
            "horizon_name": "h4",
            "horizon_minutes": 240,
            "future_log_return": h4_future,
            "causal_vol_window_bars": 60,
            "causal_vol_min_periods": 30,
            "causal_realized_vol": causal_vol,
            "volatility_threshold_multiplier": LABEL_DESIGNS["up_down_flat_volnorm_h4_5y"]["threshold_multiplier"],
            "volatility_normalized_threshold": h4_threshold,
            "up_down_flat_volnorm_h4_5y": h4_label,
            "up_down_flat_volnorm_h1_5y": h1_label,
            "binary_directional_volnorm_h4_5y": binary_h4,
            "label_valid": h4_valid,
            "label_invalid_reason": invalid_reason,
            "warmup_row": warmup,
            "label_null_count": null_count.astype("int16"),
            "label_error_count": label_error_count,
        }
    )
    return out[REQUIRED_LABEL_COLUMNS]


def future_log_return_v9_40(returns: np.ndarray, horizon_bars: int) -> np.ndarray:
    values = np.asarray(returns, dtype="float64")
    n = len(values)
    result = np.full(n, np.nan, dtype="float64")
    valid = np.isfinite(values)
    sums = np.concatenate(([0.0], np.where(valid, values, 0.0).cumsum()))
    counts = np.concatenate(([0], valid.astype("int64").cumsum()))
    if horizon_bars <= 0 or horizon_bars >= n:
        return result
    starts = np.arange(0, n - horizon_bars)
    ends = starts + horizon_bars
    totals = sums[ends + 1] - sums[starts + 1]
    valid_counts = counts[ends + 1] - counts[starts + 1]
    result[starts] = np.where(valid_counts == horizon_bars, totals, np.nan)
    return result


def ternary_volnorm_label_v9_40(future_return: np.ndarray, threshold: np.ndarray, valid: np.ndarray) -> pd.Series:
    labels = np.full(len(future_return), np.nan)
    labels[valid & (future_return > threshold)] = 1
    labels[valid & (future_return < -threshold)] = -1
    labels[valid & (future_return <= threshold) & (future_return >= -threshold)] = 0
    return pd.Series(labels, dtype="Int8")


def binary_directional_label_v9_40(future_return: np.ndarray, valid: np.ndarray) -> pd.Series:
    labels = np.full(len(future_return), np.nan)
    labels[valid & (future_return >= 0)] = 1
    labels[valid & (future_return < 0)] = -1
    return pd.Series(labels, dtype="Int8")


def invalid_reasons_v9_40(valid_features: np.ndarray, warmup: np.ndarray, vol_valid: np.ndarray, future_valid: np.ndarray) -> np.ndarray:
    reasons = np.full(len(valid_features), "", dtype=object)
    reasons[~valid_features] = "feature_row_invalid"
    reasons[valid_features & warmup] = "warmup_row"
    reasons[valid_features & ~warmup & ~vol_valid] = "causal_vol_unavailable"
    reasons[valid_features & ~warmup & vol_valid & ~future_valid] = "future_horizon_unavailable"
    return reasons


def summarize_labels_v9_40(labels: pd.DataFrame, timeframe: str, output_path: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "timeframe": timeframe,
        "row_count": int(len(labels)),
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size,
        "label_columns": [name for name in LABEL_DESIGNS],
        "valid_label_counts": {},
        "invalid_label_counts": {},
        "warmup_rows": int(labels["warmup_row"].sum()),
        "tail_unavailable_rows": int((labels["label_invalid_reason"] == "future_horizon_unavailable").sum()),
        "label_distribution": {},
        "distribution_by_year": {},
        "distribution_by_month": {},
        "split_preview_distribution": {},
        "stability": {},
        "warnings": [],
        "leakage_violations": int(((labels["label_available_ts"] <= labels["decision_ts"]) & labels["label_valid"]).sum()),
        "invalid_rows": int((~labels["label_valid"]).sum()),
    }
    for label_name in LABEL_DESIGNS:
        valid = labels[label_name].dropna()
        counts = {str(int(key)): int(value) for key, value in valid.value_counts(dropna=False).sort_index().items()}
        metrics["valid_label_counts"][label_name] = int(valid.shape[0])
        metrics["invalid_label_counts"][label_name] = int(labels[label_name].isna().sum())
        metrics["label_distribution"][label_name] = distribution_stats_v9_40(counts)
        metrics["distribution_by_year"][label_name] = grouped_distribution_v9_40(labels, label_name, "Y")
        metrics["distribution_by_month"][label_name] = grouped_distribution_v9_40(labels, label_name, "M")
        metrics["split_preview_distribution"][label_name] = split_preview_distribution_v9_40(labels, label_name)
        metrics["stability"][label_name] = stability_stats_v9_40(labels, label_name)
        metrics["warnings"].extend(label_warnings_v9_40(timeframe, label_name, metrics["label_distribution"][label_name], metrics["stability"][label_name]))
    return metrics


def distribution_stats_v9_40(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    ratios = {key: (value / total if total else 0.0) for key, value in counts.items()}
    entropy = -sum(ratio * math.log(ratio, 2) for ratio in ratios.values() if ratio > 0)
    return {
        "counts": counts,
        "ratios": {key: round(value, 6) for key, value in ratios.items()},
        "entropy": round(entropy, 6),
        "majority_class_ratio": round(max(ratios.values()) if ratios else 0.0, 6),
        "flat_ratio": round(ratios.get("0", 0.0), 6),
    }


def grouped_distribution_v9_40(labels: pd.DataFrame, label_name: str, freq: str) -> dict[str, Any]:
    valid = labels.loc[labels[label_name].notna(), ["decision_ts", label_name]].copy()
    if valid.empty:
        return {}
    group = valid["decision_ts"].dt.strftime("%Y" if freq == "Y" else "%Y-%m")
    result: dict[str, Any] = {}
    for key, chunk in valid.groupby(group, sort=True):
        counts = {str(int(label)): int(count) for label, count in chunk[label_name].value_counts().sort_index().items()}
        result[str(key)] = distribution_stats_v9_40(counts)
    return result


def split_preview_distribution_v9_40(labels: pd.DataFrame, label_name: str) -> dict[str, Any]:
    valid = labels.loc[labels[label_name].notna(), label_name]
    n = len(valid)
    if n == 0:
        return {}
    boundaries = {"train_preview": (0, int(n * 0.60)), "validation_preview": (int(n * 0.60), int(n * 0.80)), "test_preview": (int(n * 0.80), n)}
    result: dict[str, Any] = {}
    for name, (start, end) in boundaries.items():
        chunk = valid.iloc[start:end]
        counts = {str(int(label)): int(count) for label, count in chunk.value_counts().sort_index().items()}
        result[name] = distribution_stats_v9_40(counts)
    return result


def stability_stats_v9_40(labels: pd.DataFrame, label_name: str) -> dict[str, Any]:
    series = labels[label_name].dropna().astype("float64")
    if series.empty:
        return {"transition_rate": 0.0, "lag1_autocorrelation": None, "year_majority_ratio_range": 0.0, "year_flat_ratio_range": 0.0}
    transitions = float((series.diff().dropna() != 0).mean()) if len(series) > 1 else 0.0
    autocorr = series.autocorr(lag=1) if len(series) > 2 else np.nan
    by_year = grouped_distribution_v9_40(labels, label_name, "Y")
    majority = [item["majority_class_ratio"] for item in by_year.values()]
    flat = [item["flat_ratio"] for item in by_year.values()]
    return {
        "transition_rate": round(transitions, 6),
        "lag1_autocorrelation": None if pd.isna(autocorr) else round(float(autocorr), 6),
        "year_majority_ratio_range": round(max(majority) - min(majority), 6) if majority else 0.0,
        "year_flat_ratio_range": round(max(flat) - min(flat), 6) if flat else 0.0,
    }


def label_warnings_v9_40(timeframe: str, label_name: str, distribution: dict[str, Any], stability: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if distribution["majority_class_ratio"] > 0.70:
        warnings.append(f"{timeframe}/{label_name}: majority class ratio above 70%")
    if label_name.startswith("up_down_flat"):
        if distribution["flat_ratio"] < 0.05:
            warnings.append(f"{timeframe}/{label_name}: flat_ratio below 5%")
        if distribution["flat_ratio"] > 0.70:
            warnings.append(f"{timeframe}/{label_name}: flat_ratio above 70%")
    if stability["year_majority_ratio_range"] > 0.20 or stability["year_flat_ratio_range"] > 0.25:
        warnings.append(f"{timeframe}/{label_name}: descriptive yearly distribution drift warning")
    return warnings


def build_leakage_guard_v9_40(timeframe_metrics: dict[str, Any]) -> dict[str, Any]:
    violations = sum(item.get("leakage_violations", 0) for item in timeframe_metrics.values())
    return {
        "status": "PASS" if violations == 0 else "FAIL",
        "label_available_ts_gt_decision_ts_violations": int(violations),
        "future_return_used_only_as_label": True,
        "causal_volatility_uses_historical_feature": True,
        "no_future_volatility": True,
        "no_ml": True,
        "no_backtest": True,
    }


def build_forbidden_column_scan_v9_40(timeframe_metrics: dict[str, Any]) -> dict[str, Any]:
    forbidden_hits: list[str] = []
    for item in timeframe_metrics.values():
        columns = set(item.get("label_columns", []))
        forbidden_hits.extend(sorted(columns & {"prediction", "signal", "order", "pnl", "strategy"}))
    return {"status": "PASS" if not forbidden_hits else "FAIL", "forbidden_columns": forbidden_hits}


def select_primary_label_v9_40(timeframe_metrics: dict[str, Any], leakage_guard: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    if errors or leakage_guard["status"] != "PASS":
        return {
            "selected_primary_label": "none_requires_review",
            "reason": "selection blocked by errors or leakage guard failure",
            "diagnostic_only_labels": list(LABEL_DESIGNS),
        }
    primary_warnings = [
        warning
        for metrics in timeframe_metrics.values()
        for warning in metrics.get("warnings", [])
        if f"/{SELECTED_PRIMARY_LABEL}:" in warning
    ]
    if any("majority class ratio above 70%" in warning or "flat_ratio above 70%" in warning for warning in primary_warnings):
        h1_ok = all(
            metrics["label_distribution"]["up_down_flat_volnorm_h1_5y"]["majority_class_ratio"] <= 0.70
            and 0.05 <= metrics["label_distribution"]["up_down_flat_volnorm_h1_5y"]["flat_ratio"] <= 0.70
            for metrics in timeframe_metrics.values()
        )
        if h1_ok:
            return {
                "selected_primary_label": "up_down_flat_volnorm_h1_5y",
                "reason": "h4 volnorm is too FLAT-dominant on every timeframe; h1 volnorm remains below the dominance threshold and is selected as a candidate label for V9.41 review.",
                "diagnostic_only_labels": ["up_down_flat_volnorm_h4_5y", "binary_directional_volnorm_h4_5y"],
                "warnings": primary_warnings,
            }
        return {
            "selected_primary_label": "none_requires_review",
            "reason": "primary h4 volnorm label distribution is too dominant and requires review",
            "diagnostic_only_labels": list(LABEL_DESIGNS),
            "warnings": primary_warnings,
        }
    return {
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "reason": "h4 volatility-normalized ternary label passes causal checks and has no blocking dominance warning; it remains a candidate label, not a strategy.",
        "diagnostic_only_labels": ["up_down_flat_volnorm_h1_5y", "binary_directional_volnorm_h4_5y"],
        "warnings": primary_warnings,
    }


def quality_status_v9_40(labels_created: bool, leakage_guard: dict[str, Any], label_selection: dict[str, Any], warnings: list[str], errors: list[str]) -> str:
    if errors:
        return "FAIL"
    if leakage_guard["status"] != "PASS":
        return "FAIL_LEAKAGE"
    if not labels_created or label_selection["selected_primary_label"] == "none_requires_review":
        return "REQUIRES_REVIEW"
    return "PASS_WITH_WARNINGS" if warnings else "PASS"


def decide_v9_40(labels_created: bool, leakage_guard: dict[str, Any], quality_status: str, warnings: list[str], errors: list[str]) -> str:
    if leakage_guard["status"] != "PASS":
        return "ohlcv_aggtrades_5y_labels_blocked_by_leakage"
    if errors and labels_created:
        return "ohlcv_aggtrades_5y_labels_partial"
    if errors:
        return "ohlcv_aggtrades_5y_labels_blocked_by_quality"
    if quality_status == "REQUIRES_REVIEW":
        return "ohlcv_aggtrades_5y_labels_requires_manual_review"
    if labels_created and warnings:
        return "ohlcv_aggtrades_5y_labels_created_with_warnings"
    if labels_created:
        return "ohlcv_aggtrades_5y_labels_created"
    return "ohlcv_aggtrades_5y_labels_blocked_by_quality"


def coverage_status_v9_40(labels_created: bool, row_counts: dict[str, int]) -> str:
    if labels_created and row_counts == EXPECTED_FEATURE_ROWS:
        return "target_5y_label_window_complete"
    if any(value > 0 for value in row_counts.values()):
        return "target_5y_label_window_partial"
    return "target_5y_label_window_not_created"


def next_recommendation_v9_40(decision: str) -> str:
    if decision in {"ohlcv_aggtrades_5y_labels_created", "ohlcv_aggtrades_5y_labels_created_with_warnings"}:
        return "V9.41 - OHLCV + AggTrades 5Y Dataset"
    if decision == "ohlcv_aggtrades_5y_labels_requires_manual_review":
        return "V9.41 - Manual Label Review Pack"
    return "V9.41 - Label Design Correction"


def label_output_path_v9_40(timeframe: str) -> Path:
    return LABEL_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "labels.parquet"


def build_manifest_v9_40(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "datacard_path": DATACARD_MD_PATH.as_posix(),
        "distribution_path": DISTRIBUTION_JSON_PATH.as_posix(),
        "stability_path": STABILITY_JSON_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "selected_primary_label": report["selected_primary_label"],
        "row_counts": report["row_counts"],
        "valid_label_counts": report["valid_label_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
        "outputs": report["outputs"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_40(report: dict[str, Any]) -> str:
    lines = [
        "# V9.40 - OHLCV + AggTrades 5Y Label Factory",
        "",
        "## Resume",
        f"- Decision V9.40 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Labels crees : `{report['labels_created']}`.",
        f"- Dataset supervise cree : `{report['dataset_created']}`.",
        f"- Label principal selectionne : `{report['selected_primary_label']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Leakage guard : `{report['leakage_guard']['status']}`.",
        "",
        "## Row counts",
    ]
    for timeframe, rows in report["row_counts"].items():
        lines.append(f"- `{timeframe}` : `{rows}` lignes.")
    lines.extend(["", "## Distributions principales"])
    for timeframe, metrics in report["timeframe_metrics"].items():
        dist = metrics["label_distribution"].get(report["selected_primary_label"], {})
        lines.append(f"- `{timeframe}` : `{dist.get('counts', {})}`, flat_ratio `{dist.get('flat_ratio')}`.")
    lines.extend(
        [
            "",
            "## Limites",
            "- Ces labels sont des candidats descriptifs causaux. Ils ne prouvent aucun edge robuste.",
            "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.",
            "- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_datacard_v9_40(report: dict[str, Any]) -> str:
    return (
        "# Datacard V9.40 - Labels OHLCV + AggTrades 5Y\n\n"
        f"- Fenetre : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.\n"
        f"- Timeframes : `{', '.join(TIMEFRAMES)}`.\n"
        f"- Label principal candidat : `{report['selected_primary_label']}`.\n"
        "- Horizons produits : h4 volnorm, h1 volnorm, binaire directionnel h4.\n"
        "- Volatilite causale : `rolling_volatility_60` issue de la feature store, disponible a `decision_ts`.\n"
        "- `label_available_ts` est strictement posterieur a `decision_ts` pour les labels valides.\n"
        "- Usage interdit dans V9.40 : dataset supervise, ML, walk-forward, backtest, strategie, signal, ordre.\n"
    )


def update_state_surfaces_v9_40(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_40_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "selected_primary_label": report["selected_primary_label"],
        "row_counts": report["row_counts"],
        "valid_label_counts": report["valid_label_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
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
        "# Synthese courante - V9.40\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.40 : `{report['decision']}`.\n"
        f"- Labels crees : `{report['labels_created']}`.\n"
        f"- Dataset supervise cree : `{report['dataset_created']}`.\n"
        f"- Label principal candidat : `{report['selected_primary_label']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.\n"
        "- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, label factory OHLCV + aggTrades 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, ML, dataset supervise, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


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
