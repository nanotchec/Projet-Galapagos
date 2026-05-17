from __future__ import annotations

from typing import Any

def audit_live_executability(static_audit: dict[str, Any]) -> dict[str, Any]:
    """Classify the rule based on live executability potential."""
    
    uses_full_period = static_audit.get("uses_full_period_scores", False)
    
    classification = "RETROSPECTIVE_ONLY" if uses_full_period else "LIVE_EXECUTABLE"
        
    return {
        "decision_time": static_audit.get("decision_time"),
        "execution_time_defined": False,
        "live_executable_as_written": not uses_full_period,
        "delayed_execution_possible": uses_full_period,
        "delayed_execution_defined_in_protocol": False,
        "classification": classification
    }
