"""Detection of temporal gaps in intrabar data."""
from __future__ import annotations

import pandas as pd
from typing import Any

class GapDetection:
    """Detects gaps in time series data."""
    
    def run(self, intrabar: pd.DataFrame) -> dict[str, Any]:
        """Identifies short and long gaps."""
        if intrabar.empty:
            return {"status": "EMPTY_DATA", "gap_detection_status": "MICROSTRUCTURE_GAP_DETECTION_COMPLETED"}
            
        ts = pd.to_datetime(intrabar["timestamp"]).sort_values()
        diffs = ts.diff().dropna()
        
        # Expected diff is 5 minutes
        expected_diff = pd.Timedelta(minutes=5)
        gaps = diffs[diffs > expected_diff]
        
        long_gaps = gaps[gaps > pd.Timedelta(hours=4)]
        short_gaps = gaps[(gaps > expected_diff) & (gaps <= pd.Timedelta(hours=4))]
        
        return {
            "status": "COMPLETED",
            "total_gaps_count": len(gaps),
            "long_gaps_count": len(long_gaps),
            "short_gaps_count": len(short_gaps),
            "max_gap_duration_seconds": float(gaps.max().total_seconds()) if not gaps.empty else 0.0,
            "gap_detection_status": "MICROSTRUCTURE_GAP_DETECTION_COMPLETED"
        }
