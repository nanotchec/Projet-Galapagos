"""Analysis of label reliability under quality mask."""
from typing import Dict, Any, List
import pandas as pd

class LabelReliabilityAnalysis:
    def run(self, df: pd.DataFrame, mask: pd.Series, labels: List[str]) -> Dict[str, Any]:
        reliability = {}
        for l in labels:
            if l in df.columns:
                usable_labels = df.loc[mask, l]
                total_usable = len(usable_labels)
                valid_usable = usable_labels.notna().sum()
                reliability[l] = {
                    "valid_ratio": float(valid_usable / total_usable) if total_usable > 0 else 0,
                    "status": "RELIABLE" if (valid_usable / total_usable if total_usable > 0 else 0) > 0.95 else "UNRELIABLE"
                }
            else:
                reliability[l] = {"status": "MISSING_IN_DATASET", "valid_ratio": 0.0}
                
        return {
            "label_reliability": reliability,
            "reliable_labels": [l for l, v in reliability.items() if v["status"] == "RELIABLE"],
            "unreliable_labels": [l for l, v in reliability.items() if v["status"] != "RELIABLE"]
        }
