from __future__ import annotations

import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_datacard import build_dataset_datacard_v9_60
from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas import (
    ALLOWED_DECISIONS,
    COMMON_WINDOW_LABEL,
    DATACARD_MD_PATH,
    DATASET_BASE_PATH,
    DATASET_COLUMNS,
    DATASET_RUN_ID_PREFIX,
    DATASET_SCHEMA_VERSION,
    DIAGNOSTIC_LABELS,
    DIRECTION,
    DOC_PATH,
    FEATURE_AUDIT_COLUMNS,
    FEATURE_BASE_PATH,
    FEATURE_COLUMNS,
    FINDINGS,
    FORBIDDEN_COLUMNS,
    INPUT_PATHS,
    LABEL_BASE_PATH,
    LABEL_COLUMNS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    SELECTED_PRIMARY_LABEL,
    SOURCE_FEATURE_STORE_VERSION,
    SOURCE_FEATURE_VALIDATION_VERSION,
    SOURCE_LABEL_VERSION,
    SOURCE_VERSION,
    SPLIT_POLICY,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAME_MINUTES,
    TIMEFRAMES,
    VERSION,
)


SUCCESS_DECISIONS = {"funding_common_window_dataset_created", "funding_common_window_dataset_created_with_warnings"}


def run_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_dataset_report_v9_60(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_60(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DATACARD_MD_PATH, build_dataset_datacard_v9_60(report))
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_60(report))
    return report


def build_dataset_report_v9_60(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    feature_readiness = assess_feature_readiness_v9_60(inputs)
    label_readiness = assess_label_readiness_v9_60(inputs)
    dataset_run_id = f"{DATASET_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    outputs: dict[str, Any] = {}
    metrics_by_timeframe: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    if feature_readiness["ready"] and label_readiness["ready"]:
        workers = min(int(os.environ.get("GALAPAGOS_V9_60_WORKERS", "4")), len(TIMEFRAMES))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(create_timeframe_dataset_v9_60, root, timeframe, dataset_run_id): timeframe for timeframe in TIMEFRAMES}
            for future in as_completed(futures):
                timeframe = futures[future]
                try:
                    result = future.result()
                    outputs[timeframe] = result["output"]
                    metrics_by_timeframe[timeframe] = result["metrics"]
                    warnings.extend(result["metrics"].get("warnings", []))
                    print(f"[V9.60] timeframe_done={timeframe} rows={result['metrics']['row_count']}", flush=True)
                except Exception as exc:  # pragma: no cover - integration failure path.
                    outputs[timeframe] = {"created": False, "error": str(exc)}
                    errors.append(f"{timeframe}: {exc}")
    else:
        errors.extend(feature_readiness["errors"])
        errors.extend(label_readiness["errors"])
    dataset_created = bool(metrics_by_timeframe) and not errors and all(item.get("created") is True for item in outputs.values())
    leakage_guard = build_leakage_guard_v9_60(metrics_by_timeframe)
    forbidden_column_scan = build_forbidden_scan_v9_60(metrics_by_timeframe)
    row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("row_count", 0) for timeframe in TIMEFRAMES}
    valid_row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("valid_row_count", 0) for timeframe in TIMEFRAMES}
    invalid_row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("invalid_row_count", 0) for timeframe in TIMEFRAMES}
    quality_status = "PASS" if dataset_created and leakage_guard["status"] == "PASS" and forbidden_column_scan["status"] == "PASS" and not errors else "FAIL"
    coverage_status = "funding_common_window_dataset_complete" if dataset_created and all(value > 0 for value in row_counts.values()) else "funding_common_window_dataset_incomplete"
    decision = decide_v9_60(dataset_created, feature_readiness, label_readiness, leakage_guard, quality_status, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "label": COMMON_WINDOW_LABEL},
        "timeframes": list(TIMEFRAMES),
        "feature_readiness": feature_readiness,
        "label_readiness": label_readiness,
        "dataset_design": {
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "dataset_run_id": dataset_run_id,
            "target_name": SELECTED_PRIMARY_LABEL,
            "selected_primary_label": SELECTED_PRIMARY_LABEL,
            "diagnostic_label_columns": list(DIAGNOSTIC_LABELS),
            "split_policy": SPLIT_POLICY,
            "features_are_source_features_only": True,
            "feature_columns_count": len(FEATURE_COLUMNS),
            "funding_features_included": True,
        },
        "dataset_created": dataset_created,
        "outputs": outputs,
        "target_name": SELECTED_PRIMARY_LABEL,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "row_counts": row_counts,
        "valid_row_counts": valid_row_counts,
        "invalid_row_counts": invalid_row_counts,
        "label_distribution": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("label_distribution", {}) for timeframe in TIMEFRAMES},
        "split_distribution": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("split_distribution", {}) for timeframe in TIMEFRAMES},
        "monthly_distribution": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("monthly_distribution", {}) for timeframe in TIMEFRAMES},
        "null_summary": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("null_summary", {}) for timeframe in TIMEFRAMES},
        "invalid_reason_summary": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("invalid_reason_summary", {}) for timeframe in TIMEFRAMES},
        "target_majority_ratio": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("target_majority_ratio", 0.0) for timeframe in TIMEFRAMES},
        "target_flat_ratio": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("target_flat_ratio", 0.0) for timeframe in TIMEFRAMES},
        "entropy": {timeframe: metrics_by_timeframe.get(timeframe, {}).get("entropy", 0.0) for timeframe in TIMEFRAMES},
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_column_scan,
        "quality_status": quality_status,
        "coverage_status": coverage_status,
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "limitations": [
            "V9.60 cree un dataset supervise offline sur fenetre commune funding, mais n'execute aucun ML.",
            "Le split est temporel simple 60/20/20 sans walk-forward dans cette mission.",
        ],
        "decision": decision,
        "next_recommendation": "V9.61 - Funding dataset validation" if decision in SUCCESS_DECISIONS else "V9.61 - Funding dataset correction",
        "runtime_seconds": round(time.monotonic() - started, 3),
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
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.60 decision: {report['decision']}")
    return report


