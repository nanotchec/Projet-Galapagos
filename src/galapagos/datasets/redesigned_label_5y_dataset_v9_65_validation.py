from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.redesigned_label_5y_dataset_v9_65_schemas import ALLOWED_DECISIONS, FINDINGS, MANIFEST_PATH, REPORT_JSON_PATH, SAFETY_FLAGS, SELECTED_PRIMARY_LABEL, TIMEFRAMES, VERSION


def validate_redesigned_label_5y_dataset_v9_65(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    if not report_path.is_file():
        return [f"missing report: {REPORT_JSON_PATH}"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    errors = validate_report_payload_v9_65(report)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        errors.extend(validate_manifest_payload_v9_65(manifest, report))
    return errors


def validate_report_payload_v9_65(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("target_name") != SELECTED_PRIMARY_LABEL:
        errors.append("target mismatch")
    if report.get("dataset_created") is not True:
        errors.append("dataset_created must be true")
    if report.get("ml_executed") is not False:
        errors.append("ml_executed must be false")
    if report.get("leakage_guard", {}).get("status") != "PASS":
        errors.append("leakage guard must pass")
    if set(report.get("row_counts", {})) != set(TIMEFRAMES):
        errors.append("missing timeframe row counts")
    if report.get("findings") != FINDINGS:
        errors.append("findings mismatch")
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag mismatch: {key}")
    return errors


def validate_manifest_payload_v9_65(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("manifest decision mismatch")
    if manifest.get("target_name") != report.get("target_name"):
        errors.append("manifest target mismatch")
    return errors
