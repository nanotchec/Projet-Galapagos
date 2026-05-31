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

from galapagos.datasets.redesigned_label_5y_dataset_v9_65_datacard import build_dataset_datacard_v9_65
from galapagos.datasets.redesigned_label_5y_dataset_v9_65_schemas import (
    ALLOWED_DECISIONS,
    DATACARD_MD_PATH,
    DATASET_BASE_PATH,
    DATASET_COLUMNS,
    DATASET_RUN_ID_PREFIX,
    DATASET_SCHEMA_VERSION,
    DIRECTION,
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
    SOURCE_LABEL_VERSION,
    SOURCE_VERSION,
    SPLIT_POLICY,
    TIMEFRAMES,
    VERSION,
    WINDOW_LABEL,
)


SUCCESS_DECISIONS = {"redesigned_label_dataset_created", "redesigned_label_dataset_created_with_warnings"}


def run_redesigned_label_5y_dataset_v9_65(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_redesigned_label_5y_dataset_v9_65(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = markdown_v9_65(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DATACARD_MD_PATH, build_dataset_datacard_v9_65(report))
    _write_json(root / MANIFEST_PATH, manifest_v9_65(report))
    return report


def build_redesigned_label_5y_dataset_v9_65(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    readiness = assess_readiness_v9_65(inputs)
    dataset_run_id = f"{DATASET_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    outputs: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    if readiness["ready"]:
        with ProcessPoolExecutor(max_workers=min(4, len(TIMEFRAMES))) as executor:
            futures = {executor.submit(create_timeframe_dataset_v9_65, root, timeframe, dataset_run_id): timeframe for timeframe in TIMEFRAMES}
            for future in as_completed(futures):
                timeframe = futures[future]
                try:
                    result = future.result()
                    outputs[timeframe] = result["output"]
                    metrics[timeframe] = result["metrics"]
                    warnings.extend(result["metrics"].get("warnings", []))
                    print(f"[V9.65] timeframe_done={timeframe} rows={result['metrics']['row_count']}", flush=True)
                except Exception as exc:  # pragma: no cover
                    outputs[timeframe] = {"created": False, "error": str(exc)}
                    errors.append(f"{timeframe}: {type(exc).__name__}: {exc}")
    else:
        errors.extend(readiness["errors"])
    dataset_created = bool(metrics) and not errors and all(block.get("created") is True for block in outputs.values())
    leakage_guard = build_leakage_guard_v9_65(metrics)
    forbidden_scan = build_forbidden_scan_v9_65(metrics)
    quality_status = "PASS" if dataset_created and leakage_guard["status"] == "PASS" and forbidden_scan["status"] == "PASS" and not errors else "FAIL"
    decision = decide_v9_65(dataset_created, leakage_guard, forbidden_scan, quality_status, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "label": WINDOW_LABEL},
        "timeframes": list(TIMEFRAMES),
        "source_readiness": readiness,
        "dataset_design": {
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "dataset_run_id": dataset_run_id,
            "target_name": SELECTED_PRIMARY_LABEL,
            "selected_primary_label": SELECTED_PRIMARY_LABEL,
            "features_source": "V9.47 OHLCV + aggTrades exact",
            "funding_features_included": False,
            "split_policy": SPLIT_POLICY,
            "feature_columns_count": len(FEATURE_COLUMNS),
        },
        "dataset_created": dataset_created,
        "outputs": outputs,
        "target_name": SELECTED_PRIMARY_LABEL,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "row_counts": {timeframe: metrics.get(timeframe, {}).get("row_count", 0) for timeframe in TIMEFRAMES},
        "valid_row_counts": {timeframe: metrics.get(timeframe, {}).get("valid_row_count", 0) for timeframe in TIMEFRAMES},
        "invalid_row_counts": {timeframe: metrics.get(timeframe, {}).get("invalid_row_count", 0) for timeframe in TIMEFRAMES},
        "label_distribution": {timeframe: metrics.get(timeframe, {}).get("label_distribution", {}) for timeframe in TIMEFRAMES},
        "split_distribution": {timeframe: metrics.get(timeframe, {}).get("split_distribution", {}) for timeframe in TIMEFRAMES},
        "monthly_distribution": {timeframe: metrics.get(timeframe, {}).get("monthly_distribution", {}) for timeframe in TIMEFRAMES},
        "invalid_reason_summary": {timeframe: metrics.get(timeframe, {}).get("invalid_reason_summary", {}) for timeframe in TIMEFRAMES},
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "quality_status": quality_status,
        "coverage_status": "redesigned_label_dataset_complete" if dataset_created else "redesigned_label_dataset_incomplete",
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "decision": decision,
        "next_recommendation": "V9.66 - ML offline label redesign" if decision in SUCCESS_DECISIONS else "V9.66 - Dataset correction",
        "limitations": [
            "V9.65 cree un dataset supervise offline mais n'execute aucun ML.",
            "Le split est temporel 60/20/20 sans walk-forward.",
            "Aucun funding n'est inclus afin de conserver la fenetre 5Y exacte.",
        ],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.65 decision: {report['decision']}")
    return report


def assess_readiness_v9_65(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    labels = inputs["v9_64_label_factory"]["payload"]
    if labels.get("decision") not in {"redesigned_labels_created", "redesigned_labels_created_with_warnings"}:
        errors.append("V9.64 label factory is not successful")
    if labels.get("selected_primary_label") != SELECTED_PRIMARY_LABEL:
        errors.append("V9.64 selected label mismatch")
    if labels.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("V9.64 label leakage guard is not PASS")
    return {"ready": not errors, "errors": errors, "v9_64_decision": labels.get("decision"), "selected_primary_label": labels.get("selected_primary_label")}


def create_timeframe_dataset_v9_65(root: Path, timeframe: str, dataset_run_id: str) -> dict[str, Any]:
    feature_path = root / FEATURE_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "features.parquet"
    label_path = root / LABEL_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "labels.parquet"
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
        "label_valid",
        "label_invalid_reason",
        "label_null_count",
        "label_error_count",
    ]
    features = pd.read_parquet(feature_path, columns=feature_columns, engine="pyarrow")
    labels = pd.read_parquet(label_path, columns=label_columns, engine="pyarrow")
    validate_alignment_v9_65(features, labels, timeframe)
    dataset = assemble_dataset_frame_v9_65(features, labels, dataset_run_id)
    output_path = root / dataset_output_path_v9_65(timeframe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    return {
        "output": {"created": True, "path": dataset_output_path_v9_65(timeframe).as_posix(), "bytes": output_path.stat().st_size, "rows": int(len(dataset))},
        "metrics": summarize_dataset_v9_65(dataset, timeframe, output_path),
    }


def validate_alignment_v9_65(features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> None:
    if len(features) != len(labels):
        raise ValueError(f"{timeframe}: feature/label row count mismatch {len(features)} != {len(labels)}")
    for column in ["symbol", "timeframe", "event_ts"]:
        if not features[column].reset_index(drop=True).equals(labels[column].reset_index(drop=True)):
            raise ValueError(f"{timeframe}: feature/label alignment mismatch on {column}")


def assemble_dataset_frame_v9_65(features: pd.DataFrame, labels: pd.DataFrame, dataset_run_id: str) -> pd.DataFrame:
    n = len(features)
    split = split_series_v9_65(n)
    target = labels[SELECTED_PRIMARY_LABEL]
    feature_ok = features["row_valid_for_combined_features"].fillna(False).astype(bool)
    label_ok = labels["label_valid"].fillna(False).astype(bool) & target.notna()
    feature_available_ok = pd.to_datetime(features["feature_available_ts"], utc=True) <= pd.to_datetime(features["decision_ts"], utc=True)
    label_available_ok = pd.to_datetime(labels["label_available_ts"], utc=True) > pd.to_datetime(features["decision_ts"], utc=True)
    row_valid = feature_ok & label_ok & feature_available_ok & label_available_ok
    invalid_reason = np.full(n, "", dtype=object)
    invalid_reason[~feature_ok.to_numpy()] = "feature_row_invalid"
    invalid_reason[(feature_ok & ~feature_available_ok).to_numpy()] = "feature_available_after_decision"
    invalid_reason[(feature_ok & feature_available_ok & ~label_ok).to_numpy()] = "target_unavailable_or_invalid"
    invalid_reason[(feature_ok & feature_available_ok & label_ok & ~label_available_ok).to_numpy()] = "label_available_not_after_decision"
    feature_errors = pd.to_numeric(features["combined_feature_error_count"], errors="coerce").fillna(0).astype("int16")
    label_errors = pd.to_numeric(labels["label_error_count"], errors="coerce").fillna(0).astype("int16")
    target_missing = (~target.notna()).astype("int16")
    leakage_errors = ((~feature_available_ok) | (~label_available_ok)).astype("int16")
    out = features[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "open_ts", "close_ts", "decision_ts", "available_ts", "feature_available_ts", "combined_feature_schema_version", *FEATURE_COLUMNS, *FEATURE_AUDIT_COLUMNS]].copy()
    out["label_available_ts"] = labels["label_available_ts"]
    out["split"] = split
    out["walk_forward_group"] = pd.to_datetime(out["decision_ts"], utc=True).dt.strftime("%Y-%m")
    out["dataset_run_id"] = dataset_run_id
    out["dataset_schema_version"] = DATASET_SCHEMA_VERSION
    out["label_schema_version"] = labels["label_schema_version"]
    out["source_feature_store_version"] = SOURCE_FEATURE_STORE_VERSION
    out["source_label_version"] = SOURCE_LABEL_VERSION
    out["target_name"] = SELECTED_PRIMARY_LABEL
    out["selected_primary_label"] = SELECTED_PRIMARY_LABEL
    for column in LABEL_COLUMNS:
        out[column] = labels[column]
    out["label_valid"] = labels["label_valid"]
    out["label_invalid_reason"] = labels["label_invalid_reason"]
    out["row_valid_for_dataset"] = row_valid
    out["dataset_null_count"] = (pd.to_numeric(features["combined_feature_null_count"], errors="coerce").fillna(0).astype("int16") + pd.to_numeric(labels["label_null_count"], errors="coerce").fillna(0).astype("int16") + target_missing).astype("int16")
    out["dataset_error_count"] = (feature_errors + label_errors + target_missing + leakage_errors).astype("int16")
    out["dataset_invalid_reason"] = invalid_reason
    out["label_null_count"] = labels["label_null_count"]
    out["label_error_count"] = labels["label_error_count"]
    return out[DATASET_COLUMNS]


def split_series_v9_65(n: int) -> np.ndarray:
    split = np.empty(n, dtype=object)
    train_end = int(n * SPLIT_POLICY["train_ratio"])
    validation_end = int(n * (SPLIT_POLICY["train_ratio"] + SPLIT_POLICY["validation_ratio"]))
    split[:train_end] = "train"
    split[train_end:validation_end] = "validation"
    split[validation_end:] = "test"
    return split


def summarize_dataset_v9_65(dataset: pd.DataFrame, timeframe: str, output_path: Path) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], SELECTED_PRIMARY_LABEL]
    target_distribution = distribution_stats_v9_65(value_counts_v9_65(valid))
    invalid_reason_summary = {str(k): int(v) for k, v in dataset.loc[~dataset["row_valid_for_dataset"], "dataset_invalid_reason"].value_counts().sort_index().items()}
    warnings = [f"{timeframe}: invalid rows retained for audit"] if invalid_reason_summary else []
    return {
        "timeframe": timeframe,
        "created": True,
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size,
        "row_count": int(len(dataset)),
        "valid_row_count": int(dataset["row_valid_for_dataset"].sum()),
        "invalid_row_count": int((~dataset["row_valid_for_dataset"]).sum()),
        "label_distribution": target_distribution,
        "split_distribution": split_distribution_v9_65(dataset),
        "monthly_distribution": monthly_distribution_v9_65(dataset),
        "invalid_reason_summary": invalid_reason_summary,
        "feature_available_ts_gt_decision_ts": int((dataset["feature_available_ts"] > dataset["decision_ts"]).sum()),
        "label_available_ts_lte_decision_ts_for_valid_rows": int(((dataset["label_available_ts"] <= dataset["decision_ts"]) & dataset["row_valid_for_dataset"]).sum()),
        "forbidden_columns": sorted(set(dataset.columns) & FORBIDDEN_COLUMNS),
        "split_monotone": split_monotone_v9_65(dataset),
        "train_before_validation_before_test": train_before_validation_before_test_v9_65(dataset),
        "warnings": warnings,
    }


def value_counts_v9_65(series: pd.Series) -> dict[str, int]:
    return {str(int(key)): int(value) for key, value in series.dropna().value_counts().sort_index().items()}


def distribution_stats_v9_65(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    ratios = {key: value / total for key, value in counts.items()} if total else {}
    entropy = -sum(ratio * math.log(ratio, 2) for ratio in ratios.values() if ratio > 0)
    return {"counts": counts, "ratios": {key: round(value, 6) for key, value in ratios.items()}, "entropy": round(entropy, 6), "majority_class_ratio": round(max(ratios.values()) if ratios else 0.0, 6), "flat_ratio": round(ratios.get("0", 0.0), 6)}


def split_distribution_v9_65(dataset: pd.DataFrame) -> dict[str, Any]:
    return {str(split): {"rows": int(len(chunk)), **distribution_stats_v9_65(value_counts_v9_65(chunk[SELECTED_PRIMARY_LABEL]))} for split, chunk in dataset.loc[dataset["row_valid_for_dataset"]].groupby("split", sort=False)}


def monthly_distribution_v9_65(dataset: pd.DataFrame) -> dict[str, Any]:
    valid = dataset.loc[dataset["row_valid_for_dataset"], ["walk_forward_group", SELECTED_PRIMARY_LABEL]]
    return {str(month): {"rows": int(len(chunk)), **distribution_stats_v9_65(value_counts_v9_65(chunk[SELECTED_PRIMARY_LABEL]))} for month, chunk in valid.groupby("walk_forward_group", sort=True)}


def split_monotone_v9_65(dataset: pd.DataFrame) -> bool:
    ranks = dataset["split"].map({"train": 0, "validation": 1, "test": 2}).to_numpy()
    return bool(np.all(ranks[:-1] <= ranks[1:])) if len(ranks) > 1 else True


def train_before_validation_before_test_v9_65(dataset: pd.DataFrame) -> bool:
    ranges = {split: (chunk["decision_ts"].min(), chunk["decision_ts"].max()) for split, chunk in dataset.groupby("split", sort=False)}
    return set(ranges) == {"train", "validation", "test"} and bool(ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0])


def build_leakage_guard_v9_65(metrics: dict[str, Any]) -> dict[str, Any]:
    feature_violations = sum(item.get("feature_available_ts_gt_decision_ts", 0) for item in metrics.values())
    label_violations = sum(item.get("label_available_ts_lte_decision_ts_for_valid_rows", 0) for item in metrics.values())
    return {"status": "PASS" if feature_violations == 0 and label_violations == 0 else "FAIL", "feature_available_ts_gt_decision_ts": int(feature_violations), "label_available_ts_lte_decision_ts_for_valid_rows": int(label_violations), "no_future_leak": feature_violations == 0 and label_violations == 0}


def build_forbidden_scan_v9_65(metrics: dict[str, Any]) -> dict[str, Any]:
    hits = sorted({column for item in metrics.values() for column in item.get("forbidden_columns", [])})
    return {"status": "PASS" if not hits else "FAIL", "forbidden_columns": hits}


def decide_v9_65(dataset_created: bool, leakage_guard: dict[str, Any], forbidden_scan: dict[str, Any], quality_status: str, warnings: list[str], errors: list[str]) -> str:
    if leakage_guard["status"] != "PASS":
        return "redesigned_label_dataset_blocked_by_leakage"
    if forbidden_scan["status"] != "PASS" or errors:
        return "redesigned_label_dataset_blocked_by_quality"
    if quality_status != "PASS":
        return "redesigned_label_dataset_partial"
    return "redesigned_label_dataset_created_with_warnings" if warnings else "redesigned_label_dataset_created"


def dataset_output_path_v9_65(timeframe: str) -> Path:
    return DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "dataset.parquet"


def manifest_v9_65(report: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "source_version": SOURCE_VERSION, "created_at_utc": report["created_at_utc"], "decision": report["decision"], "report_path": REPORT_JSON_PATH.as_posix(), "datacard_path": DATACARD_MD_PATH.as_posix(), "outputs": report["outputs"], "target_name": report["target_name"], "quality_status": report["quality_status"], "leakage_guard": report["leakage_guard"], "findings": report["findings"], "safety_flags": report["safety_flags"]}


def markdown_v9_65(report: dict[str, Any]) -> str:
    return f"# V9.65 - Dataset label redesign 5Y\n\n- Decision : `{report['decision']}`.\n- Target : `{report['target_name']}`.\n- Dataset cree : `{report['dataset_created']}`.\n- Qualite : `{report['quality_status']}`.\n- Leakage guard : `{report['leakage_guard']['status']}`.\n\nAucun ML, backtest, walk-forward, strategie ou signal.\n"


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
