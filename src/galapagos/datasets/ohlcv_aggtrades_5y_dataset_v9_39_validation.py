from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_schemas import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
    VERSION,
)


def validate_v9_39_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    errors: list[str] = []
    if not report_path.is_file():
        errors.append(f"missing report: {REPORT_JSON_PATH.as_posix()}")
        return result_v9_39(errors)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH.as_posix()}")
        return result_v9_39(errors)
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_39(report))
    errors.extend(validate_manifest_payload_v9_39(report, manifest))
    return result_v9_39(errors, report)


def validate_report_payload_v9_39(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.38":
        errors.append("report version/source_version mismatch")
    target = report.get("target_window", {})
    if target.get("start") != TARGET_WINDOW_START or target.get("end") != TARGET_WINDOW_END or target.get("days_expected") != 1827:
        errors.append("target window mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if set(report.get("timeframes", [])) != set(TIMEFRAMES):
        errors.append("timeframes mismatch")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.39 must not use network or download data")
    if report.get("ml_executed") is not False or report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.39 must not run ML, walk-forward or backtest")
    if report.get("decision") == "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels":
        if report.get("dataset_created") is not False:
            errors.append("missing-label decision must not create a dataset")
        if report.get("target_name") is not None:
            errors.append("missing-label decision must not select a target")
        if report.get("label_readiness", {}).get("status") != "MISSING_5Y_COMPATIBLE_LABELS":
            errors.append("missing-label decision requires missing label readiness status")
        if any(value != 0 for value in report.get("row_counts", {}).values()):
            errors.append("missing-label decision must report zero dataset rows")
    if report.get("decision") in {"ohlcv_aggtrades_5y_dataset_created", "ohlcv_aggtrades_5y_dataset_created_with_warnings"}:
        if report.get("dataset_created") is not True:
            errors.append("created decision requires dataset_created=true")
        if report.get("target_name") is None:
            errors.append("created decision requires a target")
    errors.extend(validate_label_readiness_payload_v9_39(report.get("label_readiness", {})))
    errors.extend(validate_safety_flags_v9_39(report))
    return errors


def validate_label_readiness_payload_v9_39(label_readiness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidates = label_readiness.get("candidates", [])
    if not candidates:
        errors.append("label readiness must include candidate diagnostics")
        return errors
    compatible = [item for item in candidates if item.get("compatible_with_5y_window") is True]
    if label_readiness.get("status") == "MISSING_5Y_COMPATIBLE_LABELS" and compatible:
        errors.append("missing label status contradicts compatible candidates")
    for item in candidates:
        if "label_name" not in item or "coverage_start" not in item or "coverage_end" not in item:
            errors.append("label candidate missing required diagnostic fields")
    return errors


def validate_manifest_payload_v9_39(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "dataset_created", "target_name", "row_counts", "quality_status", "coverage_status", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def validate_safety_flags_v9_39(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag {key} mismatch")
    return errors


def result_v9_39(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "dataset_created": None if report is None else report.get("dataset_created"),
        "label_readiness_status": None if report is None else report.get("label_readiness", {}).get("status"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
