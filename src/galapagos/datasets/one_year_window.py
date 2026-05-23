from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.one_year_window_datacard import build_datacard_markdown_v4_5, build_quality_markdown_v4_5
from galapagos.datasets.one_year_window_quality import assess_one_year_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V4_5,
    DATASET_SCHEMA_VERSION_V4_5,
    DATACARD_MD_PATH_V4_5,
    DOC_PATH_V4_5,
    EXPECTED_LIMITATIONS_V4_5,
    EXPECTED_ROWS_V4_5,
    FEATURE_VALUE_COLUMNS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V4_5,
    REPORT_JSON_PATH_V4_5,
    REPORT_MD_PATH_V4_5,
    SPLIT_COLUMNS_V4_5,
    SPLIT_POLICY_V4_5,
    TIMEFRAMES_V4_5,
    VERSION_V4_5,
    get_dataset_v4_5_path,
    get_split_v4_5_path,
)
from galapagos.features.one_year_window import output_path as v4_3_feature_path
from galapagos.features.one_year_window_validation import validate_one_year_causal_feature_store_v4_3
from galapagos.labels.one_year_window import output_path as v4_4_label_path
from galapagos.labels.one_year_window_validation import validate_one_year_label_factory_v4_4


def run_one_year_offline_supervised_dataset_v4_5(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    created_at = utc_now_iso()
    dataset_run_id = f"v4_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V4_5:
        feature_path = input_feature_path(root, timeframe)
        label_path = input_label_path(root, timeframe)
        feature_frame = read_parquet(feature_path)
        label_frame = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)

        dataset = build_one_year_offline_supervised_dataset_v4_5(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v4_5(dataset)

        dataset_path = get_dataset_v4_5_path(root, timeframe)
        split_path = get_split_v4_5_path(root, timeframe)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(root, feature_path, feature_sha, len(feature_frame))
        input_labels[timeframe] = _input_block(root, label_path, label_sha, len(label_frame))
        outputs[timeframe] = _output_block(root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(root, split_path, len(split_frame))
        quality[timeframe] = assess_one_year_dataset_quality(
            dataset,
            expected_rows=EXPECTED_ROWS_V4_5[timeframe],
            timeframe=timeframe,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
        )
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V4_5,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V4_5,
        "dataset_columns": DATASET_COLUMNS_V4_5,
        "split_policy": SPLIT_POLICY_V4_5,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V4_5,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V4_5, manifest)
    _write_json(root / REPORT_JSON_PATH_V4_5, report)
    quality_markdown = build_quality_markdown_v4_5(manifest)
    datacard = build_datacard_markdown_v4_5(manifest)
    _write_text(root / REPORT_MD_PATH_V4_5, quality_markdown)
    _write_text(root / DATACARD_MD_PATH_V4_5, datacard)
    _write_text(root / DOC_PATH_V4_5, quality_markdown)
    return manifest


def build_one_year_offline_supervised_dataset_v4_5(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS], "features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")

    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]].copy()
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].copy()
    merged = feature_block.merge(label_block, on=JOIN_KEYS, how="inner", validate="one_to_one")
    merged = merged.sort_values("event_ts").reset_index(drop=True)
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V4_5
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v4_5(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V4_5 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype(int)
    return merged[DATASET_COLUMNS_V4_5].copy()


def assign_temporal_splits_v4_5(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V4_5["train_ratio"])
    validation_rows = (rows - train_end) // 2
    validation_end = train_end + validation_rows
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V4_5["purge_embargo"]
    return ordered


def build_split_frame_v4_5(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, SPLIT_COLUMNS_V4_5, "dataset")
    return dataset[SPLIT_COLUMNS_V4_5].copy()


def input_feature_path(root: Path, timeframe: str) -> Path:
    return v4_3_feature_path(root, timeframe)


def input_label_path(root: Path, timeframe: str) -> Path:
    return v4_4_label_path(root, timeframe)


def _validate_inputs(root: Path) -> None:
    validators = [
        ("V4.3 one_year features", validate_one_year_causal_feature_store_v4_3),
        ("V4.4 one_year labels", validate_one_year_label_factory_v4_4),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V4.5: {result['errors']}")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "dataset_run_id": manifest["dataset_run_id"],
        "input_features": manifest["input_features"],
        "input_labels": manifest["input_labels"],
        "outputs": manifest["outputs"],
        "splits": manifest["splits"],
        "dataset_schema_version": manifest["dataset_schema_version"],
        "dataset_columns": manifest["dataset_columns"],
        "split_policy": manifest["split_policy"],
        "quality": manifest["quality"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def _safety() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": True,
        "dataset_enabled": True,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required {label} columns: {missing}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
