from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.multi_day import (
    DATES_V2_9,
    EXPECTED_LIMITATIONS_V2_9,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    TIMEFRAMES_V2_9,
    VERSION,
    output_path,
    raw_zip_path,
)
from galapagos.data.public_market.multi_day_quality import (
    EXPECTED_ROWS_V2_9,
    FORBIDDEN_OHLCV_COLUMNS_V2_9,
    assess_multi_day_timeframe,
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


RUN_ID_PATTERN = re.compile(r"^v2_9_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
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
FORBIDDEN_V2_9_PATHS = [
    "data/research/v2_9/features",
    "data/research/v2_9/labels",
    "data/research/v2_9/datasets",
    "data/research/v2_9/ml",
    "data/research/v2_9/backtests",
    "reports/strategies",
    "reports/signals",
    "orders",
    "execution",
]


def validate_multi_day_public_market_data_v2_9(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH
    report_path = root / REPORT_JSON_PATH
    if not manifest_path.exists():
        return _result([f"missing manifest: {MANIFEST_PATH}"])
    if not report_path.exists():
        return _result([f"missing quality report: {REPORT_JSON_PATH}"])
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.9 manifest"))
    frames: dict[str, pd.DataFrame] = {}
    raw_rows: dict[str, int] = {}
    for date in DATES_V2_9:
        path = raw_zip_path(root, date)
        if not path.exists():
            errors.append(f"missing raw zip: {path.relative_to(root)}")
            continue
        raw_sha = sha256_file(path)
        raw_payload = manifest.get("raw_files", {}).get(date, {})
        if raw_payload.get("sha256") != raw_sha:
            errors.append(f"V2.9 raw checksum mismatch for {date}")
        try:
            raw_rows[date] = int(len(parse_binance_kline_zip(path)))
        except Exception as exc:
            errors.append(f"V2.9 raw parse failed for {date}: {exc}")
            raw_rows[date] = -1
        if raw_payload.get("rows") != raw_rows[date]:
            errors.append(f"V2.9 raw rows mismatch for {date}")
    for timeframe in TIMEFRAMES_V2_9:
        path = output_path(root, timeframe)
        if not path.exists():
            errors.append(f"missing V2.9 output parquet: {path.relative_to(root)}")
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
            errors.append(f"V2.9 parent-child consistency mismatch for {timeframe}")
        physical_quality[timeframe] = assess_multi_day_timeframe(
            frame,
            timeframe=timeframe,
            parent_child_consistency=consistency,
        )
    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V2.9 quality report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v2_9_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V2.9 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("V2.9 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V2.9 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V2.9 manifest created_at_utc invalid")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        errors.append("V2.9 manifest run_id invalid")
    errors.extend(validate_exact_keys(manifest.get("source"), SOURCE_KEYS, "V2.9 manifest source"))
    if set(manifest.get("raw_files", {})) != set(DATES_V2_9):
        errors.append("V2.9 manifest raw_files dates mismatch")
    for date, payload in manifest.get("raw_files", {}).items():
        errors.extend(validate_exact_keys(payload, RAW_FILE_KEYS, f"V2.9 manifest raw_files.{date}"))
    if set(manifest.get("outputs", {})) != set(TIMEFRAMES_V2_9):
        errors.append("V2.9 manifest outputs mismatch")
    for timeframe, payload in manifest.get("outputs", {}).items():
        errors.extend(validate_exact_keys(payload, OUTPUT_KEYS, f"V2.9 manifest outputs.{timeframe}"))
    if manifest.get("expected_rows") != EXPECTED_ROWS_V2_9:
        errors.append("V2.9 manifest expected_rows mismatch")
    if set(manifest.get("quality", {})) != set(TIMEFRAMES_V2_9):
        errors.append("V2.9 manifest quality timeframes mismatch")
    for timeframe, payload in manifest.get("quality", {}).items():
        errors.extend(validate_exact_keys(payload, QUALITY_KEYS, f"V2.9 manifest quality.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V2.9 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V2_9:
        errors.append("V2.9 manifest limitations mismatch")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V2.9 safety flag public_read_only must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only"}):
        if safety.get(flag) is not False:
            errors.append(f"V2.9 safety flag {flag} must be False")
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
            errors.append(f"V2.9 manifest output mismatch for {timeframe}.{field}")
    return errors


def _validate_ohlcv_frame(timeframe: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != OHLCV_COLUMNS:
        errors.append(f"V2.9 OHLCV schema mismatch for {timeframe}")
    forbidden_columns = sorted(column for column in frame.columns if str(column).casefold() in FORBIDDEN_OHLCV_COLUMNS_V2_9)
    if forbidden_columns:
        errors.append(f"V2.9 forbidden OHLCV columns for {timeframe}: {forbidden_columns}")
    quality = assess_multi_day_timeframe(frame, timeframe=timeframe, parent_child_consistency=True)
    for error in quality["errors"]:
        errors.append(f"V2.9 physical quality error for {timeframe}: {error}")
    return errors


def _validate_raw_to_1m(manifest: dict[str, Any], frame_1m: pd.DataFrame, raw_rows: dict[str, int]) -> list[str]:
    errors: list[str] = []
    frame = frame_1m.copy()
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    for date in DATES_V2_9:
        day_rows = frame[frame["event_ts"].dt.strftime("%Y-%m-%d") == date]
        if len(day_rows) != raw_rows.get(date):
            errors.append(f"V2.9 raw-to-1m row mismatch for {date}")
        expected_sha = manifest.get("raw_files", {}).get(date, {}).get("sha256")
        if set(day_rows["raw_file_sha256"].astype(str).unique()) != {expected_sha}:
            errors.append(f"V2.9 raw-to-1m checksum mismatch for {date}")
    return errors


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe, expected in physical_quality.items():
        observed = manifest.get("quality", {}).get(timeframe)
        if observed != expected:
            errors.append(f"V2.9 manifest quality mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    if report != manifest:
        return ["V2.9 quality report mismatch"]
    return []


def _validate_markdown(root: Path) -> list[str]:
    path = root / REPORT_MD_PATH
    if not path.exists():
        return [f"missing markdown report: {REPORT_MD_PATH}"]
    return validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), "V2.9 Markdown report")


def _find_forbidden_v2_9_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V2_9_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V2.9 artifact detected: {relative}")
    backtests = root / "reports/backtests"
    if backtests.exists():
        for child in sorted(backtests.rglob("*")):
            if not child.is_file() or child.name == ".gitkeep":
                continue
            if _is_legacy_backtest_report(child.relative_to(root)):
                continue
            errors.append(f"Forbidden V2.9 artifact detected: {child.relative_to(root).as_posix()}")
    return errors


def _is_legacy_backtest_report(relative: Path) -> bool:
    if len(relative.parts) != 3 or relative.parts[0] != "reports" or relative.parts[1] != "backtests":
        return False
    name = relative.parts[2]
    legacy_exact_prefixes = (
        "baseline_suite_v1_",
        "codex_cli_sample_backtest_v1_",
        "codex_prompt_mode_comparison_v1_",
        "codex_setup_review_v1_",
        "first_mechanical_backtest_review.",
        "llm_offline_suite_v1_",
        "mechanical_backtest_v1_",
    )
    if name.startswith(legacy_exact_prefixes):
        return True
    return bool(re.fullmatch(r"backtest_[0-9a-f-]{36}\.(json|md)", name))


def _result(errors: list[str], *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION, "passed": not errors, "errors": errors, "manifest": manifest}
