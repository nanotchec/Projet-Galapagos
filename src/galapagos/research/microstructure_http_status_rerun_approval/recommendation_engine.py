from typing import Any, Dict

class RecommendationEngine:
    def compute_recommendation(self, verdict_res: Dict[str, Any]) -> Dict[str, Any]:
        if "APPROVED" in verdict_res["final_verdict"]:
            return {
                "recommended_next_step": "execute bounded reports-only HTTP-status rerun in V1.79 with at most 10 public requests",
                "next_allowed_phase": verdict_res["next_allowed_phase"]
            }
        return {
            "recommended_next_step": "fix blocking issues before any rerun",
            "next_allowed_phase": verdict_res["next_allowed_phase"]
        }
