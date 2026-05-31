from __future__ import annotations

import json
import math
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.labels.redesigned_5y_label_factory_v9_64_schemas import (
    ALLOWED_DECISIONS,
    DIRECTION,
    DISTRIBUTION_JSON_PATH,
    DOC_PATH,
    FEATURE_BASE_PATH,
    FINDINGS,
    INPUT_PATHS,
    LABEL_BASE_PATH,
    LABEL_COLUMNS,
    LABEL_DESIGNS,
    LABEL_RUN_ID_PREFIX,
    LABEL_SCHEMA_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    REQUIRED_LABEL_COLUMNS,
    SAFETY_FLAGS,
    SELECTED_PRIMARY_LABEL,
    SOURCE_FEATURE_STORE_VERSION,
    SOURCE_LABEL_DIAGNOSTIC_VERSION,
    SOURCE_VERSION,
    TIMEFRAME_MINUTES,
    TIMEFRAMES,
    VERSION,
    WINDOW_LABEL,
)


SUCCESS_DECISIONS = {"redesigned_labels_created", "redesigned_labels_created_with_warnings"}


def run_redesigned_5y_label_factory_v9_64(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_redesigned_5y_label_factory_v9_64(root)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_json(root / DISTRIBUTION_JSON_PATH, report["label_distribution"])
    markdown = markdown_v9_64(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, manifest_v9_64(report))
    return report


def build_redesigned_5y_label_factory_v9_64(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    readiness = assess_readiness_v9_64(inputs)
    label_run_id = f"{LABEL_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    outputs: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    if readiness["ready"]:
        with ProcessPoolExecutor(max_workers=min(4, len(TIMEFRAMES))) as executor:
            futures = {executor.submit(create_timeframe_labels_v9_64, root, timeframe, label_run_id): timeframe for timeframe in TIMEFRAMES}
            for future in as_completed(futures):
                timeframe = futures[future]
                try:
                    result = future.result()
                    outputs[timeframe] = result["output"]
                    metrics[timeframe] = result["metrics"]
                    warnings.extend(result["metrics"].get("warnings", []))
                    print(f"[V9.64] timeframe_done={timeframe} rows={result['metrics']['row_count']}", flush=True)
                except Exception as exc:  # pragma: no cover - integration failure path.
                    outputs[timeframe] = {"created": False, "error": str(exc)}
                    errors.append(f"{timeframe}: {type(exc).__name__}: {exc}")
    else:
        errors.extend(readiness["errors"])
    labels_created = bool(metrics) and not errors and all(block.get("created") is True for block in outputs.values())
    leakage_guard = build_leakage_guard_v9_64(metrics)
    quality_status = "PASS" if labels_created and leakage_guard["status"] == "PASS" and not errors else "FAIL"
    decision = decide_v9_64(labels_created, leakage_guard, quality_status, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "label": WINDOW_LABEL},
        "funding_common_window_documented": {"start": "2021-05-05T00:00:00Z", "end": "2026-04-30T16:00:00Z"},
        "timeframes": list(TIMEFRAMES),
        "source_readiness": readiness,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "label_run_id": label_run_id,
        "label_designs": LABEL_DESIGNS,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "selected_primary_label_reason": "selection V9.63: binaire h4 causal, sans classe FLAT, distribution descriptive equilibree.",
        "labels_created": labels_created,
        "dataset_created": False,
        "outputs": outputs,
        "row_counts": {timeframe: metrics.get(timeframe, {}).get("row_count", 0) for timeframe in TIMEFRAMES},
        "valid_label_counts": {timeframe: metrics.get(timeframe, {}).get("valid_label_counts", {}) for timeframe in TIMEFRAMES},
        "invalid_label_counts": {timeframe: metrics.get(timeframe, {}).get("invalid_label_counts", {}) for timeframe in TIMEFRAMES},
        "label_distribution": {timeframe: metrics.get(timeframe, {}).get("label_distribution", {}) for timeframe in TIMEFRAMES},
        "split_preview_distribution": {timeframe: metrics.get(timeframe, {}).get("split_preview_distribution", {}) for timeframe in TIMEFRAMES},
        "distribution_by_year": {timeframe: metrics.get(timeframe, {}).get("distribution_by_year", {}) for timeframe in TIMEFRAMES},
        "distribution_by_month": {timeframe: metrics.get(timeframe, {}).get("distribution_by_month", {}) for timeframe in TIMEFRAMES},
        "transition_rate": {timeframe: metrics.get(timeframe, {}).get("transition_rate", {}) for timeframe in TIMEFRAMES},
        "entropy": {timeframe: metrics.get(timeframe, {}).get("entropy", {}) for timeframe in TIMEFRAMES},
        "majority_class_ratio": {timeframe: metrics.get(timeframe, {}).get("majority_class_ratio", {}) for timeframe in TIMEFRAMES},
        "leakage_guard": leakage_guard,
        "quality_status": quality_status,
        "coverage_status": "redesigned_label_window_complete" if labels_created else "redesigned_label_window_incomplete",
        "decision": decision,
        "next_recommendation": "V9.65 - Dataset avec label redesign" if decision in SUCCESS_DECISIONS else "V9.65 - Label redesign correction",
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "limitations": [
            "V9.64 cree des labels offline; aucun dataset supervise et aucun ML.",
            "Les seuils quantiles sont train-only et descriptifs; ils ne sont pas choisis par performance ML.",
            "Aucun backtest, walk-forward, strategie, signal, ordre, reseau ou telechargement.",
        ],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.64 decision: {report['decision']}")
    return report


def assess_readiness_v9_64(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    diagnostic = inputs["v9_63_diagnostic"]["payload"]
    if diagnostic.get("decision") != "label_redesign_candidate_binary_directional":
        errors.append("V9.63 did not select a binary directional candidate")
    if diagnostic.get("selected_primary_label") != SELECTED_PRIMARY_LABEL:
        errors.append("V9.63 selected label mismatch")
    return {
        "ready": not errors,
        "errors": errors,
        "v9_63_decision": diagnostic.get("decision"),
        "selected_primary_label": diagnostic.get("selected_primary_label"),
        "source_feature_store_version": SOURCE_FEATURE_STORE_VERSION,
    }


def create_timeframe_labels_v9_64(root: Path, timeframe: str, label_run_id: str) -> dict[str, Any]:
    feature_path = root / FEATURE_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "features.parquet"
    if not feature_path.is_file():
        raise FileNotFoundError(f"missing V9.47 feature parquet for {timeframe}: {feature_path}")
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
            "row_valid_for_combined_features",
        ],
        engine="pyarrow",
    )
    labels = create_label_frame_v9_64(frame, timeframe, label_run_id)
    output_path = root / label_output_path_v9_64(timeframe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    return {
        "output": {"created": True, "path": label_output_path_v9_64(timeframe).as_posix(), "bytes": output_path.stat().st_size, "rows": int(len(labels))},
        "metrics": summarize_labels_v9_64(labels, timeframe, output_path),
    }


def create_label_frame_v9_64(frame: pd.DataFrame, timeframe: str, label_run_id: str) -> pd.DataFrame:
    minutes = TIMEFRAME_MINUTES[timeframe]
    h1_bars = max(1, 60 // minutes)
    h4_bars = max(1, 240 // minutes)
    returns = pd.to_numeric(frame["log_return_1"], errors="coerce").to_numpy(dtype="float64")
    h1_future = future_log_return_v9_64(returns, h1_bars)
    h4_future = future_log_return_v9_64(returns, h4_bars)
    causal_vol = pd.to_numeric(frame["rolling_volatility_60"], errors="coerce").to_numpy(dtype="float64")
    valid_features = frame["row_valid_for_combined_features"].fillna(False).astype(bool).to_numpy()
    warmup = frame["warmup_row"].fillna(False).astype(bool).to_numpy()
    vol_valid = np.isfinite(causal_vol) & (causal_vol > 0)
    h1_threshold = causal_vol * math.sqrt(h1_bars) * LABEL_DESIGNS["binary_directional_volnorm_h1_5y"]["threshold_multiplier"]
    h4_threshold = causal_vol * math.sqrt(h4_bars) * LABEL_DESIGNS["binary_directional_volnorm_h4_5y"]["threshold_multiplier"]
    base_h1_valid = valid_features & ~warmup & vol_valid & np.isfinite(h1_future)
    base_h4_valid = valid_features & ~warmup & vol_valid & np.isfinite(h4_future)
    binary_h1 = binary_volnorm_label_v9_64(h1_future, h1_threshold, base_h1_valid)
    binary_h4 = binary_volnorm_label_v9_64(h4_future, h4_threshold, base_h4_valid)
    train_mask_h1 = train_mask_v9_64(len(frame)) & base_h1_valid
    train_mask_h4 = train_mask_v9_64(len(frame)) & base_h4_valid
    median_h1 = safe_quantile_v9_64(h1_future[train_mask_h1], 0.50)
    median_h4 = safe_quantile_v9_64(h4_future[train_mask_h4], 0.50)
    lower_h1 = safe_quantile_v9_64(h1_future[train_mask_h1], 1 / 3)
    upper_h1 = safe_quantile_v9_64(h1_future[train_mask_h1], 2 / 3)
    quantile_h1 = binary_quantile_label_v9_64(h1_future, median_h1, base_h1_valid)
    quantile_h4 = binary_quantile_label_v9_64(h4_future, median_h4, base_h4_valid)
    ternary_h1 = ternary_quantile_label_v9_64(h1_future, lower_h1, upper_h1, base_h1_valid)
    label_end_ts = frame["close_ts"].shift(-h4_bars)
    label_available_ts = label_end_ts + pd.Timedelta(milliseconds=1)
    selected_valid = binary_h4.notna().to_numpy()
    invalid_reason = invalid_reasons_v9_64(valid_features, warmup, vol_valid, np.isfinite(h4_future), selected_valid)
    null_count = sum(pd.Series(label).isna().astype("int16") for label in [binary_h1, binary_h4, quantile_h1, quantile_h4, ternary_h1])
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
            "source_label_diagnostic_version": SOURCE_LABEL_DIAGNOSTIC_VERSION,
            "selected_primary_label": SELECTED_PRIMARY_LABEL,
            "target_name": SELECTED_PRIMARY_LABEL,
            "horizon_name": "h4",
            "horizon_minutes": 240,
            "future_log_return_h1": h1_future,
            "future_log_return_h4": h4_future,
            "causal_vol_window_bars": 60,
            "causal_realized_vol": causal_vol,
            "volatility_threshold_multiplier_h1": LABEL_DESIGNS["binary_directional_volnorm_h1_5y"]["threshold_multiplier"],
            "volatility_threshold_multiplier_h4": LABEL_DESIGNS["binary_directional_volnorm_h4_5y"]["threshold_multiplier"],
            "volatility_normalized_threshold_h1": h1_threshold,
            "volatility_normalized_threshold_h4": h4_threshold,
            "train_quantile_median_h1": median_h1,
            "train_quantile_median_h4": median_h4,
            "train_quantile_lower_h1": lower_h1,
            "train_quantile_upper_h1": upper_h1,
            "binary_directional_volnorm_h1_5y": binary_h1,
            "binary_directional_volnorm_h4_5y": binary_h4,
            "quantile_directional_h1_5y": quantile_h1,
            "quantile_directional_h4_5y": quantile_h4,
            "up_down_flat_quantile_h1_5y": ternary_h1,
            "label_valid": selected_valid,
            "label_invalid_reason": invalid_reason,
            "warmup_row": warmup,
            "label_null_count": null_count.astype("int16"),
            "label_error_count": (~selected_valid).astype("int16"),
        }
    )
    return out[REQUIRED_LABEL_COLUMNS]


def future_log_return_v9_64(returns: np.ndarray, horizon_bars: int) -> np.ndarray:
    values = np.asarray(returns, dtype="float64")
    result = np.full(len(values), np.nan, dtype="float64")
    valid = np.isfinite(values)
    sums = np.concatenate(([0.0], np.where(valid, values, 0.0).cumsum()))
    counts = np.concatenate(([0], valid.astype("int64").cumsum()))
    if horizon_bars <= 0 or horizon_bars >= len(values):
        return result
    starts = np.arange(0, len(values) - horizon_bars)
    ends = starts + horizon_bars
    totals = sums[ends + 1] - sums[starts + 1]
    valid_counts = counts[ends + 1] - counts[starts + 1]
    result[starts] = np.where(valid_counts == horizon_bars, totals, np.nan)
    return result


def binary_volnorm_label_v9_64(future_return: np.ndarray, threshold: np.ndarray, valid: np.ndarray) -> pd.Series:
    labels = np.full(len(future_return), np.nan)
    labels[valid & (future_return > threshold)] = 1
    labels[valid & (future_return < -threshold)] = -1
    return pd.Series(labels, dtype="Int8")


def binary_quantile_label_v9_64(future_return: np.ndarray, median: float, valid: np.ndarray) -> pd.Series:
    labels = np.full(len(future_return), np.nan)
    if not np.isfinite(median):
        return pd.Series(labels, dtype="Int8")
    labels[valid & (future_return > median)] = 1
    labels[valid & (future_return <= median)] = -1
    return pd.Series(labels, dtype="Int8")


def ternary_quantile_label_v9_64(future_return: np.ndarray, lower: float, upper: float, valid: np.ndarray) -> pd.Series:
    labels = np.full(len(future_return), np.nan)
    if not np.isfinite(lower) or not np.isfinite(upper) or lower >= upper:
        return pd.Series(labels, dtype="Int8")
    labels[valid & (future_return < lower)] = -1
    labels[valid & (future_return > upper)] = 1
    labels[valid & (future_return >= lower) & (future_return <= upper)] = 0
    return pd.Series(labels, dtype="Int8")


def train_mask_v9_64(n: int) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    mask[: int(n * 0.60)] = True
    return mask


def safe_quantile_v9_64(values: np.ndarray, q: float) -> float:
    values = values[np.isfinite(values)]
    return float(np.quantile(values, q)) if len(values) else float("nan")


def invalid_reasons_v9_64(valid_features: np.ndarray, warmup: np.ndarray, vol_valid: np.ndarray, future_valid: np.ndarray, selected_valid: np.ndarray) -> np.ndarray:
    reasons = np.full(len(valid_features), "", dtype=object)
    reasons[~valid_features] = "feature_row_invalid"
    reasons[valid_features & warmup] = "warmup_row"
    reasons[valid_features & ~warmup & ~vol_valid] = "causal_vol_unavailable"
    reasons[valid_features & ~warmup & vol_valid & ~future_valid] = "future_horizon_unavailable"
    reasons[valid_features & ~warmup & vol_valid & future_valid & ~selected_valid] = "neutral_zone_excluded_by_binary_volnorm"
    return reasons


def summarize_labels_v9_64(labels: pd.DataFrame, timeframe: str, output_path: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "timeframe": timeframe,
        "created": True,
        "row_count": int(len(labels)),
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size,
        "valid_label_counts": {},
        "invalid_label_counts": {},
        "label_distribution": {},
        "split_preview_distribution": {},
        "distribution_by_year": {},
        "distribution_by_month": {},
        "transition_rate": {},
        "entropy": {},
        "majority_class_ratio": {},
        "leakage_violations": int(((labels["label_available_ts"] <= labels["decision_ts"]) & labels["label_valid"]).sum()),
        "warnings": [],
    }
    for label in LABEL_COLUMNS:
        valid = labels[label].dropna()
        counts = {str(int(key)): int(value) for key, value in valid.value_counts().sort_index().items()}
        distribution = distribution_stats_v9_64(counts)
        metrics["valid_label_counts"][label] = int(len(valid))
        metrics["invalid_label_counts"][label] = int(labels[label].isna().sum())
        metrics["label_distribution"][label] = distribution
        metrics["split_preview_distribution"][label] = split_preview_distribution_v9_64(labels, label)
        metrics["distribution_by_year"][label] = grouped_distribution_v9_64(labels, label, "%Y")
        metrics["distribution_by_month"][label] = grouped_distribution_v9_64(labels, label, "%Y-%m")
        metrics["transition_rate"][label] = transition_rate_v9_64(valid)
        metrics["entropy"][label] = distribution["entropy"]
        metrics["majority_class_ratio"][label] = distribution["majority_class_ratio"]
        if label == SELECTED_PRIMARY_LABEL and distribution["majority_class_ratio"] > 0.60:
            metrics["warnings"].append(f"{timeframe}/{label}: majority ratio above 60%")
    return metrics


def distribution_stats_v9_64(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    ratios = {key: value / total for key, value in counts.items()} if total else {}
    entropy = -sum(value * math.log(value, 2) for value in ratios.values() if value > 0)
    return {
        "counts": counts,
        "ratios": {key: round(value, 6) for key, value in ratios.items()},
        "entropy": round(entropy, 6),
        "majority_class_ratio": round(max(ratios.values()) if ratios else 0.0, 6),
        "flat_ratio": round(ratios.get("0", 0.0), 6),
    }


def grouped_distribution_v9_64(labels: pd.DataFrame, label: str, fmt: str) -> dict[str, Any]:
    valid = labels.loc[labels[label].notna(), ["decision_ts", label]].copy()
    if valid.empty:
        return {}
    group = pd.to_datetime(valid["decision_ts"], utc=True).dt.strftime(fmt)
    return {str(key): distribution_stats_v9_64({str(int(k)): int(v) for k, v in chunk[label].value_counts().sort_index().items()}) for key, chunk in valid.groupby(group, sort=True)}


def split_preview_distribution_v9_64(labels: pd.DataFrame, label: str) -> dict[str, Any]:
    valid = labels.loc[labels[label].notna(), label]
    n = len(valid)
    if n == 0:
        return {}
    cuts = {"train": (0, int(n * 0.60)), "validation": (int(n * 0.60), int(n * 0.80)), "test": (int(n * 0.80), n)}
    return {name: distribution_stats_v9_64({str(int(k)): int(v) for k, v in valid.iloc[start:end].value_counts().sort_index().items()}) for name, (start, end) in cuts.items()}


def transition_rate_v9_64(series: pd.Series) -> float:
    numeric = series.dropna().astype("int8")
    return round(float((numeric.diff().dropna() != 0).mean()), 6) if len(numeric) > 1 else 0.0


def build_leakage_guard_v9_64(metrics: dict[str, Any]) -> dict[str, Any]:
    violations = sum(item.get("leakage_violations", 0) for item in metrics.values())
    return {
        "status": "PASS" if violations == 0 else "FAIL",
        "label_available_ts_gt_decision_ts_violations": int(violations),
        "future_return_used_only_as_label": True,
        "causal_volatility_uses_past_feature": True,
        "quantile_thresholds_train_only": True,
        "validation_or_test_used_for_threshold_choice": False,
        "future_volatility_used": False,
    }


def decide_v9_64(labels_created: bool, leakage_guard: dict[str, Any], quality_status: str, warnings: list[str], errors: list[str]) -> str:
    if leakage_guard["status"] != "PASS":
        return "redesigned_labels_blocked_by_leakage"
    if errors:
        return "redesigned_labels_blocked_by_quality"
    if quality_status != "PASS":
        return "redesigned_labels_manual_review_required"
    if labels_created and warnings:
        return "redesigned_labels_created_with_warnings"
    if labels_created:
        return "redesigned_labels_created"
    return "redesigned_labels_blocked_by_quality"


def label_output_path_v9_64(timeframe: str) -> Path:
    return LABEL_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "labels.parquet"


def manifest_v9_64(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "distribution_path": DISTRIBUTION_JSON_PATH.as_posix(),
        "manifest_path": MANIFEST_PATH.as_posix(),
        "outputs": report["outputs"],
        "selected_primary_label": report["selected_primary_label"],
        "quality_status": report["quality_status"],
        "leakage_guard": report["leakage_guard"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def markdown_v9_64(report: dict[str, Any]) -> str:
    lines = [
        "# V9.64 - Label factory redesign 5Y",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Label principal : `{report['selected_primary_label']}`.",
        f"- Labels crees : `{report['labels_created']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Leakage guard : `{report['leakage_guard']['status']}`.",
        "",
        "## Distribution label principal",
    ]
    for timeframe, block in report["label_distribution"].items():
        dist = block.get(report["selected_primary_label"], {})
        lines.append(f"- `{timeframe}` : `{dist.get('counts', {})}`, majority `{dist.get('majority_class_ratio')}`.")
    lines.append("\nAucun dataset supervise, ML, backtest, walk-forward, strategie, signal, ordre, reseau ou telechargement.\n")
    return "\n".join(lines)


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    return {"path": path.as_posix(), "available": full.is_file(), "payload": _read_json(full) if full.is_file() and full.suffix == ".json" else {}}


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
