from typing import Any

def decompose_losses(diagnostics: dict[str, Any]) -> dict[str, Any]:
    """
    Synthesize all diagnostics into a loss decomposition.
    """
    drivers = {
        "calibration_driver": diagnostics.get("calibration", {}).get("status"),
        "ev_proxy_driver": diagnostics.get("ev_proxy", {}).get("status"),
        "payoff_driver": diagnostics.get("payoff", {}).get("status"),
        "cost_driver": diagnostics.get("cost_drag", {}).get("status"),
        "regime_driver": diagnostics.get("regime", {}).get("status"),
        "score_shift_driver": diagnostics.get("score_shift", {}).get("status"),
        "feature_shift_driver": diagnostics.get("feature_shift", {}).get("status"),
        "concentration_driver": diagnostics.get("concentration", {}).get("status"),
    }
    
    primary = "REVERSAL_UNEXPLAINED"
    secondaries = []
    
    # Priority logic
    if drivers["calibration_driver"] == "CALIBRATION_REVERSAL_DETECTED":
        primary = "CALIBRATION_DRIFT"
    elif drivers["ev_proxy_driver"] == "EV_PROXY_OVERESTIMATES_2026":
        primary = "EV_PROXY_DEGRADATION"
    elif drivers["regime_driver"] == "REGIME_SHIFT_EXPLAINS_REVERSAL":
        primary = "REGIME_SHIFT"
    elif drivers["payoff_driver"] == "PAYOFF_ASYMMETRY_DEGRADED_2026":
        primary = "PAYOFF_DEGRADATION"
        
    for k, v in drivers.items():
        if "DETECTED" in str(v) or "SHIFT" in str(v) or "DEGRADED" in str(v):
            if k != primary:
                secondaries.append(k)
                
    return {
        "drivers": drivers,
        "primary_driver": primary,
        "secondary_drivers": secondaries,
        "status": "REVERSAL_DRIVER_IDENTIFIED" if primary != "REVERSAL_UNEXPLAINED" else "REVERSAL_DIAGNOSTIC_INCONCLUSIVE"
    }
