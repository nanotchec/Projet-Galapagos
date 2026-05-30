from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.ohlcv_5y_extension_correction_v9_34_1 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    VERSION,
)
from galapagos.data.ohlcv_5y_extension_v9_34_validation import REQUIRED_FALSE_FLAGS, REQUIRED_TRUE_FLAGS


def validate_v9_34_1_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    errors: list[str] = []
    if not report_path.is_file():
        errors.append(f"missing report: {REPORT_JSON_PATH.as_posix()}")
        return _result(errors)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH.as_posix()}")
        return _result(errors)
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_34_1(report))
    errors.extend(validate_manifest_payload_v9_34_1(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_34_1(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.34":
        errors.append("report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if report.get("target_window_start") != "2021-05-05" or report.get("target_window_end") != "2026-05-05":
        errors.append("target window mismatch")
    if report.get("feature_store_created") is not False or report.get("combined_feature_store_created") is not False:
        errors.append("V9.34.1 must not create combined feature store")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.34.1 must not create labels, datasets or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.34.1 must not run walk-forward or backtest")
    bad = report.get("bad_day_diagnostic", {})
    if "before" not in bad or "repair" not in bad or "after" not in bad:
        errors.append("bad_day_diagnostic must include before, repair and after")
    if report.get("redownload_attempted") is True and report.get("network_used") is not True:
        errors.append("redownload requires network_used=true")
    if report.get("decision") == "ohlcv_5y_extension_complete":
        missing = report.get("diagnostic_after", {}).get("missing_days_by_timeframe", {})
        if report.get("ohlcv_5y_ready") is not True or any(value != 0 for value in missing.values()):
            errors.append("complete decision requires zero missing days and ohlcv_5y_ready=true")
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_34_1(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "network_used", "new_data_downloaded", "ingestion_executed", "feature_store_created", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def _validate_safety_flags(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key in sorted(REQUIRED_TRUE_FLAGS | {"no_combined_feature_store"}):
        if flags.get(key) is not True:
            errors.append(f"safety flag {key} must be true")
    for key in sorted(REQUIRED_FALSE_FLAGS):
        if flags.get(key) is not False:
            errors.append(f"safety flag {key} must be false")
    for key in ["network_used", "new_data_downloaded", "ingestion_executed"]:
        if flags.get(key) != report.get(key):
            errors.append(f"safety {key} mismatch")
    return errors


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "ohlcv_5y_ready": None if report is None else report.get("ohlcv_5y_ready"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
