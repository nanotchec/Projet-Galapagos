from typing import Any, Dict

class RecommendationEngine:
    def compute_recommendation(self, approval_granted: bool) -> Dict[str, Any]:
        if approval_granted:
            return {
                "recommended_next_step": "execute exactly one-request tiny network preflight in V1.71 with reports-only output"
            }
        else:
            return {
                "recommended_next_step": "provide exact approval phrase in approval_phrase_input if you want to authorize V1.71 one-request network preflight"
            }
