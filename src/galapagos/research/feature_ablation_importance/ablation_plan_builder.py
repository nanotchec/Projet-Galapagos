"""Ablation plan builder for V1.45."""
from __future__ import annotations

from typing import Any

def build_ablation_plan(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Define a set of ablation experiments based on feature families."""
    
    family_names = [f["family_name"] for f in registry]
    
    experiments = [
        {
            "experiment_name": "all_allowed_features",
            "included_families": family_names,
            "excluded_families": [],
            "hypothesis": "Full feature set baseline.",
        },
        {
            "experiment_name": "raw_only",
            "included_families": [f["family_name"] for f in registry if f["source_type"] == "raw_market_feature"],
            "excluded_families": [f["family_name"] for f in registry if f["source_type"] != "raw_market_feature"],
            "hypothesis": "Test performance without derived alpha or regime features.",
        },
        {
            "experiment_name": "alpha_only",
            "included_families": ["alpha_score_family"],
            "excluded_families": [f for f in family_names if f != "alpha_score_family"],
            "hypothesis": "Measure pure alpha score signal.",
        },
        {
            "experiment_name": "raw_without_microstructure",
            "included_families": [f for f in family_names if f != "microstructure" and f != "alpha_score_family"],
            "excluded_families": ["microstructure", "alpha_score_family"],
            "hypothesis": "Measure sensitivity to microstructure noise.",
        },
        {
            "experiment_name": "raw_plus_regime_interactions",
            "included_families": [f["family_name"] for f in registry if f["source_type"] in ["raw_market_feature", "interactions_regime_feature"]],
            "excluded_families": [f["family_name"] for f in registry if f["source_type"] not in ["raw_market_feature", "interactions_regime_feature"]],
            "hypothesis": "Test if regime interactions add value to raw features.",
        }
    ]
    
    # Finalize experiments with common flags
    for exp in experiments:
        exp["allowed_by_contract"] = True
        exp["no_trading_rule"] = True
        
    return experiments
