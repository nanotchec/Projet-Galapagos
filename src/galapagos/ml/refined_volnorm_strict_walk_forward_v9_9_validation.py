from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import get_refined_volnorm_dataset_path_v9_7
from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9 import (
    ALLOWED_FEATURE_COLUMNS_V9_9,
    EXPECTED_LIMITATIONS_V9_9,
    MANIFEST_PATH_V9_9,
    ML_SCHEMA_VERSION_V9_9,
    ML_SCORE_COLUMNS_V9_9,
    MODEL_NAMES_V9_9,
    REPORT_JSON_PATH_V9_9,
    REPORT_MD_PATH_V9_9,
    SAFETY_FLAGS_V9_9,
    SCORES_JSON_PATH_V9_9,
    TARGET_NAME_V9_9,
    TIMEFRAMES_V9_9,
    VERSION_V9_9,
    WALK_FORWARD_FOLD_COLUMNS_V9_9,
    feature_leakage_scan_v9_8,
    get_feature_columns_sha256_v9_9,
    get_refined_volnorm_walk_forward_folds_path_v9_9,
    get_refined_volnorm_walk_forward_score_path_v9_9,
    metric_forbidden_scan_v9_8,
)


def validate_refined_volnorm_strict_walk_forward_v9_9(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for path in [MANIFEST_PATH_V9_9, REPORT_JSON_PATH_V9_9, SCORES_JSON_PATH_V9_9, REPORT_MD_PATH_V9_9]:
        if not (root / path).exists():
            return _result([f"missing V9.9 file: {path}"], warnings)
    manifest = _read_json(root / MANIFEST_PATH_V9_9)
    report = _read_json(root / REPORT_JSON_PATH_V9_9)
    errors.extend(validate_manifest_payload_v9_9(manifest))
    if report != manifest:
        errors.append("V9.9 report and manifest mismatch")
    if errors:
        return _result(errors, warnings, manifest)
    for timeframe in TIMEFRAMES_V9_9:
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        score_path = get_refined_volnorm_walk_forward_score_path_v9_9(root, timeframe)
        folds_path = get_refined_volnorm_walk_forward_folds_path_v9_9(root, timeframe)
        if not dataset_path.exists() or not score_path.exists() or not folds_path.exists():
            errors.append(f"missing V9.9 physical files for {timeframe}")
            continue
        scores = read_parquet(score_path)
        folds = read_parquet(folds_path)
        errors.extend(validate_score_frame_v9_9(scores, sha256_file(dataset_path), manifest["walk_forward_run_id"], timeframe))
        errors.extend(validate_fold_frame_v9_9(folds, timeframe))
        if manifest["outputs"]["scores"][timeframe]["sha256"] != sha256_file(score_path):
            errors.append(f"V9.9 score sha256 mismatch for {timeframe}")
        if manifest["outputs"]["folds"][timeframe]["sha256"] != sha256_file(folds_path):
            errors.append(f"V9.9 folds sha256 mismatch for {timeframe}")
    return _result(errors, warnings, manifest)


def validate_manifest_payload_v9_9(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_9:
        errors.append("V9.9 version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.9 status must be PASS")
    if manifest.get("target_name") != TARGET_NAME_V9_9:
        errors.append("V9.9 target mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V9_9:
        errors.append("V9.9 feature columns mismatch")
    if manifest.get("models") != MODEL_NAMES_V9_9:
        errors.append("V9.9 model list mismatch")
    if manifest.get("safety") != SAFETY_FLAGS_V9_9:
        errors.append("V9.9 safety mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_9:
        errors.append("V9.9 limitations mismatch")
    if feature_leakage_scan_v9_8(manifest.get("feature_columns", {})) != manifest.get("feature_leakage_scan"):
        errors.append("V9.9 feature leakage scan mismatch")
    if manifest.get("feature_leakage_scan", {}).get("passed") is not True:
        errors.append("V9.9 feature leakage scan must pass")
    if metric_forbidden_scan_v9_8({"metrics": manifest.get("metrics", {}), "aggregate_metrics": manifest.get("aggregate_metrics", {})}).get("passed") is not True:
        errors.append("V9.9 forbidden metric terms detected")
    for key, value in manifest.get("findings", {}).items():
        if value is not False:
            errors.append(f"V9.9 finding must be false: {key}")
    return errors


def validate_score_frame_v9_9(scores: pd.DataFrame, dataset_sha: str, run_id: str, timeframe: str = "") -> list[str]:
    suffix = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V9_9:
        errors.append(f"V9.9 score schema mismatch{suffix}")
    if len(scores) and set(scores["model_name"].astype(str).unique()) != set(MODEL_NAMES_V9_9):
        errors.append(f"V9.9 model_name mismatch{suffix}")
    if len(scores) and set(scores["target_name"].astype(str).unique()) != {TARGET_NAME_V9_9}:
        errors.append(f"V9.9 target mismatch{suffix}")
    if len(scores) and set(scores["dataset_sha256"].astype(str).unique()) != {dataset_sha}:
        errors.append(f"V9.9 dataset sha mismatch{suffix}")
    if len(scores) and set(scores["feature_columns_sha256"].astype(str).unique()) != {get_feature_columns_sha256_v9_9()}:
        errors.append(f"V9.9 feature sha mismatch{suffix}")
    if len(scores) and set(scores["ml_schema_version"].astype(str).unique()) != {ML_SCHEMA_VERSION_V9_9}:
        errors.append(f"V9.9 schema version mismatch{suffix}")
    if len(scores) and set(scores["ml_run_id"].astype(str).unique()) != {run_id}:
        errors.append(f"V9.9 run id mismatch{suffix}")
    return errors


def validate_fold_frame_v9_9(folds: pd.DataFrame, timeframe: str = "") -> list[str]:
    suffix = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(folds.columns) != WALK_FORWARD_FOLD_COLUMNS_V9_9:
        errors.append(f"V9.9 folds schema mismatch{suffix}")
    for _fold_id, group in folds.groupby("fold_id", sort=True):
        ranges = {}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            if role_group.empty:
                errors.append(f"missing fold role {role}{suffix}")
                continue
            ts = pd.to_datetime(role_group["event_ts"], utc=True)
            ranges[role] = (ts.min(), ts.max())
        if set(ranges) == {"train", "validation", "test"} and not (ranges["train"][1] < ranges["validation"][0] and ranges["validation"][1] < ranges["test"][0]):
            errors.append(f"V9.9 fold temporal order invalid{suffix}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_9, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest or {}}
