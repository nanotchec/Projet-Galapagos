"""Profiling of missingness in microstructure features."""
from __future__ import annotations

import pandas as pd
from typing import Any

class MissingnessProfile:
    """Analyzes missing values in microstructure features."""
    
    def run(self, dataset: pd.DataFrame) -> dict[str, Any]:
        """Calculates missingness per feature."""
        known_features = ["amihud_illiquidity", "realized_vol_proxy", "volume_vol_ratio", "intraday_range"]
        micro_features = [c for c in dataset.columns if any(p in c for p in ["amihud", "realized", "vol_ratio", "intraday"])]
        
        # Add known features that are missing from columns as 100% missing
        for f in known_features:
            if f not in micro_features and f not in dataset.columns:
                micro_features.append(f)
                
        if not micro_features:
            return {
                "status": "NO_FEATURES_FOUND",
                "missingness_per_feature": {},
                "missingness_profile_status": "MICROSTRUCTURE_MISSINGNESS_PROFILE_COMPLETED"
            }
            
        missingness = {}
        for f in micro_features:
            if f in dataset.columns:
                missingness[f] = float(dataset[f].isnull().mean())
            else:
                missingness[f] = 1.0 # Completely missing if not in columns
        
        return {
            "status": "COMPLETED",
            "missingness_per_feature": missingness,
            "assessed_features_count": len(micro_features),
            "highly_missing_features": [k for k, v in missingness.items() if v > 0.1],
            "missingness_profile_status": "MICROSTRUCTURE_MISSINGNESS_PROFILE_COMPLETED"
        }
