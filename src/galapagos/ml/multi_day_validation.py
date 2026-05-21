from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.schemas import get_dataset_v3_2_path, get_split_v3_2_path
from galapagos.ml.multi_day_metrics import compute_multi_day_classification_metrics_v3_3
from galapagos.ml.multi_day_quality import assess_multi_day_ml_quality_v3_3
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V3_3,
    DOC_PATH_V3_3,
    EXPECTED_LIMITATIONS_V3_3,
    FORBIDDEN_FEATURE_TERMS_V3_3,
    FORBIDDEN_METRIC_TERMS_V3_3,
    FORBIDDEN_OUTPUT_TERMS_V3_3,
    MANIFEST_PATH_V3_3,
    ML_SCHEMA_VERSION_V3_3,
    ML_SCORE_COLUMNS_V3_3,
    MODEL_NAMES_V3_3,
    REPORT_JSON_PATH_V3_3,
    REPORT_MD_PATH_V3_3,
    SAFETY_FLAGS_V3_3,
    SCORES_JSON_PATH_V3_3,
    SCORES_MD_PATH_V3_3,
    TARGET_NAME_V3_3,
    TIMEFRAMES_V3_3,
    VERSION_V3_3,
    get_feature_columns_sha256_v3_3,
    get_multi_day_ml_score_path_v3_3,
)
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


