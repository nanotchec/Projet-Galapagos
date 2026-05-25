from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_trades.config import (
    DOC_PATH_V7_1,
    MANIFEST_PATH_V7_1,
    REPORT_JSON_PATH_V7_1,
    REPORT_MD_PATH_V7_1,
    SCHEMA_VERSION_V7_1,
    VERSION_V7_1,
)
from galapagos.data.public_trades.discovery import count_agg_trade_zip_rows
from galapagos.data.public_trades.expanded_window_quality import assess_expanded_agg_trade_partitions_v7_1
from galapagos.data.public_trades.provenance import sha256_file
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_1, FORBIDDEN_TRADE_COLUMNS_V7_1


REQUIRED_MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "ingestion_run_id",
    "source",
    "discovery",
    "raw_files",
    "outputs",
    "schema_version",
    "trade_columns",
    "quality",
    "safety",
    "limitations",
}
REQUIRED_SOURCE_KEYS = {"name", "venue", "market_type", "symbol", "trade_source_type"}
REQUIRED_DISCOVERY_KEYS = {
    "window_start",
    "window_end",
    "total_days",
    "matches_v5_0_window",
    "v5_0_window_start",
    "v5_0_window_end",
    "missing_dates",
    "documented_gaps_allowed",
    "window_selection_reason",
}
REQUIRED_OUTPUT_KEYS = {"partitions", "total_rows", "total_bytes", "format"}
REQUIRED_PARTITION_KEYS = {"path", "sha256", "bytes", "rows", "min_event_ts", "max_event_ts", "raw_file_sha256"}
FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "validated trading strategy",
]
FORBIDDEN_ARTIFACT_PATHS = [
    Path("data/research/v7_1/features"),
    Path("data/research/v7_1/labels"),
    Path("data/research/v7_1/datasets"),
    Path("data/research/v7_1/ml"),
    Path("data/research/v7_1/backtests"),
    Path("data/research/v7_1/strategies"),
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
    Path("models"),
]


def validate_public_trades_expanded_window_v7_1(root: Path = Path(".")) -> dict[str, Any]:
    project_root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = project_root / MANIFEST_PATH_V7_1
    report_path = project_root / REPORT_JSON_PATH_V7_1
    if not manifest_path.exists():
        return _result([f"missing V7.1 manifest: {MANIFEST_PATH_V7_1}"], warnings)
    if not report_path.exists():
        errors.append(f"missing V7.1 report JSON: {REPORT_JSON_PATH_V7_1}")
    manifest = _read_json(manifest_path)
    report = _read_json(report_path) if report_path.exists() else {}
    errors.extend(validate_manifest_payload_v7_1(manifest))
    if report != manifest:
        errors.append("V7.1 report JSON must be a deterministic projection of the manifest")
    errors.extend(_validate_exact_keys(report, REQUIRED_MANIFEST_KEYS, "V7.1 report JSON"))
    errors.extend(_validate_physical_files(project_root, manifest))
    errors.extend(_validate_markdown(project_root / REPORT_MD_PATH_V7_1, "V7.1 Markdown report"))
    errors.extend(_validate_markdown(project_root / DOC_PATH_V7_1, "V7.1 documentation"))
    errors.extend(_find_forbidden_artifacts(project_root))
    return _result(errors, warnings, manifest)


def validate_manifest_payload_v7_1(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_exact_keys(manifest, REQUIRED_MANIFEST_KEYS, "V7.1 manifest"))
    if manifest.get("version") != VERSION_V7_1:
        errors.append("V7.1 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V7.1 manifest status must be PASS")
    if manifest.get("schema_version") != SCHEMA_VERSION_V7_1:
        errors.append("V7.1 schema_version mismatch")
    if manifest.get("trade_columns") != AGG_TRADE_COLUMNS_V7_1:
        errors.append("V7.1 trade_columns must match AGG_TRADE_COLUMNS_V7_1")
    errors.extend(_validate_exact_keys(manifest.get("source", {}), REQUIRED_SOURCE_KEYS, "V7.1 source"))
    source = manifest.get("source", {})
    if source.get("name") != "binance_public_archive":
        errors.append("V7.1 source name must be binance_public_archive")
    if source.get("venue") != "binance":
        errors.append("V7.1 venue must be binance")
    if source.get("market_type") != "spot":
        errors.append("V7.1 market_type must be spot")
    if source.get("symbol") != "BTCUSDT":
        errors.append("V7.1 symbol must be BTCUSDT")
    if source.get("trade_source_type") != "aggTrades":
        errors.append("V7.1 trade_source_type must be aggTrades")
    discovery = manifest.get("discovery", {})
    errors.extend(_validate_exact_keys(discovery, REQUIRED_DISCOVERY_KEYS, "V7.1 discovery"))
    if discovery.get("window_start") != "2023-03-25":
        errors.append("V7.1 window_start must be 2023-03-25")
    if discovery.get("window_end") != "2023-04-23":
        errors.append("V7.1 window_end must be 2023-04-23")
    if discovery.get("total_days") != 30:
        errors.append("V7.1 total_days must be 30")
    if discovery.get("documented_gaps_allowed") is not False:
        errors.append("V7.1 documented_gaps_allowed must be false")
    outputs = manifest.get("outputs", {})
    errors.extend(_validate_exact_keys(outputs, REQUIRED_OUTPUT_KEYS, "V7.1 outputs"))
    if outputs.get("format") != "partitioned_parquet":
        errors.append("V7.1 outputs format must be partitioned_parquet")
    for date_key, payload in outputs.get("partitions", {}).items():
        errors.extend(_validate_exact_keys(payload, REQUIRED_PARTITION_KEYS, f"V7.1 partition {date_key}"))
    safety = manifest.get("safety", {})
    if safety.get("public_read_only") is not True:
        errors.append("V7.1 public_read_only safety flag must be true")
    for key in [
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
    ]:
        if safety.get(key) is not False:
            errors.append(f"V7.1 safety flag must be false: {key}")
    return errors


