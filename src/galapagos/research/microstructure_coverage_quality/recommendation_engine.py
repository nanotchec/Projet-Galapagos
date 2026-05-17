"""Recommendation engine for microstructure data coverage."""
from __future__ import annotations

from typing import Any

class CoverageRecommendationEngine:
    """Generates recommendations based on coverage audit."""
    
    def run(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculates recommendations."""
        scorecard = results.get("scorecard", {}).get("scorecard", {})
        final_score = scorecard.get("final_quality_score", 0.0)
        
        actions = []
        if final_score < 0.8:
            actions.append("Improve intrabar coverage for 2026")
        if scorecard.get("gap_penalty", 0) > 0:
            actions.append("Fill temporal gaps in silver dataset")
        
        next_step = "improve microstructure data coverage before further regime diagnostics"
        if final_score >= 0.9:
            next_step = "rerun micro-regime diagnostics after applying coverage quality policy"
            
        return {
            "status": "COMPLETED",
            "recommended_data_actions": actions,
            "recommended_next_step": next_step,
            "recommended_keep_for_next_research": ["amihud_illiquidity", "realized_vol_proxy"],
            "recommended_rework": ["volume_vol_ratio"] if final_score < 0.7 else [],
            "recommendation_status": "MICROSTRUCTURE_COVERAGE_RECOMMENDATION_COMPLETED"
        }
