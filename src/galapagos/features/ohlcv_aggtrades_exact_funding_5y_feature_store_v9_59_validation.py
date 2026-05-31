from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas import (
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    TIMEFRAMES,
    VERSION,
)


ALLOWED_DECISIONS = {
    "funding_common_window_feature_store_created",
    "funding_common_window_feature_store_created_with_warnings",
    "funding_common_window_feature_store_blocked_by_alignment",
    "funding_common_window_feature_store_blocked_by_schema",
    "funding_common_window_feature_store_blocked_by_quality",
    "funding_common_window_feature_store_blocked_by_leakage",
}
SUCCESS_DECISIONS = {
    "funding_common_window_feature_store_created",
    "funding_common_window_feature_store_created_with_warnings",
}


def validate_v9_59_report(root: Path = Path("."), mode: str = "full") -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    if not report_path.is_file():
        return _result(errors + [f"missing report: {REPORT_JSON_PATH.as_posix()}"])
    if not manifest_path.is_file():
        return _result(errors + [f"missing manifest: {MANIFEST_PATH.as_posix()}"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("version") != VERSION or report.get("source_version") != "V9.56_to_V9.58":
        errors.append("version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS:
        if report.get("feature_store_created") is not True:
            errors.append("success decision must create feature store")
        if report.get("quality_status") != "PASS":
            errors.append("success decision requires quality PASS")
        if report.get("leakage_guard", {}).get("status") != "PASS":
            errors.append("success decision requires leakage PASS")
        for timeframe in TIMEFRAMES:
            if timeframe not in report.get("feature_store_paths", {}):
                errors.append(f"missing feature path for {timeframe}")
    for key in ["version", "source_version", "decision", "quality_status", "coverage_status", "leakage_guard", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.59 must not use network")
    if report.get("ml_executed") is not False or report.get("dataset_created") is not False:
        errors.append("V9.59 must not execute ML or create dataset")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"safety flag mismatch: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown mode")
    return _result(errors, report)


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
    }
