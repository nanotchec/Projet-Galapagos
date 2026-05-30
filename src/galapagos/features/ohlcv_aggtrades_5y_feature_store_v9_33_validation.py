from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33 import (
    ALLOWED_DECISIONS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    VERSION,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_schemas import (
    EXPECTED_TIMEFRAMES,
    FORBIDDEN_FEATURE_COLUMNS,
    READINESS_REQUIRED_REPORT_KEYS,
    TARGET_5Y_WINDOW_END,
    TARGET_5Y_WINDOW_START,
)


REQUIRED_TRUE_SAFETY_FLAGS = {
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
    "no_new_data_download",
    "no_ingestion_executed",
    "no_data_deletion",
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
    "ingestion_executed",
}


def validate_v9_33_report(root: Path = Path(".")) -> dict[str, Any]:
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
    errors.extend(validate_report_payload_v9_33(report))
    errors.extend(validate_manifest_payload_v9_33(report, manifest))
    return _result(errors, report)


def validate_report_payload_v9_33(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_keys = sorted(READINESS_REQUIRED_REPORT_KEYS - set(report))
    if missing_keys:
        errors.append(f"missing report keys: {missing_keys}")
    if report.get("version") != VERSION or report.get("source_version") != "V9.32":
        errors.append("report version/source_version mismatch")
    if report.get("target_5y_window_start") != TARGET_5Y_WINDOW_START or report.get("target_5y_window_end") != TARGET_5Y_WINDOW_END:
        errors.append("target 5Y window mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("decision is not allowed")
    ohlcv = report.get("ohlcv_readiness", {})
    aggtrades = report.get("aggtrades_readiness", {})
    if set(ohlcv.get("timeframes", {}).keys()) != set(EXPECTED_TIMEFRAMES):
        errors.append("OHLCV readiness must cover every expected timeframe")
    if aggtrades.get("aggtrades_5y_ready") is not True:
        errors.append("V9.33 expects V9.32 aggTrades 5Y readiness to be true")
    if ohlcv.get("ohlcv_5y_ready") is not True:
        _validate_not_created_path(report, errors)
    else:
        _validate_created_path(report, errors)
    errors.extend(_validate_quality(report))
    errors.extend(_validate_safety_flags(report))
    return errors


def validate_manifest_payload_v9_33(report: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["version", "source_version", "decision", "feature_store_created", "features_created", "quality_status", "safety_flags"]:
        if manifest.get(key) != report.get(key):
            errors.append(f"manifest mismatch for {key}")
    if manifest.get("report_path") != REPORT_JSON_PATH.as_posix():
        errors.append("manifest report_path mismatch")
    return errors


def _validate_not_created_path(report: dict[str, Any], errors: list[str]) -> None:
    if report.get("decision") != "ohlcv_5y_extension_required_before_feature_store":
        errors.append("incomplete OHLCV readiness must choose ohlcv_5y_extension_required_before_feature_store")
    if report.get("feature_store_created") is not False or report.get("features_created") is not False:
        errors.append("feature store must not be created when OHLCV 5Y is incomplete")
    if report.get("quality_status") != "NOT_CREATED":
        errors.append("not-created feature store must use quality_status=NOT_CREATED")
    candidate = report.get("feature_store_candidate", {})
    if candidate.get("feature_store_paths"):
        errors.append("not-created feature store must not expose materialized feature paths")


def _validate_created_path(report: dict[str, Any], errors: list[str]) -> None:
    if report.get("feature_store_created") is not True or report.get("features_created") is not True:
        errors.append("ready OHLCV and aggTrades must create feature store or explicitly fail quality")
    if report.get("decision") not in {"ohlcv_aggtrades_5y_feature_store_created", "ohlcv_aggtrades_5y_feature_store_created_with_warnings", "ohlcv_aggtrades_5y_feature_store_blocked_by_quality"}:
        errors.append("created path decision mismatch")


def _validate_quality(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    quality = report.get("feature_quality", {})
    forbidden_scan = report.get("forbidden_columns_scan", {})
    if forbidden_scan.get("status") != "PASS":
        errors.append("forbidden column scan must pass")
    forbidden_columns = set(forbidden_scan.get("forbidden_columns", []))
    if forbidden_columns:
        errors.append(f"forbidden feature columns found: {sorted(forbidden_columns)}")
    scanned_terms = set(forbidden_scan.get("scanned_terms", []))
    if not FORBIDDEN_FEATURE_COLUMNS.issubset(scanned_terms):
        errors.append("forbidden column scan did not include the full required vocabulary")
    leakage = report.get("leakage_guard", {})
    if report.get("feature_store_created") is False:
        if leakage.get("status") != "not_applicable_no_feature_store_created":
            errors.append("leakage guard must be not applicable when no feature store is created")
    elif leakage.get("status") != "PASS":
        errors.append("leakage guard must pass when feature store is created")
    if quality.get("quality_status") != report.get("quality_status"):
        errors.append("feature_quality quality_status mismatch")
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
    for key in ["labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed", "network_used", "new_data_downloaded", "ingestion_executed"]:
        if report.get(key) is not False:
            errors.append(f"report flag {key} must be false")
    return errors


def _result(errors: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "decision": None if report is None else report.get("decision"),
        "feature_store_created": None if report is None else report.get("feature_store_created"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
