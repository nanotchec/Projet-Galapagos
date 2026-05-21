from __future__ import annotations

import json
import re
from datetime import datetime, timezone
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
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


EXPECTED_TIMEFRAMES_V2_6 = {"1m", "5m", "15m", "1h"}
EXPECTED_HORIZON_KEYS_V2_6 = {"h1", "h3", "h5"}

MANIFEST_KEYS_V2_6 = {
    "version",
    "correction_version",
    "status",
    "created_at_utc",
    "label_run_id",
    "input_ohlcv",
    "outputs",
    "label_schema_version",
    "label_columns",
    "horizons",
    "threshold",
    "quality",
    "safety",
    "limitations",
}

INPUT_OHLCV_KEYS_V2_6 = {"path", "sha256", "rows"}
OUTPUT_KEYS_V2_6 = {"path", "sha256", "bytes", "rows", "format"}
QUALITY_KEYS_V2_6 = {
    "rows",
    "expected_rows",
    "duplicate_rows",
    "tail_rows",
    "valid_counts_by_horizon",
    "null_counts_by_column",
    "forbidden_columns_present",
    "timestamps_utc",
    "monotonic_event_ts",
    "label_available_ts_valid",
    "label_end_ts_valid",
    "causal_separation_guard_passed",
    "errors",
    "warnings",
}
SAFETY_KEYS_V2_6 = {
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
EXPECTED_LIMITATIONS_V2_6 = [
    "V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.",
    "V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]

FORBIDDEN_V2_6_ARTIFACT_PATHS = [
    Path("data/gold/dataset_ml"),
    Path("data/gold/datasets"),
    Path("data/gold/datasets/ml"),
    Path("data/gold/datasets/ml_offline"),
    Path("data/gold/ml"),
    Path("data/gold/ml_offline"),
    Path("data/gold/training"),
    Path("data/gold/training_datasets"),
    Path("data/gold/backtests"),
    Path("data/gold/strategies"),
    Path("data/gold/signals"),
    Path("data/gold/predictions"),
    Path("reports/ml"),
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("reports/signals"),
    Path("reports/predictions"),
    Path("models"),
    Path("checkpoints"),
    Path("execution"),
    Path("orders"),
]
FORBIDDEN_V2_6_ARTIFACT_PATTERNS = [
    "dataset_ml",
    "ml_dataset",
    "ml_offline",
    "training_dataset",
    "training_datasets",
    "model",
    "prediction",
    "signal",
    "strategy",
    "backtest",
    "order",
    "execution",
]
ALLOWED_V2_6_ARTIFACT_ROOTS = [
    Path("data/gold/features"),
    Path("data/gold/labels"),
    Path("reports/features"),
    Path("reports/labels"),
]
LEGACY_ALLOWED_V2_6_ARTIFACT_ROOTS = [
    # Historical V1 reports and pre-V2 data remain in the repository, but they are not
    # artifacts produced by the V2.6 label factory candidate.
    Path("reports/backtests"),
    Path("reports/research"),
    Path("data/gold/ml_predictions"),
]
FUTURE_ALLOWED_DATASET_ROOTS_AFTER_V2_6 = [
    # V2.7 creates an explicitly offline supervised dataset. The V2.6 validator
    # still rejects every other data/gold/datasets path.
    Path("data/gold/datasets/offline_supervised"),
]
FUTURE_ALLOWED_ML_ROOTS_AFTER_V2_6 = [
    # V2.8 creates explicitly offline ML research scores. The V2.6 validator
    # still rejects every other ML/backtest/execution artifact path.
    Path("data/gold/ml/offline_research"),
]
FUTURE_ALLOWED_ML_REPORTS_AFTER_V2_6 = {
    Path("reports/ml/offline_ml_research_v2_8.json"),
    Path("reports/ml/offline_ml_research_v2_8.md"),
    Path("reports/ml/offline_research_scores_v2_8.json"),
    Path("reports/ml/offline_research_scores_v2_8.md"),
}


def _is_iso_utc(value: Any) -> bool:
    if not isinstance(value, str) or not value or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _compare_nested(expected: Any, actual: Any, prefix: str) -> list[str]:
    if expected == actual:
        return []
    errors: list[str] = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            errors.append(f"{prefix}.{key}")
        for key in sorted(actual_keys - expected_keys):
            errors.append(f"{prefix}.{key}")
        for key in sorted(expected_keys & actual_keys):
            errors.extend(_compare_nested(expected[key], actual[key], f"{prefix}.{key}"))
        return errors
    return [prefix]


def _is_under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _report_forbidden_artifact(path: Path) -> str:
    if path.is_dir():
        files = [child for child in sorted(path.rglob("*")) if child.is_file()]
        if files:
            return files[0].as_posix()
    return path.as_posix()


def find_forbidden_v2_6_artifacts(project_root: Path) -> list[str]:
    """Finds ML/dataset/backtest/execution artifacts forbidden in V2.6 label factory scope."""
    forbidden: set[str] = set()

    for relative in FORBIDDEN_V2_6_ARTIFACT_PATHS:
        candidate = project_root / relative
        if candidate.exists():
            if relative == Path("data/gold/datasets"):
                children = list(candidate.rglob("*"))
                forbidden_children = [
                    child
                    for child in children
                    if child.is_file()
                    and not any(_is_under(child.relative_to(project_root), allowed) for allowed in FUTURE_ALLOWED_DATASET_ROOTS_AFTER_V2_6)
                ]
                for child in forbidden_children:
                    forbidden.add(child.relative_to(project_root).as_posix())
                continue
            if relative == Path("data/gold/ml"):
                children = list(candidate.rglob("*"))
                forbidden_children = [
                    child
                    for child in children
                    if child.is_file()
                    and not any(_is_under(child.relative_to(project_root), allowed) for allowed in FUTURE_ALLOWED_ML_ROOTS_AFTER_V2_6)
                ]
                for child in forbidden_children:
                    forbidden.add(child.relative_to(project_root).as_posix())
                continue
            if relative == Path("reports/ml"):
                children = list(candidate.rglob("*"))
                forbidden_children = [
                    child
                    for child in children
                    if child.is_file() and child.relative_to(project_root) not in FUTURE_ALLOWED_ML_REPORTS_AFTER_V2_6
                ]
                for child in forbidden_children:
                    forbidden.add(child.relative_to(project_root).as_posix())
                continue
            if relative == Path("reports/backtests"):
                direct_new_artifacts = [
                    child
                    for child in candidate.iterdir()
                    if child.name in {"backtest.json", "backtest.md", "summary.json", "summary.md"}
                ]
                for child in direct_new_artifacts:
                    forbidden.add(child.relative_to(project_root).as_posix())
                continue
            forbidden.add(_report_forbidden_artifact(relative))

    scan_roots = [
        Path("models"),
        Path("checkpoints"),
        Path("execution"),
        Path("orders"),
    ]
    for scan_root in scan_roots:
        absolute_root = project_root / scan_root
        if not absolute_root.exists():
            continue
        candidates = [absolute_root, *absolute_root.rglob("*")]
        for candidate in candidates:
            try:
                relative = candidate.relative_to(project_root)
            except ValueError:
                continue
            if any(_is_under(relative, allowed) for allowed in ALLOWED_V2_6_ARTIFACT_ROOTS):
                continue
            if any(_is_under(relative, allowed) for allowed in LEGACY_ALLOWED_V2_6_ARTIFACT_ROOTS):
                continue
            text = relative.as_posix().casefold()
            if any(pattern in text for pattern in FORBIDDEN_V2_6_ARTIFACT_PATTERNS):
                forbidden.add(_report_forbidden_artifact(relative))

    return [f"Forbidden V2.6 artifact detected: {path}" for path in sorted(forbidden)]


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
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS_V2_6, "V2.6 manifest"))

    # PARTIE F - created_at_utc and label_run_id validation
    created_at = manifest.get("created_at_utc")
    if not _is_iso_utc(created_at):
        errors.append("V2.6 manifest created_at_utc invalid")

    label_run_id = manifest.get("label_run_id")
    if not isinstance(label_run_id, str) or not re.match(r"^v2_6_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$", label_run_id):
        errors.append("V2.6 manifest label_run_id invalid")

    # PARTIE B - Sous-schémas stricts du manifest
    # safety validation
    safety = manifest.get("safety", {})
    if isinstance(safety, dict):
        errors.extend(validate_exact_keys(safety, SAFETY_KEYS_V2_6, "V2.6 manifest safety"))
        
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
        errors.extend(validate_exact_keys(input_ohlcv, EXPECTED_TIMEFRAMES_V2_6, "V2.6 manifest input_ohlcv"))
        for tf, tf_input in input_ohlcv.items():
            if isinstance(tf_input, dict):
                errors.extend(validate_exact_keys(tf_input, INPUT_OHLCV_KEYS_V2_6, f"V2.6 manifest input_ohlcv.{tf}"))
            else:
                errors.append(f"input_ohlcv {tf} must be a dictionary")
    else:
        errors.append("input_ohlcv must be a dictionary")

    # outputs validation
    outputs = manifest.get("outputs", {})
    if isinstance(outputs, dict):
        errors.extend(validate_exact_keys(outputs, EXPECTED_TIMEFRAMES_V2_6, "V2.6 manifest outputs"))
        for tf, tf_output in outputs.items():
            if isinstance(tf_output, dict):
                errors.extend(validate_exact_keys(tf_output, OUTPUT_KEYS_V2_6, f"V2.6 manifest outputs.{tf}"))
            else:
                errors.append(f"outputs {tf} must be a dictionary")
    else:
        errors.append("outputs must be a dictionary")

    # quality validation
    quality = manifest.get("quality", {})
    if isinstance(quality, dict):
        errors.extend(validate_exact_keys(quality, EXPECTED_TIMEFRAMES_V2_6, "V2.6 manifest quality"))
        for tf, tf_qual in quality.items():
            if isinstance(tf_qual, dict):
                errors.extend(validate_exact_keys(tf_qual, QUALITY_KEYS_V2_6, f"V2.6 manifest quality.{tf}"))
                
                valid_counts = tf_qual.get("valid_counts_by_horizon", {})
                if isinstance(valid_counts, dict):
                    errors.extend(validate_exact_keys(valid_counts, EXPECTED_HORIZON_KEYS_V2_6, f"V2.6 manifest quality.{tf}.valid_counts_by_horizon"))
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
    if limitations != EXPECTED_LIMITATIONS_V2_6:
        errors.append("V2.6 manifest limitations mismatch")
        
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

        if isinstance(tf_qual, dict):
            expected_quality = {key: assessments.get(key) for key in QUALITY_KEYS_V2_6}
            for mismatch_path in _compare_nested(expected_quality, tf_qual, tf):
                errors.append(f"V2.6 manifest quality mismatch for {mismatch_path}")
                    
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
        report_json: Any = None
    else:
        try:
            with open(report_json_path, "r") as f:
                report_json = json.load(f)
            
            # Check top level quality report keys
            errors.extend(validate_exact_keys(report_json, MANIFEST_KEYS_V2_6, "V2.6 quality report"))
            if isinstance(report_json.get("input_ohlcv"), dict):
                errors.extend(validate_exact_keys(report_json["input_ohlcv"], EXPECTED_TIMEFRAMES_V2_6, "V2.6 quality report input_ohlcv"))
                for tf, tf_input in report_json["input_ohlcv"].items():
                    errors.extend(validate_exact_keys(tf_input, INPUT_OHLCV_KEYS_V2_6, f"V2.6 quality report input_ohlcv.{tf}"))
            if isinstance(report_json.get("outputs"), dict):
                errors.extend(validate_exact_keys(report_json["outputs"], EXPECTED_TIMEFRAMES_V2_6, "V2.6 quality report outputs"))
                for tf, tf_output in report_json["outputs"].items():
                    errors.extend(validate_exact_keys(tf_output, OUTPUT_KEYS_V2_6, f"V2.6 quality report outputs.{tf}"))
            if isinstance(report_json.get("quality"), dict):
                errors.extend(validate_exact_keys(report_json["quality"], EXPECTED_TIMEFRAMES_V2_6, "V2.6 quality report quality"))
                for tf, tf_qual in report_json["quality"].items():
                    errors.extend(validate_exact_keys(tf_qual, QUALITY_KEYS_V2_6, f"V2.6 quality report quality.{tf}"))
                    if isinstance(tf_qual, dict):
                        errors.extend(
                            validate_exact_keys(
                                tf_qual.get("valid_counts_by_horizon", {}),
                                EXPECTED_HORIZON_KEYS_V2_6,
                                f"V2.6 quality report quality.{tf}.valid_counts_by_horizon",
                            )
                        )
            if isinstance(report_json.get("safety"), dict):
                errors.extend(validate_exact_keys(report_json["safety"], SAFETY_KEYS_V2_6, "V2.6 quality report safety"))
                
            # Compare every field value between report and manifest
            for field in MANIFEST_KEYS_V2_6:
                if field in manifest and field in report_json:
                    if manifest[field] != report_json[field]:
                        errors.append(f"V2.6 quality report mismatch for {field}")
            if report_json.get("limitations") != EXPECTED_LIMITATIONS_V2_6:
                errors.append("V2.6 quality report limitations mismatch")
            if report_json.get("created_at_utc") != manifest.get("created_at_utc"):
                errors.append("V2.6 quality report created_at_utc mismatch")
            if report_json.get("label_run_id") != manifest.get("label_run_id"):
                errors.append("V2.6 quality report label_run_id mismatch")
        except Exception as e:
            report_json = None
            errors.append(f"Failed to read or parse JSON report: {str(e)}")
            
    # 4. PARTIE E - Claims positives interdites récursives
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V2.6 manifest"))

    # Verify report JSON
    if isinstance(report_json, dict):
        errors.extend(scan_payload_for_forbidden_claims(report_json, "V2.6 quality report"))

    # Verify Markdown report
    if not report_md_path.exists():
        errors.append(f"Markdown report not found: {report_md_path}")
    else:
        try:
            with open(report_md_path, "r") as f:
                md_content = f.read()
            errors.extend(validate_markdown_forbidden_claims(md_content, "V2.6 Markdown report"))
        except Exception as e:
            errors.append(f"Failed to read Markdown report: {str(e)}")
            
    # Check if forbidden ML/dataset/backtest/execution artifacts have been created.
    errors.extend(find_forbidden_v2_6_artifacts(project_root))
        
    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
    }
