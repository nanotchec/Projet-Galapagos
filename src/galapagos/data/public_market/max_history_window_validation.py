from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.max_history_discovery import (
    DISCOVERY_JSON_PATH_V5_0,
    DISCOVERY_MD_PATH_V5_0,
    VERSION_V5_0,
    build_raw_file_inventory_entry_v5_0,
    count_binance_kline_zip_rows_fast_v5_0,
    dates_from_discovery_v5_0,
    expected_rows_from_days_v5_0,
    raw_zip_path_v5_0,
)
from galapagos.data.public_market.max_history_window import (
    EXPECTED_LIMITATIONS_V5_0,
    MANIFEST_PATH_V5_0,
    REPORT_JSON_PATH_V5_0,
    REPORT_MD_PATH_V5_0,
    output_path,
)
from galapagos.data.public_market.max_history_window_quality import (
    FORBIDDEN_OHLCV_COLUMNS_V5_0,
    TIMEFRAMES_V5_0,
    assess_max_history_timeframe,
    parent_child_consistent,
    resample_max_history_ohlcv,
)
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import read_parquet
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


RUN_ID_PATTERN_V5_0 = re.compile(r"^v5_0_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "run_id",
    "discovery",
    "source",
    "raw_files",
    "outputs",
    "expected_rows",
    "quality",
    "safety",
    "limitations",
}
DISCOVERY_KEYS = {
    "first_available_date",
    "last_available_date",
    "window_start",
    "window_end",
    "total_days",
    "expected_raw_files",
    "missing_dates",
    "documented_gaps_allowed",
}
SOURCE_KEYS = {"name", "venue", "market_type", "symbol", "source_timeframe"}
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
FORBIDDEN_V5_0_PATHS = [
    "data/research/v5_0/features",
    "data/research/v5_0/labels",
    "data/research/v5_0/datasets",
    "data/research/v5_0/ml",
    "data/research/v5_0/backtests",
    "data/research/v5_0/strategies",
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


def validate_max_history_public_market_data_v5_0(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH_V5_0
    report_path = root / REPORT_JSON_PATH_V5_0
    discovery_path = root / DISCOVERY_JSON_PATH_V5_0
    if not discovery_path.exists():
        return _result([f"missing discovery report: {DISCOVERY_JSON_PATH_V5_0}"])
    if not manifest_path.exists():
        return _result([f"missing manifest: {MANIFEST_PATH_V5_0}"])
    if not report_path.exists():
        return _result([f"missing quality report: {REPORT_JSON_PATH_V5_0}"])

    discovery = load_json(discovery_path)
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(_validate_discovery_report(discovery, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V5.0 manifest"))

    frames: dict[str, pd.DataFrame] = {}
    raw_errors, raw_rows = _validate_raw_files(root, manifest)
    errors.extend(raw_errors)
    for timeframe in TIMEFRAMES_V5_0:
        path = output_path(root, timeframe, manifest["discovery"]["window_start"], manifest["discovery"]["window_end"])
        if not path.exists():
            errors.append(f"missing V5.0 output parquet: {path.relative_to(root)}")
            continue
        frame = read_parquet(path)
        frames[timeframe] = frame
        errors.extend(_validate_output_entry(root, manifest, timeframe, path, frame))

    if "1m" in frames:
        errors.extend(_validate_raw_to_1m(manifest, frames["1m"], raw_rows))

    expected_children: dict[str, pd.DataFrame] = {}
    if "1m" in frames:
        for timeframe in ["5m", "15m", "1h"]:
            try:
                expected_children[timeframe] = resample_max_history_ohlcv(frames["1m"], target_timeframe=timeframe)
            except ValueError as exc:
                errors.append(f"V5.0 parent-child resample failed for {timeframe}: {exc}")

    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe, frame in frames.items():
        consistency = True if timeframe == "1m" else _child_matches_expected(expected_children.get(timeframe), frame)
        if timeframe != "1m" and not consistency:
            errors.append(f"V5.0 parent-child consistency mismatch for {timeframe}")
        quality = _assess_frame_quality(timeframe, frame, manifest, parent_child_consistency=consistency)
        physical_quality[timeframe] = quality
        for error in quality["errors"]:
            errors.append(f"V5.0 physical quality error for {timeframe}: {error}")

    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V5.0 quality report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v5_0_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V5.0 manifest"))
    if manifest.get("version") != VERSION_V5_0:
        errors.append("V5.0 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V5.0 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V5.0 manifest created_at_utc invalid")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN_V5_0.fullmatch(run_id) is None:
        errors.append("V5.0 manifest run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("discovery"), DISCOVERY_KEYS, "V5.0 manifest discovery"))
    discovery = manifest.get("discovery", {})
    dates = dates_from_discovery_v5_0(discovery) if discovery.get("window_start") and discovery.get("window_end") else []
    if discovery.get("total_days") != len(dates):
        errors.append("V5.0 discovery total_days mismatch")
    if discovery.get("expected_raw_files") != len(dates):
        errors.append("V5.0 discovery expected_raw_files mismatch")
    if discovery.get("missing_dates") and discovery.get("documented_gaps_allowed") is not True:
        errors.append("V5.0 missing dates require documented_gaps_allowed true")
    errors.extend(validate_exact_keys(manifest.get("source"), SOURCE_KEYS, "V5.0 manifest source"))
    expected_source = {
        "name": "binance_public_archive",
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "source_timeframe": "1m",
    }
    if manifest.get("source") != expected_source:
        errors.append("V5.0 manifest source mismatch")
    if set(manifest.get("raw_files", {})) != set(dates):
        errors.append("V5.0 manifest raw_files dates mismatch")
    for current_date, payload in manifest.get("raw_files", {}).items():
        errors.extend(validate_exact_keys(payload, RAW_FILE_KEYS, f"V5.0 manifest raw_files.{current_date}"))
    if set(manifest.get("outputs", {})) != set(TIMEFRAMES_V5_0):
        errors.append("V5.0 manifest outputs mismatch")
    for timeframe, payload in manifest.get("outputs", {}).items():
        errors.extend(validate_exact_keys(payload, OUTPUT_KEYS, f"V5.0 manifest outputs.{timeframe}"))
    expected_rows = expected_rows_from_days_v5_0(len(dates))
    if manifest.get("expected_rows") != expected_rows:
        errors.append("V5.0 manifest expected_rows mismatch")
    if set(manifest.get("quality", {})) != set(TIMEFRAMES_V5_0):
        errors.append("V5.0 manifest quality timeframes mismatch")
    for timeframe, payload in manifest.get("quality", {}).items():
        errors.extend(validate_exact_keys(payload, QUALITY_KEYS, f"V5.0 manifest quality.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V5.0 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V5_0:
        errors.append("V5.0 limitations mismatch")
    return errors


def _validate_discovery_report(discovery: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if discovery.get("version") != VERSION_V5_0:
        errors.append("V5.0 discovery report version mismatch")
    if discovery.get("status") != "PASS":
        errors.append("V5.0 discovery report status must be PASS")
    for key in DISCOVERY_KEYS:
        if discovery.get(key) != manifest.get("discovery", {}).get(key):
            errors.append(f"V5.0 discovery report mismatch for {key}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V5.0 safety flag public_read_only must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only"}):
        if safety.get(flag) is not False:
            errors.append(f"V5.0 safety flag {flag} must be False")
    return errors


def _validate_raw_files(root: Path, manifest: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    raw_rows: dict[str, int] = {}
    for current_date in dates_from_discovery_v5_0(manifest["discovery"]):
        path = raw_zip_path_v5_0(root, current_date)
        if not path.exists():
            errors.append(f"missing raw zip: {path.relative_to(root)}")
            continue
        payload = manifest.get("raw_files", {}).get(current_date, {})
        expected = build_raw_file_inventory_entry_v5_0(root, current_date)
        raw_rows[current_date] = expected["rows"]
        for field, value in expected.items():
            if payload.get(field) != value:
                errors.append(f"V5.0 raw {field} mismatch for {current_date}")
        if raw_rows[current_date] != 1440:
            errors.append(f"V5.0 raw daily rows mismatch for {current_date}")
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
            errors.append(f"V5.0 manifest output mismatch for {timeframe}.{field}")
    return errors


def _validate_ohlcv_frame(timeframe: str, frame: pd.DataFrame, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    quality = _assess_frame_quality(timeframe, frame, manifest, parent_child_consistency=True)
    if list(frame.columns) != OHLCV_COLUMNS:
        errors.append(f"V5.0 OHLCV schema mismatch for {timeframe}")
    forbidden_columns = sorted(column for column in frame.columns if str(column).casefold() in FORBIDDEN_OHLCV_COLUMNS_V5_0)
    if forbidden_columns:
        errors.append(f"V5.0 forbidden OHLCV columns for {timeframe}: {forbidden_columns}")
    for error in quality["errors"]:
        errors.append(f"V5.0 physical quality error for {timeframe}: {error}")
    return errors


def _validate_raw_to_1m(manifest: dict[str, Any], frame_1m: pd.DataFrame, raw_rows: dict[str, int]) -> list[str]:
    errors: list[str] = []
    frame = frame_1m[["event_ts", "raw_file_sha256"]].copy()
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    frame["_date"] = event_ts.dt.date.astype(str)
    rows_by_date = frame.groupby("_date", sort=True).size().to_dict()
    sha_by_date = (
        frame.groupby("_date", sort=True)["raw_file_sha256"]
        .agg(lambda values: set(values.astype(str).unique()))
        .to_dict()
    )
    expected_dates = set(dates_from_discovery_v5_0(manifest["discovery"]))
    for observed_date in sorted(set(rows_by_date) - expected_dates):
        errors.append(f"V5.0 raw-to-1m unexpected date: {observed_date}")
    for current_date in sorted(expected_dates):
        observed_rows = int(rows_by_date.get(current_date, 0))
        if observed_rows != raw_rows.get(current_date):
            errors.append(f"V5.0 raw-to-1m row mismatch for {current_date}")
        expected_sha = manifest.get("raw_files", {}).get(current_date, {}).get("sha256")
        observed_sha_set = sha_by_date.get(current_date, set())
        if observed_sha_set != {expected_sha}:
            errors.append(f"V5.0 raw-to-1m checksum mismatch for {current_date}")
    return errors


def _assess_frame_quality(
    timeframe: str,
    frame: pd.DataFrame,
    manifest: dict[str, Any],
    *,
    parent_child_consistency: bool,
) -> dict[str, Any]:
    return assess_max_history_timeframe(
        frame,
        timeframe=timeframe,
        expected_rows=int(manifest["expected_rows"][timeframe]),
        window_start=manifest["discovery"]["window_start"],
        window_end=manifest["discovery"]["window_end"],
        parent_child_consistency=parent_child_consistency,
    )


def _child_matches_expected(expected: pd.DataFrame | None, child: pd.DataFrame) -> bool:
    if expected is None or list(expected.columns) != list(child.columns):
        return False
    comparable_columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "available_ts",
        "decision_ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "source_open_time_raw",
        "source_close_time_raw",
        "source_timestamp_unit",
        "ingestion_run_id",
    ]
    try:
        pdt.assert_frame_equal(
            expected[comparable_columns].reset_index(drop=True),
            child[comparable_columns].reset_index(drop=True),
            check_dtype=False,
            atol=1e-10,
            rtol=1e-10,
        )
    except AssertionError:
        return False
    return True


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, expected in physical_quality.items():
        observed = manifest.get("quality", {}).get(timeframe)
        if observed != expected:
            errors.append(f"V5.0 manifest quality mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    if report != manifest:
        return ["V5.0 quality report mismatch"]
    return []


def _validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in [REPORT_MD_PATH_V5_0, DISCOVERY_MD_PATH_V5_0]:
        path = root / relative
        if not path.exists():
            errors.append(f"missing markdown report: {relative}")
            continue
        errors.extend(validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), f"V5.0 Markdown report {relative}"))
    return errors


def _find_forbidden_v5_0_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V5_0_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V5.0 artifact detected: {relative}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V5.0 artifact detected: {child.relative_to(root).as_posix()}")
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V5.0 artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _assert_parent_child_equal(frame_1m: pd.DataFrame, child: pd.DataFrame, timeframe: str) -> None:
    if not parent_child_consistent(frame_1m, child, timeframe):
        raise AssertionError(f"V5.0 parent-child consistency mismatch for {timeframe}")


def _count_binance_kline_zip_rows_fast(path: Path) -> int:
    return count_binance_kline_zip_rows_fast_v5_0(path)


def _result(errors: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V5_0, "passed": not errors, "errors": errors, "manifest": manifest}
