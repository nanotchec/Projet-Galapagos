"""Profiling of data quality by year/session."""
from __future__ import annotations

import pandas as pd
from typing import Any

class SessionQualityProfile:
    """Evaluates data quality for different time sessions."""
    
    def run(self, dataset: pd.DataFrame) -> dict[str, Any]:
        """Calculates quality scores for 2024, 2025, 2026."""
        if not pd.api.types.is_datetime64_any_dtype(dataset.index):
            dataset.index = pd.to_datetime(dataset.index)
            
        sessions = {
            "2024": dataset[dataset.index.year == 2024],
            "2025": dataset[dataset.index.year == 2025],
            "2026": dataset[dataset.index.year == 2026],
        }
        
        scores = {}
        for year, df in sessions.items():
            if df.empty:
                scores[year] = 0.0
                continue
            # Simple score based on non-null values
            scores[year] = float(1.0 - df.isnull().mean().mean())
            
        return {
            "status": "COMPLETED",
            "session_quality_scores": scores,
            "session_quality_status": "MICROSTRUCTURE_SESSION_QUALITY_PROFILE_COMPLETED"
        }
