"""Feature set registry for V1.44 research."""
from __future__ import annotations

from typing import Any

def get_feature_set_definitions(inventory: dict[str, Any]) -> dict[str, list[str]]:
    """Define the candidate feature sets to be evaluated in V1.44."""
    
    # Extract columns by family from inventory
    family_map = {}
    for m in inventory.get("all_metadata", []):
        family = m.get("family", "unknown")
        if family not in family_map:
            family_map[family] = []
        family_map[family].append(m["column"])
        
    # Standard Families
    microstructure = family_map.get("microstructure", [])
    price_return = family_map.get("price_return", [])
    trend_momentum = family_map.get("trend_momentum", [])
    volatility = family_map.get("volatility", [])
    volume_liquidity = family_map.get("volume_liquidity", [])
    regime_proxy = family_map.get("regime_proxy", [])
    alpha_score = family_map.get("alpha_score_family", [])
    
    # Define Sets
    feature_sets = {
        "v1_38_core_baseline": microstructure + price_return + trend_momentum + volatility + volume_liquidity,
        "v1_44_regime_aware_raw": microstructure + price_return + trend_momentum + volatility + volume_liquidity + regime_proxy,
        "v1_44_alpha_only": alpha_score,
        "v1_44_combined_regime_alpha": microstructure + price_return + trend_momentum + volatility + volume_liquidity + regime_proxy + alpha_score,
        "v1_44_derivatives_heavy": [c for c in regime_proxy if "funding" in c or "oi" in c or "premium" in c] + price_return,
        "v1_44_macro_heavy": [c for c in regime_proxy if "macro" in c or "equity" in c] + price_return
    }
    
    return feature_sets
