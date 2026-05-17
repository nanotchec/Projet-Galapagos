from __future__ import annotations

from typing import Any


def generate_recommendations(decomposition: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.23.1 recommendations based on loss decomposition."""
    
    global_drivers = decomposition.get("global_ranked_loss_drivers", [])
    if not global_drivers:
        primary = "weak_diffuse_signal"
    else:
        primary = global_drivers[0]["driver"]
    
    reco_map = {
        "no_gross_edge": "Improve directional ML signal before optimizing exits.",
        "costs_dominate": "Reduce trade frequency or seek higher volatility setups to outrun costs.",
        "poor_entry_quality": "Add entry filters based on volatility or regime to reduce initial MAE.",
        "exit_policy_bad": "Optimize TP/SL levels or implement trailing stops.",
        "regime_dependency": "Implement a global regime filter to disable trading in unfavorable conditions.",
        "tail_losses": "Implement stricter outlier-based stop loss or tail-risk filters.",
        "weak_diffuse_signal": "Total signal overhaul required; current alpha is too weak."
    }
    
    return {
        "primary_recommendation": reco_map.get(primary, "Continue research."),
        "secondary_recommendations": [
            "Test stricter confidence/regime filters offline only.",
            "Validate cost assumptions.",
            "Do not activate LLM reviewer yet.",
            "Do not execute holdout.",
            "Do not trade live."
        ],
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
