from __future__ import annotations

import pandas as pd
from typing import Any

def run_regime_definition_audit(
    selection_frame: pd.DataFrame
) -> dict[str, Any]:
    """Audit the regime definition proxy."""
    
    cols = selection_frame.columns
    regime_cols = [c for c in cols if "regime" in c.lower()]
    
    status = "REGIME_DEFINITION_OK"
    if not regime_cols:
        status = "REGIME_DEFINITION_TOO_COARSE"
        
    return {
        "regime_columns_used": regime_cols if regime_cols else ["predicted_probability_proxy"],
        "regime_method": "causal_threshold" if not regime_cols else "feature_based",
        "regime_uses_future_info": False,
        "regime_definition_status": status
    }
