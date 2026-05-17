from typing import Any, Dict

class SafetyVerdictEngine:
    def compute_verdict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        phrase_valid = context.get("approval_phrase_validated") is True
        
        if phrase_valid:
            return {
                "final_verdict": "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_APPROVAL_VALIDATED",
                "recommended_next_step": "execute bounded reports-only mini-collection in V1.77 with at most 10 public requests",
                "next_allowed_phase": "bounded_reports_only_mini_collection",
                "v1_77_bounded_mini_collection_authorized": True
            }
        
        return {
            "final_verdict": "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_APPROVAL_PENDING",
            "recommended_next_step": "provide exact approval phrase only if you want to authorize V1.77 bounded reports-only mini-collection",
            "next_allowed_phase": "provide_explicit_human_approval_for_bounded_mini_collection",
            "v1_77_bounded_mini_collection_authorized": False
        }
