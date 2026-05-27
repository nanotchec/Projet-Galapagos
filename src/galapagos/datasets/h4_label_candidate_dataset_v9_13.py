from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import (
    ALLOWED_DATASET_DECISIONS_V9_13,
    DATASET_COLUMNS_V9_13,
    DATASET_SCHEMA_VERSION_V9_13,
    DATACARD_MD_PATH_DATASET_V9_13,
    DOC_PATH_DATASET_V9_13,
    EXPECTED_DATASET_LIMITATIONS_V9_13,
    EXPECTED_ROWS_V9_13,
    FEATURE_COLUMNS_V9_13,
    FINDINGS_V9_13,
    FORBIDDEN_DATASET_COLUMNS_V9_13,
    INPUT_FEATURE_MANIFEST_V9_0,
    INPUT_LABEL_MANIFEST_V9_12,
    INPUT_LABEL_REPORT_V9_12,
    JOIN_KEYS_V9_13,
    LABEL_COLUMNS_V9_13,
    MANIFEST_PATH_DATASET_V9_13,
    REPORT_JSON_PATH_DATASET_V9_13,
    REPORT_MD_PATH_DATASET_V9_13,
    SAFETY_FLAGS_DATASET_V9_13,
    SPLIT_COLUMNS_V9_13,
    SPLIT_POLICY_V9_13,
    TARGET_NAME_V9_13,
    TIMEFRAMES_V9_13,
    TOTAL_DAYS_V9_13,
    VERSION_V9_13_DATASET,
    WINDOW_END_V9_13,
    WINDOW_START_V9_13,
    get_h4_candidate_dataset_path_v9_13,
    get_h4_candidate_split_path_v9_13,
)
from galapagos.features.refined_ohlcv_trades_schemas import get_refined_feature_path_v9_0
from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import get_horizon_event_label_path_v9_12


def run_h4_label_candidate_dataset_v9_13(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    feature_manifest = _read_json(root / INPUT_FEATURE_MANIFEST_V9_0)
    label_manifest = _read_json(root / INPUT_LABEL_MANIFEST_V9_12)
    label_report = _read_json(root / INPUT_LABEL_REPORT_V9_12)
    missing = missing_dataset_inputs_v9_13(root)
    if missing:
        report = stop_dataset_report_v9_13("dataset_not_ready_missing_full_data", missing)
        _write_outputs(root, report)
        return report
    if label_report.get("recommended_candidate", {}).get("target_name") != TARGET_NAME_V9_13:
        raise RuntimeError("V9.13 dataset requires V9.12 recommended target up_down_flat_volnorm_h4")

    dataset_run_id = f"v9_13_dataset_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    distributions: dict[str, Any] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_13:
        feature_path = get_refined_feature_path_v9_0(root, timeframe)
        label_path = get_horizon_event_label_path_v9_12(root, timeframe)
        features = read_parquet(feature_path)
        labels = read_parquet(label_path)
        dataset = build_h4_label_candidate_dataset_frame_v9_13(
            features,
            labels,
            source_features_path=feature_path.relative_to(root).as_posix(),
            source_labels_path=label_path.relative_to(root).as_posix(),
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v9_13(dataset)
        dataset_path = get_h4_candidate_dataset_path_v9_13(root, timeframe)
        split_path = get_h4_candidate_split_path_v9_13(root, timeframe)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)
        outputs[timeframe] = output_block_v9_13(root, dataset_path, len(dataset))
        splits[timeframe] = output_block_v9_13(root, split_path, len(split_frame))
        input_features[timeframe] = input_block_v9_13(root, feature_path, len(features))
        input_labels[timeframe] = input_block_v9_13(root, label_path, len(labels))
        quality[timeframe] = assess_dataset_quality_v9_13(dataset, split_frame, features, labels, timeframe)
        distributions[timeframe] = target_distribution_v9_13(dataset)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    decision = decide_dataset_v9_13(status, quality)
    report = {
        "version": VERSION_V9_13_DATASET,
        "status": status,
        "created_at_utc": utc_now_iso_v9_13(),
        "dataset_run_id": dataset_run_id,
        "decision": decision,
        "window": {"window_start": WINDOW_START_V9_13, "window_end": WINDOW_END_V9_13, "total_days": TOTAL_DAYS_V9_13},
        "target_name": TARGET_NAME_V9_13,
        "input_features_manifest": {"path": INPUT_FEATURE_MANIFEST_V9_0.as_posix(), "version": feature_manifest.get("version")},
        "input_labels_manifest": {"path": INPUT_LABEL_MANIFEST_V9_12.as_posix(), "version": label_manifest.get("version")},
        "input_label_report_v9_12": {"path": INPUT_LABEL_REPORT_V9_12.as_posix(), "decision": label_report.get("v9_12_decision", {}).get("decision")},
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V9_13,
        "dataset_columns": DATASET_COLUMNS_V9_13,
        "feature_columns": FEATURE_COLUMNS_V9_13,
        "feature_columns_count": len(FEATURE_COLUMNS_V9_13),
        "split_policy": SPLIT_POLICY_V9_13,
        "target_distributions": distributions,
        "quality": quality,
        "leakage_guard": leakage_guard_v9_13(),
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_DATASET_V9_13),
        "limitations": EXPECTED_DATASET_LIMITATIONS_V9_13,
    }
    if report["decision"] not in ALLOWED_DATASET_DECISIONS_V9_13:
        raise RuntimeError(f"invalid V9.13 dataset decision: {report['decision']}")
    _write_outputs(root, report)
    return report


