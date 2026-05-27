from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import get_refined_volnorm_dataset_path_v9_7
from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import (
    ALLOWED_FEATURE_COLUMNS_V9_8,
    EXPECTED_LIMITATIONS_V9_8,
    MANIFEST_PATH_V9_8,
    ML_SCHEMA_VERSION_V9_8,
    ML_SCORE_COLUMNS_V9_8,
    MODEL_NAMES_V9_8,
    REPORT_JSON_PATH_V9_8,
    REPORT_MD_PATH_V9_8,
    SAFETY_FLAGS_V9_8,
    SCORES_JSON_PATH_V9_8,
    TARGET_NAME_V9_8,
    TIMEFRAMES_V9_8,
    VERSION_V9_8,
    feature_leakage_scan_v9_8,
    get_feature_columns_sha256_v9_8,
    get_refined_volnorm_ml_score_path_v9_8,
    metric_forbidden_scan_v9_8,
    prepare_refined_volnorm_ml_frame_v9_8,
)


def validate_refined_volnorm_labels_offline_ml_v9_8(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for path in [MANIFEST_PATH_V9_8, REPORT_JSON_PATH_V9_8, SCORES_JSON_PATH_V9_8, REPORT_MD_PATH_V9_8]:
        if not (root / path).exists():
            return _result([f"missing V9.8 file: {path}"], warnings)
    manifest = _read_json(root / MANIFEST_PATH_V9_8)
    report = _read_json(root / REPORT_JSON_PATH_V9_8)
    scores_report = _read_json(root / SCORES_JSON_PATH_V9_8)
    errors.extend(validate_manifest_payload_v9_8(manifest))
    if report != manifest:
        errors.append("V9.8 report and manifest mismatch")
    if scores_report.get("outputs") != manifest.get("outputs"):
        errors.append("V9.8 scores report outputs mismatch")
    if errors:
        return _result(errors, warnings, manifest)
    for timeframe in TIMEFRAMES_V9_8:
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        score_path = get_refined_volnorm_ml_score_path_v9_8(root, timeframe)
        if not dataset_path.exists() or not score_path.exists():
            errors.append(f"missing V9.8 physical files for {timeframe}")
            continue
        dataset = read_parquet(dataset_path)
        scores = read_parquet(score_path)
        errors.extend(validate_score_frame_v9_8(scores, dataset, sha256_file(dataset_path), manifest["ml_run_id"], timeframe))
        if manifest["outputs"][timeframe]["sha256"] != sha256_file(score_path):
            errors.append(f"V9.8 score sha256 mismatch for {timeframe}")
    return _result(errors, warnings, manifest)


def validate_manifest_payload_v9_8(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_8:
        errors.append("V9.8 version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.8 status must be PASS")
    if manifest.get("target_name") != TARGET_NAME_V9_8:
        errors.append("V9.8 target mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V9_8:
        errors.append("V9.8 feature columns mismatch")
    if manifest.get("models") != MODEL_NAMES_V9_8:
        errors.append("V9.8 model list mismatch")
    if manifest.get("safety") != SAFETY_FLAGS_V9_8:
        errors.append("V9.8 safety mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_8:
        errors.append("V9.8 limitations mismatch")
    if feature_leakage_scan_v9_8(manifest.get("feature_columns", {})) != manifest.get("feature_leakage_scan"):
        errors.append("V9.8 feature leakage scan mismatch")
    if manifest.get("feature_leakage_scan", {}).get("passed") is not True:
        errors.append("V9.8 feature leakage scan must pass")
    if metric_forbidden_scan_v9_8({"metrics": manifest.get("metrics", {}), "walk_forward_metrics": manifest.get("walk_forward_metrics", {})}).get("passed") is not True:
        errors.append("V9.8 forbidden metric terms detected")
    return errors


def validate_score_frame_v9_8(scores: pd.DataFrame, dataset: pd.DataFrame, dataset_sha: str, run_id: str, timeframe: str = "") -> list[str]:
    suffix = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V9_8:
        errors.append(f"V9.8 score schema mismatch{suffix}")
    if len(scores) != len(prepare_refined_volnorm_ml_frame_v9_8(dataset)) * len(MODEL_NAMES_V9_8):
        errors.append(f"V9.8 score row count mismatch{suffix}")
    if len(scores) and set(scores["model_name"].astype(str).unique()) != set(MODEL_NAMES_V9_8):
        errors.append(f"V9.8 model_name mismatch{suffix}")
    if len(scores) and set(scores["target_name"].astype(str).unique()) != {TARGET_NAME_V9_8}:
        errors.append(f"V9.8 target_name mismatch{suffix}")
    if len(scores) and set(scores["dataset_sha256"].astype(str).unique()) != {dataset_sha}:
        errors.append(f"V9.8 dataset sha mismatch{suffix}")
    if len(scores) and set(scores["feature_columns_sha256"].astype(str).unique()) != {get_feature_columns_sha256_v9_8()}:
        errors.append(f"V9.8 feature columns sha mismatch{suffix}")
    if len(scores) and set(scores["ml_schema_version"].astype(str).unique()) != {ML_SCHEMA_VERSION_V9_8}:
        errors.append(f"V9.8 schema version mismatch{suffix}")
    if len(scores) and set(scores["ml_run_id"].astype(str).unique()) != {run_id}:
        errors.append(f"V9.8 ml_run_id mismatch{suffix}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_8, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest or {}}
