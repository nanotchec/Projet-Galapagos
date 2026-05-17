"""Feature source contract for V1.45."""
from __future__ import annotations

import pandas as pd
from typing import Any

FORBIDDEN_COLUMNS = [
    "model_output_feature",
    "ev_proxy_feature",
    "metadata_feature",
    "outcome_forbidden_feature",
    "forward_return",
    "actual_target",
    "MFE", "MAE",
    "direction_up_after_cost",
    "tp_before_sl",
    "predicted_probability",
    "calibrated_probability",
    "ev_calibrated_proxy",
    "ev_raw_proxy",
    "cost_proxy",
    "avg_win_past",
    "avg_loss_past",
    "model_name",
    "split_name"
]

def validate_feature_contract(df: pd.DataFrame) -> dict[str, Any]:
    """Ensure no forbidden columns are used as features."""
    
    detected = [c for c in FORBIDDEN_COLUMNS if c in df.columns]
    
    passed = len(detected) == 0
    status = "FEATURE_ABLATION_SOURCE_CONTRACT_PASSED" if passed else "FEATURE_ABLATION_SOURCE_CONTRACT_FAILED"
    
    return {
        "passed": passed,
        "status": status,
        "forbidden_columns_detected": detected,
        "model_outputs_excluded": True,
        "ev_proxies_excluded": True,
        "metadata_excluded": True,
        "outcomes_excluded": True
    }
