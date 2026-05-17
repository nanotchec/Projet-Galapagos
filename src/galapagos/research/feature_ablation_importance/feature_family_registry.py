"""Feature family registry for V1.45."""
from __future__ import annotations

import pandas as pd
from typing import Any

def get_feature_family_registry(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Group available columns into logical feature families."""
    
    all_cols = set(df.columns)
    
    # Simple rule-based classification for research
    families = [
        {
            "family_name": "microstructure",
            "source_type": "raw_market_feature",
            "keywords": ["bid", "ask", "spread", "depth", "order_imbalance"],
        },
        {
            "family_name": "price_return",
            "source_type": "raw_market_feature",
            "keywords": ["return", "log_ret", "close_diff"],
        },
        {
            "family_name": "regime_proxy",
            "source_type": "regime_proxy_feature",
            "keywords": ["regime", "vix", "vol_state"],
        },
        {
            "family_name": "trend_momentum",
            "source_type": "derived_causal_feature",
            "keywords": ["rsi", "macd", "ema", "sma", "momentum"],
        },
        {
            "family_name": "volatility",
            "source_type": "raw_market_feature",
            "keywords": ["volatility", "atr", "std_dev"],
        },
        {
            "family_name": "volume_liquidity",
            "source_type": "raw_market_feature",
            "keywords": ["volume", "turnover", "liquidity"],
        },
        {
            "family_name": "alpha_score_family",
            "source_type": "alpha_score_feature",
            "keywords": ["alpha", "score"],
        },
        {
            "family_name": "interactions_regime_feature",
            "source_type": "derived_causal_feature",
            "keywords": ["interaction", "scaled_by"],
        },
    ]
    
    registry = []
    for fam in families:
        matched = [c for c in all_cols if any(k in c.lower() for k in fam["keywords"])]
        if matched:
            registry.append({
                "family_name": fam["family_name"],
                "source_type": fam["source_type"],
                "feature_count": len(matched),
                "feature_names": sorted(matched),
                "allowed_by_contract": True,
                "diagnostic_role": f"Measure impact of {fam['family_name']} signals."
            })
            all_cols -= set(matched)
            
    # Catch-all for remaining (optional)
    if all_cols:
        registry.append({
            "family_name": "other_remaining",
            "source_type": "unknown",
            "feature_count": len(all_cols),
            "feature_names": sorted(list(all_cols)),
            "allowed_by_contract": True,
            "diagnostic_role": "Catch-all for miscellaneous features."
        })
        
    return registry
