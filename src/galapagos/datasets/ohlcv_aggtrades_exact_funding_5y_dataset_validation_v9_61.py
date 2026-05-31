from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas import (
    COMMON_WINDOW_LABEL,
    DATASET_BASE_PATH,
    DATASET_COLUMNS,
    FEATURE_COLUMNS,
    FORBIDDEN_COLUMNS,
    SELECTED_PRIMARY_LABEL,
    TIMEFRAMES,
)


VERSION = "V9.61"
SOURCE_VERSION = "V9.60"
DIRECTION = "ohlcv_aggtrades_exact_funding_5y_dataset_validation"
REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.md")
V9_60_REPORT_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.json")
EXPECTED_SPLITS = {"train", "validation", "test"}
ALLOWED_DECISIONS = {
    "funding_common_window_dataset_validated",
    "funding_common_window_dataset_validated_with_warnings",
    "funding_common_window_dataset_blocked_by_coverage",
    "funding_common_window_dataset_blocked_by_schema",
    "funding_common_window_dataset_blocked_by_quality",
    "funding_common_window_dataset_blocked_by_leakage",
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
    "ml_executed": False,
}


def run_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    source_report = _read_json(root / V9_60_REPORT_PATH)
    readiness_errors = []
    if source_report.get("decision") not in {"funding_common_window_dataset_created", "funding_common_window_dataset_created_with_warnings"}:
        readiness_errors.append("V9.60 dataset is not created")
    timeframe_results: dict[str, Any] = {}
    errors: list[str] = list(readiness_errors)
    warnings: list[str] = []
    if not readiness_errors:
        for timeframe in TIMEFRAMES:
            try:
                result = validate_full_timeframe_v9_61(root, timeframe)
                timeframe_results[timeframe] = result
                warnings.extend(result["warnings"])
            except Exception as exc:
                errors.append(f"{timeframe}: {exc}")
                timeframe_results[timeframe] = {"status": "FAIL", "errors": [str(exc)]}
    coverage_status = "PASS" if timeframe_results and all(item.get("row_count", 0) > 0 for item in timeframe_results.values()) and not errors else "FAIL"
    schema_status = "PASS" if timeframe_results and all(item.get("schema_status") == "PASS" for item in timeframe_results.values()) and not errors else "FAIL"
    leakage_guard = leakage_guard_v9_61(timeframe_results)
    forbidden_scan = forbidden_scan_v9_61(timeframe_results)
    quality_status = "PASS" if coverage_status == "PASS" and schema_status == "PASS" and leakage_guard["status"] == "PASS" and forbidden_scan["status"] == "PASS" and not errors else "FAIL"
    decision = decide_v9_61(coverage_status, schema_status, quality_status, leakage_guard, forbidden_scan, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_name": SELECTED_PRIMARY_LABEL,
        "timeframes": list(TIMEFRAMES),
        "source_decision": source_report.get("decision"),
        "full_local_validation": timeframe_results,
        "row_counts": collect_metric_v9_61(timeframe_results, "row_count"),
        "valid_row_counts": collect_metric_v9_61(timeframe_results, "valid_row_count"),
        "invalid_row_counts": collect_metric_v9_61(timeframe_results, "invalid_row_count"),
        "invalid_reason_summary": collect_metric_v9_61(timeframe_results, "invalid_reason_summary"),
        "null_summary": collect_metric_v9_61(timeframe_results, "null_summary"),
        "split_distribution": collect_metric_v9_61(timeframe_results, "split_distribution"),
        "target_distribution": collect_metric_v9_61(timeframe_results, "target_distribution"),
        "target_distribution_by_split": collect_metric_v9_61(timeframe_results, "target_distribution_by_split"),
        "target_distribution_by_year": collect_metric_v9_61(timeframe_results, "target_distribution_by_year"),
        "target_distribution_by_month": collect_metric_v9_61(timeframe_results, "target_distribution_by_month"),
        "majority_class_ratio": collect_metric_v9_61(timeframe_results, "majority_class_ratio"),
        "flat_ratio": collect_metric_v9_61(timeframe_results, "flat_ratio"),
        "entropy": collect_metric_v9_61(timeframe_results, "entropy"),
        "coverage_status": coverage_status,
        "schema_status": schema_status,
        "quality_status": quality_status,
        "leakage_guard_status": leakage_guard["status"],
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "decision": decision,
        "next_recommendation": "V9.62 - Funding common window ML offline" if decision in {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"} else "V9.62 - Dataset correction",
        "runtime_seconds": round(time.monotonic() - started, 3),
        "dataset_created": False,
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
        raise RuntimeError(f"invalid V9.61 decision: {report['decision']}")
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_61(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_61(report))
    return report


def validate_full_timeframe_v9_61(root: Path, timeframe: str) -> dict[str, Any]:
    path = dataset_path_v9_61(root, timeframe)
    frame = pd.read_parquet(path, engine="pyarrow")
    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = [column for column in DATASET_COLUMNS if column not in frame.columns]
    forbidden = sorted(set(frame.columns) & FORBIDDEN_COLUMNS)
    if missing_columns:
        errors.append(f"missing dataset columns: {missing_columns[:10]}")
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if set(frame["split"].dropna().unique()) != EXPECTED_SPLITS:
        errors.append("split values mismatch")
    if not split_temporal_order_v9_61(frame):
        errors.append("split temporal order failed")
    leakage = leakage_errors_v9_61(frame)
    if leakage["feature_available_ts_gt_decision_ts"] or leakage["label_available_ts_lte_decision_ts_for_valid_rows"]:
        errors.append(f"leakage errors: {leakage}")
    target_distribution = distribution_stats_v9_61(value_counts_v9_61(frame.loc[frame["row_valid_for_dataset"], SELECTED_PRIMARY_LABEL]))
    if target_distribution["flat_ratio"] > 0.70:
        warnings.append(f"{timeframe}: FLAT ratio above 70%")
    return {
        "status": "PASS" if not errors else "FAIL",
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "row_count": int(len(frame)),
        "valid_row_count": int(frame["row_valid_for_dataset"].sum()),
        "invalid_row_count": int((~frame["row_valid_for_dataset"]).sum()),
        "schema_status": "PASS" if not missing_columns and not forbidden else "FAIL",
        "missing_columns": missing_columns,
        "forbidden_columns": forbidden,
        "temporal_status": "PASS" if split_temporal_order_v9_61(frame) else "FAIL",
        "leakage_errors": leakage,
        "invalid_reason_summary": {str(key): int(value) for key, value in frame.loc[~frame["row_valid_for_dataset"], "dataset_invalid_reason"].value_counts(dropna=False).sort_index().items()},
        "null_summary": {"dataset_null_count_sum": int(frame["dataset_null_count"].sum()), "dataset_error_count_sum": int(frame["dataset_error_count"].sum())},
        "split_distribution": {str(key): int(value) for key, value in frame["split"].value_counts(sort=False).items()},
        "target_distribution": target_distribution,
        "target_distribution_by_split": target_distribution_by_split_v9_61(frame),
        "target_distribution_by_year": grouped_distribution_v9_61(frame, "%Y"),
        "target_distribution_by_month": grouped_distribution_v9_61(frame, "%Y-%m"),
        "majority_class_ratio": target_distribution["majority_class_ratio"],
        "flat_ratio": target_distribution["flat_ratio"],
        "entropy": target_distribution["entropy"],
        "errors": errors,
        "warnings": warnings,
    }


def dataset_path_v9_61(root: Path, timeframe: str) -> Path:
    return root / DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={COMMON_WINDOW_LABEL}" / "dataset.parquet"


def leakage_errors_v9_61(frame: pd.DataFrame) -> dict[str, int]:
    feature = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    label = int(((pd.to_datetime(frame["label_available_ts"], utc=True) <= pd.to_datetime(frame["decision_ts"], utc=True)) & frame["row_valid_for_dataset"]).sum())
    return {"feature_available_ts_gt_decision_ts": feature, "label_available_ts_lte_decision_ts_for_valid_rows": label}


def split_temporal_order_v9_61(frame: pd.DataFrame) -> bool:
    ranges = {split: (chunk["decision_ts"].min(), chunk["decision_ts"].max()) for split, chunk in frame.groupby("split", sort=False)}
    return set(ranges) == EXPECTED_SPLITS and bool(ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0])


def value_counts_v9_61(series: pd.Series) -> dict[str, int]:
    return {str(int(key)): int(value) for key, value in series.dropna().value_counts().sort_index().items()}


def distribution_stats_v9_61(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    ratios = {key: (value / total if total else 0.0) for key, value in counts.items()}
    entropy = -sum(ratio * math.log(ratio, 2) for ratio in ratios.values() if ratio > 0)
    return {"counts": counts, "ratios": {key: round(value, 6) for key, value in ratios.items()}, "entropy": round(entropy, 6), "majority_class_ratio": round(max(ratios.values()) if ratios else 0.0, 6), "flat_ratio": round(ratios.get("0", 0.0), 6)}


def target_distribution_by_split_v9_61(frame: pd.DataFrame) -> dict[str, Any]:
    return {str(split): distribution_stats_v9_61(value_counts_v9_61(chunk[SELECTED_PRIMARY_LABEL])) for split, chunk in frame.loc[frame["row_valid_for_dataset"]].groupby("split", sort=False)}


def grouped_distribution_v9_61(frame: pd.DataFrame, fmt: str) -> dict[str, Any]:
    valid = frame.loc[frame["row_valid_for_dataset"], ["decision_ts", SELECTED_PRIMARY_LABEL]].copy()
    valid["group"] = pd.to_datetime(valid["decision_ts"], utc=True).dt.strftime(fmt)
    return {str(group): distribution_stats_v9_61(value_counts_v9_61(chunk[SELECTED_PRIMARY_LABEL])) for group, chunk in valid.groupby("group", sort=True)}


def leakage_guard_v9_61(results: dict[str, Any]) -> dict[str, Any]:
    feature = sum(item.get("leakage_errors", {}).get("feature_available_ts_gt_decision_ts", 0) for item in results.values())
    label = sum(item.get("leakage_errors", {}).get("label_available_ts_lte_decision_ts_for_valid_rows", 0) for item in results.values())
    return {"status": "PASS" if feature == 0 and label == 0 else "FAIL", "feature_available_ts_gt_decision_ts": int(feature), "label_available_ts_lte_decision_ts_for_valid_rows": int(label)}


def forbidden_scan_v9_61(results: dict[str, Any]) -> dict[str, Any]:
    hits = sorted({column for item in results.values() for column in item.get("forbidden_columns", [])})
    feature_hits = [column for column in FEATURE_COLUMNS if column in FORBIDDEN_COLUMNS]
    return {"status": "PASS" if not hits and not feature_hits else "FAIL", "forbidden_columns": hits, "forbidden_feature_columns": feature_hits}


def collect_metric_v9_61(results: dict[str, Any], key: str) -> dict[str, Any]:
    return {timeframe: results.get(timeframe, {}).get(key) for timeframe in TIMEFRAMES}


def decide_v9_61(coverage_status: str, schema_status: str, quality_status: str, leakage_guard: dict[str, Any], forbidden_scan: dict[str, Any], warnings: list[str], errors: list[str]) -> str:
    if coverage_status != "PASS":
        return "funding_common_window_dataset_blocked_by_coverage"
    if schema_status != "PASS":
        return "funding_common_window_dataset_blocked_by_schema"
    if leakage_guard["status"] != "PASS":
        return "funding_common_window_dataset_blocked_by_leakage"
    if quality_status != "PASS" or forbidden_scan["status"] != "PASS" or errors:
        return "funding_common_window_dataset_blocked_by_quality"
    if warnings:
        return "funding_common_window_dataset_validated_with_warnings"
    return "funding_common_window_dataset_validated"


def build_manifest_v9_61(report: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "source_version": SOURCE_VERSION, "created_at_utc": report["created_at_utc"], "decision": report["decision"], "report_path": REPORT_JSON_PATH.as_posix(), "manifest_path": MANIFEST_PATH.as_posix(), "quality_status": report["quality_status"], "coverage_status": report["coverage_status"], "leakage_guard_status": report["leakage_guard_status"], "safety_flags": report["safety_flags"], "network_used": False, "new_data_downloaded": False}


def build_markdown_v9_61(report: dict[str, Any]) -> str:
    return f"# V9.61 - Validation dataset funding common window\n\n- Decision : `{report['decision']}`.\n- Target : `{report['target_name']}`.\n- Quality : `{report['quality_status']}`.\n- Leakage : `{report['leakage_guard_status']}`.\n\nAucun ML, backtest, walk-forward, strategie ou signal.\n"


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
