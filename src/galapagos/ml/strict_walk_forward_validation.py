from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.datasets.schemas import MANIFEST_PATH_V8_4
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_7,
    DOC_PATH_V8_7,
    EXPECTED_LIMITATIONS_V8_7,
    FORBIDDEN_FEATURE_EXACT_V8_7,
    FORBIDDEN_FEATURE_PREFIXES_V8_7,
    FORBIDDEN_METRIC_TERMS_V8_7,
    FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_7,
    MANIFEST_PATH_V8_7,
    ML_SCORE_COLUMNS_V8_7,
    MODEL_NAMES_V8_7,
    REPORT_JSON_PATH_V8_7,
    REPORT_MD_PATH_V8_7,
    SAFETY_FLAGS_V8_7,
    SCORES_JSON_PATH_V8_7,
    SCORES_MD_PATH_V8_7,
    TARGET_NAME_V8_7,
    TIMEFRAMES_V8_7,
    VERSION_V8_7,
    WALK_FORWARD_FOLD_COLUMNS_V8_7,
    get_feature_columns_sha256_v8_7,
)
from galapagos.ml.strict_walk_forward import (
    WALK_FORWARD_POLICY_V8_7,
    compare_to_static_split_v8_5,
    folds_output_path,
    input_dataset_path,
    load_v8_4_dataset_manifest,
    scan_strict_walk_forward_feature_leakage_v8_7,
    score_output_path,
)
from galapagos.ml.strict_walk_forward_metrics import (
    compute_strict_walk_forward_aggregate_metrics_v8_7,
    compute_strict_walk_forward_metrics_v8_7,
)
from galapagos.ml.strict_walk_forward_quality import assess_strict_walk_forward_quality_v8_7
from galapagos.validation.safety import validate_exact_keys, validate_markdown_forbidden_claims


