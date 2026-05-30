from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.ohlcv_5y_extension_v9_34 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    TIMEFRAMES,
    VERSION,
)


REQUIRED_TRUE_FLAGS = {
    "no_trading",
    "no_paper_live",
    "no_orders",
    "no_backtest",
    "no_walk_forward",
    "no_ml",
    "no_dataset_supervised",
    "no_labels",
    "no_strategy",
    "no_actionable_signal",
    "no_persistent_model",
    "no_destructive_cleanup",
    "no_sidecars",
    "no_zip_fingerprints",
}

REQUIRED_FALSE_FLAGS = {
    "api_key_used",
    "private_endpoint_used",
    "exchange_auth_used",
    "websocket_live_used",
}


def validate_v9_34_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    errors: list[str] = []
    if not report_path.is_file():
        errors.append(f"missing report: {REPORT_JSON_PATH.as_posix()}")
        return _result(errors)
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH.as_posix()}")
        return _result(errors)
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_34(report))
    errors.extend(validate_manifest_payload_v9_34(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_34(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.33":
        errors.append("report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if report.get("target_window_start") != "2021-05-05" or report.get("target_window_end") != "2026-05-05":
        errors.append("target window mismatch")
    if report.get("missing_window_start") != "2021-05-05" or report.get("missing_window_end") != "2023-03-24":
        errors.append("missing extension window mismatch")
    if set(report.get("timeframes_required", [])) != set(TIMEFRAMES):
        errors.append("timeframes_required mismatch")
    source = report.get("source", {})
    if source.get("host") != "data.binance.vision" or source.get("public_read_only") is not True:
        errors.append("source must remain Binance public archive read-only")
    if report.get("decision") == "ohlcv_5y_extension_complete":
        if report.get("ohlcv_5y_ready") is not True:
            errors.append("complete decision requires ohlcv_5y_ready=true")
        missing = report.get("diagnostic_after", {}).get("missing_days_by_timeframe", {})
        if any(value != 0 for value in missing.values()):
            errors.append("complete decision requires zero missing days for all timeframes")
    if report.get("decision") == "ohlcv_5y_extension_failed_source_issue" and report.get("derive_ohlcv_from_aggtrades_possible") is not True:
        errors.append("source issue must preserve derivation option")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.34 must not create labels, datasets or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.34 must not run walk-forward or backtest")
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_34(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "network_used", "new_data_downloaded", "ingestion_executed", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def _validate_safety_flags(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key in sorted(REQUIRED_TRUE_FLAGS):
        if flags.get(key) is not True:
            errors.append(f"safety flag {key} must be true")
    for key in sorted(REQUIRED_FALSE_FLAGS):
        if flags.get(key) is not False:
            errors.append(f"safety flag {key} must be false")
    if flags.get("network_used") != report.get("network_used"):
        errors.append("safety network_used mismatch")
    if flags.get("new_data_downloaded") != report.get("new_data_downloaded"):
        errors.append("safety new_data_downloaded mismatch")
    if flags.get("ingestion_executed") != report.get("ingestion_executed"):
        errors.append("safety ingestion_executed mismatch")
    return errors


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "ohlcv_5y_ready": None if report is None else report.get("ohlcv_5y_ready"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
