from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    VERSION,
)


SUCCESS_DECISIONS = {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"}


def validate_v9_61_report(root: Path = Path("."), mode: str = "full") -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    if not report_path.is_file():
        return _result([f"missing report: {REPORT_JSON_PATH.as_posix()}"])
    if not manifest_path.is_file():
        return _result([f"missing manifest: {MANIFEST_PATH.as_posix()}"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("version") != VERSION or report.get("source_version") != "V9.60":
        errors.append("version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS:
        if report.get("quality_status") != "PASS":
            errors.append("success decision requires quality PASS")
        if report.get("leakage_guard_status") != "PASS":
            errors.append("success decision requires leakage PASS")
    for key in ["version", "source_version", "decision", "quality_status", "coverage_status", "leakage_guard_status", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.61 must not use network")
    if report.get("ml_executed") is not False:
        errors.append("V9.61 must not execute ML")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"safety flag mismatch: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown mode")
    return _result(errors, report)


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION, "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors, "decision": None if report is None else report.get("decision")}
