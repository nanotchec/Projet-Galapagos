from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS
from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS_V9_29,
    SOURCE_VERSION,
    TAIL_END,
    TAIL_START,
    TOTAL_DAYS_EXPECTED,
    VERSION,
    date_range_v9_29,
)


FORBIDDEN_TERMS = ["sharpe", "drawdown", "equity curve", "profit factor", "pnl"]
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".pem",
    ".key",
    ".sha256.json",
    ".sha256.txt",
}


def validate_aggtrades_post_v9_full_coverage_validation_v9_29(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.is_file():
        return [f"missing V9.29 report: {REPORT_JSON_PATH}"]
    if not manifest_path.is_file():
        errors.append(f"missing V9.29 manifest: {MANIFEST_PATH}")
    if not markdown_path.is_file():
        errors.append(f"missing V9.29 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_29(report))
    errors.extend(validate_manifest_payload_v9_29(manifest, report))
    errors.extend(validate_markdown_v9_29(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_29(root))
    return errors


def validate_report_payload_v9_29(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.29 version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.29 source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.29 decision is not allowed")
    if report.get("findings") != FINDINGS:
        errors.append("V9.29 findings mismatch")
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.29 must keep {key}=false")
    errors.extend(validate_calendar_v9_29(report.get("calendar_validation", {}), report))
    errors.extend(validate_quality_v9_29(report.get("quality_validation", {}), report))
    errors.extend(validate_quarantine_v9_29(report.get("quarantine_reconciliation", {}), report))
    errors.extend(validate_tail_v9_29(report.get("tail_reconciliation", {})))
    errors.extend(validate_safety_v9_29(report.get("safety_flags", {}), report))
    if _contains_forbidden_zip_field(report):
        errors.append("V9.29 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_calendar_v9_29(calendar: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if calendar.get("days_expected") != TOTAL_DAYS_EXPECTED or report.get("days_expected") != TOTAL_DAYS_EXPECTED:
        errors.append("V9.29 calendar must validate 731 expected days")
    if report.get("decision", "").startswith("aggtrades_full_coverage_validated"):
        if calendar.get("complete_calendar_coverage") is not True:
            errors.append("V9.29 validated decision requires complete calendar coverage")
        for key in ["days_missing", "days_failed", "days_partial"]:
            if report.get(key) != 0 or calendar.get(key) != 0:
                errors.append(f"V9.29 validated decision requires {key}=0")
        if report.get("local_file_coverage_start") != "2024-05-05" or report.get("local_file_coverage_end") != "2026-05-05":
            errors.append("V9.29 validated decision must cover full target window")
        if report.get("complete_collection_reached") is not True or report.get("future_full_coverage_complete") is not True:
            errors.append("V9.29 validated decision must set completion flags true")
    if report.get("decision") == "aggtrades_full_coverage_blocked_by_missing_days" and calendar.get("complete_calendar_coverage") is True:
        errors.append("V9.29 missing-days decision requires incomplete calendar coverage")
    return errors


def validate_quality_v9_29(quality: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    blocking_keys = [
        "global_duplicate_count",
        "global_invalid_rows",
        "schema_mismatch_count",
        "non_positive_price_count",
        "non_positive_quantity_count",
        "available_ts_violation_count",
        "partition_mismatch_count",
    ]
    if report.get("decision", "").startswith("aggtrades_full_coverage_validated"):
        if quality.get("quality_status") != "PASS" or report.get("quality_status") != "PASS":
            errors.append("V9.29 validated decision requires quality_status=PASS")
        for key in blocking_keys:
            if quality.get(key) != 0:
                errors.append(f"V9.29 validated decision requires {key}=0")
        if quality.get("raw_read_errors"):
            errors.append("V9.29 validated decision requires zero raw_read_errors")
        if quality.get("silver_read_errors"):
            errors.append("V9.29 validated decision requires zero silver_read_errors")
    if report.get("decision") == "aggtrades_full_coverage_blocked_by_quality" and quality.get("quality_status") == "PASS":
        errors.append("V9.29 quality-blocked decision requires quality_status!=PASS")
    return errors


def validate_quarantine_v9_29(quarantine: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("decision") == "aggtrades_full_coverage_blocked_by_quarantine" and quarantine.get("quarantine_blocking") is not True:
        errors.append("V9.29 quarantine-blocked decision requires quarantine_blocking=true")
    if report.get("decision", "").startswith("aggtrades_full_coverage_validated") and quarantine.get("quarantine_blocking") is True:
        errors.append("V9.29 validated decision cannot have blocking quarantine")
    if quarantine.get("quarantine_active_count", 0) and not quarantine.get("active_quarantine_dates"):
        errors.append("V9.29 active quarantine count must list dates")
    return errors


def validate_tail_v9_29(tail: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if tail.get("tail_days_expected") != len(date_range_v9_29(TAIL_START, TAIL_END)):
        errors.append("V9.29 tail expected day count mismatch")
    if tail.get("tail_days_validated_by_v9_29") == tail.get("tail_days_expected") and tail.get("tail_reporting_acceptable") is not True:
        errors.append("V9.29 tail complete validation must mark reporting acceptable")
    return errors


def validate_safety_v9_29(flags: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in SAFETY_FLAGS_V9_29.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.29 safety mismatch: {key}")
    for key in ["network_used", "new_data_downloaded", "ingestion_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.29 report must keep {key}=false")
    return errors


def validate_manifest_payload_v9_29(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.29 manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.29 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.29 manifest safety flags mismatch")
    for key in ["days_expected", "days_complete", "days_missing", "days_failed", "global_duplicate_count", "global_invalid_rows"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"V9.29 manifest/report mismatch: {key}")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.29 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_29(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.29 markdown contains forbidden metric term: {forbidden}")
    for phrase in [
        "aucun trading",
        "aucun paper live",
        "aucun ordre",
        "aucun backtest",
        "aucun walk-forward",
        "aucun ml",
        "aucun dataset supervise",
        "aucune strategie",
        "aucun signal actionnable",
        "aucun modele persistant",
        "aucune api privee",
        "aucune cle api",
        "aucun telechargement",
        "aucune ingestion",
        "aucune suppression destructive",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.29 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_29(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_29*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        lowered = path.name.casefold()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden V9.29 artifact suffix: {path}")
    for path in root.glob("projet-galapagos-v9.29-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.29 ZIP sidecar: {path}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
