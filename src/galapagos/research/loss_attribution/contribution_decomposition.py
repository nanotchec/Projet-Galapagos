from __future__ import annotations

from typing import Any


def decompose_contributions(all_verdicts_by_policy: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Rank the primary drivers of loss globally and per policy."""
    
    by_policy_drivers = {}
    global_counts = {}
    
    for p_name, verdicts in all_verdicts_by_policy.items():
        policy_drivers = _extract_drivers(verdicts)
        by_policy_drivers[p_name] = policy_drivers
        
        # Track frequency of drivers for global synthesis
        for d in policy_drivers:
            d_name = d["driver"]
            global_counts[d_name] = global_counts.get(d_name, 0) + 1
            
    # Global synthesis: drivers that appear in most policies are higher rank
    sorted_global = sorted(global_counts.items(), key=lambda x: x[1], reverse=True)
    global_drivers = []
    for d_name, count in sorted_global:
        conf = "strong" if count == len(all_verdicts_by_policy) else "moderate"
        global_drivers.append({"driver": d_name, "confidence": conf})
        
    if not global_drivers:
        global_drivers.append({"driver": "weak_diffuse_signal", "confidence": "moderate"})
        
    # Evidence summary
    evidence = "Consensus across policies." if len(global_drivers) > 0 and global_drivers[0]["confidence"] == "strong" else "Divergent policy drivers."
    
    # Recommendations based on global drivers
    primary = global_drivers[0]["driver"]
    next_exp = "Build stronger signal selection before exit optimization."
    do_not_do = ["Do not activate LLM reviewer.", "Do not execute holdout.", "Do not trade live."]
    
    if primary == "no_gross_edge":
        next_exp = "Fundamental signal overhaul; current features lack predictive power."
    elif primary == "costs_dominate":
        next_exp = "Seek higher volatility setups or reduce trade frequency to outrun costs."
    elif primary == "exit_policy_bad":
        next_exp = "Optimize TP/SL levels on existing signals."
        
    return {
        "global_ranked_loss_drivers": global_drivers,
        "by_policy_loss_drivers": by_policy_drivers,
        "evidence": evidence,
        "confidence": "strong" if evidence == "Consensus across policies." else "moderate",
        "suggested_next_experiment": next_exp,
        "do_not_do_next": do_not_do
    }

def _extract_drivers(verdicts: dict[str, str]) -> list[dict[str, str]]:
    """Helper to extract drivers for a single policy."""
    drivers = []
    
    # Priority 1: No gross edge or costs
    if verdicts.get("cost_attribution") == "NO_GROSS_EDGE":
        drivers.append({"driver": "no_gross_edge", "confidence": "strong"})
    elif verdicts.get("cost_attribution") == "COSTS_PRIMARY_LOSS_DRIVER":
        drivers.append({"driver": "costs_dominate", "confidence": "strong"})
        
    # Priority 2: Technical/Execution
    if verdicts.get("mae_mfe") == "MAE_TOO_HIGH_FOR_SIGNAL":
        drivers.append({"driver": "poor_entry_quality", "confidence": "moderate"})
    elif verdicts.get("mae_mfe") == "MFE_EXISTS_BUT_EXITS_FAIL":
        drivers.append({"driver": "exit_policy_bad", "confidence": "moderate"})
        
    # Priority 3: Market/Regime
    if verdicts.get("regimes") in ["HIGH_VOL_DESTROYS_EDGE", "DOWNTREND_UNPROFITABLE"]:
        drivers.append({"driver": "regime_dependency", "confidence": "moderate"})
        
    # Priority 4: Risk/Tail
    if verdicts.get("tail_risk") == "LOSSES_CONCENTRATED_IN_TAIL":
        drivers.append({"driver": "tail_losses", "confidence": "weak"})
        
    if not drivers:
        drivers.append({"driver": "weak_diffuse_signal", "confidence": "moderate"})
        
    return drivers
