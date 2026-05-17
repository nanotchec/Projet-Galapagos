"""Build joint regime slices from microstructure labels V1.49."""
from __future__ import annotations

import pandas as pd
from typing import Any

def build_regime_slices(
    analysis_frame: pd.DataFrame,
    labels: list[str]
) -> pd.DataFrame:
    """Build a combined 'micro_regime' column from multiple labels."""
    frame = analysis_frame.copy()
    
    if not labels:
        frame["micro_regime"] = "unknown"
        return frame
        
    # Combine labels into a single string identifier
    def combine_labels(row):
        return "|".join([f"{L}:{row[L]}" for L in labels])
        
    frame["micro_regime"] = frame.apply(combine_labels, axis=1)
    
    return frame

def get_regime_statistics(frame: pd.DataFrame) -> dict[str, Any]:
    """Calculate basic distribution stats per regime."""
    counts = frame["micro_regime"].value_counts().to_dict()
    total = len(frame)
    pct = {k: (v / total) * 100 for k, v in counts.items()}
    
    return {
        "regime_counts": counts,
        "regime_percentages": pct,
        "unique_regimes": list(counts.keys())
    }