def _validate_physical_files(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw_files = manifest.get("raw_files", {})
    raw_shas: dict[str, str] = {}
    raw_rows: dict[str, int] = {}
    for date_key, payload in raw_files.items():
        raw_path = root / payload.get("path", "")
        if not raw_path.exists():
            errors.append(f"missing raw zip for {date_key}: {payload.get('path')}")
            continue
        actual_sha = sha256_file(raw_path)
        raw_shas[date_key] = actual_sha
        if actual_sha != payload.get("sha256"):
            errors.append(f"raw checksum mismatch for {date_key}")
        if raw_path.stat().st_size != int(payload.get("bytes", -1)):
            errors.append(f"raw byte size mismatch for {date_key}")
        try:
            rows = count_agg_trade_zip_rows(raw_path)
            raw_rows[date_key] = rows
            if rows != int(payload.get("rows", -1)):
                errors.append(f"raw rows mismatch for {date_key}")
        except Exception as exc:
            errors.append(f"raw row count failed for {date_key}: {exc}")

    outputs = manifest.get("outputs", {})
    partitions = outputs.get("partitions", {})
    total_rows = 0
    total_bytes = 0
    for date_key, payload in partitions.items():
        output_path = root / payload.get("path", "")
        if not output_path.exists():
            errors.append(f"missing output partition for {date_key}: {payload.get('path')}")
            continue
        actual_sha = sha256_file(output_path)
        if actual_sha != payload.get("sha256"):
            errors.append(f"output parquet checksum mismatch for {date_key}")
        actual_bytes = output_path.stat().st_size
        if actual_bytes != int(payload.get("bytes", -1)):
            errors.append(f"output parquet byte size mismatch for {date_key}")
        frame = pd.read_parquet(output_path, engine="pyarrow")
        if list(frame.columns) != AGG_TRADE_COLUMNS_V7_1:
            errors.append(f"output parquet schema mismatch for {date_key}")
        if len(frame) != int(payload.get("rows", -1)):
            errors.append(f"output parquet row count mismatch for {date_key}")
        if date_key in raw_rows and len(frame) != raw_rows[date_key]:
            errors.append(f"output rows must equal raw rows for {date_key}")
        if date_key in raw_shas and set(frame.get("raw_file_sha256", pd.Series(dtype=str)).unique()) != {raw_shas[date_key]}:
            errors.append(f"output raw_file_sha256 mismatch for {date_key}")
        if frame.get("ingestion_run_id", pd.Series(dtype=str)).nunique() != 1:
            errors.append(f"output ingestion_run_id must be coherent for {date_key}")
        if frame.get("ingestion_run_id", pd.Series([""])).iloc[0] != manifest.get("ingestion_run_id"):
            errors.append(f"output ingestion_run_id does not match manifest for {date_key}")
        forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V7_1]
        if forbidden:
            errors.append(f"forbidden output columns present for {date_key}: {forbidden}")
        total_rows += len(frame)
        total_bytes += actual_bytes
    if total_rows != int(outputs.get("total_rows", -1)):
        errors.append("V7.1 outputs total_rows mismatch")
    if total_bytes != int(outputs.get("total_bytes", -1)):
        errors.append("V7.1 outputs total_bytes mismatch")
    quality = assess_expanded_agg_trade_partitions_v7_1(
        root,
        partitions,
        expected_days=int(manifest.get("discovery", {}).get("total_days", 0)),
        missing_dates=list(manifest.get("discovery", {}).get("missing_dates", [])),
    )
    errors.extend(f"physical quality error: {error}" for error in quality.get("errors", []))
    if quality != manifest.get("quality", {}):
        errors.append("V7.1 manifest quality does not match physical output")
    return errors


def _validate_markdown(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"missing {label}: {path}"]
    text = path.read_text(encoding="utf-8").casefold()
    return [f"{label} contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS if claim in text]


def _find_forbidden_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_ARTIFACT_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V7.1 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V7.1 artifact detected: {child.relative_to(root).as_posix()}")
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
