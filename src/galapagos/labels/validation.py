from __future__ import annotations

import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from galapagos.labels.schemas import LABEL_COLUMNS_V2_6, FORBIDDEN_COLUMNS_V2_6
from galapagos.labels.registry import (
    VERSION,
    CORRECTION_VERSION,
    LABEL_SCHEMA_VERSION,
    TARGET_TIMEFRAMES,
    HORIZONS,
    THRESHOLD,
    get_label_gold_path,
)
from galapagos.data.public_market.provenance import sha256_file
from galapagos.labels.quality import assess_label_quality


def validate_label_factory_v2_6(
    project_root: Path,
) -> Dict[str, Any]:
    """Performs deep physical, mathematical and structural verification of Galapagos V2.6 labels.
    
    Ensures 100% correctness and strictly enforces anti-leakage guards.
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # 1. Check workspace settings
    manifest_path = project_root / "reports/manifests/clean_label_factory_v2_6_manifest.json"
    report_json_path = project_root / "reports/labels/clean_label_factory_v2_6.json"
    report_md_path = project_root / "reports/labels/clean_label_factory_v2_6.md"
    
    if not manifest_path.exists():
        errors.append(f"Manifest V2.6 not found at: {manifest_path}")
        return {"passed": False, "errors": errors, "warnings": warnings}
        
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse manifest JSON: {str(e)}")
        return {"passed": False, "errors": errors, "warnings": warnings}

    # PARTIE A - Top-level keys verification
    MANIFEST_KEYS = {
        "version", "correction_version", "status", "created_at_utc", "label_run_id",
        "input_ohlcv", "outputs", "label_schema_version", "label_columns", "horizons",
        "threshold", "quality", "safety", "limitations"
    }
    manifest_keys_actual = set(manifest.keys())
    unexpected = manifest_keys_actual - MANIFEST_KEYS
    missing = MANIFEST_KEYS - manifest_keys_actual
    if unexpected:
        errors.append(f"V2.6 manifest unexpected keys: {sorted(list(unexpected))}")
    if missing:
        errors.append(f"V2.6 manifest missing keys: {sorted(list(missing))}")

    # PARTIE F - created_at_utc and label_run_id validation
    created_at = manifest.get("created_at_utc")
    if not isinstance(created_at, str) or not created_at or not created_at.endswith("Z"):
        errors.append("Invalid created_at_utc in manifest")
    else:
        try:
            pd.to_datetime(created_at)
        except Exception:
            errors.append("Invalid created_at_utc format in manifest")

    label_run_id = manifest.get("label_run_id")
    if not isinstance(label_run_id, str) or not re.match(r"^v2_6_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$", label_run_id):
        errors.append("Invalid label_run_id in manifest")

    # PARTIE B - Sous-schémas stricts du manifest
    # safety validation
    safety = manifest.get("safety", {})
    if isinstance(safety, dict):
        safety_keys_expected = {
            "public_read_only", "authentication_used", "api_key_used", "private_endpoint_used",
            "orders_enabled", "paper_live_enabled", "trading_enabled", "ml_enabled",
            "labels_enabled", "backtest_enabled"
        }
        if set(safety.keys()) != safety_keys_expected:
            errors.append("Safety keys mismatch in manifest")
        
        # Safety configuration values checks
        safety_checks = {
            "public_read_only": True,
            "authentication_used": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "orders_enabled": False,
            "paper_live_enabled": False,
            "trading_enabled": False,
            "ml_enabled": False,
            "labels_enabled": True,
            "backtest_enabled": False
        }
        for key, val in safety_checks.items():
            if safety.get(key) != val:
                errors.append(f"Safety configuration violation: {key} must be {val}, got {safety.get(key)}")
    else:
        errors.append("safety must be a dictionary")

    # input_ohlcv validation
    input_ohlcv = manifest.get("input_ohlcv", {})
    if isinstance(input_ohlcv, dict):
        if set(input_ohlcv.keys()) != {"1m", "5m", "15m", "1h"}:
            errors.append("input_ohlcv timeframes mismatch in manifest")
        for tf, tf_input in input_ohlcv.items():
            if isinstance(tf_input, dict):
                if set(tf_input.keys()) != {"path", "sha256", "rows"}:
                    errors.append(f"input_ohlcv {tf} keys mismatch in manifest")
            else:
                errors.append(f"input_ohlcv {tf} must be a dictionary")
    else:
        errors.append("input_ohlcv must be a dictionary")

    # outputs validation
    outputs = manifest.get("outputs", {})
    if isinstance(outputs, dict):
        if set(outputs.keys()) != {"1m", "5m", "15m", "1h"}:
            errors.append("outputs timeframes mismatch in manifest")
        for tf, tf_output in outputs.items():
            if isinstance(tf_output, dict):
                if set(tf_output.keys()) != {"path", "sha256", "bytes", "rows", "format"}:
                    errors.append(f"outputs {tf} keys mismatch in manifest")
            else:
                errors.append(f"outputs {tf} must be a dictionary")
    else:
        errors.append("outputs must be a dictionary")

    # quality validation
    quality = manifest.get("quality", {})
    if isinstance(quality, dict):
        if set(quality.keys()) != {"1m", "5m", "15m", "1h"}:
            errors.append("quality timeframes mismatch in manifest")
        for tf, tf_qual in quality.items():
            if isinstance(tf_qual, dict):
                expected_qual_keys = {
                    "rows", "expected_rows", "duplicate_rows", "tail_rows",
                    "valid_counts_by_horizon", "null_counts_by_column", "forbidden_columns_present",
                    "timestamps_utc", "monotonic_event_ts", "label_available_ts_valid",
                    "label_end_ts_valid", "causal_separation_guard_passed", "errors", "warnings"
                }
                if set(tf_qual.keys()) != expected_qual_keys:
                    errors.append(f"quality {tf} keys mismatch in manifest")
                
                valid_counts = tf_qual.get("valid_counts_by_horizon", {})
                if isinstance(valid_counts, dict):
                    if set(valid_counts.keys()) != {"h1", "h3", "h5"}:
                        errors.append(f"quality {tf} valid_counts_by_horizon keys mismatch in manifest")
                else:
                    errors.append(f"quality {tf} valid_counts_by_horizon must be a dictionary")
            else:
                errors.append(f"quality {tf} must be a dictionary")
    else:
        errors.append("quality must be a dictionary")

    # Check top-level manifest constraints
    if manifest.get("version") != "V2.6":
        errors.append(f"Manifest version mismatch: expected V2.6, got {manifest.get('version')}")
    if manifest.get("label_schema_version") != "V2.6":
        errors.append(f"Schema version mismatch: expected V2.6, got {manifest.get('label_schema_version')}")
        
    # Check limitations claims
    limitations = manifest.get("limitations", [])
    expected_limitations = [
        "V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.",
        "V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre."
    ]
    if limitations != expected_limitations:
        errors.append("Limitations claim modified or invalid in manifest")
        
    # Check parameters
    if manifest.get("horizons") != HORIZONS:
        errors.append(f"Horizons configuration mismatch: expected {HORIZONS}, got {manifest.get('horizons')}")
    if manifest.get("threshold") != THRESHOLD:
        errors.append(f"Threshold configuration mismatch: expected {THRESHOLD}, got {manifest.get('threshold')}")
        
    # 2. Check each timeframe's inputs, outputs and quality
    for tf in TARGET_TIMEFRAMES:
        tf_input = input_ohlcv.get(tf, {}) if isinstance(input_ohlcv, dict) else {}
        input_path_str = tf_input.get("path") if isinstance(tf_input, dict) else None
        if not input_path_str:
            errors.append(f"Input path not specified in manifest for timeframe {tf}")
            continue
        input_path = project_root / input_path_str
        if not input_path.exists():
            errors.append(f"Input OHLCV file not found: {input_path}")
            continue
            
        tf_output = outputs.get(tf, {}) if isinstance(outputs, dict) else {}
        output_path_str = tf_output.get("path") if isinstance(tf_output, dict) else None
        if not output_path_str:
            errors.append(f"Output label path not specified in manifest for timeframe {tf}")
            continue
        output_path = project_root / output_path_str
        if not output_path.exists():
            errors.append(f"Output label file not found: {output_path}")
            continue
            
        # Read files for deep mathematical and temporal verification
        try:
            ohlcv_df = pd.read_parquet(input_path)
            label_df = pd.read_parquet(output_path)
        except Exception as e:
            errors.append(f"Failed to read Parquet files for {tf}: {str(e)}")
            continue
            
        # PARTIE D - Compare manifest to recalculated physical values
        actual_input_rows = len(ohlcv_df)
        actual_input_sha = sha256_file(input_path)
        if tf_input.get("rows") != actual_input_rows:
            errors.append(f"V2.6 manifest input mismatch for {tf}.rows")
        if tf_input.get("sha256") != actual_input_sha:
            errors.append(f"V2.6 manifest input mismatch for {tf}.sha256")

        actual_output_rows = len(label_df)
        actual_output_sha = sha256_file(output_path)
        actual_output_bytes = output_path.stat().st_size
        if tf_output.get("rows") != actual_output_rows:
            errors.append(f"V2.6 manifest output mismatch for {tf}.rows")
        if tf_output.get("sha256") != actual_output_sha:
            errors.append(f"V2.6 manifest output mismatch for {tf}.sha256")
        if tf_output.get("bytes") != actual_output_bytes:
            errors.append(f"V2.6 manifest output mismatch for {tf}.bytes")

        # Row counts match
        expected_rows = len(ohlcv_df)
        if len(label_df) != expected_rows:
            errors.append(f"Labels row count mismatch for {tf}: expected {expected_rows}, got {len(label_df)}")
            continue
            
        # Verify strict column schema and order
        if list(label_df.columns) != LABEL_COLUMNS_V2_6:
            errors.append(f"Label schema mismatch or column order incorrect for {tf}")
            
        # Check source ohlcv checksum and label_schema_version inside the parquet
        if not (label_df["source_ohlcv_sha256"] == actual_input_sha).all():
            errors.append(f"source_ohlcv_sha256 inside labels Parquet is incorrect for {tf}")
        if not (label_df["label_schema_version"] == "V2.6").all():
            errors.append(f"label_schema_version inside labels Parquet is incorrect for {tf}")
            
        # Recalculate and verify labels for this timeframe
        close = ohlcv_df["close"].astype(float)
        close_ts = ohlcv_df["close_ts"]
        
        for h in HORIZONS:
            expected_future_close = close.shift(-h)
            expected_simple_return = expected_future_close / close - 1.0
            expected_log_return = np.log(expected_future_close / close)
            
            # Validity
            expected_valid = ~expected_future_close.isna() & ~close_ts.shift(-h).isna()
            
            # Check physical validity in parquet
            actual_valid = label_df[f"label_valid_h{h}"].astype(bool)
            if not (actual_valid == expected_valid).all():
                errors.append(f"label_valid_h{h} mismatch on {tf}")
                
            # Mathematical recalculation check for valid rows
            valid_mask = expected_valid
            if valid_mask.any():
                # future close
                diff_close = np.abs(label_df.loc[valid_mask, f"future_close_h{h}"] - expected_future_close[valid_mask])
                if (diff_close > 1e-8).any():
                    errors.append(f"future_close_h{h} mathematical mismatch on {tf}")
                    
                # returns
                diff_simple = np.abs(label_df.loc[valid_mask, f"future_simple_return_h{h}"] - expected_simple_return[valid_mask])
                if (diff_simple > 1e-8).any():
                    errors.append(f"future_simple_return_h{h} mathematical mismatch on {tf}")
                    
                diff_log = np.abs(label_df.loc[valid_mask, f"future_log_return_h{h}"] - expected_log_return[valid_mask])
                if (diff_log > 1e-8).any():
                    errors.append(f"future_log_return_h{h} mathematical mismatch on {tf}")
                    
                # direction
                expected_direction = np.where(expected_log_return > 0.0, 1.0, np.where(expected_log_return < 0.0, -1.0, 0.0))
                diff_direction = label_df.loc[valid_mask, f"direction_h{h}"].astype(float) - expected_direction[valid_mask]
                if (np.abs(diff_direction) > 1e-8).any():
                    errors.append(f"direction_h{h} mathematical mismatch on {tf}")
                    
                # up_down_flat
                expected_cat = np.where(expected_log_return > THRESHOLD, "UP", np.where(expected_log_return < -THRESHOLD, "DOWN", "FLAT"))
                if not (label_df.loc[valid_mask, f"up_down_flat_h{h}"] == expected_cat[valid_mask]).all():
                    errors.append(f"up_down_flat_h{h} mismatch on {tf}")
                    
                # label_end_ts_h
                expected_end_ts = close_ts.shift(-h)
                if not (label_df.loc[valid_mask, f"label_end_ts_h{h}"] == expected_end_ts[valid_mask]).all():
                    errors.append(f"label_end_ts_h{h} timestamp mismatch on {tf}")
                    
            # For invalid rows, check that values are properly nullified
            invalid_mask = ~expected_valid
            if invalid_mask.any():
                if not label_df.loc[invalid_mask, f"future_close_h{h}"].isna().all():
                    errors.append(f"future_close_h{h} not null for invalid rows on {tf}")
                if not label_df.loc[invalid_mask, f"future_simple_return_h{h}"].isna().all():
                    errors.append(f"future_simple_return_h{h} not null for invalid rows on {tf}")
                if not label_df.loc[invalid_mask, f"future_log_return_h{h}"].isna().all():
                    errors.append(f"future_log_return_h{h} not null for invalid rows on {tf}")
                if not label_df.loc[invalid_mask, f"direction_h{h}"].isna().all():
                    errors.append(f"direction_h{h} not null for invalid rows on {tf}")
                if not label_df.loc[invalid_mask, f"up_down_flat_h{h}"].isna().all():
                    errors.append(f"up_down_flat_h{h} not null for invalid rows on {tf}")
                if not label_df.loc[invalid_mask, f"label_end_ts_h{h}"].isna().all():
                    errors.append(f"label_end_ts_h{h} not null for invalid rows on {tf}")
                    
        # Check tail_row consistency
        expected_tail_row = ~(label_df["label_valid_h1"] & label_df["label_valid_h3"] & label_df["label_valid_h5"])
        if not (label_df["tail_row"] == expected_tail_row).all():
            errors.append(f"tail_row consistency violation for {tf}")
            
        # Check label_available_ts consistency
        expected_available_ts = np.where(
            label_df["label_valid_h5"],
            label_df["label_end_ts_h5"],
            np.where(
                label_df["label_valid_h3"],
                label_df["label_end_ts_h3"],
                np.where(
                    label_df["label_valid_h1"],
                    label_df["label_end_ts_h1"],
                    None
                )
            )
        )
        expected_available_ts = pd.Series(expected_available_ts).fillna("None")
        actual_available_ts = label_df["label_available_ts"].fillna("None")
        if not (actual_available_ts == expected_available_ts).all():
            errors.append(f"label_available_ts consistency violation for {tf}")
            
        # Check causal temporal separation: label_available_ts > decision_ts for all valid rows
        valid_rows_mask = label_df["label_valid_h1"]
        if valid_rows_mask.any():
            avail_ts = pd.to_datetime(label_df.loc[valid_rows_mask, "label_available_ts"])
            dec_ts = pd.to_datetime(label_df.loc[valid_rows_mask, "decision_ts"])
            if (avail_ts <= dec_ts).any():
                errors.append(f"Causal leakage detected: label_available_ts <= decision_ts on valid rows for {tf}")
                
        # Check forbidden columns check
        for col in label_df.columns:
            for term in FORBIDDEN_COLUMNS_V2_6:
                if term in col.lower():
                    errors.append(f"Forbidden column detected in Parquet '{col}' for timeframe {tf}")
                    
        # Evaluate recalculated stats against manifest to check physical coherence
        assessments = assess_label_quality(label_df, expected_rows)
        tf_qual = quality.get(tf, {}) if isinstance(quality, dict) else {}
        
        stat_keys_to_compare = [
            "rows", "expected_rows", "duplicate_rows", "tail_rows",
            "forbidden_columns_present", "timestamps_utc", "monotonic_event_ts",
            "label_available_ts_valid", "label_end_ts_valid", "causal_separation_guard_passed"
        ]
        
        for key in stat_keys_to_compare:
            if tf_qual.get(key) != assessments.get(key):
                errors.append(f"V2.6 manifest quality mismatch for {tf}.{key}")
                
        # Check valid_counts_by_horizon
        expected_counts = assessments.get("valid_counts_by_horizon", {})
        manifest_counts = tf_qual.get("valid_counts_by_horizon", {}) if isinstance(tf_qual, dict) else {}
        if isinstance(manifest_counts, dict):
            for h_key in {"h1", "h3", "h5"}:
                if expected_counts.get(h_key) != manifest_counts.get(h_key):
                    errors.append(f"V2.6 manifest quality mismatch for {tf}.valid_counts_by_horizon.{h_key}")
                    
        # Check null_counts_by_column
        expected_nulls = assessments.get("null_counts_by_column", {})
        manifest_nulls = tf_qual.get("null_counts_by_column", {}) if isinstance(tf_qual, dict) else {}
        if isinstance(manifest_nulls, dict):
            for col_key in expected_nulls:
                if expected_nulls.get(col_key) != manifest_nulls.get(col_key):
                    errors.append(f"V2.6 manifest quality mismatch for {tf}.null_counts_by_column.{col_key}")
                    
        # Proactively check that no files in gold/features have been modified.
        feature_gold_path = project_root / f"data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/features-2024-01-15.parquet"
        if feature_gold_path.exists():
            try:
                feat_df = pd.read_parquet(feature_gold_path)
                for c in feat_df.columns:
                    if "future" in c.lower() or "label" in c.lower():
                        errors.append(f"Leakage: Label column '{c}' detected inside gold feature store file for {tf}")
            except Exception as e:
                warnings.append(f"Could not read feature parquet file for checks: {str(e)}")
                
    # 3. PARTIE C - Check JSON report alignment with manifest (strict projection validation)
    if not report_json_path.exists():
        errors.append(f"JSON Report not found: {report_json_path}")
    else:
        try:
            with open(report_json_path, "r") as f:
                report_json = json.load(f)
            
            # Check top level quality report keys
            report_keys_actual = set(report_json.keys())
            unexpected_rep = report_keys_actual - MANIFEST_KEYS
            missing_rep = MANIFEST_KEYS - report_keys_actual
            if unexpected_rep:
                errors.append(f"V2.6 quality report unexpected keys: {sorted(list(unexpected_rep))}")
            if missing_rep:
                errors.append(f"V2.6 quality report missing keys: {sorted(list(missing_rep))}")
                
            # Compare every field value between report and manifest
            for field in MANIFEST_KEYS:
                if field in manifest and field in report_json:
                    if manifest[field] != report_json[field]:
                        errors.append(f"V2.6 quality report mismatch for {field}")
        except Exception as e:
            errors.append(f"Failed to read or parse JSON report: {str(e)}")
            
    # 4. PARTIE E - Claims positives interdites récursives
    FORBIDDEN_CLAIMS = [
        "strategy validated", "stratégie validée", "strategie validee",
        "signal validated", "signal validé", "signal valide",
        "trading enabled", "trading activé", "trading active",
        "paper live enabled", "paper live activé", "paper live active",
        "orders enabled", "ordre activé", "ordre active",
        "real trading", "trading réel activé", "trading reel active",
        "ml validated", "modèle ml validé", "modele ml valide",
        "backtest validated", "backtest validé", "backtest valide",
        "execution enabled", "live enabled", "production ready",
        "ordre réel activé", "ordre reel active", "strategy_validated"
    ]

    # Verify manifest
    try:
        manifest_str = json.dumps(manifest, ensure_ascii=False).lower()
        for claim in FORBIDDEN_CLAIMS:
            if claim in manifest_str:
                errors.append(f"Forbidden claim pattern detected in manifest: '{claim}'")
    except Exception as e:
        warnings.append(f"Could not scan manifest for claims: {e}")

    # Verify report JSON
    if report_json_path.exists():
        try:
            with open(report_json_path, "r") as f:
                rep_data = json.load(f)
            rep_str = json.dumps(rep_data, ensure_ascii=False).lower()
            for claim in FORBIDDEN_CLAIMS:
                if claim in rep_str:
                    errors.append(f"Forbidden claim pattern detected in report JSON: '{claim}'")
        except Exception as e:
            warnings.append(f"Could not scan report JSON for claims: {e}")

    # Verify Markdown report
    if not report_md_path.exists():
        errors.append(f"Markdown report not found: {report_md_path}")
    else:
        try:
            with open(report_md_path, "r") as f:
                md_content = f.read()
            md_content_lower = md_content.lower()
            for claim in FORBIDDEN_CLAIMS:
                if claim in md_content_lower:
                    errors.append(f"Forbidden claim pattern detected in Markdown report: '{claim}'")
        except Exception as e:
            errors.append(f"Failed to read Markdown report: {str(e)}")
            
    # Check if a ML dataset has been created (forbidden)
    ml_dataset_path = project_root / "data/gold/dataset_ml"
    if ml_dataset_path.exists():
        errors.append("Violation: ML dataset directory 'data/gold/dataset_ml' was created")
        
    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
    }
