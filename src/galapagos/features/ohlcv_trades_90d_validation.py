from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.ohlcv_trades_90d import (
    EXPECTED_LIMITATIONS_V7_8,
    EXPECTED_ROWS_V7_8,
    FEATURE_SCHEMA_VERSION_V7_8,
    MANIFEST_PATH_V7_8,
    REPORT_JSON_PATH_V7_8,
    REPORT_MD_PATH_V7_8,
    DOC_PATH_V7_8,
    TIMEFRAMES_V7_8,
    TOTAL_DAYS_V7_8,
    V7_7_TRADES_MANIFEST_PATH,
    VERSION_V7_8,
    WINDOW_END_V7_8,
    WINDOW_START_V7_8,
    filter_ohlcv_to_v7_8_window,
    input_ohlcv_path,
    load_v5_0_ohlcv_manifest,
    load_v7_7_trades_manifest,
    output_path,
)
from galapagos.features.ohlcv_trades_90d_quality import (
    assess_ohlcv_trades_feature_quality_v7_8,
    forbidden_columns_present_v7_8,
)
from galapagos.features.ohlcv_trades_90d_schemas import (
    FORBIDDEN_OHLCV_TRADES_FEATURE_COLUMNS_V7_8,
    OHLCV_TRADES_FEATURE_COLUMNS_V7_8,
)


REQUIRED_MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "feature_run_id",
    "input_ohlcv_manifest",
    "input_trades_manifest",
    "window",
    "input_ohlcv",
    "input_trades",
    "outputs",
    "feature_schema_version",
    "feature_columns",
    "quality",
    "safety",
    "limitations",
}
REQUIRED_OHLCV_MANIFEST_KEYS = {"path", "sha256", "source_window_start", "source_window_end"}
REQUIRED_TRADES_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days", "trade_source_type"}
REQUIRED_WINDOW_KEYS = {"window_start", "window_end", "total_days", "bucket_convention"}
REQUIRED_INPUT_OHLCV_KEYS = {"path", "sha256", "rows"}
REQUIRED_INPUT_TRADES_KEYS = {"path_or_partitions", "rows", "sha256_or_partition_hashes"}
REQUIRED_OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
REQUIRED_SAFETY_KEYS = {
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
FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "validated trading strategy",
]
FORBIDDEN_V7_8_ARTIFACT_PATHS = [
    Path("data/research/v7_8/labels"),
    Path("data/research/v7_8/datasets"),
    Path("data/research/v7_8/ml"),
    Path("data/research/v7_8/backtests"),
    Path("data/research/v7_8/strategies"),
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
]


def validate_ohlcv_trades_90d_feature_store_v7_8(root: Path = Path(".")) -> dict[str, Any]:
    project_root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V7_8
    report_path = project_root / REPORT_JSON_PATH_V7_8
    if not manifest_path.exists():
        return _result([f"missing V7.8 manifest: {MANIFEST_PATH_V7_8}"], warnings)
    if not report_path.exists():
        errors.append(f"missing V7.8 report JSON: {REPORT_JSON_PATH_V7_8}")
    manifest = _read_json(manifest_path)
    report = _read_json(report_path) if report_path.exists() else {}
    v5_manifest = load_v5_0_ohlcv_manifest(project_root)
    trades_manifest = load_v7_7_trades_manifest(project_root)

    errors.extend(_validate_manifest_structure(project_root, manifest, v5_manifest, trades_manifest))
    errors.extend(_validate_report(manifest, report))
    errors.extend(_validate_physical_files(project_root, manifest, v5_manifest, trades_manifest))
    errors.extend(_validate_markdown(project_root))
    errors.extend(_find_forbidden_v7_8_artifacts(project_root))
    return _result(errors, warnings, manifest)


