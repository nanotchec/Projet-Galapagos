from __future__ import annotations

import json
import re
from datetime import timezone, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.assembly import build_offline_supervised_dataset
from galapagos.datasets.quality import assess_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V2_7,
    DATASET_SCHEMA_VERSION,
    DATACARD_MD_PATH,
    EXPECTED_LIMITATIONS_V2_7,
    EXPECTED_ROWS_BY_TIMEFRAME,
    FEATURE_VALUE_COLUMNS,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SPLIT_COLUMNS_V2_7,
    SPLIT_POLICY_V2_7,
    TARGET_TIMEFRAMES,
    VERSION,
    get_dataset_gold_path,
    get_split_gold_path,
)
from galapagos.datasets.splits import build_split_frame
from galapagos.features.registry import get_feature_gold_path
from galapagos.labels.registry import get_label_gold_path
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4
from galapagos.features.validation import validate_causal_feature_store_v2_5
from galapagos.labels.validation import validate_label_factory_v2_6
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


DATASET_RUN_ID_PATTERN = re.compile(r"^v2_7_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
TIMEFRAME_KEYS = set(TARGET_TIMEFRAMES)
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
SPLIT_POLICY_KEYS = {"train_ratio", "validation_ratio", "test_ratio", "shuffle", "purge_embargo"}
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
HORIZON_KEYS = {"h1", "h3", "h5"}
SPLIT_COUNT_KEYS = {"train", "validation", "test"}


def validate_offline_supervised_dataset_v2_7(project_root: Path = Path(".")) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for label, validation in [
        ("V2.3.1 ingestion", validate_public_market_ingestion_v2_3(project_root)),
        ("V2.4.8 resampling", validate_ohlcv_resampling_v2_4(project_root)),
        ("V2.5.2 features", validate_causal_feature_store_v2_5(project_root)),
        ("V2.6.2 labels", validate_label_factory_v2_6(project_root)),
    ]:
        if not validation["passed"]:
            return _result([f"{label} validation failed: {validation['errors']}"], warnings)

    manifest_path = project_root / MANIFEST_PATH
    report_path = project_root / REPORT_JSON_PATH
    if not manifest_path.exists():
        return _result([f"missing V2.7 manifest: {MANIFEST_PATH}"], warnings)
    if not report_path.exists():
        return _result([f"missing V2.7 quality report: {REPORT_JSON_PATH}"], warnings)

    manifest = _load_json(manifest_path)
    report = _load_json(report_path)
    errors.extend(_validate_manifest_structure(project_root, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.7 manifest"))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V2.7 quality report"))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_artifacts(project_root))

    if errors:
        return _result(errors, warnings, manifest=manifest)

    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe in TARGET_TIMEFRAMES:
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
    feature_path = get_feature_gold_path(project_root, timeframe)
    label_path = get_label_gold_path(project_root, timeframe)
    dataset_path = get_dataset_gold_path(project_root, timeframe)
    split_path = get_split_gold_path(project_root, timeframe)

    for label, path in [
        ("features", feature_path),
        ("labels", label_path),
        ("dataset", dataset_path),
        ("splits", split_path),
    ]:
        if not path.exists():
            errors.append(f"missing V2.7 {label} file for {timeframe}: {path.relative_to(project_root)}")
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

    errors.extend(_compare_io_block(manifest["input_features"][timeframe], feature_path, feature_sha, len(features), project_root, f"V2.7 manifest input_features.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["input_labels"][timeframe], label_path, label_sha, len(labels), project_root, f"V2.7 manifest input_labels.{timeframe}", include_bytes=False))
    errors.extend(_compare_io_block(manifest["outputs"][timeframe], dataset_path, dataset_sha, len(dataset), project_root, f"V2.7 manifest output.{timeframe}", include_bytes=True))
    errors.extend(_compare_io_block(manifest["splits"][timeframe], split_path, split_sha, len(splits), project_root, f"V2.7 manifest splits.{timeframe}", include_bytes=True))

    if list(dataset.columns) != DATASET_COLUMNS_V2_7:
        errors.append(f"V2.7 dataset schema mismatch for {timeframe}")
    if list(splits.columns) != SPLIT_COLUMNS_V2_7:
        errors.append(f"V2.7 split schema mismatch for {timeframe}")
    unexpected_forbidden = [
        column
        for column in dataset.columns
        if column not in DATASET_COLUMNS_V2_7
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    if unexpected_forbidden:
        errors.append(f"V2.7 dataset forbidden columns for {timeframe}: {unexpected_forbidden}")

    if len(dataset) != len(features) or len(dataset) != len(labels):
        errors.append(f"V2.7 dataset row count does not match sources for {timeframe}")

    expected_dataset = build_offline_supervised_dataset(
        features,
        labels,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
        dataset_run_id=manifest["dataset_run_id"],
    )
    try:
        assert_frame_equal(
            dataset.reset_index(drop=True),
            expected_dataset.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            atol=1e-12,
            rtol=1e-12,
        )
    except AssertionError as exc:
        errors.append(f"V2.7 dataset physical mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    expected_splits = build_split_frame(expected_dataset)
    try:
        assert_frame_equal(
            splits.reset_index(drop=True),
            expected_splits.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            atol=1e-12,
            rtol=1e-12,
        )
    except AssertionError as exc:
        errors.append(f"V2.7 split physical mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    feature_source_columns = [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]
    label_source_columns = [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]
    try:
        assert_frame_equal(dataset[feature_source_columns].reset_index(drop=True), features[feature_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V2.7 dataset feature source mismatch for {timeframe}: {str(exc).splitlines()[0]}")
    try:
        assert_frame_equal(dataset[label_source_columns].reset_index(drop=True), labels[label_source_columns].reset_index(drop=True), check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)
    except AssertionError as exc:
        errors.append(f"V2.7 dataset label source mismatch for {timeframe}: {str(exc).splitlines()[0]}")

    quality = assess_dataset_quality(
        dataset,
        expected_rows=EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        timeframe=timeframe,
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    physical_quality[timeframe] = quality
    errors.extend(quality["errors"])
    return errors


def _validate_manifest_structure(project_root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V2.7 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("V2.7 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V2.7 manifest status must be PASS")
    if not _is_iso_utc(manifest.get("created_at_utc")):
        errors.append("V2.7 manifest created_at_utc invalid")
    if not isinstance(manifest.get("dataset_run_id"), str) or DATASET_RUN_ID_PATTERN.fullmatch(manifest["dataset_run_id"]) is None:
        errors.append("V2.7 manifest dataset_run_id invalid")
    if manifest.get("dataset_schema_version") != DATASET_SCHEMA_VERSION:
        errors.append("V2.7 manifest dataset_schema_version mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V2_7:
        errors.append("V2.7 manifest dataset_columns mismatch")
    if manifest.get("split_policy") != SPLIT_POLICY_V2_7:
        errors.append("V2.7 manifest split_policy mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V2_7:
        errors.append("V2.7 manifest limitations mismatch")

    for section in ["input_features", "input_labels", "outputs", "splits", "quality"]:
        block = manifest.get(section, {})
        errors.extend(validate_exact_keys(block, TIMEFRAME_KEYS, f"V2.7 manifest {section}"))
    errors.extend(validate_exact_keys(manifest.get("split_policy", {}), SPLIT_POLICY_KEYS, "V2.7 manifest split_policy"))
    errors.extend(validate_exact_keys(manifest.get("safety", {}), SAFETY_KEYS, "V2.7 manifest safety"))

    for timeframe in TARGET_TIMEFRAMES:
        errors.extend(validate_exact_keys(manifest.get("input_features", {}).get(timeframe, {}), INPUT_KEYS, f"V2.7 manifest input_features.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("input_labels", {}).get(timeframe, {}), INPUT_KEYS, f"V2.7 manifest input_labels.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), OUTPUT_KEYS, f"V2.7 manifest outputs.{timeframe}"))
        errors.extend(validate_exact_keys(manifest.get("splits", {}).get(timeframe, {}), OUTPUT_KEYS, f"V2.7 manifest splits.{timeframe}"))
        quality = manifest.get("quality", {}).get(timeframe, {})
        errors.extend(validate_exact_keys(quality, QUALITY_KEYS, f"V2.7 manifest quality.{timeframe}"))
        if isinstance(quality, dict):
            errors.extend(validate_exact_keys(quality.get("split_counts", {}), SPLIT_COUNT_KEYS, f"V2.7 manifest quality.{timeframe}.split_counts"))
            errors.extend(validate_exact_keys(quality.get("label_valid_counts_by_horizon", {}), HORIZON_KEYS, f"V2.7 manifest quality.{timeframe}.label_valid_counts_by_horizon"))
            errors.extend(validate_exact_keys(quality.get("null_counts_by_column", {}), set(DATASET_COLUMNS_V2_7), f"V2.7 manifest quality.{timeframe}.null_counts_by_column"))
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors = validate_exact_keys(report, MANIFEST_KEYS, "V2.7 quality report")
    if report != manifest:
        for path in _compare_nested(manifest, report, "V2.7 quality report"):
            errors.append(f"V2.7 quality report mismatch for {path}")
    return errors


def _compare_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, quality in physical_quality.items():
        for path in _compare_nested(quality, manifest["quality"].get(timeframe), timeframe):
            errors.append(f"V2.7 manifest quality mismatch for {path}")
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
    }
    if not isinstance(safety, dict):
        return ["V2.7 manifest safety must be an object"]
    return [f"V2.7 safety flag {key} must be {value}" for key, value in expected.items() if safety.get(key) is not value]


def _validate_markdown(project_root: Path) -> list[str]:
    errors: list[str] = []
    for relative, label in [(REPORT_MD_PATH, "V2.7 Markdown report"), (DATACARD_MD_PATH, "V2.7 data card")]:
        path = project_root / relative
        if not path.exists():
            errors.append(f"missing {label}: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), label))
    return errors


def _find_forbidden_artifacts(project_root: Path) -> list[str]:
    forbidden_roots = [Path("models"), Path("reports/strategies"), Path("reports/signals"), Path("reports/predictions"), Path("orders"), Path("execution")]
    allowed_v2_8_ml_reports = {
        Path("reports/ml/offline_ml_research_v2_8.json"),
        Path("reports/ml/offline_ml_research_v2_8.md"),
        Path("reports/ml/offline_research_scores_v2_8.json"),
        Path("reports/ml/offline_research_scores_v2_8.md"),
    }
    errors: list[str] = []
    for relative in forbidden_roots:
        path = project_root / relative
        if path.exists():
            errors.append(f"Forbidden V2.7 artifact detected: {relative.as_posix()}")
    ml_reports = project_root / "reports/ml"
    if ml_reports.exists():
        forbidden_ml = [
            child
            for child in ml_reports.rglob("*")
            if child.is_file() and child.relative_to(project_root) not in allowed_v2_8_ml_reports
        ]
        for child in forbidden_ml:
            errors.append(f"Forbidden V2.7 artifact detected: {child.relative_to(project_root).as_posix()}")
    backtests = project_root / "reports/backtests"
    if backtests.exists():
        direct_forbidden = [child for child in backtests.iterdir() if child.name in {"backtest.json", "backtest.md", "summary.json", "summary.md"}]
        for child in direct_forbidden:
            errors.append(f"Forbidden V2.7 artifact detected: {child.relative_to(project_root).as_posix()}")
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
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest": manifest,
    }
