from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import TARGET_TIMEFRAMES, get_dataset_gold_path, get_split_gold_path
from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
from galapagos.features.validation import validate_causal_feature_store_v2_5
from galapagos.labels.validation import validate_label_factory_v2_6
from galapagos.ml.metrics import compute_classification_metrics
from galapagos.ml.quality import assess_ml_quality
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V2_8,
    EXPECTED_LIMITATIONS_V2_8,
    FORBIDDEN_FEATURE_TERMS_V2_8,
    FORBIDDEN_METRIC_TERMS_V2_8,
    FORBIDDEN_OUTPUT_TERMS_V2_8,
    MANIFEST_PATH,
    ML_SCORE_COLUMNS_V2_8,
    MODEL_NAMES,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS_V2_8,
    SCORES_JSON_PATH,
    SCORES_MD_PATH,
    TARGET_NAME,
    VERSION,
    get_feature_columns_sha256,
    get_ml_score_path,
)
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


ML_RUN_ID_PATTERN = re.compile(r"^v2_8_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TARGET_TIMEFRAMES)
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "ml_run_id",
    "input_datasets",
    "input_splits",
    "outputs",
    "target_name",
    "feature_columns",
    "models",
    "metrics",
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


def validate_offline_ml_research_v2_8(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for label, validation in [
        ("V2.3.1 ingestion", validate_public_market_ingestion_v2_3(project_root)),
        ("V2.4.8 resampling", validate_ohlcv_resampling_v2_4(project_root)),
        ("V2.5.2 features", validate_causal_feature_store_v2_5(project_root)),
        ("V2.6.2 labels", validate_label_factory_v2_6(project_root)),
        ("V2.7.2 dataset", validate_offline_supervised_dataset_v2_7(project_root)),
    ]:
        if not validation["passed"]:
            return _result([f"{label} validation failed: {validation['errors']}"], warnings)

    manifest_path = project_root / MANIFEST_PATH
    report_path = project_root / REPORT_JSON_PATH
    scores_json_path = project_root / SCORES_JSON_PATH
    if not manifest_path.exists():
        return _result([f"missing V2.8 manifest: {MANIFEST_PATH}"], warnings)
    if not report_path.exists():
        return _result([f"missing V2.8 report: {REPORT_JSON_PATH}"], warnings)
    if not scores_json_path.exists():
        return _result([f"missing V2.8 scores report: {SCORES_JSON_PATH}"], warnings)

    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_json_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.8 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V2.8 quality report"))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(scan_payload_for_forbidden_claims(scores_report, "V2.8 scores report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_artifacts(project_root))
    if errors:
        return _result(errors, warnings, manifest)

    physical_quality: dict[str, dict[str, Any]] = {}
    all_scores: list[pd.DataFrame] = []
    for timeframe in TARGET_TIMEFRAMES:
        errors.extend(_validate_timeframe(project_root, manifest, timeframe, physical_quality, all_scores))
    non_empty_scores = [frame for frame in all_scores if not frame.empty]
    if non_empty_scores:
        recomputed_metrics = compute_classification_metrics(pd.concat(non_empty_scores, ignore_index=True))
        if recomputed_metrics != manifest.get("metrics"):
            errors.append("V2.8 manifest metrics mismatch")
    errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {})))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V2.8 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("V2.8 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V2.8 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V2.8 manifest created_at_utc invalid")
    if not isinstance(manifest.get("ml_run_id"), str) or ML_RUN_ID_PATTERN.fullmatch(manifest["ml_run_id"]) is None:
        errors.append("V2.8 manifest ml_run_id invalid")
    if manifest.get("target_name") != TARGET_NAME:
        errors.append("V2.8 target_name mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V2_8:
        errors.append("V2.8 feature_columns mismatch")
    if manifest.get("models") != MODEL_NAMES:
        errors.append("V2.8 models mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V2_8:
        errors.append("V2.8 limitations mismatch")
    for section in ["input_datasets", "input_splits", "outputs", "quality", "sanity_checks"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V2.8 manifest {section}"))
    for timeframe in TARGET_TIMEFRAMES:
        errors.extend(validate_exact_keys(manifest.get("input_datasets", {}).get(timeframe, {}), INPUT_KEYS, f"V2.8 manifest input_datasets.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_splits", {}).get(timeframe, {}), INPUT_KEYS, f"V2.8 manifest input_splits.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V2.8 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("quality", {}).get(timeframe, {}), QUALITY_KEYS, f"V2.8 manifest quality.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("sanity_checks", {}).get(timeframe, {}), SANITY_KEYS, f"V2.8 manifest sanity_checks.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), set(SAFETY_FLAGS_V2_8), "V2.8 manifest safety"))
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V2.8 quality report")
    if report != manifest:
        errors.append("V2.8 quality report mismatch")
    return errors


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, {"version", "ml_run_id", "outputs", "metrics"}, "V2.8 scores report")
    expected = {
        "version": manifest.get("version"),
        "ml_run_id": manifest.get("ml_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
    }
    if report != expected:
        errors.append("V2.8 scores report mismatch")
    return errors


def _validate_timeframe(
    root: Path,
    manifest: dict[str, Any],
    timeframe: str,
    physical_quality: dict[str, dict[str, Any]],
    all_scores: list[pd.DataFrame],
) -> list[str]:
    errors: list[str] = []
    dataset_path = get_dataset_gold_path(root, timeframe)
    split_path = get_split_gold_path(root, timeframe)
    score_path = get_ml_score_path(root, timeframe)
    for label, path in [("dataset", dataset_path), ("split", split_path), ("scores", score_path)]:
        if not path.exists():
            errors.append(f"missing V2.8 {label} file for {timeframe}: {path.relative_to(root)}")
    if errors:
        return errors
    dataset = read_parquet(dataset_path)
    split = read_parquet(split_path)
    scores = read_parquet(score_path)
    all_scores.append(scores)
    errors.extend(_compare_input_block(manifest["input_datasets"][timeframe], dataset_path, sha256_file(dataset_path), len(dataset), root, f"V2.8 manifest input_datasets.{timeframe}"))
    errors.extend(_compare_input_block(manifest["input_splits"][timeframe], split_path, sha256_file(split_path), len(split), root, f"V2.8 manifest input_splits.{timeframe}"))
    errors.extend(_compare_output_block(manifest["outputs"][timeframe], score_path, sha256_file(score_path), len(scores), root, f"V2.8 manifest outputs.{timeframe}"))
    if list(scores.columns) != ML_SCORE_COLUMNS_V2_8:
        errors.append(f"V2.8 score schema mismatch for {timeframe}")
    forbidden_output = [
        column for column in scores.columns if any(term in column.casefold() for term in FORBIDDEN_OUTPUT_TERMS_V2_8)
    ]
    if forbidden_output:
        errors.append(f"V2.8 score forbidden columns for {timeframe}: {forbidden_output}")
    if not scores["prediction_available_ts"].ge(scores["decision_ts"]).all():
        errors.append(f"V2.8 prediction_available_ts invalid for {timeframe}")
    if len(scores) > 0:
        if set(scores["model_name"].unique()) != set(MODEL_NAMES):
            errors.append(f"V2.8 score models mismatch for {timeframe}")
        if set(scores["target_name"].unique()) != {TARGET_NAME}:
            errors.append(f"V2.8 score target mismatch for {timeframe}")
        if set(scores["feature_columns_sha256"].unique()) != {get_feature_columns_sha256()}:
            errors.append(f"V2.8 score feature_columns_sha256 mismatch for {timeframe}")
    quality = assess_ml_quality(dataset, scores, timeframe)
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        if manifest["quality"].get(timeframe) != quality:
            errors.append(f"V2.8 manifest quality mismatch for {timeframe}")
    return errors


def _validate_safety(safety: Any) -> list[str]:
    if not isinstance(safety, dict):
        return ["V2.8 manifest safety must be object"]
    return [f"V2.8 safety flag {key} must be {value}" for key, value in SAFETY_FLAGS_V2_8.items() if safety.get(key) is not value]


def _find_forbidden_artifacts(root: Path) -> list[str]:
    forbidden_roots = ["models", "reports/strategies", "reports/signals", "reports/predictions", "orders", "execution"]
    errors: list[str] = []
    for relative in forbidden_roots:
        if (root / relative).exists():
            errors.append(f"Forbidden V2.8 artifact detected: {relative}")
    backtests = root / "reports/backtests"
    if backtests.exists():
        direct_forbidden = [
            child for child in backtests.iterdir() if child.name in {"backtest.json", "backtest.md", "summary.json", "summary.md"}
        ]
        for child in direct_forbidden:
            errors.append(f"Forbidden V2.8 artifact detected: {child.relative_to(root).as_posix()}")
    return errors


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [(REPORT_MD_PATH, "V2.8 Markdown report"), (SCORES_MD_PATH, "V2.8 scores Markdown")]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _scan_metrics_for_forbidden_terms(metrics: Any) -> list[str]:
    text = json.dumps(metrics, ensure_ascii=False).casefold()
    return [f"V2.8 metrics contain forbidden trading metric: {term}" for term in FORBIDDEN_METRIC_TERMS_V2_8 if term in text]


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
