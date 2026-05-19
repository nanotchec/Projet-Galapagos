from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.config import PublicMarketIngestionConfig
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.resampling import TARGET_TIMEFRAMES, resample_ohlcv
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.storage import ensure_parent, read_parquet, write_parquet
from galapagos.validation.manifests import load_json
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.safety import scan_new_modules_for_forbidden_terms, validate_safety_flags


VERSION = "V2.4"
CORRECTION_VERSION = "V2.4.1"
VERSION_SUFFIX = "v2_4"
TARGETS = ["5m", "15m", "1h"]
EXPECTED_ROWS = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24}
MANIFEST_PATH = Path("reports/manifests/ohlcv_resampling_v2_4_manifest.json")
QUALITY_JSON_PATH = Path("reports/data_quality/ohlcv_resampling_v2_4.json")
QUALITY_MD_PATH = Path("reports/data_quality/ohlcv_resampling_v2_4.md")
QUALITY_FIELDS = [
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
]


def run_ohlcv_resampling_v2_4(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    input_config = _input_config(root)
    ingestion_validation = validate_public_market_ingestion_v2_3(root)
    if not ingestion_validation["passed"]:
        raise RuntimeError(f"V2.3.1 input validation failed: {ingestion_validation['errors']}")
    created_at = _utc_now_iso()
    run_id = f"v2_4_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    frame_1m = read_parquet(input_config.silver_path)
    outputs: dict[str, dict[str, Any]] = {}
    qualities: dict[str, dict[str, Any]] = {}
    parent_child_consistency = True
    for timeframe in TARGETS:
        resampled = resample_ohlcv(frame_1m, target_timeframe=timeframe)
        output_path = resampled_silver_path(root, timeframe)
        write_parquet(resampled[OHLCV_COLUMNS], output_path)
        quality = assess_ohlcv_quality(
            resampled,
            expected_rows=EXPECTED_ROWS[timeframe],
            timeframe=timeframe,
        ).payload
        qualities[timeframe] = quality
        outputs[timeframe] = {
            "path": str(output_path.relative_to(root)),
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
            "rows": int(len(resampled)),
            "format": "parquet",
        }
    input_quality = assess_ohlcv_quality(frame_1m, expected_rows=EXPECTED_ROWS["1m"], timeframe="1m").payload
    status = "PASS"
    if input_quality["errors"] or any(quality["errors"] for quality in qualities.values()):
        status = "FAIL"
    manifest = {
        "version": VERSION,
        "correction_version": CORRECTION_VERSION,
        "status": status,
        "created_at_utc": created_at,
        "resampling_run_id": run_id,
        "input_1m": {
            "path": str(input_config.silver_path.relative_to(root)),
            "sha256": sha256_file(input_config.silver_path),
            "bytes": input_config.silver_path.stat().st_size,
            "rows": int(len(frame_1m)),
        },
        "outputs": outputs,
        "expected_rows": EXPECTED_ROWS,
        "quality": {"1m": input_quality, **qualities},
        "parent_child_consistency": parent_child_consistency,
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": False,
        "backtest_enabled": False,
        "limitations": [
            "V2.4 resample uniquement BTCUSDT 2024-01-15 depuis le silver 1m valide V2.3.1.",
            "V2.4 est data-only : aucun signal, aucun label, aucun ML, aucun backtest et aucun trading.",
        ],
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / QUALITY_JSON_PATH, report)
    _write_markdown(root / QUALITY_MD_PATH, report)
    return manifest


def validate_ohlcv_resampling_v2_4(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH
    quality_path = root / QUALITY_JSON_PATH
    if not manifest_path.exists():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
        return _result(errors)
    if not quality_path.exists():
        errors.append(f"missing quality report: {QUALITY_JSON_PATH}")
        return _result(errors)
    manifest = load_json(manifest_path)
    report = load_json(quality_path)
    errors.extend(_validate_manifest(root, manifest))
    ingestion_validation = validate_public_market_ingestion_v2_3(root)
    if not ingestion_validation["passed"]:
        errors.append(f"V2.3.1 input validation failed: {ingestion_validation['errors']}")
        return _result(errors, manifest=manifest)
    frame_1m = read_parquet(_input_config(root).silver_path)
    physical_qualities: dict[str, dict[str, Any]] = {
        "1m": assess_ohlcv_quality(frame_1m, expected_rows=EXPECTED_ROWS["1m"], timeframe="1m").payload
    }
    errors.extend(_validate_frame_quality("1m", frame_1m))
    for timeframe in TARGETS:
        output_path = resampled_silver_path(root, timeframe)
        if not output_path.exists():
            errors.append(f"missing output parquet: {output_path.relative_to(root)}")
            continue
        frame = read_parquet(output_path)
        physical_qualities[timeframe] = assess_ohlcv_quality(
            frame,
            expected_rows=EXPECTED_ROWS[timeframe],
            timeframe=timeframe,
        ).payload
        errors.extend(_validate_frame_quality(timeframe, frame))
        errors.extend(_validate_resampled_provenance(timeframe, frame, frame_1m))
        errors.extend(_validate_parent_child(timeframe, frame_1m, frame))
    errors.extend(_validate_manifest_quality(manifest, physical_qualities))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_new_modules_for_forbidden_terms(root))
    errors.extend(_scan_v2_4_scripts(root))
    return _result(errors, manifest=manifest)


def resampled_silver_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/silver/market_data/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / "part-2024-01-15.parquet"
    )


