from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SOURCE_VERSION,
    TARGET_5Y_WINDOW_END,
    TARGET_5Y_WINDOW_START,
    TOTAL_DAYS_EXPECTED_5Y,
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


def validate_aggtrades_5y_full_coverage_validation_v9_32(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.is_file():
        return [f"missing V9.32 report: {REPORT_JSON_PATH}"]
    if not manifest_path.is_file():
        errors.append(f"missing V9.32 manifest: {MANIFEST_PATH}")
    if not markdown_path.is_file():
        errors.append(f"missing V9.32 markdown: {REPORT_MD_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_32(report))
    errors.extend(validate_manifest_payload_v9_32(manifest, report))
    errors.extend(validate_markdown_v9_32(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_v9_32(root))
    return errors


def validate_report_payload_v9_32(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.32 version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.32 source_version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.32 decision is not allowed")
    if report.get("findings") != FINDINGS:
        errors.append("V9.32 findings mismatch")
    errors.extend(validate_windows_v9_32(report))
    errors.extend(validate_coverage_quality_v9_32(report))
    errors.extend(validate_reconciliation_v9_32(report))
    errors.extend(validate_safety_v9_32(report.get("safety_flags", {}), report))
    if _contains_forbidden_zip_field(report):
        errors.append("V9.32 report must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_windows_v9_32(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "days_expected_5y": TOTAL_DAYS_EXPECTED_5Y,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            errors.append(f"V9.32 window mismatch: {key}")
    return errors


def validate_coverage_quality_v9_32(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    decision = report.get("decision")
    validated = decision in {
        "aggtrades_5y_full_coverage_validated",
        "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings",
    }
    if validated:
        expected = {
            "days_complete": TOTAL_DAYS_EXPECTED_5Y,
            "days_missing": 0,
            "days_failed": 0,
            "global_duplicate_count": 0,
            "global_invalid_rows": 0,
            "schema_mismatch_count": 0,
            "non_positive_price_count": 0,
            "non_positive_quantity_count": 0,
            "available_ts_violation_count": 0,
            "partition_mismatch_count": 0,
        }
        for key, value in expected.items():
            if report.get(key) != value:
                errors.append(f"V9.32 validated report mismatch for {key}")
        if report.get("complete_collection_reached") is not True:
            errors.append("V9.32 validated decision requires complete_collection_reached=true")
        if report.get("future_full_coverage_complete") is not True:
            errors.append("V9.32 validated decision requires future_full_coverage_complete=true")
        if report.get("quality_status") != "PASS":
            errors.append("V9.32 validated decision requires quality_status=PASS")
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.32 must keep {key}=false")
    return errors


def validate_reconciliation_v9_32(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    reconciliation = report.get("v9_31_counter_reconciliation", {})
    if reconciliation.get("days_complete_reported") != 1096:
        errors.append("V9.32 reconciliation must preserve V9.31 reported complete days")
    if reconciliation.get("days_complete_canonical") != 1096:
        errors.append("V9.32 reconciliation must confirm 1096 canonical extension days")
    if reconciliation.get("reporting_inconsistency_blocking") is not False:
        errors.append("V9.32 V9.31 reporting ambiguity must be explicitly non-blocking when files validate")
    if report.get("reporting_inconsistency_blocking") is not False:
        errors.append("V9.32 flattened reporting ambiguity must be non-blocking")
    return errors


def validate_safety_v9_32(flags: dict[str, Any], report: dict[str, Any]) -> list[str]:
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
        "no_data_deletion",
        "no_destructive_cleanup",
        "no_sidecars",
        "no_zip_fingerprints",
        "no_new_data_download",
        "no_ingestion_executed",
    ]:
        if flags.get(key) is not True:
            errors.append(f"V9.32 safety mismatch: {key}")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used", "network_used"]:
        if flags.get(key) is not False:
            errors.append(f"V9.32 safety mismatch: {key}")
    for key in ["network_used", "new_data_downloaded", "ingestion_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.32 report must keep {key}=false")
    return errors


def validate_manifest_payload_v9_32(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.32 manifest version mismatch")
    for key in [
        "status",
        "decision",
        "days_expected_5y",
        "days_complete",
        "days_failed",
        "global_duplicate_count",
        "global_invalid_rows",
        "complete_collection_reached",
        "future_full_coverage_complete",
    ]:
        if manifest.get(key) != report.get(key):
            errors.append(f"V9.32 manifest mismatch: {key}")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.32 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.32 manifest must not contain ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_32(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.32 markdown contains forbidden metric term: {forbidden}")
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
        "aucun telechargement de nouvelles donnees",
        "aucune nouvelle ingestion",
        "aucune suppression destructive",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.32 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_v9_32(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*v9_32*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        lowered = path.name.casefold()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden V9.32 artifact suffix: {path}")
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
