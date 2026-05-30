from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_validation_v9_42 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    SAMPLES_JSON_PATH,
    SELECTED_PRIMARY_LABEL,
    TIMEFRAMES,
    VERSION,
)


def validate_v9_42_report(root: Path = Path("."), mode: str = "audit-lite") -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    samples_path = root / SAMPLES_JSON_PATH
    if not report_path.is_file():
        errors.append(f"missing report: {REPORT_JSON_PATH.as_posix()}")
        return result_v9_42(errors)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH.as_posix()}")
        return result_v9_42(errors)
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    samples = _read_json(samples_path) if samples_path.is_file() else {"samples": {}}
    errors.extend(validate_report_payload_v9_42(report))
    errors.extend(validate_manifest_payload_v9_42(report, manifest))
    if mode == "audit-lite":
        errors.extend(validate_audit_lite_samples_v9_42(root, samples))
    return result_v9_42(errors, report)


def validate_report_payload_v9_42(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.41":
        errors.append("report version/source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if report.get("target_name") != SELECTED_PRIMARY_LABEL:
        errors.append("target_name mismatch")
    if report.get("dataset_created") is not False:
        errors.append("V9.42 itself must not create a new full dataset")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.42 must not use network or download data")
    if report.get("ml_executed") is not False or report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.42 must not run ML, walk-forward or backtest")
    if report.get("signal_created") is not False or report.get("strategy_created") is not False:
        errors.append("V9.42 must not create signals or strategies")
    if report.get("leakage_guard_status") != "PASS":
        errors.append("leakage guard must pass")
    if report.get("forbidden_column_scan", {}).get("status") != "PASS":
        errors.append("forbidden column scan must pass")
    if report.get("decision") in {"ohlcv_aggtrades_5y_dataset_validated", "ohlcv_aggtrades_5y_dataset_validated_with_non_blocking_warnings"}:
        if report.get("quality_status") not in {"PASS", "PASS_WITH_WARNINGS"}:
            errors.append("validated decision requires PASS/PASS_WITH_WARNINGS quality")
        if report.get("schema_status") not in {"PASS", "audit_lite_schema_checked_from_manifest_and_samples"}:
            errors.append("validated decision requires schema pass")
    errors.extend(validate_safety_flags_v9_42(report))
    return errors


def validate_manifest_payload_v9_42(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "target_name", "coverage_status", "schema_status", "quality_status", "leakage_guard_status", "dataset_created", "network_used", "new_data_downloaded", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def validate_audit_lite_samples_v9_42(root: Path, samples: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sample_map = samples.get("samples", {})
    for timeframe in TIMEFRAMES:
        item = sample_map.get(timeframe, {})
        if not item:
            errors.append(f"{timeframe}: missing sample inventory entry")
            continue
        path = root / item.get("path", "")
        if item.get("rows", 0) <= 0:
            errors.append(f"{timeframe}: sample rows must be positive")
        if not path.is_file():
            errors.append(f"{timeframe}: sample file missing")
    return errors


def validate_safety_flags_v9_42(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag {key} mismatch")
    return errors


def result_v9_42(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "validation_mode": None if report is None else report.get("validation_mode"),
        "quality_status": None if report is None else report.get("quality_status"),
        "coverage_status": None if report is None else report.get("coverage_status"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
