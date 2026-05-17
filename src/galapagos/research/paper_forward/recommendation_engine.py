from __future__ import annotations

from typing import Any

def get_v1_27_recommendation(validation_res: dict[str, Any]) -> dict[str, Any]:
    """Generate final recommendation based on validation harness results."""
    
    executed = validation_res.get("validation_executed", False)
    status = validation_res.get("criteria_status", "UNKNOWN")
    count = validation_res.get("selected_count", 0)
    
    if not executed:
        verdict = "PAPER_FORWARD_HARNESS_READY_NO_NEW_DATA"
        reco = "Harness is ready. Waiting for out-of-sample data collection."
    elif count < 60:
        verdict = "PAPER_FORWARD_VALIDATION_INCONCLUSIVE_NEEDS_MORE_DATA"
        reco = f"Detected {count} trades OOS. 60 trades required for conclusive validation."
    elif validation_res.get("validation_passed"):
        verdict = "PAPER_FORWARD_VALIDATION_PASSED_PRELIMINARY"
        reco = "Preliminary criteria passed on OOS data. Strategy remains in validation phase."
    else:
        verdict = "PAPER_FORWARD_VALIDATION_FAILED"
        reco = "Out-of-sample criteria not met. Strategy robustness rejected."
        
    return {
        "final_verdict": verdict,
        "validation_status": status,
        "future_validation_required": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "recommended_next_step": reco,
        "do_not_do_next": [
            "ACTIVATE_REVIEWER",
            "EXECUTE_HOLDOUT",
            "REAL_TRADING",
            "MODIFY_FILTER"
        ]
    }
