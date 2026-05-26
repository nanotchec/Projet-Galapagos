from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import MANIFEST_PATH_V9_1
from galapagos.ml.refined_strict_walk_forward import (
    WALK_FORWARD_POLICY_V9_3,
    compare_to_static_split_v9_2,
    folds_output_path,
    input_dataset_path,
    load_v9_1_dataset_manifest,
    scan_refined_strict_walk_forward_feature_leakage_v9_3,
    score_output_path,
)
from galapagos.ml.refined_strict_walk_forward_metrics import (
    compute_refined_strict_walk_forward_aggregate_metrics_v9_3,
    compute_refined_strict_walk_forward_metrics_v9_3,
)
from galapagos.ml.refined_strict_walk_forward_quality import assess_refined_strict_walk_forward_quality_v9_3
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V9_3,
    DOC_PATH_V9_3,
    EXPECTED_LIMITATIONS_V9_3,
    FORBIDDEN_FEATURE_EXACT_V9_3,
    FORBIDDEN_FEATURE_PREFIXES_V9_3,
    FORBIDDEN_METRIC_TERMS_V9_3,
    FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_3,
    MANIFEST_PATH_V9_3,
    ML_SCORE_COLUMNS_V9_3,
    MODEL_NAMES_V9_3,
    REPORT_JSON_PATH_V9_3,
    REPORT_MD_PATH_V9_3,
    SAFETY_FLAGS_V9_3,
    SCORES_JSON_PATH_V9_3,
    SCORES_MD_PATH_V9_3,
    TARGET_NAME_V9_3,
    TIMEFRAMES_V9_3,
    VERSION_V9_3,
    WALK_FORWARD_FOLD_COLUMNS_V9_3,
    get_feature_columns_sha256_v9_3,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


RUN_ID_PATTERN_V9_3 = re.compile(r"^v9_3_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V9_3)
INPUT_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days", "feature_columns_count"}
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
OUTPUT_SECTION_KEYS = {"scores", "folds"}
FINDINGS_KEYS = {
    "robust_edge_claimed",
    "strategy_validated",
    "backtest_performed",
    "actionable_signal_produced",
    "walk_forward_validated_for_trading",
    "warnings",
}
QUALITY_KEYS = {
    "rows_total",
    "rows_used_for_ml",
    "folds_count",
    "rows_excluded_warmup",
    "rows_excluded_invalid_label",
    "rows_purged",
    "rows_embargoed",
    "fold_role_counts",
    "forbidden_feature_columns_present",
    "forbidden_output_columns_present",
    "fold_temporal_order_valid",
    "no_shuffle_confirmed",
    "errors",
    "warnings",
    "timeframe",
}
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "walk_forward_run_id",
    "input_dataset_manifest",
    "input_datasets",
    "walk_forward_policy",
    "folds",
    "outputs",
    "target_name",
    "feature_columns",
    "feature_columns_count",
    "models",
    "metrics",
    "aggregate_metrics",
    "label_shuffle_falsification",
    "comparison_to_static_split_v9_2",
    "feature_leakage_scan",
    "metric_forbidden_scan",
    "findings",
    "quality",
    "safety",
    "limitations",
}
SCORES_REPORT_KEYS = {
    "version",
    "walk_forward_run_id",
    "outputs",
    "metrics",
    "aggregate_metrics",
    "label_shuffle_falsification",
    "comparison_to_static_split_v9_2",
}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def validate_refined_strict_walk_forward_validation_v9_3(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    warnings: list[str] = []
    manifest_path = root / MANIFEST_PATH_V9_3
    report_path = root / REPORT_JSON_PATH_V9_3
    scores_report_path = root / SCORES_JSON_PATH_V9_3
    if not manifest_path.exists():
        return _result([f"missing V9.3 manifest: {MANIFEST_PATH_V9_3}"], warnings)
    if not report_path.exists():
        return _result([f"missing V9.3 report: {REPORT_JSON_PATH_V9_3}"], warnings)
    if not scores_report_path.exists():
        return _result([f"missing V9.3 scores report: {SCORES_JSON_PATH_V9_3}"], warnings)

    dataset_manifest = load_v9_1_dataset_manifest(root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_report_path)
    errors: list[str] = []
    errors.extend(_validate_manifest_structure(root, manifest, dataset_manifest))
    errors.extend(_validate_report(manifest, report))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v9_3_artifacts(root))
    if errors:
        return _result(errors, warnings, manifest)

    recomputed_metrics: dict[str, Any] = {}
    recomputed_aggregate: dict[str, Any] = {}
    physical_quality: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_3:
        errors.extend(_validate_timeframe(root, manifest, dataset_manifest, timeframe, recomputed_metrics, recomputed_aggregate, physical_quality))
    if recomputed_metrics != manifest.get("metrics"):
        errors.append("V9.3 metrics mismatch")
    if recomputed_aggregate != manifest.get("aggregate_metrics"):
        errors.append("V9.3 aggregate_metrics mismatch")
    if compare_to_static_split_v9_2(root, manifest.get("aggregate_metrics", {})) != manifest.get("comparison_to_static_split_v9_2"):
        errors.append("V9.3 comparison_to_static_split_v9_2 mismatch")
    if scan_refined_strict_walk_forward_feature_leakage_v9_3(manifest.get("feature_columns", [])) != manifest.get("feature_leakage_scan"):
        errors.append("V9.3 feature_leakage_scan mismatch")
    if manifest.get("quality") != physical_quality:
        errors.append("V9.3 quality mismatch")
    errors.extend(_validate_findings(manifest.get("findings", {})))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {}), "metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("aggregate_metrics", {}), "aggregate_metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("label_shuffle_falsification", {}), "label_shuffle_falsification"))
    errors.extend(_validate_metric_bounds(manifest.get("metrics", {}), "metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("aggregate_metrics", {}), "aggregate_metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("label_shuffle_falsification", {}), "label_shuffle_falsification"))
    return _result(errors, warnings, manifest)


