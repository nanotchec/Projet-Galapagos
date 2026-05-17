"""Scorecard of microstructure coverage and quality metrics."""
from __future__ import annotations

from typing import Any

class CoverageScorecard:
    """Aggregates all metrics into a single scorecard."""
    
    def run(self, results: dict[str, Any]) -> dict[str, Any]:
        """Builds the final scorecard."""
        
        scorecard = {
            "intrabar_coverage_score": results.get("intrabar_coverage", {}).get("average_coverage_ratio", 0.0),
            "alignment_score": results.get("timestamp_alignment", {}).get("alignment_score", 0.0),
            "missingness_score": 1.0 - sum(results.get("missingness_profile", {}).get("missingness_per_feature", {}).values()) / max(1, len(results.get("missingness_profile", {}).get("missingness_per_feature", {}))),
            "gap_penalty": min(1.0, results.get("gap_detection", {}).get("long_gaps_count", 0) * 0.1),
        }
        
        scorecard["final_quality_score"] = float(np.mean([scorecard["intrabar_coverage_score"], scorecard["alignment_score"], scorecard["missingness_score"]]) - scorecard["gap_penalty"])
        
        return {
            "status": "COMPLETED",
            "scorecard": scorecard,
            "coverage_scorecard_status": "MICROSTRUCTURE_COVERAGE_SCORECARD_COMPLETED"
        }

import numpy as np