def _validate_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("manifest version must be V2.4")
    if manifest.get("correction_version") != CORRECTION_VERSION:
        errors.append("manifest correction_version must be V2.4.1")
    if manifest.get("status") != "PASS":
        errors.append("manifest status must be PASS")
    errors.extend(validate_safety_flags(manifest))
    if manifest.get("parent_child_consistency") is not True:
        errors.append("parent_child_consistency must be true")
    input_path = _input_config(root).silver_path
    input_block = manifest.get("input_1m", {})
    if (root / Path(input_block.get("path", ""))).resolve() != input_path.resolve():
        errors.append("input_1m path mismatch")
    if input_block.get("sha256") != sha256_file(input_path):
        errors.append("input_1m checksum mismatch")
    if input_block.get("rows") != EXPECTED_ROWS["1m"]:
        errors.append("input_1m rows mismatch")
    outputs = manifest.get("outputs", {})
    for timeframe in TARGETS:
        block = outputs.get(timeframe, {})
        path = resampled_silver_path(root, timeframe)
        if (root / Path(block.get("path", ""))).resolve() != path.resolve():
            errors.append(f"{timeframe} path mismatch")
        if not path.exists():
            errors.append(f"{timeframe} output missing")
            continue
        if block.get("sha256") != sha256_file(path):
            errors.append(f"{timeframe} checksum mismatch")
        if block.get("bytes") != path.stat().st_size:
            errors.append(f"{timeframe} bytes mismatch")
        if block.get("rows") != EXPECTED_ROWS[timeframe]:
            errors.append(f"{timeframe} rows mismatch")
        if block.get("format") != "parquet":
            errors.append(f"{timeframe} format must be parquet")
    expected_rows = manifest.get("expected_rows", {})
    for timeframe, expected in EXPECTED_ROWS.items():
        if expected_rows.get(timeframe) != expected:
            errors.append(f"expected rows mismatch for {timeframe}")
    return errors


