from typing import Any

def determine_diagnostic_verdict(decomposition: dict[str, Any]) -> dict[str, Any]:
    """
    Determine final diagnostic verdict and next steps.
    """
    primary = decomposition.get("primary_driver")
    
    verdict = "RECENT_REVERSAL_DIAGNOSTIC_INCONCLUSIVE"
    recommended_step = "deeper data/model audit"
    
    if primary == "CALIBRATION_DRIFT":
        verdict = "RECENT_REVERSAL_DRIVER_IDENTIFIED"
        recommended_step = "V1.34 recalibration / recalibration drift research"
    elif primary == "EV_PROXY_DEGRADATION":
        verdict = "RECENT_REVERSAL_DRIVER_IDENTIFIED"
        recommended_step = "V1.34 payoff-aware model objective research"
    elif primary == "REGIME_SHIFT":
        verdict = "RECENT_REVERSAL_DRIVER_IDENTIFIED"
        recommended_step = "V1.34 causal regime-aware modeling research"
    elif primary == "PAYOFF_DEGRADATION":
        verdict = "RECENT_REVERSAL_DRIVER_IDENTIFIED"
        recommended_step = "V1.34 payoff-aware model objective research"
        
    return {
        "final_verdict": verdict,
        "recommended_next_step": recommended_step,
        "evidence_classification": "DIAGNOSTIC_ONLY"
    }
