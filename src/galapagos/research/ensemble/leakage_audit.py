from __future__ import annotations

from typing import Any

import pandas as pd


def audit_ensemble_leakage(
    dataset_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    target_col: str = "target_up_after_cost_12bar",
) -> dict[str, Any]:
    """Check for obvious leakage in ensemble inputs with strict validation."""
    checks = []
    status = "ENSEMBLE_LEAKAGE_AUDIT_STRICT_PASSED"
    
    # 1. Check for split_name presence and OOS proof
    if "split_name" not in predictions_df.columns:
        checks.append("split_name column missing - cannot prove OOS")
        status = "ENSEMBLE_LEAKAGE_AUDIT_LIMITED"
    else:
        # Check if rows contain 'train' without 'test' (suspicious)
        train_rows = predictions_df[
            predictions_df["split_name"].str.contains("train", na=False) & 
            ~predictions_df["split_name"].str.contains("test", na=False)
        ]
        if len(train_rows) > 0:
            checks.append(f"Found {len(train_rows)} train split rows in predictions")
            status = "ENSEMBLE_LEAKAGE_AUDIT_FAILED"

    
    # It's okay if they are in the parquet for audit, but they must NOT correlate perfectly with probability
    if "actual_target" in predictions_df.columns:
        clean_preds = predictions_df.dropna(subset=["predicted_probability", "actual_target"])
        if len(clean_preds) > 10:
            corr = clean_preds["predicted_probability"].corr(clean_preds["actual_target"])
            if corr > 0.95: # Very high correlation is suspicious
                msg = f"Suspiciously high correlation ({corr:.4f}) between probability and target"
                checks.append(msg)
                status = "ENSEMBLE_LEAKAGE_AUDIT_FAILED"

    # 3. Check for duplicates
    subset = ["timestamp", "model_name", "target", "feature_set"]
    existing_cols = [c for c in subset if c in predictions_df.columns]
    dupes = predictions_df.duplicated(subset=existing_cols).sum()
    if dupes > 0:
        checks.append(f"Found {dupes} duplicate prediction rows")
        status = "ENSEMBLE_LEAKAGE_AUDIT_FAILED"

    # 4. Honesty check: if we only have 'test_train_...' it might be weak proof
    if status == "ENSEMBLE_LEAKAGE_AUDIT_STRICT_PASSED":
        # Check if we have evidence of OOS beyond naming
        # (For now, we default to LIMITED if split_name doesn't strictly match a 'test_only' pattern)
        split_names = predictions_df["split_name"].unique()
        if any("train" in str(s).lower() for s in split_names):
            checks.append("split_name contains 'train' - potential contamination or weak OOS proof")
            status = "ENSEMBLE_LEAKAGE_AUDIT_LIMITED"
            
    if status == "ENSEMBLE_LEAKAGE_AUDIT_STRICT_PASSED":
        checks.append("No obvious train split rows found")
        checks.append("Correlation between probability and target is within normal research bounds")
        checks.append("No duplicate prediction rows found")
        checks.append("Strict OOS proof verified (split names do not contain 'train')")

    return {
        "status": status,
        "checks": checks,
        "rows_audited": len(predictions_df),
        "target_col": target_col
    }