def _validate_manifest_quality(manifest: dict[str, Any], physical_qualities: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    manifest_quality = manifest.get("quality")
    if not isinstance(manifest_quality, dict):
        return ["V2.4 manifest quality missing or invalid"]
    for timeframe in ["1m", *TARGETS]:
        declared = manifest_quality.get(timeframe)
        physical = physical_qualities.get(timeframe)
        if not isinstance(declared, dict):
            errors.append(f"V2.4 manifest quality missing for {timeframe}")
            continue
        if not isinstance(physical, dict):
            errors.append(f"V2.4 physical quality unavailable for {timeframe}")
            continue
        for field in QUALITY_FIELDS:
            if field not in declared:
                errors.append(f"V2.4 manifest quality mismatch for {timeframe}.{field}")
                continue
            if declared.get(field) != physical.get(field):
                errors.append(f"V2.4 manifest quality mismatch for {timeframe}.{field}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = _build_report(manifest)
    for field, message in [
        ("version", "quality report version mismatch"),
        ("correction_version", "quality report correction_version mismatch"),
        ("status", "quality report status mismatch"),
        ("created_at_utc", "quality report created_at_utc mismatch"),
        ("resampling_run_id", "quality report resampling_run_id mismatch"),
        ("input_1m", "quality report input_1m mismatch"),
        ("outputs", "quality report outputs mismatch"),
        ("expected_rows", "quality report expected_rows mismatch"),
        ("quality", "quality report quality mismatch"),
        ("parent_child_consistency", "quality report parent_child_consistency mismatch"),
        ("safety", "quality report safety mismatch"),
        ("limitations", "quality report limitations mismatch"),
    ]:
        if report.get(field) != expected.get(field):
            errors.append(message)
    errors.extend(validate_safety_flags(report.get("safety", {})))
    return errors


def _validate_frame_quality(timeframe: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if "normalized_file_sha256" in frame.columns:
        errors.append(f"{timeframe} must not contain normalized_file_sha256")
    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        errors.append(f"{timeframe} missing columns: {missing}")
        return errors
    if set(frame["timeframe"].astype(str).unique()) != {timeframe}:
        errors.append(f"{timeframe} timeframe column mismatch")
    quality = assess_ohlcv_quality(frame, expected_rows=EXPECTED_ROWS[timeframe], timeframe=timeframe).payload
    for field in [
        "duplicate_rows",
        "gap_count",
        "ohlc_violations",
        "negative_volume_rows",
        "null_critical_rows",
    ]:
        if quality[field] != 0:
            errors.append(f"{timeframe} quality {field} != 0")
    if quality["rows"] != EXPECTED_ROWS[timeframe]:
        errors.append(f"{timeframe} row count mismatch")
    if quality["monotonic_event_ts"] is not True:
        errors.append(f"{timeframe} physical event_ts is not monotonic")
    if quality["timestamp_order_valid"] is not True:
        errors.append(f"{timeframe} timestamp order invalid")
    if quality["timestamps_utc"] is not True:
        errors.append(f"{timeframe} timestamps are not UTC")
    return errors


def _validate_resampled_provenance(timeframe: str, frame: pd.DataFrame, frame_1m: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    for column in ["raw_file_sha256", "ingestion_run_id", "ingested_at_ts"]:
        expected = set(frame_1m[column].astype("string").dropna().unique())
        actual = set(frame[column].astype("string").dropna().unique())
        if len(expected) != 1 or actual != expected:
            errors.append(f"{timeframe} provenance {column} mismatch")
        if frame[column].isna().any():
            errors.append(f"{timeframe} provenance {column} contains null")
    return errors


def _validate_parent_child(timeframe: str, frame_1m: pd.DataFrame, physical: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    try:
        expected = _canonical_frame(resample_ohlcv(frame_1m, target_timeframe=timeframe))
        actual = _canonical_frame(physical)
        pdt.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False, rtol=0.0, atol=1e-9)
    except AssertionError as exc:
        errors.append(f"{timeframe} parent-child mismatch: {exc}")
    except Exception as exc:
        errors.append(f"{timeframe} parent-child validation failed: {exc}")
    return errors


def _canonical_frame(frame: pd.DataFrame) -> pd.DataFrame:
    canonical = frame[OHLCV_COLUMNS].copy()
    for column in ["event_ts", "close_ts", "available_ts", "decision_ts", "ingested_at_ts"]:
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
    for column in ["source", "venue", "market_type", "symbol", "timeframe", "source_timestamp_unit", "raw_file_sha256", "ingestion_run_id"]:
        canonical[column] = canonical[column].astype("string")
    return canonical.sort_values("event_ts").reset_index(drop=True)


def _scan_v2_4_scripts(root: Path) -> list[str]:
    errors: list[str] = []
    tokens = ["create" + "_order", "place" + "_order", "submit" + "_order", "/api/v3/account", "/api/v3/order"]
    for relative in [
        Path("scripts/run_ohlcv_resampling_v2_4.py"),
        Path("scripts/validate_ohlcv_resampling_v2_4.py"),
    ]:
        path = root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token in text:
                errors.append(f"forbidden safety token in {relative}: {token}")
    return errors


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "correction_version": manifest.get("correction_version"),
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "resampling_run_id": manifest["resampling_run_id"],
        "input_1m": manifest["input_1m"],
        "outputs": manifest["outputs"],
        "expected_rows": manifest["expected_rows"],
        "quality": manifest["quality"],
        "parent_child_consistency": manifest["parent_child_consistency"],
        "safety": {
            "public_read_only": True,
            "authentication_used": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "orders_enabled": False,
            "paper_live_enabled": False,
            "trading_enabled": False,
            "ml_enabled": False,
            "labels_enabled": False,
            "backtest_enabled": False,
        },
        "limitations": manifest["limitations"],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    lines = [
        "# OHLCV Resampling V2.4",
        "",
        f"- Correction : `{payload.get('correction_version')}`",
        f"- Statut : `{payload['status']}`",
        f"- Run : `{payload['resampling_run_id']}`",
        f"- Parent-child consistency : `{payload['parent_child_consistency']}`",
        "",
        "## Lignes",
    ]
    for timeframe in ["1m", *TARGETS]:
        quality = payload["quality"][timeframe]
        lines.append(f"- `{timeframe}` : `{quality['rows']}` / `{payload['expected_rows'][timeframe]}`")
    lines.extend(
        [
            "",
            "## Securite",
            "",
            "- Aucun ordre.",
            "- Aucun paper live.",
            "- Aucun trading.",
            "- Aucun ML.",
            "- Aucun label.",
            "- Aucun backtest.",
            "",
            "V2.4 est uniquement une etape de stockage/resampling OHLCV data-only.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _input_config(root: Path) -> PublicMarketIngestionConfig:
    return PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=root,
    )


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _result(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, **extra}
