"""Audit of intrabar coverage for microstructure research."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

class IntrabarCoverageAudit:
    """Audits temporal coverage of intrabar data."""
    
    def run(self, dataset: pd.DataFrame, intrabar: pd.DataFrame) -> dict[str, Any]:
        """Calculates coverage metrics."""
        # This is a research-only diagnostic audit
        # We check how many 5m candles exist for each 4h window
        
        # Ensure timestamps are datetime
        if not pd.api.types.is_datetime64_any_dtype(dataset.index):
            if "timestamp" in dataset.columns:
                dataset = dataset.set_index("timestamp")
            dataset.index = pd.to_datetime(dataset.index)
            
        if not pd.api.types.is_datetime64_any_dtype(intrabar["timestamp"]):
            intrabar["timestamp"] = pd.to_datetime(intrabar["timestamp"])
            
        # For each row in dataset (4h), count 5m candles in the previous 4h
        coverage_stats = []
        for ts in dataset.index:
            start_window = ts - pd.Timedelta(hours=4)
            end_window = ts
            
            mask = (intrabar["timestamp"] > start_window) & (intrabar["timestamp"] <= end_window)
            count = mask.sum()
            
            # Expected: 4h / 5m = 48 candles
            expected = 48
            ratio = count / expected if expected > 0 else 0
            coverage_stats.append(ratio)
            
        avg_coverage = float(np.mean(coverage_stats))
        
        return {
            "status": "COMPLETED",
            "average_coverage_ratio": avg_coverage,
            "total_4h_windows": len(dataset),
            "perfectly_covered_windows": int(np.sum(np.array(coverage_stats) >= 1.0)),
            "critically_low_coverage_windows": int(np.sum(np.array(coverage_stats) < 0.5)),
            "intrabar_coverage_status": "MICROSTRUCTURE_INTRABAR_COVERAGE_AUDIT_COMPLETED"
        }
