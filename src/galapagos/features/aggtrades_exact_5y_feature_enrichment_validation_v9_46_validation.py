from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_ROWS_BY_TIMEFRAME, EXPECTED_TIMEFRAMES, FEATURE_COLUMNS, FORBIDDEN_FEATURE_COLUMNS, STRICT_COLUMNS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46 import (
    DOC_PATH,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    SAMPLE_REPORT_PATH,
    SAMPLE_ROOT,
)


VERSION = "V9.46"
ALLOWED_DECISIONS = {
    "aggtrades_exact_5y_feature_enrichment_validated",
    "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings",
    "aggtrades_exact_5y_feature_enrichment_blocked_by_coverage",
    "aggtrades_exact_5y_feature_enrichment_blocked_by_schema",
    "aggtrades_exact_5y_feature_enrichment_blocked_by_quality",
    "aggtrades_exact_5y_feature_enrichment_blocked_by_leakage",
    "aggtrades_exact_5y_feature_enrichment_inconclusive_manual_review_required",
    "stop_aggtrades_exact_feature_branch",
}


def validate_aggtrades_exact_5y_feature_enrichment_validation_v9_46(root: Path = Path("."), *, mode: str = "full-local") -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH, REPORT_MD_PATH, DOC_PATH, MANIFEST_PATH, SAMPLE_REPORT_PATH]:
        if not (root / path).is_file():
            errors.append(f"missing V9.46 artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH)
    manifest = _read_json(root / MANIFEST_PATH)
    sample_report = _read_json(root / SAMPLE_REPORT_PATH)
    errors.extend(validate_report_payload_v9_46(report))
    errors.extend(validate_manifest_payload_v9_46(manifest, report))
    errors.extend(validate_sample_report_payload_v9_46(root, sample_report, require_parquet_checks=mode == "audit-lite"))
    if mode == "full-local" and report.get("validation_mode") == "full-local":
        errors.extend(validate_full_local_report_summaries_v9_46(report))
    errors.extend(validate_no_forbidden_sidecars_v9_46(root))
    return errors


def validate_report_payload_v9_46(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.45":
        errors.append("V9.46 report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.46 decision is not allowed")
    if set(report.get("timeframes", [])) != set(EXPECTED_TIMEFRAMES):
        errors.append("V9.46 timeframes mismatch")
    if report.get("feature_columns_count") != len(FEATURE_COLUMNS):
        errors.append("V9.46 feature column count mismatch")
    for key in ["features_created", "feature_store_combined_created", "dataset_created", "labels_created", "ml_executed", "walk_forward_executed", "backtest_executed", "signal_created", "strategy_created", "network_used", "new_data_downloaded"]:
        if report.get(key) is not False:
            errors.append(f"V9.46 forbidden flag must be false: {key}")
    if report.get("findings") != FINDINGS:
        errors.append("V9.46 findings mismatch")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.46 safety flag mismatch: {key}")
    if report.get("coverage_validation", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.46 coverage validation status missing")
    if report.get("schema_validation", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.46 schema validation status missing")
    if report.get("quality_validation", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.46 quality validation status missing")
    if report.get("leakage_guard", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.46 leakage guard status missing")
    if report.get("forbidden_column_scan", {}).get("status") not in {"PASS", "FAIL"}:
        errors.append("V9.46 forbidden column scan status missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.46 report contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_full_local_report_summaries_v9_46(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in EXPECTED_TIMEFRAMES:
        item = report.get("timeframe_reports", {}).get(timeframe, {})
        if item.get("actual_rows") != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
            errors.append(f"{timeframe}: expected row count mismatch")
        for key in ["coverage_status", "schema_status", "quality_status", "leakage_guard_status"]:
            if item.get(key) != "PASS":
                errors.append(f"{timeframe}: {key} must be PASS")
        if item.get("null_summary", {}).get("feature_null_count") != 0:
            errors.append(f"{timeframe}: feature nulls must be zero")
        if item.get("zero_trade_bucket_summary", {}).get("zero_trade_bucket_blocking") is not False:
            errors.append(f"{timeframe}: zero-trade buckets must be non-blocking")
    return errors


def validate_manifest_payload_v9_46(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION or manifest.get("source_version") != "V9.45":
        errors.append("V9.46 manifest version/source mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.46 manifest decision mismatch")
    if manifest.get("feature_columns_count") != report.get("feature_columns_count"):
        errors.append("V9.46 manifest feature count mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.46 manifest safety flags mismatch")
    if manifest.get("sidecars_created") is not False or manifest.get("zip_fingerprints_created") is not False:
        errors.append("V9.46 manifest must confirm no sidecars and no ZIP fingerprints")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.46 manifest contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_sample_report_payload_v9_46(root: Path, sample_report: dict[str, Any], *, require_parquet_checks: bool) -> list[str]:
    errors: list[str] = []
    samples = sample_report.get("samples", {})
    if set(samples) != set(EXPECTED_TIMEFRAMES):
        errors.append("V9.46 sample report timeframe mismatch")
    if sample_report.get("full_feature_parquets_included") is not False:
        errors.append("V9.46 sample report must confirm full Parquets are excluded")
    if require_parquet_checks:
        for timeframe, item in samples.items():
            path = root / item.get("sample_path", "")
            if not path.is_file():
                errors.append(f"{timeframe}: missing sample parquet")
                continue
            try:
                frame = pd.read_parquet(path, engine="pyarrow")
            except ImportError as exc:
                errors.append(f"{timeframe}: pyarrow or parquet engine missing for sample checks: {exc}")
                continue
            if list(frame.columns) != STRICT_COLUMNS:
                errors.append(f"{timeframe}: sample strict schema mismatch")
            forbidden = [column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)]
            if forbidden:
                errors.append(f"{timeframe}: forbidden sample columns: {forbidden}")
    return errors


def validate_no_forbidden_sidecars_v9_46(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".venv", "__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.relative_to(root).parts):
            continue
        if relative.startswith("projet-galapagos-v9.46-audit-lite.zip"):
            continue
        if "v9.46" in path.name.casefold() and path.name.endswith((".sha256.json", ".sha256.txt")):
            errors.append(f"forbidden V9.46 sidecar artifact: {relative}")
        if "v9_46" in relative.casefold() and path.name.endswith((".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")):
            errors.append(f"forbidden V9.46 persistent model artifact: {relative}")
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
