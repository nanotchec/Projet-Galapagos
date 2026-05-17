from __future__ import annotations

from typing import Any

def generate_causality_verdict(
    static: dict[str, Any],
    lookahead: dict[str, Any],
    executability: dict[str, Any]
) -> dict[str, Any]:
    """Synthesize results into a final verdict."""
    
    is_static_non_causal = static.get("static_causality_status") == "NON_CAUSAL_FULL_PERIOD_SELECTION"
    has_lookahead = lookahead.get("lookahead_status") == "INTRA_PERIOD_LOOKAHEAD_DETECTED"
    is_retrospective = executability.get("classification") == "RETROSPECTIVE_ONLY"
    
    if is_static_non_causal or has_lookahead or is_retrospective:
        final_verdict = "CURRENT_FILTER_NON_CAUSAL_RETROSPECTIVE_ONLY"
        strategy_status = "INVALID_FOR_LIVE_VALIDATION"
        reclassification = "RETROSPECTIVE_DISCOVERY_ONLY"
    else:
        final_verdict = "CURRENT_FILTER_CAUSAL_FORWARD_READY"
        strategy_status = "VALID_FOR_FORWARD_TESTING"
        reclassification = "CAUSAL_REFERENCE_PROTOCOL"
        
    return {
        "static_causality_status": static.get("static_causality_status"),
        "lookahead_status": lookahead.get("lookahead_status"),
        "live_executability_classification": executability.get("classification"),
        "final_verdict": final_verdict,
        "strategy_validation_status": strategy_status,
        "protocol_status_recommendation": reclassification
    }