def create_timeframe_dataset_v9_60(root: Path, timeframe: str, dataset_run_id: str) -> dict[str, Any]:
    feature_path = root / FEATURE_BASE_PATH / f"timeframe={timeframe}" / f"window={COMMON_WINDOW_LABEL}" / "features.parquet"
    label_path = root / LABEL_BASE_PATH / f"timeframe={timeframe}" / "window=2021-05-05_2026-05-05" / "labels.parquet"
    feature_columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "open_ts",
        "close_ts",
        "decision_ts",
        "available_ts",
        "feature_available_ts",
        "funding_common_feature_schema_version",
        *FEATURE_COLUMNS,
        *FEATURE_AUDIT_COLUMNS,
    ]
    label_columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "decision_ts",
        "label_available_ts",
        "label_schema_version",
        *LABEL_COLUMNS,
        "label_null_count",
        "label_error_count",
    ]
    features = pd.read_parquet(feature_path, columns=feature_columns, engine="pyarrow")
    labels = pd.read_parquet(label_path, columns=label_columns, engine="pyarrow")
    labels = labels.loc[pd.to_datetime(labels["event_ts"], utc=True).isin(pd.to_datetime(features["event_ts"], utc=True))].reset_index(drop=True)
    validate_alignment_v9_60(features, labels, timeframe)
    dataset = assemble_dataset_frame_v9_60(features, labels, timeframe, dataset_run_id)
    output_path = root / dataset_output_path_v9_60(timeframe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    metrics = summarize_dataset_v9_60(dataset, timeframe, output_path)
    return {"output": {"created": True, "path": dataset_output_path_v9_60(timeframe).as_posix(), "bytes": output_path.stat().st_size, "rows": int(len(dataset))}, "metrics": metrics}


def validate_alignment_v9_60(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> None:
    if len(features) != len(labels):
        raise ValueError(f"{timeframe}: feature/label row count mismatch {len(features)} != {len(labels)}")
    for column in ["symbol", "timeframe", "event_ts"]:
        if not features[column].reset_index(drop=True).equals(labels[column].reset_index(drop=True)):
            raise ValueError(f"{timeframe}: feature/label alignment mismatch on {column}")
    decision_delta_ms = (pd.to_datetime(features["decision_ts"], utc=True) - pd.to_datetime(labels["decision_ts"], utc=True)).dt.total_seconds().mul(1000)
    if not bool(decision_delta_ms.eq(1.0).all()):
        raise ValueError(f"{timeframe}: feature/label decision_ts boundary mismatch")


def assemble_dataset_frame_v9_60(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str, dataset_run_id: str) -> pd.DataFrame:
    n = len(features)
    split = split_series_v9_60(n)
    target = labels[SELECTED_PRIMARY_LABEL]
    label_available_ts = selected_h1_label_available_ts_v9_60(features, timeframe)
    feature_ok = features["row_valid_for_funding_common_features"].fillna(False).astype(bool)
    feature_available_ok = pd.to_datetime(features["feature_available_ts"], utc=True) <= pd.to_datetime(features["decision_ts"], utc=True)
    label_available_ok = pd.to_datetime(label_available_ts, utc=True) > pd.to_datetime(features["decision_ts"], utc=True)
    target_available = target.notna()
    row_valid = feature_ok & feature_available_ok & label_available_ok & target_available
    invalid_reason = np.full(n, "", dtype=object)
    invalid_reason[~feature_ok.to_numpy()] = "feature_row_invalid"
    invalid_reason[(feature_ok & ~feature_available_ok).to_numpy()] = "feature_available_after_decision"
    invalid_reason[(feature_ok & feature_available_ok & ~target_available).to_numpy()] = "target_unavailable"
    invalid_reason[(feature_ok & feature_available_ok & target_available & ~label_available_ok).to_numpy()] = "label_available_not_after_decision"
    target_missing = (~target_available).astype("int16")
    leakage_errors = ((~feature_available_ok) | (~label_available_ok)).astype("int16")
    feature_errors = pd.to_numeric(features["funding_common_feature_error_count"], errors="coerce").fillna(0).astype("int16")
    dataset_error_count = (feature_errors + target_missing + leakage_errors).astype("int16")
    dataset_null_count = (pd.to_numeric(features["funding_common_feature_null_count"], errors="coerce").fillna(0).astype("int16") + pd.to_numeric(labels["label_null_count"], errors="coerce").fillna(0).astype("int16") + target_missing).astype("int16")
    out = features[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "open_ts", "close_ts", "decision_ts", "available_ts", "feature_available_ts", "funding_common_feature_schema_version", *FEATURE_COLUMNS, *FEATURE_AUDIT_COLUMNS]].copy()
    out["label_available_ts"] = label_available_ts
    out["split"] = split
    out["walk_forward_group"] = out["decision_ts"].dt.strftime("%Y-%m")
    out["purge_embargo_group"] = SPLIT_POLICY["purge_embargo_group"]
    out["dataset_run_id"] = dataset_run_id
    out["dataset_schema_version"] = DATASET_SCHEMA_VERSION
    out["label_schema_version"] = labels["label_schema_version"]
    out["source_combined_feature_store_version"] = SOURCE_FEATURE_STORE_VERSION
    out["source_combined_feature_validation_version"] = SOURCE_FEATURE_VALIDATION_VERSION
    out["source_label_version"] = SOURCE_LABEL_VERSION
    out["target_name"] = SELECTED_PRIMARY_LABEL
    out["selected_primary_label"] = SELECTED_PRIMARY_LABEL
    for column in LABEL_COLUMNS:
        out[column] = labels[column]
    out["label_null_count"] = labels["label_null_count"]
    out["label_error_count"] = labels["label_error_count"]
    out["row_valid_for_dataset"] = row_valid
    out["dataset_null_count"] = dataset_null_count
    out["dataset_error_count"] = dataset_error_count
    out["dataset_invalid_reason"] = invalid_reason
    return out[DATASET_COLUMNS]


def selected_h1_label_available_ts_v9_60(features: pd.DataFrame, timeframe: str) -> pd.Series:
    horizon_bars = 60 // TIMEFRAME_MINUTES[timeframe]
    return features["close_ts"].shift(-horizon_bars) + pd.Timedelta(milliseconds=1)


def split_series_v9_60(n: int) -> np.ndarray:
    train_end = int(n * SPLIT_POLICY["train_ratio"])
    validation_end = int(n * (SPLIT_POLICY["train_ratio"] + SPLIT_POLICY["validation_ratio"]))
    split = np.empty(n, dtype=object)
    split[:train_end] = "train"
    split[train_end:validation_end] = "validation"
    split[validation_end:] = "test"
    return split


def summarize_dataset_v9_60(dataset: pd.DataFrame, timeframe: str, output_path: Path) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], SELECTED_PRIMARY_LABEL]
    target_distribution = distribution_stats_v9_60(value_counts_v9_60(valid))
    leakage_feature = int((dataset["feature_available_ts"] > dataset["decision_ts"]).sum())
    leakage_label = int(((dataset["label_available_ts"] <= dataset["decision_ts"]) & dataset["row_valid_for_dataset"]).sum())
    invalid_reason_summary = {str(key): int(value) for key, value in dataset.loc[~dataset["row_valid_for_dataset"], "dataset_invalid_reason"].value_counts(dropna=False).sort_index().items()}
    warnings: list[str] = []
    if invalid_reason_summary:
        warnings.append(f"{timeframe}: invalid rows retained for audit")
    return {
        "timeframe": timeframe,
        "created": True,
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size,
        "row_count": int(len(dataset)),
        "valid_row_count": int(dataset["row_valid_for_dataset"].sum()),
        "invalid_row_count": int((~dataset["row_valid_for_dataset"]).sum()),
        "target_name": SELECTED_PRIMARY_LABEL,
        "label_distribution": target_distribution,
        "split_distribution": split_distribution_v9_60(dataset),
        "monthly_distribution": monthly_distribution_v9_60(dataset),
        "invalid_reason_summary": invalid_reason_summary,
        "null_summary": null_summary_v9_60(dataset),
        "dataset_error_count_sum": int(dataset["dataset_error_count"].sum()),
        "feature_available_ts_gt_decision_ts": leakage_feature,
        "label_available_ts_lte_decision_ts_for_valid_rows": leakage_label,
        "forbidden_columns": sorted(set(dataset.columns) & FORBIDDEN_COLUMNS),
        "target_majority_ratio": target_distribution["majority_class_ratio"],
        "target_flat_ratio": target_distribution["flat_ratio"],
        "entropy": target_distribution["entropy"],
        "split_monotone": split_monotone_v9_60(dataset),
        "train_before_validation_before_test": train_before_validation_before_test_v9_60(dataset),
        "warnings": warnings,
    }


