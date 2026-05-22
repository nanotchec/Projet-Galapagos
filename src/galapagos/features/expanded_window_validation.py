from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.expanded_window import output_path as v3_5_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.expanded_window import (
    EXPECTED_LIMITATIONS_V3_6,
    FEATURE_SCHEMA_VERSION_V3_6,
    MANIFEST_PATH_V3_6,
    REPORT_JSON_PATH_V3_6,
    REPORT_MD_PATH_V3_6,
    TIMEFRAMES_V3_6,
    VERSION_V3_6,
    output_path,
)
from galapagos.features.expanded_window_quality import assess_expanded_feature_quality
from galapagos.features.schemas import FEATURE_COLUMNS_V3_6, FORBIDDEN_TERMS
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


RUN_ID_PATTERN_V3_6 = re.compile(r"^v3_6_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "feature_run_id",
    "input_ohlcv",
    "outputs",
    "feature_schema_version",
    "feature_columns",
    "quality",
    "safety",
    "limitations",
}
REPORT_KEYS = MANIFEST_KEYS.copy()
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
QUALITY_KEYS = {
    "rows",
    "expected_rows",
    "warmup_rows",
    "rows_after_warmup",
    "duplicate_rows",
    "null_counts_by_column",
    "inf_counts_by_column",
    "forbidden_columns_present",
    "timestamps_utc",
    "monotonic_event_ts",
    "feature_available_ts_valid",
    "decision_ts_valid",
    "source_hashes_valid",
    "causal_guard_passed",
    "errors",
    "warnings",
}
SAFETY_KEYS = {
    "public_read_only",
    "authentication_used",
    "api_key_used",
    "private_endpoint_used",
    "orders_enabled",
    "paper_live_enabled",
    "trading_enabled",
    "ml_enabled",
    "labels_enabled",
    "dataset_enabled",
    "backtest_enabled",
    "strategy_enabled",
    "execution_enabled",
}
FORBIDDEN_V3_6_PATHS = [
    "data/research/v3_6/labels",
    "data/research/v3_6/datasets",
    "data/research/v3_6/ml",
    "data/research/v3_6/backtests",
    "data/research/v3_6/strategies",
    "reports/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
    "models",
    "checkpoints",
]
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def validate_expanded_causal_feature_store_v3_6(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH_V3_6
    report_path = root / REPORT_JSON_PATH_V3_6
    if not manifest_path.exists():
        return _result([f"missing V3.6 manifest: {MANIFEST_PATH_V3_6}"])
    if not report_path.exists():
        return _result([f"missing V3.6 feature report: {REPORT_JSON_PATH_V3_6}"])

    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(root, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V3.6 manifest"))

    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V3_6:
        input_path = v3_5_ohlcv_path(root, timeframe)
        feature_path = output_path(root, timeframe)
        if not input_path.exists():
            errors.append(f"missing V3.6 input OHLCV: {input_path.relative_to(root)}")
            continue
        if not feature_path.exists():
            errors.append(f"missing V3.6 output features: {feature_path.relative_to(root)}")
            continue

        input_frame = read_parquet(input_path)
        frame = read_parquet(feature_path)
        errors.extend(_validate_input_entry(root, manifest, timeframe, input_path, input_frame))
        errors.extend(_validate_output_entry(root, manifest, timeframe, feature_path, frame))
        frame_errors, quality = _validate_feature_frame(
            timeframe,
            frame,
            input_path,
            input_frame,
            manifest.get("feature_run_id"),
        )
        errors.extend(frame_errors)
        physical_quality[timeframe] = quality

    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V3.6 feature report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v3_6_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V3.6 manifest"))
    if manifest.get("version") != VERSION_V3_6:
        errors.append("V3.6 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.6 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V3.6 manifest created_at_utc invalid")
    run_id = manifest.get("feature_run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN_V3_6.fullmatch(run_id) is None:
        errors.append("V3.6 manifest feature_run_id invalid")
    if manifest.get("feature_schema_version") != FEATURE_SCHEMA_VERSION_V3_6:
        errors.append("V3.6 manifest feature_schema_version mismatch")
    if manifest.get("feature_columns") != FEATURE_COLUMNS_V3_6:
        errors.append("V3.6 manifest feature_columns mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V3_6:
        errors.append("V3.6 manifest limitations mismatch")
    for section, keys in [("input_ohlcv", INPUT_KEYS), ("outputs", OUTPUT_KEYS), ("quality", QUALITY_KEYS)]:
        payload = manifest.get(section, {})
        errors.extend(validate_exact_keys(payload, set(TIMEFRAMES_V3_6), f"V3.6 manifest {section}"))
        for timeframe, block in payload.items():
            errors.extend(validate_exact_keys(block, keys, f"V3.6 manifest {section}.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V3.6 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    for timeframe in TIMEFRAMES_V3_6:
        input_path = v3_5_ohlcv_path(root, timeframe)
        feature_path = output_path(root, timeframe)
        if manifest.get("input_ohlcv", {}).get(timeframe, {}).get("path") != str(input_path.relative_to(root)):
            errors.append(f"V3.6 manifest input path mismatch for {timeframe}")
        if manifest.get("outputs", {}).get(timeframe, {}).get("path") != str(feature_path.relative_to(root)):
            errors.append(f"V3.6 manifest output path mismatch for {timeframe}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V3.6 safety flag public_read_only must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only"}):
        if safety.get(flag) is not False:
            errors.append(f"V3.6 safety flag {flag} must be False")
    return errors


def _validate_input_entry(
    root: Path,
    manifest: dict[str, Any],
    timeframe: str,
    path: Path,
    frame: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []
    payload = manifest.get("input_ohlcv", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"V3.6 manifest input mismatch for {timeframe}.{field}")
    return errors


def _validate_output_entry(root: Path, manifest: dict[str, Any], timeframe: str, path: Path, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    payload = manifest.get("outputs", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "format": "parquet",
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"V3.6 manifest output mismatch for {timeframe}.{field}")
    return errors


def _validate_feature_frame(
    timeframe: str,
    frame: pd.DataFrame,
    input_path: Path,
    input_frame: pd.DataFrame,
    feature_run_id: Any,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if list(frame.columns) != FEATURE_COLUMNS_V3_6:
        errors.append(f"V3.6 feature schema mismatch for {timeframe}")
    forbidden = _forbidden_columns(frame)
    if forbidden:
        errors.append(f"V3.6 forbidden feature columns for {timeframe}: {forbidden}")
    if len(frame) != len(input_frame):
        errors.append(f"V3.6 feature row count mismatch for {timeframe}")

    input_sha = sha256_file(input_path)
    source_hashes_valid = bool(
        "source_ohlcv_sha256" in frame.columns and set(frame["source_ohlcv_sha256"].astype(str).unique()) == {input_sha}
    )
    if not source_hashes_valid:
        errors.append(f"V3.6 source_ohlcv_sha256 mismatch for {timeframe}")
    if "feature_run_id" in frame.columns and feature_run_id is not None:
        if set(frame["feature_run_id"].astype(str).unique()) != {str(feature_run_id)}:
            errors.append(f"V3.6 feature_run_id mismatch for {timeframe}")
    if "feature_schema_version" in frame.columns:
        if set(frame["feature_schema_version"].astype(str).unique()) != {FEATURE_SCHEMA_VERSION_V3_6}:
            errors.append(f"V3.6 feature_schema_version mismatch for {timeframe}")
    if {"event_ts", "close_ts", "available_ts", "decision_ts"}.issubset(frame.columns) and {
        "event_ts",
        "close_ts",
        "available_ts",
        "decision_ts",
    }.issubset(input_frame.columns):
        key_columns = ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "available_ts", "decision_ts"]
        try:
            pd.testing.assert_frame_equal(
                frame[key_columns].reset_index(drop=True),
                input_frame[key_columns].reset_index(drop=True),
                check_dtype=False,
            )
        except AssertionError:
            errors.append(f"V3.6 feature metadata mismatch with input OHLCV for {timeframe}")
    if {"feature_available_ts", "available_ts"}.issubset(frame.columns):
        feature_available = pd.to_datetime(frame["feature_available_ts"], utc=True)
        available = pd.to_datetime(frame["available_ts"], utc=True)
        if not bool((feature_available == available).all()):
            errors.append(f"V3.6 feature_available_ts must equal available_ts for {timeframe}")

    quality = assess_expanded_feature_quality(frame, timeframe)
    quality["source_hashes_valid"] = source_hashes_valid
    errors.extend(f"V3.6 physical quality error for {timeframe}: {error}" for error in quality["errors"])
    return errors, quality


def _forbidden_columns(frame: pd.DataFrame) -> list[str]:
    forbidden: list[str] = []
    for column in frame.columns:
        if column in FEATURE_COLUMNS_V3_6:
            continue
        lower = str(column).casefold()
        if any(term in lower for term in FORBIDDEN_TERMS):
            forbidden.append(str(column))
    return sorted(forbidden)


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V3_6:
        declared = manifest.get("quality", {}).get(timeframe)
        physical = physical_quality.get(timeframe)
        if not isinstance(declared, dict):
            errors.append(f"V3.6 manifest quality missing for {timeframe}")
            continue
        if not isinstance(physical, dict):
            errors.append(f"V3.6 physical quality unavailable for {timeframe}")
            continue
        for field in sorted(QUALITY_KEYS - {"warnings", "errors"}):
            if declared.get(field) != physical.get(field):
                errors.append(f"V3.6 manifest quality mismatch for {timeframe}.{field}")
        if declared.get("errors") != physical.get("errors"):
            errors.append(f"V3.6 manifest quality errors mismatch for {timeframe}")
        if declared.get("warnings") != physical.get("warnings"):
            errors.append(f"V3.6 manifest quality warnings mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(report, REPORT_KEYS, "V3.6 feature report"))
    expected = {key: manifest.get(key) for key in REPORT_KEYS}
    for field, value in expected.items():
        if report.get(field) != value:
            errors.append(f"V3.6 feature report {field} mismatch")
    errors.extend(_validate_safety(report.get("safety", {})))
    return errors


def _validate_markdown(root: Path) -> list[str]:
    path = root / REPORT_MD_PATH_V3_6
    if not path.exists():
        return [f"missing V3.6 feature markdown: {REPORT_MD_PATH_V3_6}"]
    text = path.read_text(encoding="utf-8")
    errors = validate_markdown_forbidden_claims(text, "V3.6 feature markdown")
    required = [
        "V3.6 ne valide aucune stratégie",
        "V3.6 ne produit aucun label",
        "V3.6 ne produit aucun dataset ML",
        "V3.6 ne produit aucun modèle ML",
        "V3.6 ne produit aucun backtest",
        "V3.6 ne produit aucun signal de trading",
        "V3.6 ne produit aucun ordre",
        "V3.6 n’autorise aucun paper live",
        "V3.6 n’autorise aucun trading réel",
    ]
    normalized_text = text.replace("’", "'")
    for clause in required:
        if clause.replace("’", "'") not in normalized_text:
            errors.append(f"V3.6 feature markdown missing safety clause: {clause}")
    return errors


def _find_forbidden_v3_6_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V3_6_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V3.6 artifact detected: {relative}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V3.6 artifact detected: {child.relative_to(root).as_posix()}")
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V3.6 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _result(errors: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V3_6, "passed": not errors, "errors": errors, "manifest": manifest}
