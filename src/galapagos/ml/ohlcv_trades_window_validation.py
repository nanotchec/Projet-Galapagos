from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import MANIFEST_PATH_V7_3
from galapagos.ml.ohlcv_trades_window import (
    input_dataset_path,
    input_split_path,
    build_comparison_to_references_v7_4,
    load_v7_3_dataset_manifest,
    prepare_ohlcv_trades_ml_frame_v7_4,
    score_output_path,
    validate_split_alignment_v7_4,
)
from galapagos.ml.ohlcv_trades_window_metrics import (
    compute_ohlcv_trades_classification_metrics_v7_4,
    compute_ohlcv_trades_walk_forward_metrics_v7_4,
)
from galapagos.ml.ohlcv_trades_window_quality import assess_ohlcv_trades_ml_quality_v7_4
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V7_4,
    DOC_PATH_V7_4,
    EXPECTED_LIMITATIONS_V7_4,
    FORBIDDEN_FEATURE_EXACT_V7_4,
    FORBIDDEN_FEATURE_PREFIXES_V7_4,
    FORBIDDEN_METRIC_TERMS_V7_4,
    FORBIDDEN_OUTPUT_COLUMNS_EXACT_V7_4,
    MANIFEST_PATH_V7_4,
    ML_SCHEMA_VERSION_V7_4,
    ML_SCORE_COLUMNS_V7_4,
    MODEL_NAMES_V7_4,
    REPORT_JSON_PATH_V7_4,
    REPORT_MD_PATH_V7_4,
    SAFETY_FLAGS_V7_4,
    SCORES_JSON_PATH_V7_4,
    SCORES_MD_PATH_V7_4,
    TARGET_NAME_V7_4,
    TIMEFRAMES_V7_4,
    VERSION_V7_4,
    get_feature_columns_sha256_v7_4,
)
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


