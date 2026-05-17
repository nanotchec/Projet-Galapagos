from __future__ import annotations

from typing import Any


def audit_overfit(
    rules_tested: int, 
    best_filter_beats_p95: bool,
    top_filter_rank: int = 1
) -> dict[str, Any]:
    """Audit for multiple testing bias and selection overfit."""
    
    multiple_testing_warning = False
    if rules_tested > 10:
        multiple_testing_warning = True
        
    verdict = "FILTER_PRELIMINARILY_INTERESTING"
    if rules_tested > 10:
        verdict = "MULTIPLE_TESTING_RISK_MODERATE"
    if rules_tested > 25: # V1.25 had 26 rules
        verdict = "MULTIPLE_TESTING_RISK_HIGH"
        
    if not best_filter_beats_p95:
        verdict = "FILTER_NOT_ROBUST"
        
    return {
        "rules_tested_count": rules_tested,
        "multiple_testing_warning": multiple_testing_warning,
        "best_filter_beats_p95": best_filter_beats_p95,
        "top_filter_rank": top_filter_rank,
        "verdict": verdict,
        "audit_note": (
            "FILTER_NEEDS_OUT_OF_SAMPLE_CONFIRMATION" 
            if verdict != "FILTER_NOT_ROBUST" else "FILTER_REJECTED"
        )
    }
