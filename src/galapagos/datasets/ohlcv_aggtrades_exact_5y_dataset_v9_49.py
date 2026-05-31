from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_datacard import build_dataset_datacard_v9_49
from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_schemas import (
    ALLOWED_DECISIONS,
    DATACARD_MD_PATH,
    DATASET_BASE_PATH,
    DATASET_COLUMNS,
    DATASET_RUN_ID_PREFIX,
    DATASET_SCHEMA_VERSION,
    DIAGNOSTIC_LABELS,
    DIRECTION,
    DOC_PATH,
    EXPECTED_ROWS,
    FEATURE_AUDIT_COLUMNS,
    FEATURE_BASE_PATH,
    FEATURE_COLUMNS,
    FINDINGS,
    FORBIDDEN_COLUMNS,
    INPUT_PATHS,
    LABEL_BASE_PATH,
    LABEL_COLUMNS,
    LAST_VALIDATED_VERSION,
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
    TOTAL_DAYS,
    VERSION,
)


def run_ohlcv_aggtrades_exact_5y_dataset_v9_49(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_dataset_report_v9_49(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_49(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DATACARD_MD_PATH, build_dataset_datacard_v9_49(report))
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_49(report))
    update_state_surfaces_v9_49(root, report)
    return report


def build_dataset_report_v9_49(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    feature_readiness = assess_feature_readiness_v9_49(inputs)
    label_readiness = assess_label_readiness_v9_49(inputs)
    dataset_run_id = f"{DATASET_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"

    outputs: dict[str, Any] = {}
    metrics_by_timeframe: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []

    if feature_readiness["ready"] and label_readiness["ready"]:
        for timeframe in TIMEFRAMES:
            try:
                result = create_timeframe_dataset_v9_49(root, timeframe, dataset_run_id)
                outputs[timeframe] = result["output"]
                metrics_by_timeframe[timeframe] = result["metrics"]
                warnings.extend(result["metrics"].get("warnings", []))
            except Exception as exc:  # pragma: no cover - integration failure path.
                outputs[timeframe] = {"created": False, "error": str(exc)}
                errors.append(f"{timeframe}: {exc}")
    else:
        errors.extend(feature_readiness["errors"])
        errors.extend(label_readiness["errors"])

    leakage_guard = build_leakage_guard_v9_49(metrics_by_timeframe)
    forbidden_column_scan = build_forbidden_scan_v9_49(metrics_by_timeframe)
    dataset_created = bool(metrics_by_timeframe) and not errors and all(item.get("created") is True for item in outputs.values())
    row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("row_count", 0) for timeframe in TIMEFRAMES}
    valid_row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("valid_row_count", 0) for timeframe in TIMEFRAMES}
    invalid_row_counts = {timeframe: metrics_by_timeframe.get(timeframe, {}).get("invalid_row_count", 0) for timeframe in TIMEFRAMES}
    quality_status = quality_status_v9_49(dataset_created, leakage_guard, forbidden_column_scan, warnings, errors)
    coverage_status = coverage_status_v9_49(dataset_created, row_counts)
    decision = decide_v9_49(dataset_created, feature_readiness, label_readiness, leakage_guard, quality_status, warnings, errors)

    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"combined_features_5y_dataset_created", "combined_features_5y_dataset_created_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": TOTAL_DAYS},
        "timeframes": list(TIMEFRAMES),
        "source_combined_feature_store_version": SOURCE_FEATURE_STORE_VERSION,
        "source_combined_feature_validation_version": SOURCE_FEATURE_VALIDATION_VERSION,
        "source_label_version": SOURCE_LABEL_VERSION,
        "feature_readiness": feature_readiness,
        "label_readiness": label_readiness,
        "dataset_design": {
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "dataset_run_id": dataset_run_id,
            "target_name": SELECTED_PRIMARY_LABEL,
            "selected_primary_label": SELECTED_PRIMARY_LABEL,
            "diagnostic_label_columns": list(DIAGNOSTIC_LABELS),
            "split_policy": SPLIT_POLICY,
            "splits_in_dataset_parquet": True,
            "feature_columns_count": len(FEATURE_COLUMNS),
            "base_feature_columns_count": 41,
            "exact_feature_columns_count": 56,
            "features_are_source_features_only": True,
        },
        "dataset_created": dataset_created,
        "outputs": outputs,
        "target_name": SELECTED_PRIMARY_LABEL,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "row_counts": row_counts,
        "valid_row_counts": valid_row_counts,
        "invalid_row_counts": invalid_row_counts,
        "label_distribution": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("label_distribution", {})
            for timeframe in TIMEFRAMES
        },
        "split_distribution": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("split_distribution", {})
            for timeframe in TIMEFRAMES
        },
        "monthly_distribution": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("monthly_distribution", {})
            for timeframe in TIMEFRAMES
        },
        "null_summary": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("null_summary", {})
            for timeframe in TIMEFRAMES
        },
        "target_majority_ratio": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("target_majority_ratio", 0.0)
            for timeframe in TIMEFRAMES
        },
        "target_flat_ratio": {
            timeframe: metrics_by_timeframe.get(timeframe, {}).get("target_flat_ratio", 0.0)
            for timeframe in TIMEFRAMES
        },
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_column_scan,
        "quality_status": quality_status,
        "coverage_status": coverage_status,
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "limitations": [
            "V9.49 cree un dataset supervise offline, mais n'execute aucun ML.",
            "Le target H1 est un candidat de recherche et ne valide aucun edge, strategie ou signal.",
            "Le split est temporel simple 60/20/20 sans purge/embargo reel; V9.49 reste un dataset-only preview.",
        ],
        "decision": decision,
        "next_recommendation": next_recommendation_v9_49(decision),
        "runtime_seconds": round(time.monotonic() - started, 3),
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.49 decision: {report['decision']}")
    return report