def assess_feature_readiness_v9_60(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_59_feature_store"].get("payload", {})
    errors: list[str] = []
    if report.get("decision") not in {"funding_common_window_feature_store_created", "funding_common_window_feature_store_created_with_warnings"}:
        errors.append("V9.59 feature store is not created")
    if report.get("quality_status") != "PASS" or report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("V9.59 feature store quality/leakage is not PASS")
    return {"ready": not errors, "errors": errors, "row_counts": report.get("row_counts"), "source_feature_store_version": SOURCE_FEATURE_STORE_VERSION}


def assess_label_readiness_v9_60(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_40_label_factory"].get("payload", {})
    errors: list[str] = []
    if report.get("labels_created") is not True:
        errors.append("V9.40 labels_created is not true")
    if report.get("selected_primary_label") != SELECTED_PRIMARY_LABEL:
        errors.append("V9.40 selected primary label mismatch")
    if report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("V9.40 label leakage guard is not PASS")
    return {"ready": not errors, "errors": errors, "source_label_version": SOURCE_LABEL_VERSION, "selected_primary_label": report.get("selected_primary_label")}


def value_counts_v9_60(series: pd.Series) -> dict[str, int]:
    return {str(int(key)): int(value) for key, value in series.dropna().value_counts().sort_index().items()}


def distribution_stats_v9_60(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    ratios = {key: (value / total if total else 0.0) for key, value in counts.items()}
    entropy = -sum(ratio * math.log(ratio, 2) for ratio in ratios.values() if ratio > 0)
    return {"counts": counts, "ratios": {key: round(value, 6) for key, value in ratios.items()}, "entropy": round(entropy, 6), "majority_class_ratio": round(max(ratios.values()) if ratios else 0.0, 6), "flat_ratio": round(ratios.get("0", 0.0), 6)}


def split_distribution_v9_60(dataset: pd.DataFrame) -> dict[str, Any]:
    return {str(split): {"rows": int(len(chunk)), **distribution_stats_v9_60(value_counts_v9_60(chunk[SELECTED_PRIMARY_LABEL]))} for split, chunk in dataset.loc[dataset["row_valid_for_dataset"]].groupby("split", sort=False)}


def monthly_distribution_v9_60(dataset: pd.DataFrame) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], ["walk_forward_group", SELECTED_PRIMARY_LABEL]]
    return {str(month): {"rows": int(len(chunk)), **distribution_stats_v9_60(value_counts_v9_60(chunk[SELECTED_PRIMARY_LABEL]))} for month, chunk in valid.groupby("walk_forward_group", sort=True)}


def null_summary_v9_60(dataset: pd.DataFrame) -> dict[str, Any]:
    return {"dataset_null_count_sum": int(dataset["dataset_null_count"].sum()), "dataset_error_count_sum": int(dataset["dataset_error_count"].sum())}


def split_monotone_v9_60(dataset: pd.DataFrame) -> bool:
    ranks = dataset["split"].map({"train": 0, "validation": 1, "test": 2}).to_numpy()
    return bool(np.all(ranks[:-1] <= ranks[1:])) if len(ranks) > 1 else True


def train_before_validation_before_test_v9_60(dataset: pd.DataFrame) -> bool:
    ranges = {split: (chunk["decision_ts"].min(), chunk["decision_ts"].max()) for split, chunk in dataset.groupby("split", sort=False)}
    return set(ranges) == {"train", "validation", "test"} and bool(ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0])


