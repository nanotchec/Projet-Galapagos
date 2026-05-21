from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.validation.manifests import load_json
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4, resampled_silver_path
from galapagos.validation.safety import (
    scan_new_modules_for_forbidden_terms,
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
    validate_safety_flags,
)
from galapagos.features.schemas import FEATURE_COLUMNS_V2_5, FORBIDDEN_TERMS
from galapagos.features.registry import (
    VERSION,
    CORRECTION_VERSION,
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MD_PATH,
    TARGET_TIMEFRAMES,
    get_feature_gold_path,
)
from galapagos.features.quality import assess_feature_quality

RUN_ID_PATTERN = re.compile(r"^v2_5_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
EXPECTED_LIMITATIONS_V2_5 = [
    "V2.5 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-15 a partir des donnees V2.4 validees.",
    "V2.5 ne produit aucun label, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre."
]

MANIFEST_TOP_LEVEL_KEYS = {
    "version",
    "correction_version",
    "status",
    "created_at_utc",
    "feature_run_id",
    "input_ohlcv",
    "outputs",
    "feature_schema_version",
    "feature_columns",
    "quality",
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
    "limitations",
}

REPORT_TOP_LEVEL_KEYS = {
    "version",
    "correction_version",
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

INPUT_TIMEFRAME_KEYS = {"path", "sha256", "rows"}
OUTPUT_TIMEFRAME_KEYS = {"path", "sha256", "bytes", "rows", "format"}

EXPECTED_ROWS_BY_TIMEFRAME = {
    "1m": 1440,
    "5m": 288,
    "15m": 96,
    "1h": 24,
}


def validate_causal_feature_store_v2_5(root: Path = Path(".")) -> dict[str, Any]:
    """Performs strict validation of the V2.5 feature store preview."""
    root = root.resolve()
    errors: list[str] = []
    
    # 1. Validate previous steps
    v2_4_validation = validate_ohlcv_resampling_v2_4(root)
    if not v2_4_validation["passed"]:
        errors.append(f"V2.4.8 resampling validation failed: {v2_4_validation['errors']}")
        return _result(errors)
        
    manifest_file = root / MANIFEST_PATH
    quality_file = root / QUALITY_JSON_PATH
    
    if not manifest_file.exists():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
        return _result(errors)
    if not quality_file.exists():
        errors.append(f"missing quality report: {QUALITY_JSON_PATH}")
        return _result(errors)
        
    manifest = load_json(manifest_file)
    report = load_json(quality_file)
    
    # 2. Validate manifest basic layout
    errors.extend(_validate_manifest_structure(root, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.5 manifest"))
    
    # If basic checks failed, stop early
    if errors:
        return _result(errors, manifest=manifest)
        
    # 3. physical features validation
    physical_qualities: dict[str, dict[str, Any]] = {}
    feature_run_id = manifest.get("feature_run_id")
    
    for timeframe in TARGET_TIMEFRAMES:
        gold_path = get_feature_gold_path(root, timeframe)
        if not gold_path.exists():
            errors.append(f"missing output gold features parquet: {gold_path.relative_to(root)}")
            continue
            
        # Physical load & shape check
        df = read_parquet(gold_path)
        
        # Schemas columns ordering and check
        errors.extend(_validate_frame_schema(timeframe, df))
        
        # Verify physical event_ts, duplicates, temporal correctness
        expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
        quality = assess_feature_quality(df, expected_rows, timeframe)
        physical_qualities[timeframe] = quality
        
        errors.extend(quality["errors"])
        
        # Check source_ohlcv_sha256 synchronization
        input_ohlcv_path = resampled_silver_path(root, timeframe)
        expected_sha = sha256_file(input_ohlcv_path) if input_ohlcv_path.exists() else ""
        
        if "source_ohlcv_sha256" in df.columns and expected_sha:
            actual_sha = df["source_ohlcv_sha256"].astype(str).iloc[0]
            if actual_sha != expected_sha:
                errors.append(f"{timeframe} features source_ohlcv_sha256 mismatch with input OHLCV Parquet")
                
        # Check metadata alignment
        if "feature_run_id" in df.columns:
            actual_run_id = df["feature_run_id"].astype(str).iloc[0]
            if actual_run_id != feature_run_id:
                errors.append(f"{timeframe} features feature_run_id mismatch with manifest")
                
        if "feature_schema_version" in df.columns:
            actual_version = df["feature_schema_version"].astype(str).iloc[0]
            if actual_version != "V2.5":
                errors.append(f"{timeframe} features feature_schema_version is not V2.5")
                
    # 4. Check quality stats synchronization
    errors.extend(_validate_manifest_quality(manifest, physical_qualities))
    
    # 5. Check report synchronization
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "quality report"))
    
    # 6. Check quality Markdown claims
    errors.extend(_validate_quality_markdown(root))
    
    # 7. Scan modules & scripts for safety
    errors.extend(scan_new_modules_for_forbidden_terms(root))
    errors.extend(_scan_v2_5_scripts(root))
    
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    
    errors.extend(validate_exact_keys(manifest, MANIFEST_TOP_LEVEL_KEYS, "V2.5 manifest"))
    
    if manifest.get("version") != VERSION:
        errors.append(f"manifest version must be {VERSION}")
    if manifest.get("correction_version") != CORRECTION_VERSION:
        errors.append(f"manifest correction_version must be {CORRECTION_VERSION}")
    if manifest.get("status") != "PASS":
        errors.append("manifest status must be PASS")
    if not _is_valid_utc_iso(manifest.get("created_at_utc")):
        errors.append("V2.5 manifest created_at_utc invalid")
        
    run_id = manifest.get("feature_run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        errors.append("V2.5 manifest feature_run_id invalid")
        
    if manifest.get("feature_schema_version") != "V2.5":
        errors.append("V2.5 manifest feature_schema_version must be V2.5")
    if manifest.get("feature_columns") != FEATURE_COLUMNS_V2_5:
        errors.append("V2.5 manifest feature_columns mismatch")
        
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V2_5:
        errors.append("V2.5 manifest limitations mismatch")
        
    errors.extend(validate_safety_flags(manifest))
    
    # Validate input_ohlcv section
    input_ohlcv_raw = manifest.get("input_ohlcv", {})
    input_ohlcv = input_ohlcv_raw if isinstance(input_ohlcv_raw, dict) else {}
    errors.extend(validate_exact_keys(input_ohlcv, set(TARGET_TIMEFRAMES), "V2.5 manifest input_ohlcv"))
    
    for tf in TARGET_TIMEFRAMES:
        block_raw = input_ohlcv.get(tf, {})
        block = block_raw if isinstance(block_raw, dict) else {}
        errors.extend(validate_exact_keys(block, INPUT_TIMEFRAME_KEYS, f"V2.5 manifest input_ohlcv.{tf}"))
        
        path = resampled_silver_path(root, tf)
        if (root / Path(block.get("path", ""))).resolve() != path.resolve():
            errors.append(f"input_ohlcv.{tf} path mismatch")
        if path.exists():
            if block.get("sha256") != sha256_file(path):
                errors.append(f"input_ohlcv.{tf} checksum mismatch")
            if block.get("rows") != EXPECTED_ROWS_BY_TIMEFRAME[tf]:
                errors.append(f"input_ohlcv.{tf} rows mismatch")
                
    # Validate outputs section
    outputs_raw = manifest.get("outputs", {})
    outputs = outputs_raw if isinstance(outputs_raw, dict) else {}
    errors.extend(validate_exact_keys(outputs, set(TARGET_TIMEFRAMES), "V2.5 manifest outputs"))
    
    for tf in TARGET_TIMEFRAMES:
        block_raw = outputs.get(tf, {})
        block = block_raw if isinstance(block_raw, dict) else {}
        errors.extend(validate_exact_keys(block, OUTPUT_TIMEFRAME_KEYS, f"V2.5 manifest outputs.{tf}"))
        
        gold_path = get_feature_gold_path(root, tf)
        if (root / Path(block.get("path", ""))).resolve() != gold_path.resolve():
            errors.append(f"outputs.{tf} path mismatch")
        if gold_path.exists():
            if block.get("sha256") != sha256_file(gold_path):
                errors.append(f"outputs.{tf} checksum mismatch")
            if block.get("bytes") != gold_path.stat().st_size:
                errors.append(f"outputs.{tf} bytes mismatch")
            if block.get("rows") != EXPECTED_ROWS_BY_TIMEFRAME[tf]:
                errors.append(f"outputs.{tf} rows mismatch")
            if block.get("format") != "parquet":
                errors.append(f"outputs.{tf} format must be parquet")
                
    return errors


def _validate_frame_schema(timeframe: str, df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    
    # Check strict schema columns and ordering
    if list(df.columns) != FEATURE_COLUMNS_V2_5:
        missing = [c for c in FEATURE_COLUMNS_V2_5 if c not in df.columns]
        unexpected = [c for c in df.columns if c not in FEATURE_COLUMNS_V2_5]
        if missing:
            errors.append(f"{timeframe} features missing columns: {missing}")
        if unexpected:
            errors.append(f"{timeframe} features unexpected columns: {unexpected}")
        if not missing and not unexpected:
            errors.append(f"{timeframe} features column order mismatch")
            
    # Check forbidden columns
    for col in df.columns:
        if col in FEATURE_COLUMNS_V2_5:
            continue
        # allow standard return columns
        is_allowed = (
            col.startswith("return_")
            or col.startswith("log_return_")
            or col == "volume_return_1"
        )
        if not is_allowed:
            for term in FORBIDDEN_TERMS:
                if term in col.lower():
                    errors.append(f"{timeframe} features column '{col}' matches forbidden term '{term}'")
                    
    return errors


def _validate_manifest_quality(manifest: dict[str, Any], physical_qualities: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    manifest_quality = manifest.get("quality")
    if not isinstance(manifest_quality, dict):
        return ["V2.5 manifest quality missing or invalid"]
        
    for tf in TARGET_TIMEFRAMES:
        declared = manifest_quality.get(tf)
        physical = physical_qualities.get(tf)
        
        if not isinstance(declared, dict):
            errors.append(f"V2.5 manifest quality missing for {tf}")
            continue
        if not isinstance(physical, dict):
            errors.append(f"V2.5 physical quality unavailable for {tf}")
            continue
            
        # Fields to check
        fields_to_validate = [
            "rows",
            "expected_rows",
            "warmup_rows",
            "rows_after_warmup",
            "duplicate_rows",
            "forbidden_columns_present",
            "timestamps_utc",
            "monotonic_event_ts",
            "feature_available_ts_valid",
            "decision_ts_valid",
            "causal_guard_passed",
        ]
        
        for field in fields_to_validate:
            if declared.get(field) != physical.get(field):
                errors.append(f"V2.5 manifest quality mismatch for {tf}.{field}: got {declared.get(field)}, physical is {physical.get(field)}")
                
        # Validate null counts map
        declared_nulls = declared.get("null_counts_by_column", {})
        physical_nulls = physical.get("null_counts_by_column", {})
        if declared_nulls != physical_nulls:
            errors.append(f"V2.5 manifest quality null_counts_by_column mismatch for {tf}")
            
        # Validate inf counts map
        declared_infs = declared.get("inf_counts_by_column", {})
        physical_infs = physical.get("inf_counts_by_column", {})
        if declared_infs != physical_infs:
            errors.append(f"V2.5 manifest quality inf_counts_by_column mismatch for {tf}")
            
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    
    expected = _build_report(manifest)
    errors.extend(validate_exact_keys(report, set(expected), "quality report"))
    
    if report.get("limitations") != EXPECTED_LIMITATIONS_V2_5:
        errors.append("quality report limitations mismatch")
        
    for field in [
        "version",
        "correction_version",
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
    ]:
        if report.get(field) != expected.get(field):
            errors.append(f"quality report {field} mismatch")
            
    errors.extend(validate_safety_flags(report.get("safety", {})))
    return errors


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "correction_version": manifest.get("correction_version"),
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_run_id": manifest["feature_run_id"],
        "input_ohlcv": manifest["input_ohlcv"],
        "outputs": manifest["outputs"],
        "feature_schema_version": manifest["feature_schema_version"],
        "feature_columns": manifest["feature_columns"],
        "quality": manifest["quality"],
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


def _validate_quality_markdown(root: Path) -> list[str]:
    path = root / QUALITY_MD_PATH
    if not path.exists():
        return [f"missing quality markdown: {QUALITY_MD_PATH}"]
        
    text = path.read_text(encoding="utf-8")
    errors = validate_markdown_forbidden_claims(text, "quality markdown")
    
    # Must explicitly state lack of validation, trading, signal
    required_clauses = [
        "V2.5 ne valide aucune stratégie",
        "V2.5 ne produit aucun label",
        "V2.5 ne produit aucun modèle ML",
        "V2.5 ne produit aucun backtest",
        "V2.5 ne produit aucun signal de trading",
        "V2.5 ne produit aucun ordre",
        "V2.5 n’autorise aucun paper live",
        "V2.5 n’autorise aucun trading réel",
    ]
    
    for clause in required_clauses:
        # replace any punctuation differences or non-breaking spaces for matches
        cleaned_text = text.replace("’", "'").replace(" ", " ")
        cleaned_clause = clause.replace("’", "'").replace(" ", " ")
        if cleaned_clause not in cleaned_text:
            errors.append(f"quality markdown is missing required explicit safety clause: '{clause}'")
            
    return errors


def _scan_v2_5_scripts(root: Path) -> list[str]:
    errors: list[str] = []
    tokens = ["create" + "_order", "place" + "_order", "submit" + "_order", "/api/v3/account", "/api/v3/order"]
    for relative in [
        Path("scripts/run_causal_feature_store_v2_5.py"),
        Path("scripts/validate_causal_feature_store_v2_5.py"),
    ]:
        path = root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token in text:
                errors.append(f"forbidden safety token in {relative}: {token}")
    return errors


def _is_valid_utc_iso(value: Any) -> bool:
    if not isinstance(value, str) or not value or not value.endswith("Z"):
        return False
    try:
        parsed = datetime = pd.to_datetime(value, utc=True)
    except ValueError:
        return False
    return True


def _result(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, **extra}
