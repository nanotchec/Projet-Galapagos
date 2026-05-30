from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.ohlcv_from_aggtrades_5y_validation_v9_36 import (
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
    "no_feature_store",
    "no_combined_feature_store",
    "no_strategy",
    "no_actionable_signal",
    "no_persistent_model",
    "no_new_data_download",
    "no_ingestion_executed",
    "no_data_deletion",
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


def validate_v9_36_report(root: Path = Path(".")) -> dict[str, Any]:
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
    errors.extend(validate_report_payload_v9_36(report))
    errors.extend(validate_manifest_payload_v9_36(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_36(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.35":
        errors.append("report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if report.get("target_window_start") != "2021-05-05" or report.get("target_window_end") != "2026-05-05":
        errors.append("target window mismatch")
    if set(report.get("timeframes_required", [])) != set(TIMEFRAMES):
        errors.append("timeframes_required mismatch")
    if report.get("feature_store_created") is not False or report.get("combined_feature_store_created") is not False:
        errors.append("V9.36 must not create combined feature store")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.36 must not create labels, datasets or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.36 must not run walk-forward or backtest")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False or report.get("ingestion_executed") is not False:
        errors.append("V9.36 must not use network, download data or ingest new data")
    if report.get("decision") in {"ohlcv_from_aggtrades_5y_validation_pass", "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings"}:
        if report.get("coverage_status") != "target_5y_window_complete" or report.get("quality_status") != "PASS":
            errors.append("pass decision requires complete coverage and PASS quality")
    for timeframe in TIMEFRAMES:
        coverage = report.get("coverage_validation", {}).get(timeframe, {})
        if coverage.get("quality_status") != "PASS" or coverage.get("days_missing") != 0:
            errors.append(f"{timeframe} coverage must pass with zero missing days")
        zero = report.get("zero_trade_bucket_analysis", {}).get(timeframe, {})
        if zero.get("causal_fill_uses_future_data") is not False or zero.get("zero_trade_buckets_blocking") is not False:
            errors.append(f"{timeframe} zero-trade fill must be non-blocking and causal")
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_36(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "network_used", "new_data_downloaded", "ingestion_executed", "feature_store_created", "combined_feature_store_created", "safety_flags"]:
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
