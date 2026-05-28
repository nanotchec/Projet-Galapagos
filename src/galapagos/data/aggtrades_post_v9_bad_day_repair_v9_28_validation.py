from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_bad_day_repair_v9_28 import (
    ALLOWED_DECISIONS,
    BAD_DAY,
    BASE_SAFETY_FLAGS_V9_28,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SOURCE_VERSION,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VERSION,
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


def validate_aggtrades_post_v9_bad_day_repair_v9_28(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.is_file():
        return [f"missing V9.28 report: {REPORT_JSON_PATH}"]
    if not manifest_path.is_file():
        errors.append(f"missing V9.28 manifest: {MANIFEST_PATH}")
    if not markdown_path.is_file():
        errors.append(f"missing V9.28 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_28(report))
    errors.extend(validate_manifest_payload_v9_28(manifest, report))
    errors.extend(validate_markdown_v9_28(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_28(root))
    return errors


def validate_report_payload_v9_28(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.28 version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.28 source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.28 decision is not allowed")
    if report.get("findings") != FINDINGS:
        errors.append("V9.28 findings mismatch")
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.28 must keep {key}=false")
    errors.extend(validate_diagnostic_v9_28(report.get("bad_day_diagnostic", {}), report))
    errors.extend(validate_repair_v9_28(report.get("bad_day_repair_report", {}), report))
    errors.extend(validate_global_validation_v9_28(report.get("global_validation", {}), report))
    errors.extend(validate_safety_v9_28(report.get("safety_flags", {}), report))
    if _contains_forbidden_zip_field(report):
        errors.append("V9.28 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_diagnostic_v9_28(diagnostic: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if diagnostic.get("date") != BAD_DAY:
        errors.append("V9.28 diagnostic bad day mismatch")
    if diagnostic.get("duplicate_count", 0) < diagnostic.get("duplicate_exact_count", 0):
        errors.append("V9.28 exact duplicates cannot exceed duplicate count")
    if diagnostic.get("duplicate_conflict_count", 0) < 0:
        errors.append("V9.28 conflict duplicate count must be non-negative")
    if diagnostic.get("duplicate_repair_possible") is True:
        if diagnostic.get("duplicate_exact_count", 0) <= 0:
            errors.append("V9.28 repair possible requires exact duplicates")
        if diagnostic.get("duplicate_conflict_count") != 0:
            errors.append("V9.28 repair possible requires zero conflicting duplicates")
        if diagnostic.get("repaired_aggregate_trade_id_monotone") is not True:
            errors.append("V9.28 repair possible requires monotone aggregate_trade_id after repair")
    if report.get("decision") == "bad_day_repair_not_needed_report_false_positive" and diagnostic.get("duplicate_count", 0) != 0:
        errors.append("V9.28 false-positive decision requires zero duplicate count")
    return errors


def validate_repair_v9_28(repair: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if repair.get("date") != BAD_DAY:
        errors.append("V9.28 repair report bad day mismatch")
    if repair.get("repair_applied") is True:
        if repair.get("duplicate_conflict_count") != 0:
            errors.append("V9.28 applied repair cannot contain conflicting duplicates")
        if repair.get("duplicate_exact_count", 0) <= 0:
            errors.append("V9.28 applied repair requires exact duplicates")
        if repair.get("quality_status") != "PASS":
            errors.append("V9.28 applied repair must pass quality")
        after = repair.get("after_result", {})
        if after.get("status") != "day_complete":
            errors.append("V9.28 applied repair must leave bad day complete")
        if after.get("duplicates") not in {0, None}:
            errors.append("V9.28 applied repair must remove aggregate_trade_id duplicates")
    if report.get("decision") == "bad_day_repaired_and_remaining_window_completed" and repair.get("repair_applied") is not True:
        errors.append("V9.28 completed decision requires repair_applied=true")
    return errors


def validate_global_validation_v9_28(global_validation: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if global_validation.get("local_file_coverage_start") != TARGET_WINDOW_START:
        errors.append("V9.28 global coverage must start at target start")
    if report.get("decision") == "bad_day_repaired_and_remaining_window_completed":
        if global_validation.get("local_file_coverage_end") != TARGET_WINDOW_END:
            errors.append("V9.28 completed decision must end at target end")
        if global_validation.get("complete_collection_reached") is not True:
            errors.append("V9.28 completed decision must set complete_collection_reached=true")
        if global_validation.get("future_full_coverage_complete") is not True:
            errors.append("V9.28 completed decision must set future_full_coverage_complete=true")
        if global_validation.get("global_duplicate_count") != 0:
            errors.append("V9.28 completed decision requires zero global duplicates")
        if global_validation.get("global_invalid_rows") != 0:
            errors.append("V9.28 completed decision requires zero global invalid rows")
    if report.get("decision") != "bad_day_repaired_and_remaining_window_completed":
        if global_validation.get("complete_collection_reached") is True:
            errors.append("V9.28 non-completed decision cannot claim complete collection")
    return errors


def validate_safety_v9_28(flags: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in BASE_SAFETY_FLAGS_V9_28.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.28 safety mismatch: {key}")
    if flags.get("network_used"):
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.28 network scope must be public archive read-only")
        if flags.get("new_data_downloaded") and flags.get("new_data_download_scope") != "public_historical_aggtrades_bad_day_or_final_tail_only":
            errors.append("V9.28 new data download scope mismatch")
    else:
        if flags.get("no_new_data_download") is not True:
            errors.append("V9.28 no-network run must set no_new_data_download=true")
    if report.get("ingestion_executed") and flags.get("ingestion_executed") is not True:
        errors.append("V9.28 report/flags ingestion mismatch")
    return errors


def validate_manifest_payload_v9_28(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.28 manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.28 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.28 manifest safety flags mismatch")
    if manifest.get("repair_applied") != report.get("v9_28_summary", {}).get("repair_applied"):
        errors.append("V9.28 manifest repair_applied mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.28 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_28(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.28 markdown contains forbidden metric term: {forbidden}")
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
        "aucune suppression destructive",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.28 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_28(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_28*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        lowered = path.name.casefold()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden V9.28 artifact suffix: {path}")
    for path in root.glob("projet-galapagos-v9.28-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.28 ZIP sidecar: {path}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
