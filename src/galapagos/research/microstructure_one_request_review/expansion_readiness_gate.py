from typing import Any, Dict

class ExpansionReadinessGate:
    def evaluate_gate(self, review_passed: bool) -> Dict[str, Any]:
        return {
            "expansion_readiness_gate_created": True,
            "one_request_preflight_review_passed": review_passed,
            "collection_expansion_approved": False,
            "future_expansion_requires_new_human_approval": True,
            "max_future_request_count_without_new_approval": 0,
            "gate_status": "LOCKED_PENDING_NEW_HUMAN_APPROVAL" if review_passed else "BLOCKED_BY_REVIEW_FAILURE"
        }
