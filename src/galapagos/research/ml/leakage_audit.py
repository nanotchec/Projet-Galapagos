"""Anti-leakage ML Audit."""
from __future__ import annotations

import pandas as pd


def audit_ml_leakage(
    dataset: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    train_idx: list[int],
    test_idx: list[int],
) -> dict[str, str]:
    """Audit the features and split for any leakage."""
    if not feature_cols:
        return {"status": "ML_LEAKAGE_RISK_FOUND", "reason": "no_features"}
        
    # Check 1: Target column in features
    if target_col in feature_cols:
        return {"status": "ML_FEATURE_COLUMNS_UNSAFE", "reason": "target_in_features"}
        
    # Check 2: Future/Forward in features
    forbidden_words = ["future", "forward", "target", "label", "next"]
    for col in feature_cols:
        col_lower = col.lower()
        if any(w in col_lower for w in forbidden_words):
            # Special exceptions if needed could go here
            return {
                "status": "ML_FEATURE_COLUMNS_UNSAFE",
                "reason": f"suspicious_column_name: {col}",
            }
            
    # Check 3: Overlap in indices
    train_set = set(train_idx)
    test_set = set(test_idx)
    if train_set.intersection(test_set):
        return {"status": "ML_SPLIT_UNSAFE", "reason": "train_test_overlap"}
        
    # Check 4: Chronological order
    if "timestamp" in dataset.columns:
        ts = pd.to_datetime(dataset["timestamp"], utc=True).values
        train_max = ts[train_idx].max() if len(train_idx) > 0 else 0
        test_min = ts[test_idx].min() if len(test_idx) > 0 else 0
        if train_max > test_min:
            return {"status": "ML_SPLIT_UNSAFE", "reason": "train_after_test_starts"}
            
    return {"status": "ML_LEAKAGE_AUDIT_PASSED", "reason": "all_checks_passed"}
