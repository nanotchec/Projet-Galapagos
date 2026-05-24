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
from galapagos.datasets.advanced_ohlcv_window import (
    build_report_v6_1,
    dataset_output_path,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v6_0_feature_manifest,
    split_output_path,
)
from galapagos.datasets.advanced_ohlcv_window_quality import assess_advanced_ohlcv_dataset_quality, forbidden_dataset_columns_v6_1
from galapagos.datasets.schemas import (
    ADVANCED_DATASET_FEATURE_COLUMNS_V6_1,
    DATASET_COLUMNS_V6_1,
    DATASET_SCHEMA_VERSION_V6_1,
    DATACARD_MD_PATH_V6_1,
    DOC_PATH_V6_1,
    EXPECTED_LIMITATIONS_V6_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V6_1,
    REPORT_JSON_PATH_V6_1,
    REPORT_MD_PATH_V6_1,
    SPLIT_COLUMNS_V6_1,
    SPLIT_POLICY_V6_1,
    TIMEFRAMES_V6_1,
    VERSION_V6_1,
)
from galapagos.features.advanced_ohlcv import MANIFEST_PATH_V6_0 as FEATURE_MANIFEST_PATH_V6_0
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


DATASET_RUN_ID_PATTERN_V6_1 = re.compile(r"^v6_1_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V6_1)
INPUT_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days"}
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
SPLIT_POLICY_KEYS = {"train_ratio", "validation_ratio", "test_ratio", "shuffle", "purge_embargo", "walk_forward_grouping"}
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
    "input_features_manifest",
    "input_labels_manifest",
    "input_features",
    "input_labels",
    "outputs",
    "splits",
    "dataset_schema_version",
    "dataset_columns",
    "advanced_feature_columns_count",
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
    "walk_forward_group_counts",
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
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
FORBIDDEN_V6_1_PATHS = [
    "data/research/v6_1/ml",
    "data/research/v6_1/backtests",
    "data/research/v6_1/strategies",
    "reports/ml/advanced_ohlcv_offline_ml_research_v6_1.json",
    "reports/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
    "models",
    "checkpoints",
]


def validate_advanced_ohlcv_offline_supervised_dataset_v6_1(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V6_1
    report_path = project_root / REPORT_JSON_PATH_V6_1
    if not manifest_path.exists():
        return _result([f"missing V6.1 manifest: {MANIFEST_PATH_V6_1}"], warnings)
    if not report_path.exists():
        return _result([f"missing V6.1 quality report: {REPORT_JSON_PATH_V6_1}"], warnings)

    feature_manifest = load_v6_0_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_input_manifest_windows(feature_manifest, label_manifest))
    errors.extend(_validate_manifest_structure(project_root, manifest, feature_manifest, label_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V6.1 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V6.1 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v6_1_artifacts(project_root))

    if not errors:
        physical_quality: dict[str, dict[str, Any]] = {}
        for timeframe in TIMEFRAMES_V6_1:
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
    window_start = feature_manifest["input_ohlcv_manifest"]["window_start"]
    window_end = feature_manifest["input_ohlcv_manifest"]["window_end"]
    feature_path = input_feature_path(project_root, timeframe, feature_manifest)
    label_path = input_label_path(project_root, timeframe, label_manifest)
    dataset_path = dataset_output_path(project_root, timeframe, window_start, window_end)
    split_path = split_output_path(project_root, timeframe, window_start, window_end)
    for label, path in [("features", feature_path), ("labels", label_path), ("dataset", dataset_path), ("splits", split_path)]:
        if not path.exists():
            errors.append(f"missing V6.1 {label} file for {timeframe}: {path.relative_to(project_root)}")
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

    errors.extend(_compare_io_block(manifest["input_features"][timeframe], feature_path, feature_sha, len(features), project_root, f"V6.1 manifest input_features.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["input_labels"][timeframe], label_path, label_sha, len(labels), project_root, f"V6.1 manifest input_labels.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], dataset_path, dataset_sha, len(dataset), project_root, f"V6.1 manifest outputs.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["splits"][timeframe], split_path, split_sha, len(splits), project_root, f"V6.1 manifest splits.{timeframe}", include_bytes=True))
    errors.extend(validate_dataset_schema_v6_1(dataset, timeframe))
    errors.extend(validate_split_frame_v6_1(dataset, splits, timeframe))
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V6.1 dataset row count does not match sources for {timeframe}")
    errors.extend(validate_dataset_values_against_sources_v6_1(timeframe, dataset, features, labels, manifest["dataset_run_id"], feature_sha, label_sha))
    errors.extend(validate_dataset_source_value_equality_v6_1(timeframe, dataset, features, labels))

    quality = assess_advanced_ohlcv_dataset_quality(
        dataset,
        splits,
        expected_rows=int(feature_manifest["outputs"][timeframe]["rows"]),
        timeframe=timeframe,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def validate_dataset_schema_v6_1(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(frame.columns) != DATASET_COLUMNS_V6_1:
        errors.append(f"V6.1 dataset schema mismatch{label}")
    forbidden = forbidden_dataset_columns_v6_1(frame)
    if forbidden:
        errors.append(f"V6.1 dataset contains forbidden columns{label}: {forbidden}")
    if "macd_like_signal" not in frame.columns:
        errors.append(f"V6.1 dataset missing allowed macd_like_signal feature{label}")
    return errors


def validate_split_frame_v6_1(dataset: pd.DataFrame, splits: pd.DataFrame, timeframe: str = "") -> list[str]:
    label = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(splits.columns) != SPLIT_COLUMNS_V6_1:
        errors.append(f"V6.1 split schema mismatch{label}")
    if len(splits) != len(dataset):
        errors.append(f"V6.1 split rows mismatch dataset rows{label}")
        return errors
    try:
        assert_frame_equal(splits.reset_index(drop=True), dataset[SPLIT_COLUMNS_V6_1].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V6.1 split file mismatch dataset split columns{label}: {str(exc).splitlines()[0]}")
    if "walk_forward_group" not in splits.columns or splits["walk_forward_group"].isna().any():
        errors.append(f"V6.1 walk_forward_group missing{label}")
    return errors


def validate_dataset_values_against_sources_v6_1(
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
        errors.append(f"V6.1 dataset_run_id mismatch for {timeframe}")
    if set(dataset["dataset_schema_version"].astype(str).unique()) != {DATASET_SCHEMA_VERSION_V6_1}:
        errors.append(f"V6.1 dataset_schema_version mismatch for {timeframe}")
    if set(dataset["source_features_sha256"].astype(str).unique()) != {feature_sha}:
        errors.append(f"V6.1 source_features_sha256 mismatch for {timeframe}")
    if set(dataset["source_labels_sha256"].astype(str).unique()) != {label_sha}:
        errors.append(f"V6.1 source_labels_sha256 mismatch for {timeframe}")
    try:
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), features[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
        assert_frame_equal(dataset[JOIN_KEYS].reset_index(drop=True), labels[JOIN_KEYS].reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        errors.append(f"V6.1 join keys mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    if "feature_available_ts" in dataset.columns and "decision_ts" in dataset.columns:
        if not bool((pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()):
            errors.append(f"V6.1 feature_available_ts > decision_ts for {timeframe}")
    valid_mask = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    if valid_mask.any():
        if not bool(
            (
                pd.to_datetime(dataset.loc[valid_mask, "label_available_ts"], utc=True)
                > pd.to_datetime(dataset.loc[valid_mask, "decision_ts"], utc=True)
            ).all()
        ):
            errors.append(f"V6.1 label_available_ts <= decision_ts for valid labels {timeframe}")
    feature_forbidden = [column for column in features.columns if column.startswith("future_") or column.startswith("label") or column == "target"]
    if feature_forbidden:
        errors.append(f"V6.1 source features contain labels/future columns for {timeframe}: {feature_forbidden}")
    return errors


def validate_dataset_source_value_equality_v6_1(
    timeframe: str,
    dataset: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []
    feature_source_columns = [*JOIN_KEYS, "feature_available_ts", *ADVANCED_DATASET_FEATURE_COLUMNS_V6_1]
    label_source_columns = [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]
    try:
        assert_frame_equal(
            dataset[feature_source_columns].reset_index(drop=True),
            features[feature_source_columns].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            atol=1e-6,
            rtol=1e-6,
        )
    except AssertionError as exc:
        errors.append(f"V6.1 dataset feature source mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(
            dataset[label_source_columns].reset_index(drop=True),
            labels[label_source_columns].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            atol=1e-12,
            rtol=1e-12,
        )
    except AssertionError as exc:
        errors.append(f"V6.1 dataset label source mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    return errors


def _validate_manifest_structure(
    project_root: Path,
    manifest: dict[str, Any],
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V6.1 manifest"))
    if manifest.get("version") != VERSION_V6_1:
        errors.append("V6.1 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V6.1 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str):
        errors.append("V6.1 manifest created_at_utc missing")
    else:
        try:
            datetime.fromisoformat(manifest["created_at_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            errors.append("V6.1 manifest created_at_utc invalid")
    run_id = manifest.get("dataset_run_id")
    if not isinstance(run_id, str) or DATASET_RUN_ID_PATTERN_V6_1.fullmatch(run_id) is None:
        errors.append("V6.1 dataset_run_id invalid")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION_V6_1:
        errors.append("V6.1 dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V6_1:
        errors.append("V6.1 dataset_columns mismatch")
    if manifest.get("advanced_feature_columns_count") != 158:
        errors.append("V6.1 advanced_feature_columns_count mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V6_1:
        errors.append("V6.1 split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V6_1:
        errors.append("V6.1 limitations mismatch")

    errors.extend(_validate_manifest_reference(project_root, manifest.get("input_features_manifest"), FEATURE_MANIFEST_PATH_V6_0, feature_manifest["input_ohlcv_manifest"], "input_features_manifest"))
    errors.extend(_validate_manifest_reference(project_root, manifest.get("input_labels_manifest"), LABEL_MANIFEST_PATH_V5_2, label_manifest["input_ohlcv_manifest"], "input_labels_manifest"))

    for section, keys in [("input_features", INPUT_KEYS), ("input_labels", INPUT_KEYS), ("outputs", OUTPUT_KEYS), ("splits", OUTPUT_KEYS), ("quality", QUALITY_KEYS)]:
        payload = manifest.get(section, {})
        errors.extend(validate_exact_keys(payload, TIMEFRAME_KEYS, f"V6.1 manifest {section}"))
        for timeframe, block in payload.items():
            errors.extend(validate_exact_keys(block, keys, f"V6.1 manifest {section}.{timeframe}"))
    for timeframe in TIMEFRAMES_V6_1:
        for key, expected in [("split_counts", SPLIT_COUNT_KEYS), ("label_valid_counts_by_horizon", HORIZON_KEYS)]:
            errors.extend(validate_exact_keys(manifest.get("quality", {}).get(timeframe, {}).get(key), expected, f"V6.1 quality {timeframe}.{key}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V6.1 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    return errors


def _validate_manifest_reference(project_root: Path, payload: Any, expected_path: Path, source_window: dict[str, Any], label: str) -> list[str]:
    errors = validate_exact_keys(payload, INPUT_MANIFEST_KEYS, f"V6.1 manifest {label}")
    if errors:
        return errors
    expected = {
        "path": expected_path.as_posix(),
        "sha256": sha256_file(project_root / expected_path),
        "window_start": source_window["window_start"],
        "window_end": source_window["window_end"],
        "total_days": source_window["total_days"],
    }
    if payload != expected:
        errors.append(f"V6.1 {label} mismatch")
    return errors


def _validate_input_manifest_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    feature_window = feature_manifest["input_ohlcv_manifest"]
    label_window = label_manifest["input_ohlcv_manifest"]
    for key in ["window_start", "window_end", "total_days"]:
        if feature_window[key] != label_window[key]:
            errors.append(f"V6.1 input window mismatch for {key}")
    for timeframe in TIMEFRAMES_V6_1:
        if int(feature_manifest["outputs"][timeframe]["rows"]) != int(label_manifest["outputs"][timeframe]["rows"]):
            errors.append(f"V6.1 input row count mismatch for {timeframe}")
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
    expected = {"path": str(path.relative_to(project_root)), "sha256": sha256, "rows": int(rows)}
    if include_bytes:
        expected["bytes"] = path.stat().st_size
        expected["format"] = "parquet"
    return [f"{label}.{field} mismatch: got {payload.get(field)!r}, expected {value!r}" for field, value in expected.items() if payload.get(field) != value]


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V6_1:
        declared = manifest.get("quality", {}).get(timeframe)
        physical = physical_quality.get(timeframe)
        if declared is None or physical is None:
            errors.append(f"V6.1 quality missing for {timeframe}")
            continue
        for field in QUALITY_KEYS:
            if declared.get(field) != physical.get(field):
                errors.append(f"V6.1 quality mismatch for {timeframe}.{field}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V6.1 quality report")
    expected = build_report_v6_1(manifest)
    for field, value in expected.items():
        if report.get(field) != value:
            errors.append(f"V6.1 quality report {field} mismatch")
    return errors


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for path, label in [
        (project_root / REPORT_MD_PATH_V6_1, "V6.1 markdown"),
        (project_root / DATACARD_MD_PATH_V6_1, "V6.1 datacard"),
        (project_root / DOC_PATH_V6_1, "V6.1 docs"),
    ]:
        if not path.exists():
            errors.append(f"missing {label}: {path.relative_to(project_root)}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(validate_markdown_forbidden_claims(text, label))
        normalized = text.replace("’", "'").replace("é", "e").replace("è", "e").replace("à", "a")
        required = [
            "V6.1 ne valide aucune strategie",
            "V6.1 ne produit aucun modele ML",
            "V6.1 ne produit aucun backtest",
            "V6.1 ne produit aucun signal de trading",
            "V6.1 ne produit aucun ordre",
            "V6.1 n'autorise aucun paper live",
            "V6.1 n'autorise aucun trading reel",
            "macd_like_signal",
        ]
        for clause in required:
            if clause not in normalized:
                errors.append(f"{label} missing clause: {clause}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V6.1 public_read_only must be true")
    if safety.get("labels_enabled") is not True:
        errors.append("V6.1 labels_enabled must be true")
    if safety.get("dataset_enabled") is not True:
        errors.append("V6.1 dataset_enabled must be true")
    for flag in sorted(SAFETY_KEYS - {"public_read_only", "labels_enabled", "dataset_enabled"}):
        if safety.get(flag) is not False:
            errors.append(f"V6.1 safety flag {flag} must be false")
    return errors


def _find_forbidden_v6_1_artifacts(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V6_1_PATHS:
        path = project_root / relative
        if path.exists():
            errors.append(f"Forbidden V6.1 artifact detected: {relative}")
            if path.is_dir():
                for child in sorted(path.rglob("*")):
                    if child.is_file():
                        errors.append(f"Forbidden V6.1 artifact detected: {child.relative_to(project_root).as_posix()}")
    for path in project_root.rglob("*"):
        if any(part in IGNORED_SCAN_PARTS for part in path.parts) or not path.is_file():
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V6.1 model artifact detected: {path.relative_to(project_root).as_posix()}")
    return sorted(set(errors))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V6_1, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
