from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import (
    ALLOWED_DECISIONS,
    DERIVED_COLUMNS,
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
    "no_combined_feature_store",
    "no_strategy",
    "no_actionable_signal",
    "no_persistent_model",
    "no_new_data_download",
    "no_destructive_cleanup",
    "no_sidecars",
    "no_zip_fingerprints",
}

REQUIRED_FALSE_FLAGS = {
    "api_key_used",
    "private_endpoint_used",
    "exchange_auth_used",
    "websocket_live_used",
    "network_used",
}


def validate_v9_35_report(root: Path = Path(".")) -> dict[str, Any]:
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
    errors.extend(validate_report_payload_v9_35(report))
    errors.extend(validate_manifest_payload_v9_35(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_35(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.34.1":
        errors.append("report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if report.get("target_window_start") != "2021-05-05" or report.get("target_window_end") != "2026-05-05":
        errors.append("target window mismatch")
    if set(report.get("timeframes_required", [])) != set(TIMEFRAMES):
        errors.append("timeframes_required mismatch")
    method = report.get("method", {})
    if method.get("ohlcv_source_type") != "derived_from_aggtrades" or method.get("network_used") is not False:
        errors.append("method must be offline derived_from_aggtrades")
    if report.get("feature_store_created") is not False or report.get("combined_feature_store_created") is not False:
        errors.append("V9.35 must not create combined feature store")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.35 must not create labels, datasets or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.35 must not run walk-forward or backtest")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.35 must not use network or download new data")
    if report.get("decision") in {"ohlcv_from_aggtrades_5y_derivation_complete", "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings"}:
        if set(report.get("timeframes_produced", [])) != set(TIMEFRAMES):
            errors.append("complete decision requires all four timeframes")
        if report.get("quality_status") != "PASS":
            errors.append("complete decision requires quality_status PASS")
    for timeframe_report in report.get("timeframe_reports", []):
        if timeframe_report.get("quality_status") == "PASS" and timeframe_report.get("days_missing") != 0:
            errors.append(f"{timeframe_report.get('timeframe')} cannot pass with missing days")
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_35(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "network_used", "new_data_downloaded", "ingestion_executed", "feature_store_created", "combined_feature_store_created", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def validate_derived_schema_columns_v9_35(columns: list[str]) -> list[str]:
    missing = sorted(set(DERIVED_COLUMNS) - set(columns))
    extra = sorted(set(columns) - set(DERIVED_COLUMNS))
    errors: list[str] = []
    if missing:
        errors.append(f"missing derived OHLCV columns: {missing}")
    if extra:
        errors.append(f"unexpected derived OHLCV columns: {extra}")
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
    return errors


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "quality_status": None if report is None else report.get("quality_status"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
