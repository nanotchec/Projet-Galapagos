from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_5y_extension_plan_v9_30 import (
    ALLOWED_DECISIONS,
    EXTENSION_WINDOW_END,
    EXTENSION_WINDOW_START,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS_V9_30,
    SOURCE_VERSION,
    TARGET_5Y_WINDOW_END,
    TARGET_5Y_WINDOW_START,
    VERSION,
)
from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS


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


def validate_aggtrades_5y_extension_plan_v9_30(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.is_file():
        return [f"missing V9.30 report: {REPORT_JSON_PATH}"]
    if not manifest_path.is_file():
        errors.append(f"missing V9.30 manifest: {MANIFEST_PATH}")
    if not markdown_path.is_file():
        errors.append(f"missing V9.30 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_30(report))
    errors.extend(validate_manifest_payload_v9_30(manifest, report))
    errors.extend(validate_markdown_v9_30(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_30(root))
    return errors


def validate_report_payload_v9_30(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.30 version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.30 source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.30 decision is not allowed")
    if report.get("findings") != FINDINGS:
        errors.append("V9.30 findings mismatch")
    if report.get("mode") != "plan-only":
        errors.append("V9.30 must remain plan-only")
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed", "network_used", "new_data_downloaded", "ingestion_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.30 must keep {key}=false")
    errors.extend(validate_windows_v9_30(report))
    errors.extend(validate_estimates_v9_30(report.get("estimated_volume", {}), report))
    errors.extend(validate_source_v9_30(report.get("source_availability_assessment", {})))
    errors.extend(validate_collection_plan_v9_30(report.get("collection_plan_v9_31", []), report))
    errors.extend(validate_safety_v9_30(report.get("safety_flags", {})))
    if _contains_forbidden_zip_field(report):
        errors.append("V9.30 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_windows_v9_30(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("target_5y_window_start") != TARGET_5Y_WINDOW_START or report.get("target_5y_window_end") != TARGET_5Y_WINDOW_END:
        errors.append("V9.30 target 5Y window mismatch")
    if report.get("extension_window_start") != EXTENSION_WINDOW_START or report.get("extension_window_end") != EXTENSION_WINDOW_END:
        errors.append("V9.30 extension window mismatch")
    if report.get("target_5y_days_expected") != 1827:
        errors.append("V9.30 target 5Y expected days must be 1827")
    if report.get("already_validated_days") != 731:
        errors.append("V9.30 already_validated_days must be 731")
    if report.get("extension_days_needed") != 1096:
        errors.append("V9.30 extension_days_needed must be 1096")
    return errors


def validate_estimates_v9_30(estimated: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if estimated.get("safety_margin_factor", 0) < 1.3:
        errors.append("V9.30 safety margin must be at least 1.3")
    if estimated.get("estimated_extension_raw_bytes", 0) <= 0 or estimated.get("estimated_extension_silver_bytes", 0) <= 0:
        errors.append("V9.30 extension estimates must be positive")
    if estimated.get("required_free_bytes_for_extension", 0) <= estimated.get("estimated_extension_total_bytes", 0):
        errors.append("V9.30 required free bytes must include a safety margin")
    if report.get("decision") == "aggtrades_5y_extension_not_ready_storage_blocker" and report.get("safe_for_5y_extension_collection") is True:
        errors.append("V9.30 storage blocker decision cannot be safe_for_5y_extension_collection=true")
    return errors


def validate_source_v9_30(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("host") != "data.binance.vision":
        errors.append("V9.30 source host must remain data.binance.vision")
    if source.get("availability_needs_confirmation") is not True:
        errors.append("V9.30 must require future availability confirmation")
    if source.get("network_check_required_in_future_collection") is not True:
        errors.append("V9.30 must defer network check to future collection")
    return errors


def validate_collection_plan_v9_30(batches: list[dict[str, Any]], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not batches:
        errors.append("V9.30 collection plan must contain batches")
        return errors
    if batches[0].get("start_date") != EXTENSION_WINDOW_START or batches[-1].get("end_date") != EXTENSION_WINDOW_END:
        errors.append("V9.30 V9.31 batches must cover the extension window")
    if any(int(batch.get("max_downloads", 0)) > 90 for batch in batches):
        errors.append("V9.30 V9.31 batches must be capped at 90 days")
    if any(batch.get("overwrite_complete_days") is not False for batch in batches):
        errors.append("V9.30 V9.31 batches must never overwrite complete days")
    if sum(int(batch.get("expected_days", 0)) for batch in batches) != report.get("extension_days_needed"):
        errors.append("V9.30 V9.31 batch days must equal extension_days_needed")
    return errors


def validate_safety_v9_30(flags: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in SAFETY_FLAGS_V9_30.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.30 safety mismatch: {key}")
    return errors


def validate_manifest_payload_v9_30(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.30 manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.30 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.30 manifest safety flags mismatch")
    if manifest.get("extension_days_needed") != report.get("extension_days_needed"):
        errors.append("V9.30 manifest extension_days_needed mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.30 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_30(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.30 markdown contains forbidden metric term: {forbidden}")
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
        "aucune nouvelle ingestion",
        "aucune suppression destructive",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.30 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_30(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_30*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        lowered = path.name.casefold()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden V9.30 artifact suffix: {path}")
    for path in root.glob("projet-galapagos-v9.30-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.30 ZIP sidecar: {path}")
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
