from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.expanded_window import (
    build_expanded_offline_supervised_dataset_v3_8,
    build_split_frame_v3_8,
    input_feature_path,
    input_label_path,
)
from galapagos.datasets.expanded_window_quality import assess_expanded_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V3_8,
    DATASET_SCHEMA_VERSION_V3_8,
    DATACARD_MD_PATH_V3_8,
    DOC_PATH_V3_8,
    EXPECTED_LIMITATIONS_V3_8,
    EXPECTED_ROWS_V3_8,
    FEATURE_VALUE_COLUMNS,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V3_8,
    REPORT_JSON_PATH_V3_8,
    REPORT_MD_PATH_V3_8,
    SPLIT_COLUMNS_V3_8,
    SPLIT_POLICY_V3_8,
    TIMEFRAMES_V3_8,
    VERSION_V3_8,
    get_dataset_v3_8_path,
    get_split_v3_8_path,
)
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


DATASET_RUN_ID_PATTERN = re.compile(r"^v3_8_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V3_8)
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
SPLIT_POLICY_KEYS = {"train_ratio", "validation_ratio", "test_ratio", "shuffle", "purge_embargo"}
SPLIT_COUNT_KEYS = {"train", "validation", "test"}
HORIZON_KEYS = {"h1", "h3", "h5"}
SAFETY_KEYS = {
    "public_read_only",
    "authentication_used",
    "api_key_used",
    "private_endpoint_used",
    "orders_enabled",
    "paper_live_enabled",
    "trading_enabled",
    "ml_enabled",
    "labels_enabled",
    "dataset_enabled",
    "backtest_enabled",
    "strategy_enabled",
    "execution_enabled",
}
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "dataset_run_id",
    "input_features",
    "input_labels",
    "outputs",
    "splits",
    "dataset_schema_version",
    "dataset_columns",
    "split_policy",
    "quality",
    "safety",
    "limitations",
}
QUALITY_KEYS = {
    "rows",
    "expected_rows",
    "duplicate_rows",
    "split_counts",
    "label_valid_counts_by_horizon",
    "feature_warmup_rows",
    "tail_rows",
    "null_counts_by_column",
    "forbidden_columns_present",
    "timestamps_utc",
    "monotonic_event_ts",
    "feature_available_ts_valid",
    "label_available_ts_valid",
    "split_temporal_order_valid",
    "source_hashes_valid",
    "errors",
    "warnings",
}


IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def validate_expanded_offline_supervised_dataset_v3_8(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = project_root / MANIFEST_PATH_V3_8
    report_path = project_root / REPORT_JSON_PATH_V3_8
    if not manifest_path.exists():
        return _result([f"missing V3.8 manifest: {MANIFEST_PATH_V3_8}"], warnings)
    if not report_path.exists():
        return _result([f"missing V3.8 quality report: {REPORT_JSON_PATH_V3_8}"], warnings)

    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_manifest_structure(project_root, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V3.8 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V3.8 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v3_8_artifacts(project_root))

    if not errors:
        physical_quality: dict[str, dict[str, Any]] = {}
        for timeframe in TIMEFRAMES_V3_8:
            errors.extend(_validate_timeframe(project_root, manifest, timeframe, physical_quality))
        errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    return _result(errors, warnings, manifest=manifest)


def _validate_timeframe(
    project_root: Path,
    manifest: dict[str, Any],
    timeframe: str,
    physical_quality: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    feature_path = input_feature_path(project_root, timeframe)
    label_path = input_label_path(project_root, timeframe)
    dataset_path = get_dataset_v3_8_path(project_root, timeframe)
    split_path = get_split_v3_8_path(project_root, timeframe)
    for label, path in [("features", feature_path), ("labels", label_path), ("dataset", dataset_path), ("splits", split_path)]:
        if not path.exists():
            errors.append(f"missing V3.8 {label} file for {timeframe}: {path.relative_to(project_root)}")
    if errors:
        return errors

    features = read_parquet(feature_path)
    labels = read_parquet(label_path)
    dataset = read_parquet(dataset_path)
    splits = read_parquet(split_path)
    feature_sha = sha256_file(feature_path)
    label_sha = sha256_file(label_path)
    dataset_sha = sha256_file(dataset_path)
    split_sha = sha256_file(split_path)

    errors.extend(_compare_io_block(manifest["input_features"][timeframe], feature_path, feature_sha, len(features), project_root, f"V3.8 manifest input_features.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["input_labels"][timeframe], label_path, label_sha, len(labels), project_root, f"V3.8 manifest input_labels.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], dataset_path, dataset_sha, len(dataset), project_root, f"V3.8 manifest outputs.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["splits"][timeframe], split_path, split_sha, len(splits), project_root, f"V3.8 manifest splits.{timeframe}", include_bytes=True))
    errors.extend(_validate_dataset_schema(dataset, timeframe))
    if list(splits.columns) != SPLIT_COLUMNS_V3_8:
        errors.append(f"V3.8 split schema mismatch for {timeframe}")
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V3.8 dataset row count does not match sources for {timeframe}")
    errors.extend(_validate_dataset_values_against_sources(timeframe, dataset, features, labels, manifest["dataset_run_id"], feature_sha, label_sha))

    expected_splits = build_split_frame_v3_8(dataset)
    try:
        assert_frame_equal(splits.reset_index(drop=True), expected_splits.reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V3.8 split physical mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    feature_source_columns = [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]
    label_source_columns = [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]
    try:
        assert_frame_equal(dataset[feature_source_columns].reset_index(drop=True), features[feature_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V3.8 dataset feature source mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(dataset[label_source_columns].reset_index(drop=True), labels[label_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V3.8 dataset label source mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    quality = assess_expanded_dataset_quality(
        dataset,
        expected_rows=EXPECTED_ROWS_V3_8[timeframe],
        timeframe=timeframe,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def _validate_dataset_schema(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    errors: list[str] = []
    label = f" for {timeframe}" if timeframe else ""
    if list(frame.columns) != DATASET_COLUMNS_V3_8:
        errors.append(f"V3.8 dataset schema mismatch{label}")
    forbidden = [
        column
        for column in frame.columns
        if column not in DATASET_COLUMNS_V3_8
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    if forbidden:
        errors.append(f"V3.8 dataset forbidden columns{label}: {forbidden}")
    return errors


def _validate_dataset_temporal_rules(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    feature_sha = frame["source_features_sha256"].iloc[0] if "source_features_sha256" in frame.columns and len(frame) else ""
    label_sha = frame["source_labels_sha256"].iloc[0] if "source_labels_sha256" in frame.columns and len(frame) else ""
    quality = assess_expanded_dataset_quality(frame, expected_rows=len(frame), timeframe=timeframe or "dataset", feature_sha256=feature_sha, label_sha256=label_sha)
    return [
        *[error for error in quality["errors"] if "rows mismatch" not in error and "split counts mismatch" not in error],
    ]


def _validate_dataset_values_against_sources(
    timeframe: str,
    dataset_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    label_frame: pd.DataFrame,
    dataset_run_id: str,
    feature_sha256: str,
    label_sha256: str,
) -> list[str]:
    errors: list[str] = []
    try:
        expected = build_expanded_offline_supervised_dataset_v3_8(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha256,
            label_sha256=label_sha256,
            dataset_run_id=dataset_run_id,
        )
        assert_frame_equal(dataset_frame.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V3.8 dataset physical mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    except Exception as exc:
        errors.append(f"V3.8 dataset value validation failed for {timeframe}: {exc}")
    return errors


def _validate_manifest_structure(project_root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V3.8 manifest"))
    if manifest.get("version") != VERSION_V3_8:
        errors.append("V3.8 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.8 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V3.8 manifest created_at_utc invalid")
    if not isinstance(manifest.get("dataset_run_id"), str) or DATASET_RUN_ID_PATTERN.fullmatch(manifest["dataset_run_id"]) is None:
        errors.append("V3.8 manifest dataset_run_id invalid")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION_V3_8:
        errors.append("V3.8 manifest dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V3_8:
        errors.append("V3.8 manifest dataset_columns mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V3_8:
        errors.append("V3.8 manifest split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V3_8:
        errors.append("V3.8 manifest limitations mismatch")
    for section in ["input_features", "input_labels", "outputs", "splits", "quality"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V3.8 manifest {section}"))
    errors.extend(validate_exact_keys(manifest.get("split_policy", {}), SPLIT_POLICY_KEYS, "V3.8 manifest split_policy"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), SAFETY_KEYS, "V3.8 manifest safety"))
    for timeframe in TIMEFRAMES_V3_8:
        errors.extend(validate_exact_keys(manifest.get("input_features", {}).get(timeframe, {}), INPUT_KEYS, f"V3.8 manifest input_features.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_labels", {}).get(timeframe, {}), INPUT_KEYS, f"V3.8 manifest input_labels.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V3.8 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("splits", {}).get(timeframe, {}), OUTPUT_KEYS, f"V3.8 manifest splits.{timeframe}"))
        quality = manifest.get("quality", {}).get(timeframe, {})
        errors.extend(validate_exact_keys(quality, QUALITY_KEYS, f"V3.8 manifest quality.{timeframe}"))
        if isinstance(quality, dict):
            errors.extend(validate_exact_keys(quality.get("split_counts", {}), SPLIT_COUNT_KEYS, f"V3.8 manifest quality.{timeframe}.split_counts"))
            errors.extend(validate_exact_keys(quality.get("label_valid_counts_by_horizon", {}), HORIZON_KEYS, f"V3.8 manifest quality.{timeframe}.label_valid_counts_by_horizon"))
            errors.extend(validate_exact_keys(quality.get("null_counts_by_column", {}), set(DATASET_COLUMNS_V3_8), f"V3.8 manifest quality.{timeframe}.null_counts_by_column"))
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V3.8 quality report")
    if report != manifest:
        for path in _compare_nested(manifest, report, "V3.8 quality report"):
            errors.append(f"V3.8 quality report mismatch for {path}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        for path in _compare_nested(quality, manifest["quality"].get(timeframe), timeframe):
            errors.append(f"V3.8 manifest quality mismatch for {path}")
    return errors


def _compare_io_block(
    block: dict[str, Any],
    path: Path,
    sha256: str,
    rows: int,
    project_root: Path,
    label: str,
    *,
    include_bytes: bool,
) -> list[str]:
    errors: list[str] = []
    if (project_root / Path(str(block.get("path", "")))).resolve() != path.resolve():
        errors.append(f"{label}.path mismatch")
    if block.get("sha256") != sha256:
        errors.append(f"{label}.sha256 mismatch")
    if block.get("rows") != rows:
        errors.append(f"{label}.rows mismatch")
    if include_bytes:
        if block.get("bytes") != path.stat().st_size:
            errors.append(f"{label}.bytes mismatch")
        if block.get("format") != "parquet":
            errors.append(f"{label}.format mismatch")
    return errors


def _validate_safety(safety: Any) -> list[str]:
    expected = {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": True,
        "dataset_enabled": True,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }
    if not isinstance(safety, dict):
        return ["V3.8 manifest safety must be an object"]
    return [f"V3.8 safety flag {key} must be {value}" for key, value in expected.items() if safety.get(key) is not value]


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [
        (REPORT_MD_PATH_V3_8, "V3.8 Markdown report"),
        (DATACARD_MD_PATH_V3_8, "V3.8 data card"),
        (DOC_PATH_V3_8, "V3.8 documentation"),
    ]:
        path = project_root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _find_forbidden_v3_8_artifacts(project_root: Path) -> list[str]:
    forbidden_roots = [
        Path("models"),
        Path("checkpoints"),
        Path("reports/strategies"),
        Path("reports/signals"),
        Path("reports/predictions"),
        Path("orders"),
        Path("execution"),
        Path("data/research/v3_8/ml"),
        Path("data/research/v3_8/backtests"),
        Path("data/research/v3_8/strategies"),
        Path("data/research/v3_8/models"),
    ]
    errors: list[str] = []
    for relative in forbidden_roots:
        if (project_root / relative).exists():
            errors.append(f"Forbidden V3.8 artifact detected: {relative.as_posix()}")
    backtests = project_root / "reports/backtests"
    if backtests.exists():
        errors.append("Forbidden V3.8 artifact detected: reports/backtests")
        for child in sorted(backtests.rglob("*")):
            if child.is_file():
                errors.append(f"Forbidden V3.8 artifact detected: {child.relative_to(project_root).as_posix()}")
    for suffix in [".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"]:
        matches = [path for path in project_root.rglob(f"*{suffix}") if not any(part in IGNORED_SCAN_PARTS for part in path.parts)]
        for path in matches:
            errors.append(f"Forbidden V3.8 model artifact detected: {path.relative_to(project_root).as_posix()}")
    reports_ml = project_root / "reports/ml"
    if reports_ml.exists():
        for path in sorted(reports_ml.rglob("*v3_8*")):
            if path.is_file():
                errors.append(f"Forbidden V3.8 ML report detected: {path.relative_to(project_root).as_posix()}")
    return errors


def _compare_nested(expected: Any, actual: Any, prefix: str) -> list[str]:
    if expected == actual:
        return []
    if isinstance(expected, dict) and isinstance(actual, dict):
        errors: list[str] = []
        for key in sorted(set(expected) - set(actual)):
            errors.append(f"{prefix}.{key}")
        for key in sorted(set(actual) - set(expected)):
            errors.append(f"{prefix}.{key}")
        for key in sorted(set(expected) & set(actual)):
            errors.extend(_compare_nested(expected[key], actual[key], f"{prefix}.{key}"))
        return errors
    return [prefix]


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
