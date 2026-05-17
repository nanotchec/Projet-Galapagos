from typing import Dict, Any

class OfflineReviewRecommendationEngine:
    """Generates next steps for V1.58."""
    
    def generate(self, gate_passed: bool) -> Dict[str, Any]:
        if gate_passed:
            return {
                "recommended_next_step": "prepare controlled preflight plan with network disabled by default",
                "next_allowed_phase": "controlled_preflight_planning",
                "evidence_required": "preflight_planning_artifact"
            }
        else:
            return {
                "recommended_next_step": "resolve blocking contract review risks before preflight",
                "next_allowed_phase": "more_contract_refinement",
                "evidence_required": "updated_contract_spec"
            }
