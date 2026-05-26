from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.refined_ohlcv_trades_window import (
    build_report_v9_1,
    dataset_output_path,
    filter_labels_to_v9_1_window,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v9_0_feature_manifest,
    split_output_path,
)
from galapagos.datasets.refined_ohlcv_trades_window_quality import (
    assess_refined_ohlcv_trades_dataset_quality_v9_1,
    forbidden_dataset_columns_v9_1,
)
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V9_1,
    DATASET_SCHEMA_VERSION_V9_1,
    DATACARD_MD_PATH_V9_1,
    DOC_PATH_V9_1,
    EXPECTED_LIMITATIONS_V9_1,
    EXPECTED_ROWS_V9_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V9_1,
    REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1,
    REPORT_JSON_PATH_V9_1,
    REPORT_MD_PATH_V9_1,
    SPLIT_COLUMNS_V9_1,
    SPLIT_POLICY_V9_1,
    TIMEFRAMES_V9_1,
    VERSION_V9_1,
)
from galapagos.features.refined_ohlcv_trades import MANIFEST_PATH_V9_0 as FEATURE_MANIFEST_PATH_V9_0
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.validation.safety import scan_payload_for_forbidden_claims, validate_markdown_forbidden_claims


DATASET_RUN_ID_PATTERN_V9_1 = re.compile(r"^v9_1_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
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
FORBIDDEN_V9_1_PATHS = [
    "data/research/v9_1/ml",
    "data/research/v9_1/backtests",
    "data/research/v9_1/strategies",
    "reports/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
    "models",
    "checkpoints",
]


def validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V9_1
    report_path = project_root / REPORT_JSON_PATH_V9_1
    if not manifest_path.exists():
        return _result([f"missing V9.1 manifest: {MANIFEST_PATH_V9_1}"], warnings)
    if not report_path.exists():
        return _result([f"missing V9.1 quality report: {REPORT_JSON_PATH_V9_1}"], warnings)

    feature_manifest = load_v9_0_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_input_manifest_windows(feature_manifest, label_manifest))
    errors.extend(_validate_manifest_structure(project_root, manifest, feature_manifest, label_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V9.1 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V9.1 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v9_1_artifacts(project_root))

    if not errors:
        physical_quality: dict[str, dict[str, Any]] = {}
        for timeframe in TIMEFRAMES_V9_1:
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
            errors.append(f"missing V9.1 {label} file for {timeframe}: {path.relative_to(project_root)}")
    if errors:
        return errors

    features = read_parquet(feature_path)
    labels = filter_labels_to_v9_1_window(read_parquet(label_path))
    dataset = read_parquet(dataset_path)
    split_frame = read_parquet(split_path)
    feature_sha = sha256_file(feature_path)
    label_sha = sha256_file(label_path)
    dataset_sha = sha256_file(dataset_path)
    split_sha = sha256_file(split_path)

    errors.extend(_compare_io_block(manifest["input_features"][timeframe], feature_path, feature_sha, len(features), project_root, f"V9.1 manifest input_features.{timeframe}", include_bytes=False))
    if manifest["input_labels_filtered"][timeframe]["rows"] != len(labels):
        errors.append(f"V9.1 manifest input_labels_filtered.{timeframe} rows mismatch")
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], dataset_path, dataset_sha, len(dataset), project_root, f"V9.1 manifest outputs.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["splits"][timeframe], split_path, split_sha, len(split_frame), project_root, f"V9.1 manifest splits.{timeframe}", include_bytes=True))
    errors.extend(validate_dataset_schema_v9_1(dataset, timeframe))
    errors.extend(validate_split_frame_v9_1(dataset, split_frame, timeframe))
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V9.1 dataset row count does not match sources for {timeframe}")
    errors.extend(validate_dataset_values_against_sources_v9_1(timeframe, dataset, features, labels, manifest["dataset_run_id"], feature_sha, label_sha))
    errors.extend(validate_dataset_source_value_equality_v9_1(timeframe, dataset, features, labels))
    errors.extend(validate_feature_source_has_no_labels_v9_1(timeframe, features))

    quality = assess_refined_ohlcv_trades_dataset_quality_v9_1(
        dataset,
        split_frame,
        expected_rows=EXPECTED_ROWS_V9_1[timeframe],
        timeframe=timeframe,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def validate_dataset_schema_v9_1(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(frame.columns) != DATASET_COLUMNS_V9_1:
        errors.append(f"V9.1 dataset schema mismatch{label}")
    forbidden = forbidden_dataset_columns_v9_1(frame)
    if forbidden:
        errors.append(f"V9.1 dataset contains forbidden columns{label}: {forbidden}")
    return errors


def validate_split_frame_v9_1(dataset: pd.DataFrame, split_frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(split_frame.columns) != SPLIT_COLUMNS_V9_1:
        errors.append(f"V9.1 split schema mismatch{label}")
    if len(split_frame) != len(dataset):
        errors.append(f"V9.1 split rows mismatch dataset rows{label}")
        return errors
    try:
        assert_frame_equal(split_frame.reset_index(drop=True), dataset[SPLIT_COLUMNS_V9_1].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V9.1 split file mismatch dataset split columns{label}: {str(exc).splitlines()[0]}")
    if "walk_forward_group" not in split_frame.columns or split_frame["walk_forward_group"].isna().any():
        errors.append(f"V9.1 walk_forward_group missing{label}")
    if "event_ts" in split_frame.columns and not pd.to_datetime(split_frame["event_ts"], utc=True).is_monotonic_increasing:
        errors.append(f"V9.1 split temporal order invalid{label}")
    if "split_order" in split_frame.columns and not split_frame["split_order"].is_monotonic_increasing:
        errors.append(f"V9.1 split_order invalid{label}")
    if "split" in split_frame.columns:
        rank = split_frame["split"].map({"train": 0, "validation": 1, "test": 2})
        if not bool(rank.notna().all() and rank.is_monotonic_increasing):
            errors.append(f"V9.1 split role temporal order invalid{label}")
    return errors


def validate_dataset_values_against_sources_v9_1(
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
        errors.append(f"V9.1 dataset_run_id mismatch for {timeframe}")
    if set(dataset["dataset_schema_version"].astype(str).unique()) != {DATASET_SCHEMA_VERSION_V9_1}:
        errors.append(f"V9.1 dataset_schema_version mismatch for {timeframe}")
    if set(dataset["source_features_sha256"].astype(str).unique()) != {feature_sha}:
        errors.append(f"V9.1 source_features_sha256 mismatch for {timeframe}")
    if set(dataset["source_labels_sha256"].astype(str).unique()) != {label_sha}:
        errors.append(f"V9.1 source_labels_sha256 mismatch for {timeframe}")
    try:
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), features[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), labels[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V9.1 join keys mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    if not (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all():
        errors.append(f"V9.1 feature_available_ts > decision_ts for {timeframe}")
    valid_mask = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    if valid_mask.any() and not (
        pd.to_datetime(dataset.loc[valid_mask, "label_available_ts"], utc=True)
        > pd.to_datetime(dataset.loc[valid_mask, "decision_ts"], utc=True)
    ).all():
        errors.append(f"V9.1 label_available_ts <= decision_ts for valid labels in {timeframe}")
    return errors


def validate_dataset_source_value_equality_v9_1(
    timeframe: str,
    dataset: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []
    try:
        assert_frame_equal(
            dataset[REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1].reset_index(drop=True),
            features[REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-9,
            atol=1e-12,
        )
    except AssertionError as exc:
        errors.append(f"V9.1 feature values modified for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(
            dataset[LABEL_VALUE_COLUMNS].reset_index(drop=True),
            labels[LABEL_VALUE_COLUMNS].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-9,
            atol=1e-12,
        )
    except AssertionError as exc:
        errors.append(f"V9.1 label values modified for {timeframe}: {str(exc).splitlines()[0]}")
    return errors


def validate_feature_source_has_no_labels_v9_1(timeframe: str, features: pd.DataFrame) -> list[str]:
    forbidden = [column for column in features.columns if column.startswith("future_") or column.startswith("label_")]
    forbidden.extend(column for column in features.columns if column.startswith("direction_") or column.startswith("up_down_flat_"))
    return [f"V9.1 feature source contains label-like columns for {timeframe}: {sorted(set(forbidden))}"] if forbidden else []


def _validate_manifest_structure(
    project_root: Path,
    manifest: dict[str, Any],
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if set(manifest) != MANIFEST_KEYS:
        errors.append("V9.1 manifest keys mismatch")
    if manifest.get("version") != VERSION_V9_1:
        errors.append("V9.1 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.1 manifest status must be PASS")
    if not DATASET_RUN_ID_PATTERN_V9_1.match(str(manifest.get("dataset_run_id", ""))):
        errors.append("V9.1 dataset_run_id format mismatch")
    if set(manifest.get("input_features_manifest", {})) != FEATURE_MANIFEST_KEYS:
        errors.append("V9.1 input_features_manifest keys mismatch")
    if set(manifest.get("input_labels_manifest", {})) != LABEL_MANIFEST_KEYS:
        errors.append("V9.1 input_labels_manifest keys mismatch")
    if manifest.get("input_features_manifest", {}).get("path") != FEATURE_MANIFEST_PATH_V9_0.as_posix():
        errors.append("V9.1 input_features_manifest path mismatch")
    if manifest.get("input_features_manifest", {}).get("sha256") != sha256_file(project_root / FEATURE_MANIFEST_PATH_V9_0):
        errors.append("V9.1 input_features_manifest sha256 mismatch")
    if manifest.get("input_labels_manifest", {}).get("path") != LABEL_MANIFEST_PATH_V5_2.as_posix():
        errors.append("V9.1 input_labels_manifest path mismatch")
    if manifest.get("input_labels_manifest", {}).get("sha256") != sha256_file(project_root / LABEL_MANIFEST_PATH_V5_2):
        errors.append("V9.1 input_labels_manifest sha256 mismatch")
    if manifest.get("input_features_manifest", {}).get("window_start") != feature_manifest["window"]["window_start"]:
        errors.append("V9.1 feature input window_start mismatch")
    if manifest.get("input_features_manifest", {}).get("window_end") != feature_manifest["window"]["window_end"]:
        errors.append("V9.1 feature input window_end mismatch")
    if manifest.get("input_labels_manifest", {}).get("source_window_start") != label_manifest["input_ohlcv_manifest"]["window_start"]:
        errors.append("V9.1 label source_window_start mismatch")
    if manifest.get("input_labels_manifest", {}).get("source_window_end") != label_manifest["input_ohlcv_manifest"]["window_end"]:
        errors.append("V9.1 label source_window_end mismatch")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION_V9_1:
        errors.append("V9.1 dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V9_1:
        errors.append("V9.1 dataset_columns mismatch")
    if manifest.get("feature_columns_count") != len(REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1):
        errors.append("V9.1 feature_columns_count mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V9_1:
        errors.append("V9.1 split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_1:
        errors.append("V9.1 limitations mismatch")
    for key_name, value, expected_keys in [
        ("input_features", manifest.get("input_features", {}), INPUT_FEATURE_KEYS),
        ("input_labels_filtered", manifest.get("input_labels_filtered", {}), INPUT_LABEL_FILTERED_KEYS),
        ("outputs", manifest.get("outputs", {}), OUTPUT_KEYS),
        ("splits", manifest.get("splits", {}), OUTPUT_KEYS),
    ]:
        if set(value) != set(TIMEFRAMES_V9_1):
            errors.append(f"V9.1 {key_name} timeframes mismatch")
        for timeframe, payload in value.items():
            if set(payload) != expected_keys:
                errors.append(f"V9.1 {key_name}.{timeframe} keys mismatch")
    return errors


def _validate_input_manifest_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if feature_manifest["window"]["window_start"] != "2023-03-25" or feature_manifest["window"]["window_end"] != "2024-03-24":
        errors.append("V9.1 feature manifest window mismatch")
    label_window_start = label_manifest["input_ohlcv_manifest"]["window_start"]
    label_window_end = label_manifest["input_ohlcv_manifest"]["window_end"]
    if "2023-03-25" < label_window_start or "2024-03-24" > label_window_end:
        errors.append("V9.1 labels do not cover feature window")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    return [] if report == build_report_v9_1(manifest) else ["V9.1 report JSON differs from deterministic manifest projection"]


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for path in [REPORT_MD_PATH_V9_1, DATACARD_MD_PATH_V9_1, DOC_PATH_V9_1]:
        full = project_root / path
        if not full.exists():
            errors.append(f"missing V9.1 markdown: {path}")
            continue
        errors.extend(validate_markdown_forbidden_claims(full.read_text(encoding="utf-8"), f"V9.1 markdown {path}"))
    return errors


def _find_forbidden_v9_1_artifacts(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V9_1_PATHS:
        path = project_root / relative
        if path.exists():
            errors.append(f"forbidden V9.1 artifact exists: {relative}")
    for suffix in FORBIDDEN_MODEL_SUFFIXES:
        for path in project_root.glob(f"**/*{suffix}"):
            if ".venv" not in path.parts and "__pycache__" not in path.parts:
                errors.append(f"forbidden persistent model file exists: {path.relative_to(project_root)}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if set(manifest.get("quality", {})) != set(physical_quality):
        errors.append("V9.1 quality timeframe keys mismatch")
        return errors
    for timeframe, quality in physical_quality.items():
        if manifest["quality"][timeframe] != quality:
            errors.append(f"V9.1 quality mismatch for {timeframe}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(safety) != SAFETY_KEYS:
        errors.append("V9.1 safety keys mismatch")
        return errors
    expected_false = SAFETY_KEYS - {"public_read_only", "labels_enabled", "dataset_enabled"}
    for key in expected_false:
        if safety.get(key) is not False:
            errors.append(f"V9.1 safety flag must be false: {key}")
    for key in ["public_read_only", "labels_enabled", "dataset_enabled"]:
        if safety.get(key) is not True:
            errors.append(f"V9.1 safety flag must be true: {key}")
    return errors


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
    if include_bytes:
        if int(payload.get("bytes", -1)) != path.stat().st_size:
            errors.append(f"{label} bytes mismatch")
        if payload.get("format") != "parquet":
            errors.append(f"{label} format mismatch")
    return errors


def _result(errors: list[str], warnings: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
