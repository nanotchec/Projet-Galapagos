"""Analysis of quality mask impact."""
import pandas as pd
from typing import Dict, Any

class MaskImpactAnalysis:
    def run(self, df: pd.DataFrame, masks: Dict[str, pd.Series]) -> Dict[str, Any]:
        usable = masks["usable_mask"]
        blocked = masks["blocked_mask"]
        
        total_rows = len(df)
        usable_rows = usable.sum()
        blocked_rows = blocked.sum()
        
        impact = {
            "total_rows": int(total_rows),
            "usable_rows": int(usable_rows),
            "blocked_rows": int(blocked_rows),
            "usable_ratio": float(usable_rows / total_rows) if total_rows > 0 else 0,
            "blocked_ratio": float(blocked_rows / total_rows) if total_rows > 0 else 0,
        }
        
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])
            for year in [2024, 2025, 2026]:
                year_mask = ts.dt.year == year
                if year_mask.any():
                    year_total = year_mask.sum()
                    year_usable = (usable & year_mask).sum()
                    impact[f"usable_ratio_{year}"] = float(year_usable / year_total)
                    impact[f"blocked_ratio_{year}"] = float(1 - (year_usable / year_total))
        
        return impact
