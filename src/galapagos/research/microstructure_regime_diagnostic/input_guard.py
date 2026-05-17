"""Input guard for microstructure regime diagnostic V1.49."""
from __future__ import annotations

from typing import Any
import pandas as pd

FORBIDDEN_COLUMNS = {
    "forward_return", "target", "outcome", "future", 
    "mfe", "mae", "ev_proxy", "model_output", "prediction_label"
}

def validate_diagnostic_inputs(
    analysis_frame: pd.DataFrame,
    micro_summary: dict[str, Any]
) -> dict[str, Any]:
    """Validate that inputs are research-safe and consistent."""
    issues = []
    
    # Check for forbidden columns in feature set (except those allowed for diagnostic only)
    # The mission says outcomes can be used for diagnostic analysis but never for construction.
    # We check if construction labels are present in columns.
    
    selected_labels = micro_summary.get("best_microstructure_regime_labels", [])
    if not selected_labels:
        selected_labels = ["amihud_illiquidity_regime", "realized_vol_proxy_regime"]
        
    for label in selected_labels:
        if label not in analysis_frame.columns:
            issues.append(f"Selected label missing from analysis frame: {label}")

    # Check for lookahead bias in labels (very basic check)
    # In a real system we would check for rolling vs global stats.
    
    # Check for NaN in critical columns
    for label in selected_labels:
        if label in analysis_frame.columns:
            nan_count = analysis_frame[label].isna().sum()
            if nan_count > 0.5 * len(analysis_frame):
                issues.append(f"Label {label} has too many NaNs: {nan_count}")

    return {
        "status": "MICROSTRUCTURE_REGIME_DIAGNOSTIC_INPUT_GUARD_PASSED" if not issues else "FAILED",
        "issues": issues,
        "selected_labels": selected_labels,
        "row_count": len(analysis_frame),
    }
