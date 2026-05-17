"""Data action plan builder for microstructure enrichment."""
from typing import Dict, Any, List

class DataActionPlanBuilder:
    def build_plan(self, impact: Dict[str, Any], retention: Dict[str, Any]) -> Dict[str, Any]:
        actions = []
        
        if impact.get("blocked_ratio_2026", 0) > 0.5:
            actions.append("URGENT: Re-collect intrabar data for 2026 to reduce blocked windows")
            
        for f in retention.get("reworked_features", []):
            actions.append(f"REWORK: Fix data quality for feature {f}")
            
        if not actions:
            actions.append("MAINTENANCE: Regular monitoring of intrabar coverage")
            
        return {
            "status": "DATA_ACTION_PLAN_DEFINED",
            "actions": actions,
            "minimum_conditions": [
                "Intrabar coverage > 98% for 2026",
                "Feature missingness < 2% across all usable windows"
            ]
        }
