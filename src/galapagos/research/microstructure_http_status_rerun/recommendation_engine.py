from typing import Any, Dict

class RecommendationEngine:
    def compute_recommendation(self, verdict_res: Dict[str, Any]) -> Dict[str, Any]:
        verdict = verdict_res["final_verdict"]
        
        if "PASSED" in verdict:
            return {
                "recommended_next_step": "review bounded HTTP-status rerun before any data-write or dataset proposal",
                "next_allowed_phase": verdict_res["next_allowed_phase"]
            }
        elif "INCOMPLETE" in verdict:
            return {
                "recommended_next_step": "fix HTTP status capture before any further network expansion",
                "next_allowed_phase": verdict_res["next_allowed_phase"]
            }
        elif "FAILED_SAFELY" in verdict:
            return {
                "recommended_next_step": "review network failure before retrying any bounded rerun",
                "next_allowed_phase": verdict_res["next_allowed_phase"]
            }
        else:
            return {
                "recommended_next_step": "review safety incident before any further action",
                "next_allowed_phase": verdict_res["next_allowed_phase"]
            }