def build_leakage_guard_v9_60(metrics: dict[str, Any]) -> dict[str, Any]:
    feature_violations = sum(item.get("feature_available_ts_gt_decision_ts", 0) for item in metrics.values())
    label_violations = sum(item.get("label_available_ts_lte_decision_ts_for_valid_rows", 0) for item in metrics.values())
    return {"status": "PASS" if feature_violations == 0 and label_violations == 0 else "FAIL", "feature_available_ts_gt_decision_ts": int(feature_violations), "label_available_ts_lte_decision_ts_for_valid_rows": int(label_violations), "no_future_leak": feature_violations == 0 and label_violations == 0}


def build_forbidden_scan_v9_60(metrics: dict[str, Any]) -> dict[str, Any]:
    hits = sorted({column for item in metrics.values() for column in item.get("forbidden_columns", [])})
    return {"status": "PASS" if not hits else "FAIL", "forbidden_columns": hits}


def decide_v9_60(dataset_created: bool, feature_readiness: dict[str, Any], label_readiness: dict[str, Any], leakage_guard: dict[str, Any], quality_status: str, warnings: list[str], errors: list[str]) -> str:
    if not feature_readiness["ready"]:
        return "funding_common_window_dataset_blocked_by_feature_quality"
    if not label_readiness["ready"]:
        return "funding_common_window_dataset_blocked_by_label_quality"
    if leakage_guard["status"] != "PASS":
        return "funding_common_window_dataset_blocked_by_leakage"
    if quality_status != "PASS":
        return "funding_common_window_dataset_partial"
    if warnings:
        return "funding_common_window_dataset_created_with_warnings"
    return "funding_common_window_dataset_created" if dataset_created and not errors else "funding_common_window_dataset_partial"


