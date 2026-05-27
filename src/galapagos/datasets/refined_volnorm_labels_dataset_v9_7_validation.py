from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7 import assess_dataset_quality_v9_7
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import (
    ALLOWED_DECISIONS_V9_7,
    DATASET_COLUMNS_V9_7,
    EXPECTED_LIMITATIONS_V9_7,
    FORBIDDEN_DATASET_COLUMNS_V9_7,
    MANIFEST_PATH_V9_7,
    REPORT_JSON_PATH_V9_7,
    REPORT_MD_PATH_V9_7,
    SAFETY_FLAGS_V9_7,
    SPLIT_COLUMNS_V9_7,
    TARGET_NAME_V9_7,
    TIMEFRAMES_V9_7,
    VERSION_V9_7,
    get_refined_volnorm_dataset_path_v9_7,
    get_refined_volnorm_split_path_v9_7,
)
from galapagos.features.refined_ohlcv_trades_schemas import MANIFEST_PATH_V9_0
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import MANIFEST_PATH_V9_6, get_refined_volnorm_label_path_v9_6


def validate_refined_volnorm_labels_dataset_v9_7(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for path in [MANIFEST_PATH_V9_7, REPORT_JSON_PATH_V9_7, REPORT_MD_PATH_V9_7]:
        if not (root / path).exists():
            return _result([f"missing V9.7 file: {path}"], warnings)
    manifest = _read_json(root / MANIFEST_PATH_V9_7)
    report = _read_json(root / REPORT_JSON_PATH_V9_7)
    feature_manifest = _read_json(root / MANIFEST_PATH_V9_0)
    errors.extend(validate_payload_v9_7(manifest))
    if report != manifest:
        errors.append("V9.7 report and manifest mismatch")
    if errors:
        return _result(errors, warnings, manifest)
    physical_quality: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_7:
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        split_path = get_refined_volnorm_split_path_v9_7(root, timeframe)
        feature_path = root / feature_manifest["outputs"][timeframe]["path"]
        label_path = get_refined_volnorm_label_path_v9_6(root, timeframe)
        for label, path in [("dataset", dataset_path), ("splits", split_path), ("features", feature_path), ("labels", label_path)]:
            if not path.exists():
                errors.append(f"missing V9.7 {label} for {timeframe}: {path}")
        if errors:
            continue
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        features = read_parquet(feature_path)
        labels = read_parquet(label_path)
        errors.extend(validate_dataset_frame_v9_7(dataset, splits, timeframe))
        if manifest["outputs"][timeframe]["sha256"] != sha256_file(dataset_path):
            errors.append(f"dataset sha256 mismatch for {timeframe}")
        if manifest["splits"][timeframe]["sha256"] != sha256_file(split_path):
            errors.append(f"split sha256 mismatch for {timeframe}")
        quality = assess_dataset_quality_v9_7(dataset, splits, features, labels, timeframe)
        physical_quality[timeframe] = quality
        errors.extend(quality["errors"])
    if manifest.get("quality") != physical_quality:
        errors.append("V9.7 quality mismatch")
    return _result(errors, warnings, manifest)


def validate_payload_v9_7(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("version") != VERSION_V9_7:
        errors.append("V9.7 version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V9.7 status must be PASS")
    if payload.get("decision") not in ALLOWED_DECISIONS_V9_7:
        errors.append("V9.7 decision is not allowed")
    if payload.get("target_name") != TARGET_NAME_V9_7:
        errors.append("V9.7 target mismatch")
    if payload.get("dataset_columns") != DATASET_COLUMNS_V9_7:
        errors.append("V9.7 dataset columns mismatch")
    if payload.get("safety") != SAFETY_FLAGS_V9_7:
        errors.append("V9.7 safety mismatch")
    if payload.get("limitations") != EXPECTED_LIMITATIONS_V9_7:
        errors.append("V9.7 limitations mismatch")
    if payload.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.7 leakage guard must pass")
    return errors


def validate_dataset_frame_v9_7(dataset, splits, timeframe: str = "") -> list[str]:
    suffix = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(dataset.columns) != DATASET_COLUMNS_V9_7:
        errors.append(f"V9.7 dataset schema mismatch{suffix}")
    if list(splits.columns) != SPLIT_COLUMNS_V9_7:
        errors.append(f"V9.7 split schema mismatch{suffix}")
    if len(dataset) != len(splits):
        errors.append(f"V9.7 split row count mismatch{suffix}")
    forbidden = [column for column in dataset.columns if column.casefold() in FORBIDDEN_DATASET_COLUMNS_V9_7]
    if forbidden:
        errors.append(f"V9.7 forbidden dataset columns{suffix}: {forbidden}")
    if set(dataset["target_name"].astype(str).unique()) != {TARGET_NAME_V9_7}:
        errors.append(f"V9.7 target_name mismatch{suffix}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_7, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest or {}}
