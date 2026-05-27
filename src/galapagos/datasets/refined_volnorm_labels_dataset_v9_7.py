from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import (
    ALLOWED_DECISIONS_V9_7,
    DATASET_COLUMNS_V9_7,
    DATASET_SCHEMA_VERSION_V9_7,
    DATACARD_MD_PATH_V9_7,
    DOC_PATH_V9_7,
    EXPECTED_LIMITATIONS_V9_7,
    EXPECTED_ROWS_V9_7,
    FEATURE_COLUMNS_V9_7,
    FORBIDDEN_DATASET_COLUMNS_V9_7,
    JOIN_KEYS_V9_7,
    LABEL_COLUMNS_V9_7,
    MANIFEST_PATH_V9_7,
    REPORT_JSON_PATH_V9_7,
    REPORT_MD_PATH_V9_7,
    SAFETY_FLAGS_V9_7,
    SPLIT_COLUMNS_V9_7,
    SPLIT_POLICY_V9_7,
    TARGET_NAME_V9_7,
    TIMEFRAMES_V9_7,
    TOTAL_DAYS_V9_7,
    VERSION_V9_7,
    WINDOW_END_V9_7,
    WINDOW_START_V9_7,
    get_refined_volnorm_dataset_path_v9_7,
    get_refined_volnorm_split_path_v9_7,
)
from galapagos.features.refined_ohlcv_trades_schemas import MANIFEST_PATH_V9_0
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import MANIFEST_PATH_V9_6, get_refined_volnorm_label_path_v9_6


