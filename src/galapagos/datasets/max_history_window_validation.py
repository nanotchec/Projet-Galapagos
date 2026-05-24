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
from galapagos.datasets.max_history_window import (
    build_max_history_offline_supervised_dataset_v5_3,
    build_split_frame_v5_3,
    dataset_output_path,
    input_feature_path,
    input_label_path,
    load_v5_1_feature_manifest,
    load_v5_2_label_manifest,
    split_output_path,
)
from galapagos.datasets.max_history_window_quality import assess_max_history_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V5_3,
    DATASET_SCHEMA_VERSION_V5_3,
    DATACARD_MD_PATH_V5_3,
    DOC_PATH_V5_3,
    EXPECTED_LIMITATIONS_V5_3,
    FEATURE_VALUE_COLUMNS,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V5_3,
    REPORT_JSON_PATH_V5_3,
    REPORT_MD_PATH_V5_3,
    SPLIT_COLUMNS_V5_3,
    SPLIT_POLICY_V5_3,
    TIMEFRAMES_V5_3,
    VERSION_V5_3,
)
from galapagos.features.max_history_window import MANIFEST_PATH_V5_1 as FEATURE_MANIFEST_PATH_V5_1
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


DATASET_RUN_ID_PATTERN_V5_3 = re.compile(r"^v5_3_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TIMEFRAMES_V5_3)
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


def validate_max_history_offline_supervised_dataset_v5_3(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V5_3
    report_path = project_root / REPORT_JSON_PATH_V5_3
    if not manifest_path.exists():
        return _result([f"missing V5.3 manifest: {MANIFEST_PATH_V5_3}"], warnings)
    if not report_path.exists():
        return _result([f"missing V5.3 quality report: {REPORT_JSON_PATH_V5_3}"], warnings)

    feature_manifest = load_v5_1_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_input_manifest_windows(feature_manifest, label_manifest))
    errors.extend(_validate_manifest_structure(project_root, manifest, feature_manifest, label_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V5.3 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V5.3 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v5_3_artifacts(project_root))

    if not errors:
        physical_quality: dict[str, dict[str, Any]] = {}
        for timeframe in TIMEFRAMES_V5_3:
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
            errors.append(f"missing V5.3 {label} file for {timeframe}: {path.relative_to(project_root)}")
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

    errors.extend(
        _compare_io_block(
            manifest["input_features"][timeframe],
            feature_path,
            feature_sha,
            len(features),
            project_root,
            f"V5.3 manifest input_features.{timeframe}",
            include_bytes=False,
        )
    )
    errors.extend(
        _compare_io_block(
            manifest["input_labels"][timeframe],
            label_path,
            label_sha,
            len(labels),
            project_root,
            f"V5.3 manifest input_labels.{timeframe}",
            include_bytes=False,
        )
    )
    errors.extend(
        _compare_io_block(
            manifest["outputs"][timeframe],
            dataset_path,
            dataset_sha,
            len(dataset),
            project_root,
            f"V5.3 manifest outputs.{timeframe}",
            include_bytes=True,
        )
    )
    errors.extend(
        _compare_io_block(
            manifest["splits"][timeframe],
            split_path,
            split_sha,
            len(splits),
            project_root,
            f"V5.3 manifest splits.{timeframe}",
            include_bytes=True,
        )
    )
    errors.extend(_validate_dataset_schema(dataset, timeframe))
    errors.extend(_validate_split_frame(dataset, splits, timeframe))
    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V5.3 dataset row count does not match sources for {timeframe}")
    errors.extend(_validate_dataset_values_against_sources(timeframe, dataset, features, labels, manifest["dataset_run_id"], feature_sha, label_sha))

    feature_source_columns = [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]
    label_source_columns = [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]
    try:
        assert_frame_equal(dataset[feature_source_columns].reset_index(drop=True), features[feature_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V5.3 dataset feature source mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(dataset[label_source_columns].reset_index(drop=True), labels[label_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V5.3 dataset label source mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    quality = assess_max_history_dataset_quality(
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


def _validate_dataset_schema(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    errors: list[str] = []
    label = f" for {timeframe}" if timeframe else ""
    if list(frame.columns) != DATASET_COLUMNS_V5_3:
        errors.append(f"V5.3 dataset schema mismatch{label}")
    forbidden = [
        column
        for column in frame.columns
        if column not in DATASET_COLUMNS_V5_3 and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    if forbidden:
        errors.append(f"V5.3 dataset forbidden columns{label}: {forbidden}")
    return errors


def _validate_split_frame(dataset: pd.DataFrame, splits: pd.DataFrame, timeframe: str = "") -> list[str]:
    errors: list[str] = []
    label = f" for {timeframe}" if timeframe else ""
    if list(splits.columns) != SPLIT_COLUMNS_V5_3:
        errors.append(f"V5.3 split schema mismatch{label}")
        return errors
    try:
        expected = build_split_frame_v5_3(dataset)
        assert_frame_equal(splits.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V5.3 split physical mismatch{label}: {str(exc).splitlines()[0]}")
    if "walk_forward_group" not in splits.columns or splits["walk_forward_group"].isna().any():
        errors.append(f"V5.3 walk_forward_group missing{label}")
    return errors


def _validate_dataset_temporal_rules(frame: pd.DataFrame, timeframe: str = "") -> list[str]:
    feature_sha = frame["source_features_sha256"].iloc[0] if "source_features_sha256" in frame.columns and len(frame) else ""
    label_sha = frame["source_labels_sha256"].iloc[0] if "source_labels_sha256" in frame.columns and len(frame) else ""
    required_split_columns = set(SPLIT_COLUMNS_V5_3) - {"walk_forward_group"}
    split_frame = build_split_frame_v5_3(frame) if required_split_columns.issubset(frame.columns) else pd.DataFrame()
    quality = assess_max_history_dataset_quality(
        frame,
        split_frame,
        expected_rows=len(frame),
        timeframe=timeframe or "dataset",
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    return [
        error
        for error in quality["errors"]
        if "rows mismatch" not in error and "split counts mismatch" not in error and "walk_forward_group missing" not in error
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
        expected = build_max_history_offline_supervised_dataset_v5_3(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha256,
            label_sha256=label_sha256,
            dataset_run_id=dataset_run_id,
        )
        assert_frame_equal(dataset_frame.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V5.3 dataset physical mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    except Exception as exc:
        errors.append(f"V5.3 dataset value validation failed for {timeframe}: {exc}")
    return errors


def _validate_manifest_structure(
    project_root: Path,
    manifest: dict[str, Any],
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V5.3 manifest"))
    if manifest.get("version") != VERSION_V5_3:
        errors.append("V5.3 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V5.3 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V5.3 manifest created_at_utc invalid")
    if not isinstance(manifest.get("dataset_run_id"), str) or DATASET_RUN_ID_PATTERN_V5_3.fullmatch(manifest["dataset_run_id"]) is None:
        errors.append("V5.3 manifest dataset_run_id invalid")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION_V5_3:
        errors.append("V5.3 manifest dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V5_3:
        errors.append("V5.3 manifest dataset_columns mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V5_3:
        errors.append("V5.3 manifest split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V5_3:
        errors.append("V5.3 manifest limitations mismatch")

    expected_feature_manifest = {
        "path": FEATURE_MANIFEST_PATH_V5_1.as_posix(),
        "sha256": sha256_file(project_root / FEATURE_MANIFEST_PATH_V5_1),
        "window_start": feature_manifest["input_ohlcv_manifest"]["window_start"],
        "window_end": feature_manifest["input_ohlcv_manifest"]["window_end"],
        "total_days": int(feature_manifest["input_ohlcv_manifest"]["total_days"]),
    }
    expected_label_manifest = {
        "path": LABEL_MANIFEST_PATH_V5_2.as_posix(),
        "sha256": sha256_file(project_root / LABEL_MANIFEST_PATH_V5_2),
        "window_start": label_manifest["input_ohlcv_manifest"]["window_start"],
        "window_end": label_manifest["input_ohlcv_manifest"]["window_end"],
        "total_days": int(label_manifest["input_ohlcv_manifest"]["total_days"]),
    }
    errors.extend(validate_exact_keys(manifest.get("input_features_manifest", {}), INPUT_MANIFEST_KEYS, "V5.3 manifest input_features_manifest"))
    errors.extend(validate_exact_keys(manifest.get("input_labels_manifest", {}), INPUT_MANIFEST_KEYS, "V5.3 manifest input_labels_manifest"))
    if manifest.get("input_features_manifest") != expected_feature_manifest:
        errors.append("V5.3 input_features_manifest mismatch")
    if manifest.get("input_labels_manifest") != expected_label_manifest:
        errors.append("V5.3 input_labels_manifest mismatch")

    for section in ["input_features", "input_labels", "outputs", "splits", "quality"]:
        errors.extend(validate_exact_keys(manifest.get(section, {}), TIMEFRAME_KEYS, f"V5.3 manifest {section}"))
    errors.extend(validate_exact_keys(manifest.get("split_policy", {}), SPLIT_POLICY_KEYS, "V5.3 manifest split_policy"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), SAFETY_KEYS, "V5.3 manifest safety"))
    window_start = feature_manifest["input_ohlcv_manifest"]["window_start"]
    window_end = feature_manifest["input_ohlcv_manifest"]["window_end"]
    for timeframe in TIMEFRAMES_V5_3:
        errors.extend(validate_exact_keys(manifest.get("input_features", {}).get(timeframe, {}), INPUT_KEYS, f"V5.3 manifest input_features.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_labels", {}).get(timeframe, {}), INPUT_KEYS, f"V5.3 manifest input_labels.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V5.3 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("splits", {}).get(timeframe, {}), OUTPUT_KEYS, f"V5.3 manifest splits.{timeframe}"))
        quality = manifest.get("quality", {}).get(timeframe, {})
        errors.extend(validate_exact_keys(quality, QUALITY_KEYS, f"V5.3 manifest quality.{timeframe}"))
        if isinstance(quality, dict):
            errors.extend(validate_exact_keys(quality.get("split_counts", {}), SPLIT_COUNT_KEYS, f"V5.3 manifest quality.{timeframe}.split_counts"))
            errors.extend(validate_exact_keys(quality.get("label_valid_counts_by_horizon", {}), HORIZON_KEYS, f"V5.3 manifest quality.{timeframe}.label_valid_counts_by_horizon"))
            errors.extend(validate_exact_keys(quality.get("null_counts_by_column", {}), set(DATASET_COLUMNS_V5_3), f"V5.3 manifest quality.{timeframe}.null_counts_by_column"))
            if not quality.get("walk_forward_group_counts"):
                errors.append(f"V5.3 manifest quality.{timeframe}.walk_forward_group_counts empty")
        if manifest.get("outputs", {}).get(timeframe, {}).get("path") != str(dataset_output_path(project_root, timeframe, window_start, window_end).relative_to(project_root)):
            errors.append(f"V5.3 manifest output path mismatch for {timeframe}")
        if manifest.get("splits", {}).get(timeframe, {}).get("path") != str(split_output_path(project_root, timeframe, window_start, window_end).relative_to(project_root)):
            errors.append(f"V5.3 manifest split path mismatch for {timeframe}")
    return errors


def _validate_input_manifest_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    feature_window = feature_manifest.get("input_ohlcv_manifest", {})
    label_window = label_manifest.get("input_ohlcv_manifest", {})
    for field in ["window_start", "window_end", "total_days"]:
        if feature_window.get(field) != label_window.get(field):
            errors.append(f"V5.3 input manifest window mismatch for {field}")
    for timeframe in TIMEFRAMES_V5_3:
        if int(feature_manifest.get("outputs", {}).get(timeframe, {}).get("rows", -1)) != int(
            label_manifest.get("outputs", {}).get(timeframe, {}).get("rows", -2)
        ):
            errors.append(f"V5.3 input manifest rows mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V5.3 quality report")
    if report != manifest:
        for path in _compare_nested(manifest, report, "V5.3 quality report"):
            errors.append(f"V5.3 quality report mismatch for {path}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        for path in _compare_nested(quality, manifest["quality"].get(timeframe), timeframe):
            errors.append(f"V5.3 manifest quality mismatch for {path}")
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
        return ["V5.3 manifest safety must be an object"]
    return [f"V5.3 safety flag {key} must be {value}" for key, value in expected.items() if safety.get(key) is not value]


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    required_clauses = [
        "ne valide aucune strategie",
        "ne produit aucun modele ML",
        "ne produit aucun backtest",
        "ne produit aucun signal de trading",
        "ne produit aucun ordre",
        "n'autorise aucun paper live",
        "n'autorise aucun trading reel",
    ]
    for relative, label in [
        (REPORT_MD_PATH_V5_3, "V5.3 Markdown report"),
        (DATACARD_MD_PATH_V5_3, "V5.3 data card"),
        (DOC_PATH_V5_3, "V5.3 documentation"),
    ]:
        path = project_root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(validate_markdown_forbidden_claims(text, label))
        normalized = text.replace("’", "'").casefold()
        for clause in required_clauses:
            if clause.casefold() not in normalized:
                errors.append(f"{label} missing safety clause: {clause}")
    return errors


def _find_forbidden_v5_3_artifacts(project_root: Path) -> list[str]:
    forbidden_roots = [
        Path("models"),
        Path("checkpoints"),
        Path("reports/strategies"),
        Path("reports/signals"),
        Path("reports/predictions"),
        Path("orders"),
        Path("execution"),
        Path("data/research/v5_3/ml"),
        Path("data/research/v5_3/backtests"),
        Path("data/research/v5_3/strategies"),
        Path("data/research/v5_3/models"),
    ]
    errors: list[str] = []
    for relative in forbidden_roots:
        if (project_root / relative).exists():
            errors.append(f"Forbidden V5.3 artifact detected: {relative.as_posix()}")
    backtests = project_root / "reports/backtests"
    if backtests.exists():
        errors.append("Forbidden V5.3 artifact detected: reports/backtests")
        for child in sorted(backtests.rglob("*")):
            if child.is_file():
                errors.append(f"Forbidden V5.3 artifact detected: {child.relative_to(project_root).as_posix()}")
    for suffix in FORBIDDEN_MODEL_SUFFIXES:
        matches = [
            path
            for path in project_root.rglob(f"*{suffix}")
            if not any(part in IGNORED_SCAN_PARTS for part in path.relative_to(project_root).parts)
        ]
        for path in matches:
            errors.append(f"Forbidden V5.3 model artifact detected: {path.relative_to(project_root).as_posix()}")
    reports_ml = project_root / "reports/ml"
    if reports_ml.exists():
        for path in sorted(reports_ml.rglob("*v5_3*")):
            if path.is_file():
                errors.append(f"Forbidden V5.3 ML report detected: {path.relative_to(project_root).as_posix()}")
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
    return {"version": VERSION_V5_3, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
