from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.config import VERSION, PublicMarketIngestionConfig
from galapagos.data.public_market.ingestion import normalize_binance_klines
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import parse_binance_kline_zip
from galapagos.data.public_market.storage import read_parquet
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_new_modules_for_forbidden_terms,
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
    validate_safety_flags,
)

EXPECTED_LIMITATIONS_V2_3 = [
    "V2.3 couvre une seule source publique read-only, un seul symbole, un seul timeframe et une seule journee.",
    "V2.3 ne valide aucune strategie, aucun modele ML, aucun signal, aucun backtest et aucun trading.",
]

INGESTION_RUN_ID_PATTERN = re.compile(r"^v2_3_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

MANIFEST_TOP_LEVEL_KEYS = {
    "version",
    "correction_version",
    "mission",
    "status",
    "created_at_utc",
    "ingestion_run_id",
    "network_used",
    "public_read_only",
    "authentication_used",
    "api_key_used",
    "private_endpoint_used",
    "orders_enabled",
    "paper_live_enabled",
    "trading_enabled",
    "ml_enabled",
    "labels_enabled",
    "backtest_enabled",
    "source",
    "raw",
    "silver",
    "quality",
    "limitations",
}

REPORT_TOP_LEVEL_KEYS = {
    "version",
    "correction_version",
    "status",
    "created_at_utc",
    "ingestion_run_id",
    "source_url",
    "source",
    "quality",
    "raw_checksum",
    "silver_checksum",
    "raw_path",
    "silver_path",
    "safety",
    "limitations",
}

SOURCE_KEYS = {"name", "venue", "market_type", "symbol", "timeframe", "date"}
RAW_KEYS = {"path", "sha256", "bytes"}
SILVER_KEYS = {"path", "sha256", "bytes", "format"}
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
    "backtest_enabled",
}

RAW_SILVER_LINEAGE_COLUMNS = [
    "event_ts",
    "close_ts",
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
]

STALE_SCOPE_TOKENS = [
    "walk-forward",
    "walk_forward",
    "offline_walk_forward",
    "bounded_offline_walk_forward_protocol",
    "sans réseau",
    "no_network",
]

PROJECT_SCOPE_FIELDS = [
    "authorized_future_scope",
    "approval_phrase_expected_exact",
    "approval_phrase_provided",
    "candidate_scope",
    "candidate_future_scope",
    "candidate_approval_phrase_expected_exact",
    "candidate_approval_phrase_provided",
    "next_direction",
]


def validate_public_market_ingestion_v2_3(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    config = PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=root,
    )
    errors: list[str] = []
    errors.extend(_validate_required_files(config))
    if errors:
        return _result(errors)

    manifest = load_json(config.manifest_path)
    quality_report = load_json(config.quality_json_path)
    errors.extend(_validate_manifest(root=root, config=config, manifest=manifest))
    errors.extend(_validate_quality_report(manifest=manifest, quality_report=quality_report))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.3 manifest"))
    errors.extend(scan_payload_for_forbidden_claims(quality_report, "V2.3 quality report"))
    errors.extend(_validate_quality_markdown(config.quality_md_path))
    frame = read_parquet(config.silver_path)
    errors.extend(_validate_silver_frame(frame))
    errors.extend(_validate_silver_provenance(frame, manifest))
    errors.extend(_compare_raw_silver_lineage(config=config, manifest=manifest, silver_frame=frame))
    quality = assess_ohlcv_quality(frame, expected_rows=config.expected_rows, timeframe=config.timeframe).payload
    errors.extend(_compare_quality(manifest_quality=manifest.get("quality", {}), physical_quality=quality))
    errors.extend(_validate_project_state_scope(root))
    errors.extend(scan_new_modules_for_forbidden_terms(root))
    return _result(errors, manifest=manifest, physical_quality=quality)


def _validate_required_files(config: PublicMarketIngestionConfig) -> list[str]:
    errors: list[str] = []
    for path in [config.raw_path, config.silver_path, config.manifest_path, config.quality_json_path, config.quality_md_path]:
        if not path.exists():
            errors.append(f"missing required file: {path}")
    return errors


