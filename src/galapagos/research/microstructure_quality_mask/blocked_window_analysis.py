"""Analysis of usable and blocked windows."""
import pandas as pd
from typing import Dict, Any, List

class WindowAnalysis:
    def analyze_usable(self, df: pd.DataFrame, mask: pd.Series) -> Dict[str, Any]:
        if "timestamp" not in df.columns:
            return {"status": "NO_TIMESTAMP_COLUMN"}
            
        ts = pd.to_datetime(df["timestamp"])
        usable_ts = ts[mask]
        
        if usable_ts.empty:
            return {"status": "NO_USABLE_WINDOWS", "windows": []}
            
        return {
            "status": "USABLE_WINDOWS_IDENTIFIED",
            "start": str(usable_ts.min()),
            "end": str(usable_ts.max()),
            "count": int(mask.sum())
        }

    def analyze_blocked(self, df: pd.DataFrame, mask: pd.Series) -> Dict[str, Any]:
        if "timestamp" not in df.columns:
            return {"status": "NO_TIMESTAMP_COLUMN"}
            
        ts = pd.to_datetime(df["timestamp"])
        blocked_ts = ts[mask]
        
        if blocked_ts.empty:
            return {"status": "NO_BLOCKED_WINDOWS", "windows": []}
            
        # Group by year/month for a summary
        blocked_summary = blocked_ts.dt.to_period("M").value_counts().sort_index()
        
        return {
            "status": "BLOCKED_WINDOWS_IDENTIFIED",
            "count": int(mask.sum()),
            "summary": {str(k): int(v) for k, v in blocked_summary.items()}
        }