def _validate_manifest_structure(
    root: Path,
    manifest: dict[str, Any],
    v5_manifest: dict[str, Any],
    trades_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_exact_keys(manifest, REQUIRED_MANIFEST_KEYS, "V7.8 manifest"))
    if manifest.get("version") != VERSION_V7_8:
        errors.append("V7.8 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V7.8 manifest status must be PASS")
    if manifest.get("feature_schema_version") != FEATURE_SCHEMA_VERSION_V7_8:
        errors.append("V7.8 feature_schema_version mismatch")
    if manifest.get("feature_columns") != OHLCV_TRADES_FEATURE_COLUMNS_V7_8:
        errors.append("V7.8 feature_columns must match OHLCV_TRADES_FEATURE_COLUMNS_V7_8")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V7_8:
        errors.append("V7.8 limitations mismatch")

    input_ohlcv_manifest = manifest.get("input_ohlcv_manifest", {})
    errors.extend(_validate_exact_keys(input_ohlcv_manifest, REQUIRED_OHLCV_MANIFEST_KEYS, "V7.8 input_ohlcv_manifest"))
    if input_ohlcv_manifest.get("path") != "reports/manifests/max_history_public_market_data_v5_0_manifest.json":
        errors.append("V7.8 input_ohlcv_manifest path mismatch")
    expected_v5_sha = sha256_file(root / "reports/manifests/max_history_public_market_data_v5_0_manifest.json")
    if input_ohlcv_manifest.get("sha256") != expected_v5_sha:
        errors.append("V7.8 input_ohlcv_manifest sha256 mismatch")
    if input_ohlcv_manifest.get("source_window_start") != v5_manifest.get("discovery", {}).get("window_start"):
        errors.append("V7.8 input_ohlcv_manifest source_window_start mismatch")
    if input_ohlcv_manifest.get("source_window_end") != v5_manifest.get("discovery", {}).get("window_end"):
        errors.append("V7.8 input_ohlcv_manifest source_window_end mismatch")

    input_trades_manifest = manifest.get("input_trades_manifest", {})
    errors.extend(_validate_exact_keys(input_trades_manifest, REQUIRED_TRADES_MANIFEST_KEYS, "V7.8 input_trades_manifest"))
    if input_trades_manifest.get("path") != V7_7_TRADES_MANIFEST_PATH.as_posix():
        errors.append("V7.8 input_trades_manifest path mismatch")
    expected_trades_sha = sha256_file(root / V7_7_TRADES_MANIFEST_PATH)
    if input_trades_manifest.get("sha256") != expected_trades_sha:
        errors.append("V7.8 input_trades_manifest sha256 mismatch")
    if input_trades_manifest.get("window_start") != trades_manifest["discovery"]["window_start"]:
        errors.append("V7.8 input_trades_manifest window_start mismatch")
    if input_trades_manifest.get("window_end") != trades_manifest["discovery"]["window_end"]:
        errors.append("V7.8 input_trades_manifest window_end mismatch")
    if input_trades_manifest.get("total_days") != trades_manifest["discovery"]["total_days"]:
        errors.append("V7.8 input_trades_manifest total_days mismatch")
    if input_trades_manifest.get("trade_source_type") != "aggTrades":
        errors.append("V7.8 trade_source_type must be aggTrades")

    window = manifest.get("window", {})
    errors.extend(_validate_exact_keys(window, REQUIRED_WINDOW_KEYS, "V7.8 window"))
    if window.get("window_start") != WINDOW_START_V7_8:
        errors.append("V7.8 window_start must be 2023-03-25")
    if window.get("window_end") != WINDOW_END_V7_8:
        errors.append("V7.8 window_end must be 2023-06-22")
    if window.get("total_days") != TOTAL_DAYS_V7_8:
        errors.append("V7.8 total_days must be 90")

    for timeframe in TIMEFRAMES_V7_8:
        errors.extend(_validate_exact_keys(manifest.get("input_ohlcv", {}).get(timeframe, {}), REQUIRED_INPUT_OHLCV_KEYS, f"V7.8 input_ohlcv {timeframe}"))
        errors.extend(_validate_exact_keys(manifest.get("outputs", {}).get(timeframe, {}), REQUIRED_OUTPUT_KEYS, f"V7.8 output {timeframe}"))
    errors.extend(_validate_exact_keys(manifest.get("input_trades", {}), REQUIRED_INPUT_TRADES_KEYS, "V7.8 input_trades"))
    errors.extend(_validate_safety(manifest))
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report != manifest:
        errors.append("V7.8 report JSON must be a deterministic projection of the manifest")
    errors.extend(_validate_exact_keys(report, REQUIRED_MANIFEST_KEYS, "V7.8 report JSON"))
    return errors


