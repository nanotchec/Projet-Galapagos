from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47 import FINDINGS, MANIFEST_PATH, REPORT_JSON_PATH, REPORT_MD_PATH, SAFETY_FLAGS, combined_feature_output_path_v9_47
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import EXPECTED_ROWS_BY_TIMEFRAME, EXPECTED_TIMEFRAMES, FEATURE_COLUMNS, FORBIDDEN_FEATURE_COLUMNS, STRICT_COLUMNS


VERSION = "V9.47"
ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_exact_5y_feature_store_created",
    "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings",
    "ohlcv_aggtrades_exact_5y_feature_store_partial",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_alignment",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_schema",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_quality",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_leakage",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_runtime",
    "ohlcv_aggtrades_exact_5y_feature_store_blocked_by_storage",
    "stop_combined_feature_branch",
}


def validate_ohlcv_aggtrades_exact_5y_feature_store_v9_47(root: Path = Path("."), *, audit_lite: bool = False) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH, REPORT_MD_PATH, MANIFEST_PATH]:
        if not (root / path).is_file():
            errors.append(f"missing V9.47 artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH)
    manifest = _read_json(root / MANIFEST_PATH)
    errors.extend(validate_report_payload_v9_47(report))
    errors.extend(validate_manifest_payload_v9_47(manifest, report))
    if not audit_lite and report.get("features_created") is True:
        errors.extend(validate_feature_files_v9_47(root, report))
    if audit_lite:
        errors.extend(validate_audit_lite_scope_v9_47(root))
    errors.extend(validate_no_forbidden_sidecars_v9_47(root))
    return errors


def validate_report_payload_v9_47(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.46":
        errors.append("V9.47 report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.47 decision is not allowed")
    if set(report.get("timeframes", [])) != set(EXPECTED_TIMEFRAMES):
        errors.append("V9.47 timeframes mismatch")
    if report.get("combined_feature_columns_count") != len(FEATURE_COLUMNS):
        errors.append("V9.47 combined feature column count mismatch")
    for key in ["dataset_created", "labels_created", "ml_executed", "walk_forward_executed", "backtest_executed", "signal_created", "strategy_created", "network_used", "new_data_downloaded"]:
        if report.get(key) is not False:
            errors.append(f"V9.47 forbidden flag must be false: {key}")
    if report.get("findings") != FINDINGS:
        errors.append("V9.47 findings mismatch")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.47 safety flag mismatch: {key}")
    if report.get("leakage_guard", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.47 leakage guard status missing")
    if report.get("forbidden_column_scan", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.47 forbidden column scan status missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.47 report contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_manifest_payload_v9_47(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION or manifest.get("source_version") != "V9.46":
        errors.append("V9.47 manifest version/source mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.47 manifest decision mismatch")
    if manifest.get("combined_feature_columns_count") != report.get("combined_feature_columns_count"):
        errors.append("V9.47 manifest feature count mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.47 manifest safety flags mismatch")
    if manifest.get("sidecars_created") is not False or manifest.get("zip_fingerprints_created") is not False:
        errors.append("V9.47 manifest must confirm no sidecars and no ZIP fingerprints")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.47 manifest contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_feature_files_v9_47(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in EXPECTED_TIMEFRAMES:
        path = combined_feature_output_path_v9_47(root, timeframe)
        if not path.is_file():
            errors.append(f"missing V9.47 feature file: {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != STRICT_COLUMNS:
            errors.append(f"{timeframe}: strict columns mismatch")
        if len(frame) != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
            errors.append(f"{timeframe}: row count mismatch")
        if frame["open_ts"].duplicated().any() or frame["close_ts"].duplicated().any():
            errors.append(f"{timeframe}: duplicate timestamps")
        if not frame["open_ts"].is_monotonic_increasing:
            errors.append(f"{timeframe}: timestamps not monotone")
        if (pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).any():
            errors.append(f"{timeframe}: leakage guard violation")
        forbidden = [column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)]
        if forbidden:
            errors.append(f"{timeframe}: forbidden columns present: {forbidden}")
        warmup_mask = frame["warmup_row"].astype(bool)
        if frame.loc[~warmup_mask, FEATURE_COLUMNS].isna().sum().sum() != 0:
            errors.append(f"{timeframe}: non-warmup feature nulls present")
        if (~frame.loc[~warmup_mask, "row_valid_for_combined_features"].astype(bool)).sum() != 0:
            errors.append(f"{timeframe}: invalid non-warmup combined feature rows")
    return errors


def validate_audit_lite_scope_v9_47(root: Path) -> list[str]:
    errors: list[str] = []
    for prefix in ["data/research/", "data/raw/", "data/silver/"]:
        if (root / prefix).exists():
            errors.append(f"audit-lite must not include full data directory: {prefix}")
    return errors


def validate_no_forbidden_sidecars_v9_47(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".venv", "__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.relative_to(root).parts):
            continue
        if relative.startswith("projet-galapagos-v9.47-audit-lite.zip"):
            continue
        if "v9.47" in path.name.casefold() and path.name.endswith((".sha256.json", ".sha256.txt")):
            errors.append(f"forbidden V9.47 sidecar artifact: {relative}")
        if "v9_47" in relative.casefold() and path.name.endswith((".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")):
            errors.append(f"forbidden V9.47 persistent model artifact: {relative}")
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
