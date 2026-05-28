from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1 import (
    ALLOWED_DECISIONS,
    FINDINGS_V9_25_1,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_BASE_V9_25_1,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VERSION,
)


FORBIDDEN_TERMS = ["sharpe", "drawdown", "equity curve", "profit factor", "pnl"]
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_aggtrades_post_v9_resume_campaign_v9_25_1(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        return [f"missing V9.25.1 report: {REPORT_JSON_PATH}"]
    if not manifest_path.exists():
        errors.append(f"missing V9.25.1 manifest: {MANIFEST_PATH}")
    if not markdown_path.exists():
        errors.append(f"missing V9.25.1 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_25_1(report, root))
    errors.extend(validate_manifest_payload_v9_25_1(manifest, report))
    errors.extend(validate_markdown_v9_25_1(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_25_1(root))
    return errors


def validate_report_payload_v9_25_1(report: dict[str, Any], root: Path = Path(".")) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.25.1 version mismatch")
    if report.get("source_version") != "V9.25":
        errors.append("V9.25.1 source_version mismatch")
    if report.get("correction_scope") != "campaign_state_reconciliation_and_resume_collection":
        errors.append("V9.25.1 correction_scope mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.25.1 decision is not allowed")
    if report.get("findings") != FINDINGS_V9_25_1:
        errors.append("V9.25.1 findings mismatch")
    errors.extend(validate_canonical_v9_25_1(report.get("canonical_coverage_before_resume", {})))
    errors.extend(validate_disk_preflight_v9_25_1(report.get("disk_preflight", {})))
    errors.extend(validate_summary_v9_25_1(report.get("resume_summary", {}), report, root))
    errors.extend(validate_safety_v9_25_1(report.get("safety_flags", {}), report))
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.25.1 must keep {key}=false")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.25.1 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_canonical_v9_25_1(canonical: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if canonical.get("target_window_start") != TARGET_WINDOW_START or canonical.get("target_window_end") != TARGET_WINDOW_END:
        errors.append("V9.25.1 canonical target window mismatch")
    if canonical.get("first_missing_day") and canonical.get("last_complete_day_before_gap") >= canonical.get("first_missing_day"):
        errors.append("V9.25.1 first missing day ordering mismatch")
    if canonical.get("days_partial", 0) < 0 or canonical.get("days_complete", 0) < 0:
        errors.append("V9.25.1 canonical day counters must be non-negative")
    return errors


def validate_disk_preflight_v9_25_1(disk: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if disk.get("minimum_free_bytes_required") != 60 * 1024**3:
        errors.append("V9.25.1 minimum disk threshold mismatch")
    if disk.get("free_bytes_current", 0) < 0:
        errors.append("V9.25.1 free disk bytes must be non-negative")
    if disk.get("batch_size_days", 0) not in {0, 30, 60, 90}:
        errors.append("V9.25.1 batch size must follow disk policy")
    return errors


def validate_summary_v9_25_1(summary: dict[str, Any], report: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if summary.get("target_window_start") != TARGET_WINDOW_START or summary.get("target_window_end") != TARGET_WINDOW_END:
        errors.append("V9.25.1 summary target window mismatch")
    if summary.get("batches_executed", 0) > summary.get("batches_planned", 0):
        errors.append("V9.25.1 executed more batches than planned")
    if summary.get("days_quarantined_total", 0) < 0 or summary.get("days_failed_total", 0) < 0:
        errors.append("V9.25.1 failed/quarantine counters must be non-negative")
    if summary.get("complete_collection_reached") is True:
        if summary.get("local_file_coverage_start") != TARGET_WINDOW_START or summary.get("local_file_coverage_end") != TARGET_WINDOW_END:
            errors.append("V9.25.1 complete collection must cover full target window")
        if report.get("decision") != "resume_collection_completed_full_window":
            errors.append("V9.25.1 complete collection decision mismatch")
    if report.get("decision") == "resume_collection_not_executed_storage_blocker" and summary.get("days_attempted_total") != 0:
        errors.append("V9.25.1 storage blocker decision cannot attempt days")
    for raw_path in report.get("batch_report_paths", []):
        if not (root / raw_path).is_file():
            errors.append(f"missing V9.25.1 batch report: {raw_path}")
    return errors


def validate_safety_v9_25_1(flags: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in SAFETY_BASE_V9_25_1.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.25.1 safety mismatch: {key}")
    if report.get("collection_executed"):
        if flags.get("network_used") is not True or flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.25.1 collection must use public archive read-only network")
        if flags.get("new_data_downloaded") is not True or flags.get("new_data_download_scope") != "public_historical_aggtrades_resume_only":
            errors.append("V9.25.1 download scope mismatch")
        if flags.get("ingestion_executed") is not True or flags.get("ingestion_scope") != "public_aggtrades_bronze_silver_resume_only":
            errors.append("V9.25.1 ingestion scope mismatch")
    else:
        if flags.get("network_used") is not False or flags.get("no_new_data_download") is not True or flags.get("no_ingestion_executed") is not True:
            errors.append("V9.25.1 no-collection flags mismatch")
    return errors


def validate_manifest_payload_v9_25_1(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.25.1 manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.25.1 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.25.1 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.25.1 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_25_1(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.25.1 markdown contains forbidden metric term: {forbidden}")
    for phrase in [
        "aucun trading",
        "aucun paper live",
        "aucun ordre",
        "aucun backtest",
        "aucun walk-forward",
        "aucun ml",
        "aucun dataset supervise",
        "aucune suppression de donnees",
        "aucun nettoyage destructif",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.25.1 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_25_1(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_25_1*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.25.1 artifact suffix: {path}")
    for path in root.glob("projet-galapagos-v9.25.1-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.25.1 ZIP sidecar: {path}")
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