def _validate_physical_files(
    root: Path,
    manifest: dict[str, Any],
    v5_manifest: dict[str, Any],
    trades_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    trades_manifest_sha = sha256_file(root / V7_7_TRADES_MANIFEST_PATH)
    for date_key, payload in trades_manifest.get("outputs", {}).get("partitions", {}).items():
        path = root / payload.get("path", "")
        if not path.exists():
            errors.append(f"missing V7.8 input trades partition for {date_key}: {payload.get('path')}")
            continue
        if sha256_file(path) != payload.get("sha256"):
            errors.append(f"V7.8 input trades partition checksum mismatch for {date_key}")

    for timeframe in TIMEFRAMES_V7_8:
        input_path = input_ohlcv_path(root, timeframe, v5_manifest)
        if not input_path.exists():
            errors.append(f"missing V7.8 input OHLCV for {timeframe}: {input_path}")
            continue
        input_sha = sha256_file(input_path)
        if manifest.get("input_ohlcv", {}).get(timeframe, {}).get("sha256") != input_sha:
            errors.append(f"V7.8 input OHLCV sha256 mismatch for {timeframe}")
        input_window = filter_ohlcv_to_v7_8_window(read_parquet(input_path))
        if len(input_window) != EXPECTED_ROWS_V7_8[timeframe]:
            errors.append(f"V7.8 input OHLCV window rows mismatch for {timeframe}")
        if manifest.get("input_ohlcv", {}).get(timeframe, {}).get("rows") != len(input_window):
            errors.append(f"V7.8 manifest input_ohlcv rows mismatch for {timeframe}")

        output = output_path(root, timeframe, WINDOW_START_V7_8, WINDOW_END_V7_8)
        output_manifest = manifest.get("outputs", {}).get(timeframe, {})
        if not output.exists():
            errors.append(f"missing V7.8 output features for {timeframe}: {output}")
            continue
        if output_manifest.get("path") != output.relative_to(root).as_posix():
            errors.append(f"V7.8 output path mismatch for {timeframe}")
        actual_sha = sha256_file(output)
        if actual_sha != output_manifest.get("sha256"):
            errors.append(f"V7.8 output sha256 mismatch for {timeframe}")
        if output.stat().st_size != int(output_manifest.get("bytes", -1)):
            errors.append(f"V7.8 output byte size mismatch for {timeframe}")
        frame = read_parquet(output)
        frame_errors, quality = validate_ohlcv_trades_feature_frame_v7_8(
            frame,
            timeframe,
            expected_rows=EXPECTED_ROWS_V7_8[timeframe],
            expected_source_ohlcv_sha256=input_sha,
            expected_source_trades_manifest_sha256=trades_manifest_sha,
            expected_feature_run_id=manifest.get("feature_run_id", ""),
        )
        errors.extend(frame_errors)
        if quality != manifest.get("quality", {}).get(timeframe):
            errors.append(f"V7.8 manifest quality does not match physical output for {timeframe}")
    return errors


def validate_ohlcv_trades_feature_frame_v7_8(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    expected_rows: int,
    expected_source_ohlcv_sha256: str,
    expected_source_trades_manifest_sha256: str,
    expected_feature_run_id: str,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    quality = assess_ohlcv_trades_feature_quality_v7_8(frame, timeframe, expected_rows=expected_rows)
    quality["source_hashes_valid"] = False
    errors.extend(quality["errors"])
    if list(frame.columns) != OHLCV_TRADES_FEATURE_COLUMNS_V7_8:
        errors.append(f"{timeframe} V7.8 strict column order mismatch")
        return errors, quality
    if len(frame) != expected_rows:
        errors.append(f"{timeframe} V7.8 row count mismatch")
    if forbidden_columns_present_v7_8(frame):
        errors.append(f"{timeframe} V7.8 forbidden columns detected")
    if set(frame["source_ohlcv_sha256"].astype(str).unique()) != {expected_source_ohlcv_sha256}:
        errors.append(f"{timeframe} V7.8 source_ohlcv_sha256 mismatch")
    if set(frame["source_trades_manifest_sha256"].astype(str).unique()) != {expected_source_trades_manifest_sha256}:
        errors.append(f"{timeframe} V7.8 source_trades_manifest_sha256 mismatch")
    if set(frame["feature_run_id"].astype(str).unique()) != {expected_feature_run_id}:
        errors.append(f"{timeframe} V7.8 feature_run_id mismatch")
    if set(frame["feature_schema_version"].astype(str).unique()) != {FEATURE_SCHEMA_VERSION_V7_8}:
        errors.append(f"{timeframe} V7.8 feature_schema_version mismatch")
    if set(frame["trade_source_type"].astype(str).unique()) != {"aggTrades"}:
        errors.append(f"{timeframe} V7.8 trade_source_type mismatch")
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    feature_available_ts = pd.to_datetime(frame["feature_available_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    if not bool((feature_available_ts >= available_ts).all()):
        errors.append(f"{timeframe} V7.8 feature_available_ts before available_ts")
    if not bool((decision_ts >= feature_available_ts).all()):
        errors.append(f"{timeframe} V7.8 decision_ts before feature_available_ts")
    expected_warmup = frame["trades_feature_null_count"] > 0
    if len(expected_warmup) >= 60:
        expected_warmup.iloc[:60] = True
    if not bool((frame["warmup_row"].astype(bool) == expected_warmup).all()):
        errors.append(f"{timeframe} V7.8 warmup rows are not coherent with null counts")
    expected_null_counts = frame[
        [column for column in OHLCV_TRADES_FEATURE_COLUMNS_V7_8[15:] if column not in {"trades_feature_null_count", "trades_feature_error_count"}]
    ].isna().sum(axis=1)
    if not bool((frame["trades_feature_null_count"].astype("int64") == expected_null_counts.astype("int64")).all()):
        errors.append(f"{timeframe} V7.8 trades_feature_null_count mismatch")
    quality["source_hashes_valid"] = not any("source_" in error for error in errors)
    return errors, quality


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for path, label in [(root / REPORT_MD_PATH_V7_8, "V7.8 Markdown report"), (root / DOC_PATH_V7_8, "V7.8 documentation")]:
        if not path.exists():
            errors.append(f"missing {label}: {path}")
            continue
        text = path.read_text(encoding="utf-8").casefold()
        for claim in FORBIDDEN_CLAIMS:
            if claim in text:
                errors.append(f"{label} contains forbidden claim: {claim}")
    return errors


def _validate_safety(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    safety = manifest.get("safety", {})
    errors.extend(_validate_exact_keys(safety, REQUIRED_SAFETY_KEYS, "V7.8 safety"))
    if safety.get("public_read_only") is not True:
        errors.append("V7.8 public_read_only safety flag must be true")
    for key in REQUIRED_SAFETY_KEYS - {"public_read_only"}:
        if safety.get(key) is not False:
            errors.append(f"V7.8 safety flag must be false: {key}")
    return errors


def _find_forbidden_v7_8_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V7_8_ARTIFACT_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V7.8 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V7.8 artifact detected: {child.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _validate_exact_keys(payload: Any, expected: set[str], label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    actual = set(payload)
    errors: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"{label} missing keys: {missing}")
    if unexpected:
        errors.append(f"{label} unexpected keys: {unexpected}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
