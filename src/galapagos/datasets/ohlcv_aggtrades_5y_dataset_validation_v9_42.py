from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_schemas import (
    DATASET_BASE_PATH,
    DATASET_COLUMNS,
    EXPECTED_ROWS,
    FEATURE_COLUMNS,
    FORBIDDEN_COLUMNS,
    SELECTED_PRIMARY_LABEL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
)


VERSION = "V9.42"
SOURCE_VERSION = "V9.41"
LAST_VALIDATED_VERSION = "V9.41"
DIRECTION = "ohlcv_aggtrades_5y_dataset_validation"
REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.md")
SAMPLES_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42_samples.json")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_dataset_validation_v9_42_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_dataset_validation_v9_42.md")
SAMPLE_BASE_PATH = Path("data/audit_samples/v9_42/ohlcv_aggtrades_5y_dataset")
EXPECTED_VALID_ROWS = {"1m": 2_630_395, "5m": 526_104, "15m": 175_328, "1h": 43_787}
EXPECTED_INVALID_ROWS = {"1m": 485, "5m": 72, "15m": 64, "1h": 61}
EXPECTED_SPLITS = {"train", "validation", "test"}
ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_5y_dataset_validated",
    "ohlcv_aggtrades_5y_dataset_validated_with_non_blocking_warnings",
    "ohlcv_aggtrades_5y_dataset_blocked_by_coverage",
    "ohlcv_aggtrades_5y_dataset_blocked_by_schema",
    "ohlcv_aggtrades_5y_dataset_blocked_by_quality",
    "ohlcv_aggtrades_5y_dataset_blocked_by_leakage",
    "ohlcv_aggtrades_5y_dataset_inconclusive_manual_review_required",
    "stop_ohlcv_aggtrades_5y_dataset_branch",
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
SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
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