RUN_ID_PATTERN_V8_7 = re.compile(r"^v8_7_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V8_7)
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
    "comparison_to_static_split_v8_5",
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
    "comparison_to_static_split_v8_5",
}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def validate_strict_walk_forward_validation_v8_7(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    warnings: list[str] = []
    dataset_errors = _validate_v8_4_dataset_layer(root)
    if dataset_errors:
        return _result(dataset_errors, warnings)

    manifest_path = root / MANIFEST_PATH_V8_7
    report_path = root / REPORT_JSON_PATH_V8_7
    scores_report_path = root / SCORES_JSON_PATH_V8_7
    if not manifest_path.exists():
        return _result([f"missing V8.7 manifest: {MANIFEST_PATH_V8_7}"], warnings)
    if not report_path.exists():
        return _result([f"missing V8.7 report: {REPORT_JSON_PATH_V8_7}"], warnings)
    if not scores_report_path.exists():
        return _result([f"missing V8.7 scores report: {SCORES_JSON_PATH_V8_7}"], warnings)

    dataset_manifest = load_v8_4_dataset_manifest(root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_report_path)
    errors: list[str] = []
    errors.extend(_validate_manifest_structure(root, manifest, dataset_manifest))
    errors.extend(_validate_report(manifest, report))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v8_7_artifacts(root))
    if errors:
        return _result(errors, warnings, manifest)

    recomputed_metrics: dict[str, Any] = {}
    recomputed_aggregate: dict[str, Any] = {}
    physical_quality: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V8_7:
        errors.extend(_validate_timeframe(root, manifest, dataset_manifest, timeframe, recomputed_metrics, recomputed_aggregate, physical_quality))
    if recomputed_metrics != manifest.get("metrics"):
        errors.append("V8.7 metrics mismatch")
    if recomputed_aggregate != manifest.get("aggregate_metrics"):
        errors.append("V8.7 aggregate_metrics mismatch")
    if compare_to_static_split_v8_5(root, manifest.get("aggregate_metrics", {})) != manifest.get("comparison_to_static_split_v8_5"):
        errors.append("V8.7 comparison_to_static_split_v8_5 mismatch")
    if scan_strict_walk_forward_feature_leakage_v8_7(manifest.get("feature_columns", [])) != manifest.get("feature_leakage_scan"):
        errors.append("V8.7 feature_leakage_scan mismatch")
    errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_findings(manifest.get("findings", {})))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {}), "metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("aggregate_metrics", {}), "aggregate_metrics"))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("label_shuffle_falsification", {}), "label_shuffle_falsification"))
    errors.extend(_validate_metric_bounds(manifest.get("metrics", {}), "metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("aggregate_metrics", {}), "aggregate_metrics"))
    errors.extend(_validate_metric_bounds(manifest.get("label_shuffle_falsification", {}), "label_shuffle_falsification"))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any], dataset_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V8.7 manifest"))
    if manifest.get("version") != VERSION_V8_7:
        errors.append("V8.7 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V8.7 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V8.7 manifest created_at_utc invalid")
    if not isinstance(manifest.get("walk_forward_run_id"), str) or RUN_ID_PATTERN_V8_7.fullmatch(manifest["walk_forward_run_id"]) is None:
        errors.append("V8.7 walk_forward_run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("input_dataset_manifest", {}), INPUT_MANIFEST_KEYS, "V8.7 input_dataset_manifest"))
    expected_window = dataset_manifest["input_features_manifest"]
    input_manifest = manifest.get("input_dataset_manifest", {})
    if input_manifest.get("path") != MANIFEST_PATH_V8_4.as_posix():
        errors.append("V8.7 input_dataset_manifest.path mismatch")
    if input_manifest.get("sha256") != sha256_file(root / MANIFEST_PATH_V8_4):
        errors.append("V8.7 input_dataset_manifest.sha256 mismatch")
    for key in ["window_start", "window_end", "total_days"]:
        if input_manifest.get(key) != expected_window.get(key):
            errors.append(f"V8.7 input_dataset_manifest.{key} mismatch")
    if input_manifest.get("feature_columns_count") != dataset_manifest.get("feature_columns_count"):
        errors.append("V8.7 input_dataset_manifest.feature_columns_count mismatch")
    if manifest.get("walk_forward_policy") != WALK_FORWARD_POLICY_V8_7:
        errors.append("V8.7 walk_forward_policy mismatch")
    if manifest.get("target_name") != TARGET_NAME_V8_7:
        errors.append("V8.7 target_name mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V8_7:
        errors.append("V8.7 feature_columns mismatch")
    if manifest.get("feature_columns_count") != len(ALLOWED_FEATURE_COLUMNS_V8_7):
        errors.append("V8.7 feature_columns_count mismatch")
    errors.extend(_validate_feature_columns(manifest.get("feature_columns", [])))
    if manifest.get("models") != MODEL_NAMES_V8_7:
        errors.append("V8.7 models mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V8_7:
        errors.append("V8.7 limitations mismatch")
    for section in ["input_datasets", "folds", "quality"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V8.7 manifest {section}"))
    errors.extend(validate_exact_keys(manifest.get("outputs", {}), OUTPUT_SECTION_KEYS, "V8.7 outputs"))
    for output_section in ["scores", "folds"]:
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(output_section, {}), TIMEFRAME_KEYS, f"V8.7 outputs.{output_section}"))
    for timeframe in TIMEFRAMES_V8_7:
        errors.extend(validate_exact_keys(manifest.get("input_datasets", {}).get(timeframe, {}), INPUT_KEYS, f"V8.7 input_datasets.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get("scores", {}).get(timeframe, {}), OUTPUT_KEYS, f"V8.7 outputs.scores.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get("folds", {}).get(timeframe, {}), OUTPUT_KEYS, f"V8.7 outputs.folds.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("quality", {}).get(timeframe, {}), QUALITY_KEYS, f"V8.7 quality.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("findings", {}), FINDINGS_KEYS, "V8.7 findings"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), set(SAFETY_FLAGS_V8_7), "V8.7 safety"))
    if manifest.get("feature_leakage_scan", {}).get("forbidden_feature_columns_present"):
        errors.append("V8.7 feature leakage detected")
    if manifest.get("metric_forbidden_scan", {}).get("forbidden_terms_present"):
        errors.append("V8.7 forbidden metric terms detected")
    return errors


def _validate_feature_columns(columns: Any) -> list[str]:
    if not isinstance(columns, list):
        return ["V8.7 feature_columns must be list"]
    exact = {term.casefold() for term in FORBIDDEN_FEATURE_EXACT_V8_7}
    prefixes = tuple(term.casefold() for term in FORBIDDEN_FEATURE_PREFIXES_V8_7)
    forbidden = []
    for column in columns:
        folded = str(column).casefold()
        if folded in exact or folded.startswith(prefixes):
            forbidden.append(str(column))
    return [f"V8.7 forbidden feature columns: {forbidden}"] if forbidden else []


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V8.7 report")
    if report != manifest:
        errors.append("V8.7 report mismatch")
    return errors


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, SCORES_REPORT_KEYS, "V8.7 scores report")
    expected = {
        "version": manifest.get("version"),
        "walk_forward_run_id": manifest.get("walk_forward_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
        "aggregate_metrics": manifest.get("aggregate_metrics"),
        "label_shuffle_falsification": manifest.get("label_shuffle_falsification"),
        "comparison_to_static_split_v8_5": manifest.get("comparison_to_static_split_v8_5"),
    }
    if report != expected:
        errors.append("V8.7 scores report mismatch")
    return errors


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
    window = manifest["input_dataset_manifest"]
    dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
    score_path = score_output_path(root, timeframe, window["window_start"], window["window_end"])
    fold_path = folds_output_path(root, timeframe, window["window_start"], window["window_end"])
    if not dataset_path.exists():
        errors.append(f"V8.7 missing input dataset for {timeframe}: {dataset_path}")
        return errors
    if not score_path.exists():
        errors.append(f"V8.7 missing score file for {timeframe}: {score_path}")
        return errors
    if not fold_path.exists():
        errors.append(f"V8.7 missing folds file for {timeframe}: {fold_path}")
        return errors
    dataset = read_parquet(dataset_path)
    scores = read_parquet(score_path)
    folds = read_parquet(fold_path)
    errors.extend(_validate_score_frame_schema_only(scores, timeframe))
    errors.extend(_validate_folds_frame_schema_only(folds, timeframe))
    errors.extend(_validate_folds_temporal_order(folds, timeframe))
    expected_score = manifest["outputs"]["scores"][timeframe]
    expected_folds = manifest["outputs"]["folds"][timeframe]
    errors.extend(_validate_output_block(root, score_path, scores, expected_score, f"V8.7 scores {timeframe}"))
    errors.extend(_validate_output_block(root, fold_path, folds, expected_folds, f"V8.7 folds {timeframe}"))
    if manifest["input_datasets"][timeframe]["sha256"] != sha256_file(dataset_path):
        errors.append(f"V8.7 input dataset sha256 mismatch for {timeframe}")
    if scores["dataset_sha256"].nunique() != 1 or scores["dataset_sha256"].iloc[0] != sha256_file(dataset_path):
        errors.append(f"V8.7 score dataset_sha256 mismatch for {timeframe}")
    if scores["feature_columns_sha256"].nunique() != 1 or scores["feature_columns_sha256"].iloc[0] != get_feature_columns_sha256_v8_7():
        errors.append(f"V8.7 score feature_columns_sha256 mismatch for {timeframe}")
    if scores["target_name"].nunique() != 1 or scores["target_name"].iloc[0] != TARGET_NAME_V8_7:
        errors.append(f"V8.7 target_name mismatch in scores for {timeframe}")
    if sorted(scores["model_name"].unique().tolist()) != sorted(MODEL_NAMES_V8_7):
        errors.append(f"V8.7 model set mismatch for {timeframe}")
    if pd.to_datetime(scores["prediction_available_ts"], utc=True).lt(pd.to_datetime(scores["decision_ts"], utc=True)).any():
        errors.append(f"V8.7 prediction_available_ts before decision_ts for {timeframe}")
    fold_metrics = compute_strict_walk_forward_metrics_v8_7(scores)
    recomputed_metrics.update(fold_metrics)
    recomputed_aggregate.update(compute_strict_walk_forward_aggregate_metrics_v8_7(fold_metrics))
    physical_quality[timeframe] = assess_strict_walk_forward_quality_v8_7(dataset, folds, scores, timeframe)
    return errors


def _validate_score_frame_schema_only(scores: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V8_7:
        errors.append(f"V8.7 score schema mismatch for {timeframe}")
    forbidden = [column for column in scores.columns if column.casefold() in {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_7}]
    if forbidden:
        errors.append(f"V8.7 score forbidden columns for {timeframe}: {forbidden}")
    if "fold_id" not in scores.columns or "fold_role" not in scores.columns:
        errors.append(f"V8.7 score fold columns missing for {timeframe}")
    return errors


def _validate_folds_frame_schema_only(folds: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    if list(folds.columns) != WALK_FORWARD_FOLD_COLUMNS_V8_7:
        errors.append(f"V8.7 folds schema mismatch for {timeframe}")
    return errors


def _validate_folds_temporal_order(folds: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    if folds.empty:
        return [f"V8.7 folds empty for {timeframe}"]
    for fold_id, group in folds.groupby("fold_id", sort=True):
        ranges: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            if role_group.empty:
                errors.append(f"V8.7 missing {role} rows in {fold_id} for {timeframe}")
                continue
            timestamps = pd.to_datetime(role_group["event_ts"], utc=True)
            ranges[role] = (timestamps.min(), timestamps.max())
        if set(ranges) == {"train", "validation", "test"}:
            if not (ranges["train"][1] < ranges["validation"][0]):
                errors.append(f"V8.7 fold validation before train for {fold_id} {timeframe}")
            if not (ranges["validation"][1] < ranges["test"][0]):
                errors.append(f"V8.7 fold test before validation for {fold_id} {timeframe}")
        if int(group["is_purged"].sum()) <= 0 or int(group["is_embargoed"].sum()) <= 0:
            errors.append(f"V8.7 purge/embargo missing for {fold_id} {timeframe}")
    return errors


def _validate_output_block(root: Path, path: Path, frame: pd.DataFrame, expected: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    if expected.get("path") != str(path.relative_to(root)):
        errors.append(f"{label} path mismatch")
    if expected.get("sha256") != sha256_file(path):
        errors.append(f"{label} sha256 mismatch")
    if expected.get("bytes") != path.stat().st_size:
        errors.append(f"{label} bytes mismatch")
    if expected.get("rows") != len(frame):
        errors.append(f"{label} rows mismatch")
    if expected.get("format") != "parquet":
        errors.append(f"{label} format mismatch")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, Any]) -> list[str]:
    return ["V8.7 quality mismatch"] if manifest.get("quality") != physical_quality else []


def _validate_findings(findings: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in [
        "robust_edge_claimed",
        "strategy_validated",
        "backtest_performed",
        "actionable_signal_produced",
        "walk_forward_validated_for_trading",
    ]:
        if findings.get(key) is not False:
            errors.append(f"V8.7 finding {key} must be False")
    if not isinstance(findings.get("warnings"), list):
        errors.append("V8.7 findings warnings must be list")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety != SAFETY_FLAGS_V8_7:
        errors.append("V8.7 safety flags mismatch")
    for key in ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
        if safety.get(key) is not False:
            errors.append(f"V8.7 safety flag {key} must be False")
    return errors


def _scan_metrics_for_forbidden_terms(payload: Any, section: str = "metrics") -> list[str]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    return [f"V8.7 {section} contain forbidden trading metric: {term}" for term in FORBIDDEN_METRIC_TERMS_V8_7 if term in text]


def _validate_metric_bounds(payload: Any, section: str) -> list[str]:
    errors: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
            return
        if not isinstance(value, (int, float)):
            return
        name = path.casefold()
        if any(term in name for term in ["gap", "delta", "range"]):
            if not -1.0 <= float(value) <= 1.0:
                errors.append(f"V8.7 metric bound violation in {section}: {path}={value}")
            return
        if any(term in name for term in ["accuracy", "f1", "precision", "recall", "balanced_accuracy"]):
            if not 0.0 <= float(value) <= 1.0:
                errors.append(f"V8.7 metric bound violation in {section}: {path}={value}")
        if any(term in name for term in ["rows", "count"]):
            if float(value) < 0:
                errors.append(f"V8.7 count bound violation in {section}: {path}={value}")

    walk(payload, section)
    return errors


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in [REPORT_MD_PATH_V8_7, SCORES_MD_PATH_V8_7, DOC_PATH_V8_7]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing V8.7 markdown: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(validate_markdown_forbidden_claims(text, f"V8.7 markdown {relative}"))
        folded = text.casefold()
        for claim in ["strategy validated", "tradable edge confirmed", "live trading ready"]:
            if claim in folded:
                errors.append(f"V8.7 markdown {relative} contains forbidden claim: {claim}")
    return errors


def _find_forbidden_v8_7_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_prefixes = [
        Path("reports/backtests"),
        Path("reports/strategies"),
        Path("orders"),
        Path("execution"),
        Path("models"),
        Path("checkpoints"),
        Path("data/research/v8_7/backtests"),
        Path("data/research/v8_7/strategies"),
    ]
    for prefix in forbidden_prefixes:
        path = root / prefix
        if path.exists():
            errors.append(f"Forbidden V8.7 artifact detected: {prefix}")
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V8.7 model artifact detected: {path.relative_to(root)}")
    return errors


def _validate_v8_4_dataset_layer(root: Path) -> list[str]:
    result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
    return [] if result["passed"] else [f"V8.4 dataset validation failed before V8.7: {result['errors']}"]


def _is_iso_utc(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.astimezone(timezone.utc).tzinfo is not None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION_V8_7,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest_status": manifest.get("status") if manifest else None,
    }