def _validate_manifest(*, root: Path, config: PublicMarketIngestionConfig, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_TOP_LEVEL_KEYS, "V2.3 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("manifest version must be V2.3")
    if manifest.get("correction_version") != "V2.3.1":
        errors.append("manifest correction_version must be V2.3.1")
    if manifest.get("mission") != "Public Market Data Read-Only Ingestion Preview":
        errors.append("manifest mission mismatch")
    if manifest.get("status") != "PASS":
        errors.append("manifest status must be PASS")
    if not _is_valid_utc_iso(manifest.get("created_at_utc")):
        errors.append("V2.3 manifest created_at_utc invalid")
    run_id = manifest.get("ingestion_run_id")
    if not isinstance(run_id, str) or INGESTION_RUN_ID_PATTERN.fullmatch(run_id) is None:
        errors.append("V2.3 manifest ingestion_run_id invalid")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V2_3:
        errors.append("V2.3 manifest limitations mismatch")
    errors.extend(validate_safety_flags(manifest))
    expected_source = {
        "name": "binance_public_archive",
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "date": "2024-01-15",
    }
    if manifest.get("source") != expected_source:
        errors.append("manifest source block mismatch")
    source_raw = manifest.get("source", {})
    source = source_raw if isinstance(source_raw, dict) else {}
    raw_raw = manifest.get("raw", {})
    raw = raw_raw if isinstance(raw_raw, dict) else {}
    silver_raw = manifest.get("silver", {})
    silver = silver_raw if isinstance(silver_raw, dict) else {}
    quality_raw = manifest.get("quality", {})
    quality = quality_raw if isinstance(quality_raw, dict) else {}
    errors.extend(validate_exact_keys(source, SOURCE_KEYS, "V2.3 manifest source"))
    errors.extend(validate_exact_keys(raw, RAW_KEYS, "V2.3 manifest raw"))
    errors.extend(validate_exact_keys(silver, SILVER_KEYS, "V2.3 manifest silver"))
    errors.extend(validate_exact_keys(quality, QUALITY_KEYS, "V2.3 manifest quality"))
    if (root / Path(raw.get("path", ""))).resolve() != config.raw_path.resolve():
        errors.append("manifest raw path mismatch")
    if (root / Path(silver.get("path", ""))).resolve() != config.silver_path.resolve():
        errors.append("manifest silver path mismatch")
    if raw.get("sha256") != sha256_file(config.raw_path):
        errors.append("raw checksum mismatch")
    if silver.get("sha256") != sha256_file(config.silver_path):
        errors.append("silver checksum mismatch")
    if raw.get("bytes") != config.raw_path.stat().st_size:
        errors.append("raw bytes mismatch")
    if silver.get("bytes") != config.silver_path.stat().st_size:
        errors.append("silver bytes mismatch")
    if silver.get("format") != "parquet":
        errors.append("silver format must be parquet")
    return errors


def _validate_quality_report(*, manifest: dict[str, Any], quality_report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(quality_report, REPORT_TOP_LEVEL_KEYS, "V2.3 quality report"))
    source_raw = quality_report.get("source", {})
    source = source_raw if isinstance(source_raw, dict) else {}
    quality_raw = quality_report.get("quality", {})
    quality = quality_raw if isinstance(quality_raw, dict) else {}
    safety_raw = quality_report.get("safety", {})
    safety = safety_raw if isinstance(safety_raw, dict) else {}
    errors.extend(validate_exact_keys(source, SOURCE_KEYS, "V2.3 quality report source"))
    errors.extend(validate_exact_keys(quality, QUALITY_KEYS, "V2.3 quality report quality"))
    errors.extend(validate_exact_keys(safety, SAFETY_KEYS, "V2.3 quality report safety"))
    expected_safety = {field: manifest.get(field) for field in SAFETY_KEYS}
    comparisons = [
        ("version", manifest.get("version"), "V2.3 quality report version mismatch"),
        ("correction_version", manifest.get("correction_version"), "V2.3 quality report correction_version mismatch"),
        ("status", manifest.get("status"), "V2.3 quality report status mismatch"),
        ("created_at_utc", manifest.get("created_at_utc"), "V2.3 quality report created_at_utc mismatch"),
        ("ingestion_run_id", manifest.get("ingestion_run_id"), "V2.3 quality report ingestion_run_id mismatch"),
        ("source", manifest.get("source"), "V2.3 quality report source mismatch"),
        ("quality", manifest.get("quality"), "V2.3 quality report quality mismatch"),
        ("raw_checksum", manifest.get("raw", {}).get("sha256"), "V2.3 quality report raw_checksum mismatch"),
        ("silver_checksum", manifest.get("silver", {}).get("sha256"), "V2.3 quality report silver_checksum mismatch"),
        ("raw_path", manifest.get("raw", {}).get("path"), "V2.3 quality report raw_path mismatch"),
        ("silver_path", manifest.get("silver", {}).get("path"), "V2.3 quality report silver_path mismatch"),
        ("safety", expected_safety, "V2.3 quality report safety mismatch"),
        ("limitations", manifest.get("limitations"), "V2.3 quality report limitations mismatch"),
    ]
    for field, expected, message in comparisons:
        if quality_report.get(field) != expected:
            errors.append(message)
    if quality_report.get("limitations") != EXPECTED_LIMITATIONS_V2_3:
        errors.append("V2.3 quality report limitations mismatch")
    errors.extend(validate_safety_flags(safety))
    return errors


def _validate_silver_frame(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if "normalized_file_sha256" in frame.columns:
        errors.append("silver must not contain normalized_file_sha256")
    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        errors.append(f"silver missing columns: {missing}")
        return errors
    for column in ["event_ts", "close_ts", "available_ts", "decision_ts", "ingested_at_ts"]:
        series = pd.to_datetime(frame[column], utc=True)
        if str(series.dt.tz) != "UTC":
            errors.append(f"{column} must be UTC timezone-aware")
    if set(frame["source"].unique()) != {"binance_archive"}:
        errors.append("unexpected source values")
    if set(frame["venue"].unique()) != {"binance"}:
        errors.append("unexpected venue values")
    if set(frame["market_type"].unique()) != {"spot"}:
        errors.append("unexpected market_type values")
    if set(frame["symbol"].unique()) != {"BTCUSDT"}:
        errors.append("unexpected symbol values")
    if set(frame["timeframe"].unique()) != {"1m"}:
        errors.append("unexpected timeframe values")
    return errors


def _validate_silver_provenance(frame: pd.DataFrame, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_raw_sha = manifest.get("raw", {}).get("sha256")
    expected_run_id = manifest.get("ingestion_run_id")
    try:
        expected_ingested_at = pd.Timestamp(manifest.get("created_at_utc")).tz_convert("UTC")
    except Exception:
        expected_ingested_at = None
    checks = {
        "raw_file_sha256": expected_raw_sha,
        "ingestion_run_id": expected_run_id,
    }
    for column, expected in checks.items():
        if column not in frame.columns:
            errors.append(f"silver missing provenance column: {column}")
            continue
        if frame[column].isna().any():
            errors.append(f"silver provenance {column} contains null")
        values = set(frame[column].astype("string").dropna().unique())
        if values != {str(expected)}:
            errors.append(f"silver provenance {column} mismatch")
    if "ingested_at_ts" not in frame.columns:
        errors.append("silver missing provenance column: ingested_at_ts")
    else:
        ingested_at = pd.to_datetime(frame["ingested_at_ts"], utc=True)
        if ingested_at.isna().any():
            errors.append("silver provenance ingested_at_ts contains null")
        if expected_ingested_at is None or not (ingested_at == expected_ingested_at).all():
            errors.append("silver provenance ingested_at_ts mismatch")
    return errors


def _compare_raw_silver_lineage(
    *, config: PublicMarketIngestionConfig, manifest: dict[str, Any], silver_frame: pd.DataFrame
) -> list[str]:
    errors: list[str] = []
    try:
        raw_frame = parse_binance_kline_zip(config.raw_path)
        expected = normalize_binance_klines(
            raw_frame,
            config=config,
            raw_sha=manifest.get("raw", {}).get("sha256", ""),
            ingestion_run_id=str(manifest.get("ingestion_run_id", "")),
            ingested_at_ts=str(manifest.get("created_at_utc", "1970-01-01T00:00:00Z")),
        )
        expected = _canonical_lineage_frame(expected)
        actual = _canonical_lineage_frame(silver_frame)
        pdt.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False, rtol=0.0, atol=1e-9)
    except AssertionError as exc:
        errors.append(f"raw/silver mismatch: {exc}")
    except Exception as exc:
        errors.append(f"raw/silver lineage validation failed: {exc}")
    return errors


def _canonical_lineage_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in RAW_SILVER_LINEAGE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing lineage columns: {missing}")
    canonical = frame[RAW_SILVER_LINEAGE_COLUMNS].copy()
    for column in ["event_ts", "close_ts"]:
        canonical[column] = pd.to_datetime(canonical[column], utc=True)
    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]:
        canonical[column] = pd.to_numeric(canonical[column], errors="raise").astype("float64")
    for column in ["trade_count", "source_open_time_raw", "source_close_time_raw"]:
        canonical[column] = pd.to_numeric(canonical[column], errors="raise").astype("int64")
    canonical["source_timestamp_unit"] = canonical["source_timestamp_unit"].astype("string")
    return canonical.sort_values("event_ts").reset_index(drop=True)


def _compare_quality(*, manifest_quality: dict[str, Any], physical_quality: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = [
        "rows",
        "expected_rows",
        "duplicate_rows",
        "gap_count",
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
    ]
    for field in fields:
        if manifest_quality.get(field) != physical_quality.get(field):
            errors.append(f"quality mismatch for {field}")
    if physical_quality.get("rows") != physical_quality.get("expected_rows"):
        errors.append("row count mismatch")
    if physical_quality.get("duplicate_rows") != 0:
        errors.append("duplicate rows detected")
    if physical_quality.get("gap_count") != 0:
        errors.append("gaps detected")
    if physical_quality.get("ohlc_violations") != 0:
        errors.append("OHLC violations detected")
    if physical_quality.get("negative_volume_rows") != 0:
        errors.append("negative volume detected")
    if physical_quality.get("null_critical_rows") != 0:
        errors.append("null critical rows detected")
    if physical_quality.get("timestamp_order_valid") is not True:
        errors.append("timestamp order invalid")
    if physical_quality.get("timestamps_utc") is not True:
        errors.append("timestamps are not UTC")
    if physical_quality.get("monotonic_event_ts") is not True:
        errors.append("event_ts physical order is not monotonic")
    return errors


def _validate_quality_markdown(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing quality markdown: {path}"]
    return validate_markdown_forbidden_claims(path.read_text(encoding="utf-8"), "V2.3 quality markdown")


def _is_valid_utc_iso(value: Any) -> bool:
    if not isinstance(value, str) or not value or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == UTC.utcoffset(parsed)


def _validate_project_state_scope(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in [Path("reports/PROJECT_STATE.json"), Path("reports/current/latest_metrics.json")]:
        path = root / relative
        if not path.exists():
            continue
        payload = load_json(path)
        for field in PROJECT_SCOPE_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str):
                continue
            lowered = value.lower()
            stale_tokens = [token for token in STALE_SCOPE_TOKENS if token in lowered]
            if stale_tokens:
                errors.append(f"{relative}: stale V2.3 candidate scope in {field}: {stale_tokens}")
        if payload.get("v2_3_validated") is True:
            errors.append(f"{relative}: V2.3 must remain unvalidated after V2.3.1 correction")
        if payload.get("last_validated_version") not in {None, "V2.2.1", "V2.3.1"}:
            errors.append(f"{relative}: last_validated_version must remain V2.2.1 or V2.3.1")
    return errors


def _result(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, **extra}