def run_ohlcv_aggtrades_5y_dataset_validation_v9_42(root: Path = Path("."), mode: str = "full-local") -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = load_inputs_v9_42(root)
    readiness = assess_v9_41_readiness_v9_42(inputs)
    timeframe_results: dict[str, Any] = {}
    sample_inventory: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []

    if mode not in {"full-local", "audit-lite"}:
        raise ValueError(f"unsupported V9.42 mode: {mode}")
    if not readiness["ready"]:
        errors.extend(readiness["errors"])
    elif mode == "full-local":
        for timeframe in TIMEFRAMES:
            try:
                result = validate_full_timeframe_v9_42(root, timeframe)
                timeframe_results[timeframe] = result
                warnings.extend(result["warnings"])
                sample_inventory[timeframe] = write_sample_v9_42(root, timeframe, result["sample_rows"])
                timeframe_results[timeframe].pop("sample_rows", None)
            except Exception as exc:  # pragma: no cover - integration failure path.
                errors.append(f"{timeframe}: {exc}")
                timeframe_results[timeframe] = {"status": "FAIL", "errors": [str(exc)]}
    else:
        sample_inventory = inspect_samples_v9_42(root)
        warnings.append("audit-lite mode: full Parquet datasets are not required and were not revalidated")

    coverage_status = coverage_status_v9_42(timeframe_results, mode, errors)
    schema_status = schema_status_v9_42(timeframe_results, mode, errors)
    leakage_guard = leakage_guard_v9_42(timeframe_results, mode, errors)
    forbidden_scan = forbidden_scan_v9_42(timeframe_results, mode)
    quality_status = quality_status_v9_42(timeframe_results, mode, errors, warnings, leakage_guard, forbidden_scan)
    decision = decide_v9_42(coverage_status, schema_status, quality_status, leakage_guard, forbidden_scan, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"ohlcv_aggtrades_5y_dataset_validated", "ohlcv_aggtrades_5y_dataset_validated_with_non_blocking_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "validation_mode": mode,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "target_name": SELECTED_PRIMARY_LABEL,
        "timeframes": list(TIMEFRAMES),
        "readiness": readiness,
        "full_local_validation": timeframe_results,
        "sample_inventory": sample_inventory,
        "row_counts_by_timeframe": collect_metric_v9_42(timeframe_results, "row_count"),
        "valid_row_counts": collect_metric_v9_42(timeframe_results, "valid_row_count"),
        "invalid_row_counts": collect_metric_v9_42(timeframe_results, "invalid_row_count"),
        "invalid_reason_summary": collect_metric_v9_42(timeframe_results, "invalid_reason_summary"),
        "null_summary": collect_metric_v9_42(timeframe_results, "null_summary"),
        "feature_null_summary": collect_metric_v9_42(timeframe_results, "feature_null_summary"),
        "label_null_summary": collect_metric_v9_42(timeframe_results, "label_null_summary"),
        "split_distribution": collect_metric_v9_42(timeframe_results, "split_distribution"),
        "target_distribution": collect_metric_v9_42(timeframe_results, "target_distribution"),
        "target_distribution_by_split": collect_metric_v9_42(timeframe_results, "target_distribution_by_split"),
        "target_distribution_by_year": collect_metric_v9_42(timeframe_results, "target_distribution_by_year"),
        "target_distribution_by_month": collect_metric_v9_42(timeframe_results, "target_distribution_by_month"),
        "majority_class_ratio": collect_metric_v9_42(timeframe_results, "majority_class_ratio"),
        "flat_ratio": collect_metric_v9_42(timeframe_results, "flat_ratio"),
        "entropy": collect_metric_v9_42(timeframe_results, "entropy"),
        "coverage_status": coverage_status,
        "schema_status": schema_status,
        "quality_status": quality_status,
        "leakage_guard_status": leakage_guard["status"],
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "decision": decision,
        "next_recommendation": next_recommendation_v9_42(decision),
        "runtime_seconds": round(time.monotonic() - started, 3),
        "dataset_created": False,
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
        raise RuntimeError(f"invalid V9.42 decision: {report['decision']}")
    _write_json(root / REPORT_JSON_PATH, report)
    _write_text(root / REPORT_MD_PATH, build_markdown_v9_42(report))
    _write_text(root / DOC_PATH, build_markdown_v9_42(report))
    _write_json(root / SAMPLES_JSON_PATH, {"version": VERSION, "samples": sample_inventory})
    _write_json(root / MANIFEST_PATH, build_manifest_v9_42(report))
    update_state_surfaces_v9_42(root, report)
    return report


def validate_full_timeframe_v9_42(root: Path, timeframe: str) -> dict[str, Any]:
    path = dataset_path_v9_42(root, timeframe)
    if not path.is_file():
        raise FileNotFoundError(f"missing dataset parquet: {path}")
    frame = pd.read_parquet(path)
    errors: list[str] = []
    warnings: list[str] = []
    columns = list(frame.columns)
    missing_columns = [column for column in DATASET_COLUMNS if column not in columns]
    extra_forbidden = sorted(set(columns) & FORBIDDEN_COLUMNS)
    if missing_columns:
        errors.append(f"missing dataset columns: {missing_columns[:10]}")
    if extra_forbidden:
        errors.append(f"forbidden columns present: {extra_forbidden}")
    row_count = int(len(frame))
    valid_row_count = int(frame["row_valid_for_dataset"].fillna(False).sum()) if "row_valid_for_dataset" in frame else 0
    invalid_row_count = row_count - valid_row_count
    if row_count != EXPECTED_ROWS[timeframe]:
        errors.append(f"row_count mismatch: {row_count} != {EXPECTED_ROWS[timeframe]}")
    if valid_row_count != EXPECTED_VALID_ROWS[timeframe]:
        errors.append(f"valid_row_count mismatch: {valid_row_count} != {EXPECTED_VALID_ROWS[timeframe]}")
    if invalid_row_count != EXPECTED_INVALID_ROWS[timeframe]:
        errors.append(f"invalid_row_count mismatch: {invalid_row_count} != {EXPECTED_INVALID_ROWS[timeframe]}")
    errors.extend(validate_metadata_v9_42(frame, timeframe))
    errors.extend(validate_temporal_v9_42(frame))
    leakage_errors = leakage_errors_v9_42(frame)
    if leakage_errors["feature_available_ts_gt_decision_ts"] or leakage_errors["label_available_ts_lte_decision_ts_for_valid_rows"]:
        errors.append(f"leakage errors: {leakage_errors}")
    target_distribution = distribution_stats_v9_42(value_counts_v9_42(frame.loc[frame["row_valid_for_dataset"], SELECTED_PRIMARY_LABEL]))
    if target_distribution["flat_ratio"] > 0.70:
        warnings.append(f"{timeframe}: FLAT ratio above 70%")
    if min(target_distribution["ratios"].get("-1", 0.0), target_distribution["ratios"].get("1", 0.0)) < 0.10:
        warnings.append(f"{timeframe}: directional class below 10%")
    split_stats = target_distribution_by_split_v9_42(frame)
    if distribution_drift_warning_v9_42(split_stats):
        warnings.append(f"{timeframe}: target distribution drift between train/validation/test")
    year_stats = grouped_distribution_v9_42(frame, "%Y")
    if distribution_drift_warning_v9_42(year_stats):
        warnings.append(f"{timeframe}: target distribution drift between years")
    return {
        "status": "PASS" if not errors else "FAIL",
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "readable": True,
        "row_count": row_count,
        "valid_row_count": valid_row_count,
        "invalid_row_count": invalid_row_count,
        "schema_status": "PASS" if not missing_columns and not extra_forbidden else "FAIL",
        "missing_columns": missing_columns,
        "forbidden_columns": extra_forbidden,
        "target_name_values": sorted(map(str, frame["target_name"].dropna().unique().tolist()))[:5],
        "selected_primary_label_values": sorted(map(str, frame["selected_primary_label"].dropna().unique().tolist()))[:5],
        "source_versions": {
            "source_feature_store_version": sorted(map(str, frame["source_feature_store_version"].dropna().unique().tolist())),
            "source_feature_validation_version": sorted(map(str, frame["source_feature_validation_version"].dropna().unique().tolist())),
            "source_label_version": sorted(map(str, frame["source_label_version"].dropna().unique().tolist())),
        },
        "temporal_status": "PASS" if not validate_temporal_v9_42(frame) else "FAIL",
        "leakage_errors": leakage_errors,
        "invalid_reason_summary": {str(key): int(value) for key, value in frame.loc[~frame["row_valid_for_dataset"], "dataset_invalid_reason"].value_counts(dropna=False).sort_index().items()},
        "null_summary": null_summary_v9_42(frame),
        "feature_null_summary": {column: int(frame[column].isna().sum()) for column in FEATURE_COLUMNS if int(frame[column].isna().sum()) > 0},
        "label_null_summary": {column: int(frame[column].isna().sum()) for column in [SELECTED_PRIMARY_LABEL, "up_down_flat_volnorm_h4_5y", "binary_directional_volnorm_h4_5y"] if int(frame[column].isna().sum()) > 0},
        "split_distribution": {str(key): int(value) for key, value in frame["split"].value_counts(sort=False).items()},
        "target_distribution": target_distribution,
        "target_distribution_by_split": split_stats,
        "target_distribution_by_year": year_stats,
        "target_distribution_by_month": grouped_distribution_v9_42(frame, "%Y-%m"),
        "majority_class_ratio": target_distribution["majority_class_ratio"],
        "flat_ratio": target_distribution["flat_ratio"],
        "entropy": target_distribution["entropy"],
        "errors": errors,
        "warnings": warnings,
        "sample_rows": sample_rows_v9_42(frame),
    }


def validate_metadata_v9_42(frame: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    expected_values = {
        "timeframe": timeframe,
        "target_name": SELECTED_PRIMARY_LABEL,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "source_feature_store_version": "V9.37",
        "source_feature_validation_version": "V9.38",
        "source_label_version": "V9.40",
    }
    for column, expected in expected_values.items():
        values = set(map(str, frame[column].dropna().unique().tolist()))
        if values != {expected}:
            errors.append(f"{column} values mismatch: {sorted(values)}")
    return errors


def validate_temporal_v9_42(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if not frame["decision_ts"].is_monotonic_increasing:
        errors.append("decision_ts is not monotone increasing")
    if int(frame.duplicated("event_ts").sum()) != 0:
        errors.append("duplicate event_ts detected")
    if int(frame.duplicated("close_ts").sum()) != 0:
        errors.append("duplicate close_ts detected")
    if set(frame["split"].dropna().unique()) != EXPECTED_SPLITS:
        errors.append("split values mismatch")
    ranks = frame["split"].map({"train": 0, "validation": 1, "test": 2}).to_numpy()
    if len(ranks) > 1 and not bool((ranks[:-1] <= ranks[1:]).all()):
        errors.append("split is not monotone")
    ranges = {split: (chunk["decision_ts"].min(), chunk["decision_ts"].max()) for split, chunk in frame.groupby("split", sort=False)}
    if set(ranges) == EXPECTED_SPLITS and not (ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0]):
        errors.append("train/validation/test temporal order failed")
    if not frame["walk_forward_group"].equals(frame["decision_ts"].dt.strftime("%Y-%m")):
        errors.append("walk_forward_group is not calendar_month")
    return errors


def leakage_errors_v9_42(frame: pd.DataFrame) -> dict[str, int]:
    valid = frame["row_valid_for_dataset"].fillna(False)
    return {
        "feature_available_ts_gt_decision_ts": int((frame["feature_available_ts"] > frame["decision_ts"]).sum()),
        "label_available_ts_lte_decision_ts_for_valid_rows": int(((frame["label_available_ts"] <= frame["decision_ts"]) & valid).sum()),
    }


def value_counts_v9_42(series: pd.Series) -> dict[str, int]:
    return {str(int(key)): int(value) for key, value in series.dropna().value_counts().sort_index().items()}


def distribution_stats_v9_42(counts: dict[str, int]) -> dict[str, Any]:
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


def target_distribution_by_split_v9_42(frame: pd.DataFrame) -> dict[str, Any]:
    valid = frame.loc[frame["row_valid_for_dataset"], ["split", SELECTED_PRIMARY_LABEL]]
    return {str(key): distribution_stats_v9_42(value_counts_v9_42(chunk[SELECTED_PRIMARY_LABEL])) for key, chunk in valid.groupby("split", sort=False)}


def grouped_distribution_v9_42(frame: pd.DataFrame, fmt: str) -> dict[str, Any]:
    valid = frame.loc[frame["row_valid_for_dataset"], ["decision_ts", SELECTED_PRIMARY_LABEL]]
    group = valid["decision_ts"].dt.strftime(fmt)
    return {str(key): distribution_stats_v9_42(value_counts_v9_42(chunk[SELECTED_PRIMARY_LABEL])) for key, chunk in valid.groupby(group, sort=True)}


def distribution_drift_warning_v9_42(stats: dict[str, Any]) -> bool:
    if len(stats) < 2:
        return False
    majority = [item["majority_class_ratio"] for item in stats.values()]
    flat = [item["flat_ratio"] for item in stats.values()]
    return (max(majority) - min(majority)) > 0.20 or (max(flat) - min(flat)) > 0.25


def null_summary_v9_42(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "dataset_null_count_sum": int(frame["dataset_null_count"].sum()),
        "dataset_error_count_sum": int(frame["dataset_error_count"].sum()),
        "rows_with_any_null": int(frame.isna().any(axis=1).sum()),
    }


def sample_rows_v9_42(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "decision_ts",
        "feature_available_ts",
        "label_available_ts",
        "split",
        "walk_forward_group",
        "target_name",
        SELECTED_PRIMARY_LABEL,
        "row_valid_for_dataset",
        "dataset_invalid_reason",
    ]
    chunks = [frame.head(20), frame.loc[frame["split"] == "validation"].head(20), frame.loc[frame["split"] == "test"].head(20), frame.tail(20)]
    sample = pd.concat(chunks, ignore_index=True).drop_duplicates("event_ts").head(80)
    return sample[columns]


def write_sample_v9_42(root: Path, timeframe: str, sample: pd.DataFrame) -> dict[str, Any]:
    path = SAMPLE_BASE_PATH / f"timeframe={timeframe}" / "dataset_sample.parquet"
    full = root / path
    full.parent.mkdir(parents=True, exist_ok=True)
    sample.to_parquet(full, index=False, engine="pyarrow", compression="zstd")
    return {"path": path.as_posix(), "rows": int(len(sample)), "bytes": full.stat().st_size}


def inspect_samples_v9_42(root: Path) -> dict[str, Any]:
    samples: dict[str, Any] = {}
    for timeframe in TIMEFRAMES:
        path = root / SAMPLE_BASE_PATH / f"timeframe={timeframe}" / "dataset_sample.parquet"
        samples[timeframe] = {"path": path.relative_to(root).as_posix(), "available": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0}
    return samples


def load_inputs_v9_42(root: Path) -> dict[str, dict[str, Any]]:
    paths = {
        "v9_41_report": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json"),
        "v9_41_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_dataset_v9_41_manifest.json"),
        "v9_38_feature_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
        "v9_37_feature_store": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
        "v9_40_label_factory": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
        "latest_metrics": Path("reports/current/latest_metrics.json"),
        "project_state": Path("reports/PROJECT_STATE.json"),
    }
    return {name: load_input_v9_42(root, path) for name, path in paths.items()}


def load_input_v9_42(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"available": False, "path": path.as_posix(), "payload": {}}
    return {"available": True, "path": path.as_posix(), "payload": _read_json(full)}


def assess_v9_41_readiness_v9_42(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_41_report"].get("payload", {})
    errors: list[str] = []
    if not inputs["v9_41_report"].get("available"):
        errors.append("missing V9.41 dataset report")
    if not inputs["v9_41_manifest"].get("available"):
        errors.append("missing V9.41 manifest")
    if report.get("dataset_created") is not True:
        errors.append("V9.41 dataset_created is not true")
    if report.get("coverage_status") != "target_5y_dataset_window_complete":
        errors.append("V9.41 coverage status is not complete")
    if report.get("quality_status") != "PASS":
        errors.append("V9.41 quality status is not PASS")
    if report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("V9.41 leakage guard is not PASS")
    if report.get("forbidden_column_scan", {}).get("status") != "PASS":
        errors.append("V9.41 forbidden column scan is not PASS")
    if report.get("row_counts") != EXPECTED_ROWS:
        errors.append("V9.41 row counts mismatch")
    if report.get("valid_row_counts") != EXPECTED_VALID_ROWS:
        errors.append("V9.41 valid row counts mismatch")
    if report.get("invalid_row_counts") != EXPECTED_INVALID_ROWS:
        errors.append("V9.41 invalid row counts mismatch")
    return {"ready": not errors, "errors": errors, "v9_41_decision": report.get("decision"), "v9_41_quality_status": report.get("quality_status")}


def coverage_status_v9_42(results: dict[str, Any], mode: str, errors: list[str]) -> str:
    if mode == "audit-lite":
        return "audit_lite_report_and_samples_checked"
    if errors:
        return "target_5y_dataset_validation_failed"
    if all(results.get(tf, {}).get("row_count") == EXPECTED_ROWS[tf] for tf in TIMEFRAMES):
        return "target_5y_dataset_window_complete"
    return "target_5y_dataset_coverage_failed"


def schema_status_v9_42(results: dict[str, Any], mode: str, errors: list[str]) -> str:
    if mode == "audit-lite":
        return "audit_lite_schema_checked_from_manifest_and_samples"
    if errors:
        return "FAIL"
    return "PASS" if all(results.get(tf, {}).get("schema_status") == "PASS" for tf in TIMEFRAMES) else "FAIL"


def leakage_guard_v9_42(results: dict[str, Any], mode: str, errors: list[str]) -> dict[str, Any]:
    if mode == "audit-lite":
        return {"status": "PASS", "mode": mode, "note": "validated from V9.41 report and optional samples; full Parquets not required"}
    feature = sum(results.get(tf, {}).get("leakage_errors", {}).get("feature_available_ts_gt_decision_ts", 0) for tf in TIMEFRAMES)
    label = sum(results.get(tf, {}).get("leakage_errors", {}).get("label_available_ts_lte_decision_ts_for_valid_rows", 0) for tf in TIMEFRAMES)
    return {"status": "PASS" if feature == 0 and label == 0 and not errors else "FAIL", "feature_available_ts_gt_decision_ts": int(feature), "label_available_ts_lte_decision_ts_for_valid_rows": int(label)}


def forbidden_scan_v9_42(results: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "audit-lite":
        return {"status": "PASS", "mode": mode, "full_parquets_required": False}
    hits = sorted({col for tf in TIMEFRAMES for col in results.get(tf, {}).get("forbidden_columns", [])})
    feature_hits = sorted(set(FEATURE_COLUMNS) & FORBIDDEN_COLUMNS)
    return {"status": "PASS" if not hits and not feature_hits else "FAIL", "forbidden_columns": hits, "forbidden_feature_columns": feature_hits, "diagnostic_labels_excluded_from_features": True}


def quality_status_v9_42(results: dict[str, Any], mode: str, errors: list[str], warnings: list[str], leakage_guard: dict[str, Any], forbidden_scan: dict[str, Any]) -> str:
    if errors:
        return "FAIL"
    if leakage_guard["status"] != "PASS":
        return "FAIL_LEAKAGE"
    if forbidden_scan["status"] != "PASS":
        return "FAIL_FORBIDDEN_COLUMNS"
    if mode == "audit-lite":
        return "PASS_WITH_WARNINGS"
    if any(results.get(tf, {}).get("status") != "PASS" for tf in TIMEFRAMES):
        return "FAIL"
    return "PASS_WITH_WARNINGS" if warnings else "PASS"


def decide_v9_42(coverage: str, schema: str, quality: str, leakage_guard: dict[str, Any], forbidden_scan: dict[str, Any], warnings: list[str], errors: list[str]) -> str:
    if leakage_guard["status"] != "PASS":
        return "ohlcv_aggtrades_5y_dataset_blocked_by_leakage"
    if schema == "FAIL" or forbidden_scan["status"] != "PASS":
        return "ohlcv_aggtrades_5y_dataset_blocked_by_schema"
    if coverage == "target_5y_dataset_coverage_failed":
        return "ohlcv_aggtrades_5y_dataset_blocked_by_coverage"
    if errors or quality.startswith("FAIL"):
        return "ohlcv_aggtrades_5y_dataset_blocked_by_quality"
    if warnings or quality == "PASS_WITH_WARNINGS":
        return "ohlcv_aggtrades_5y_dataset_validated_with_non_blocking_warnings"
    return "ohlcv_aggtrades_5y_dataset_validated"


def next_recommendation_v9_42(decision: str) -> str:
    if decision in {"ohlcv_aggtrades_5y_dataset_validated", "ohlcv_aggtrades_5y_dataset_validated_with_non_blocking_warnings"}:
        return "V9.43 - OHLCV + AggTrades 5Y ML Offline"
    if decision.endswith("_leakage") or decision.endswith("_schema") or decision.endswith("_quality"):
        return "V9.43 - Dataset Correction"
    return "V9.43 - Manual Dataset Review Pack"


def collect_metric_v9_42(results: dict[str, Any], key: str) -> dict[str, Any]:
    return {timeframe: results.get(timeframe, {}).get(key) for timeframe in TIMEFRAMES}


def dataset_path_v9_42(root: Path, timeframe: str) -> Path:
    return root / DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={TARGET_WINDOW_START}_{TARGET_WINDOW_END}" / "dataset.parquet"


def build_manifest_v9_42(report: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "version",
        "source_version",
        "status",
        "direction",
        "validation_mode",
        "decision",
        "next_recommendation",
        "target_name",
        "coverage_status",
        "schema_status",
        "quality_status",
        "leakage_guard_status",
        "dataset_created",
        "ml_executed",
        "walk_forward_executed",
        "backtest_executed",
        "network_used",
        "new_data_downloaded",
        "findings",
        "safety_flags",
    ]
    payload = {key: report.get(key) for key in keys}
    payload.update({"created_at_utc": _utc_now(), "report_path": REPORT_JSON_PATH.as_posix(), "markdown_path": REPORT_MD_PATH.as_posix(), "samples_report_path": SAMPLES_JSON_PATH.as_posix()})
    return payload


def build_markdown_v9_42(report: dict[str, Any]) -> str:
    lines = [
        "# V9.42 - OHLCV + AggTrades 5Y Dataset Validation",
        "",
        "## Resume",
        f"- Mode : `{report['validation_mode']}`.",
        f"- Decision V9.42 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        f"- Schema : `{report['schema_status']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Leakage guard : `{report['leakage_guard_status']}`.",
        f"- Forbidden columns scan : `{report['forbidden_column_scan']['status']}`.",
        "",
        "## Counts",
    ]
    for timeframe in TIMEFRAMES:
        lines.append(f"- `{timeframe}` : rows `{report['row_counts_by_timeframe'].get(timeframe)}`, valides `{report['valid_row_counts'].get(timeframe)}`, invalides `{report['invalid_row_counts'].get(timeframe)}`.")
    lines.extend(
        [
            "",
            "## Audit-lite",
            "- Le mode audit-lite ne requiert pas les Parquets full.",
            "- Les petits samples auditables sont separes des datasets full.",
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


def update_state_surfaces_v9_42(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_42_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "dataset_created": False,
        "target_name": report["target_name"],
        "coverage_status": report["coverage_status"],
        "schema_status": report["schema_status"],
        "quality_status": report["quality_status"],
        "leakage_guard_status": report["leakage_guard_status"],
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
        "# Synthese courante - V9.42\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.42 : `{report['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.\n"
        "- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(root / "README.md", "# Projet Galapagos\n\n" f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n" f"- Candidate : {VERSION}, validation dataset OHLCV + aggTrades 5Y.\n" f"- Decision : {report['decision']}.\n" "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n")


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
