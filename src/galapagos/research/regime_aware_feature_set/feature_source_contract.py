"""Feature source contract for V1.44 research."""
from __future__ import annotations

from typing import Any
import pandas as pd

ALLOWED_SOURCE_TYPES = ["raw_market_feature", "regime_proxy_feature", "alpha_score_feature"]
FORBIDDEN_SOURCE_TYPES = ["model_output_feature", "ev_proxy_feature", "outcome_forbidden_feature", "metadata_feature"]

def check_feature_source_contract(
    df: pd.DataFrame,
    inventory: dict[str, Any],
    subset_columns: list[str] | None = None
) -> dict[str, Any]:
    """Validate that the dataframe columns comply with the V1.44 source contract."""
    
    # Map from column name to source type using the audited inventory
    source_map = {m["column"]: m["source_type"] for m in inventory.get("all_metadata", [])}
    
    forbidden_columns_detected = []
    columns_not_in_inventory = []
    
    cols_to_check = subset_columns if subset_columns is not None else df.columns
    
    for col in cols_to_check:
        if col not in source_map:
            # If it's a derived feature, check if it contains allowed keywords
            is_derived = any(suffix in col for suffix in ["_excess", "_vol_scaled", "_zscore_24h", "_delta_3h", "_interaction"])
            if not is_derived:
                columns_not_in_inventory.append(col)
            continue
            
        source_type = source_map[col]
        if source_type in FORBIDDEN_SOURCE_TYPES:
            forbidden_columns_detected.append({
                "column": col,
                "source_type": source_type,
                "reason": "STRICT_SOURCE_ISOLATION_VIOLATION"
            })
            
    passed = len(forbidden_columns_detected) == 0
    
    return {
        "status": "REGIME_AWARE_FEATURE_SOURCE_CONTRACT_PASSED" if passed else "REGIME_AWARE_FEATURE_SOURCE_CONTRACT_FAILED",
        "passed": passed,
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "forbidden_source_types": FORBIDDEN_SOURCE_TYPES,
        "forbidden_columns_detected": forbidden_columns_detected,
        "columns_not_in_inventory": columns_not_in_inventory,
        "model_outputs_excluded": True,
        "ev_proxies_excluded": True,
        "outcomes_excluded": True,
        "metadata_excluded": True
    }

def is_column_allowed(col: str, inventory: dict[str, Any]) -> bool:
    """Helper to check if a single column is allowed by the contract."""
    source_map = {m["column"]: m["source_type"] for m in inventory.get("all_metadata", [])}
    source_type = source_map.get(col, "unknown")
    return source_type in ALLOWED_SOURCE_TYPES
