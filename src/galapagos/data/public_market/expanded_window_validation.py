from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.expanded_window import (
    DATES_V3_5,
    EXPECTED_LIMITATIONS_V3_5,
    MANIFEST_PATH_V3_5,
    REPORT_JSON_PATH_V3_5,
    REPORT_MD_PATH_V3_5,
    TIMEFRAMES_V3_5,
    VERSION_V3_5,
    output_path,
    raw_zip_path,
)
from galapagos.data.public_market.expanded_window_quality import (
    EXPECTED_ROWS_V3_5,
    FORBIDDEN_OHLCV_COLUMNS_V3_5,
    assess_expanded_timeframe,
    parent_child_consistent,
)
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import parse_binance_kline_zip
from galapagos.data.public_market.storage import read_parquet
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


RUN_ID_PATTERN_V3_5 = re.compile(r"^v3_5_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "run_id",
    "source",
    "raw_files",
    "outputs",
    "expected_rows",
    "quality",
    "safety",
    "limitations",
}
SOURCE_KEYS = {"name", "venue", "market_type", "symbol", "source_timeframe", "window_start", "window_end"}
RAW_FILE_KEYS = {"path", "sha256", "bytes", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
QUALITY_KEYS = {
    "rows",
    "expected_rows",
    "duplicate_rows",
    "gap_count",
    "gaps",
    "ohlc_violations",
    "negative_volume_rows",
    "null_critical_rows",
    "min_event_ts",
    "max_event_ts",
    "min_close_ts",
    "max_close_ts",
    "monotonic_event_ts",
    "timestamp_order_valid",
    "timestamps_utc",
    "parent_child_consistency",
    "forbidden_columns_present",
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
FORBIDDEN_V3_5_PATHS = [
    "data/research/v3_5/features",
    "data/research/v3_5/labels",
    "data/research/v3_5/datasets",
    "data/research/v3_5/ml",
    "data/research/v3_5/backtests",
    "data/research/v3_5/strategies",
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


def validate_expanded_public_market_data_v3_5(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH_V3_5
    report_path = root / REPORT_JSON_PATH_V3_5
    if not manifest_path.exists():
        return _result([f"missing manifest: {MANIFEST_PATH_V3_5}"])
    if not report_path.exists():
        return _result([f"missing quality report: {REPORT_JSON_PATH_V3_5}"])
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V3.5 manifest"))
    frames: dict[str, pd.DataFrame] = {}
    raw_errors, raw_rows = _validate_raw_files(root, manifest)
    errors.extend(raw_errors)
    for timeframe in TIMEFRAMES_V3_5:
        path = output_path(root, timeframe)
        if not path.exists():
            errors.append(f"missing V3.5 output parquet: {path.relative_to(root)}")
            continue
        frame = read_parquet(path)
        frames[timeframe] = frame
        errors.extend(_validate_output_entry(root, manifest, timeframe, path, frame))
        errors.extend(_validate_ohlcv_frame(timeframe, frame))
    if "1m" in frames:
        errors.extend(_validate_raw_to_1m(manifest, frames["1m"], raw_rows))
    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe, frame in frames.items():
        consistency = True if timeframe == "1m" else ("1m" in frames and parent_child_consistent(frames["1m"], frame, timeframe))
        if timeframe != "1m" and not consistency:
            errors.append(f"V3.5 parent-child consistency mismatch for {timeframe}")
        physical_quality[timeframe] = assess_expanded_timeframe(
            frame,
            timeframe=timeframe,
            parent_child_consistency=consistency,
        )
    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V3.5 quality report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v3_5_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V3.5 manifest"))
    if manifest.get("version") != VERSION_V3_5:
        errors.append("V3.5 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.5 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V3.5 manifest created_at_utc invalid")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN_V3_5.fullmatch(run_id) is None:
        errors.append("V3.5 manifest run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("source"), SOURCE_KEYS, "V3.5 manifest source"))
    source = manifest.get("source", {})
    expected_source = {
        "name": "binance_public_archive",
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "source_timeframe": "1m",
        "window_start": "2024-01-01",
        "window_end": "2024-03-30",
    }
    if source != expected_source:
        errors.append("V3.5 manifest source mismatch")
    if set(manifest.get("raw_files", {})) != set(DATES_V3_5):
        errors.append("V3.5 manifest raw_files dates mismatch")
    for current_date, payload in manifest.get("raw_files", {}).items():
        errors.extend(validate_exact_keys(payload, RAW_FILE_KEYS, f"V3.5 manifest raw_files.{current_date}"))
    if set(manifest.get("outputs", {})) != set(TIMEFRAMES_V3_5):
        errors.append("V3.5 manifest outputs mismatch")
    for timeframe, payload in manifest.get("outputs", {}).items():
        errors.extend(validate_exact_keys(payload, OUTPUT_KEYS, f"V3.5 manifest outputs.{timeframe}"))
    if manifest.get("expected_rows") != EXPECTED_ROWS_V3_5:
        errors.append("V3.5 manifest expected_rows mismatch")
    if set(manifest.get("quality", {})) != set(TIMEFRAMES_V3_5):
        errors.append("V3.5 manifest quality timeframes mismatch")
    for timeframe, payload in manifest.get("quality", {}).items():
        errors.extend(validate_exact_keys(payload, QUALITY_KEYS, f"V3.5 manifest quality.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V3.5 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V3_5:
        errors.append("V3.5 limitations mismatch")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V3.5 safety flag public_read_only must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only"}):
        if safety.get(flag) is not False:
            errors.append(f"V3.5 safety flag {flag} must be False")
    return errors


def _validate_raw_files(root: Path, manifest: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    raw_rows: dict[str, int] = {}
    for current_date in DATES_V3_5:
        path = raw_zip_path(root, current_date)
        if not path.exists():
            errors.append(f"missing raw zip: {path.relative_to(root)}")
            continue
        raw_sha = sha256_file(path)
        raw_payload = manifest.get("raw_files", {}).get(current_date, {})
        if raw_payload.get("path") != str(path.relative_to(root)):
            errors.append(f"V3.5 raw path mismatch for {current_date}")
        if raw_payload.get("sha256") != raw_sha:
            errors.append(f"V3.5 raw checksum mismatch for {current_date}")
        if raw_payload.get("bytes") != path.stat().st_size:
            errors.append(f"V3.5 raw bytes mismatch for {current_date}")
        try:
            raw_rows[current_date] = int(len(parse_binance_kline_zip(path)))
        except Exception as exc:
            errors.append(f"V3.5 raw parse failed for {current_date}: {exc}")
            raw_rows[current_date] = -1
        if raw_payload.get("rows") != raw_rows[current_date]:
            errors.append(f"V3.5 raw rows mismatch for {current_date}")
        if raw_rows[current_date] != 1440:
            errors.append(f"V3.5 raw daily rows mismatch for {current_date}")
    return errors, raw_rows


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
            errors.append(f"V3.5 manifest output mismatch for {timeframe}.{field}")
    return errors


def _validate_ohlcv_frame(timeframe: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != OHLCV_COLUMNS:
        errors.append(f"V3.5 OHLCV schema mismatch for {timeframe}")
    forbidden_columns = sorted(column for column in frame.columns if str(column).casefold() in FORBIDDEN_OHLCV_COLUMNS_V3_5)
    if forbidden_columns:
        errors.append(f"V3.5 forbidden OHLCV columns for {timeframe}: {forbidden_columns}")
    quality = assess_expanded_timeframe(frame, timeframe=timeframe, parent_child_consistency=True)
    for error in quality["errors"]:
        errors.append(f"V3.5 physical quality error for {timeframe}: {error}")
    return errors


def _validate_raw_to_1m(manifest: dict[str, Any], frame_1m: pd.DataFrame, raw_rows: dict[str, int]) -> list[str]:
    errors: list[str] = []
    frame = frame_1m.copy()
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    for current_date in DATES_V3_5:
        day_rows = frame[frame["event_ts"].dt.strftime("%Y-%m-%d") == current_date]
        if len(day_rows) != raw_rows.get(current_date):
            errors.append(f"V3.5 raw-to-1m row mismatch for {current_date}")
        expected_sha = manifest.get("raw_files", {}).get(current_date, {}).get("sha256")
        if set(day_rows["raw_file_sha256"].astype(str).unique()) != {expected_sha}:
            errors.append(f"V3.5 raw-to-1m checksum mismatch for {current_date}")
    return errors


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, expected in physical_quality.items():
        observed = manifest.get("quality", {}).get(timeframe)
        if observed != expected:
            errors.append(f"V3.5 manifest quality mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    if report != manifest:
        return ["V3.5 quality report mismatch"]
    return []


def _validate_markdown(root: Path) -> list[str]:
    path = root / REPORT_MD_PATH_V3_5
    if not path.exists():
        return [f"missing markdown report: {REPORT_MD_PATH_V3_5}"]
    return validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), "V3.5 Markdown report")


def _find_forbidden_v3_5_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V3_5_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V3.5 artifact detected: {relative}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V3.5 artifact detected: {child.relative_to(root).as_posix()}")
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V3.5 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _assert_parent_child_equal(frame_1m: pd.DataFrame, child: pd.DataFrame, timeframe: str) -> None:
    if not parent_child_consistent(frame_1m, child, timeframe):
        raise AssertionError(f"V3.5 parent-child consistency mismatch for {timeframe}")


def _assert_frame_values_equal(left: pd.DataFrame, right: pd.DataFrame, columns: list[str]) -> None:
    pdt.assert_frame_equal(left[columns].reset_index(drop=True), right[columns].reset_index(drop=True), check_dtype=False)


def _result(errors: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V3_5, "passed": not errors, "errors": errors, "manifest": manifest}