ML_RUN_ID_PATTERN_V7_4 = re.compile(r"^v7_4_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V7_4)
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
    "comparison_to_references",
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
SANITY_KEYS = {
    "train_rows",
    "validation_rows",
    "test_rows",
    "target_classes_seen_train",
    "target_classes_seen_validation",
    "target_classes_seen_test",
    "no_shuffle_confirmed",
    "forbidden_feature_columns_present",
    "forbidden_output_columns_present",
}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def validate_ohlcv_trades_offline_ml_research_v7_4(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    dataset_validation = _validate_v7_3_dataset_layer(project_root)
    if dataset_validation:
        return _result(dataset_validation, warnings)

    manifest_path = project_root / MANIFEST_PATH_V7_4
    report_path = project_root / REPORT_JSON_PATH_V7_4
    scores_json_path = project_root / SCORES_JSON_PATH_V7_4
    if not manifest_path.exists():
        return _result([f"missing V7.4 manifest: {MANIFEST_PATH_V7_4}"], warnings)
    if not report_path.exists():
        return _result([f"missing V7.4 quality report: {REPORT_JSON_PATH_V7_4}"], warnings)
    if not scores_json_path.exists():
        return _result([f"missing V7.4 scores report: {SCORES_JSON_PATH_V7_4}"], warnings)

    dataset_manifest = load_v7_3_dataset_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_json_path)
    errors.extend(_validate_manifest_structure(project_root, manifest, dataset_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V7.4 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V7.4 quality report"))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(scan_payload_for_forbidden_claims(scores_report, "V7.4 scores report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v7_4_artifacts(project_root))

    if errors:
        return _result(errors, warnings, manifest)

    physical_quality: dict[str, dict[str, Any]] = {}
    recomputed_metrics: dict[str, Any] = {}
    recomputed_walk_forward_metrics: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V7_4:
        errors.extend(_validate_timeframe(project_root, manifest, dataset_manifest, timeframe, physical_quality, recomputed_metrics, recomputed_walk_forward_metrics))
    if recomputed_metrics != manifest.get("metrics"):
        errors.append("V7.4 manifest metrics mismatch")
    if recomputed_walk_forward_metrics != manifest.get("walk_forward_metrics"):
        errors.append("V7.4 manifest walk_forward_metrics mismatch")
    errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {}), "metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("walk_forward_metrics", {}), "walk_forward_metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("comparison_to_references", {}), "comparison_to_references"))
    errors.extend(_validate_metric_bounds(manifest.get("metrics", {}), "metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("walk_forward_metrics", {}), "walk_forward_metrics"))
    errors.extend(_validate_comparison_bounds(manifest.get("comparison_to_references", {})))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any], dataset_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V7.4 manifest"))
    if manifest.get("version") != VERSION_V7_4:
        errors.append("V7.4 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V7.4 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V7.4 manifest created_at_utc invalid")
    if not isinstance(manifest.get("ml_run_id"), str) or ML_RUN_ID_PATTERN_V7_4.fullmatch(manifest["ml_run_id"]) is None:
        errors.append("V7.4 manifest ml_run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("input_dataset_manifest", {}), INPUT_MANIFEST_KEYS, "V7.4 manifest input_dataset_manifest"))
    expected_window = dataset_manifest["input_features_manifest"]
    input_manifest = manifest.get("input_dataset_manifest", {})
    if input_manifest.get("path") != MANIFEST_PATH_V7_3.as_posix():
        errors.append("V7.4 input_dataset_manifest.path mismatch")
    if input_manifest.get("sha256") != sha256_file(root / MANIFEST_PATH_V7_3):
        errors.append("V7.4 input_dataset_manifest.sha256 mismatch")
    for key in ["window_start", "window_end", "total_days"]:
        if input_manifest.get(key) != expected_window.get(key):
            errors.append(f"V7.4 input_dataset_manifest.{key} mismatch")
    if input_manifest.get("feature_columns_count") != dataset_manifest.get("feature_columns_count"):
        errors.append("V7.4 input_dataset_manifest.feature_columns_count mismatch")
    if manifest.get("feature_columns_count") != len(ALLOWED_FEATURE_COLUMNS_V7_4):
        errors.append("V7.4 feature_columns_count mismatch")
    if manifest.get("target_name") != TARGET_NAME_V7_4:
        errors.append("V7.4 target_name mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V7_4:
        errors.append("V7.4 feature_columns mismatch")
    errors.extend(_validate_feature_columns(manifest.get("feature_columns", [])))
    if manifest.get("models") != MODEL_NAMES_V7_4:
        errors.append("V7.4 models mismatch")
    expected_comparison = build_comparison_to_references_v7_4(root, manifest.get("metrics", {}))
    if manifest.get("comparison_to_references") != expected_comparison:
        errors.append("V7.4 comparison_to_references mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V7_4:
        errors.append("V7.4 limitations mismatch")
    for section in ["input_datasets", "input_splits", "outputs", "quality", "sanity_checks"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V7.4 manifest {section}"))
    for timeframe in TIMEFRAMES_V7_4:
        errors.extend(validate_exact_keys(manifest.get("input_datasets", {}).get(timeframe, {}), INPUT_KEYS, f"V7.4 manifest input_datasets.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_splits", {}).get(timeframe, {}), INPUT_KEYS, f"V7.4 manifest input_splits.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V7.4 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("quality", {}).get(timeframe, {}), QUALITY_KEYS, f"V7.4 manifest quality.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("sanity_checks", {}).get(timeframe, {}), SANITY_KEYS, f"V7.4 manifest sanity_checks.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), set(SAFETY_FLAGS_V7_4), "V7.4 manifest safety"))
    return errors


def _validate_feature_columns(columns: Any) -> list[str]:
    if not isinstance(columns, list):
        return ["V7.4 feature_columns must be list"]
    forbidden_exact = {column.casefold() for column in FORBIDDEN_FEATURE_EXACT_V7_4}
    forbidden_prefixes = tuple(prefix.casefold() for prefix in FORBIDDEN_FEATURE_PREFIXES_V7_4)
    forbidden = []
    for column in columns:
        if not isinstance(column, str):
            forbidden.append(column)
            continue
        folded = column.casefold()
        if folded in forbidden_exact or folded.startswith(forbidden_prefixes):
            forbidden.append(column)
    return [f"V7.4 forbidden feature columns: {forbidden}"] if forbidden else []


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V7.4 quality report")
    if report != manifest:
        errors.append("V7.4 quality report mismatch")
    return errors


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(
        report,
        {"version", "ml_run_id", "outputs", "metrics", "walk_forward_metrics", "comparison_to_references"},
        "V7.4 scores report",
    )
    expected = {
        "version": manifest.get("version"),
        "ml_run_id": manifest.get("ml_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
        "walk_forward_metrics": manifest.get("walk_forward_metrics"),
        "comparison_to_references": manifest.get("comparison_to_references"),
    }
    if report != expected:
        errors.append("V7.4 scores report mismatch")
    return errors


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
    window = dataset_manifest["input_features_manifest"]
    dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
    split_path = input_split_path(root, timeframe, dataset_manifest)
    score_path = score_output_path(root, timeframe, window["window_start"], window["window_end"])
    for label, path in [("dataset", dataset_path), ("split", split_path), ("scores", score_path)]:
        if not path.exists():
            errors.append(f"missing V7.4 {label} file for {timeframe}: {path.relative_to(root)}")
    if errors:
        return errors

    dataset = read_parquet(dataset_path)
    split = read_parquet(split_path)
    dataset_for_ml = validate_split_alignment_v7_4(dataset, split)
    scores = read_parquet(score_path)
    dataset_sha = sha256_file(dataset_path)
    errors.extend(_compare_input_block(manifest["input_datasets"][timeframe], dataset_path, dataset_sha, len(dataset), root, f"V7.4 manifest input_datasets.{timeframe}"))
    errors.extend(_compare_input_block(manifest["input_splits"][timeframe], split_path, sha256_file(split_path), len(split), root, f"V7.4 manifest input_splits.{timeframe}"))
    errors.extend(_compare_output_block(manifest["outputs"][timeframe], score_path, sha256_file(score_path), len(scores), root, f"V7.4 manifest outputs.{timeframe}"))
    errors.extend(_validate_score_frame_schema_only(scores, timeframe))
    errors.extend(_validate_score_values(dataset_for_ml, scores, timeframe, dataset_sha))
    quality = assess_ohlcv_trades_ml_quality_v7_4(dataset_for_ml, scores, timeframe)
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    recomputed_metrics.update(compute_ohlcv_trades_classification_metrics_v7_4(scores))
    recomputed_walk_forward_metrics.update(compute_ohlcv_trades_walk_forward_metrics_v7_4(scores))
    return errors


def _validate_score_frame_schema_only(scores: pd.DataFrame, timeframe: str = "") -> list[str]:
    errors: list[str] = []
    label = f" for {timeframe}" if timeframe else ""
    if list(scores.columns) != ML_SCORE_COLUMNS_V7_4:
        errors.append(f"V7.4 score schema mismatch{label}")
    forbidden_output = [
        column for column in scores.columns if str(column).casefold() in {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_EXACT_V7_4}
    ]
    if forbidden_output:
        errors.append(f"V7.4 score forbidden columns{label}: {forbidden_output}")
    if "walk_forward_group" not in scores.columns:
        errors.append(f"V7.4 score walk_forward_group missing{label}")
    if {"prediction_available_ts", "decision_ts"}.issubset(scores.columns) and not scores["prediction_available_ts"].ge(scores["decision_ts"]).all():
        errors.append(f"V7.4 prediction_available_ts invalid{label}")
    if len(scores) > 0:
        if "model_name" in scores.columns and set(scores["model_name"].unique()) != set(MODEL_NAMES_V7_4):
            errors.append(f"V7.4 score models mismatch{label}")
        if "target_name" in scores.columns and set(scores["target_name"].unique()) != {TARGET_NAME_V7_4}:
            errors.append(f"V7.4 score target mismatch{label}")
        if "feature_columns_sha256" in scores.columns and set(scores["feature_columns_sha256"].unique()) != {get_feature_columns_sha256_v7_4()}:
            errors.append(f"V7.4 score feature_columns_sha256 mismatch{label}")
        if "ml_schema_version" in scores.columns and set(scores["ml_schema_version"].unique()) != {ML_SCHEMA_VERSION_V7_4}:
            errors.append(f"V7.4 score schema version mismatch{label}")
    return errors


def _validate_score_values(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str, dataset_sha: str) -> list[str]:
    errors: list[str] = []
    used = prepare_ohlcv_trades_ml_frame_v7_4(dataset)
    expected_rows = len(used) * len(MODEL_NAMES_V7_4)
    if len(scores) != expected_rows:
        errors.append(f"V7.4 score row count mismatch for {timeframe}")
    if len(scores) and set(scores["dataset_sha256"].unique()) != {dataset_sha}:
        errors.append(f"V7.4 score dataset_sha256 mismatch for {timeframe}")
    if len(scores) and not scores["row_valid_for_ml"].eq(True).all():
        errors.append(f"V7.4 score row_valid_for_ml mismatch for {timeframe}")
    if len(scores) and set(scores["target_value"].dropna().astype(str).unique()) - {"DOWN", "FLAT", "UP"}:
        errors.append(f"V7.4 score target classes invalid for {timeframe}")
    if len(scores) and scores["walk_forward_group"].isna().any():
        errors.append(f"V7.4 score walk_forward_group null for {timeframe}")
    if len(scores):
        expected_groups = set(used["walk_forward_group"].dropna().astype(str).unique())
        score_groups = set(scores["walk_forward_group"].dropna().astype(str).unique())
        if not score_groups.issubset(expected_groups):
            errors.append(f"V7.4 score walk_forward_group unexpected for {timeframe}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        if manifest["quality"].get(timeframe) != quality:
            errors.append(f"V7.4 manifest quality mismatch for {timeframe}")
    return errors


def _validate_safety(safety: Any) -> list[str]:
    if not isinstance(safety, dict):
        return ["V7.4 manifest safety must be object"]
    return [f"V7.4 safety flag {key} must be {value}" for key, value in SAFETY_FLAGS_V7_4.items() if safety.get(key) is not value]


def _find_forbidden_v7_4_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_roots = [
        Path("models"),
        Path("checkpoints"),
        Path("reports/backtests"),
        Path("reports/strategies"),
        Path("reports/signals"),
        Path("reports/predictions"),
        Path("reports/orders"),
        Path("reports/execution"),
        Path("orders"),
        Path("execution"),
        Path("data/research/v7_4/backtests"),
        Path("data/research/v7_4/strategies"),
        Path("data/research/v7_4/orders"),
    ]
    allowed_reports = {
        REPORT_JSON_PATH_V7_4,
        REPORT_MD_PATH_V7_4,
        SCORES_JSON_PATH_V7_4,
        SCORES_MD_PATH_V7_4,
    }
    for relative in forbidden_roots:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V7.4 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V7.4 artifact detected: {child.relative_to(root).as_posix()}")

    data_v7_4_ml = root / "data/research/v7_4/ml"
    if data_v7_4_ml.exists():
        for child in sorted(data_v7_4_ml.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(root)
            if _is_allowed_v7_4_ml_score_path(relative):
                continue
            errors.append(f"Forbidden V7.4 artifact detected: {relative.as_posix()}")

    reports_ml = root / "reports/ml"
    if reports_ml.exists():
        for child in sorted(reports_ml.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(root)
            if relative in allowed_reports:
                continue
            if child.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
                errors.append(f"Forbidden V7.4 artifact detected: {relative.as_posix()}")

    for path in root.rglob("*"):
        if any(part in IGNORED_SCAN_PARTS for part in path.parts) or not path.is_file():
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V7.4 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _is_allowed_v7_4_ml_score_path(relative: Path) -> bool:
    parts = relative.parts
    return (
        len(parts) == 11
        and parts[0] == "data"
        and parts[1] == "research"
        and parts[2] == "v7_4"
        and parts[3] == "ml"
        and parts[4] == "offline_research_ohlcv_trades"
        and parts[5] == "source=binance_archive"
        and parts[6] == "market_type=spot"
        and parts[7] == "symbol=BTCUSDT"
        and parts[8] in {f"timeframe={timeframe}" for timeframe in TIMEFRAMES_V7_4}
        and parts[9].startswith("window=")
        and parts[10] == "ml-scores.parquet"
    )


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [
        (REPORT_MD_PATH_V7_4, "V7.4 Markdown report"),
        (SCORES_MD_PATH_V7_4, "V7.4 scores Markdown"),
        (DOC_PATH_V7_4, "V7.4 documentation"),
    ]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _scan_metrics_for_forbidden_terms(metrics: Any, label: str) -> list[str]:
    text = json.dumps(metrics, ensure_ascii=False).casefold()
    return [f"V7.4 {label} contain forbidden trading metric: {term}" for term in FORBIDDEN_METRIC_TERMS_V7_4 if term in text]


def _validate_metric_bounds(metrics: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(metrics, dict):
        return [f"V7.4 {label} must be object"]
    bounded_names = {"accuracy", "balanced_accuracy", "macro_f1"}
    per_class_names = {"per_class_precision", "per_class_recall"}
    for metric_key, payload in metrics.items():
        if not isinstance(payload, dict):
            errors.append(f"V7.4 {label}.{metric_key} must be object")
            continue
        for name in bounded_names:
            value = payload.get(name)
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                errors.append(f"V7.4 {label}.{metric_key}.{name} out of bounds")
        for name in per_class_names:
            values = payload.get(name, {})
            if values and any(not isinstance(value, (int, float)) or not 0 <= float(value) <= 1 for value in values.values()):
                errors.append(f"V7.4 {label}.{metric_key}.{name} out of bounds")
        rows = payload.get("rows")
        if not isinstance(rows, int) or rows < 0:
            errors.append(f"V7.4 {label}.{metric_key}.rows invalid")
    return errors


def _validate_comparison_bounds(comparison: Any) -> list[str]:
    if not isinstance(comparison, dict):
        return ["V7.4 comparison_to_references must be object"]
    errors: list[str] = []
    delta_names = {
        "accuracy_delta_v7_4_minus_reference",
        "balanced_accuracy_delta_v7_4_minus_reference",
        "macro_f1_delta_v7_4_minus_reference",
    }
    for reference_name, reference_payload in comparison.items():
        if not isinstance(reference_payload, dict):
            errors.append(f"V7.4 comparison_to_references.{reference_name} must be object")
            continue
        comparisons = reference_payload.get("comparisons", {})
        if not isinstance(comparisons, dict):
            errors.append(f"V7.4 comparison_to_references.{reference_name}.comparisons must be object")
            continue
        for key, payload in comparisons.items():
            if not isinstance(payload, dict):
                errors.append(f"V7.4 comparison_to_references.{reference_name}.{key} must be object")
                continue
            for name in delta_names:
                value = payload.get(name)
                if value is not None and (not isinstance(value, (int, float)) or not -1 <= float(value) <= 1):
                    errors.append(f"V7.4 comparison_to_references.{reference_name}.{key}.{name} out of bounds")
    return errors


def _validate_v7_3_dataset_layer(root: Path) -> list[str]:
    from galapagos.datasets.ohlcv_trades_window_validation import validate_ohlcv_trades_offline_supervised_dataset_v7_3

    result = validate_ohlcv_trades_offline_supervised_dataset_v7_3(root)
    if result["passed"]:
        return []
    return [f"V7.3 dataset validation failed before V7.4: {result['errors']}"]


def _compare_input_block(block: dict[str, Any], path: Path, sha256: str, rows: int, root: Path, label: str) -> list[str]:
    errors: list[str] = []
    if (root / Path(str(block.get("path", "")))).resolve() != path.resolve():
        errors.append(f"{label}.path mismatch")
    if block.get("sha256") != sha256:
        errors.append(f"{label}.sha256 mismatch")
    if block.get("rows") != rows:
        errors.append(f"{label}.rows mismatch")
    return errors


def _compare_output_block(block: dict[str, Any], path: Path, sha256: str, rows: int, root: Path, label: str) -> list[str]:
    errors = _compare_input_block(block, path, sha256, rows, root, label)
    if block.get("bytes") != path.stat().st_size:
        errors.append(f"{label}.bytes mismatch")
    if block.get("format") != "parquet":
        errors.append(f"{label}.format mismatch")
    return errors


def _is_iso_utc(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z") or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
