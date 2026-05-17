"""Analyze feature inventory for V1.43."""
from __future__ import annotations

import pandas as pd
from typing import Any
from .feature_family_mapper import map_feature_to_family, map_feature_to_source_type

def analyze_feature_inventory(df: pd.DataFrame) -> dict[str, Any]:
    """List and classify all available columns with strict source semantics."""
    cols = df.columns.tolist()
    inventory = []
    
    for c in cols:
        family = map_feature_to_family(c)
        source_type = map_feature_to_source_type(c)
        
        is_forbidden = source_type == "outcome_forbidden_feature"
        is_metadata = source_type == "metadata_feature"
        
        # Sémantique V1.43.3 Strict
        inventory.append({
            "column": c,
            "family": family,
            "source_type": source_type,
            "is_usable_for_raw_feature_engineering": source_type in ["raw_market_feature", "regime_proxy_feature"],
            "is_usable_for_alpha_feature_engineering": source_type == "alpha_score_feature",
            "is_usable_for_model_output_diagnostic": source_type == "model_output_feature",
            "is_usable_for_ev_proxy_diagnostic": source_type == "ev_proxy_feature",
            "is_metadata": is_metadata,
            "is_forbidden_outcome": is_forbidden,
            "forbidden_reason": "FUTURE_OR_POST_TRADE_OUTCOME" if is_forbidden else None
        })
        
    inv_df = pd.DataFrame(inventory)
    source_counts = inv_df["source_type"].value_counts().to_dict()
    family_counts = inv_df["family"].value_counts().to_dict()
    
    # Strictly filtered lists
    raw_market = inv_df[inv_df["source_type"] == "raw_market_feature"]["column"].tolist()
    alpha_scores = inv_df[inv_df["source_type"] == "alpha_score_feature"]["column"].tolist()
    model_outputs = inv_df[inv_df["source_type"] == "model_output_feature"]["column"].tolist()
    ev_proxies = inv_df[inv_df["source_type"] == "ev_proxy_feature"]["column"].tolist()
    metadata = inv_df[inv_df["source_type"] == "metadata_feature"]["column"].tolist()
    regimes = inv_df[inv_df["source_type"] == "regime_proxy_feature"]["column"].tolist()
    forbidden = inv_df[inv_df["source_type"] == "outcome_forbidden_feature"]["column"].tolist()
    
    usable_raw = raw_market + regimes
    usable_alpha = alpha_scores
    
    return {
        "inventory_status": "REGIME_FEATURE_INVENTORY_COMPLETE_WITH_STRICT_SOURCE_SEMANTICS",
        "total_columns": len(cols),
        "raw_market_feature_count": len(raw_market),
        "alpha_score_feature_count": len(alpha_scores),
        "model_output_feature_count": len(model_outputs),
        "ev_proxy_feature_count": len(ev_proxies),
        "metadata_feature_count": len(metadata),
        "regime_proxy_feature_count": len(regimes),
        "outcome_like_feature_exclusion_count": len(forbidden),
        
        "usable_raw_features": usable_raw,
        "usable_alpha_features": usable_alpha,
        "diagnostic_only_model_output_features": model_outputs,
        "diagnostic_only_ev_proxy_features": ev_proxies,
        
        "usable_raw_feature_count": len(usable_raw),
        "usable_alpha_feature_count": len(usable_alpha),
        "usable_model_output_diagnostic_count": len(model_outputs),
        "usable_ev_proxy_diagnostic_count": len(ev_proxies),
        
        "source_type_counts": source_counts,
        "family_counts": family_counts,
        
        "raw_market_features": raw_market,
        "alpha_score_features": alpha_scores,
        "model_output_features": model_outputs,
        "ev_proxy_features": ev_proxies,
        "metadata_features": metadata,
        "regime_proxy_features": regimes,
        "outcome_forbidden_features": forbidden,
        
        "usable_features": usable_raw + usable_alpha, # For backward compatibility in older analysis steps
        "outcome_like_features_excluded": True,
        "model_outputs_separated_from_raw_features": True,
        "ev_proxies_separated_from_raw_features": True,
        "metadata_separated_from_raw_features": True,
        "all_metadata": inventory
    }
