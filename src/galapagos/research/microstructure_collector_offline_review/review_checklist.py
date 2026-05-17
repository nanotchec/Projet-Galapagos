from typing import Dict, Any

class OfflineReviewChecklist:
    """Verifies baseline requirements for V1.58."""
    
    def __init__(self):
        self.results = {}

    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        v1572 = data.get("field_coverage_summary", {})
        
        self.results = {
            "v1_57_2_final_verdict_ok": v1572.get("final_verdict") == "MICROSTRUCTURE_FIELD_COVERAGE_READY_FOR_OFFLINE_REVIEW",
            "v1_57_2_packaging_ok": v1572.get("release_reports_packaging_status") == "RELEASE_REPORTS_INCLUDED",
            "v1_57_2_semantics_consistent": v1572.get("field_coverage_semantic_consistency_status") == "FIELD_COVERAGE_SEMANTICS_CONSISTENT",
            "real_collection_not_approved": v1572.get("real_collection_approved") is False,
            "human_review_required": v1572.get("human_review_required_before_collection") is True,
            "infrastructure_only": v1572.get("evidence_classification") == "INFRASTRUCTURE_ONLY",
            "network_disabled": v1572.get("network_disabled") is True
        }
        
        return self.results

    def get_report(self) -> Dict[str, Any]:
        passed = all(self.results.values())
        return {
            "status": "COMPLETED",
            "checklist_passed": passed,
            "details": self.results
        }
