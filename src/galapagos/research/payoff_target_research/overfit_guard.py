"""Monitor and guard against overfitting in payoff research."""
from __future__ import annotations

from typing import Any

def check_overfit_risk(
    horizons_count: int,
    targets_count: int,
    metrics_count: int = 10
) -> dict[str, Any]:
    """Assess the risk of multiple testing bias."""
    combinations = horizons_count * targets_count
    
    status = "PAYOFF_TARGET_OVERFIT_RISK_LOW"
    if combinations > 20:
        status = "PAYOFF_TARGET_OVERFIT_RISK_HIGH"
    elif combinations > 5:
        status = "PAYOFF_TARGET_OVERFIT_RISK_MODERATE"
        
    return {
        "status": status,
        "horizons_tested_count": horizons_count,
        "target_definitions_count": targets_count,
        "combinations_tested_count": combinations,
        "metric_count": metrics_count,
        "multiple_testing_risk": status.split("_")[-1],
        "evidence_classification": "EXPLORATORY_ONLY",
        "preregistration_allowed": False,
        "paper_live_allowed": False,
        "no_strategy_validated": True
    }
