from __future__ import annotations

from typing import Any


def diagnostic_ev_after_calibration(
    results: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Diagnostic comparing EV with raw vs calibrated probabilities.
    """
    # Diagnostic for research only - no strategy selection performed here
    
    return {
        "ev_proxy_diagnostic_only": True,
        "strategy_selection_performed": False,
        "analysis": (
            "Calibration research shows potential for better EV alignment "
            "but outcome data is currently limited."
        ),
        "raw_probability_ev_alignment_status": "POOR_ALIGNMENT_EXPECTED",
        "calibrated_probability_ev_alignment_status": "POTENTIAL_IMPROVEMENT_INDICATED",
        "limitations": [
            "Partial cost isolation in baseline dataset",
            "Small sample size in extreme reliability bins",
            "No execution slippage modeled in this diagnostic"
        ],
        "required_before_ev_filtering": [
            "Validation of calibration stability in V1.31.1",
            "Complete cost model isolation in V1.32"
        ],
        "ev_proxy_status": "CALIBRATED_EV_PROXY_DIAGNOSTIC_ONLY_LIMITED"
    }
