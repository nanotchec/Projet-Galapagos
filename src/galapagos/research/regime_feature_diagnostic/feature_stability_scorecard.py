"""Generate feature stability scorecard for V1.43."""
from __future__ import annotations

import pandas as pd
from typing import Any
from .feature_family_mapper import map_feature_to_family, map_feature_to_source_type

def generate_stability_scorecard(
    shifts: dict[str, Any],
    decays: dict[str, Any],
    interactions: dict[str, Any],
    usable_features: list[str]
) -> dict[str, Any]:
    """Classify features based on their stability and predictive power in 2026."""
    
    shift_map = {s["feature"]: s["drift_score"] for s in shifts.get("shifts", [])}
    decay_map = {d["feature"]: d for d in decays.get("decay_results", [])}
    unstable_in_regime = {i["feature"] for i in interactions.get("unstable_features_in_dominant_regime", [])}
    
    scorecard = []
    for feat in usable_features:
        family = map_feature_to_family(feat)
        source_type = map_feature_to_source_type(feat)
        drift = shift_map.get(feat, 0.0)
        decay = decay_map.get(feat, {})
        is_unstable_regime = feat in unstable_in_regime
        
        # Stability Classification Logic
        stability_class = "STABLE_CANDIDATE"
        if drift > 1.0:
            stability_class = "UNSTABLE_SHIFTED"
        elif decay.get("sign_flip"):
            stability_class = "DECAYED_PREDICTIVE_POWER"
        elif is_unstable_regime:
            stability_class = "REGIME_DEPENDENT"
        elif drift > 0.5 or decay.get("abs_delta", 0) > 0.02:
            stability_class = "MODERATELY_UNSTABLE"
            
        scorecard.append({
            "feature": feat,
            "family": family,
            "source_type": source_type,
            "drift_score": drift,
            "abs_decay_delta": decay.get("abs_delta", 0.0),
            "sign_flip": decay.get("sign_flip", False),
            "is_unstable_regime": is_unstable_regime,
            "stability_class": stability_class
        })
        
    score_df = pd.DataFrame(scorecard)
    family_summary = score_df.groupby("family")["stability_class"].value_counts().unstack().fillna(0).to_dict(orient="index")
    
    # Filter for recommendations
    raw_df = score_df[score_df["source_type"] == "raw_market_feature"]
    alpha_df = score_df[score_df["source_type"] == "alpha_score_feature"]
    model_df = score_df[score_df["source_type"] == "model_output_feature"]
    ev_proxy_df = score_df[score_df["source_type"] == "ev_proxy_feature"]
    
    stable_raw_candidates = raw_df[raw_df["stability_class"] == "STABLE_CANDIDATE"]["feature"].tolist()
    stable_alpha_candidates = alpha_df[alpha_df["stability_class"] == "STABLE_CANDIDATE"]["feature"].tolist()
    
    # Strictly filter families
    forbidden_raw_families = [
        "metadata", "metadata_feature", "model_output_feature", "ev_proxy_feature", 
        "alpha_score_or_model_output", "alpha_score_family", "unknown", "model_output_family",
        "target_outcome_forbidden"
    ]
    
    recommended_raw = [f for f, s in family_summary.items() 
                       if f not in forbidden_raw_families 
                       and s.get("STABLE_CANDIDATE", 0) > 0]
                       
    # If recommended_raw is empty, use a safe default of well-known families if they exist in summary
    if not recommended_raw:
        safe_defaults = ["volatility", "trend_momentum", "price_return", "volume_liquidity", "microstructure", "regime_proxy"]
        recommended_raw = [f for f in safe_defaults if f in family_summary]

    recommended_alpha = [f for f, s in family_summary.items() 
                         if f == "alpha_score_family"
                         and s.get("STABLE_CANDIDATE", 0) > 0]
    
    problematic_families = [f for f, s in family_summary.items() if s.get("UNSTABLE_SHIFTED", 0) + s.get("DECAYED_PREDICTIVE_POWER", 0) > 5]
    
    return {
        "feature_stability_scorecard_status": "FEATURE_STABILITY_SCORECARD_COMPLETE",
        "family_summary": family_summary,
        "stable_candidate_count": len(stable_raw_candidates) + len(stable_alpha_candidates),
        "stable_raw_candidate_features": stable_raw_candidates[:50],
        "stable_alpha_candidate_features": stable_alpha_candidates[:50],
        "unstable_feature_count": len(score_df) - (len(stable_raw_candidates) + len(stable_alpha_candidates)),
        "recommended_raw_feature_families_for_v1_44": recommended_raw,
        "recommended_alpha_feature_families_for_v1_44": recommended_alpha,
        "diagnostic_only_model_output_features": model_df["feature"].tolist(),
        "diagnostic_only_ev_proxy_features": ev_proxy_df["feature"].tolist(),
        "avoid_feature_families_for_v1_44": problematic_families,
        "model_outputs_excluded_from_raw_feature_recommendations": True,
        "ev_proxies_excluded_from_raw_feature_recommendations": True,
        "metadata_excluded_from_raw_feature_recommendations": True,
        "alpha_score_or_model_output_removed": True
    }
