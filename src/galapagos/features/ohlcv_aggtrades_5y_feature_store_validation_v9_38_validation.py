from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_aggtrades_5y_feature_store_validation_v9_38 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    VERSION,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FORBIDDEN_FEATURE_COLUMNS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
)


REQUIRED_TRUE_SAFETY_FLAGS = {
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
    "no_new_data_download",
    "no_destructive_cleanup",
    "no_sidecars",
    "no_zip_fingerprints",
}

REQUIRED_FALSE_SAFETY_FLAGS = {
    "api_key_used",
    "private_endpoint_used",
    "exchange_auth_used",
    "websocket_live_used",
    "network_used",
}


def validate_v9_38_report(root: Path = Path(".")) -> dict[str, Any]:
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
    errors.extend(validate_report_payload_v9_38(report))
    errors.extend(validate_manifest_payload_v9_38(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_38(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.37":
        errors.append("report version/source_version mismatch")
    target = report.get("target_window", {})
    if target.get("start") != TARGET_WINDOW_START or target.get("end") != TARGET_WINDOW_END or target.get("days_expected") != 1827:
        errors.append("target window mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    if set(report.get("timeframes", [])) != set(EXPECTED_TIMEFRAMES):
        errors.append("timeframes mismatch")
    if report.get("feature_columns_count") != len(FEATURE_COLUMNS):
        errors.append("feature_columns_count mismatch")
    if set(report.get("feature_columns", [])) != set(FEATURE_COLUMNS):
        errors.append("feature_columns mismatch")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.38 must not create labels, dataset or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.38 must not run walk-forward or backtest")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False or report.get("ingestion_executed") is not False:
        errors.append("V9.38 must not use network, download data or ingest data")
    if report.get("features_full_modified") is not False:
        errors.append("V9.38 must not modify full feature files")
    if report.get("decision") in {"ohlcv_aggtrades_5y_feature_store_validated", "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings"}:
        if report.get("quality_status") != "PASS" or report.get("coverage_status") != "target_5y_feature_window_complete":
            errors.append("validated decision requires PASS quality and complete coverage")
        if report.get("schema_status") != "PASS" or report.get("leakage_guard_status") != "PASS":
            errors.append("validated decision requires PASS schema and leakage guard")
    errors.extend(_validate_timeframe_reports(report))
    errors.extend(_validate_schema_quality_leakage(report))
    errors.extend(_validate_zero_trade_and_limitations(report))
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_38(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "quality_status", "coverage_status", "schema_status", "leakage_guard_status", "features_full_modified", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def _validate_timeframe_reports(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    reports = report.get("feature_store_validation", {})
    if set(reports) != set(EXPECTED_TIMEFRAMES):
        errors.append("feature_store_validation must contain every expected timeframe")
        return errors
    for timeframe, expected_rows in EXPECTED_ROWS_BY_TIMEFRAME.items():
        item = reports.get(timeframe, {})
        if item.get("actual_rows") != expected_rows or item.get("expected_rows") != expected_rows:
            errors.append(f"{timeframe} row count mismatch")
        if item.get("days_missing") != 0 or item.get("coverage_status") != "PASS" or item.get("complete_calendar_coverage") is not True:
            errors.append(f"{timeframe} coverage must be complete")
        if item.get("strict_schema_status") != "PASS" or item.get("quality_status") != "PASS":
            errors.append(f"{timeframe} schema and quality must pass")
        if item.get("feature_available_ts_lte_decision_ts") is not True or item.get("available_ts_lte_decision_ts") is not True:
            errors.append(f"{timeframe} timestamp availability guard failed")
        if item.get("rolling_windows_past_only_status") != "PASS":
            errors.append(f"{timeframe} rolling windows guard failed")
        if item.get("forbidden_columns"):
            errors.append(f"{timeframe} forbidden columns present")
    return errors


def _validate_schema_quality_leakage(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema = report.get("schema_validation", {})
    quality = report.get("quality_validation", {})
    leakage = report.get("leakage_guard", {})
    if schema.get("status") != "PASS":
        errors.append("schema validation must pass")
    if quality.get("status") != "PASS":
        errors.append("quality validation must pass")
    if leakage.get("status") != "PASS" or leakage.get("rolling_windows_past_only") is not True:
        errors.append("leakage guard must pass")
    forbidden = schema.get("forbidden_scan", {})
    if forbidden.get("status") != "PASS" or forbidden.get("forbidden_columns"):
        errors.append("forbidden column scan must pass")
    if not FORBIDDEN_FEATURE_COLUMNS.issubset(set(forbidden.get("scanned_terms", []))):
        errors.append("forbidden scan vocabulary incomplete")
    return errors


def _validate_zero_trade_and_limitations(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    zero = report.get("zero_trade_bucket_validation", {})
    limitations = report.get("aggtrades_feature_limitations", {})
    if zero.get("status") != "PASS" or zero.get("zero_trade_bucket_blocking") is not False:
        errors.append("zero-trade bucket validation must be non-blocking PASS")
    if limitations.get("direct_aggtrades_full_scan_performed") is not False:
        errors.append("V9.38 must not claim a direct full aggTrades scan")
    if limitations.get("non_blocking_for_current_feature_store_validation") is not True:
        errors.append("V9.37 aggTrades limitations must be classified explicitly")
    if limitations.get("blocking_for_next_dataset") is not False:
        errors.append("V9.37 limitations must not block V9.39 when quality passes")
    return errors


def _validate_safety_flags(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key in sorted(REQUIRED_TRUE_SAFETY_FLAGS):
        if flags.get(key) is not True:
            errors.append(f"safety flag {key} must be true")
    for key in sorted(REQUIRED_FALSE_SAFETY_FLAGS):
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
        "coverage_status": None if report is None else report.get("coverage_status"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
