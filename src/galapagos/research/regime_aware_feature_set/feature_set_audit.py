"""Feature set audit for V1.44 research."""
from __future__ import annotations

from typing import Any
from .feature_source_contract import is_column_allowed

def audit_feature_set(
    set_name: str,
    feature_list: list[str],
    inventory: dict[str, Any]
) -> dict[str, Any]:
    """Audit a single feature set for compliance."""
    
    forbidden_cols = []
    unknown_cols = []
    
    source_map = {m["column"]: m["source_type"] for m in inventory.get("all_metadata", [])}
    
    for col in feature_list:
        if col not in source_map:
            # Check if it's a known derived suffix from our builders
            is_derived = any(suffix in col for suffix in ["_excess", "_vol_scaled", "_zscore_24h", "_delta_3h", "_interaction"])
            if not is_derived:
                unknown_cols.append(col)
            continue
            
        if not is_column_allowed(col, inventory):
            forbidden_cols.append({
                "column": col,
                "source_type": source_map[col]
            })
            
    passed = len(forbidden_cols) == 0 and len(unknown_cols) == 0
    
    return {
        "set_name": set_name,
        "passed": passed,
        "feature_count": len(feature_list),
        "forbidden_cols": forbidden_cols,
        "unknown_cols": unknown_cols,
        "audit_verdict": "PASSED" if passed else "FAILED"
    }

def audit_all_feature_sets(
    feature_sets: dict[str, list[str]],
    inventory: dict[str, Any]
) -> dict[str, Any]:
    """Audit all candidate feature sets."""
    
    results = {}
    all_passed = True
    
    for name, flist in feature_sets.items():
        audit_res = audit_feature_set(name, flist, inventory)
        results[name] = audit_res
        if not audit_res["passed"]:
            all_passed = False
            
    return {
        "status": "FEATURE_SET_AUDIT_COMPLETE",
        "all_passed": all_passed,
        "results": results
    }
