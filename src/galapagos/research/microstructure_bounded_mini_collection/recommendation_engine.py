from typing import Any, Dict

class RecommendationEngine:
    def compute_recommendation(self, verdict_res: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "recommended_next_step": verdict_res["recommended_next_step"],
            "next_allowed_phase": verdict_res["next_allowed_phase"],
            "v1_77_mini_collection_certified": True if "PASSED" in verdict_res["final_verdict"] else False
        }