def _validate_timeframe(
    root: Path,
    manifest: dict[str, Any],
    dataset_manifest: dict[str, Any],
    timeframe: str,
    recomputed_metrics: dict[str, Any],
    recomputed_aggregate: dict[str, Any],
    physical_quality: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
    scores_path = score_output_path(root, timeframe, manifest["input_dataset_manifest"]["window_start"], manifest["input_dataset_manifest"]["window_end"])
    folds_path = folds_output_path(root, timeframe, manifest["input_dataset_manifest"]["window_start"], manifest["input_dataset_manifest"]["window_end"])
    for label, path in [("dataset", dataset_path), ("scores", scores_path), ("folds", folds_path)]:
        if not path.exists():
            errors.append(f"missing V9.3 {label} for {timeframe}: {path.relative_to(root)}")
    if errors:
        return errors
    dataset = read_parquet(dataset_path)
    scores = read_parquet(scores_path)
    folds = read_parquet(folds_path)
    errors.extend(_compare_io_block(manifest["input_datasets"][timeframe], dataset_path, sha256_file(dataset_path), len(dataset), root, f"V9.3 input_datasets.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["outputs"]["scores"][timeframe], scores_path, sha256_file(scores_path), len(scores), root, f"V9.3 outputs.scores.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["outputs"]["folds"][timeframe], folds_path, sha256_file(folds_path), len(folds), root, f"V9.3 outputs.folds.{timeframe}", include_bytes=True))
    errors.extend(validate_score_schema_v9_3(scores, timeframe))
    errors.extend(validate_folds_schema_v9_3(folds, timeframe))
    errors.extend(validate_fold_temporal_order_v9_3(folds, timeframe))
    errors.extend(validate_scores_against_inputs_v9_3(scores, dataset, sha256_file(dataset_path), manifest["walk_forward_run_id"], timeframe))
    metrics = compute_refined_strict_walk_forward_metrics_v9_3(scores)
    recomputed_metrics.update(metrics)
    recomputed_aggregate.update(compute_refined_strict_walk_forward_aggregate_metrics_v9_3(metrics))
    quality = assess_refined_strict_walk_forward_quality_v9_3(dataset, folds, scores, timeframe)
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def validate_score_schema_v9_3(scores: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V9_3:
        errors.append(f"V9.3 score schema mismatch{label}")
    forbidden = [column for column in scores.columns if column.casefold() in {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_3}]
    if forbidden:
        errors.append(f"V9.3 forbidden output columns{label}: {forbidden}")
    if len(scores) and set(scores["model_name"].dropna().astype(str).unique()) - set(MODEL_NAMES_V9_3):
        errors.append(f"V9.3 unknown model_name{label}")
    return errors


def validate_folds_schema_v9_3(folds: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    return [] if list(folds.columns) == WALK_FORWARD_FOLD_COLUMNS_V9_3 else [f"V9.3 folds schema mismatch{label}"]


def validate_fold_temporal_order_v9_3(folds: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if folds.empty:
        return [f"V9.3 no folds{label}"]
    for fold_id, group in folds.groupby("fold_id", sort=True):
        role_ranges = {}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            if role_group.empty:
                errors.append(f"V9.3 missing {role} in {fold_id}{label}")
                continue
            timestamps = pd.to_datetime(role_group["event_ts"], utc=True)
            role_ranges[role] = (timestamps.min(), timestamps.max())
        if set(role_ranges) == {"train", "validation", "test"} and not (
            role_ranges["train"][1] < role_ranges["validation"][0] and role_ranges["validation"][1] < role_ranges["test"][0]
        ):
            errors.append(f"V9.3 fold temporal order invalid in {fold_id}{label}")
    return errors


def validate_scores_against_inputs_v9_3(
    scores: pd.DataFrame,
    dataset: pd.DataFrame,
    dataset_sha: str,
    run_id: str,
    timeframe: str,
) -> list[str]:
    errors: list[str] = []
    if len(scores) == 0:
        return [f"V9.3 empty scores for {timeframe}"]
    if "walk_forward_run_id" in scores.columns:
        errors.append(f"V9.3 scores must use ml_run_id, not walk_forward_run_id for {timeframe}")
    if set(scores["ml_run_id"].astype(str).unique()) != {run_id}:
        errors.append(f"V9.3 ml_run_id mismatch for {timeframe}")
    if set(scores["dataset_sha256"].astype(str).unique()) != {dataset_sha}:
        errors.append(f"V9.3 dataset_sha256 mismatch for {timeframe}")
    if set(scores["feature_columns_sha256"].astype(str).unique()) != {get_feature_columns_sha256_v9_3()}:
        errors.append(f"V9.3 feature_columns_sha256 mismatch for {timeframe}")
    if set(scores["target_name"].astype(str).unique()) != {TARGET_NAME_V9_3}:
        errors.append(f"V9.3 target_name mismatch for {timeframe}")
    if not (pd.to_datetime(scores["prediction_available_ts"], utc=True) >= pd.to_datetime(scores["decision_ts"], utc=True)).all():
        errors.append(f"V9.3 prediction_available_ts before decision_ts for {timeframe}")
    if dataset.empty:
        errors.append(f"V9.3 empty source dataset for {timeframe}")
    return errors


def validate_feature_columns_v9_3(columns: Any) -> list[str]:
    if not isinstance(columns, list):
        return ["V9.3 feature_columns must be list"]
    exact = {term.casefold() for term in FORBIDDEN_FEATURE_EXACT_V9_3}
    prefixes = tuple(term.casefold() for term in FORBIDDEN_FEATURE_PREFIXES_V9_3)
    forbidden = [str(column) for column in columns if str(column).casefold() in exact or str(column).casefold().startswith(prefixes)]
    if forbidden:
        return [f"V9.3 forbidden feature columns: {forbidden}"]
    if columns != ALLOWED_FEATURE_COLUMNS_V9_3:
        return ["V9.3 feature_columns mismatch"]
    return []


def _validate_manifest_structure(root: Path, manifest: dict[str, Any], dataset_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(manifest) != MANIFEST_KEYS:
        errors.append("V9.3 manifest keys mismatch")
    if manifest.get("version") != VERSION_V9_3:
        errors.append("V9.3 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.3 manifest status must be PASS")
    if not isinstance(manifest.get("walk_forward_run_id"), str) or RUN_ID_PATTERN_V9_3.fullmatch(manifest["walk_forward_run_id"]) is None:
        errors.append("V9.3 walk_forward_run_id invalid")
    input_manifest = manifest.get("input_dataset_manifest", {})
    if set(input_manifest) != INPUT_MANIFEST_KEYS:
        errors.append("V9.3 input_dataset_manifest keys mismatch")
    if input_manifest.get("path") != MANIFEST_PATH_V9_1.as_posix():
        errors.append("V9.3 input_dataset_manifest.path mismatch")
    if input_manifest.get("sha256") != sha256_file(root / MANIFEST_PATH_V9_1):
        errors.append("V9.3 input_dataset_manifest.sha256 mismatch")
    expected_window = dataset_manifest["input_features_manifest"]
    for key in ["window_start", "window_end", "total_days"]:
        if input_manifest.get(key) != expected_window.get(key):
            errors.append(f"V9.3 input_dataset_manifest.{key} mismatch")
    if manifest.get("walk_forward_policy") != WALK_FORWARD_POLICY_V9_3:
        errors.append("V9.3 walk_forward_policy mismatch")
    if manifest.get("target_name") != TARGET_NAME_V9_3:
        errors.append("V9.3 target_name mismatch")
    errors.extend(validate_feature_columns_v9_3(manifest.get("feature_columns", [])))
    if manifest.get("feature_columns_count") != len(ALLOWED_FEATURE_COLUMNS_V9_3):
        errors.append("V9.3 feature_columns_count mismatch")
    if manifest.get("models") != MODEL_NAMES_V9_3:
        errors.append("V9.3 models mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_3:
        errors.append("V9.3 limitations mismatch")
    for section in ["input_datasets", "folds", "quality"]:
        if set(manifest.get(section, {})) != TIMEFRAME_KEYS:
            errors.append(f"V9.3 manifest {section} timeframes mismatch")
    if set(manifest.get("outputs", {})) != OUTPUT_SECTION_KEYS:
        errors.append("V9.3 outputs keys mismatch")
    for output_section in ["scores", "folds"]:
        if set(manifest.get("outputs", {}).get(output_section, {})) != TIMEFRAME_KEYS:
            errors.append(f"V9.3 outputs.{output_section} timeframes mismatch")
    for timeframe in TIMEFRAMES_V9_3:
        if set(manifest.get("input_datasets", {}).get(timeframe, {})) != INPUT_KEYS:
            errors.append(f"V9.3 input_datasets.{timeframe} keys mismatch")
        if set(manifest.get("outputs", {}).get("scores", {}).get(timeframe, {})) != OUTPUT_KEYS:
            errors.append(f"V9.3 outputs.scores.{timeframe} keys mismatch")
        if set(manifest.get("outputs", {}).get("folds", {}).get(timeframe, {})) != OUTPUT_KEYS:
            errors.append(f"V9.3 outputs.folds.{timeframe} keys mismatch")
        if set(manifest.get("quality", {}).get(timeframe, {})) != QUALITY_KEYS:
            errors.append(f"V9.3 quality.{timeframe} keys mismatch")
    if set(manifest.get("findings", {})) != FINDINGS_KEYS:
        errors.append("V9.3 findings keys mismatch")
    if manifest.get("feature_leakage_scan", {}).get("forbidden_feature_columns_present"):
        errors.append("V9.3 feature leakage detected")
    if manifest.get("metric_forbidden_scan", {}).get("forbidden_terms_present"):
        errors.append("V9.3 forbidden metric terms detected")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    return [] if report == manifest else ["V9.3 report mismatch"]


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    expected = {
        "version": manifest.get("version"),
        "walk_forward_run_id": manifest.get("walk_forward_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
        "aggregate_metrics": manifest.get("aggregate_metrics"),
        "label_shuffle_falsification": manifest.get("label_shuffle_falsification"),
        "comparison_to_static_split_v9_2": manifest.get("comparison_to_static_split_v9_2"),
    }
    return [] if report == expected else ["V9.3 scores report mismatch"]


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [REPORT_MD_PATH_V9_3, SCORES_MD_PATH_V9_3, DOC_PATH_V9_3]:
        full = root / path
        if not full.exists():
            errors.append(f"missing V9.3 markdown: {path}")
            continue
        errors.extend(validate_markdown_forbidden_claims(full.read_text(encoding="utf-8"), f"V9.3 markdown {path}"))
    return errors


def _find_forbidden_v9_3_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in ["data/research/v9_3/backtests", "data/research/v9_3/strategies", "reports/backtests", "reports/strategies", "orders", "execution", "models", "checkpoints"]:
        if (root / relative).exists():
            errors.append(f"forbidden V9.3 artifact exists: {relative}")
    for path in root.rglob("*"):
        if any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"forbidden persistent model file exists: {path.relative_to(root)}")
    return errors


def _validate_findings(findings: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if findings.get(key) is not False:
            errors.append(f"V9.3 finding must be false: {key}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    return [] if safety == SAFETY_FLAGS_V9_3 else ["V9.3 safety flags mismatch"]


def _scan_metrics_for_forbidden_terms(payload: Any, label: str) -> list[str]:
    text = json.dumps(payload, sort_keys=True).casefold()
    present = sorted(term for term in FORBIDDEN_METRIC_TERMS_V9_3 if term in text)
    return [f"V9.3 forbidden metric terms in {label}: {present}"] if present else []


def _validate_metric_bounds(payload: Any, label: str) -> list[str]:
    errors: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"accuracy", "balanced_accuracy", "macro_f1", "mean_validation_accuracy", "mean_test_accuracy", "mean_test_macro_f1", "std_test_accuracy", "std_test_macro_f1", "min_test_accuracy", "max_test_accuracy", "original_accuracy", "original_macro_f1", "shuffled_accuracy", "shuffled_macro_f1"}:
                if value is not None and (not isinstance(value, int | float) or not 0 <= float(value) <= 1):
                    errors.append(f"V9.3 {label}.{key} out of bounds")
            elif isinstance(value, dict):
                errors.extend(_validate_metric_bounds(value, f"{label}.{key}"))
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
