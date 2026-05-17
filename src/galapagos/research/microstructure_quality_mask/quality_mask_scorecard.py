"""Quality mask scorecard."""
from typing import Dict, Any

class QualityMaskScorecard:
    def run(self, impact: Dict[str, Any], retention: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        
        # Base score on usable ratio
        ratio = impact.get("usable_ratio", 0)
        if ratio > 0.9: score += 50
        elif ratio > 0.7: score += 30
        else: score += 10
        
        # Base score on feature retention
        retained = len(retention.get("retained_features", []))
        total = retained + len(retention.get("reworked_features", [])) + len(retention.get("blocked_features", []))
        if total > 0:
            score += int(50 * (retained / total))
            
        return {
            "overall_quality_score": score,
            "grade": "A" if score > 80 else "B" if score > 60 else "C" if score > 40 else "F",
            "impact_metrics": impact,
            "retention_summary": retention
        }
