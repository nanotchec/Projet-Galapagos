from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48 import (
    ALLOWED_DECISIONS,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    VERSION,
)


def validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48(root: Path = Path("."), *, audit_lite: bool = False) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH, REPORT_MD_PATH, MANIFEST_PATH]:
        if not (root / path).is_file():
            errors.append(f"missing V9.48 artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH)
    manifest = _read_json(root / MANIFEST_PATH)
    errors.extend(validate_report_payload_v9_48(report))
    if manifest.get("decision") != report.get("decision") or manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.48 manifest/report mismatch")
    if not audit_lite and report.get("decision") in {"combined_feature_store_validated", "combined_feature_store_validated_with_warnings"}:
        if report.get("quality_status") != "PASS" or report.get("leakage_guard_status") != "PASS":
            errors.append("V9.48 successful decision requires quality/leakage PASS")
    if _contains_forbidden_zip_field(report) or _contains_forbidden_zip_field(manifest):
        errors.append("V9.48 payload contains forbidden ZIP fingerprint field")
    return errors


def validate_report_payload_v9_48(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.47":
        errors.append("V9.48 version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.48 decision not allowed")
    if report.get("combined_feature_columns_count") != 97:
        errors.append("V9.48 combined feature count mismatch")
    for key in ["dataset_created", "labels_created", "ml_executed", "walk_forward_executed", "backtest_executed", "signal_created", "strategy_created", "network_used", "new_data_downloaded"]:
        if report.get(key) is not False:
            errors.append(f"V9.48 forbidden flag must be false: {key}")
    if report.get("findings") != FINDINGS:
        errors.append("V9.48 findings mismatch")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.48 safety flag mismatch: {key}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
