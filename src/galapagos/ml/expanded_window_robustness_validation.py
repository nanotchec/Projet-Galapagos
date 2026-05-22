from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import MANIFEST_PATH_V3_8
from galapagos.ml.expanded_window_robustness import (
    ACCURACY_GAP_WARNING_THRESHOLD_V4_0,
    DOC_PATH_V4_0,
    EXPECTED_LIMITATIONS_V4_0,
    FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V4_0,
    LABEL_SHUFFLE_RANDOM_SEED_V4_0,
    MACRO_F1_GAP_WARNING_THRESHOLD_V4_0,
    MANIFEST_PATH_V4_0,
    REPORT_JSON_PATH_V4_0,
    REPORT_MD_PATH_V4_0,
    SAFETY_FLAGS_V4_0,
    VERSION_V4_0,
)
from galapagos.ml.schemas import MANIFEST_PATH_V3_9, TIMEFRAMES_V3_9, get_expanded_ml_score_path_v3_9
from galapagos.validation.safety import validate_exact_keys, validate_markdown_forbidden_claims


ROBUSTNESS_RUN_ID_PATTERN_V4_0 = re.compile(r"^v4_0_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V3_9)
PATH_SHA_KEYS = {"path", "sha256"}
SCORE_FILE_KEYS = {"path", "sha256", "rows"}
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "robustness_run_id",
    "input_dataset_manifest",
    "input_ml_manifest",
    "input_score_files",
    "analyses",
    "thresholds",
    "findings",
    "safety",
    "limitations",
}
ANALYSES_KEYS = {
    "baseline_delta",
    "split_stability",
    "timeframe_stability",
    "label_shuffle_falsification",
    "feature_leakage_scan",
    "metric_forbidden_scan",
}
THRESHOLD_KEYS = {"accuracy_gap_warning_threshold", "macro_f1_gap_warning_threshold", "random_seed"}
FINDINGS_KEYS = {
    "robust_edge_claimed",
    "strategy_validated",
    "backtest_performed",
    "actionable_signal_produced",
    "warnings",
}
FORBIDDEN_ARTIFACT_ROOTS = [
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
    Path("data/research/v4_0/backtests"),
    Path("data/research/v4_0/strategies"),
]
PERSISTENT_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
CLASSIFICATION_METRIC_SUFFIXES = (
    "accuracy",
    "balanced_accuracy",
    "macro_f1",
    "precision",
    "recall",
)
EXPLICIT_UNIT_METRIC_FIELDS = {
    "majority_class_baseline_accuracy",
    "majority_class_baseline_macro_f1",
    "random_seeded_baseline_accuracy",
    "random_seeded_baseline_macro_f1",
    "original_accuracy",
    "original_macro_f1",
    "shuffled_accuracy",
    "shuffled_macro_f1",
}
DELTA_GAP_RANGE_TERMS = ("delta", "gap", "range")
NON_NEGATIVE_PROBABILITY_FIELDS = {
    "probability_sum_max_abs_error",
    "probability_nan_count",
    "probability_inf_count",
}
EXPECTED_BOOL_FIELDS = {
    "train_test_accuracy_gap_gt_0_10",
    "train_test_macro_f1_gap_gt_0_10",
    "validation_test_accuracy_gap_gt_0_05",
    "validation_test_macro_f1_gap_gt_0_05",
    "learned_model_underperforms_majority_on_test",
    "learned_model_underperforms_random_on_test",
    "no_clear_edge_vs_shuffled_labels",
    "validation_test_contaminated",
    "single_timeframe_concentration_warning",
    "feature_leakage_detected",
    "metric_forbidden_terms_detected",
    "overfit_warning",
}
COUNT_FIELD_SUFFIXES = ("_rows", "_count", "_counts", "rows", "count")


