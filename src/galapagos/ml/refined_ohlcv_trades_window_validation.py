from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import MANIFEST_PATH_V9_1
from galapagos.ml.refined_ohlcv_trades_window import (
    input_dataset_path,
    input_split_path,
    load_v9_1_dataset_manifest,
    prepare_refined_ohlcv_trades_ml_frame_v9_2,
    score_output_path,
    validate_split_alignment_v9_2,
)
from galapagos.ml.refined_ohlcv_trades_window_metrics import (
    compute_refined_ohlcv_trades_classification_metrics_v9_2,
    compute_refined_ohlcv_trades_walk_forward_metrics_v9_2,
)
from galapagos.ml.refined_ohlcv_trades_window_quality import (
    assess_refined_ohlcv_trades_ml_quality_v9_2,
    find_forbidden_feature_columns_v9_2,
    find_forbidden_output_columns_v9_2,
)
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V9_2,
    DOC_PATH_V9_2,
    EXPECTED_LIMITATIONS_V9_2,
    FORBIDDEN_METRIC_TERMS_V9_2,
    MANIFEST_PATH_V9_2,
    ML_SCHEMA_VERSION_V9_2,
    ML_SCORE_COLUMNS_V9_2,
    MODEL_NAMES_V9_2,
    REPORT_JSON_PATH_V9_2,
    REPORT_MD_PATH_V9_2,
    SAFETY_FLAGS_V9_2,
    SCORES_JSON_PATH_V9_2,
    SCORES_MD_PATH_V9_2,
    TARGET_NAME_V9_2,
    TIMEFRAMES_V9_2,
    VERSION_V9_2,
    get_feature_columns_sha256_v9_2,
)
from galapagos.validation.safety import scan_payload_for_forbidden_claims, validate_markdown_forbidden_claims


ML_RUN_ID_PATTERN_V9_2 = re.compile(r"^v9_2_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V9_2)
INPUT_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days", "feature_columns_count"}
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "ml_run_id",
    "input_dataset_manifest",
    "input_datasets",
    "input_splits",
    "outputs",
    "target_name",
    "feature_columns",
    "feature_columns_count",
    "models",
    "metrics",
    "walk_forward_metrics",
    "sanity_checks",
    "quality",
    "safety",
    "limitations",
}
QUALITY_KEYS = {
    "rows_total",
    "rows_used_for_ml",
    "rows_excluded_warmup",
    "rows_excluded_invalid_label",
    "train_rows",
    "validation_rows",
    "test_rows",
    "walk_forward_groups",
    "forbidden_feature_columns_present",
    "forbidden_output_columns_present",
    "target_name_valid",
    "split_temporal_order_valid",
    "no_shuffle_confirmed",
    "errors",
    "warnings",
}
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def validate_refined_ohlcv_trades_offline_ml_research_v9_2(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V9_2
    report_path = project_root / REPORT_JSON_PATH_V9_2
    scores_json_path = project_root / SCORES_JSON_PATH_V9_2
    if not manifest_path.exists():
        return _result([f"missing V9.2 manifest: {MANIFEST_PATH_V9_2}"], warnings)
    if not report_path.exists():
        return _result([f"missing V9.2 quality report: {REPORT_JSON_PATH_V9_2}"], warnings)
    if not scores_json_path.exists():
        return _result([f"missing V9.2 scores report: {SCORES_JSON_PATH_V9_2}"], warnings)

    dataset_manifest = load_v9_1_dataset_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_json_path)
    errors.extend(_validate_manifest_structure(project_root, manifest, dataset_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V9.2 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V9.2 quality report"))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(scan_payload_for_forbidden_claims(scores_report, "V9.2 scores report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v9_2_artifacts(project_root))

    if errors:
        return _result(errors, warnings, manifest)

    physical_quality: dict[str, dict[str, Any]] = {}
    recomputed_metrics: dict[str, Any] = {}
    recomputed_walk_forward_metrics: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_2:
        errors.extend(_validate_timeframe(project_root, manifest, dataset_manifest, timeframe, physical_quality, recomputed_metrics, recomputed_walk_forward_metrics))
    if recomputed_metrics != manifest.get("metrics"):
        errors.append("V9.2 manifest metrics mismatch")
    if recomputed_walk_forward_metrics != manifest.get("walk_forward_metrics"):
        errors.append("V9.2 manifest walk_forward_metrics mismatch")
    if manifest.get("quality") != physical_quality:
        errors.append("V9.2 manifest quality mismatch")
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {}), "metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("walk_forward_metrics", {}), "walk_forward_metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("metrics", {}), "metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("walk_forward_metrics", {}), "walk_forward_metrics"))
    return _result(errors, warnings, manifest)