def dataset_output_path_v9_60(timeframe: str) -> Path:
    return DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={COMMON_WINDOW_LABEL}" / "dataset.parquet"


def build_manifest_v9_60(report: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "source_version": SOURCE_VERSION, "created_at_utc": report["created_at_utc"], "decision": report["decision"], "report_path": REPORT_JSON_PATH.as_posix(), "datacard_path": DATACARD_MD_PATH.as_posix(), "manifest_path": MANIFEST_PATH.as_posix(), "outputs": report["outputs"], "quality_status": report["quality_status"], "coverage_status": report["coverage_status"], "leakage_guard": report["leakage_guard"], "safety_flags": report["safety_flags"], "network_used": False, "new_data_downloaded": False}


def build_markdown_v9_60(report: dict[str, Any]) -> str:
    return f"# V9.60 - Dataset common window avec funding\n\n- Decision : `{report['decision']}`.\n- Dataset cree : `{report['dataset_created']}`.\n- Fenetre : `{report['target_window']['start']}` -> `{report['target_window']['end']}`.\n- Target : `{report['target_name']}`.\n- Quality : `{report['quality_status']}`.\n- Leakage : `{report['leakage_guard']['status']}`.\n\nAucun ML, backtest, walk-forward, strategie ou signal.\n"


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    return {"path": path.as_posix(), "available": full.is_file(), "payload": _read_json(full) if full.is_file() else {}}


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
