"""Calculation of diagnostic verdict for microstructure coverage."""
from __future__ import annotations

from typing import Any

class CoverageDiagnosticVerdict:
    """Calculates the final diagnostic verdict."""
    
    def run(self, results: dict[str, Any]) -> dict[str, Any]:
        """Determines the final verdict."""
        scorecard = results.get("scorecard", {}).get("scorecard", {})
        final_score = scorecard.get("final_quality_score", 0.0)
        
        if final_score >= 0.9:
            verdict = "MICROSTRUCTURE_COVERAGE_SUFFICIENT_FOR_NEXT_DIAGNOSTIC"
        elif final_score >= 0.7:
            verdict = "MICROSTRUCTURE_COVERAGE_WEAK_BUT_USABLE"
        elif final_score >= 0.4:
            verdict = "MICROSTRUCTURE_COVERAGE_BLOCKS_NEXT_DIAGNOSTIC"
        else:
            verdict = "MICROSTRUCTURE_COVERAGE_INCONCLUSIVE"
            
        return {
            "status": "COMPLETED",
            "final_verdict": verdict,
            "evidence_classification": "RESEARCH_ONLY"
        }