def _validate_timeframe(
    root: Path,
    manifest: dict[str, Any],
    dataset_manifest: dict[str, Any],
    timeframe: str,
    physical_quality: dict[str, dict[str, Any]],
    recomputed_metrics: dict[str, Any],
    recomputed_walk_forward_metrics: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
    split_path = input_split_path(root, timeframe, dataset_manifest)
    score_path = score_output_path(root, timeframe, manifest["input_dataset_manifest"]["window_start"], manifest["input_dataset_manifest"]["window_end"])
    for label, path in [("dataset", dataset_path), ("split", split_path), ("scores", score_path)]:
        if not path.exists():
            errors.append(f"missing V9.2 {label} file for {timeframe}: {path.relative_to(root)}")
    if errors:
        return errors
    dataset = read_parquet(dataset_path)
    splits = read_parquet(split_path)
    scores = read_parquet(score_path)
    dataset_for_ml = validate_split_alignment_v9_2(dataset, splits)
    dataset_sha = sha256_file(dataset_path)
    split_sha = sha256_file(split_path)
    score_sha = sha256_file(score_path)

    errors.extend(_compare_io_block(manifest["input_datasets"][timeframe], dataset_path, dataset_sha, len(dataset), root, f"V9.2 input_datasets.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["input_splits"][timeframe], split_path, split_sha, len(splits), root, f"V9.2 input_splits.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], score_path, score_sha, len(scores), root, f"V9.2 outputs.{timeframe}", include_bytes=True))
    errors.extend(validate_score_schema_v9_2(scores, timeframe))
    errors.extend(validate_scores_against_dataset_v9_2(scores, dataset_for_ml, dataset_sha, timeframe, manifest["ml_run_id"]))
    quality = assess_refined_ohlcv_trades_ml_quality_v9_2(dataset_for_ml, scores, timeframe)
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    recomputed_metrics.update(compute_refined_ohlcv_trades_classification_metrics_v9_2(scores))
    recomputed_walk_forward_metrics.update(compute_refined_ohlcv_trades_walk_forward_metrics_v9_2(scores))
    return errors


