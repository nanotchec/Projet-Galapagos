from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.label_redesign_diagnostic_v9_63 import (
    ALLOWED_DECISIONS,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    SAFETY_FLAGS,
    VERSION,
)


def validate_label_redesign_diagnostic_v9_63(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    if not report_path.is_file():
        return [f"missing report: {REPORT_JSON_PATH}"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    errors.extend(validate_report_payload_v9_63(report))
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        errors.extend(validate_manifest_payload_v9_63(manifest, report))
    return errors


def validate_report_payload_v9_63(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if not report.get("selected_primary_label"):
        errors.append("missing selected_primary_label")
    for key, expected in {
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
    }.items():
        if report.get(key) is not expected:
            errors.append(f"{key} must be {expected}")
    if report.get("findings") != FINDINGS:
        errors.append("findings mismatch")
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag mismatch: {key}")
    if report.get("selection_methodology", {}).get("selected_from_ml_performance") is not False:
        errors.append("label selection must not be based on ML performance")
    return errors


def validate_manifest_payload_v9_63(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("manifest decision mismatch")
    if manifest.get("selected_primary_label") != report.get("selected_primary_label"):
        errors.append("manifest selected label mismatch")
    return errors