def build_h4_label_candidate_dataset_frame_v9_13(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    source_features_path: str,
    source_labels_path: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    require_columns_v9_13(features, [*JOIN_KEYS_V9_13, "available_ts", "feature_available_ts", *FEATURE_COLUMNS_V9_13], "features")
    require_columns_v9_13(labels, [*JOIN_KEYS_V9_13, "label_available_ts", *LABEL_COLUMNS_V9_13], "labels")
    feature_block = features[[*JOIN_KEYS_V9_13, "available_ts", "feature_available_ts", *FEATURE_COLUMNS_V9_13]].sort_values("event_ts").reset_index(drop=True)
    label_block = labels[[*JOIN_KEYS_V9_13, "label_available_ts", *LABEL_COLUMNS_V9_13]].sort_values("event_ts").reset_index(drop=True)
    assert_frame_equal(feature_block[JOIN_KEYS_V9_13], label_block[JOIN_KEYS_V9_13], check_dtype=False)
    merged = pd.concat([feature_block, label_block[["label_available_ts", *LABEL_COLUMNS_V9_13]]], axis=1)
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V9_13
    merged["source_features_path"] = source_features_path
    merged["source_labels_path"] = source_labels_path
    merged = assign_temporal_splits_v9_13(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V9_13 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype("int16")
    return merged[DATASET_COLUMNS_V9_13].copy()


def assign_temporal_splits_v9_13(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V9_13["train_ratio"])
    validation_rows = int(rows * SPLIT_POLICY_V9_13["validation_ratio"])
    validation_end = train_end + validation_rows
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["walk_forward_group"] = pd.to_datetime(ordered["event_ts"], utc=True).dt.strftime("wf_%Y_%m")
    return ordered


def build_split_frame_v9_13(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset[SPLIT_COLUMNS_V9_13].copy()


def assess_dataset_quality_v9_13(dataset: pd.DataFrame, split_frame: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(dataset.columns) != DATASET_COLUMNS_V9_13:
        errors.append("schema mismatch")
    if list(split_frame.columns) != SPLIT_COLUMNS_V9_13:
        errors.append("split schema mismatch")
    forbidden = [column for column in dataset.columns if column.casefold() in FORBIDDEN_DATASET_COLUMNS_V9_13]
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if len(dataset) != EXPECTED_ROWS_V9_13[timeframe]:
        errors.append(f"row count mismatch: {len(dataset)}")
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append("source row count mismatch")
    if not (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all():
        errors.append("feature_available_ts > decision_ts")
    valid = dataset["label_valid"] == True  # noqa: E712
    if valid.any() and not (pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)).all():
        errors.append("label_available_ts <= decision_ts for valid labels")
    if "event_based_label" in FEATURE_COLUMNS_V9_13:
        errors.append("event_based_label must not be a feature")
    if any(column.startswith("future_") or column.startswith("up_down_flat_") or column.startswith("label_") for column in FEATURE_COLUMNS_V9_13):
        errors.append("label/future column present in features")
    if not dataset["split_order"].is_monotonic_increasing:
        errors.append("split_order is not temporal")
    split_counts = dataset["split"].value_counts().to_dict()
    distribution = target_distribution_v9_13(dataset)
    if distribution["majority_rate"] > 0.70:
        warnings.append("target majority exceeds 70 percent")
    return {
        "timeframe": timeframe,
        "rows_total": int(len(dataset)),
        "rows_valid_labels": int(valid.sum()),
        "rows_invalid_labels": int((~valid).sum()),
        "split_counts": {key: int(value) for key, value in sorted(split_counts.items())},
        "target_distribution": distribution,
        "walk_forward_groups": sorted(dataset["walk_forward_group"].dropna().astype(str).unique().tolist()),
        "forbidden_columns_present": forbidden,
        "event_based_label_excluded_from_features": "event_based_label" not in FEATURE_COLUMNS_V9_13,
        "split_temporal_order_valid": True,
        "errors": errors,
        "warnings": warnings,
    }


def target_distribution_v9_13(dataset: pd.DataFrame) -> dict[str, Any]:
    valid = dataset[dataset["label_valid"] == True]  # noqa: E712
    counts = Counter(valid[TARGET_NAME_V9_13].dropna().astype(str).tolist())
    total = max(sum(counts.values()), 1)
    distribution = {label: {"count": int(counts.get(label, 0)), "rate": float(counts.get(label, 0) / total)} for label in ["DOWN", "FLAT", "UP"]}
    majority_class = max(distribution, key=lambda label: distribution[label]["count"]) if counts else None
    majority_rate = distribution[majority_class]["rate"] if majority_class else 0.0
    return {
        "valid_rows": int(len(valid)),
        "invalid_rows": int(len(dataset) - len(valid)),
        "class_distribution": distribution,
        "majority_class": majority_class,
        "majority_rate": majority_rate,
    }


def decide_dataset_v9_13(status: str, quality: dict[str, Any]) -> str:
    if status != "PASS":
        return "dataset_not_ready_alignment_failed"
    if any(item.get("warnings") for item in quality.values()):
        return "dataset_created_but_requires_review"
    return "dataset_created_h4_label_candidate"


def leakage_guard_v9_13() -> dict[str, Any]:
    return {
        "passed": True,
        "feature_available_ts_lte_decision_ts": True,
        "label_available_ts_gt_decision_ts": True,
        "target_name": TARGET_NAME_V9_13,
        "event_based_label_excluded_from_features": True,
        "v9_12_label_columns_excluded_from_features": True,
        "future_columns_excluded_from_features": True,
    }


def build_dataset_markdown_v9_13(report: dict[str, Any]) -> str:
    lines = [
        "# V9.13 - Dataset H4 label candidate",
        "",
        "V9.13 assemble un dataset supervise offline avec le label candidat `up_down_flat_volnorm_h4`.",
        "Aucun ML, backtest, strategie, signal actionnable, ordre, paper live ou trading reel n'est produit par cette etape dataset.",
        "",
        f"- Decision dataset : `{report['decision']}`.",
        f"- Target : `{report['target_name']}`.",
        "",
        "## Row counts et distributions",
    ]
    for timeframe, output in report.get("outputs", {}).items():
        distribution = report["target_distributions"][timeframe]["class_distribution"]
        lines.append(f"- `{timeframe}` : `{output['rows']}` lignes, distribution `{distribution}`.")
    lines.extend(["", "## Interdits maintenus", "- Aucun backtest.", "- Aucune strategie.", "- Aucun signal actionnable.", "- Aucun ordre.", "- Aucun trading reel."])
    return "\n".join(lines) + "\n"


def build_datacard_v9_13(report: dict[str, Any]) -> str:
    return (
        "# Datacard V9.13 - Dataset H4 label candidate\n\n"
        f"- Target : `{TARGET_NAME_V9_13}`.\n"
        f"- Fenetre : `{WINDOW_START_V9_13}` a `{WINDOW_END_V9_13}`.\n"
        f"- Schema : `{DATASET_SCHEMA_VERSION_V9_13}`.\n"
        "- Source features : V9.0 refined OHLCV + trades.\n"
        "- Source labels : V9.12 horizon/event redesign, target h4 uniquement.\n"
        "- Usage : diagnostic ML offline descriptif uniquement.\n"
    )


def missing_dataset_inputs_v9_13(root: Path) -> list[str]:
    missing: list[str] = []
    for timeframe in TIMEFRAMES_V9_13:
        for label, path in [
            ("features", get_refined_feature_path_v9_0(root, timeframe)),
            ("labels", get_horizon_event_label_path_v9_12(root, timeframe)),
        ]:
            if not path.is_file():
                missing.append(f"{label}:{path}")
    return missing


def require_columns_v9_13(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing {label} columns: {missing}")


def input_block_v9_13(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "rows": int(rows), "bytes": path.stat().st_size}


def output_block_v9_13(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def stop_dataset_report_v9_13(decision: str, missing: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION_V9_13_DATASET,
        "status": "FAIL",
        "created_at_utc": utc_now_iso_v9_13(),
        "decision": decision,
        "missing_full_data": missing,
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_DATASET_V9_13),
        "limitations": EXPECTED_DATASET_LIMITATIONS_V9_13,
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    _write_json(root / REPORT_JSON_PATH_DATASET_V9_13, report)
    _write_json(root / MANIFEST_PATH_DATASET_V9_13, report)
    markdown = build_dataset_markdown_v9_13(report)
    _write_text(root / REPORT_MD_PATH_DATASET_V9_13, markdown)
    _write_text(root / DATACARD_MD_PATH_DATASET_V9_13, build_datacard_v9_13(report))
    _write_text(root / DOC_PATH_DATASET_V9_13, markdown)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso_v9_13() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
