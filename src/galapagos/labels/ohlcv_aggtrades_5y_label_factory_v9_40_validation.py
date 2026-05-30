from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_schemas import (
    ALLOWED_DECISIONS,
    EXPECTED_FEATURE_ROWS,
    FORBIDDEN_LABEL_COLUMNS,
    LABEL_DESIGNS,
    LABEL_SCHEMA_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REQUIRED_LABEL_COLUMNS,
    SAFETY_FLAGS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
    VERSION,
)


def validate_v9_40_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    errors: list[str] = []
    if not report_path.is_file():
        return result_v9_40([f"missing report: {REPORT_JSON_PATH.as_posix()}"])
    if not manifest_path.is_file():
        return result_v9_40([f"missing manifest: {MANIFEST_PATH.as_posix()}"])
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_40(report))
    errors.extend(validate_manifest_payload_v9_40(report, manifest))
    if report.get("labels_created") is True:
        errors.extend(validate_label_parquets_v9_40(root, report))
    return result_v9_40(errors, report)


def validate_report_payload_v9_40(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.39":
        errors.append("report version/source_version mismatch")
    target = report.get("target_window", {})
    if target.get("start") != TARGET_WINDOW_START or target.get("end") != TARGET_WINDOW_END or target.get("days_expected") != 1827:
        errors.append("target window mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if set(report.get("timeframes", [])) != set(TIMEFRAMES):
        errors.append("timeframes mismatch")
    if report.get("dataset_created") is not False:
        errors.append("V9.40 must not create a supervised dataset")
    for key in ["network_used", "new_data_downloaded", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.40 must report {key}=false")
    if report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("leakage guard must pass")
    if report.get("forbidden_column_scan", {}).get("status") != "PASS":
        errors.append("forbidden column scan must pass")
    if report.get("labels_created") is True:
        if report.get("row_counts") != EXPECTED_FEATURE_ROWS:
            errors.append("created labels must match expected feature rows")
        if report.get("selected_primary_label") not in LABEL_DESIGNS:
            errors.append("created labels must select a known primary label")
        for timeframe in TIMEFRAMES:
            if timeframe not in report.get("outputs", {}):
                errors.append(f"missing output diagnostic for {timeframe}")
            if not report.get("valid_label_counts", {}).get(timeframe, {}).get(report.get("selected_primary_label"), 0):
                errors.append(f"missing valid primary labels for {timeframe}")
    errors.extend(validate_safety_flags_v9_40(report))
    return errors


def validate_manifest_payload_v9_40(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "labels_created", "dataset_created", "selected_primary_label", "row_counts", "quality_status", "coverage_status", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    if manifest.get("leakage_guard_status") != report.get("leakage_guard", {}).get("status"):
        errors.append("manifest leakage guard mismatch")
    return errors


def validate_label_parquets_v9_40(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES:
        output = report.get("outputs", {}).get(timeframe, {})
        path = root / output.get("path", "")
        if not path.is_file():
            errors.append(f"missing label parquet for {timeframe}: {path}")
            continue
        try:
            parquet = pq.ParquetFile(path)
        except Exception as exc:
            errors.append(f"unreadable label parquet for {timeframe}: {exc}")
            continue
        columns = parquet.schema_arrow.names
        missing = [column for column in REQUIRED_LABEL_COLUMNS if column not in columns]
        if missing:
            errors.append(f"{timeframe} label parquet missing columns: {missing}")
        forbidden = sorted(set(columns) & FORBIDDEN_LABEL_COLUMNS)
        if forbidden:
            errors.append(f"{timeframe} label parquet contains forbidden columns: {forbidden}")
        if parquet.metadata.num_rows != EXPECTED_FEATURE_ROWS[timeframe]:
            errors.append(f"{timeframe} row count mismatch: {parquet.metadata.num_rows}")
        schema_field = parquet.schema_arrow.field("label_schema_version") if "label_schema_version" in columns else None
        if schema_field is None:
            errors.append(f"{timeframe} label_schema_version field missing")
        if output.get("rows") != parquet.metadata.num_rows:
            errors.append(f"{timeframe} output row count does not match parquet metadata")
    if report.get("label_schema_version") != LABEL_SCHEMA_VERSION:
        errors.append("label schema version mismatch")
    return errors


def validate_safety_flags_v9_40(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag {key} mismatch")
    return errors


def result_v9_40(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "labels_created": None if report is None else report.get("labels_created"),
        "dataset_created": None if report is None else report.get("dataset_created"),
        "selected_primary_label": None if report is None else report.get("selected_primary_label"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