def assess_feature_readiness_v9_49(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_48_feature_validation"].get("payload", {})
    errors: list[str] = []
    if not inputs["v9_48_feature_validation"].get("available"):
        errors.append("missing V9.48 combined feature validation report")
    if report.get("coverage_status") != "target_5y_combined_feature_window_complete":
        errors.append("V9.48 combined feature coverage is not complete")
    if report.get("quality_status") != "PASS":
        errors.append("V9.48 combined feature quality is not PASS")
    if report.get("leakage_guard_status") != "PASS":
        errors.append("V9.48 combined feature leakage guard is not PASS")
    if report.get("row_counts") != EXPECTED_ROWS:
        errors.append(f"V9.48 combined feature row counts mismatch: {report.get('row_counts')}")
    return {
        "ready": not errors,
        "errors": errors,
        "source_feature_store_version": SOURCE_FEATURE_STORE_VERSION,
        "source_feature_validation_version": SOURCE_FEATURE_VALIDATION_VERSION,
        "coverage_status": report.get("coverage_status"),
        "quality_status": report.get("quality_status"),
        "leakage_guard_status": report.get("leakage_guard_status"),
        "row_counts": report.get("row_counts"),
    }


def assess_label_readiness_v9_49(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_40_label_factory"].get("payload", {})
    errors: list[str] = []
    if not inputs["v9_40_label_factory"].get("available"):
        errors.append("missing V9.40 label factory report")
    if report.get("labels_created") is not True:
        errors.append("V9.40 labels_created is not true")
    if report.get("coverage_status") != "target_5y_label_window_complete":
        errors.append("V9.40 label coverage is not complete")
    if report.get("quality_status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        errors.append("V9.40 label quality is not pass/pass_with_warnings")
    if report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("V9.40 label leakage guard is not PASS")
    if report.get("selected_primary_label") != SELECTED_PRIMARY_LABEL:
        errors.append(f"V9.40 selected primary label is not {SELECTED_PRIMARY_LABEL}")
    if report.get("row_counts") != EXPECTED_ROWS:
        errors.append(f"V9.40 label row counts mismatch: {report.get('row_counts')}")
    return {
        "ready": not errors,
        "errors": errors,
        "source_label_version": SOURCE_LABEL_VERSION,
        "selected_primary_label": report.get("selected_primary_label"),
        "coverage_status": report.get("coverage_status"),
        "quality_status": report.get("quality_status"),
        "leakage_guard": report.get("leakage_guard"),
        "row_counts": report.get("row_counts"),
        "valid_label_counts": report.get("valid_label_counts", {}),
    }


def create_timeframe_dataset_v9_49(root: Path, timeframe: str, dataset_run_id: str) -> dict[str, Any]:
    feature_path = root / FEATURE_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "features.parquet"
    label_path = root / LABEL_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "labels.parquet"
    if not feature_path.is_file():
        raise FileNotFoundError(f"missing feature parquet for {timeframe}: {feature_path}")
    if not label_path.is_file():
        raise FileNotFoundError(f"missing label parquet for {timeframe}: {label_path}")

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
        "combined_feature_schema_version",
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
    features = pd.read_parquet(feature_path, columns=feature_columns)
    labels = pd.read_parquet(label_path, columns=label_columns)
    validate_alignment_v9_49(features, labels, timeframe)
    dataset = assemble_dataset_frame_v9_49(features, labels, timeframe, dataset_run_id)
    output_path = root / dataset_output_path_v9_49(timeframe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    metrics = summarize_dataset_v9_49(dataset, timeframe, output_path)
    return {
        "output": {
            "created": True,
            "path": dataset_output_path_v9_49(timeframe).as_posix(),
            "bytes": output_path.stat().st_size,
            "rows": int(len(dataset)),
        },
        "metrics": metrics,
    }


def validate_alignment_v9_49(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> None:
    if len(features) != len(labels):
        raise ValueError(f"{timeframe}: feature/label row count mismatch {len(features)} != {len(labels)}")
    for column in ["source", "venue", "market_type", "symbol", "timeframe", "event_ts"]:
        if not features[column].equals(labels[column]):
            raise ValueError(f"{timeframe}: feature/label alignment mismatch on {column}")
    decision_delta_ms = (
        pd.to_datetime(features["decision_ts"], utc=True)
        - pd.to_datetime(labels["decision_ts"], utc=True)
    ).dt.total_seconds().mul(1000)
    if not bool(decision_delta_ms.eq(1.0).all()):
        raise ValueError(f"{timeframe}: feature/label decision_ts boundary mismatch")


def assemble_dataset_frame_v9_49(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str, dataset_run_id: str) -> pd.DataFrame:
    n = len(features)
    split = split_series_v9_49(n)
    target = labels[SELECTED_PRIMARY_LABEL]
    label_available_ts = selected_h1_label_available_ts_v9_49(features, timeframe)
    feature_ok = features["row_valid_for_combined_features"].fillna(False).astype(bool)
    feature_available_ok = features["feature_available_ts"] <= features["decision_ts"]
    label_available_ok = label_available_ts > features["decision_ts"]
    target_available = target.notna()
    row_valid = feature_ok & feature_available_ok & label_available_ok & target_available
    invalid_reason = np.full(n, "", dtype=object)
    invalid_reason[~feature_ok.to_numpy()] = "feature_row_invalid"
    invalid_reason[(feature_ok & ~feature_available_ok).to_numpy()] = "feature_available_after_decision"
    invalid_reason[(feature_ok & feature_available_ok & ~target_available).to_numpy()] = "target_unavailable"
    invalid_reason[(feature_ok & feature_available_ok & target_available & ~label_available_ok).to_numpy()] = "label_available_not_after_decision"
    target_missing = (~target_available).astype("int16")
    leakage_errors = ((~feature_available_ok) | (~label_available_ok)).astype("int16")
    feature_errors = pd.to_numeric(features["combined_feature_error_count"], errors="coerce").fillna(0).astype("int16")
    dataset_error_count = (feature_errors + target_missing + leakage_errors).astype("int16")
    dataset_null_count = (
        pd.to_numeric(features["combined_feature_null_count"], errors="coerce").fillna(0).astype("int16")
        + pd.to_numeric(labels["label_null_count"], errors="coerce").fillna(0).astype("int16")
        + target_missing
    ).astype("int16")

    out = features[
        [
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
            "combined_feature_schema_version",
            *FEATURE_COLUMNS,
            "feature_null_count",
            "feature_error_count",
            "combined_feature_null_count",
            "combined_feature_error_count",
            "warmup_row",
        ]
    ].copy()
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


def selected_h1_label_available_ts_v9_49(features: pd.DataFrame, timeframe: str) -> pd.Series:
    horizon_bars = 60 // TIMEFRAME_MINUTES[timeframe]
    return features["close_ts"].shift(-horizon_bars) + pd.Timedelta(milliseconds=1)


def split_series_v9_49(n: int) -> np.ndarray:
    train_end = int(n * SPLIT_POLICY["train_ratio"])
    validation_end = int(n * (SPLIT_POLICY["train_ratio"] + SPLIT_POLICY["validation_ratio"]))
    split = np.empty(n, dtype=object)
    split[:train_end] = "train"
    split[train_end:validation_end] = "validation"
    split[validation_end:] = "test"
    return split


def summarize_dataset_v9_49(dataset: pd.DataFrame, timeframe: str, output_path: Path) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], SELECTED_PRIMARY_LABEL]
    target_distribution = distribution_stats_v9_49(value_counts_v9_49(valid))
    leakage_feature = int((dataset["feature_available_ts"] > dataset["decision_ts"]).sum())
    leakage_label = int(((dataset["label_available_ts"] <= dataset["decision_ts"]) & dataset["row_valid_for_dataset"]).sum())
    metrics = {
        "timeframe": timeframe,
        "created": True,
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size,
        "row_count": int(len(dataset)),
        "valid_row_count": int(dataset["row_valid_for_dataset"].sum()),
        "invalid_row_count": int((~dataset["row_valid_for_dataset"]).sum()),
        "target_name": SELECTED_PRIMARY_LABEL,
        "label_distribution": target_distribution,
        "split_distribution": split_distribution_v9_49(dataset),
        "monthly_distribution": monthly_distribution_v9_49(dataset),
        "null_summary": null_summary_v9_49(dataset),
        "dataset_error_count_sum": int(dataset["dataset_error_count"].sum()),
        "feature_available_ts_gt_decision_ts": leakage_feature,
        "label_available_ts_lte_decision_ts_for_valid_rows": leakage_label,
        "forbidden_columns": sorted(set(dataset.columns) & FORBIDDEN_COLUMNS),
        "target_majority_ratio": target_distribution["majority_class_ratio"],
        "target_flat_ratio": target_distribution["flat_ratio"],
        "warmup_rows": int(dataset["warmup_row"].sum()),
        "tail_invalid_rows": int((dataset["dataset_invalid_reason"] == "target_unavailable").sum()),
        "split_monotone": split_monotone_v9_49(dataset),
        "train_before_validation_before_test": train_before_validation_before_test_v9_49(dataset),
        "warnings": [],
    }
    if metrics["target_majority_ratio"] > 0.70:
        metrics["warnings"].append(f"{timeframe}: target majority ratio above 70%")
    if metrics["target_flat_ratio"] > 0.70:
        metrics["warnings"].append(f"{timeframe}: target flat ratio above 70%")
    if not metrics["split_monotone"] or not metrics["train_before_validation_before_test"]:
        metrics["warnings"].append(f"{timeframe}: split temporal order warning")
    return metrics


def value_counts_v9_49(series: pd.Series) -> dict[str, int]:
    return {str(int(key)): int(value) for key, value in series.dropna().value_counts().sort_index().items()}


def distribution_stats_v9_49(counts: dict[str, int]) -> dict[str, Any]:
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


def split_distribution_v9_49(dataset: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for split_name, chunk in dataset.loc[dataset["row_valid_for_dataset"]].groupby("split", sort=False):
        result[str(split_name)] = distribution_stats_v9_49(value_counts_v9_49(chunk[SELECTED_PRIMARY_LABEL]))
        result[str(split_name)]["rows"] = int(len(chunk))
    return result


def monthly_distribution_v9_49(dataset: pd.DataFrame) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], ["walk_forward_group", SELECTED_PRIMARY_LABEL]]
    result: dict[str, Any] = {}
    for month, chunk in valid.groupby("walk_forward_group", sort=True):
        result[str(month)] = distribution_stats_v9_49(value_counts_v9_49(chunk[SELECTED_PRIMARY_LABEL]))
        result[str(month)]["rows"] = int(len(chunk))
    return result


def null_summary_v9_49(dataset: pd.DataFrame) -> dict[str, Any]:
    feature_nulls = {column: int(dataset[column].isna().sum()) for column in FEATURE_COLUMNS if int(dataset[column].isna().sum()) > 0}
    label_nulls = {column: int(dataset[column].isna().sum()) for column in LABEL_COLUMNS if int(dataset[column].isna().sum()) > 0}
    return {
        "feature_columns_with_nulls": feature_nulls,
        "label_columns_with_nulls": label_nulls,
        "dataset_null_count_sum": int(dataset["dataset_null_count"].sum()),
        "dataset_error_count_sum": int(dataset["dataset_error_count"].sum()),
    }


def split_monotone_v9_49(dataset: pd.DataFrame) -> bool:
    ranks = dataset["split"].map({"train": 0, "validation": 1, "test": 2}).to_numpy()
    return bool(np.all(ranks[:-1] <= ranks[1:])) if len(ranks) > 1 else True


def train_before_validation_before_test_v9_49(dataset: pd.DataFrame) -> bool:
    ranges = {}
    for split_name, chunk in dataset.groupby("split", sort=False):
        ranges[split_name] = (chunk["decision_ts"].min(), chunk["decision_ts"].max())
    required = {"train", "validation", "test"}
    if set(ranges) != required:
        return False
    return bool(ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0])


def build_leakage_guard_v9_49(metrics_by_timeframe: dict[str, Any]) -> dict[str, Any]:
    feature_violations = sum(item.get("feature_available_ts_gt_decision_ts", 0) for item in metrics_by_timeframe.values())
    label_violations = sum(item.get("label_available_ts_lte_decision_ts_for_valid_rows", 0) for item in metrics_by_timeframe.values())
    return {
        "status": "PASS" if feature_violations == 0 and label_violations == 0 else "FAIL",
        "feature_available_ts_gt_decision_ts": int(feature_violations),
        "label_available_ts_lte_decision_ts_for_valid_rows": int(label_violations),
        "no_future_leak": feature_violations == 0 and label_violations == 0,
        "no_ml": True,
        "no_backtest": True,
        "no_signal": True,
    }


def build_forbidden_scan_v9_49(metrics_by_timeframe: dict[str, Any]) -> dict[str, Any]:
    hits = sorted({column for item in metrics_by_timeframe.values() for column in item.get("forbidden_columns", [])})
    feature_hits = sorted(set(FEATURE_COLUMNS) & FORBIDDEN_COLUMNS)
    return {
        "status": "PASS" if not hits and not feature_hits else "FAIL",
        "forbidden_columns": hits,
        "forbidden_feature_columns": feature_hits,
        "diagnostic_labels_excluded_from_features": True,
    }


def quality_status_v9_49(
    dataset_created: bool,
    leakage_guard: dict[str, Any],
    forbidden_column_scan: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> str:
    if errors:
        return "FAIL"
    if leakage_guard["status"] != "PASS":
        return "FAIL_LEAKAGE"
    if forbidden_column_scan["status"] != "PASS":
        return "FAIL_FORBIDDEN_COLUMNS"
    if not dataset_created:
        return "FAIL"
    return "PASS_WITH_WARNINGS" if warnings else "PASS"


def coverage_status_v9_49(dataset_created: bool, row_counts: dict[str, int]) -> str:
    if dataset_created and row_counts == EXPECTED_ROWS:
        return "target_5y_dataset_window_complete"
    if any(row_counts.values()):
        return "target_5y_dataset_window_partial"
    return "target_5y_dataset_not_created"


def decide_v9_49(
    dataset_created: bool,
    feature_readiness: dict[str, Any],
    label_readiness: dict[str, Any],
    leakage_guard: dict[str, Any],
    quality_status: str,
    warnings: list[str],
    errors: list[str],
) -> str:
    if not feature_readiness["ready"]:
        return "combined_features_5y_dataset_blocked_by_feature_quality"
    if not label_readiness["ready"]:
        return "combined_features_5y_dataset_blocked_by_label_quality"
    if leakage_guard["status"] != "PASS":
        return "combined_features_5y_dataset_blocked_by_leakage"
    if errors and dataset_created:
        return "combined_features_5y_dataset_partial"
    if errors:
        return "combined_features_5y_dataset_blocked_by_label_quality"
    if dataset_created and quality_status == "PASS_WITH_WARNINGS":
        return "combined_features_5y_dataset_created_with_warnings"
    if dataset_created:
        return "combined_features_5y_dataset_created"
    if warnings:
        return "combined_features_5y_dataset_partial"
    return "combined_features_5y_dataset_blocked_by_label_quality"


def next_recommendation_v9_49(decision: str) -> str:
    if decision in {"combined_features_5y_dataset_created", "combined_features_5y_dataset_created_with_warnings"}:
        return "V9.50 - Combined Features 5Y Dataset Validation"
    if decision == "combined_features_5y_dataset_blocked_by_leakage":
        return "V9.50 - Combined Dataset Correction"
    if "feature" in decision or "label" in decision:
        return "V9.50 - Manual Dataset Review Pack"
    return "V9.50 - Combined Dataset Correction"


def dataset_output_path_v9_49(timeframe: str) -> Path:
    return DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "dataset.parquet"


def build_manifest_v9_49(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "datacard_path": DATACARD_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "dataset_created": report["dataset_created"],
        "target_name": report["target_name"],
        "selected_primary_label": report["selected_primary_label"],
        "row_counts": report["row_counts"],
        "valid_row_counts": report["valid_row_counts"],
        "invalid_row_counts": report["invalid_row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
        "forbidden_column_scan_status": report["forbidden_column_scan"]["status"],
        "outputs": report["outputs"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_49(report: dict[str, Any]) -> str:
    lines = [
        "# V9.49 - OHLCV + AggTrades 5Y Dataset",
        "",
        "## Resume",
        f"- Decision V9.49 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Dataset cree : `{report['dataset_created']}`.",
        f"- Target : `{report['target_name']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Leakage guard : `{report['leakage_guard']['status']}`.",
        f"- Forbidden columns scan : `{report['forbidden_column_scan']['status']}`.",
        "",
        "## Readiness",
        f"- Features combinees V9.47/V9.48 : `{report['feature_readiness']['ready']}`.",
        f"- Labels V9.40 : `{report['label_readiness']['ready']}`.",
        "",
        "## Lignes par timeframe",
    ]
    for timeframe in TIMEFRAMES:
        lines.append(
            f"- `{timeframe}` : rows `{report['row_counts'].get(timeframe)}`, valides `{report['valid_row_counts'].get(timeframe)}`, invalides `{report['invalid_row_counts'].get(timeframe)}`."
        )
    lines.extend(
        [
            "",
            "## Splits",
            "- Les splits sont inclus dans `dataset.parquet`.",
            "- Split temporel sans shuffle : train 60 %, validation 20 %, test 20 %.",
            "- `walk_forward_group = calendar_month`; `purge_embargo_group = none_v9_49_preview`.",
            "",
            "## Garde-fous",
            "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.",
            "- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.",
        ]
    )
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_49(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_49_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "dataset_created": report["dataset_created"],
        "target_name": report["target_name"],
        "row_counts": report["row_counts"],
        "valid_row_counts": report["valid_row_counts"],
        "invalid_row_counts": report["invalid_row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
        "forbidden_column_scan_status": report["forbidden_column_scan"]["status"],
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.49\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.49 : `{report['decision']}`.\n"
        f"- Dataset cree : `{report['dataset_created']}`.\n"
        f"- Target : `{report['target_name']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        f"- Couverture : `{report['coverage_status']}`.\n"
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
        f"- Candidate : {VERSION}, dataset supervise offline OHLCV + aggTrades 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
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