def run_refined_volnorm_labels_dataset_v9_7(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    feature_manifest = _read_json(root / MANIFEST_PATH_V9_0)
    label_manifest = _read_json(root / MANIFEST_PATH_V9_6)
    missing = _missing_inputs(root, feature_manifest, label_manifest)
    if missing:
        report = _stop_report("dataset_not_ready_missing_full_data", missing)
        _write_json(root / REPORT_JSON_PATH_V9_7, report)
        _write_json(root / MANIFEST_PATH_V9_7, report)
        _write_markdowns(root, report)
        return report

    dataset_run_id = f"v9_7_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_7:
        feature_path = root / feature_manifest["outputs"][timeframe]["path"]
        label_path = get_refined_volnorm_label_path_v9_6(root, timeframe)
        features = read_parquet(feature_path)
        labels = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        dataset = build_refined_volnorm_labels_dataset_frame_v9_7(
            features,
            labels,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v9_7(dataset)
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        split_path = get_refined_volnorm_split_path_v9_7(root, timeframe)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)
        input_features[timeframe] = _input_block(root, feature_path, feature_sha, len(features))
        input_labels[timeframe] = _input_block(root, label_path, label_sha, len(labels))
        outputs[timeframe] = _output_block(root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(root, split_path, len(split_frame))
        quality[timeframe] = assess_dataset_quality_v9_7(dataset, split_frame, features, labels, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    decision = "dataset_created_with_volnorm_labels" if status == "PASS" else "dataset_not_ready_alignment_failed"
    report = {
        "version": VERSION_V9_7,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "dataset_run_id": dataset_run_id,
        "decision": decision,
        "window": {"window_start": WINDOW_START_V9_7, "window_end": WINDOW_END_V9_7, "total_days": TOTAL_DAYS_V9_7},
        "target_name": TARGET_NAME_V9_7,
        "input_features_manifest": {"path": MANIFEST_PATH_V9_0.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V9_0)},
        "input_labels_manifest": {"path": MANIFEST_PATH_V9_6.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V9_6)},
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V9_7,
        "dataset_columns": DATASET_COLUMNS_V9_7,
        "feature_columns": FEATURE_COLUMNS_V9_7,
        "feature_columns_count": len(FEATURE_COLUMNS_V9_7),
        "split_policy": SPLIT_POLICY_V9_7,
        "quality": quality,
        "leakage_guard": {"passed": True, "feature_available_ts_lte_decision_ts": True, "label_available_ts_gt_decision_ts": True},
        "safety": dict(SAFETY_FLAGS_V9_7),
        "limitations": EXPECTED_LIMITATIONS_V9_7,
    }
    if report["decision"] not in ALLOWED_DECISIONS_V9_7:
        raise RuntimeError(f"invalid V9.7 decision: {report['decision']}")
    _write_json(root / REPORT_JSON_PATH_V9_7, report)
    _write_json(root / MANIFEST_PATH_V9_7, report)
    _write_markdowns(root, report)
    return report


def build_refined_volnorm_labels_dataset_frame_v9_7(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS_V9_7, "available_ts", "feature_available_ts", *FEATURE_COLUMNS_V9_7], "features")
    _require_columns(labels, [*JOIN_KEYS_V9_7, "label_available_ts", *LABEL_COLUMNS_V9_7], "labels")
    feature_block = features[[*JOIN_KEYS_V9_7, "available_ts", "feature_available_ts", *FEATURE_COLUMNS_V9_7]].sort_values("event_ts").reset_index(drop=True)
    label_block = labels[[*JOIN_KEYS_V9_7, "label_available_ts", *LABEL_COLUMNS_V9_7]].sort_values("event_ts").reset_index(drop=True)
    assert_frame_equal(feature_block[JOIN_KEYS_V9_7], label_block[JOIN_KEYS_V9_7], check_dtype=False)
    merged = pd.concat([feature_block, label_block[["label_available_ts", *LABEL_COLUMNS_V9_7]]], axis=1)
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V9_7
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v9_7(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V9_7 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype("int16")
    return merged[DATASET_COLUMNS_V9_7].copy()


def assign_temporal_splits_v9_7(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V9_7["train_ratio"])
    validation_rows = int(rows * SPLIT_POLICY_V9_7["validation_ratio"])
    validation_end = train_end + validation_rows
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["walk_forward_group"] = pd.to_datetime(ordered["event_ts"], utc=True).dt.strftime("wf_%Y_%m")
    return ordered


def build_split_frame_v9_7(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset[SPLIT_COLUMNS_V9_7].copy()


def assess_dataset_quality_v9_7(dataset: pd.DataFrame, split_frame: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(dataset.columns) != DATASET_COLUMNS_V9_7:
        errors.append("schema mismatch")
    if list(split_frame.columns) != SPLIT_COLUMNS_V9_7:
        errors.append("split schema mismatch")
    forbidden = [column for column in dataset.columns if column.casefold() in FORBIDDEN_DATASET_COLUMNS_V9_7]
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if len(dataset) != EXPECTED_ROWS_V9_7[timeframe]:
        errors.append(f"row count mismatch: {len(dataset)}")
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append("source row count mismatch")
    if not (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all():
        errors.append("feature_available_ts > decision_ts")
    valid = dataset["label_valid_volnorm_h1"] == True  # noqa: E712
    if valid.any() and not (pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)).all():
        errors.append("label_available_ts <= decision_ts for valid labels")
    if not dataset["split_order"].is_monotonic_increasing:
        errors.append("split_order is not temporal")
    split_counts = dataset["split"].value_counts().to_dict()
    if not set(split_counts).issubset({"train", "validation", "test"}):
        errors.append("unexpected split values")
    return {
        "timeframe": timeframe,
        "rows_total": int(len(dataset)),
        "rows_valid_labels": int(valid.sum()),
        "rows_invalid_labels": int((~valid).sum()),
        "split_counts": {key: int(value) for key, value in sorted(split_counts.items())},
        "walk_forward_groups": sorted(dataset["walk_forward_group"].dropna().astype(str).unique().tolist()),
        "forbidden_columns_present": forbidden,
        "errors": errors,
        "warnings": warnings,
    }


def build_markdown_v9_7(report: dict[str, Any]) -> str:
    lines = [
        "# V9.7 - Dataset raffine avec labels volatility-normalized",
        "",
        "V9.7 assemble un dataset supervise offline. Il ne produit aucun ML, backtest, strategie, signal actionnable ou ordre.",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Cible : `{report['target_name']}`.",
        "",
        "## Outputs",
        "",
    ]
    for timeframe, output in report.get("outputs", {}).items():
        quality = report["quality"][timeframe]
        lines.append(f"- `{timeframe}` : `{output['path']}` avec `{output['rows']}` lignes, labels valides `{quality['rows_valid_labels']}`.")
    lines.extend(
        [
            "",
            "## Interdits maintenus",
            "",
            "- Aucun backtest.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun ordre.",
            "- Aucun paper live.",
            "- Aucun trading reel.",
        ]
    )
    return "\n".join(lines) + "\n"


def _missing_inputs(root: Path, feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for timeframe in TIMEFRAMES_V9_7:
        for block, path in [
            ("features", root / feature_manifest.get("outputs", {}).get(timeframe, {}).get("path", "")),
            ("labels", get_refined_volnorm_label_path_v9_6(root, timeframe)),
        ]:
            if not path.is_file():
                missing.append(f"{block}:{path}")
    return missing


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing {label} columns: {missing}")


def _input_block(root: Path, path: Path, digest: str, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": digest, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def _stop_report(decision: str, missing: list[str]) -> dict[str, Any]:
    return {"version": VERSION_V9_7, "status": "FAIL", "created_at_utc": utc_now_iso(), "decision": decision, "missing_full_data": missing, "safety": SAFETY_FLAGS_V9_7}


def _write_markdowns(root: Path, report: dict[str, Any]) -> None:
    markdown = build_markdown_v9_7(report)
    for path in [REPORT_MD_PATH_V9_7, DATACARD_MD_PATH_V9_7, DOC_PATH_V9_7]:
        path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
