from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_5y_extension_collection_v9_31 import (
    ALLOWED_DECISIONS,
    ALREADY_VALIDATED_WINDOW_END,
    ALREADY_VALIDATED_WINDOW_START,
    EXTENSION_WINDOW_END,
    EXTENSION_WINDOW_START,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
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


def validate_aggtrades_5y_extension_collection_v9_31(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.is_file():
        return [f"missing V9.31 report: {REPORT_JSON_PATH}"]
    if not manifest_path.is_file():
        errors.append(f"missing V9.31 manifest: {MANIFEST_PATH}")
    if not markdown_path.is_file():
        errors.append(f"missing V9.31 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_31(report))
    errors.extend(validate_manifest_payload_v9_31(manifest, report))
    errors.extend(validate_markdown_v9_31(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_31(root))
    return errors


def validate_report_payload_v9_31(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.31 version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.31 source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.31 decision is not allowed")
    if report.get("findings") != FINDINGS:
        errors.append("V9.31 findings mismatch")
    errors.extend(validate_windows_v9_31(report))
    errors.extend(validate_collection_outcome_v9_31(report))
    errors.extend(validate_safety_v9_31(report.get("safety_flags", {}), report))
    if _contains_forbidden_zip_field(report):
        errors.append("V9.31 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_windows_v9_31(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "extension_window_start": EXTENSION_WINDOW_START,
        "extension_window_end": EXTENSION_WINDOW_END,
        "already_validated_window_start": ALREADY_VALIDATED_WINDOW_START,
        "already_validated_window_end": ALREADY_VALIDATED_WINDOW_END,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            errors.append(f"V9.31 window mismatch: {key}")
    if report.get("days_expected_extension") != 1096:
        errors.append("V9.31 extension days must be 1096")
    planned = report.get("batches_planned_detail", [])
    if not planned:
        errors.append("V9.31 must include planned batches")
    elif planned[0].get("start_date") != EXTENSION_WINDOW_START or planned[-1].get("end_date") != EXTENSION_WINDOW_END:
        errors.append("V9.31 planned batches must cover the extension window")
    if any(int(batch.get("max_downloads", 0)) > 60 for batch in planned):
        errors.append("V9.31 batches must be capped at 60 downloads")
    return errors


def validate_collection_outcome_v9_31(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    decision = report.get("decision")
    complete = decision == "aggtrades_5y_extension_collection_complete"
    if complete:
        expected = {
            "days_complete": 1096,
            "days_missing": 0,
            "days_failed": 0,
            "days_quarantined": 0,
        }
        for key, value in expected.items():
            if report.get(key) != value:
                errors.append(f"V9.31 complete report mismatch for {key}")
        if report.get("complete_extension_reached") is not True:
            errors.append("V9.31 complete decision requires complete_extension_reached=true")
        if report.get("target_5y_collection_reached") is not True:
            errors.append("V9.31 complete decision requires target_5y_collection_reached=true")
        if report.get("quality_status") != "PASS" or report.get("coverage_status") != "extension_complete":
            errors.append("V9.31 complete decision requires PASS quality and extension_complete coverage")
    else:
        if report.get("complete_extension_reached") is True and report.get("quality_status") == "PASS":
            errors.append("V9.31 non-complete decision cannot claim clean complete extension")
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.31 must keep {key}=false")
    return errors


def validate_safety_v9_31(flags: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in [
        "no_trading",
        "no_paper_live",
        "no_orders",
        "no_backtest",
        "no_walk_forward",
        "no_ml",
        "no_dataset_supervised",
        "no_strategy",
        "no_actionable_signal",
        "no_persistent_model",
        "no_destructive_cleanup",
        "no_sidecars",
        "no_zip_fingerprints",
    ]:
        if flags.get(key) is not True:
            errors.append(f"V9.31 safety mismatch: {key}")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if flags.get(key) is not False:
            errors.append(f"V9.31 safety mismatch: {key}")
    if report.get("days_attempted", 0) > 0:
        expected = {
            "network_used": True,
            "network_scope": "public_archive_read_only",
            "new_data_download_scope": "public_historical_aggtrades_5y_extension_only",
            "ingestion_scope": "public_aggtrades_bronze_silver_5y_extension_only",
        }
        for key, value in expected.items():
            if flags.get(key) != value:
                errors.append(f"V9.31 collection safety mismatch: {key}")
    else:
        if flags.get("network_used") is not False or flags.get("no_new_data_download") is not True:
            errors.append("V9.31 non-executed safety must keep no network and no new data")
    return errors


def validate_manifest_payload_v9_31(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.31 manifest version mismatch")
    for key in ["status", "decision", "days_expected_extension", "days_complete", "days_failed", "complete_extension_reached", "target_5y_collection_reached"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"V9.31 manifest mismatch: {key}")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.31 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.31 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_31(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.31 markdown contains forbidden metric term: {forbidden}")
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
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.31 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_31(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_31*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        lowered = path.name.casefold()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden V9.31 artifact suffix: {path}")
    for path in root.glob("projet-galapagos-v9.31-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.31 ZIP sidecar: {path}")
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
