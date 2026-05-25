from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.ohlcv_trades_1y_window import (
    build_report_v8_4,
    dataset_output_path,
    filter_labels_to_v8_4_window,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v8_3_feature_manifest,
    split_output_path,
)
from galapagos.datasets.ohlcv_trades_1y_window_quality import (
    assess_ohlcv_trades_dataset_quality_v8_4,
    forbidden_dataset_columns_v8_4,
)
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V8_4,
    DATASET_SCHEMA_VERSION_V8_4,
    DATACARD_MD_PATH_V8_4,
    DOC_PATH_V8_4,
    EXPECTED_LIMITATIONS_V8_4,
    EXPECTED_ROWS_V8_4,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V8_4,
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4,
    REPORT_JSON_PATH_V8_4,
    REPORT_MD_PATH_V8_4,
    SPLIT_COLUMNS_V8_4,
    SPLIT_POLICY_V8_4,
    TIMEFRAMES_V8_4,
    VERSION_V8_4,
)
from galapagos.features.ohlcv_trades_1y import MANIFEST_PATH_V8_3 as FEATURE_MANIFEST_PATH_V8_3
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.validation.safety import scan_payload_for_forbidden_claims, validate_markdown_forbidden_claims


DATASET_RUN_ID_PATTERN_V8_4 = re.compile(r"^v8_4_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "dataset_run_id",
    "input_features_manifest",
    "input_labels_manifest",
    "input_features",
    "input_labels_filtered",
    "outputs",
    "splits",
    "dataset_schema_version",
    "dataset_columns",
    "feature_columns_count",
    "split_policy",
    "quality",
    "safety",
    "limitations",
}
FEATURE_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days"}
LABEL_MANIFEST_KEYS = {"path", "sha256", "source_window_start", "source_window_end", "dataset_window_start", "dataset_window_end"}
INPUT_FEATURE_KEYS = {"path", "sha256", "rows"}
INPUT_LABEL_FILTERED_KEYS = {"rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
SPLIT_POLICY_KEYS = {"train_ratio", "validation_ratio", "test_ratio", "shuffle", "purge_embargo", "walk_forward_grouping"}
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
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
FORBIDDEN_V8_4_PATHS = [
    "data/research/v8_4/ml",
    "data/research/v8_4/backtests",
    "data/research/v8_4/strategies",
    "reports/ml/ohlcv_trades_offline_ml_research_v8_4.json",
    "reports/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
    "models",
    "checkpoints",
]


def validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V8_4
    report_path = project_root / REPORT_JSON_PATH_V8_4
    if not manifest_path.exists():
        return _result([f"missing V8.4 manifest: {MANIFEST_PATH_V8_4}"], warnings)
    if not report_path.exists():
        return _result([f"missing V8.4 quality report: {REPORT_JSON_PATH_V8_4}"], warnings)

    feature_manifest = load_v8_3_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_input_manifest_windows(feature_manifest, label_manifest))
    errors.extend(_validate_manifest_structure(project_root, manifest, feature_manifest, label_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V8.4 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V8.4 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v8_4_artifacts(project_root))

    if not errors:
        physical_quality: dict[str, dict[str, Any]] = {}
        for timeframe in TIMEFRAMES_V8_4:
            errors.extend(_validate_timeframe(project_root, manifest, feature_manifest, label_manifest, timeframe, physical_quality))
        errors.extend(_compare_quality(manifest, physical_quality))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    return _result(errors, warnings, manifest=manifest)


def _validate_timeframe(
    project_root: Path,
    manifest: dict[str, Any],
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
    timeframe: str,
    physical_quality: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    feature_path = input_feature_path(project_root, timeframe, feature_manifest)
    label_path = input_label_path(project_root, timeframe, label_manifest)
    dataset_path = dataset_output_path(project_root, timeframe)
    split_path = split_output_path(project_root, timeframe)
    for label, path in [("features", feature_path), ("labels", label_path), ("dataset", dataset_path), ("splits", split_path)]:
        if not path.exists():
            errors.append(f"missing V8.4 {label} file for {timeframe}: {path.relative_to(project_root)}")
    if errors:
        return errors

    features = read_parquet(feature_path)
    labels = filter_labels_to_v8_4_window(read_parquet(label_path))
    dataset = read_parquet(dataset_path)
    split_frame = read_parquet(split_path)
    feature_sha = sha256_file(feature_path)
    label_sha = sha256_file(label_path)
    dataset_sha = sha256_file(dataset_path)
    split_sha = sha256_file(split_path)

    errors.extend(_compare_io_block(manifest["input_features"][timeframe], feature_path, feature_sha, len(features), project_root, f"V8.4 manifest input_features.{timeframe}", include_bytes=False))
    if manifest["input_labels_filtered"][timeframe]["rows"] != len(labels):
        errors.append(f"V8.4 manifest input_labels_filtered.{timeframe} rows mismatch")
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], dataset_path, dataset_sha, len(dataset), project_root, f"V8.4 manifest outputs.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["splits"][timeframe], split_path, split_sha, len(split_frame), project_root, f"V8.4 manifest splits.{timeframe}", include_bytes=True))
    errors.extend(validate_dataset_schema_v8_4(dataset, timeframe))
    errors.extend(validate_split_frame_v8_4(dataset, split_frame, timeframe))
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V8.4 dataset row count does not match sources for {timeframe}")
    errors.extend(validate_dataset_values_against_sources_v8_4(timeframe, dataset, features, labels, manifest["dataset_run_id"], feature_sha, label_sha))
    errors.extend(validate_dataset_source_value_equality_v8_4(timeframe, dataset, features, labels))
    errors.extend(validate_feature_source_has_no_labels_v8_4(timeframe, features))

    quality = assess_ohlcv_trades_dataset_quality_v8_4(
        dataset,
        split_frame,
        expected_rows=EXPECTED_ROWS_V8_4[timeframe],
        timeframe=timeframe,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def validate_dataset_schema_v8_4(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(frame.columns) != DATASET_COLUMNS_V8_4:
        errors.append(f"V8.4 dataset schema mismatch{label}")
    forbidden = forbidden_dataset_columns_v8_4(frame)
    if forbidden:
        errors.append(f"V8.4 dataset contains forbidden columns{label}: {forbidden}")
    return errors


def validate_split_frame_v8_4(dataset: pd.DataFrame, split_frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(split_frame.columns) != SPLIT_COLUMNS_V8_4:
        errors.append(f"V8.4 split schema mismatch{label}")
    if len(split_frame) != len(dataset):
        errors.append(f"V8.4 split rows mismatch dataset rows{label}")
        return errors
    try:
        assert_frame_equal(split_frame.reset_index(drop=True), dataset[SPLIT_COLUMNS_V8_4].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V8.4 split file mismatch dataset split columns{label}: {str(exc).splitlines()[0]}")
    if "walk_forward_group" not in split_frame.columns or split_frame["walk_forward_group"].isna().any():
        errors.append(f"V8.4 walk_forward_group missing{label}")
    return errors


def validate_dataset_values_against_sources_v8_4(
    timeframe: str,
    dataset: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.DataFrame,
    dataset_run_id: str,
    feature_sha: str,
    label_sha: str,
) -> list[str]:
    errors: list[str] = []
    if set(dataset["dataset_run_id"].astype(str).unique()) != {dataset_run_id}:
        errors.append(f"V8.4 dataset_run_id mismatch for {timeframe}")
    if set(dataset["dataset_schema_version"].astype(str).unique()) != {DATASET_SCHEMA_VERSION_V8_4}:
        errors.append(f"V8.4 dataset_schema_version mismatch for {timeframe}")
    if set(dataset["source_features_sha256"].astype(str).unique()) != {feature_sha}:
        errors.append(f"V8.4 source_features_sha256 mismatch for {timeframe}")
    if set(dataset["source_labels_sha256"].astype(str).unique()) != {label_sha}:
        errors.append(f"V8.4 source_labels_sha256 mismatch for {timeframe}")
    try:
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), features[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), labels[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V8.4 join keys mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    if not (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all():
        errors.append(f"V8.4 feature_available_ts > decision_ts for {timeframe}")
    valid_mask = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    if valid_mask.any() and not (
        pd.to_datetime(dataset.loc[valid_mask, "label_available_ts"], utc=True)
        > pd.to_datetime(dataset.loc[valid_mask, "decision_ts"], utc=True)
    ).all():
        errors.append(f"V8.4 label_available_ts <= decision_ts for valid labels in {timeframe}")
    return errors


def validate_dataset_source_value_equality_v8_4(
    timeframe: str,
    dataset: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []
    try:
        assert_frame_equal(
            dataset[[*OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4, "feature_available_ts"]].reset_index(drop=True),
            features[[*OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4, "feature_available_ts"]].reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        errors.append(f"V8.4 feature values changed in dataset for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(
            dataset[[*LABEL_VALUE_COLUMNS, "label_available_ts"]].reset_index(drop=True),
            labels[[*LABEL_VALUE_COLUMNS, "label_available_ts"]].reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        errors.append(f"V8.4 label values changed in dataset for {timeframe}: {str(exc).splitlines()[0]}")
    return errors


def validate_feature_source_has_no_labels_v8_4(timeframe: str, features: pd.DataFrame) -> list[str]:
    forbidden = [
        column
        for column in features.columns
        if str(column).startswith("future_") or str(column).startswith("label_") or str(column).startswith("direction_") or str(column).startswith("up_down_flat_")
    ]
    return [f"V8.4 features source contains label-like columns for {timeframe}: {forbidden}"] if forbidden else []


def _validate_manifest_structure(
    project_root: Path,
    manifest: dict[str, Any],
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_exact_keys(manifest, MANIFEST_KEYS, "V8.4 manifest"))
    if manifest.get("version") != VERSION_V8_4:
        errors.append("V8.4 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V8.4 manifest status must be PASS")
    if not DATASET_RUN_ID_PATTERN_V8_4.match(str(manifest.get("dataset_run_id", ""))):
        errors.append("V8.4 dataset_run_id format invalid")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION_V8_4:
        errors.append("V8.4 dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V8_4:
        errors.append("V8.4 dataset_columns mismatch")
    if manifest.get("feature_columns_count") != len(OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4):
        errors.append("V8.4 feature_columns_count mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V8_4:
        errors.append("V8.4 split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V8_4:
        errors.append("V8.4 limitations mismatch")

    feature_manifest_block = manifest.get("input_features_manifest", {})
    errors.extend(_validate_exact_keys(feature_manifest_block, FEATURE_MANIFEST_KEYS, "V8.4 input_features_manifest"))
    if feature_manifest_block.get("path") != FEATURE_MANIFEST_PATH_V8_3.as_posix():
        errors.append("V8.4 feature manifest path mismatch")
    if feature_manifest_block.get("sha256") != sha256_file(project_root / FEATURE_MANIFEST_PATH_V8_3):
        errors.append("V8.4 feature manifest sha256 mismatch")
    if feature_manifest_block.get("window_start") != "2023-03-25" or feature_manifest_block.get("window_end") != "2024-03-24":
        errors.append("V8.4 feature manifest window mismatch")
    if feature_manifest_block.get("total_days") != 366:
        errors.append("V8.4 feature manifest total_days mismatch")

    label_manifest_block = manifest.get("input_labels_manifest", {})
    errors.extend(_validate_exact_keys(label_manifest_block, LABEL_MANIFEST_KEYS, "V8.4 input_labels_manifest"))
    if label_manifest_block.get("path") != LABEL_MANIFEST_PATH_V5_2.as_posix():
        errors.append("V8.4 label manifest path mismatch")
    if label_manifest_block.get("sha256") != sha256_file(project_root / LABEL_MANIFEST_PATH_V5_2):
        errors.append("V8.4 label manifest sha256 mismatch")
    if label_manifest_block.get("source_window_start") != label_manifest["input_ohlcv_manifest"]["window_start"]:
        errors.append("V8.4 label manifest source_window_start mismatch")
    if label_manifest_block.get("source_window_end") != label_manifest["input_ohlcv_manifest"]["window_end"]:
        errors.append("V8.4 label manifest source_window_end mismatch")
    if label_manifest_block.get("dataset_window_start") != "2023-03-25" or label_manifest_block.get("dataset_window_end") != "2024-03-24":
        errors.append("V8.4 label manifest dataset window mismatch")

    for mapping_name, expected_keys in [
        ("input_features", INPUT_FEATURE_KEYS),
        ("input_labels_filtered", INPUT_LABEL_FILTERED_KEYS),
        ("outputs", OUTPUT_KEYS),
        ("splits", OUTPUT_KEYS),
    ]:
        mapping = manifest.get(mapping_name, {})
        if set(mapping) != set(TIMEFRAMES_V8_4):
            errors.append(f"V8.4 {mapping_name} timeframe keys mismatch")
        for timeframe in TIMEFRAMES_V8_4:
            errors.extend(_validate_exact_keys(mapping.get(timeframe, {}), expected_keys, f"V8.4 {mapping_name}.{timeframe}"))
    return errors


def _validate_input_manifest_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if feature_manifest.get("window", {}).get("window_start") != "2023-03-25":
        errors.append("V8.4 input features window_start must be 2023-03-25")
    if feature_manifest.get("window", {}).get("window_end") != "2024-03-24":
        errors.append("V8.4 input features window_end must be 2024-03-24")
    if int(feature_manifest.get("window", {}).get("total_days", 0)) != 366:
        errors.append("V8.4 input features total_days must be 366")
    label_start = label_manifest.get("input_ohlcv_manifest", {}).get("window_start")
    label_end = label_manifest.get("input_ohlcv_manifest", {}).get("window_end")
    if not (label_start <= "2023-03-25" and label_end >= "2024-03-24"):
        errors.append("V8.4 V5.2 labels do not cover the V8.3 window")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report != build_report_v8_4(manifest):
        errors.append("V8.4 report JSON must be a deterministic projection of the manifest")
    errors.extend(_validate_exact_keys(report, MANIFEST_KEYS, "V8.4 report JSON"))
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    return ["V8.4 manifest quality does not match physical quality"] if manifest.get("quality") != physical_quality else []


def _compare_io_block(
    payload: dict[str, Any],
    path: Path,
    sha256: str,
    rows: int,
    project_root: Path,
    label: str,
    *,
    include_bytes: bool,
) -> list[str]:
    errors: list[str] = []
    if payload.get("path") != path.relative_to(project_root).as_posix():
        errors.append(f"{label} path mismatch")
    if payload.get("sha256") != sha256:
        errors.append(f"{label} sha256 mismatch")
    if int(payload.get("rows", -1)) != int(rows):
        errors.append(f"{label} rows mismatch")
    if include_bytes and int(payload.get("bytes", -1)) != path.stat().st_size:
        errors.append(f"{label} bytes mismatch")
    if include_bytes and payload.get("format") != "parquet":
        errors.append(f"{label} format mismatch")
    return errors


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [
        (REPORT_MD_PATH_V8_4, "V8.4 Markdown report"),
        (DOC_PATH_V8_4, "V8.4 documentation"),
        (DATACARD_MD_PATH_V8_4, "V8.4 datacard"),
    ]:
        path = project_root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
        else:
            errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors = _validate_exact_keys(safety, SAFETY_KEYS, "V8.4 safety")
    if safety.get("public_read_only") is not True:
        errors.append("V8.4 public_read_only safety flag must be true")
    if safety.get("labels_enabled") is not True:
        errors.append("V8.4 labels_enabled safety flag must be true")
    if safety.get("dataset_enabled") is not True:
        errors.append("V8.4 dataset_enabled safety flag must be true")
    for key in SAFETY_KEYS - {"public_read_only", "labels_enabled", "dataset_enabled"}:
        if safety.get(key) is not False:
            errors.append(f"V8.4 safety flag must be false: {key}")
    return errors


def _find_forbidden_v8_4_artifacts(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V8_4_PATHS:
        path = project_root / relative
        if path.exists():
            errors.append(f"Forbidden V8.4 artifact detected: {relative}")
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"} for part in path.parts):
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V8.4 model artifact detected: {path.relative_to(project_root).as_posix()}")
    return sorted(set(errors))


def _validate_exact_keys(payload: Any, expected: set[str], label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    actual = set(payload)
    errors: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"{label} missing keys: {missing}")
    if unexpected:
        errors.append(f"{label} unexpected keys: {unexpected}")
    return errors


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
