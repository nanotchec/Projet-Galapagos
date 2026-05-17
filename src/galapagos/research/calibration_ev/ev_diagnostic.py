from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.calibration_ev.expected_value_proxy import calculate_ev_proxy


def run_ev_diagnostic(
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """
    Orchestrate the EV diagnostic.
    """
    ev_results = calculate_ev_proxy(selection_frame, outcome_frame)
    
    if not ev_results:
        return {"ev_proxy_status": "DATA_QUALITY_BLOCKS_EV_RESEARCH"}
        
    avg_ev = sum(r["ev_proxy"] for r in ev_results) / len(ev_results)
    avg_actual = sum(r["actual_avg_outcome"] for r in ev_results) / len(ev_results)
    
    status = "EV_PROXY_RESEARCH_FOUNDATION_READY"
    if avg_ev > 0 and avg_actual < 0:
        status = "EV_PROXY_DIAGNOSTIC_ONLY"  # Severe mismatch
        
    return {
        "ev_by_bin": ev_results,
        "global_avg_ev_proxy": float(avg_ev),
        "global_avg_actual_outcome": float(avg_actual),
        "ev_proxy_status": status
    }
