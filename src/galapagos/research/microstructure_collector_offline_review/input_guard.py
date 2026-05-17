from typing import Dict, Any, List

class OfflineReviewInputGuard:
    """Validates input reports for V1.58."""
    
    def __init__(self):
        self.issues = []

    def validate(self, data: Dict[str, Any]) -> bool:
        self.issues = []
        
        # Check V1.57.2 alignment
        v1572 = data.get("field_coverage_summary", {})
        if v1572.get("version") != "V1.57.2":
            self.issues.append(f"Invalid field coverage version: {v1572.get('version')}, expected V1.57.2")
            
        # Check safety flags in V1.57.2
        if v1572.get("real_collection_approved") is not False:
            self.issues.append("V1.57.2 must have real_collection_approved=false")
            
        if not v1572.get("contract_ready_for_offline_review"):
            self.issues.append("V1.57.2 must indicate contract_ready_for_offline_review=true")

        # Check V1.56.1
        v1561 = data.get("contract_approval_summary", {})
        if v1561.get("version") != "V1.56.1":
            self.issues.append(f"Invalid contract approval version: {v1561.get('version')}, expected V1.56.1")

        return len(self.issues) == 0

    def get_report(self) -> Dict[str, Any]:
        return {
            "status": "PASSED" if not self.issues else "FAILED",
            "issues": self.issues,
            "input_guard_passed": len(self.issues) == 0
        }
