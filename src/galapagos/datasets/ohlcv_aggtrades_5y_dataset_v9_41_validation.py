from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_schemas import (
    ALLOWED_DECISIONS,
    EXPECTED_ROWS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    SELECTED_PRIMARY_LABEL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
    VERSION,
)


def validate_v9_41_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    errors: list[str] = []
    if not report_path.is_file():
        errors.append(f"missing report: {REPORT_JSON_PATH.as_posix()}")
        return result_v9_41(errors)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH.as_posix()}")
        return result_v9_41(errors)
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_41(report))
    errors.extend(validate_manifest_payload_v9_41(report, manifest))
    errors.extend(validate_outputs_v9_41(root, report))
    return result_v9_41(errors, report)


def validate_report_payload_v9_41(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.40":
        errors.append("report version/source_version mismatch")
    target = report.get("target_window", {})
    if target.get("start") != TARGET_WINDOW_START or target.get("end") != TARGET_WINDOW_END or target.get("days_expected") != 1827:
        errors.append("target window mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if set(report.get("timeframes", [])) != set(TIMEFRAMES):
        errors.append("timeframes mismatch")
    if report.get("target_name") != SELECTED_PRIMARY_LABEL or report.get("selected_primary_label") != SELECTED_PRIMARY_LABEL:
        errors.append("selected primary target mismatch")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.41 must not use network or download data")
    if report.get("ml_executed") is not False or report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.41 must not run ML, walk-forward or backtest")
    if report.get("signal_created") is not False or report.get("strategy_created") is not False:
        errors.append("V9.41 must not create signals or strategies")
    if report.get("decision") in {"ohlcv_aggtrades_5y_dataset_created", "ohlcv_aggtrades_5y_dataset_created_with_warnings"}:
        if report.get("dataset_created") is not True:
            errors.append("created decision requires dataset_created=true")
        if report.get("row_counts") != EXPECTED_ROWS:
            errors.append("created decision row counts mismatch")
        if report.get("coverage_status") != "target_5y_dataset_window_complete":
            errors.append("created decision requires complete dataset coverage")
        if report.get("leakage_guard", {}).get("status") != "PASS":
            errors.append("created decision requires leakage guard PASS")
        if report.get("forbidden_column_scan", {}).get("status") != "PASS":
            errors.append("created decision requires forbidden column scan PASS")
    if report.get("feature_readiness", {}).get("ready") is not True:
        errors.append("feature readiness must be true")
    if report.get("label_readiness", {}).get("ready") is not True:
        errors.append("label readiness must be true")
    errors.extend(validate_safety_flags_v9_41(report))
    return errors


def validate_manifest_payload_v9_41(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in [
        "version",
        "source_version",
        "decision",
        "dataset_created",
        "target_name",
        "selected_primary_label",
        "row_counts",
        "valid_row_counts",
        "invalid_row_counts",
        "quality_status",
        "coverage_status",
        "safety_flags",
    ]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def validate_outputs_v9_41(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("dataset_created") is not True:
        return errors
    outputs = report.get("outputs", {})
    for timeframe in TIMEFRAMES:
        item = outputs.get(timeframe, {})
        path = item.get("path")
        if item.get("created") is not True or not path:
            errors.append(f"{timeframe}: missing output metadata")
            continue
        full = root / path
        if not full.is_file():
            errors.append(f"{timeframe}: missing dataset parquet {path}")
        elif full.stat().st_size <= 0:
            errors.append(f"{timeframe}: dataset parquet is empty")
    return errors


def validate_safety_flags_v9_41(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag {key} mismatch")
    return errors


def result_v9_41(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "dataset_created": None if report is None else report.get("dataset_created"),
        "target_name": None if report is None else report.get("target_name"),
        "quality_status": None if report is None else report.get("quality_status"),
        "coverage_status": None if report is None else report.get("coverage_status"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