def validate_expanded_ml_robustness_v4_0(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = project_root / MANIFEST_PATH_V4_0
    report_path = project_root / REPORT_JSON_PATH_V4_0
    if not manifest_path.exists():
        return _result([f"missing V4.0 manifest: {MANIFEST_PATH_V4_0}"], warnings)
    if not report_path.exists():
        return _result([f"missing V4.0 report: {REPORT_JSON_PATH_V4_0}"], warnings)

    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(_validate_metric_value_bounds(manifest.get("analyses", {})))
    errors.extend(_validate_report(manifest, report))
    errors.extend(_validate_input_hashes(project_root, manifest))
    errors.extend(_validate_score_files(project_root, manifest))
    errors.extend(_validate_findings(manifest.get("findings", {})))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    analyses_without_self_report = {
        key: value for key, value in manifest.get("analyses", {}).items() if key != "metric_forbidden_scan"
    }
    errors.extend(_scan_metrics_for_forbidden_terms(analyses_without_self_report))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v4_0_artifacts(project_root))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V4.0 manifest"))
    if manifest.get("version") != VERSION_V4_0:
        errors.append("V4.0 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V4.0 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V4.0 manifest created_at_utc invalid")
    if not isinstance(manifest.get("robustness_run_id"), str) or ROBUSTNESS_RUN_ID_PATTERN_V4_0.fullmatch(manifest["robustness_run_id"]) is None:
        errors.append("V4.0 robustness_run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("input_dataset_manifest", {}), PATH_SHA_KEYS, "V4.0 input_dataset_manifest"))
    errors.extend(validate_exact_keys(manifest.get("input_ml_manifest", {}), PATH_SHA_KEYS, "V4.0 input_ml_manifest"))
    errors.extend(validate_exact_keys(manifest.get("input_score_files", {}), TIMEFRAME_KEYS, "V4.0 input_score_files"))
    for timeframe in TIMEFRAMES_V3_9:
        errors.extend(validate_exact_keys(manifest.get("input_score_files", {}).get(timeframe, {}), SCORE_FILE_KEYS, f"V4.0 input_score_files.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("analyses", {}), ANALYSES_KEYS, "V4.0 analyses"))
    errors.extend(validate_exact_keys(manifest.get("thresholds", {}), THRESHOLD_KEYS, "V4.0 thresholds"))
    errors.extend(validate_exact_keys(manifest.get("findings", {}), FINDINGS_KEYS, "V4.0 findings"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), set(SAFETY_FLAGS_V4_0), "V4.0 safety"))
    if manifest.get("thresholds", {}).get("accuracy_gap_warning_threshold") != ACCURACY_GAP_WARNING_THRESHOLD_V4_0:
        errors.append("V4.0 accuracy threshold mismatch")
    if manifest.get("thresholds", {}).get("macro_f1_gap_warning_threshold") != MACRO_F1_GAP_WARNING_THRESHOLD_V4_0:
        errors.append("V4.0 macro F1 threshold mismatch")
    if manifest.get("thresholds", {}).get("random_seed") != LABEL_SHUFFLE_RANDOM_SEED_V4_0:
        errors.append("V4.0 random seed mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V4_0:
        errors.append("V4.0 limitations mismatch")
    analyses = manifest.get("analyses", {})
    for key in ANALYSES_KEYS:
        if not analyses.get(key):
            errors.append(f"V4.0 analysis missing or empty: {key}")
    feature_scan = analyses.get("feature_leakage_scan", {})
    if feature_scan.get("feature_leakage_detected") is not False:
        errors.append("V4.0 feature leakage scan failed")
    metric_scan = analyses.get("metric_forbidden_scan", {})
    if metric_scan.get("metric_forbidden_terms_detected") is not False:
        errors.append("V4.0 metric forbidden scan failed")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V4.0 report")
    if report != manifest:
        errors.append("V4.0 report JSON mismatch")
    return errors


def _validate_input_hashes(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_path_sha(root, manifest.get("input_dataset_manifest", {}), MANIFEST_PATH_V3_8, "V4.0 input_dataset_manifest"))
    errors.extend(_validate_path_sha(root, manifest.get("input_ml_manifest", {}), MANIFEST_PATH_V3_9, "V4.0 input_ml_manifest"))
    return errors


def _validate_score_files(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V3_9:
        expected_path = get_expanded_ml_score_path_v3_9(root, timeframe)
        block = manifest.get("input_score_files", {}).get(timeframe, {})
        if (root / Path(str(block.get("path", "")))).resolve() != expected_path.resolve():
            errors.append(f"V4.0 input_score_files.{timeframe}.path mismatch")
            continue
        if not expected_path.exists():
            errors.append(f"missing V4.0 input score file: {expected_path.relative_to(root)}")
            continue
        if block.get("sha256") != sha256_file(expected_path):
            errors.append(f"V4.0 input_score_files.{timeframe}.sha256 mismatch")
        scores = read_parquet(expected_path)
        if block.get("rows") != len(scores):
            errors.append(f"V4.0 input_score_files.{timeframe}.rows mismatch")
    return errors


def _validate_findings(findings: Any) -> list[str]:
    if not isinstance(findings, dict):
        return ["V4.0 findings must be object"]
    errors: list[str] = []
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced"]:
        if findings.get(key) is not False:
            errors.append(f"V4.0 finding {key} must be False")
    if not isinstance(findings.get("warnings"), list):
        errors.append("V4.0 findings warnings must be list")
    return errors


def _validate_safety(safety: Any) -> list[str]:
    if not isinstance(safety, dict):
        return ["V4.0 safety must be object"]
    return [f"V4.0 safety flag {key} must be {value}" for key, value in SAFETY_FLAGS_V4_0.items() if safety.get(key) is not value]


def _scan_metrics_for_forbidden_terms(payload: Any) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    return [f"V4.0 metrics contain forbidden trading metric: {term}" for term in FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V4_0 if term in text]


def _validate_metric_value_bounds(analyses: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _walk_metric_value_bounds(analyses, "analyses", errors)
    return errors


def _walk_metric_value_bounds(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            _validate_metric_field(key, child, child_path, errors)
            _walk_metric_value_bounds(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}.{index}"
            _walk_metric_value_bounds(child, child_path, errors)


def _validate_metric_field(field: str, value: Any, path: str, errors: list[str]) -> None:
    if field in EXPECTED_BOOL_FIELDS and not isinstance(value, bool):
        errors.append(f"V4.0 metric bound violation: {path} = {value}")
        return
    if isinstance(value, dict | list):
        return
    if field in {"probability_min", "probability_max"}:
        _validate_numeric_range(path, value, 0.0, 1.0, errors)
        return
    if field in NON_NEGATIVE_PROBABILITY_FIELDS:
        _validate_numeric_min(path, value, 0.0, errors)
        return
    if _contains_delta_gap_or_range(field):
        _validate_numeric_range(path, value, -1.0, 1.0, errors)
        return
    if field in EXPLICIT_UNIT_METRIC_FIELDS or _is_classification_metric_field(field):
        _validate_numeric_range(path, value, 0.0, 1.0, errors)
        return
    if _is_count_field(field) and _is_numeric_like(value):
        _validate_numeric_min(path, value, 0.0, errors)


def _is_classification_metric_field(field: str) -> bool:
    return any(field == suffix or field.endswith(f"_{suffix}") for suffix in CLASSIFICATION_METRIC_SUFFIXES)


def _contains_delta_gap_or_range(field: str) -> bool:
    return any(term in field for term in DELTA_GAP_RANGE_TERMS)


def _is_count_field(field: str) -> bool:
    return any(field == suffix or field.endswith(suffix) for suffix in COUNT_FIELD_SUFFIXES)


def _is_numeric_like(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _validate_numeric_range(path: str, value: Any, lower: float, upper: float, errors: list[str]) -> None:
    if not _is_finite_number(value) or not lower <= float(value) <= upper:
        errors.append(f"V4.0 metric bound violation: {path} = {value}")


def _validate_numeric_min(path: str, value: Any, lower: float, errors: list[str]) -> None:
    if not _is_finite_number(value) or float(value) < lower:
        errors.append(f"V4.0 metric bound violation: {path} = {value}")


def _is_finite_number(value: Any) -> bool:
    return _is_numeric_like(value) and math.isfinite(float(value))


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [(REPORT_MD_PATH_V4_0, "V4.0 Markdown report"), (DOC_PATH_V4_0, "V4.0 documentation")]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _find_forbidden_v4_0_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_ARTIFACT_ROOTS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V4.0 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V4.0 artifact detected: {child.relative_to(root).as_posix()}")
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in PERSISTENT_MODEL_SUFFIXES:
            errors.append(f"Forbidden V4.0 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _validate_path_sha(root: Path, block: dict[str, Any], expected_relative: Path, label: str) -> list[str]:
    path = root / expected_relative
    errors: list[str] = []
    if block.get("path") != expected_relative.as_posix():
        errors.append(f"{label}.path mismatch")
    if not path.exists():
        errors.append(f"missing {label}: {expected_relative}")
    elif block.get("sha256") != sha256_file(path):
        errors.append(f"{label}.sha256 mismatch")
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