def validate_score_schema_v9_2(scores: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V9_2:
        errors.append(f"V9.2 score schema mismatch{label}")
    forbidden = find_forbidden_output_columns_v9_2(scores.columns)
    if forbidden:
        errors.append(f"V9.2 forbidden output columns{label}: {forbidden}")
    if len(scores) and set(scores["model_name"].dropna().astype(str).unique()) - set(MODEL_NAMES_V9_2):
        errors.append(f"V9.2 unknown model_name{label}")
    if len(scores) and set(scores["target_name"].dropna().astype(str).unique()) != {TARGET_NAME_V9_2}:
        errors.append(f"V9.2 target_name mismatch{label}")
    return errors


def validate_scores_against_dataset_v9_2(
    scores: pd.DataFrame,
    dataset: pd.DataFrame,
    dataset_sha: str,
    timeframe: str,
    ml_run_id: str,
) -> list[str]:
    errors: list[str] = []
    ml_frame = prepare_refined_ohlcv_trades_ml_frame_v9_2(dataset)
    expected_rows = len(ml_frame) * len(MODEL_NAMES_V9_2)
    if len(scores) != expected_rows:
        errors.append(f"V9.2 score rows mismatch for {timeframe}: got {len(scores)}, expected {expected_rows}")
    if len(scores) == 0:
        return errors
    if set(scores["ml_run_id"].astype(str).unique()) != {ml_run_id}:
        errors.append(f"V9.2 ml_run_id mismatch for {timeframe}")
    if set(scores["dataset_sha256"].astype(str).unique()) != {dataset_sha}:
        errors.append(f"V9.2 dataset_sha256 mismatch for {timeframe}")
    if set(scores["feature_columns_sha256"].astype(str).unique()) != {get_feature_columns_sha256_v9_2()}:
        errors.append(f"V9.2 feature_columns_sha256 mismatch for {timeframe}")
    if set(scores["ml_schema_version"].astype(str).unique()) != {ML_SCHEMA_VERSION_V9_2}:
        errors.append(f"V9.2 ml_schema_version mismatch for {timeframe}")
    if not (pd.to_datetime(scores["prediction_available_ts"], utc=True) >= pd.to_datetime(scores["decision_ts"], utc=True)).all():
        errors.append(f"V9.2 prediction_available_ts before decision_ts for {timeframe}")
    if not scores["row_valid_for_ml"].eq(True).all():  # noqa: E712
        errors.append(f"V9.2 row_valid_for_ml must be true for {timeframe}")
    return errors


def validate_feature_columns_v9_2(columns: Any) -> list[str]:
    if not isinstance(columns, list):
        return ["V9.2 feature_columns must be list"]
    forbidden = find_forbidden_feature_columns_v9_2(columns)
    if forbidden:
        return [f"V9.2 forbidden feature columns: {forbidden}"]
    if columns != ALLOWED_FEATURE_COLUMNS_V9_2:
        return ["V9.2 feature_columns mismatch"]
    return []


def _validate_manifest_structure(root: Path, manifest: dict[str, Any], dataset_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(manifest) != MANIFEST_KEYS:
        errors.append("V9.2 manifest keys mismatch")
    if manifest.get("version") != VERSION_V9_2:
        errors.append("V9.2 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.2 manifest status must be PASS")
    if not isinstance(manifest.get("ml_run_id"), str) or ML_RUN_ID_PATTERN_V9_2.fullmatch(manifest["ml_run_id"]) is None:
        errors.append("V9.2 manifest ml_run_id invalid")
    input_manifest = manifest.get("input_dataset_manifest", {})
    if set(input_manifest) != INPUT_MANIFEST_KEYS:
        errors.append("V9.2 input_dataset_manifest keys mismatch")
    if input_manifest.get("path") != MANIFEST_PATH_V9_1.as_posix():
        errors.append("V9.2 input_dataset_manifest.path mismatch")
    if input_manifest.get("sha256") != sha256_file(root / MANIFEST_PATH_V9_1):
        errors.append("V9.2 input_dataset_manifest.sha256 mismatch")
    expected_window = dataset_manifest["input_features_manifest"]
    for key in ["window_start", "window_end", "total_days"]:
        if input_manifest.get(key) != expected_window.get(key):
            errors.append(f"V9.2 input_dataset_manifest.{key} mismatch")
    if input_manifest.get("feature_columns_count") != dataset_manifest.get("feature_columns_count"):
        errors.append("V9.2 input_dataset_manifest.feature_columns_count mismatch")
    if manifest.get("feature_columns_count") != len(ALLOWED_FEATURE_COLUMNS_V9_2):
        errors.append("V9.2 feature_columns_count mismatch")
    if manifest.get("target_name") != TARGET_NAME_V9_2:
        errors.append("V9.2 target_name mismatch")
    errors.extend(validate_feature_columns_v9_2(manifest.get("feature_columns", [])))
    if manifest.get("models") != MODEL_NAMES_V9_2:
        errors.append("V9.2 models mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_2:
        errors.append("V9.2 limitations mismatch")
    for section in ["input_datasets", "input_splits", "outputs", "quality", "sanity_checks"]:
        if set(manifest.get(section, {})) != TIMEFRAME_KEYS:
            errors.append(f"V9.2 manifest {section} timeframes mismatch")
    for timeframe in TIMEFRAMES_V9_2:
        for section, keys in [("input_datasets", INPUT_KEYS), ("input_splits", INPUT_KEYS), ("outputs", OUTPUT_KEYS)]:
            if set(manifest.get(section, {}).get(timeframe, {})) != keys:
                errors.append(f"V9.2 manifest {section}.{timeframe} keys mismatch")
        if set(manifest.get("quality", {}).get(timeframe, {})) != QUALITY_KEYS:
            errors.append(f"V9.2 manifest quality.{timeframe} keys mismatch")
    if manifest.get("safety") != SAFETY_FLAGS_V9_2:
        errors.append("V9.2 safety mismatch")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    return [] if report == manifest else ["V9.2 quality report mismatch"]


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    expected = {
        "version": manifest.get("version"),
        "ml_run_id": manifest.get("ml_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
        "walk_forward_metrics": manifest.get("walk_forward_metrics"),
    }
    return [] if report == expected else ["V9.2 scores report mismatch"]


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for path in [REPORT_MD_PATH_V9_2, SCORES_MD_PATH_V9_2, DOC_PATH_V9_2]:
        full = project_root / path
        if not full.exists():
            errors.append(f"missing V9.2 markdown: {path}")
            continue
        errors.extend(validate_markdown_forbidden_claims(full.read_text(encoding="utf-8"), f"V9.2 markdown {path}"))
    return errors


def _find_forbidden_v9_2_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in ["data/research/v9_2/backtests", "data/research/v9_2/strategies", "reports/backtests", "reports/strategies", "orders", "execution", "models", "checkpoints"]:
        if (root / relative).exists():
            errors.append(f"forbidden V9.2 artifact exists: {relative}")
    for path in root.rglob("*"):
        if any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"forbidden persistent model file exists: {path.relative_to(root)}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    return [] if safety == SAFETY_FLAGS_V9_2 else ["V9.2 safety flags mismatch"]


def _scan_metrics_for_forbidden_terms(payload: Any, label: str) -> list[str]:
    text = json.dumps(payload, sort_keys=True).casefold()
    present = sorted(term for term in FORBIDDEN_METRIC_TERMS_V9_2 if term in text)
    return [f"V9.2 forbidden metric terms in {label}: {present}"] if present else []


def _validate_metric_bounds(payload: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for key, metrics in payload.items():
        for metric_name in ["accuracy", "balanced_accuracy", "macro_f1"]:
            value = metrics.get(metric_name)
            if not isinstance(value, int | float) or not 0 <= float(value) <= 1:
                errors.append(f"V9.2 {label}.{key}.{metric_name} out of bounds")
        for nested_name in ["per_class_precision", "per_class_recall"]:
            nested = metrics.get(nested_name, {})
            if isinstance(nested, dict):
                for class_name, value in nested.items():
                    if not isinstance(value, int | float) or not 0 <= float(value) <= 1:
                        errors.append(f"V9.2 {label}.{key}.{nested_name}.{class_name} out of bounds")
    return errors


def _compare_io_block(
    payload: dict[str, Any],
    path: Path,
    sha256: str,
    rows: int,
    root: Path,
    label: str,
    *,
    include_bytes: bool,
) -> list[str]:
    errors: list[str] = []
    if payload.get("path") != path.relative_to(root).as_posix():
        errors.append(f"{label} path mismatch")
    if payload.get("sha256") != sha256:
        errors.append(f"{label} sha256 mismatch")
    if int(payload.get("rows", -1)) != int(rows):
        errors.append(f"{label} rows mismatch")
    if include_bytes:
        if int(payload.get("bytes", -1)) != path.stat().st_size:
            errors.append(f"{label} bytes mismatch")
        if payload.get("format") != "parquet":
            errors.append(f"{label} format mismatch")
    return errors


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
