"""Analysis of feature retention under quality mask."""
from typing import Dict, Any, List
import pandas as pd

class FeatureRetentionAnalysis:
    def run(self, df: pd.DataFrame, mask: pd.Series, features: List[str]) -> Dict[str, Any]:
        retention = {}
        for f in features:
            if f in df.columns:
                # Check how many valid values are in the usable mask
                usable_data = df.loc[mask, f]
                total_usable = len(usable_data)
                valid_usable = usable_data.notna().sum()
                retention[f] = {
                    "valid_ratio": float(valid_usable / total_usable) if total_usable > 0 else 0,
                    "status": "RETAINED" if (valid_usable / total_usable if total_usable > 0 else 0) > 0.9 else "REWORK_REQUIRED"
                }
            else:
                retention[f] = {"status": "MISSING_IN_DATASET", "valid_ratio": 0.0}
        
        return {
            "feature_retention": retention,
            "retained_features": [f for f, v in retention.items() if v["status"] == "RETAINED"],
            "reworked_features": [f for f, v in retention.items() if v["status"] == "REWORK_REQUIRED"],
            "blocked_features": [f for f, v in retention.items() if v["status"] == "MISSING_IN_DATASET"]
        }
