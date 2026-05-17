"""Loader for microstructure regime labels V1.49."""
from __future__ import annotations

import pandas as pd
from typing import Any

def load_microstructure_labels(
    analysis_frame: pd.DataFrame,
    micro_summary: dict[str, Any]
) -> tuple[pd.DataFrame, list[str]]:
    """Extract and validate selected microstructure labels."""
    selected_labels = micro_summary.get("best_microstructure_regime_labels", [
        "amihud_illiquidity_regime", 
        "realized_vol_proxy_regime"
    ])
    
    # Ensure they are in the frame
    available_labels = [L for L in selected_labels if L in analysis_frame.columns]
    
    # Check for consistency with V1.48.1
    if len(available_labels) < len(selected_labels):
        print(f"Warning: only {len(available_labels)}/{len(selected_labels)} labels available")
        
    return analysis_frame[available_labels], available_labels
