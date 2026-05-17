from typing import Any, Dict

class MiniCollectionReadinessGate:
    def create_gate(self, review_passed: bool) -> Dict[str, Any]:
        return {
            "mini_collection_readiness_gate_created": True,
            "bounded_mini_collection_approved": False,
            "future_mini_collection_requires_new_human_approval": True,
            "max_future_request_count_without_new_approval": 0,
            "readiness_status": "READY_FOR_APPROVAL_INTAKE" if review_passed else "BLOCKED_BY_REVIEW",
            "mini_collection_scope": "BOUNDED_REPORTS_ONLY_NO_DATA_NO_TRADING",
            "mini_collection_max_requests": 100 # Example planned limit
        }