ML_RUN_ID_PATTERN_V3_3 = re.compile(r"^v3_3_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V3_3)
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


def validate_multi_day_offline_ml_research_v3_3(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    dataset_validation = _validate_v3_2_dataset_layer(project_root)
    if dataset_validation:
        return _result(dataset_validation, warnings)

    manifest_path = project_root / MANIFEST_PATH_V3_3
    report_path = project_root / REPORT_JSON_PATH_V3_3
    scores_json_path = project_root / SCORES_JSON_PATH_V3_3
    if not manifest_path.exists():
        return _result([f"missing V3.3 manifest: {MANIFEST_PATH_V3_3}"], warnings)
    if not report_path.exists():
        return _result([f"missing V3.3 quality report: {REPORT_JSON_PATH_V3_3}"], warnings)
    if not scores_json_path.exists():
        return _result([f"missing V3.3 scores report: {SCORES_JSON_PATH_V3_3}"], warnings)

    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    scores_report = _load_json(scores_json_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V3.3 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V3.3 quality report"))
    errors.extend(_validate_scores_report(manifest, scores_report))
    errors.extend(scan_payload_for_forbidden_claims(scores_report, "V3.3 scores report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v3_3_artifacts(project_root))

    if errors:
        return _result(errors, warnings, manifest)

    physical_quality: dict[str, dict[str, Any]] = {}
    all_scores: list[pd.DataFrame] = []
    for timeframe in TIMEFRAMES_V3_3:
        errors.extend(_validate_timeframe(project_root, manifest, timeframe, physical_quality, all_scores))
    non_empty_scores = [frame for frame in all_scores if not frame.empty]
    if non_empty_scores:
        recomputed_metrics = compute_multi_day_classification_metrics_v3_3(pd.concat(non_empty_scores, ignore_index=True))
        if recomputed_metrics != manifest.get("metrics"):
            errors.append("V3.3 manifest metrics mismatch")
    errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    errors.extend(_scan_metrics_for_forbidden_terms(manifest.get("metrics", {})))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V3.3 manifest"))
    if manifest.get("version") != VERSION_V3_3:
        errors.append("V3.3 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.3 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V3.3 manifest created_at_utc invalid")
    if not isinstance(manifest.get("ml_run_id"), str) or ML_RUN_ID_PATTERN_V3_3.fullmatch(manifest["ml_run_id"]) is None:
        errors.append("V3.3 manifest ml_run_id invalid")
    if manifest.get("target_name") != TARGET_NAME_V3_3:
        errors.append("V3.3 target_name mismatch")
    if manifest.get("feature_columns") != ALLOWED_FEATURE_COLUMNS_V3_3:
        errors.append("V3.3 feature_columns mismatch")
    errors.extend(_validate_feature_columns(manifest.get("feature_columns", [])))
    if manifest.get("models") != MODEL_NAMES_V3_3:
        errors.append("V3.3 models mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V3_3:
        errors.append("V3.3 limitations mismatch")
    for section in ["input_datasets", "input_splits", "outputs", "quality", "sanity_checks"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V3.3 manifest {section}"))
    for timeframe in TIMEFRAMES_V3_3:
        errors.extend(validate_exact_keys(manifest.get("input_datasets", {}).get(timeframe, {}), INPUT_KEYS, f"V3.3 manifest input_datasets.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_splits", {}).get(timeframe, {}), INPUT_KEYS, f"V3.3 manifest input_splits.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V3.3 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("quality", {}).get(timeframe, {}), QUALITY_KEYS, f"V3.3 manifest quality.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("sanity_checks", {}).get(timeframe, {}), SANITY_KEYS, f"V3.3 manifest sanity_checks.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), set(SAFETY_FLAGS_V3_3), "V3.3 manifest safety"))
    return errors


def _validate_feature_columns(columns: Any) -> list[str]:
    if not isinstance(columns, list):
        return ["V3.3 feature_columns must be list"]
    forbidden = [
        column
        for column in columns
        if not isinstance(column, str) or any(term in column.casefold() for term in FORBIDDEN_FEATURE_TERMS_V3_3)
    ]
    return [f"V3.3 forbidden feature columns: {forbidden}"] if forbidden else []


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V3.3 quality report")
    if report != manifest:
        errors.append("V3.3 quality report mismatch")
    return errors


def _validate_scores_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, {"version", "ml_run_id", "outputs", "metrics"}, "V3.3 scores report")
    expected = {
        "version": manifest.get("version"),
        "ml_run_id": manifest.get("ml_run_id"),
        "outputs": manifest.get("outputs"),
        "metrics": manifest.get("metrics"),
    }
    if report != expected:
        errors.append("V3.3 scores report mismatch")
    return errors


def _validate_timeframe(
    root: Path,
    manifest: dict[str, Any],
    timeframe: str,
    physical_quality: dict[str, dict[str, Any]],
    all_scores: list[pd.DataFrame],
) -> list[str]:
    errors: list[str] = []
    dataset_path = get_dataset_v3_2_path(root, timeframe)
    split_path = get_split_v3_2_path(root, timeframe)
    score_path = get_multi_day_ml_score_path_v3_3(root, timeframe)
    for label, path in [("dataset", dataset_path), ("split", split_path), ("scores", score_path)]:
        if not path.exists():
            errors.append(f"missing V3.3 {label} file for {timeframe}: {path.relative_to(root)}")
    if errors:
        return errors

    dataset = read_parquet(dataset_path)
    split = read_parquet(split_path)
    scores = read_parquet(score_path)
    all_scores.append(scores)
    errors.extend(_compare_input_block(manifest["input_datasets"][timeframe], dataset_path, sha256_file(dataset_path), len(dataset), root, f"V3.3 manifest input_datasets.{timeframe}"))
    errors.extend(_compare_input_block(manifest["input_splits"][timeframe], split_path, sha256_file(split_path), len(split), root, f"V3.3 manifest input_splits.{timeframe}"))
    errors.extend(_compare_output_block(manifest["outputs"][timeframe], score_path, sha256_file(score_path), len(scores), root, f"V3.3 manifest outputs.{timeframe}"))
    errors.extend(_validate_score_frame_schema_only(scores, timeframe))
    errors.extend(_validate_score_values(dataset, scores, timeframe, sha256_file(dataset_path)))
    quality = assess_multi_day_ml_quality_v3_3(dataset, scores, timeframe)
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def _validate_score_frame_schema_only(scores: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    if list(scores.columns) != ML_SCORE_COLUMNS_V3_3:
        errors.append(f"V3.3 score schema mismatch for {timeframe}")
    forbidden_output = [
        column for column in scores.columns if any(term in column.casefold() for term in FORBIDDEN_OUTPUT_TERMS_V3_3)
    ]
    if forbidden_output:
        errors.append(f"V3.3 score forbidden columns for {timeframe}: {forbidden_output}")
    if {"prediction_available_ts", "decision_ts"}.issubset(scores.columns) and not scores["prediction_available_ts"].ge(scores["decision_ts"]).all():
        errors.append(f"V3.3 prediction_available_ts invalid for {timeframe}")
    if len(scores) > 0:
        if "model_name" in scores.columns and set(scores["model_name"].unique()) != set(MODEL_NAMES_V3_3):
            errors.append(f"V3.3 score models mismatch for {timeframe}")
        if "target_name" in scores.columns and set(scores["target_name"].unique()) != {TARGET_NAME_V3_3}:
            errors.append(f"V3.3 score target mismatch for {timeframe}")
        if "feature_columns_sha256" in scores.columns and set(scores["feature_columns_sha256"].unique()) != {get_feature_columns_sha256_v3_3()}:
            errors.append(f"V3.3 score feature_columns_sha256 mismatch for {timeframe}")
        if "ml_schema_version" in scores.columns and set(scores["ml_schema_version"].unique()) != {ML_SCHEMA_VERSION_V3_3}:
            errors.append(f"V3.3 score schema version mismatch for {timeframe}")
    return errors


def _validate_score_values(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str, dataset_sha: str) -> list[str]:
    errors: list[str] = []
    used = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)]  # noqa: E712
    expected_rows = len(used) * len(MODEL_NAMES_V3_3)
    if len(scores) != expected_rows:
        errors.append(f"V3.3 score row count mismatch for {timeframe}")
    if len(scores) and set(scores["dataset_sha256"].unique()) != {dataset_sha}:
        errors.append(f"V3.3 score dataset_sha256 mismatch for {timeframe}")
    if len(scores) and not scores["row_valid_for_ml"].eq(True).all():
        errors.append(f"V3.3 score row_valid_for_ml mismatch for {timeframe}")
    if len(scores) and set(scores["target_value"].dropna().astype(str).unique()) - {"DOWN", "FLAT", "UP"}:
        errors.append(f"V3.3 score target classes invalid for {timeframe}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        if manifest["quality"].get(timeframe) != quality:
            errors.append(f"V3.3 manifest quality mismatch for {timeframe}")
    return errors


def _validate_safety(safety: Any) -> list[str]:
    if not isinstance(safety, dict):
        return ["V3.3 manifest safety must be object"]
    return [f"V3.3 safety flag {key} must be {value}" for key, value in SAFETY_FLAGS_V3_3.items() if safety.get(key) is not value]


def _find_forbidden_v3_3_artifacts(root: Path) -> list[str]:
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
        Path("data/research/v3_3/backtests"),
        Path("data/research/v3_3/strategies"),
        Path("data/research/v3_3/orders"),
    ]
    persistent_model_suffixes = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
    allowed_reports = {
        Path("reports/ml/offline_ml_research_v2_8.json"),
        Path("reports/ml/offline_ml_research_v2_8.md"),
        Path("reports/ml/offline_research_scores_v2_8.json"),
        Path("reports/ml/offline_research_scores_v2_8.md"),
        REPORT_JSON_PATH_V3_3,
        REPORT_MD_PATH_V3_3,
        SCORES_JSON_PATH_V3_3,
        SCORES_MD_PATH_V3_3,
    }

    for relative in forbidden_roots:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V3.3 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V3.3 artifact detected: {child.relative_to(root).as_posix()}")

    data_v3_3_ml = root / "data/research/v3_3/ml"
    if data_v3_3_ml.exists():
        for child in sorted(data_v3_3_ml.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(root)
            if _is_allowed_v3_3_ml_score_path(relative):
                continue
            errors.append(f"Forbidden V3.3 artifact detected: {relative.as_posix()}")

    reports_ml = root / "reports/ml"
    if reports_ml.exists():
        for child in sorted(reports_ml.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(root)
            if relative in allowed_reports:
                continue
            if child.suffix.casefold() in persistent_model_suffixes:
                errors.append(f"Forbidden V3.3 artifact detected: {relative.as_posix()}")

    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in persistent_model_suffixes:
            errors.append(f"Forbidden V3.3 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _is_allowed_v3_3_ml_score_path(relative: Path) -> bool:
    parts = relative.parts
    return (
        len(parts) == 11
        and parts[0] == "data"
        and parts[1] == "research"
        and parts[2] == "v3_3"
        and parts[3] == "ml"
        and parts[4] == "offline_research"
        and parts[5] == "source=binance_archive"
        and parts[6] == "market_type=spot"
        and parts[7] == "symbol=BTCUSDT"
        and parts[8] in {f"timeframe={timeframe}" for timeframe in TIMEFRAMES_V3_3}
        and parts[9] == "window=2024-01-15_2024-01-21"
        and parts[10] == "ml-scores.parquet"
    )


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [
        (REPORT_MD_PATH_V3_3, "V3.3 Markdown report"),
        (SCORES_MD_PATH_V3_3, "V3.3 scores Markdown"),
        (DOC_PATH_V3_3, "V3.3 documentation"),
    ]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _scan_metrics_for_forbidden_terms(metrics: Any) -> list[str]:
    text = json.dumps(metrics, ensure_ascii=False).casefold()
    return [f"V3.3 metrics contain forbidden trading metric: {term}" for term in FORBIDDEN_METRIC_TERMS_V3_3 if term in text]


def _validate_v3_2_dataset_layer(root: Path) -> list[str]:
    from galapagos.datasets.multi_day_validation import validate_multi_day_offline_supervised_dataset_v3_2

    result = validate_multi_day_offline_supervised_dataset_v3_2(root)
    if result["passed"]:
        return []
    return [f"V3.2.1 dataset validation failed before V3.3: {result['errors']}"]


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
